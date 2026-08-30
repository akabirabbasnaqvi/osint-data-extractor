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

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()
