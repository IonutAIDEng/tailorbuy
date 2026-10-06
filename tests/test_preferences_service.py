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
