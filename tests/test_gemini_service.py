import json
from unittest.mock import MagicMock, patch

import pytest

from backend.services.gemini_service import (
    GeminiService,
    GeminiServiceError,
    _extract_products,
    _fix_newlines_in_strings,
    _parse_llm_json,
)


class TestExtractProducts:
    def test_extracts_products_from_valid_json(self):
        raw = json.dumps({"products": [{"name": "TV", "price_ron": 1200}]})
        result = _extract_products(raw)
        assert len(result) == 1
        assert result[0]["name"] == "TV"

    def test_returns_empty_list_for_empty_products(self):
        raw = json.dumps({"products": []})
        result = _extract_products(raw)
        assert result == []

    def test_returns_empty_list_when_key_missing(self):
        raw = json.dumps({"items": []})
        result = _extract_products(raw)
        assert result == []

    def test_handles_markdown_fenced_json(self):
        raw = "```json\n{\"products\": [{\"name\": \"test\"}]}\n```"
        result = _extract_products(raw)
        assert len(result) == 1

    def test_handles_escaped_quotes(self):
        raw = "{\"products\": [{\"name\": \"it\\'s nice\"}]}"
        result = _extract_products(raw)
        assert len(result) == 1


class TestParseLlmJson:
    def test_parses_clean_json(self):
        raw = '{"products": []}'
        result = _parse_llm_json(raw)
        assert result == {"products": []}

    def test_parses_json_with_trailing_text(self):
        raw = '{"products": []} some trailing text'
        result = _parse_llm_json(raw)
        assert "products" in result

    def test_parses_markdown_fenced(self):
        raw = "```json\n{\"key\": \"value\"}\n```"
        result = _parse_llm_json(raw)
        assert result["key"] == "value"

    def test_raises_on_invalid_json(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_llm_json("this is not json at all !!!")

    def test_parses_array_response(self):
        raw = '[{"name": "a"}, {"name": "b"}]'
        result = _parse_llm_json(raw)
        assert isinstance(result, list)
        assert len(result) == 2


class TestFixNewlinesInStrings:
    def test_replaces_newline_inside_string(self):
        text = '{"key": "line1\nline2"}'
        result = _fix_newlines_in_strings(text)
        assert "\\n" in result
        assert "\n" not in result.split('"key"')[1].split('"')[1]

    def test_keeps_newline_outside_string(self):
        text = '{"key": "value"}\n{"key2": "value2"}'
        result = _fix_newlines_in_strings(text)
        assert result.count("\n") == 1

    def test_handles_escaped_backslash(self):
        text = '{"key": "value\\\\"}'
        result = _fix_newlines_in_strings(text)
        assert result == text


class TestGeminiService:
    def test_raises_on_missing_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("backend.services.gemini_service.os.getenv", return_value=None):
                with pytest.raises(GeminiServiceError, match="GEMINI_API_KEY"):
                    GeminiService()

    def test_initialises_successfully_with_key(self):
        with patch("backend.services.gemini_service.genai.Client"):
            service = GeminiService()
            assert service is not None

    def test_search_products_returns_parsed_list(self):
        raw_response = json.dumps({"products": [{"name": "TV", "price_ron": 999}]})
        mock_response = MagicMock()
        mock_response.text = raw_response
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=100, candidates_token_count=200, thoughts_token_count=0
        )

        with patch("backend.services.gemini_service.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.return_value = mock_response
            service = GeminiService()
            result = service.search_products("some prompt")

        assert len(result) == 1
        assert result[0]["name"] == "TV"

    def test_search_products_wraps_unexpected_errors(self):
        with patch("backend.services.gemini_service.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.side_effect = RuntimeError("oops")
            service = GeminiService()
            with pytest.raises(GeminiServiceError):
                service.search_products("prompt")

    def test_search_products_reraises_gemini_error(self):
        with patch("backend.services.gemini_service.genai.Client") as MockClient:
            mock_response = MagicMock()
            mock_response.text = "not json"
            mock_response.usage_metadata = MagicMock(
                prompt_token_count=10, candidates_token_count=10, thoughts_token_count=0
            )
            MockClient.return_value.models.generate_content.return_value = mock_response
            service = GeminiService()
            with pytest.raises(GeminiServiceError):
                service.search_products("prompt")
