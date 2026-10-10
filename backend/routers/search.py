import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.exceptions import SearchQuotaExceededError
from backend.limiter import limiter
from backend.models import User
from backend.schemas.search import SearchRequest, SearchResponse
from backend.services import search_service
from backend.services.gemini_service import GeminiServiceError

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def search_products(
    request: Request,
    body: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """Search for products using the authenticated user's preferences and quota."""
    try:
        return search_service.search(db, current_user.id, body.query)
    except SearchQuotaExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "quota_exceeded", "message": "Ai atins limita zilnică de căutări. Revino mâine."},
        )
    except GeminiServiceError as e:
        _logger.error("Gemini search failed for query '%s': %s", body.query, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Eroare la căutarea produselor."
        )
