"""
SQLAlchemy model for the `results` table — one row per data point a
scraper finds for a job (e.g. one row for the LinkedIn profile, one row
for each discovered email). Mirrors blueprint Section 7.
"""
import uuid

from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from db import Base


class Result(Base):
    __tablename__ = "results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)  # e.g. 'linkedin', 'work_email'
    data = Column(JSONB, nullable=False)
    source_url = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
