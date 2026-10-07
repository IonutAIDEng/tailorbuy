from unittest.mock import MagicMock, patch


def test_get_db_yields_session_and_closes():
    mock_session = MagicMock()

    with patch("backend.database.SessionLocal", return_value=mock_session):
        from backend.database import get_db
        gen = get_db()
        session = next(gen)
        assert session is mock_session
        try:
            next(gen)
        except StopIteration:
            pass

    mock_session.close.assert_called_once()


def test_get_db_closes_on_exception():
    mock_session = MagicMock()

    with patch("backend.database.SessionLocal", return_value=mock_session):
        from backend.database import get_db
        gen = get_db()
        next(gen)
        try:
            gen.throw(RuntimeError("simulated error"))
        except RuntimeError:
            pass

    mock_session.close.assert_called_once()
