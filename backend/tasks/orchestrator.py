"""
The job fan-out logic (blueprint 9.1). run_search() is what the API
enqueues for every submitted search. It:

  1. Runs discovery (Google/DuckDuckGo dorks) synchronously — every
     other scraper needs its output as leads, so there's no point
     parallelising it with them.
  2. Fans out one Celery task per requested output category, running
     in parallel via a chord.
  3. merge_results() runs once every fanned-out task finishes (whether
     it found data or not) and marks the job completed.

linkedin/facebook/instagram/twitter do NOT scrape those platforms (see
tasks/scrapers/social_links.py for why) — they only surface profile
URLs the user gave us directly or that discovery already found via
search-engine results.
"""
from celery import chord

from tasks.celery_app import celery_app
from tasks.result_writer import mark_job_completed, mark_job_running
from tasks.scrapers.company_scraper import scrape_company
from tasks.scrapers.email_finder import scrape_personal_email, scrape_work_email
from tasks.scrapers.github_scraper import scrape_github
from tasks.scrapers.google_scraper import discover_urls, EMPTY_DISCOVERY
from tasks.scrapers.phone_scraper import scrape_phone
from tasks.scrapers.social_links import scrape_facebook, scrape_instagram, scrape_linkedin, scrape_twitter
from tasks.scrapers.website_scraper import scrape_website

TASK_MAP = {
    "github": scrape_github,
    "personal_email": scrape_personal_email,
    "work_email": scrape_work_email,
    "phone": scrape_phone,
    "personal_website": scrape_website,
    "company": scrape_company,
    "linkedin": scrape_linkedin,
    "facebook": scrape_facebook,
    "instagram": scrape_instagram,
    "twitter": scrape_twitter,
}


@celery_app.task(name="tasks.orchestrator.run_search")
def run_search(job_id: str, inputs: dict, retrieve: list[str]) -> None:
    mark_job_running(job_id)

    try:
        discovered = discover_urls(inputs)
    except Exception:
        discovered = dict(EMPTY_DISCOVERY)

    subtasks = [
        TASK_MAP[category].s(job_id, inputs, discovered)
        for category in retrieve
        if category in TASK_MAP
    ]

    if not subtasks:
        merge_results.delay([], job_id=job_id, note=None)
        return

    chord(subtasks)(merge_results.s(job_id=job_id, note=None))


@celery_app.task(name="tasks.orchestrator.merge_results")
def merge_results(_task_returns: list, job_id: str, note: str | None = None) -> None:
    """Chord callback. Each scraper task already wrote its own Result
    rows directly (see result_writer.save_result), so `_task_returns`
    (the list of each task's return value) is unused — this just
    finalizes the job."""
    mark_job_completed(job_id, note=note)
