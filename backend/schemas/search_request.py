"""
Validates the body of POST /api/search. Mirrors blueprint Section 6.2:
all 12 input fields are optional individually, but at least one must be
filled, and at least one output category must be selected.

Inputs are normalised before they are validated: whitespace is trimmed,
blank strings become None, and the formats the UI itself suggests (a bare
domain like "acme.com", a path like "linkedin.com/in/janedoe", or an
"@handle") are accepted instead of being rejected as "not http/https".
"""
import ipaddress
import re
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ValidationInfo, field_validator

MAX_FIELD_LENGTH = 200

SOCIAL_URL_FIELDS = ("linkedin", "facebook", "instagram", "twitter", "github")
WEBSITE_FIELDS = ("company_website",)


# What a bare handle may look like: "@janedoe", "jane.doe", "jane-doe_1".
HANDLE_PATTERN = re.compile(r"^@?[A-Za-z0-9._-]{1,100}$")

SOCIAL_DOMAINS = {
    "linkedin": "linkedin.com",
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "twitter": "twitter.com",
    "github": "github.com",
}


def _is_handle(value: str, platform_domain: str) -> bool:
    """A bare handle such as "@janedoe" or "jane.doe": no slash and not
    mentioning the platform's own domain."""
    return "/" not in value and platform_domain not in value.lower()


def _ensure_scheme(value: str) -> str:
    return value if "://" in value else f"https://{value}"


def _reject_non_public_host(url: str) -> None:
    """Reject malformed or private-network URLs to prevent SSRF."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must use http or https and include a hostname")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith((".local", ".internal", ".localhost")):
        raise ValueError("Local network URLs are not allowed")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        raise ValueError("Private network URLs are not allowed")


class SearchInputs(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    personal_email: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    github: Optional[str] = None
    twitter: Optional[str] = None

    @field_validator("*", mode="before")
    @classmethod
    def strip_and_blank_to_none(cls, value):
        """Trim whitespace; whitespace-only input counts as "not provided"."""
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("*")
    @classmethod
    def limit_length(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value) > MAX_FIELD_LENGTH:
            raise ValueError(f"Must be at most {MAX_FIELD_LENGTH} characters")
        return value

    @field_validator(*SOCIAL_URL_FIELDS)
    @classmethod
    def social_url_or_handle(cls, value: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Accept a handle ("@jane") or a URL with or without a scheme."""
        if not value:
            return value
        if _is_handle(value, SOCIAL_DOMAINS[info.field_name]):
            if not HANDLE_PATTERN.fullmatch(value):
                raise ValueError("Enter a username (like @janedoe) or a profile URL")
            return value
        value = _ensure_scheme(value)
        _reject_non_public_host(value)
        return value

    @field_validator(*WEBSITE_FIELDS)
    @classmethod
    def public_website(cls, value: Optional[str]) -> Optional[str]:
        """Accept "acme.com" as well as "https://acme.com"."""
        if not value:
            return value
        value = _ensure_scheme(value)
        _reject_non_public_host(value)
        return value


VALID_OUTPUT_CATEGORIES = {
    "personal_email", "work_email", "phone", "linkedin", "github",
    "twitter", "facebook", "instagram", "personal_website", "company",
}


class SearchRequest(BaseModel):
    inputs: SearchInputs
    retrieve: list[str]

    @field_validator("inputs")
    @classmethod
    def at_least_one_input(cls, v: SearchInputs) -> SearchInputs:
        if not any(v.model_dump().values()):
            raise ValueError("At least one input field is required")
        return v

    @field_validator("retrieve")
    @classmethod
    def valid_output_categories(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Select at least one output category")
        unknown = set(v) - VALID_OUTPUT_CATEGORIES
        if unknown:
            raise ValueError(f"Unknown output categories: {sorted(unknown)}")
        # Drop duplicates (keeping order) so a category is never scraped twice.
        return list(dict.fromkeys(v))
