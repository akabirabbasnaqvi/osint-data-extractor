import pytest
from pydantic import ValidationError

from schemas.search_request import SearchInputs


@pytest.mark.parametrize(
    "field, value, expected",
    [
        ("twitter", "@janedoe", "@janedoe"),
        ("twitter", "x.com/janedoe", "https://x.com/janedoe"),
        ("github", "janedoe", "janedoe"),
        ("github", "github.com/janedoe", "https://github.com/janedoe"),
        ("instagram", "jane.doe_1", "jane.doe_1"),
    ],
)
def test_valid_handles_and_urls_are_accepted(field: str, value: str, expected: str) -> None:
    assert getattr(SearchInputs(**{field: value}), field) == expected


@pytest.mark.parametrize("field", ["twitter", "github", "linkedin", "facebook", "instagram"])
@pytest.mark.parametrize("value", ["javascript:alert(1)", "<script>", "jane doe", "a;b"])
def test_unsafe_handles_are_rejected(field: str, value: str) -> None:
    with pytest.raises(ValidationError, match="username"):
        SearchInputs(**{field: value})


@pytest.mark.parametrize("field", ["twitter", "github"])
@pytest.mark.parametrize("value", ["http://localhost/x", "https://169.254.169.254/latest", "http://10.0.0.5/x"])
def test_private_urls_are_rejected_for_twitter_and_github(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        SearchInputs(**{field: value})
