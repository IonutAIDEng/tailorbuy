import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User
from backend.schemas.preferences import PreferencesResponse, PreferencesUpdateRequest
from backend.services import preferences_service

router = APIRouter(prefix="/preferences", tags=["Preferences"])

_logger = logging.getLogger(__name__)


@router.get("", status_code=status.HTTP_200_OK)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferencesResponse:
    """Return current preferences for the given user, or defaults if none are saved."""
    return preferences_service.get_preferences(db, current_user.id)


@router.put("", status_code=status.HTTP_200_OK)
def update_preferences(
    request: PreferencesUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferencesResponse:
    """Create or update preferences for the given user."""
    try:
        return preferences_service.update_preferences(db, current_user.id, request)
    except Exception as e:
        _logger.error("Failed to update preferences for user_id=%d: %s", current_user.id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Eroare la salvarea preferințelor.",
        )
