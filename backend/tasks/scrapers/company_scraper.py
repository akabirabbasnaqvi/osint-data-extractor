"""
Company/domain enrichment via WHOIS. Note: most domains use privacy
proxies that redact registrant contact details, so this mostly confirms
registration facts (registrar, creation date, country) rather than
personal contact info — it's a supporting data point, not a primary
source.
"""
import whois

from tasks.celery_app import celery_app
from tasks.result_writer import save_result


@celery_app.task(name="tasks.scrapers.company")
def scrape_company(job_id: str, inputs: dict, discovered: dict) -> None:
    try:
        domain = inputs.get("company_website")
        name = inputs.get("company_name")
        if not domain and not name:
            return

        data = {"name": name, "website": domain}

        if domain:
            try:
                w = whois.whois(domain)
                data["registrar"] = w.registrar
                data["creation_date"] = str(w.creation_date) if w.creation_date else None
                data["country"] = w.country
            except Exception:
                # WHOIS lookups fail often (rate limits, missing TLD
                # support, privacy redaction) — that's fine, we still
                # keep the name/website the user gave us.
                pass

        save_result(job_id, "company", data, confidence=0.8)
    except Exception:
        pass
