from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.services.auth_service import verify_access_token

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency that validates the JWT and returns the authenticated User.

    Raises 401 if the token is missing, expired, or invalid.
    Raises 403 if the account exists but has been deactivated.
    """
    payload = verify_access_token(credentials.credentials)

    user_id = int(payload["sub"])
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Utilizator inexistent",
                            headers={"WWW-Authenticate": "Bearer"})

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Cont dezactivat")

    return user
