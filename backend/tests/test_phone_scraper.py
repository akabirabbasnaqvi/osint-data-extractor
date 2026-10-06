import pytest

import tasks.celery_app  # noqa: F401  (must load first: it registers the task modules)
from tasks.scrapers.phone_scraper import _extract_phones, _region_hint


def test_valid_international_number_is_extracted() -> None:
    assert _extract_phones("Call us: +1 650-253-0000 today", None) == {"+1 650-253-0000"}


def test_national_number_needs_a_region_hint() -> None:
    assert _extract_phones("Call (650) 253-0000", None) == set()
    assert _extract_phones("Call (650) 253-0000", "US") == {"+1 650-253-0000"}


def test_order_ids_and_dates_are_not_phone_numbers() -> None:
    assert _extract_phones("Order 123456789012 shipped 2026-01-02", "US") == set()


@pytest.mark.parametrize(
    "country, region",
    [("us", "US"), ("GB", "GB"), ("United States", None), ("", None), (None, None)],
)
def test_region_hint_only_accepts_two_letter_codes(country, region) -> None:
    assert _region_hint(country) == region
