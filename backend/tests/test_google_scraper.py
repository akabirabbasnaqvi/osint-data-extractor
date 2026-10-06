import pytest

import tasks.celery_app  # noqa: F401  (must load first: it registers the task modules)
from tasks.scrapers import google_scraper
from tasks.scrapers.google_scraper import _classify


@pytest.mark.parametrize(
    "url, bucket",
    [
        ("https://www.linkedin.com/in/janedoe", "linkedin"),
        ("https://linkedin.com/in/janedoe", "linkedin"),
        ("https://github.com/janedoe", "github"),
        ("https://gist.github.com/janedoe", "github"),
        ("https://twitter.com/janedoe", "twitter"),
        ("https://x.com/janedoe", "twitter"),
        ("https://mobile.twitter.com/janedoe", "twitter"),
        ("https://www.facebook.com/jane.doe", "facebook"),
        ("https://www.instagram.com/janedoe/", "instagram"),
        ("https://janedoe.dev/about", "general"),
    ],
)
def test_classify_real_platform_hosts(url: str, bucket: str) -> None:
    assert _classify(url) == bucket


@pytest.mark.parametrize(
    "url",
    [
        "https://notgithub.com/janedoe",
        "https://evil-linkedin.com/in/janedoe",
        "https://linkedin.com.evil.io/in/janedoe",
        "https://fakex.com/janedoe",
        "https://example.com/?next=github.com",
    ],
)
def test_classify_rejects_lookalike_hosts(url: str) -> None:
    assert _classify(url) == "general"


def test_discovery_keeps_only_http_urls(monkeypatch) -> None:
    results = [
        {"url": "javascript:alert(1)", "title": "Jane Doe"},
        {"url": "data:text/html,<script>1</script>", "title": "Jane Doe"},
        {"url": "ftp://files.example/jane", "title": "Jane Doe"},
        {"url": "https://janedoe.dev/", "title": "Jane Doe"},
    ]
    monkeypatch.setattr(google_scraper, "_search_searxng", lambda query: results)
    monkeypatch.setattr(google_scraper.time, "sleep", lambda _s: None)

    discovered = google_scraper.discover_urls({"full_name": "Jane Doe"}, max_dorks=1)

    assert discovered["general"] == ["https://janedoe.dev/"]
