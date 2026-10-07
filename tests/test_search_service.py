from unittest.mock import MagicMock, patch

import pytest

from backend.models import UserPreference
from backend.schemas.search import SearchRequest
from backend.services import search_service
from backend.services.gemini_service import GeminiServiceError
from backend.services.search_service import _apply_filters


def make_pref(**kwargs):
    defaults = dict(cash_only=False, open_package=False, min_rating=0.0, max_price=None)
    defaults.update(kwargs)
    p = UserPreference()
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


def raw_product(**kwargs):
    defaults = dict(
        name="Test Product",
        price_ron=200.0,
        rating=4.5,
        review_count=10,
        cash_on_delivery=True,
        store="eMAG",
        url="https://example.com",
        image_url=None,
    )
    defaults.update(kwargs)
    return defaults


class TestApplyFilters:
    def test_no_preferences_returns_all(self):
        products = [raw_product(), raw_product(price_ron=999)]
        result = _apply_filters(products, None)
        assert len(result) == 2

    def test_cash_only_filters_non_cash(self):
        products = [
            raw_product(cash_on_delivery=True),
            raw_product(cash_on_delivery=False),
        ]
        pref = make_pref(cash_only=True)
        result = _apply_filters(products, pref)
        assert len(result) == 1
        assert result[0]["cash_on_delivery"] is True

    def test_min_rating_filters_low_rated(self):
        products = [raw_product(rating=4.8), raw_product(rating=3.0)]
        pref = make_pref(min_rating=4.5)
        result = _apply_filters(products, pref)
        assert len(result) == 1
        assert result[0]["rating"] == 4.8

    def test_max_price_filters_expensive(self):
        products = [raw_product(price_ron=100), raw_product(price_ron=500)]
        pref = make_pref(max_price=200)
        result = _apply_filters(products, pref)
        assert len(result) == 1
        assert result[0]["price_ron"] == 100

    def test_results_sorted_by_rating_descending(self):
        products = [
            raw_product(rating=3.0),
            raw_product(rating=4.9),
            raw_product(rating=4.5),
        ]
        result = _apply_filters(products, None)
        ratings = [p["rating"] for p in result]
        assert ratings == sorted(ratings, reverse=True)

    def test_combined_filters(self):
        products = [
            raw_product(cash_on_delivery=True, rating=4.8, price_ron=100),
            raw_product(cash_on_delivery=False, rating=4.8, price_ron=100),
            raw_product(cash_on_delivery=True, rating=4.8, price_ron=600),
        ]
        pref = make_pref(cash_only=True, max_price=500)
        result = _apply_filters(products, pref)
        assert len(result) == 1

    def test_missing_rating_treated_as_zero(self):
        products = [{"name": "X", "price_ron": 100, "cash_on_delivery": True, "store": "eMAG", "url": "u", "image_url": None}]
        pref = make_pref(min_rating=4.5)
        result = _apply_filters(products, pref)
        assert len(result) == 0


class TestSearch:
    def test_search_returns_response(self, db, user, user_preference):
        raw = [raw_product(cash_on_delivery=True, rating=4.5)]
        with patch("backend.services.search_service.GeminiService") as MockGemini:
            MockGemini.return_value.search_products.return_value = raw
            request = SearchRequest(user_id=user.id, query="canapea")
            response = search_service.search(db, request)

        assert response.query == "canapea"
        assert response.total == 1
        assert response.products[0].id == 1

    def test_search_assigns_sequential_ids(self, db, user, user_preference):
        raw = [raw_product(), raw_product(), raw_product()]
        with patch("backend.services.search_service.GeminiService") as MockGemini:
            MockGemini.return_value.search_products.return_value = raw
            request = SearchRequest(user_id=user.id, query="scaun")
            response = search_service.search(db, request)

        ids = [p.id for p in response.products]
        assert ids == [1, 2, 3]

    def test_search_without_preferences_still_works(self, db, user):
        raw = [raw_product()]
        with patch("backend.services.search_service.GeminiService") as MockGemini:
            MockGemini.return_value.search_products.return_value = raw
            request = SearchRequest(user_id=user.id, query="laptop")
            response = search_service.search(db, request)

        assert response.total == 1

    def test_search_propagates_gemini_error(self, db, user):
        with patch("backend.services.search_service.GeminiService") as MockGemini:
            MockGemini.return_value.search_products.side_effect = GeminiServiceError("fail")
            request = SearchRequest(user_id=user.id, query="masa")
            with pytest.raises(GeminiServiceError):
                search_service.search(db, request)
