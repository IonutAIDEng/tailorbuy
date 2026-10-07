"""Tests for gemini_service module-level utilities not covered elsewhere."""
import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from backend.services.gemini_service import (
    _compute_usage,
    _fix_newlines_in_strings,
    _is_retryable,
    _log_usage,
    _parse_llm_json,
    UsageSummary,
)
from google.genai import errors as genai_errors


class TestIsRetryable:
    def test_client_error_429_is_retryable(self):
        exc = MagicMock(spec=genai_errors.ClientError)
        exc.status_code = 429
        assert _is_retryable(exc) is True

    def test_client_error_503_is_retryable(self):
        exc = MagicMock(spec=genai_errors.ClientError)
        exc.status_code = 503
        assert _is_retryable(exc) is True

    def test_client_error_404_is_not_retryable(self):
        exc = MagicMock(spec=genai_errors.ClientError)
        exc.status_code = 404
        assert _is_retryable(exc) is False

    def test_value_error_is_retryable(self):
        assert _is_retryable(ValueError("parse error")) is True

    def test_connect_error_is_retryable(self):
        assert _is_retryable(httpx.ConnectError("connect failed")) is True

    def test_remote_protocol_error_is_retryable(self):
        assert _is_retryable(httpx.RemoteProtocolError("disconnected")) is True

    def test_generic_exception_is_not_retryable(self):
        assert _is_retryable(RuntimeError("boom")) is False

    def test_exception_with_code_429_is_retryable(self):
        exc = Exception("quota exceeded")
        exc.code = 429
        assert _is_retryable(exc) is True

    def test_exception_with_status_code_503_is_retryable(self):
        exc = Exception("server error")
        exc.status_code = 503
        assert _is_retryable(exc) is True


class TestComputeUsage:
    def test_computes_cost_with_known_model(self):
        metadata = MagicMock(
            prompt_token_count=1_000_000,
            candidates_token_count=1_000_000,
            thoughts_token_count=0,
        )
        summary = _compute_usage(metadata)
        assert summary.input_tokens == 1_000_000
        assert summary.output_tokens == 1_000_000
        assert summary.thinking_tokens == 0
        assert summary.cost_usd > 0

    def test_computes_thinking_tokens(self):
        metadata = MagicMock(
            prompt_token_count=100,
            candidates_token_count=100,
            thoughts_token_count=500,
        )
        summary = _compute_usage(metadata)
        assert summary.thinking_tokens == 500
        assert summary.total_tokens == 700

    def test_returns_zero_cost_for_unknown_model(self):
        metadata = MagicMock(
            prompt_token_count=100,
            candidates_token_count=100,
            thoughts_token_count=0,
        )
        with patch("backend.services.gemini_service.GEMINI_MODEL", "unknown-model"):
            summary = _compute_usage(metadata)
        assert summary.cost_usd == 0.0

    def test_handles_none_token_counts(self):
        metadata = MagicMock(
            prompt_token_count=None,
            candidates_token_count=None,
            thoughts_token_count=None,
        )
        summary = _compute_usage(metadata)
        assert summary.input_tokens == 0
        assert summary.output_tokens == 0
        assert summary.total_tokens == 0

    def test_log_usage_does_not_raise(self):
        summary = UsageSummary(
            input_tokens=100, output_tokens=200, thinking_tokens=50,
            total_tokens=350, cost_usd=0.001,
        )
        _log_usage(summary)


class TestFixNewlinesAdditional:
    def test_replaces_carriage_return_inside_string(self):
        text = '{"key": "line1\rline2"}'
        result = _fix_newlines_in_strings(text)
        assert "\\r" in result

    def test_empty_string(self):
        assert _fix_newlines_in_strings("") == ""

    def test_no_strings(self):
        text = '{"a": 1, "b": 2}'
        result = _fix_newlines_in_strings(text)
        assert result == text


class TestParseLlmJsonAdditional:
    def test_parses_json_with_trailing_prose(self):
        raw = '{"products": [{"name": "TV"}]} Some trailing explanation from the model.'
        result = _parse_llm_json(raw)
        assert "products" in result

    def test_extracts_json_from_surrounding_text(self):
        raw = 'Here are your results: {"products": [{"name": "TV"}]} end.'
        result = _parse_llm_json(raw)
        assert result["products"][0]["name"] == "TV"

    def test_parses_json_with_bare_newlines_in_strings(self):
        raw = '{"products": [{"name": "line1\nline2"}]}'
        result = _parse_llm_json(raw)
        assert "products" in result

    def test_raises_when_regex_match_finds_unparseable_braces(self):
        """Covers except branch inside the regex fallback (lines 232-233).

        Input has bracket-like content so the regex matches, but the content
        is not valid JSON, exercising the final recovery failure path.
        """
        raw = "prefix {not: valid json content} suffix"
        with pytest.raises(json.JSONDecodeError):
            _parse_llm_json(raw)
