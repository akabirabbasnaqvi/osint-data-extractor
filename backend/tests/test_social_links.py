import pytest

import tasks.celery_app  # noqa: F401  (must load first: it registers the task modules)
from tasks.scrapers import social_links


@pytest.mark.parametrize(
    "category, raw, expected",
    [
        ("linkedin", "janedoe", "https://linkedin.com/in/janedoe"),
        ("linkedin", "@janedoe", "https://linkedin.com/in/janedoe"),
        ("linkedin", "https://www.linkedin.com/in/janedoe", "https://www.linkedin.com/in/janedoe"),
        ("twitter", "@janedoe", "https://twitter.com/janedoe"),
        ("facebook", "jane.doe", "https://facebook.com/jane.doe"),
        ("instagram", "@janedoe", "https://instagram.com/janedoe"),
    ],
)
def test_handles_become_profile_urls(monkeypatch, category: str, raw: str, expected: str) -> None:
    saved = []
    monkeypatch.setattr(social_links, "save_result", lambda *a, **k: saved.append((a, k)))

    getattr(social_links, f"scrape_{category}")("job-1", {category: raw}, {})

    ((args, kwargs),) = saved
    assert args[2] == {"url": expected, "source": "user-provided"}
    assert kwargs["confidence"] == 1.0


def test_discovered_urls_are_reported_at_lower_confidence(monkeypatch) -> None:
    saved = []
    monkeypatch.setattr(social_links, "save_result", lambda *a, **k: saved.append((a, k)))

    social_links.scrape_linkedin(
        "job-1", {}, {"linkedin": ["https://linkedin.com/in/a", "https://linkedin.com/in/b"]}
    )

    assert [k["confidence"] for _, k in saved] == [0.6, 0.6]
