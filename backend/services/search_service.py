import logging

from sqlalchemy.orm import Session

from backend.models import UserPreference
from backend.schemas.search import SearchRequest, SearchResponse, Product
from backend.services.gemini_service import GeminiService, GeminiServiceError
from backend.services.prompt_builder import build_search_prompt

_logger = logging.getLogger(__name__)


def search(db: Session, request: SearchRequest) -> SearchResponse:
    """
    Execute a product search using the user's query and stored preferences.

    Fetches the user's saved preferences from the database, builds an XML prompt,
    calls the Gemini API with Google Search grounding, applies deterministic filters,
    and returns a validated response.

    Args:
        db: Active SQLAlchemy database session.
        request: Search request containing user_id and natural language query.

    Returns:
        SearchResponse with filtered and sorted products.
    """
    _logger.info("Search started | user_id=%s query='%s'", request.user_id, request.query)

    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == request.user_id
    ).first()

    if preferences is None:
        _logger.warning("No preferences found for user_id=%s — search will run without filters", request.user_id)
    else:
        _logger.info("Preferences loaded for user_id=%s", request.user_id)

    prompt = build_search_prompt(query=request.query, preferences=preferences)
    try:
        gemini = GeminiService()
        raw_products = gemini.search_products(prompt)
    except GeminiServiceError as e:
        raise GeminiServiceError(f"Search failed for query '{request.query}': {str(e)}")

    _logger.info("Gemini returned %d raw products for query='%s'", len(raw_products), request.query)

    filtered = _apply_filters(raw_products, preferences)
    products = [Product(id=i + 1, **p) for i, p in enumerate(filtered)]

    _logger.info(
        "Search complete | user_id=%s query='%s' raw=%d filtered=%d",
        request.user_id, request.query, len(raw_products), len(products)
    )

    return SearchResponse(
        query=request.query,
        products=products,
        total=len(products)
    )


def _apply_filters(raw: list[dict], preferences: UserPreference | None) -> list[dict]:
    """
    Apply deterministic preference-based filters to raw product data.

    Filters by cash on delivery, minimum rating, and maximum price when the
    corresponding preferences are set. Results are sorted by rating descending.

    Args:
        raw: List of raw product dicts returned by the Gemini service.
        preferences: User's saved preferences, or None to skip all filtering.

    Returns:
        Filtered and sorted list of product dicts.
    """
    if not preferences:
        return raw

    result = raw

    if preferences.cash_only:
        result = [p for p in result if p.get("cash_on_delivery") is True]

    if preferences.min_rating:
        result = [p for p in result if p.get("rating", 0) >= preferences.min_rating]

    if preferences.max_price is not None:
        result = [p for p in result if p.get("price_ron", 0) <= preferences.max_price]

    return sorted(result, key=lambda p: p.get("rating", 0), reverse=True)