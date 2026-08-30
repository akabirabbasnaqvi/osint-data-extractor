"""
GET /api/results/{job_id}  — poll job status + retrieved data
GET /api/jobs               — list recent jobs
DELETE /api/jobs/{job_id}   — delete a job and its results (CASCADE)
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models.job import Job
from models.result import Result
from schemas.result_response import JobStatusResponse, JobSummary

router = APIRouter()


@router.get("/api/results/{job_id}", response_model=JobStatusResponse)
def get_results(job_id: UUID, db: Session = Depends(get_db)):
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
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(50).all()
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
def delete_job(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
