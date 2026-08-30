"""
SQLAlchemy model for the `jobs` table — one row per search request the
user submits. Mirrors blueprint Section 7.
"""
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func

from db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), nullable=True)
    status = Column(String(20), default="pending")  # pending | running | completed | failed
    inputs = Column(JSONB, nullable=False)
    retrieve = Column(ARRAY(String), nullable=False)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_msg = Column(Text, nullable=True)
