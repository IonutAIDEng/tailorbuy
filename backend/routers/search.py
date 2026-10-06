import logging

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.search import SearchRequest, SearchResponse
from backend.services import search_service
from backend.services.gemini_service import GeminiServiceError

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", status_code=status.HTTP_200_OK)
async def search_products(request: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    try:
        return search_service.search(db, request)
    except GeminiServiceError as e:
        _logger.error("Gemini search failed for query '%s': %s", request.query, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Eroare la căutarea produselor."
        )