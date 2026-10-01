"""
Celery app + task registration.
"""
from celery import Celery

from config import settings

celery_app = Celery(
    "public_intelligence",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# A hung scraper (slow host, WHOIS, DNS...) must not occupy a worker slot
# forever or leave a job "running" indefinitely. The soft limit raises
# SoftTimeLimitExceeded inside the task (scrapers already swallow it and
# return what they have); the hard limit kills the task as a last resort.
celery_app.conf.update(
    task_soft_time_limit=120,
    task_time_limit=150,
)

# Imported at the bottom (after `celery_app` is defined) because every
# task module does `from tasks.celery_app import celery_app` — importing
# them here registers their @celery_app.task-decorated functions with
# this app. Both the API process (to enqueue jobs) and the worker
# process (to execute them) import this module, so both see the same
# registered task names.
from tasks import orchestrator  # noqa: E402,F401
