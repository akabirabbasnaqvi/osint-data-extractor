"""
POST /api/search — creates a Job row and enqueues it onto Celery.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from sqlalchemy.orm import Session

from db import get_db
from models.job import Job
from rate_limit import limiter
from schemas.search_request import SearchRequest
from session import optional_session_id
from tasks.orchestrator import run_search
from tasks.result_writer import mark_job_failed

router = APIRouter()


@router.post("/api/search", status_code=201)
@limiter.limit("10/minute")
def create_search(
    request: Request,
    payload: SearchRequest,
    db: Session = Depends(get_db),
    session_id: Optional[str] = Depends(optional_session_id),
):
    job = Job(
        session_id=session_id,
        inputs=payload.inputs.model_dump(exclude_none=True),
        retrieve=payload.retrieve,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        run_search.delay(str(job.id), job.inputs, job.retrieve)
    except Exception:
        # Broker down: don't leave a job "pending" forever that no worker will
        # ever pick up -- fail it and tell the client to retry.
        logger.exception(f"could not enqueue job {job.id}")
        mark_job_failed(str(job.id), "The search queue is unavailable.")
        raise HTTPException(status_code=503, detail="Search service is temporarily unavailable. Please try again.")

    return {"job_id": job.id, "status": job.status}
