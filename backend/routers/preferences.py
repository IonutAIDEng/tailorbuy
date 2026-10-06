import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.preferences import PreferencesResponse, PreferencesUpdateRequest
from backend.services import preferences_service

router = APIRouter(prefix="/preferences", tags=["Preferences"])

_logger = logging.getLogger(__name__)


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
def get_preferences(user_id: int, db: Session = Depends(get_db)) -> PreferencesResponse:
    """Return current preferences for the given user, or defaults if none are saved."""
    return preferences_service.get_preferences(db, user_id)


@router.put("/{user_id}", status_code=status.HTTP_200_OK)
def update_preferences(
    user_id: int,
    request: PreferencesUpdateRequest,
    db: Session = Depends(get_db),
) -> PreferencesResponse:
    """Create or update preferences for the given user."""
    try:
        return preferences_service.update_preferences(db, user_id, request)
    except Exception as e:
        _logger.error("Failed to update preferences for user_id=%d: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Eroare la salvarea preferințelor.",
        )
