"""
Shared helpers for every scraper: rotated user-agents, a robots.txt
check before each request, and a polite randomised delay between
requests to the same domain. This is the shared implementation of
blueprint Section 10 (Anti-Detection & Rate Limiting / Respectful
Crawling) so every scraper follows the same rules automatically.
"""
import random
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests
from loguru import logger

try:
    from fake_useragent import UserAgent
    _ua = UserAgent()
except Exception:
    # fake-useragent fetches its data online; if that's unavailable
    # (offline, blocked, etc.) fall back to a small static list instead
    # of crashing every scraper at import time.
    _ua = None

_FALLBACK_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


def random_user_agent() -> str:
    if _ua is not None:
        try:
            return _ua.random
        except Exception:
            pass
    return random.choice(_FALLBACK_USER_AGENTS)


def polite_delay(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def robots_allowed(url: str, user_agent: str = "*") -> bool:
    """Per blueprint 10.4: always check robots.txt before scraping."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        # robots.txt unreachable — fail-open, same default most crawlers use
        return True


def get(url: str, **kwargs) -> requests.Response | None:
    """A GET request that respects robots.txt and rotates its User-Agent.
    Returns None (instead of raising) on any failure so callers can just
    skip a source rather than handling exceptions everywhere."""
    if not robots_allowed(url):
        logger.warning(f"utils.get: robots.txt disallows {url}")
        return None
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", random_user_agent())
    try:
        return requests.get(url, headers=headers, timeout=10, **kwargs)
    except requests.RequestException:
        return None
