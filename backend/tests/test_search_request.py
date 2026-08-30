import pytest
from pydantic import ValidationError

from schemas.search_request import SearchInputs, SearchRequest


def test_search_requires_an_input() -> None:
    with pytest.raises(ValidationError, match="At least one input field"):
        SearchRequest(inputs=SearchInputs(), retrieve=["github"])


def test_search_rejects_unknown_result_category() -> None:
    with pytest.raises(ValidationError, match="Unknown output categories"):
        SearchRequest(
            inputs=SearchInputs(full_name="Example Person"),
            retrieve=["private_records"],
        )


def test_search_rejects_private_network_url() -> None:
    with pytest.raises(ValidationError, match="Private network URLs"):
        SearchInputs(company_website="http://127.0.0.1:8000")


def test_search_accepts_public_https_url() -> None:
    inputs = SearchInputs(company_website="https://example.com")
    assert inputs.company_website == "https://example.com"
