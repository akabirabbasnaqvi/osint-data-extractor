"""
Email discovery (blueprint 5.7). Two categories, two Celery tasks:
personal_email and work_email — matching the two separate output
checkboxes the frontend will expose.

Deliberate scope decision: the blueprint's third strategy ("pattern
guessing + validation... verify via SMTP") is implemented WITHOUT the
SMTP verification step. Actively connecting to a company's mail server
to probe whether an address exists is exactly what automated email-
harvesting/verification abuse looks like from the receiving server's
side, and it's not something to build in without you explicitly asking
for it. Guessed addresses are instead stored unverified, at low
confidence, clearly labeled — the frontend can show that distinction.
"""
import re
from urllib.parse import urlparse

import requests

from config import settings
from tasks.celery_app import celery_app
from tasks.result_writer import save_result
from tasks.scrapers.utils import get

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# "logo@2x.png", "sprite@3x.webp", "bundle@1.2.3.js" match the email regex
# but are asset filenames, not addresses -- ubiquitous in scraped HTML.
_ASSET_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp", ".avif",
    ".css", ".js", ".mjs", ".map", ".json", ".woff", ".woff2", ".ttf", ".eot",
    ".mp4", ".webm", ".pdf",
)


def _extract_emails(text: str) -> set[str]:
    """Unique, lower-cased addresses, with asset filenames filtered out."""
    return {
        email.lower()
        for email in EMAIL_REGEX.findall(text)
        if not email.lower().endswith(_ASSET_SUFFIXES)
    }


def _clean_domain(website: str) -> str:
    """Bare registrable-looking domain from a URL or domain: strips the
    scheme, path, port and a leading "www." (guessing "jane@www.acme.com"
    is never right)."""
    website = (website or "").strip()
    if not website:
        return ""
    if "://" not in website:
        website = f"//{website}"
    host = (urlparse(website).hostname or "").lower()
    return host.removeprefix("www.")


def _guess_patterns(full_name: str, domain: str) -> list[str]:
    parts = full_name.lower().split()
    if len(parts) < 2 or not domain:
        return []
    first, last = parts[0], parts[-1]
    return [
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first}@{domain}",
    ]


def _hunter_lookup(domain: str, first_name: str, last_name: str) -> str | None:
    if not settings.hunter_io_api_key or not domain:
        return None
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/email-finder",
            params={
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": settings.hunter_io_api_key,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        return resp.json().get("data", {}).get("email")
    except requests.RequestException:
        return None


@celery_app.task(name="tasks.scrapers.email_personal")
def scrape_personal_email(job_id: str, inputs: dict, discovered: dict) -> None:
    try:
        if inputs.get("personal_email"):
            save_result(job_id, "personal_email", {"email": inputs["personal_email"]}, confidence=1.0)

        seen = {(inputs.get("personal_email") or "").lower()}
        for url in discovered.get("general", [])[:10]:
            resp = get(url)
            if resp is not None:
                for email in sorted(_extract_emails(resp.text) - seen):
                    seen.add(email)  # same address on several pages -> one result
                    save_result(job_id, "personal_email", {"email": email}, source_url=url, confidence=0.5)
    except Exception:
        pass


@celery_app.task(name="tasks.scrapers.email_work")
def scrape_work_email(job_id: str, inputs: dict, discovered: dict) -> None:
    try:
        if inputs.get("email"):
            save_result(job_id, "work_email", {"email": inputs["email"]}, confidence=1.0)

        domain = _clean_domain(inputs.get("company_website", ""))
        full_name = inputs.get("full_name", "")

        if domain and full_name:
            parts = full_name.split()
            if len(parts) >= 2:
                hunter_email = _hunter_lookup(domain, parts[0], parts[-1])
                if hunter_email:
                    save_result(job_id, "work_email",
                                {"email": hunter_email, "source": "hunter.io"}, confidence=0.9)

            for guess in _guess_patterns(full_name, domain):
                save_result(job_id, "work_email", {"email": guess, "verified": False}, confidence=0.3)
    except Exception:
        pass
