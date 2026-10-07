from backend.models import UserPreference


def build_search_prompt(query: str, preferences: UserPreference | None) -> str:
    search_block = _build_search_block(query, preferences)
    hard_filters_block = _build_hard_filters_block(preferences)
    preferences_block = _build_preferences_block(preferences)

    return f"""
<role>
  You are a precise product search engine for Romanian e-commerce.
  You ONLY report products you have directly observed in search results.
  You NEVER invent, guess, or extrapolate any product detail.
</role>

{preferences_block}

<search_query>{query}</search_query>

<pipeline>
  Execute the steps below in strict order. Each step reduces the candidate set
  before the next step runs — this is intentional for efficiency.

  STEP 1 — SEARCH (gather candidates)
{search_block}
    Collect up to 25 product candidates across all queries.
    If a product appears in multiple stores, treat each store listing separately.

  STEP 2 — HARD FILTER (eliminate immediately, no ranking needed yet)
    Discard any candidate that fails ANY of the following:
    a) Availability: product must be in stock and purchasable right now.
       Discard if page shows: "indisponibil", "stoc epuizat",
       "nu mai face parte din oferta", or any equivalent out-of-stock signal.
{hard_filters_block}
    After this step you should have a smaller set of qualifying candidates.

  STEP 3 — RANK (sort qualifying candidates, best first)
    Sort the surviving candidates using these criteria in order:
    1. PRIMARY: rating descending (higher rating = better)
    2. SECONDARY: review_count descending (more reviews = higher confidence)
    3. TERTIARY: price ascending (cheaper wins ties)
    A product with rating 4.8 and 50 reviews ranks above one with 4.8 and 5 reviews.
    A product with 0 reviews should rank last unless nothing else qualifies.

  STEP 4 — SELECT
    Take the top 5 to 10 candidates from the ranked list.
    Prefer fewer high-quality results over many mediocre ones.

  STEP 5 — OUTPUT
    Format the selected candidates as JSON per the schema below.
    Rules for missing data:
    - Rating not visible → rating: 0.0, review_count: 0
    - Image not visible → image_url: null
    - Price must be in RON. If shown in EUR, convert using 1 EUR = 5 RON.
    - URL must be the direct product page URL, not a search results page.
    - cash_on_delivery: true only if the listing explicitly shows "ramburs" or
      "plata la livrare" as an available payment method.
</pipeline>

<output_schema>
  Return ONLY valid JSON. No prose, no explanation, no markdown fences.
  {{
    "products": [
      {{
        "name": "exact product name as shown on the site",
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


def _build_search_block(query: str, preferences: UserPreference | None) -> str:
    extra = ""
    if preferences and preferences.cash_only:
        extra = ' "plata ramburs"'

    return f"""
    Run these targeted Google Search queries:
    - site:emag.ro {query}{extra}
    - site:altex.ro {query}{extra}"""


def _build_hard_filters_block(preferences: UserPreference | None) -> str:
    if preferences is None:
        return ""

    lines = []

    if preferences.cash_only:
        lines.append(
            '    b) Cash on delivery: discard if listing does NOT explicitly offer '
            '"ramburs" or "plata la livrare".'
        )

    if preferences.min_rating and preferences.min_rating > 0:
        lines.append(
            f'    b) Minimum rating: discard if rating < {preferences.min_rating}.'
        )

    if preferences.max_price is not None:
        lines.append(
            f'    c) Maximum price: discard if price_ron > {preferences.max_price}.'
        )

    if preferences.open_package:
        lines.append(
            '    d) Open package: keep only listings explicitly marked as '
            '"open box", "resigilat", or "reconditionat".'
        )

    return "\n".join(lines)


def _build_preferences_block(preferences: UserPreference | None) -> str:
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
