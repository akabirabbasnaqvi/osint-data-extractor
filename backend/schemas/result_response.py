"""
Response shapes returned by the results/jobs endpoints.

Note: this is a deliberate simplification of the illustrative JSON in
blueprint Section 6.3. Rather than hard-coding a different shape per
category (e.g. linkedin as an object, emails as a list of strings), each
category is returned as a list of generic result entries. This is
simpler and is what the actual `results` table naturally produces —
each scraper writes one or more rows per category. The frontend groups
these by category to render its cards.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ResultEntry(BaseModel):
    data: dict[str, Any]
    source_url: Optional[str] = None
    confidence: float
    scraped_at: datetime

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    progress: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_msg: Optional[str] = None
    results: dict[str, list[ResultEntry]]

    class Config:
        from_attributes = True


class JobSummary(BaseModel):
    job_id: UUID
    status: str
    progress: int
    created_at: datetime
    inputs: dict[str, Any]

    class Config:
        from_attributes = True
