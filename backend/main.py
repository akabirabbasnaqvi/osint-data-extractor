"""
FastAPI application entry point. Right now it only exposes a health
check — routers for /api/search and /api/results get added in Phase 2
once the database models exist.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import search, results

app = FastAPI(title="Public Intelligence API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, tags=["search"])
app.include_router(results.router, tags=["results"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
