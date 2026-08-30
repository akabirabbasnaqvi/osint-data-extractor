"""
Validates the body of POST /api/search. Mirrors blueprint Section 6.2:
all 12 input fields are optional individually, but at least one must be
filled, and at least one output category must be selected.
"""
from typing import Optional

from pydantic import BaseModel, field_validator


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
        if not any(val and val.strip() for val in v.model_dump().values()):
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
        return v
