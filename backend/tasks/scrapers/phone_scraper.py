"""
Phone number discovery (blueprint 5.8). Extracts phone-shaped
substrings from pages found during discovery and validates each one
with Google's `phonenumbers` library, which rejects anything that
isn't a real, dialable number — filtering out most false positives
from the regex pass.
"""
import re

import phonenumbers

from tasks.celery_app import celery_app
from tasks.result_writer import save_result
from tasks.scrapers.utils import get

PHONE_CANDIDATE_REGEX = re.compile(r'[\+]?[1-9][0-9 .\-\(\)]{8,15}')


def _region_hint(country: str | None) -> str | None:
    # phonenumbers needs a 2-letter ISO region code (e.g. "US"); a full
    # country name like "United States" isn't usable, so only pass it
    # through when it already looks like a code.
    if country and len(country) == 2 and country.isalpha():
        return country.upper()
    return None


def _extract_phones(text: str, region: str | None) -> set[str]:
    valid = set()
    for candidate in PHONE_CANDIDATE_REGEX.findall(text):
        try:
            parsed = phonenumbers.parse(candidate, region)
            if phonenumbers.is_valid_number(parsed):
                valid.add(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
        except phonenumbers.NumberParseException:
            continue
    return valid


@celery_app.task(name="tasks.scrapers.phone")
def scrape_phone(job_id: str, inputs: dict, discovered: dict) -> None:
    try:
        region = _region_hint(inputs.get("country"))

        for url in discovered.get("general", [])[:10]:
            resp = get(url)
            if resp is not None:
                for phone in _extract_phones(resp.text, region):
                    save_result(job_id, "phone", {"phone": phone}, source_url=url, confidence=0.5)
    except Exception:
        pass
