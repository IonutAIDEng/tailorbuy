from dataclasses import dataclass


@dataclass(frozen=True)
class GeminiModelPricing:
    """Per-million-token USD prices for a Gemini model."""
    input: float
    output: float
    thinking: float = 0.0


GEMINI_MODEL_PRICING: dict[str, GeminiModelPricing] = {
    "gemini-3.8-flash": GeminiModelPricing(input=0.75, output=3.75),
    "gemini-2.5-flash": GeminiModelPricing(input=0.15, output=0.60),
}

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_MAX_WAIT_SECONDS = 60

DAILY_SEARCH_LIMIT = 10

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
JWT_ALGORITHM = "HS256"
