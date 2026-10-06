"""
FastAPI application entry point: wires up rate limiting, CORS, the
/api/search and /api/results routers, and a health check.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
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
