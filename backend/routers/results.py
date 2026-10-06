"""
GET /api/results/{job_id}  — poll job status + retrieved data
GET /api/jobs               — list the caller's recent jobs (X-Session-ID scoped)
DELETE /api/jobs/{job_id}   — delete the caller's job and its results (CASCADE)
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from config import settings
from db import get_db
from models.job import Job
from models.result import Result
from rate_limit import limiter
from schemas.result_response import JobStatusResponse, JobSummary
from session import optional_session_id

router = APIRouter()


def _fail_if_stale(job: Job, db: Session) -> None:
    """Jobs whose worker died would otherwise report "running" forever (and the
    UI would poll forever). Past the cutoff, report them as failed."""
    if job.status not in ("pending", "running") or job.created_at is None:
        return
    age = datetime.now(timezone.utc) - job.created_at
    if age > timedelta(minutes=settings.stale_job_minutes):
        job.status = "failed"
        job.error_msg = "This search timed out before it could finish."
        job.completed_at = datetime.now(timezone.utc)
        db.commit()


@router.get("/api/results/{job_id}", response_model=JobStatusResponse)
@limiter.limit("60/minute")
def get_results(
    request: Request,
    job_id: UUID,
    db: Session = Depends(get_db),
    session_id: Optional[str] = Depends(optional_session_id),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    # A job stamped with a session belongs to that visitor: the job id alone
    # must not expose the personal details they searched for. Same 404 as
    # "missing" so ids can't be probed. Jobs with no session (API clients) stay open.
    if not job or (job.session_id is not None and job.session_id != session_id):
        raise HTTPException(status_code=404, detail="Job not found")

    _fail_if_stale(job, db)

    rows = (
        db.query(Result)
        .filter(Result.job_id == job_id)
        .order_by(Result.confidence.desc(), Result.scraped_at.asc())
        .all()
    )
    results_by_category: dict[str, list] = {}
    for row in rows:
        results_by_category.setdefault(row.category, []).append(row)

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_msg=job.error_msg,
        results=results_by_category,
    )


@router.get("/api/jobs", response_model=list[JobSummary])
@limiter.limit("60/minute")
def list_jobs(
    request: Request,
    db: Session = Depends(get_db),
    session_id: Optional[str] = Depends(optional_session_id),
):
    # Only the caller's own searches. No session id -> nothing to show.
    if session_id is None:
        return []
    jobs = (
        db.query(Job)
        .filter(Job.session_id == session_id)
        .order_by(Job.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        JobSummary(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            created_at=job.created_at,
            inputs=job.inputs,
        )
        for job in jobs
    ]


@router.delete("/api/jobs/{job_id}", status_code=204)
@limiter.limit("20/minute")
def delete_job(
    request: Request,
    job_id: UUID,
    db: Session = Depends(get_db),
    session_id: Optional[str] = Depends(optional_session_id),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    # Same 404 for "missing" and "not yours" so ids can't be probed.
    if not job or session_id is None or job.session_id != session_id:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
