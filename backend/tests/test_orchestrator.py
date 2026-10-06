from unittest.mock import MagicMock

import tasks.celery_app  # noqa: F401  (must load first: it registers the task modules)
from tasks import orchestrator


def test_unexpected_error_marks_job_failed(monkeypatch) -> None:
    failed = MagicMock()
    monkeypatch.setattr(orchestrator, "mark_job_running", MagicMock(side_effect=RuntimeError("db down")))
    monkeypatch.setattr(orchestrator, "mark_job_failed", failed)

    orchestrator.run_search("job-1", {"full_name": "Jane"}, ["github"])

    failed.assert_called_once()
    assert failed.call_args.args[0] == "job-1"
    assert "RuntimeError" in failed.call_args.args[1]


def test_discovery_failure_still_runs_scrapers(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "mark_job_running", MagicMock())
    monkeypatch.setattr(orchestrator, "discover_urls", MagicMock(side_effect=RuntimeError("blocked")))
    chord_call = MagicMock()
    monkeypatch.setattr(orchestrator, "chord", MagicMock(return_value=chord_call))
    failed = MagicMock()
    monkeypatch.setattr(orchestrator, "mark_job_failed", failed)

    orchestrator.run_search("job-2", {"github": "janedoe"}, ["github"])

    failed.assert_not_called()
    chord_call.assert_called_once()  # chord(subtasks)(callback) was reached


def test_chord_callback_has_error_handler(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "mark_job_running", MagicMock())
    monkeypatch.setattr(orchestrator, "discover_urls", MagicMock(return_value=dict(orchestrator.EMPTY_DISCOVERY)))
    chord_call = MagicMock()
    monkeypatch.setattr(orchestrator, "chord", MagicMock(return_value=chord_call))

    orchestrator.run_search("job-3", {"github": "janedoe"}, ["github"])

    callback = chord_call.call_args.args[0]
    assert callback.options.get("link_error"), "merge_results must have an error callback"


def test_fail_job_marks_failed(monkeypatch) -> None:
    failed = MagicMock()
    monkeypatch.setattr(orchestrator, "mark_job_failed", failed)
    orchestrator.fail_job("some-task-id", job_id="job-4")  # old-style errback args
    failed.assert_called_once()
    assert failed.call_args.args[0] == "job-4"


def test_time_limits_are_configured() -> None:
    conf = tasks.celery_app.celery_app.conf
    assert conf.task_soft_time_limit and conf.task_time_limit
    assert conf.task_soft_time_limit < conf.task_time_limit
