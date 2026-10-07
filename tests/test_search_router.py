from unittest.mock import patch

from backend.schemas.search import SearchResponse, Product
from backend.services.gemini_service import GeminiServiceError


def make_product(**kwargs):
    defaults = dict(
        id=1, name="Test", price_ron=100.0, rating=4.5, review_count=5,
        cash_on_delivery=True, store="eMAG", url="https://example.com", image_url=None,
    )
    defaults.update(kwargs)
    return Product(**defaults)


def test_search_returns_200_on_success(client, user):
    mock_response = SearchResponse(query="canapea", products=[make_product()], total=1)
    with patch("backend.routers.search.search_service.search", return_value=mock_response):
        response = client.post("/search", json={"user_id": user.id, "query": "canapea"})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "canapea"
    assert body["total"] == 1


def test_search_returns_500_on_gemini_error(client, user):
    with patch("backend.routers.search.search_service.search", side_effect=GeminiServiceError("fail")):
        response = client.post("/search", json={"user_id": user.id, "query": "laptop"})

    assert response.status_code == 500
    assert "Eroare" in response.json()["detail"]


def test_search_rejects_short_query(client, user):
    response = client.post("/search", json={"user_id": user.id, "query": "ab"})
    assert response.status_code == 422


def test_search_rejects_too_long_query(client, user):
    response = client.post("/search", json={"user_id": user.id, "query": "x" * 201})
    assert response.status_code == 422


def test_search_accepts_minimum_length_query(client, user):
    mock_response = SearchResponse(query="abc", products=[], total=0)
    with patch("backend.routers.search.search_service.search", return_value=mock_response):
        response = client.post("/search", json={"user_id": user.id, "query": "abc"})
    assert response.status_code == 200


def test_search_rejects_missing_user_id(client):
    response = client.post("/search", json={"query": "laptop"})
    assert response.status_code == 422


def test_search_rejects_missing_query(client, user):
    response = client.post("/search", json={"user_id": user.id})
    assert response.status_code == 422
