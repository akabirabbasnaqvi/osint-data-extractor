import pytest

import tasks.celery_app  # noqa: F401  (must load first: it registers the task modules)
from tasks.scrapers.email_finder import _clean_domain, _extract_emails, _guess_patterns


def test_asset_filenames_are_not_emails() -> None:
    html = '<img src="logo@2x.png"> <script src="app@1.2.js"></script> mail jane@acme.com'
    assert _extract_emails(html) == {"jane@acme.com"}


def test_emails_are_lowercased_and_deduplicated() -> None:
    assert _extract_emails("Jane@Acme.com jane@acme.com") == {"jane@acme.com"}


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("https://www.acme.com/about", "acme.com"),
        ("acme.com", "acme.com"),
        ("http://acme.com:8080/x", "acme.com"),
        ("WWW.Acme.COM", "acme.com"),
        ("", ""),
    ],
)
def test_clean_domain(raw: str, expected: str) -> None:
    assert _clean_domain(raw) == expected


def test_guess_patterns_use_clean_domain() -> None:
    guesses = _guess_patterns("Jane Doe", _clean_domain("https://www.acme.com"))
    assert "jane.doe@acme.com" in guesses
    assert all("@www." not in g for g in guesses)
