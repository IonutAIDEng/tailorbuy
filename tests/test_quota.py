"""Tests for daily search quota logic."""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from backend.constants import DAILY_SEARCH_LIMIT
from backend.exceptions import SearchQuotaExceededError
from backend.services.search_service import _check_and_increment_quota


class TestCheckAndIncrementQuota:
    def test_increments_counter_on_first_search(self, db, user):
        _check_and_increment_quota(db, user.id)
        db.refresh(user)
        assert user.searches_today == 1

    def test_increments_counter_on_subsequent_searches(self, db, user):
        _check_and_increment_quota(db, user.id)
        _check_and_increment_quota(db, user.id)
        db.refresh(user)
        assert user.searches_today == 2

    def test_sets_last_search_date_to_today(self, db, user):
        _check_and_increment_quota(db, user.id)
        db.refresh(user)
        assert user.last_search_date == date.today()

    def test_allows_search_at_limit_minus_one(self, db, user):
        user.searches_today = DAILY_SEARCH_LIMIT - 1
        user.last_search_date = date.today()
        db.commit()
        _check_and_increment_quota(db, user.id)
        db.refresh(user)
        assert user.searches_today == DAILY_SEARCH_LIMIT

    def test_raises_when_daily_limit_reached(self, db, user):
        user.searches_today = DAILY_SEARCH_LIMIT
        user.last_search_date = date.today()
        db.commit()
        with pytest.raises(SearchQuotaExceededError):
            _check_and_increment_quota(db, user.id)

    def test_counter_does_not_increment_when_limit_exceeded(self, db, user):
        user.searches_today = DAILY_SEARCH_LIMIT
        user.last_search_date = date.today()
        db.commit()
        with pytest.raises(SearchQuotaExceededError):
            _check_and_increment_quota(db, user.id)
        db.refresh(user)
        assert user.searches_today == DAILY_SEARCH_LIMIT

    def test_resets_counter_on_new_day(self, db, user):
        yesterday = date.today() - timedelta(days=1)
        user.searches_today = DAILY_SEARCH_LIMIT
        user.last_search_date = yesterday
        db.commit()
        _check_and_increment_quota(db, user.id)
        db.refresh(user)
        assert user.searches_today == 1
        assert user.last_search_date == date.today()

    def test_resets_counter_when_last_date_is_none(self, db, user):
        user.searches_today = 5
        user.last_search_date = None
        db.commit()
        _check_and_increment_quota(db, user.id)
        db.refresh(user)
        assert user.searches_today == 1

    def test_raises_value_error_for_unknown_user_id(self, db):
        with pytest.raises(ValueError, match="user_id=999 not found"):
            _check_and_increment_quota(db, 999)

    @pytest.mark.parametrize("count", [0, 1, DAILY_SEARCH_LIMIT - 2, DAILY_SEARCH_LIMIT - 1])
    def test_does_not_raise_below_limit(self, db, user, count):
        user.searches_today = count
        user.last_search_date = date.today()
        db.commit()
        _check_and_increment_quota(db, user.id)


class TestSearchEndpointQuota:
    def test_returns_429_when_quota_exceeded(self, auth_client, db, user):
        user.searches_today = DAILY_SEARCH_LIMIT
        user.last_search_date = date.today()
        db.commit()
        response = auth_client.post("/search", json={"query": "laptop gaming"})
        assert response.status_code == 429
        assert response.json()["detail"]["code"] == "quota_exceeded"

    def test_quota_error_message_is_in_romanian(self, auth_client, db, user):
        user.searches_today = DAILY_SEARCH_LIMIT
        user.last_search_date = date.today()
        db.commit()
        response = auth_client.post("/search", json={"query": "laptop gaming"})
        assert "message" in response.json()["detail"]

    def test_search_succeeds_before_limit_is_reached(self, auth_client, db, user, user_preference):
        user.searches_today = DAILY_SEARCH_LIMIT - 1
        user.last_search_date = date.today()
        db.commit()
        raw = [{"name": "TV", "price_ron": 500, "rating": 4.5, "review_count": 10,
                "cash_on_delivery": True, "store": "eMAG", "url": "http://x.com", "image_url": None}]
        with patch("backend.services.search_service.GeminiService") as MockGemini:
            MockGemini.return_value.search_products.return_value = raw
            response = auth_client.post("/search", json={"query": "televizor smart"})
        assert response.status_code == 200
