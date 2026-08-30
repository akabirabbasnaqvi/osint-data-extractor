"""
Surfaces "personal website" candidates: any URL the discovery step
found that isn't one of the known social platforms (those already get
bucketed separately — see google_scraper._classify).
"""
from tasks.celery_app import celery_app
from tasks.result_writer import save_result


@celery_app.task(name="tasks.scrapers.website")
def scrape_website(job_id: str, inputs: dict, discovered: dict) -> None:
    try:
        for url in discovered.get("general", []):
            save_result(job_id, "personal_website", {"url": url}, source_url=url, confidence=0.4)
    except Exception:
        pass
