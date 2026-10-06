import pytest

import tasks.celery_app  # noqa: F401  (must load first: it registers the task modules)
from tasks.scrapers.github_scraper import _extract_username


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
