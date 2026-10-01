import os

for _k, _v in {
    "DATABASE_URL": "postgresql://u:p@localhost/db",
    "REDIS_URL": "redis://localhost/0",
    "CELERY_BROKER_URL": "redis://localhost/0",
    "CELERY_RESULT_BACKEND": "redis://localhost/1",
    "SECRET_KEY": "test",
}.items():
    os.environ.setdefault(_k, _v)

import pytest  # noqa: E402

import tasks.celery_app  # noqa: E402,F401  (must load first: it registers the task modules)
from tasks.scrapers.github_scraper import _extract_username  # noqa: E402


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("janedoe", "janedoe"),
        ("@janedoe", "janedoe"),
        ("https://github.com/janedoe", "janedoe"),
        ("https://github.com/janedoe/some-repo", "janedoe"),
    ],
)
def test_valid_usernames(raw: str, expected: str) -> None:
    assert _extract_username({"github": raw}, {}) == expected


@pytest.mark.parametrize("raw", ["x/../../repos", "a b", "-leading", "x" * 60, "?q=1"])
def test_unsafe_usernames_are_rejected(raw: str) -> None:
    assert _extract_username({"github": raw}, {}) is None


def test_discovery_skips_reserved_github_pages() -> None:
    discovered = {"github": ["https://github.com/orgs/acme", "https://github.com/janedoe"]}
    assert _extract_username({}, discovered) == "janedoe"
