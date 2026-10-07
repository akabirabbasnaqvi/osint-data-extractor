from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import main
from db import get_db


def _client(db) -> TestClient:
    main.app.dependency_overrides[get_db] = lambda: db
    return TestClient(main.app)


def teardown_function() -> None:
    main.app.dependency_overrides.clear()


def test_liveness_does_not_touch_the_database() -> None:
    assert TestClient(main.app).get("/api/health").json() == {"status": "ok"}


def test_readiness_is_ok_when_the_database_answers() -> None:
    res = _client(MagicMock()).get("/api/health/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ready"}


def test_readiness_is_503_when_the_database_is_down() -> None:
    db = MagicMock()
    db.execute.side_effect = ConnectionError("postgres down")
    res = _client(db).get("/api/health/ready")
    assert res.status_code == 503
