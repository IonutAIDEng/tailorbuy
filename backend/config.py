import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
if len(JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        f"JWT_SECRET_KEY is too short ({len(JWT_SECRET_KEY)} chars). "
        "HS256 requires at least 32 characters (256 bits). "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
