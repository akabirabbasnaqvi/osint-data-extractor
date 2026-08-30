"""
LinkedIn / Facebook / Instagram / Twitter — deliberately NOT full
scrapers. See Phase 3b discussion: these platforms' Terms of Service
prohibit automated scraping (logged in or not), and building stealth
headless-browser evasion to defeat their anti-bot protections for a
public commercial product is not something this project does.

Instead, each of these just surfaces the profile URL as a "found link"
result:
  - If the user directly supplied a username/URL for that platform, we
    normalize and report it (confidence 1.0 — it's literally what they
    told us).
  - Otherwise, we report whatever URL(s) the discovery step
    (google_scraper.discover_urls) already found via DuckDuckGo search
    results — i.e. what a search engine has already publicly indexed.
    We never visit linkedin.com/facebook.com/instagram.com/twitter.com
    ourselves.

This means these categories return a link to follow up on manually,
not a scraped profile. That's an intentional product limitation, not a
bug.
"""
from tasks.celery_app import celery_app
from tasks.result_writer import save_result

PLATFORM_CONFIG = {
    "linkedin": {"input_key": "linkedin", "domain": "linkedin.com"},
    "facebook": {"input_key": "facebook", "domain": "facebook.com"},
    "instagram": {"input_key": "instagram", "domain": "instagram.com"},
    "twitter": {"input_key": "twitter", "domain": "twitter.com / x.com"},
}


def _normalize_input_url(raw: str, domain: str) -> str:
    raw = raw.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    handle = raw.lstrip("@")
    primary_domain = domain.split(" / ")[0]
    return f"https://{primary_domain}/{handle}"


def _make_task(category: str):
    config = PLATFORM_CONFIG[category]

    def task_fn(job_id: str, inputs: dict, discovered: dict) -> None:
        try:
            direct_input = inputs.get(config["input_key"])
            if direct_input:
                url = _normalize_input_url(direct_input, config["domain"])
                save_result(
                    job_id, category,
                    {"url": url, "source": "user-provided"},
                    source_url=url, confidence=1.0,
                )
                return

            for url in discovered.get(category, []):
                save_result(
                    job_id, category,
                    {"url": url, "source": "search-engine-discovery"},
                    source_url=url, confidence=0.6,
                )
        except Exception:
            pass

    task_fn.__name__ = f"scrape_{category}"
    return celery_app.task(name=f"tasks.scrapers.{category}")(task_fn)


scrape_linkedin = _make_task("linkedin")
scrape_facebook = _make_task("facebook")
scrape_instagram = _make_task("instagram")
scrape_twitter = _make_task("twitter")
