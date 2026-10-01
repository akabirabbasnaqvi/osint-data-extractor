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


def test_bare_domain_is_normalised_to_https() -> None:
    # The UI placeholder suggests "acme.com" -- it must not be rejected.
    assert SearchInputs(company_website="acme.com").company_website == "https://acme.com"
    assert (
        SearchInputs(linkedin="linkedin.com/in/janedoe").linkedin
        == "https://linkedin.com/in/janedoe"
    )


def test_social_handles_are_accepted() -> None:
    assert SearchInputs(instagram="@janedoe").instagram == "@janedoe"
    assert SearchInputs(facebook="jane.doe").facebook == "jane.doe"
    assert SearchInputs(facebook="facebook.com/jane.doe").facebook == "https://facebook.com/jane.doe"


def test_bare_private_hosts_are_still_rejected() -> None:
    with pytest.raises(ValidationError, match="Local network URLs"):
        SearchInputs(company_website="localhost:8000")
    with pytest.raises(ValidationError, match="Private network URLs"):
        SearchInputs(company_website="10.0.0.5")


def test_whitespace_only_input_does_not_count() -> None:
    with pytest.raises(ValidationError, match="At least one input field"):
        SearchRequest(inputs=SearchInputs(full_name="   "), retrieve=["github"])


def test_inputs_are_trimmed() -> None:
    assert SearchInputs(full_name="  Jane Doe  ").full_name == "Jane Doe"


def test_overlong_input_is_rejected() -> None:
    with pytest.raises(ValidationError, match="at most"):
        SearchInputs(full_name="x" * 500)


def test_duplicate_categories_are_collapsed() -> None:
    request = SearchRequest(
        inputs=SearchInputs(full_name="Jane Doe"),
        retrieve=["github", "phone", "github"],
    )
    assert request.retrieve == ["github", "phone"]
