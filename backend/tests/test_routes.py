"""
Route-level tests with a fake DB session -- no Postgres, Redis or Celery
broker needed. Only the behaviour added around the routes is covered here
(ownership, stale jobs, ordering, enqueue failures).
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import main
from db import get_db
from models.job import Job
from models.result import Result
from rate_limit import limiter
from routers import search as search_router

SESSION = "session-owner-1234"
OTHER_SESSION = "session-intruder-1234"


class FakeDb:
    def __init__(self, job=None, rows=()):
        self.job = job
        self.rows = list(rows)
        self.committed = 0
        self.added = []
        self.result_query = MagicMock()
        self.result_query.filter.return_value.order_by.return_value.all.return_value = self.rows

    def query(self, model):
        if model is Job:
            query = MagicMock()
            query.filter.return_value.first.return_value = self.job
            return query
        assert model is Result
        return self.result_query

    def commit(self):
        self.committed += 1

    def add(self, obj):
        self.added.append(obj)

    def refresh(self, obj):
        obj.id = obj.id or uuid.uuid4()
        obj.status = obj.status or "pending"


def make_job(session_id=SESSION, status="running", age_minutes=1) -> Job:
    return Job(
        id=uuid.uuid4(),
        session_id=session_id,
        status=status,
        inputs={"full_name": "Jane Doe"},
        retrieve=["github"],
        progress=0,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=age_minutes),
    )


@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter.reset()
    yield
    main.app.dependency_overrides.clear()


def client_for(db: FakeDb) -> TestClient:
    main.app.dependency_overrides[get_db] = lambda: db
    return TestClient(main.app)


def test_owner_can_read_their_job() -> None:
    job = make_job()
    res = client_for(FakeDb(job)).get(f"/api/results/{job.id}", headers={"X-Session-ID": SESSION})
    assert res.status_code == 200
    assert res.json()["job_id"] == str(job.id)


@pytest.mark.parametrize("headers", [{"X-Session-ID": OTHER_SESSION}, {}])
def test_other_visitors_cannot_read_a_session_owned_job(headers) -> None:
    job = make_job()
    res = client_for(FakeDb(job)).get(f"/api/results/{job.id}", headers=headers)
    assert res.status_code == 404


def test_job_without_a_session_stays_readable() -> None:
    job = make_job(session_id=None)
    assert client_for(FakeDb(job)).get(f"/api/results/{job.id}").status_code == 200


def test_unknown_job_is_404() -> None:
    assert client_for(FakeDb(None)).get(f"/api/results/{uuid.uuid4()}").status_code == 404


def test_results_are_queried_best_first() -> None:
    job = make_job(status="completed")
    db = FakeDb(job)
    client_for(db).get(f"/api/results/{job.id}", headers={"X-Session-ID": SESSION})
    order_by = db.result_query.filter.return_value.order_by
    order_by.assert_called_once()
    rendered = [str(clause) for clause in order_by.call_args.args]
    assert "confidence DESC" in rendered[0] and "scraped_at ASC" in rendered[1]


@pytest.mark.parametrize("status", ["pending", "running"])
def test_stale_unfinished_job_is_reported_failed(status) -> None:
    job = make_job(status=status, age_minutes=24 * 60)
    db = FakeDb(job)
    res = client_for(db).get(f"/api/results/{job.id}", headers={"X-Session-ID": SESSION})
    body = res.json()
    assert body["status"] == "failed"
    assert "timed out" in body["error_msg"]
    assert body["completed_at"] is not None
    assert db.committed == 1


@pytest.mark.parametrize(
    "status, age", [("running", 1), ("completed", 24 * 60), ("failed", 24 * 60)]
)
def test_recent_or_finished_jobs_are_left_alone(status, age) -> None:
    job = make_job(status=status, age_minutes=age)
    db = FakeDb(job)
    res = client_for(db).get(f"/api/results/{job.id}", headers={"X-Session-ID": SESSION})
    assert res.json()["status"] == status
    assert db.committed == 0


def test_enqueue_failure_fails_the_job_and_returns_503(monkeypatch) -> None:
    db = FakeDb()
    delay = MagicMock(side_effect=ConnectionError("broker down"))
    failed = MagicMock()
    monkeypatch.setattr(search_router.run_search, "delay", delay)
    monkeypatch.setattr(search_router, "mark_job_failed", failed)

    res = client_for(db).post(
        "/api/search",
        json={"inputs": {"full_name": "Jane Doe"}, "retrieve": ["github"]},
        headers={"X-Session-ID": SESSION},
    )

    assert res.status_code == 503
    failed.assert_called_once()
    assert failed.call_args.args[0] == str(db.added[0].id)


def test_successful_search_is_enqueued(monkeypatch) -> None:
    db = FakeDb()
    delay = MagicMock()
    monkeypatch.setattr(search_router.run_search, "delay", delay)

    res = client_for(db).post(
        "/api/search", json={"inputs": {"github": "janedoe"}, "retrieve": ["github"]}
    )

    assert res.status_code == 201
    delay.assert_called_once()
    assert res.json()["job_id"] == str(db.added[0].id)


def test_cors_does_not_allow_credentials_or_arbitrary_headers() -> None:
    res = TestClient(main.app).options(
        "/api/search",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-session-id",
        },
    )
    assert res.status_code == 200
    assert "access-control-allow-credentials" not in res.headers
    assert "X-Session-ID" in res.headers["access-control-allow-headers"]
