"""
GitHub scraper — uses the free, unauthenticated GitHub REST API v3
(blueprint 5.6). Rate limit: 60 requests/hour without a token, which is
fine for one profile lookup per job.
"""
import re

import requests

from tasks.celery_app import celery_app
from tasks.result_writer import save_result

GITHUB_API = "https://api.github.com"
USERNAME_FROM_URL = re.compile(r"github\.com/([A-Za-z0-9-]+)")


def _extract_username(inputs: dict, discovered: dict) -> str | None:
    if inputs.get("github"):
        match = USERNAME_FROM_URL.search(inputs["github"])
        return match.group(1) if match else inputs["github"].strip()

    for url in discovered.get("github", []):
        match = USERNAME_FROM_URL.search(url)
        if match:
            return match.group(1)
    return None


@celery_app.task(name="tasks.scrapers.github")
def scrape_github(job_id: str, inputs: dict, discovered: dict) -> None:
    try:
        username = _extract_username(inputs, discovered)
        if not username:
            return

        resp = requests.get(f"{GITHUB_API}/users/{username}", timeout=10)
        if resp.status_code != 200:
            return

        profile = resp.json()
        data = {
            "username": profile.get("login"),
            "name": profile.get("name"),
            "bio": profile.get("bio"),
            "company": profile.get("company"),
            "location": profile.get("location"),
            "blog": profile.get("blog"),
            "email": profile.get("email"),
            "public_repos": profile.get("public_repos"),
            "followers": profile.get("followers"),
            "following": profile.get("following"),
            "avatar_url": profile.get("avatar_url"),
        }
        save_result(job_id, "github", data, source_url=profile.get("html_url"), confidence=0.95)
    except Exception:
        # Per blueprint 9.2: a scraper failure must not crash the job —
        # it just contributes no data for this category.
        pass
