def test_get_preferences_defaults_for_new_user(auth_client, user):
    response = auth_client.get("/preferences")

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == user.id
    assert body["cash_only"] is False
    assert body["open_package"] is False
    assert body["min_rating"] == 0.0
    assert body["max_price"] is None
    assert body["min_review_count"] is None
    assert body["new_only"] is False
    assert body["search_emag"] is True
    assert body["search_altex"] is True


def test_get_preferences_returns_stored(auth_client, user, user_preference):
    response = auth_client.get("/preferences")

    assert response.status_code == 200
    body = response.json()
    assert body["cash_only"] is True
    assert body["min_rating"] == 4.0
    assert body["max_price"] == 1000


def test_put_preferences_creates(auth_client, user):
    payload = {
        "cash_only": True,
        "open_package": True,
        "min_rating": 4.5,
        "max_price": 3000,
    }
    response = auth_client.put("/preferences", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["cash_only"] is True
    assert body["min_rating"] == 4.5
    assert body["max_price"] == 3000


def test_put_preferences_updates_existing(auth_client, user, user_preference):
    payload = {
        "cash_only": False,
        "open_package": True,
        "min_rating": 0.0,
        "max_price": None,
    }
    response = auth_client.put("/preferences", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["cash_only"] is False
    assert body["max_price"] is None


def test_put_preferences_rejects_invalid_rating(auth_client, user):
    payload = {"cash_only": False, "open_package": False, "min_rating": 6.0, "max_price": None}
    response = auth_client.put("/preferences", json=payload)
    assert response.status_code == 422


def test_put_preferences_rejects_negative_max_price(auth_client, user):
    payload = {"cash_only": False, "open_package": False, "min_rating": 0.0, "max_price": -1}
    response = auth_client.put("/preferences", json=payload)
    assert response.status_code == 422


def test_put_preferences_saves_min_review_count(auth_client, user):
    payload = {"cash_only": False, "open_package": False, "min_rating": 0.0, "max_price": None,
               "min_review_count": 30, "new_only": False}
    response = auth_client.put("/preferences", json=payload)
    assert response.status_code == 200
    assert response.json()["min_review_count"] == 30


def test_put_preferences_saves_new_only(auth_client, user):
    payload = {"cash_only": False, "open_package": False, "min_rating": 0.0, "max_price": None,
               "min_review_count": None, "new_only": True}
    response = auth_client.put("/preferences", json=payload)
    assert response.status_code == 200
    assert response.json()["new_only"] is True


def test_put_preferences_rejects_negative_min_review_count(auth_client, user):
    payload = {"cash_only": False, "open_package": False, "min_rating": 0.0,
               "max_price": None, "min_review_count": -1, "new_only": False}
    response = auth_client.put("/preferences", json=payload)
    assert response.status_code == 422


def test_put_preferences_saves_emag_only(auth_client, user):
    payload = {"cash_only": False, "open_package": False, "min_rating": 0.0,
               "max_price": None, "min_review_count": None, "new_only": False,
               "search_emag": True, "search_altex": False}
    response = auth_client.put("/preferences", json=payload)
    assert response.status_code == 200
    assert response.json()["search_emag"] is True
    assert response.json()["search_altex"] is False


def test_put_preferences_returns_500_on_service_error(auth_client, user):
    from unittest.mock import patch
    with patch(
        "backend.routers.preferences.preferences_service.update_preferences",
        side_effect=Exception("db exploded"),
    ):
        payload = {"cash_only": False, "open_package": False, "min_rating": 0.0, "max_price": None}
        response = auth_client.put("/preferences", json=payload)

    assert response.status_code == 500
    assert "Eroare" in response.json()["detail"]
