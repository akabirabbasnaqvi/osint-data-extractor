from config import Settings

REQUIRED = dict(
    database_url="postgresql://u:p@localhost/db",
    redis_url="redis://localhost/0",
    celery_broker_url="redis://localhost/0",
    celery_result_backend="redis://localhost/1",
    secret_key="test",
)


def test_allowed_origins_ignore_blank_entries() -> None:
    settings = Settings(_env_file=None, allowed_origins="https://a.example, ,https://b.example,", **REQUIRED)
    assert settings.allowed_origins_list == ["https://a.example", "https://b.example"]


def test_stale_job_cutoff_has_a_sensible_default() -> None:
    assert Settings(_env_file=None, **REQUIRED).stale_job_minutes == 30
