"""
Small DB-write helpers used by every Celery task. Tasks run in the
worker process, not the API process, so they can't reuse a FastAPI
request's DB session — each call here opens and closes its own
short-lived session.
"""
import uuid
from datetime import datetime, timezone

from db import SessionLocal
from models.job import Job
from models.result import Result


def _to_uuid(job_id) -> uuid.UUID:
    return job_id if isinstance(job_id, uuid.UUID) else uuid.UUID(str(job_id))


def mark_job_running(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == _to_uuid(job_id)).first()
        if job:
            job.status = "running"
            db.commit()
    finally:
        db.close()


def save_result(job_id: str, category: str, data: dict, source_url: str | None = None,
                 confidence: float = 1.0) -> None:
    if not data:
        return
    db = SessionLocal()
    try:
        db.add(Result(
            job_id=_to_uuid(job_id),
            category=category,
            data=data,
            source_url=source_url,
            confidence=confidence,
        ))
        db.commit()
    finally:
        db.close()


def mark_job_completed(job_id: str, note: str | None = None) -> None:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == _to_uuid(job_id)).first()
        if job:
            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.now(timezone.utc)
            if note:
                job.error_msg = note
            db.commit()
    finally:
        db.close()


def mark_job_failed(job_id: str, error_msg: str) -> None:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == _to_uuid(job_id)).first()
        if job:
            job.status = "failed"
            job.error_msg = error_msg
            db.commit()
    finally:
        db.close()
