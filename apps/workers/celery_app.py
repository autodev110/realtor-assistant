from __future__ import annotations

from celery import Celery

from core.config import get_settings
from core.providers import enabled_providers
from . import tasks

settings = get_settings()

celery_app = Celery(
    "realtor_assistant",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.beat_schedule = {
    "ingest-providers": {
        "task": "apps.workers.celery_app.run_ingestion",
        "schedule": 30 * 60,
    },
    "daily-digest": {
        "task": "apps.workers.celery_app.run_daily_digest",
        "schedule": 24 * 60 * 60,
        "options": {"expires": 60 * 60},
    },
}


@celery_app.task(name="apps.workers.celery_app.run_ingestion")
def run_ingestion():
    for provider in enabled_providers():
        tasks.ingest_provider(provider)


@celery_app.task(name="apps.workers.celery_app.run_daily_digest")
def run_daily_digest():
    tasks.run_daily_digests()
