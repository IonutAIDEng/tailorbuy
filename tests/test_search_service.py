from unittest.mock import MagicMock, patch

import pytest

from backend.models import UserPreference
from backend.services import search_service
from backend.services.gemini_service import GeminiServiceError
from backend.services.search_service import _apply_filters, _compute_match_score, _build_no_results_message


def make_pref(**kwargs):
    defaults = dict(cash_only=False, open_package=False, min_rating=0.0, max_price=None,
                    min_review_count=None, new_only=False, search_emag=True, search_altex=True)
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

    def test_full_match_appears_before_partial_match(self):
        full = raw_product(cash_on_delivery=True, rating=4.0, price_ron=100)
        partial_cash = raw_product(cash_on_delivery=False, rating=4.9, price_ron=100)
        partial_price = raw_product(cash_on_delivery=True, rating=4.9, price_ron=600)
        pref = make_pref(cash_only=True, max_price=500)
        result = _apply_filters([full, partial_cash, partial_price], pref)
        assert len(result) == 3
        assert result[0] == full

    def test_zero_match_product_excluded(self):
        zero_match = raw_product(cash_on_delivery=False, price_ron=600)
        some_match = raw_product(cash_on_delivery=True, price_ron=600)
        pref = make_pref(cash_only=True, max_price=500)
        result = _apply_filters([zero_match, some_match], pref)
        assert zero_match not in result
        assert some_match in result

    def test_missing_rating_treated_as_zero(self):
        products = [{"name": "X", "price_ron": 100, "cash_on_delivery": True, "store": "eMAG", "url": "u", "image_url": None}]
        pref = make_pref(min_rating=4.5)
        result = _apply_filters(products, pref)
        assert len(result) == 0

    def test_min_review_count_filters_low_review_products(self):
        products = [raw_product(review_count=50), raw_product(review_count=5)]
        pref = make_pref(min_review_count=10)
        result = _apply_filters(products, pref)
        assert len(result) == 1
        assert result[0]["review_count"] == 50

    def test_min_review_count_none_does_not_filter(self):
        products = [raw_product(review_count=0), raw_product(review_count=100)]
        pref = make_pref(min_review_count=None)
        result = _apply_filters(products, pref)
        assert len(result) == 2

    def test_min_review_count_exact_threshold_passes(self):
        products = [raw_product(review_count=10)]
        pref = make_pref(min_review_count=10)
        result = _apply_filters(products, pref)
        assert len(result) == 1

    def test_missing_review_count_treated_as_zero(self):
        products = [{"name": "X", "price_ron": 100, "cash_on_delivery": True, "store": "eMAG",
                     "url": "u", "image_url": None, "rating": 4.0}]
        pref = make_pref(min_review_count=5)
        result = _apply_filters(products, pref)
        assert len(result) == 0

    def test_prompt_only_preferences_trust_gemini(self):
        products = [raw_product(), raw_product(rating=3.0)]
        pref = make_pref(new_only=True, open_package=False)
        result = _apply_filters(products, pref)
        assert len(result) == 2

    def test_compute_match_score_all_satisfied(self):
        product = raw_product(cash_on_delivery=True, rating=4.8, price_ron=200, review_count=20)
        pref = make_pref(cash_only=True, min_rating=4.5, max_price=500, min_review_count=10)
        assert _compute_match_score(product, pref) == 4

    def test_compute_match_score_none_satisfied(self):
        product = raw_product(cash_on_delivery=False, rating=3.0, price_ron=600, review_count=2)
        pref = make_pref(cash_only=True, min_rating=4.5, max_price=500, min_review_count=10)
        assert _compute_match_score(product, pref) == 0


class TestNoResultsMessage:
    def test_message_includes_active_preferences(self):
        pref = make_pref(cash_only=True, min_rating=4.5, max_price=500)
        msg = _build_no_results_message(pref)
        assert "ramburs" in msg
        assert "4.5" in msg
        assert "500" in msg

    def test_message_includes_store_names(self):
        pref = make_pref(search_emag=True, search_altex=False)
        msg = _build_no_results_message(pref)
        assert "eMAG" in msg
        assert "Altex" not in msg

    def test_message_both_stores_when_both_selected(self):
        pref = make_pref(search_emag=True, search_altex=True)
        msg = _build_no_results_message(pref)
        assert "eMAG" in msg
        assert "Altex" in msg

    def test_message_none_preferences(self):
        msg = _build_no_results_message(None)
        assert "Niciun produs" in msg

    def test_message_includes_new_only(self):
        pref = make_pref(new_only=True)
        msg = _build_no_results_message(pref)
        assert "noi" in msg

    def test_message_includes_open_package(self):
        pref = make_pref(open_package=True)
        msg = _build_no_results_message(pref)
        assert "deschidere colet" in msg

    def test_message_includes_min_review_count(self):
        pref = make_pref(min_review_count=50)
        msg = _build_no_results_message(pref)
        assert "50" in msg
        assert "recenzii" in msg

    def test_message_only_altex_when_emag_disabled(self):
        pref = make_pref(search_emag=False, search_altex=True)
        msg = _build_no_results_message(pref)
        assert "Altex" in msg
        assert "eMAG" not in msg


class TestSearch:
    def test_search_returns_response(self, db, user, user_preference):
        raw = [raw_product(cash_on_delivery=True, rating=4.5)]
        with patch("backend.services.search_service.GeminiService") as MockGemini:
            MockGemini.return_value.search_products.return_value = raw
            response = search_service.search(db, user.id, "canapea")

        assert response.query == "canapea"
        assert response.total == 1
        assert response.products[0].id == 1

    def test_search_assigns_sequential_ids(self, db, user, user_preference):
        raw = [raw_product(), raw_product(), raw_product()]
        with patch("backend.services.search_service.GeminiService") as MockGemini:
            MockGemini.return_value.search_products.return_value = raw
            response = search_service.search(db, user.id, "scaun")

        ids = [p.id for p in response.products]
        assert ids == [1, 2, 3]

    def test_search_without_preferences_still_works(self, db, user):
        raw = [raw_product()]
        with patch("backend.services.search_service.GeminiService") as MockGemini:
            MockGemini.return_value.search_products.return_value = raw
            response = search_service.search(db, user.id, "laptop")

        assert response.total == 1

    def test_search_propagates_gemini_error(self, db, user):
        with patch("backend.services.search_service.GeminiService") as MockGemini:
            MockGemini.return_value.search_products.side_effect = GeminiServiceError("fail")
            with pytest.raises(GeminiServiceError):
                search_service.search(db, user.id, "masa")
