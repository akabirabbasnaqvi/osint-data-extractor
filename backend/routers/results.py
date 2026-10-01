"""
GET /api/results/{job_id}  — poll job status + retrieved data
GET /api/jobs               — list the caller's recent jobs (X-Session-ID scoped)
DELETE /api/jobs/{job_id}   — delete the caller's job and its results (CASCADE)
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db import get_db
from models.job import Job
from models.result import Result
from rate_limit import limiter
from schemas.result_response import JobStatusResponse, JobSummary
from session import optional_session_id

router = APIRouter()


@router.get("/api/results/{job_id}", response_model=JobStatusResponse)
@limiter.limit("60/minute")
def get_results(request: Request, job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    rows = db.query(Result).filter(Result.job_id == job_id).all()
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
