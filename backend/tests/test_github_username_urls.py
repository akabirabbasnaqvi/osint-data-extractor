import pytest

import tasks.celery_app  # noqa: F401  (must load first: it registers the task modules)
from tasks.scrapers.github_scraper import _extract_username


@pytest.mark.parametrize(
    "raw",
    [
        "https://notgithub.com/janedoe",
        "https://github.com.evil.io/janedoe",
        "https://evil.example/?u=github.com/janedoe",
    ],
)
def test_lookalike_hosts_are_not_treated_as_github(raw: str) -> None:
    assert _extract_username({"github": raw}, {}) is None


@pytest.mark.parametrize(
    "raw",
    ["github.com/janedoe", "www.github.com/janedoe", "https://www.github.com/janedoe/repo"],
)
def test_real_github_urls_are_still_accepted(raw: str) -> None:
    assert _extract_username({"github": raw}, {}) == "janedoe"
