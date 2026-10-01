"""
Shared helpers for every scraper: rotated user-agents, a robots.txt
check before each request, and a polite randomised delay between
requests to the same domain. This is the shared implementation of
blueprint Section 10 (Anti-Detection & Rate Limiting / Respectful
Crawling) so every scraper follows the same rules automatically.
"""
import ipaddress
import random
import socket
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import requests
from loguru import logger

REQUEST_TIMEOUT = 10
MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # never buffer more than 2 MB of a page
REDIRECT_STATUSES = {301, 302, 303, 307, 308}

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


def is_public_url(url: str) -> bool:
    """SSRF guard: True only for http(s) URLs whose host resolves
    exclusively to public IP addresses.

    Scraped URLs come from search results, i.e. from third parties, so a
    hostile page can point (or redirect) us at localhost, the Docker
    network (redis, postgres, searxng) or a cloud metadata endpoint."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or 80, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError):
        return False
    if not infos:
        return False
    for info in infos:
        try:
            if not ipaddress.ip_address(info[4][0]).is_global:
                return False
        except ValueError:
            return False
    return True


def robots_allowed(url: str, user_agent: str = "*") -> bool:
    """Per blueprint 10.4: always check robots.txt before scraping.

    The robots.txt file is fetched with `requests` and a timeout --
    `RobotFileParser.read()` uses urllib with no timeout and could hang a
    worker indefinitely on a slow host."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = requests.get(
            robots_url,
            headers={"User-Agent": random_user_agent()},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException:
        # robots.txt unreachable — fail-open, same default most crawlers use
        return True

    if resp.status_code in (401, 403):
        return False  # same rule urllib.robotparser applies
    if resp.status_code != 200:
        return True  # no robots.txt (or redirect/5xx) — nothing forbids us

    rp = urllib.robotparser.RobotFileParser()
    rp.parse(resp.text.splitlines())
    return rp.can_fetch(user_agent, url)


def get(url: str, **kwargs) -> requests.Response | None:
    """A GET request that respects robots.txt and rotates its User-Agent.

    Hardened for fetching untrusted URLs: every hop (including redirects,
    followed manually, max MAX_REDIRECTS) must resolve to a public IP, and
    the body is capped at MAX_RESPONSE_BYTES. Returns None (instead of
    raising) on any failure so callers can just skip a source rather than
    handling exceptions everywhere."""
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", random_user_agent())
    kwargs.pop("allow_redirects", None)
    kwargs.pop("stream", None)

    try:
        for _ in range(MAX_REDIRECTS + 1):
            if not is_public_url(url):
                logger.warning(f"utils.get: refusing non-public or unresolvable URL {url}")
                return None
            if not robots_allowed(url):
                logger.warning(f"utils.get: robots.txt disallows {url}")
                return None

            resp = requests.get(
                url, headers=headers, timeout=REQUEST_TIMEOUT,
                allow_redirects=False, stream=True, **kwargs,
            )
            if resp.status_code in REDIRECT_STATUSES and resp.headers.get("Location"):
                url = urljoin(url, resp.headers["Location"])
                resp.close()
                continue

            body = bytearray()
            for chunk in resp.iter_content(chunk_size=16384):
                body.extend(chunk)
                if len(body) >= MAX_RESPONSE_BYTES:
                    break
            resp.close()
            resp._content = bytes(body)
            resp._content_consumed = True
            return resp

        logger.warning(f"utils.get: too many redirects for {url}")
        return None
    except requests.RequestException:
        return None
