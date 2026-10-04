import json
import os
import re
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_MODEL_NAME = "gemini-1.5-flash"


class GeminiServiceError(Exception):
    pass


class GeminiService:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise GeminiServiceError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self._model = self._build_model()

    def _build_model(self) -> genai.GenerativeModel:
        search_tool = genai.protos.Tool(
            google_search_retrieval=genai.protos.GoogleSearchRetrieval()
        )
        return genai.GenerativeModel(
            model_name=_MODEL_NAME,
            tools=[search_tool]
        )

    def search_products(self, prompt: str) -> list[dict]:
        try:
            response = self._model.generate_content(contents=prompt)
            return self._parse_response(response.text)
        except GeminiServiceError:
            raise
        except Exception as e:
            raise GeminiServiceError(f"Gemini API call failed: {str(e)}") from e

    def _parse_response(self, raw_text: str) -> list[dict]:
        cleaned = re.sub(r"```json\s*|\s*```", "", raw_text).strip()
        try:
            data = json.loads(cleaned)
            return data.get("products", [])
        except json.JSONDecodeError as e:
            raise GeminiServiceError(f"Failed to parse Gemini response as JSON: {str(e)}") from e
