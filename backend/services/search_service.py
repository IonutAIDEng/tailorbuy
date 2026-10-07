import logging
from datetime import date

from sqlalchemy.orm import Session

from backend.constants import DAILY_SEARCH_LIMIT
from backend.exceptions import SearchQuotaExceededError
from backend.models import User, UserPreference
from backend.schemas.search import SearchRequest, SearchResponse, Product
from backend.services.gemini_service import GeminiService, GeminiServiceError
from backend.services.prompt_builder import build_search_prompt

_logger = logging.getLogger(__name__)


def search(db: Session, request: SearchRequest) -> SearchResponse:
    """Run a quota-checked, preference-filtered product search via Gemini."""
    _logger.info("Search started | user_id=%s query='%s'", request.user_id, request.query)

    _check_and_increment_quota(db, request.user_id)

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

    return SearchResponse(query=request.query, products=products, total=len(products))


def _check_and_increment_quota(db: Session, user_id: int) -> None:
    """Enforce the daily search limit, resetting the counter at the start of each new day.

    Raises:
        ValueError: if the user does not exist.
        SearchQuotaExceededError: if the user has reached DAILY_SEARCH_LIMIT today.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise ValueError(f"user_id={user_id} not found")

    today = date.today()
    if user.last_search_date != today:
        user.searches_today = 0
        user.last_search_date = today

    if user.searches_today >= DAILY_SEARCH_LIMIT:
        _logger.warning("Daily quota exceeded | user_id=%s searches_today=%s", user_id, user.searches_today)
        raise SearchQuotaExceededError(
            f"Daily search limit of {DAILY_SEARCH_LIMIT} reached for user_id={user_id}"
        )

    user.searches_today += 1
    db.commit()
    _logger.debug("Quota incremented | user_id=%s searches_today=%s", user_id, user.searches_today)


def _apply_filters(raw: list[dict], preferences: UserPreference | None) -> list[dict]:
    """Filter raw Gemini products by user preferences and sort by rating descending."""
    result = raw

    if preferences is None:
        return sorted(result, key=lambda p: p.get("rating", 0), reverse=True)

    if preferences.cash_only:
        result = [p for p in result if p.get("cash_on_delivery") is True]

    if preferences.min_rating:
        result = [p for p in result if p.get("rating", 0) >= preferences.min_rating]

    if preferences.max_price is not None:
        result = [p for p in result if p.get("price_ron", 0) <= preferences.max_price]

    return sorted(result, key=lambda p: p.get("rating", 0), reverse=True)
