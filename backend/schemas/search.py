from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    user_id: int
    query: str = Field(min_length=3, max_length=200)


class Product(BaseModel):
    id: int
    name: str
    price_ron: float
    rating: float
    review_count: int
    cash_on_delivery: bool
    store: str
    url: str
    image_url: str | None


class SearchResponse(BaseModel):
    query: str
    products: list[Product]
    total: int