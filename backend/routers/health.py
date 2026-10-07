from fastapi import APIRouter, status

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """
    Verify that the API is running and reachable.

    Returns:
        JSON object with status and a user-facing confirmation message.
    """
    return {"status": "ok", "message": "Aplicația funcționează."}