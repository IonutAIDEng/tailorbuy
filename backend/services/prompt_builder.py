from backend.models import UserPreference


def build_search_prompt(query: str, preferences: UserPreference | None) -> str:
    """
    Build a structured XML prompt for a Gemini product search request.

    Args:
        query: Natural language search query entered by the user.
        preferences: User's saved preferences, or None if none are configured.

    Returns:
        Complete XML-structured prompt string ready to send to Gemini.
    """
    preferences_block = _build_preferences_block(preferences)

    return f"""
<role>
  You are a product search assistant specializing in Romanian e-commerce sites
  (eMAG, Altex, Media Galaxy, Cel.ro).
  Your goal is to find real, currently available products in Romania that best match
  the user's search query and preferences.
  Always search the web for actual products — never invent or hallucinate products.
</role>

{preferences_block}

<search_query>{query}</search_query>

<instructions>
  Search Romanian e-commerce sites for real products matching the search query.
  Return between 5 and 10 products.
  Prices must be in RON (Romanian Lei).
  Only include products currently available for purchase.
  If a product does not have a visible rating, set rating to 0.0 and review_count to 0.
  If image URL is not available, set image_url to null.
</instructions>

<output_schema>
  Return a valid JSON object with this exact structure and no extra text:
  {{
    "products": [
      {{
        "name": "product name",
        "price_ron": 149.99,
        "rating": 4.3,
        "review_count": 127,
        "cash_on_delivery": true,
        "store": "eMAG",
        "url": "https://...",
        "image_url": "https://..."
      }}
    ]
  }}
</output_schema>
""".strip()


def _build_preferences_block(preferences: UserPreference | None) -> str:
    """
    Render user preferences as an XML block for prompt injection.

    Args:
        preferences: User's saved preferences, or None to return an empty string.

    Returns:
        Formatted XML string with preference tags, or empty string if None.
    """
    if preferences is None:
        return ""

    max_price_tag = (
        f"  <max_price_ron>{preferences.max_price}</max_price_ron>"
        if preferences.max_price is not None
        else ""
    )

    return f"""
<user_preferences>
  <cash_on_delivery>{str(preferences.cash_only).lower()}</cash_on_delivery>
  <min_rating>{preferences.min_rating}</min_rating>
  <open_package>{str(preferences.open_package).lower()}</open_package>
{max_price_tag}
</user_preferences>
""".strip()
