import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path

import httpx

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
    before_sleep_log,
)

from backend.constants import GEMINI_MODEL, GEMINI_MAX_RETRIES, GEMINI_RETRY_MAX_WAIT_SECONDS, GEMINI_MODEL_PRICING

load_dotenv(Path(__file__).parent.parent / ".env")

_logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    pass


def _is_retryable(exc: Exception) -> bool:
    """Identify transient failures that should trigger an automatic retry.

    Retries on:
      - SDK ClientError with 429 or 503: quota exhausted / transient overload.
      - httpx HTTP 429/503: same, surfaced at transport layer.
      - ValueError: occasional SDK-level parse failures on otherwise valid responses.
      - httpx network errors: connection drops and remote disconnects.
    """
    if isinstance(exc, genai_errors.ClientError):
        return getattr(exc, "status_code", None) in (429, 503)
    status_code = (
        getattr(exc, "code", None)
        or getattr(exc, "status_code", None)
        or (exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None)
    )
    if status_code in (429, 503):
        return True
    return isinstance(exc, (ValueError, httpx.RemoteProtocolError, httpx.ConnectError))


_retry_strategy = retry(
    stop=stop_after_attempt(GEMINI_MAX_RETRIES),
    wait=wait_random_exponential(multiplier=1, max=GEMINI_RETRY_MAX_WAIT_SECONDS),
    retry=retry_if_exception(_is_retryable),
    before_sleep=before_sleep_log(_logger, logging.WARNING),
    reraise=True,
)


@dataclass(frozen=True)
class UsageSummary:
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    total_tokens: int
    cost_usd: float


def _compute_usage(usage_metadata) -> UsageSummary:
    input_tokens = getattr(usage_metadata, "prompt_token_count", 0) or 0
    output_tokens = getattr(usage_metadata, "candidates_token_count", 0) or 0
    thinking_tokens = getattr(usage_metadata, "thoughts_token_count", 0) or 0

    pricing = GEMINI_MODEL_PRICING.get(GEMINI_MODEL)
    if pricing is None:
        _logger.warning("No pricing config for model '%s' — cost will be reported as $0.00", GEMINI_MODEL)
        cost_usd = 0.0
    else:
        cost_usd = (
            input_tokens * pricing.input / 1_000_000
            + output_tokens * pricing.output / 1_000_000
            + thinking_tokens * pricing.thinking / 1_000_000
        )

    return UsageSummary(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        thinking_tokens=thinking_tokens,
        total_tokens=input_tokens + output_tokens + thinking_tokens,
        cost_usd=cost_usd,
    )


def _log_usage(summary: UsageSummary) -> None:
    _logger.info(
        "Gemini usage | input=%d output=%d thinking=%d total=%d cost=$%.6f",
        summary.input_tokens,
        summary.output_tokens,
        summary.thinking_tokens,
        summary.total_tokens,
        summary.cost_usd,
    )


class GeminiService:
    """Client wrapper for the Google Gemini generative AI API.

    Configures the Gemini client with Google Search grounding on initialisation
    and exposes a single public method for executing product searches.

    Attributes:
        _client: Authenticated google.genai Client instance.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            _logger.critical("GEMINI_API_KEY is missing — Gemini service cannot be initialised")
            raise GeminiServiceError("GEMINI_API_KEY not found in environment variables")
        self._client = genai.Client(api_key=api_key)
        _logger.info("GeminiService initialised with model '%s'", GEMINI_MODEL)

    @_retry_strategy
    def _call_api(self, prompt: str) -> str:
        """
        Send a prompt to the Gemini API and return the raw text response.

        Decorated with the retry strategy for transient failures (429, 503).
        AFC is explicitly disabled to prevent the SDK from treating Google Search
        as a Python callable — grounding is handled server-side by the model.

        Args:
            prompt: Complete XML-structured prompt string.

        Returns:
            Raw text response from Gemini.
        """
        response = self._client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        _log_usage(_compute_usage(response.usage_metadata))
        return response.text

    def search_products(self, prompt: str) -> list[dict]:
        """
        Execute a product search and return parsed results.

        Args:
            prompt: Complete XML-structured prompt string.

        Returns:
            List of raw product dicts extracted from the Gemini response.
        """
        try:
            raw_text = self._call_api(prompt)
            return _extract_products(raw_text)
        except GeminiServiceError:
            raise
        except Exception as e:
            raise GeminiServiceError(f"Gemini search failed: {str(e)}") from e


def _extract_products(raw_text: str) -> list[dict]:
    """
    Parse Gemini's raw text response and extract the products list.

    Args:
        raw_text: Raw string response from the Gemini API.

    Returns:
        List of product dicts, or empty list if none found.
    """
    data = _parse_llm_json(raw_text)
    if isinstance(data, dict):
        return data.get("products", [])
    return []


def _parse_llm_json(raw: str) -> dict | list:
    """Robustly extract and parse a JSON payload from a raw LLM response string.

    Applies progressive fallback strategies to handle common model quirks:
    literal escape sequences, markdown fences, bare newlines inside strings,
    and trailing prose after the JSON block.

    Stages:
      1. Normalise escape sequences the model occasionally emits verbatim.
      2. Strip markdown code fences (```json ... ```) and stray backticks.
      3. Repair bare newlines inside JSON string values.
      4. Attempt a direct parse on the cleaned text.
      5. Trim any trailing non-JSON content after the last closing delimiter.
      6. Regex-extract the first JSON object or array from the original
         pre-stripped text and retry, to recover when stripping corrupted content.

    Raises:
        json.JSONDecodeError: when all recovery attempts are exhausted.
    """
    normalised = raw.replace("\\'", "'")

    stripped = re.sub(r"```(?:json)?", "", normalised).strip().rstrip("`").strip()

    repaired = _fix_newlines_in_strings(stripped)

    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    for closing in ("}", "]"):
        last = repaired.rfind(closing)
        if last != -1:
            try:
                return json.loads(repaired[: last + 1])
            except json.JSONDecodeError:
                pass

    match = re.search(r"(\[.*]|\{.*})", normalised, re.DOTALL)
    if match:
        try:
            return json.loads(_fix_newlines_in_strings(match.group(0)))
        except json.JSONDecodeError:
            pass

    _logger.warning(
        "All JSON extraction attempts failed.",
        extra={"preview": raw[:300].encode("ascii", "replace").decode("ascii")},
    )
    raise json.JSONDecodeError("All extraction attempts failed", raw, 0)


def _fix_newlines_in_strings(text: str) -> str:
    """Replace bare newline characters inside JSON string values with their escaped forms.

    Walks the input character by character, tracks whether the cursor is inside
    a JSON string, and replaces literal newline and carriage-return characters
    with their escape sequences. Properly skips over already-escaped sequences
    so valid escape characters are not double-escaped.
    """
    out = []
    inside_string = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and inside_string:
            out.append(ch)
            i += 1
            if i < len(text):
                out.append(text[i])
                i += 1
            continue
        if ch == '"':
            inside_string = not inside_string
        if inside_string and ch == "\n":
            out.append("\\n")
        elif inside_string and ch == "\r":
            out.append("\\r")
        else:
            out.append(ch)
        i += 1
    return "".join(out)
