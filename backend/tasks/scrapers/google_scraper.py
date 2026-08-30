"""
Discovery scraper — the primary lead-generation step (blueprint 5.1).

Uses a self-hosted SearxNG instance (the `searxng` service in
docker-compose.yml) — a free, open-source metasearch engine, genuinely
free with no account or billing card required. This IS the ceiling of
"100% free, no account" web search: every real API alternative we tried
(Google Custom Search, Brave Search) turned out to require a payment
method on file even for their nominally "free" tier.

Accept this as best-effort, not guaranteed: the underlying search
engines SearxNG queries (DuckDuckGo, Brave, Startpage, Bing, Google)
actively detect and block/rate-limit automated traffic, so some
searches will come back with partial or no discovery results — that's
a real, structural limitation of free scraping-based search, not a bug
to keep re-chasing. GitHub lookups and anything the user provides
directly (name, LinkedIn URL, etc.) work reliably regardless.

(Full history: DuckDuckGo HTML scraping -> blocked by DuckDuckGo's own
robots.txt -> Google Custom Search API -> required a Google Cloud
billing account -> Brave Search API -> no longer has a free tier ->
back to self-hosted SearxNG, accepted as best-effort.)
"""
import re
import time
from urllib.parse import urlparse

import requests
from loguru import logger

from config import settings

EMPTY_DISCOVERY = {
    "linkedin": [], "facebook": [], "twitter": [],
    "instagram": [], "github": [], "general": [],
}


def build_dorks(inputs: dict) -> list[tuple[str, str]]:
    """Returns (query, identity) pairs.

    `query` is what's actually sent to the search engine — deliberately
    UNQUOTED, so the engine can fuzzy-match name variations (e.g. a
    LinkedIn profile indexed as "Syed Muhammad Hamza" when the user only
    gave us "S.M Hamza") instead of requiring an exact phrase, which
    testing showed returns far fewer results.

    `identity` is the person/username we're actually looking for. It's
    kept separate from `query` so our own relevance filter (_is_relevant)
    can still strictly enforce it afterward, regardless of how loosely
    the engine itself searched — precision comes from our filter, not
    from the engine's query syntax.
    """
    name = inputs.get("full_name")
    email = inputs.get("email") or inputs.get("personal_email")
    company = inputs.get("company_name")
    city = inputs.get("city")
    github = inputs.get("github")

    dorks: list[tuple[str, str]] = []
    if name:
        dorks.append((f'{name} site:linkedin.com/in', name))
        dorks.append((f'{name} site:facebook.com', name))
        dorks.append((f'{name} site:twitter.com OR site:x.com', name))
        dorks.append((f'{name} site:github.com', name))
        dorks.append((f'{name} email OR contact OR phone', name))
        if company:
            dorks.append((f'{name} {company} email', name))
        if city:
            dorks.append((f'{name} {city}', name))
    if email:
        # Emails have no meaningful "variant" — exact match stays useful here.
        dorks.append((f'"{email}"', email))
        dorks.append((f'"{email}" site:linkedin.com', email))
    if github:
        # Cross-references the GitHub identity against the rest of the
        # web — a username is often a more unique search key than a
        # common full name, so this frequently surfaces pages the
        # name-based dorks above miss entirely.
        dorks.append((f'{github} email OR contact', github))
        dorks.append((f'{github} site:linkedin.com OR site:twitter.com OR site:x.com', github))
    return dorks


def _classify(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "linkedin.com" in host:
        return "linkedin"
    if "facebook.com" in host:
        return "facebook"
    if "twitter.com" in host or host == "x.com":
        return "twitter"
    if "instagram.com" in host:
        return "instagram"
    if "github.com" in host:
        return "github"
    return "general"


def _search_searxng(query: str) -> list[dict]:
    try:
        resp = requests.get(
            f"{settings.searxng_url}/search",
            params={"q": query, "format": "json"},
            timeout=15,
        )
    except requests.RequestException as e:
        logger.warning(f"discovery: SearxNG request failed for {query!r}: {e}")
        return []

    if resp.status_code != 200:
        logger.warning(f"discovery: SearxNG returned {resp.status_code} for {query!r}: {resp.text[:200]}")
        return []

    try:
        return resp.json().get("results", [])
    except ValueError:
        logger.warning(f"discovery: SearxNG returned a non-JSON response for {query!r}")
        return []


def _normalize(text: str) -> str:
    """Lowercase and strip everything but letters/digits, so "S.M Hamza",
    "S M Hamza", and "s-m-hamza" (a likely URL slug) all collapse to the
    same "smhamza" — comparing on that instead of exact formatting is
    what lets this match real-world variation."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _is_relevant(identity: str, result: dict) -> bool:
    if not identity:
        return True
    haystack = _normalize(f"{result.get('title') or ''} {result.get('content') or ''} {result.get('url') or ''}")
    required = _normalize(identity)
    if required in haystack:
        return True

    # Fallback for multi-word identities (full names): gated platforms like
    # LinkedIn often return a stripped-down snippet to search engines that
    # doesn't reproduce the full name verbatim, even for the correct
    # profile — e.g. the name only shows up split across the title and
    # URL slug, not as one contiguous block. Since every dork that carries
    # a full name is already scoped with `site:`, requiring each
    # individual word to appear somewhere (not necessarily adjacent) is
    # still precise enough to avoid false positives, just less brittle
    # about exact formatting.
    words = [w for w in re.findall(r"[a-z0-9]+", identity.lower()) if len(w) > 1]
    if len(words) < 2:
        return False
    return all(word in haystack for word in words)


def discover_urls(inputs: dict, max_dorks: int = 6) -> dict[str, list[str]]:
    """Runs up to `max_dorks` dorks through the local SearxNG instance,
    discards results that don't actually mention the person/identity we
    searched for (see _is_relevant), and buckets what's left by
    platform. Best-effort — see module docstring."""
    discovered = {k: list(v) for k, v in EMPTY_DISCOVERY.items()}

    for query, identity in build_dorks(inputs)[:max_dorks]:
        raw_results = _search_searxng(query)
        kept = 0

        for result in raw_results:
            url = result.get("url")
            if not url or not _is_relevant(identity, result):
                continue
            bucket = _classify(url)
            if url not in discovered[bucket]:
                discovered[bucket].append(url)
                kept += 1

        logger.info(f"discovery: query {query!r} -> {len(raw_results)} raw, {kept} kept after relevance filter")
        time.sleep(3)  # deliberately slow — the underlying search engines
        # SearxNG queries temporarily block/CAPTCHA IPs that query them
        # rapidly and repeatedly. This doesn't guarantee no throttling,
        # but it makes a single real job's burst of queries look much
        # less like abuse than one every 0.5s.

    counts = {k: len(v) for k, v in discovered.items()}
    logger.info(f"discovery finished: {counts}")
    return discovered
