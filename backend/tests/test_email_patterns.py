import pytest

import tasks.celery_app  # noqa: F401  (must load first: it registers the task modules)
from tasks.scrapers import email_finder
from tasks.scrapers.email_finder import _guess_patterns


@pytest.mark.parametrize(
    "name, first_guess",
    [
        ("Jane O'Brien", "jane.obrien@acme.com"),
        ("José García", "jose.garcia@acme.com"),
        ("S.M Hamza", "sm.hamza@acme.com"),
        ("Dr. Jane Doe Jr.", "jane.doe@acme.com"),
    ],
)
def test_guesses_are_always_valid_ascii_mailboxes(name: str, first_guess: str) -> None:
    guesses = _guess_patterns(name, "acme.com")
    assert guesses[0] == first_guess
    for guess in guesses:
        local = guess.split("@")[0]
        assert local.replace(".", "").isalnum() and local.isascii()
        assert ".." not in local and not local.startswith(".") and not local.endswith(".")


@pytest.mark.parametrize("name", ["Madonna", "", "   ", "Dr. Jr."])
def test_no_guesses_without_a_first_and_last_name(name: str) -> None:
    assert _guess_patterns(name, "acme.com") == []


def test_no_guesses_without_a_domain() -> None:
    assert _guess_patterns("Jane Doe", "") == []


def test_work_email_does_not_repeat_known_addresses(monkeypatch) -> None:
    saved = []
    monkeypatch.setattr(
        email_finder,
        "save_result",
        lambda job_id, category, data, source_url=None, confidence=1.0: saved.append(data["email"]),
    )
    monkeypatch.setattr(email_finder, "_hunter_lookup", lambda *a: "jane.doe@acme.com")

    email_finder.scrape_work_email(
        "job-1",
        {"full_name": "Jane Doe", "company_website": "https://acme.com", "email": "jane@acme.com"},
        {},
    )

    assert saved.count("jane.doe@acme.com") == 1  # from hunter.io, not re-guessed
    assert saved.count("jane@acme.com") == 1  # the user-supplied one, not re-guessed
