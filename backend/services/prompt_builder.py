from backend.models import UserPreference


def build_search_prompt(query: str, preferences: UserPreference | None) -> str:
    search_block = _build_search_block(query, preferences)
    hard_filters_block = _build_hard_filters_block(preferences)
    preferences_block = _build_preferences_block(preferences)

    return f"""
<role>
  You are a product search engine for Romanian e-commerce.
  Your job is to find products matching the user's query that also satisfy the user's
  preferences. Return products sorted by how well they match: products satisfying ALL
  preferences first, then products satisfying MOST, then partial matches.
  Do NOT return products that clearly satisfy NONE of the user's preferences.
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
    Include products that fully OR partially match preferences — ranked best match first.
    Do NOT return products that satisfy zero preferences.
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
    if preferences and preferences.open_package:
        extra += ' "deschidere colet"'
    if preferences and preferences.new_only:
        extra += " -resigilat -reconditionat"

    search_emag = not preferences or preferences.search_emag
    search_altex = not preferences or preferences.search_altex
    if not search_emag and not search_altex:
        search_emag = True
        search_altex = True

    queries = []
    if search_emag:
        queries.append(f"site:emag.ro {query}{extra}")
    if search_altex:
        queries.append(f"site:altex.ro {query}{extra}")

    query_lines = "\n    - ".join(queries)
    return f"""
    Run these targeted Google Search queries:
    - {query_lines}"""


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
            '    d) Deschidere colet: keep only listings that explicitly offer '
            '"deschidere colet" delivery — the courier waits while the buyer '
            'inspects the product and can return it on the spot if unsatisfied.'
        )

    if preferences.new_only:
        lines.append(
            '    e) New only: discard any listing marked as "resigilat", "reconditionat", '
            '"open box", or "second hand".'
        )

    if preferences.min_review_count:
        lines.append(
            f'    f) Minimum reviews: discard if review_count < {preferences.min_review_count}.'
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

    min_review_tag = (
        f"  <min_review_count>{preferences.min_review_count}</min_review_count>"
        if preferences.min_review_count
        else ""
    )

    stores = []
    if preferences.search_emag:
        stores.append("eMAG")
    if preferences.search_altex:
        stores.append("Altex")
    store_str = ", ".join(stores) if stores else "eMAG, Altex"

    return f"""
<user_preferences>
  <cash_on_delivery>{str(preferences.cash_only).lower()}</cash_on_delivery>
  <min_rating>{preferences.min_rating}</min_rating>
  <open_package>{str(preferences.open_package).lower()}</open_package>
  <new_only>{str(preferences.new_only).lower()}</new_only>
  <search_stores>{store_str}</search_stores>
{max_price_tag}
{min_review_tag}
</user_preferences>
""".strip()
