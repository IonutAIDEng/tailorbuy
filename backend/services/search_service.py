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
    message = _build_no_results_message(preferences) if not products else None

    _logger.info(
        "Search complete | user_id=%s query='%s' raw=%d filtered=%d",
        request.user_id, request.query, len(raw_products), len(products)
    )

    return SearchResponse(query=request.query, products=products, total=len(products), message=message)


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
    """Score products against Python-verifiable preferences and sort by best match.

    Products matching zero verifiable preferences are excluded. When no verifiable
    preferences are active (e.g. only new_only/open_package which Gemini enforces),
    all returned products are trusted and sorted by rating.
    Results are sorted by match score descending, then rating descending.
    """
    if preferences is None:
        return sorted(raw, key=lambda p: p.get("rating", 0), reverse=True)

    total_verifiable = _count_verifiable_preferences(preferences)
    if total_verifiable == 0:
        return sorted(raw, key=lambda p: p.get("rating", 0), reverse=True)

    scored = [(product, _compute_match_score(product, preferences)) for product in raw]
    qualifying = [(p, score) for p, score in scored if score > 0]
    qualifying.sort(key=lambda x: (x[1], x[0].get("rating", 0)), reverse=True)
    return [p for p, _ in qualifying]


def _count_verifiable_preferences(preferences: UserPreference) -> int:
    """Count how many preferences Python can verify against product data fields."""
    total = 0
    if preferences.cash_only:
        total += 1
    if preferences.min_rating and preferences.min_rating > 0:
        total += 1
    if preferences.max_price is not None:
        total += 1
    if preferences.min_review_count:
        total += 1
    return total


def _compute_match_score(product: dict, preferences: UserPreference) -> int:
    """Return how many Python-verifiable preferences this product satisfies."""
    score = 0
    if preferences.cash_only and product.get("cash_on_delivery") is True:
        score += 1
    if preferences.min_rating and preferences.min_rating > 0 and product.get("rating", 0) >= preferences.min_rating:
        score += 1
    if preferences.max_price is not None and product.get("price_ron", 0) <= preferences.max_price:
        score += 1
    if preferences.min_review_count and product.get("review_count", 0) >= preferences.min_review_count:
        score += 1
    return score


def _build_no_results_message(preferences: UserPreference | None) -> str:
    """Build a Romanian message explaining which preferences were active when no results were found."""
    if preferences is None:
        return "Niciun produs găsit."

    active = []
    if preferences.cash_only:
        active.append("plată la livrare (ramburs)")
    if preferences.min_rating and preferences.min_rating > 0:
        active.append(f"rating minim {preferences.min_rating}★")
    if preferences.max_price is not None:
        active.append(f"preț maxim {preferences.max_price} RON")
    if preferences.min_review_count:
        active.append(f"minim {preferences.min_review_count} recenzii")
    if preferences.new_only:
        active.append("doar produse noi")
    if preferences.open_package:
        active.append("deschidere colet")

    stores = []
    if preferences.search_emag:
        stores.append("eMAG")
    if preferences.search_altex:
        stores.append("Altex")

    pref_str = ", ".join(active) if active else "fără filtre specifice"
    store_str = " și ".join(stores) if stores else "eMAG și Altex"

    return (
        f"Niciun produs găsit cu preferințele selectate: {pref_str}. "
        f"Magazine căutate: {store_str}. "
        f"Încearcă să relaxezi preferințele pentru mai multe rezultate."
    )
