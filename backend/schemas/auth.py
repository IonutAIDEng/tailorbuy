from pydantic import BaseModel, field_validator


class RegisterRequest(BaseModel):
    email: str
    password: str
    nickname: str | None = None

    @field_validator('email')
    @classmethod
    def email_valid(cls, v: str) -> str:
        v = v.lower().strip()
        parts = v.split('@')
        if len(parts) != 2 or '.' not in parts[1]:
            raise ValueError('Email invalid')
        return v

    @field_validator('password')
    @classmethod
    def password_strong_enough(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Parola trebuie să aibă cel puțin 8 caractere')
        return v

    @field_validator('nickname')
    @classmethod
    def nickname_valid(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 30:
            raise ValueError('Nickname prea lung (max 30 caractere)')
        return v or None  # treat empty string as None


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def email_normalise(cls, v: str) -> str:
        return v.lower().strip()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    id: int
    email: str
    nickname: str | None


class UpdateProfileRequest(BaseModel):
    email: str | None = None
    nickname: str | None = None

    @field_validator('email')
    @classmethod
    def email_valid(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.lower().strip()
        parts = v.split('@')
        if len(parts) != 2 or '.' not in parts[1]:
            raise ValueError('Email invalid')
        return v

    @field_validator('nickname')
    @classmethod
    def nickname_valid(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 30:
            raise ValueError('Nickname prea lung (max 30 caractere)')
        return v or None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def password_strong_enough(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Parola trebuie să aibă cel puțin 8 caractere')
        return v
