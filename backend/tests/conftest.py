"""
config.Settings() is instantiated at import time and requires these
variables, so they are set before any test module imports application code.
Real environment values (e.g. in CI) are never overridden.
"""
import os

for _key, _value in {
    "DATABASE_URL": "postgresql://u:p@localhost/db",
    "REDIS_URL": "redis://localhost/0",
    "CELERY_BROKER_URL": "redis://localhost/0",
    "CELERY_RESULT_BACKEND": "redis://localhost/1",
    "SECRET_KEY": "test",
}.items():
    os.environ.setdefault(_key, _value)
