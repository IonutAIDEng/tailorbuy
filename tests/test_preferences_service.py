import pytest

from backend.schemas.preferences import PreferencesUpdateRequest
from backend.services.preferences_service import get_preferences, update_preferences


def test_get_preferences_returns_defaults_when_none_exist(db, user):
    result = get_preferences(db, user.id)

    assert result.user_id == user.id
    assert result.cash_only is False
    assert result.open_package is False
    assert result.min_rating == 0.0
    assert result.max_price is None
    assert result.min_review_count is None
    assert result.new_only is False
    assert result.search_emag is True
    assert result.search_altex is True


def test_get_preferences_returns_stored_values(db, user_preference, user):
    result = get_preferences(db, user.id)

    assert result.cash_only is True
    assert result.open_package is False
    assert result.min_rating == 4.0
    assert result.max_price == 1000


def test_update_preferences_creates_new_record(db, user):
    data = PreferencesUpdateRequest(
        cash_only=True,
        open_package=True,
        min_rating=4.5,
        max_price=2000,
    )
    result = update_preferences(db, user.id, data)

    assert result.cash_only is True
    assert result.open_package is True
    assert result.min_rating == 4.5
    assert result.max_price == 2000


def test_update_preferences_overwrites_existing(db, user, user_preference):
    data = PreferencesUpdateRequest(
        cash_only=False,
        open_package=True,
        min_rating=0.0,
        max_price=None,
    )
    result = update_preferences(db, user.id, data)

    assert result.cash_only is False
    assert result.open_package is True
    assert result.min_rating == 0.0
    assert result.max_price is None


def test_update_preferences_with_zero_max_price(db, user):
    data = PreferencesUpdateRequest(cash_only=False, open_package=False, min_rating=0.0, max_price=0)
    result = update_preferences(db, user.id, data)
    assert result.max_price == 0


@pytest.mark.parametrize("min_rating", [0.0, 2.5, 4.5, 5.0])
def test_update_preferences_various_ratings(db, user, min_rating):
    data = PreferencesUpdateRequest(cash_only=False, open_package=False, min_rating=min_rating, max_price=None)
    result = update_preferences(db, user.id, data)
    assert result.min_rating == min_rating


def test_update_preferences_saves_min_review_count(db, user):
    data = PreferencesUpdateRequest(min_review_count=25)
    result = update_preferences(db, user.id, data)
    assert result.min_review_count == 25


def test_update_preferences_saves_new_only(db, user):
    data = PreferencesUpdateRequest(new_only=True)
    result = update_preferences(db, user.id, data)
    assert result.new_only is True


def test_update_preferences_clears_min_review_count(db, user, user_preference):
    data = PreferencesUpdateRequest(min_review_count=None)
    result = update_preferences(db, user.id, data)
    assert result.min_review_count is None


def test_update_preferences_saves_emag_only(db, user):
    data = PreferencesUpdateRequest(search_emag=True, search_altex=False)
    result = update_preferences(db, user.id, data)
    assert result.search_emag is True
    assert result.search_altex is False


def test_update_preferences_saves_altex_only(db, user):
    data = PreferencesUpdateRequest(search_emag=False, search_altex=True)
    result = update_preferences(db, user.id, data)
    assert result.search_emag is False
    assert result.search_altex is True
