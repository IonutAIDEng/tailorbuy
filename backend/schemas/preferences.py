from pydantic import BaseModel, Field


class PreferencesResponse(BaseModel):
    user_id: int
    cash_only: bool
    open_package: bool
    min_rating: float
    max_price: int | None
    min_review_count: int | None
    new_only: bool
    search_emag: bool
    search_altex: bool


class PreferencesUpdateRequest(BaseModel):
    cash_only: bool = False
    open_package: bool = False
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    max_price: int | None = Field(default=None, ge=0)
    min_review_count: int | None = Field(default=None, ge=0)
    new_only: bool = False
    search_emag: bool = True
    search_altex: bool = True
