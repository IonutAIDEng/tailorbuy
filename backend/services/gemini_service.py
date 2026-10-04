import json
import logging
import os
import re
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
    before_sleep_log,
)

from backend.constants import GEMINI_MODEL, GEMINI_MAX_RETRIES, GEMINI_RETRY_MAX_WAIT_SECONDS

load_dotenv(Path(__file__).parent.parent / ".env")

_logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    pass


def _is_retryable(exc: Exception) -> bool:
    """Identify transient failures that should trigger an automatic retry.

    Retries on:
      - HTTP 429: quota exhausted — back off and retry.
      - HTTP 503: transient server overload.
      - ValueError: occasional SDK-level parse failures on otherwise valid responses.
    """
    from google.api_core.exceptions import GoogleAPICallError
    if isinstance(exc, GoogleAPICallError):
        code = getattr(exc, "grpc_status_code", None)
        http_code = getattr(exc, "code", None)
        if http_code in (429, 503) or (code is not None and code.value[0] in (8, 14)):
            return True
    return isinstance(exc, ValueError)


_retry_strategy = retry(
    stop=stop_after_attempt(GEMINI_MAX_RETRIES),
    wait=wait_random_exponential(multiplier=1, max=GEMINI_RETRY_MAX_WAIT_SECONDS),
    retry=retry_if_exception(_is_retryable),
    before_sleep=before_sleep_log(_logger, logging.WARNING),
    reraise=True,
)


class GeminiService:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise GeminiServiceError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self._model = self._build_model()

    def _build_model(self) -> genai.GenerativeModel:
        return genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            tools=[{"google_search_retrieval": {}}],
        )

    @_retry_strategy
    def _call_api(self, prompt: str) -> str:
        response = self._model.generate_content(contents=prompt)
        return response.text

    def search_products(self, prompt: str) -> list[dict]:
        try:
            raw_text = self._call_api(prompt)
            return _extract_products(raw_text)
        except GeminiServiceError:
            raise
        except Exception as e:
            raise GeminiServiceError(f"Gemini search failed: {str(e)}") from e


def _extract_products(raw_text: str) -> list[dict]:
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
