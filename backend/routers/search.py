"""
POST /api/search — creates a Job row and enqueues it onto Celery.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from models.job import Job
from schemas.search_request import SearchRequest
from tasks.orchestrator import run_search

router = APIRouter()


@router.post("/api/search", status_code=201)
def create_search(payload: SearchRequest, db: Session = Depends(get_db)):
    job = Job(
        inputs=payload.inputs.model_dump(exclude_none=True),
        retrieve=payload.retrieve,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    run_search.delay(str(job.id), job.inputs, job.retrieve)

    return {"job_id": job.id, "status": job.status}
