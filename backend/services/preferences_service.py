import logging

from sqlalchemy.orm import Session

from backend.models import UserPreference
from backend.schemas.preferences import PreferencesResponse, PreferencesUpdateRequest

_logger = logging.getLogger(__name__)

_RATING_THRESHOLD = 4.5


def get_preferences(db: Session, user_id: int) -> PreferencesResponse:
    """
    Return the stored preferences for a user, or safe defaults if none exist.

    Args:
        db: Active SQLAlchemy database session.
        user_id: Target user identifier.

    Returns:
        PreferencesResponse with current or default values.
    """
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if prefs is None:
        _logger.info("No preferences found for user_id=%d — returning defaults", user_id)
        return _default_response(user_id)

    _logger.info("Preferences loaded for user_id=%d", user_id)
    return PreferencesResponse(
        user_id=user_id,
        cash_only=bool(prefs.cash_only),
        open_package=bool(prefs.open_package),
        min_rating=float(prefs.min_rating or 0.0),
        max_price=prefs.max_price,
    )


def update_preferences(db: Session, user_id: int, data: PreferencesUpdateRequest) -> PreferencesResponse:
    """
    Create or update preferences for a user (upsert).

    Args:
        db: Active SQLAlchemy database session.
        user_id: Target user identifier.
        data: New preference values to persist.

    Returns:
        PreferencesResponse reflecting the saved state.
    """
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if prefs is None:
        prefs = UserPreference(user_id=user_id)
        db.add(prefs)
        _logger.info("Creating preferences for user_id=%d", user_id)
    else:
        _logger.info("Updating preferences for user_id=%d", user_id)

    prefs.cash_only = data.cash_only
    prefs.open_package = data.open_package
    prefs.min_rating = data.min_rating
    prefs.max_price = data.max_price

    db.commit()
    db.refresh(prefs)

    return PreferencesResponse(
        user_id=user_id,
        cash_only=bool(prefs.cash_only),
        open_package=bool(prefs.open_package),
        min_rating=float(prefs.min_rating or 0.0),
        max_price=prefs.max_price,
    )


def _default_response(user_id: int) -> PreferencesResponse:
    return PreferencesResponse(
        user_id=user_id,
        cash_only=False,
        open_package=False,
        min_rating=0.0,
        max_price=None,
    )
