"""
FastAPI application entry point: wires up rate limiting, CORS, the
/api/search and /api/results routers, and a health check.
"""
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import settings
from db import get_db
from rate_limit import limiter
from routers import search, results

app = FastAPI(title="Public Intelligence API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    # No cookies or HTTP auth are used (identity is the X-Session-ID header),
    # so credentialed cross-origin requests are not needed.
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Session-ID"],
)

app.include_router(search.router, tags=["search"])
app.include_router(results.router, tags=["results"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Like /api/health, but also proves the database is reachable, so a load
    balancer or orchestrator can stop routing to an instance that cannot work."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ready"}
