"""
Central application settings, loaded from environment variables (.env).
Using pydantic-settings means every value is validated at startup — if
DATABASE_URL is missing or malformed, the app fails immediately with a
clear error instead of crashing later mid-request.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    hunter_io_api_key: str = ""
    searxng_url: str = "http://searxng:8080"

    http_proxy: str = ""

    secret_key: str
    allowed_origins: str = "http://localhost:3000"

    # A job still pending/running after this long has lost its worker (crash,
    # restart, purged queue) and is reported as failed instead of spinning forever.
    stale_job_minutes: int = 30

    # Where rate-limit counters live. "memory://" is per-process: with several
    # uvicorn workers (production) each keeps its own count, so the effective
    # limit multiplies and resets on restart. Point it at Redis there.
    rate_limit_storage: str = "memory://"

    @property
    def allowed_origins_list(self) -> list[str]:
        # Ignore blanks so "a.com, ,b.com" or a trailing comma can't add "" as an origin.
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
