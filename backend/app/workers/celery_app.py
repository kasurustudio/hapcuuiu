"""Celery app + jadwal Beat. SPEC.md Bagian 6.4.

Fase 1 hanya mengaktifkan `sync_instruments` dan `ingest_daily_ohlcv`.
Job lain (indikator, sinyal, level, alert, fundamental) ditambahkan di
fase-fase berikutnya begitu modulnya ada.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "stockapp",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks.ingest"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
)

# Jadwal WIB, dikonversi Celery otomatis lewat conf.timezone di atas.
celery_app.conf.beat_schedule = {
    "sync-instruments-daily": {
        "task": "app.workers.tasks.ingest.sync_instruments",
        "schedule": crontab(hour=6, minute=0),
    },
    "ingest-daily-ohlcv": {
        "task": "app.workers.tasks.ingest.ingest_daily_ohlcv",
        "schedule": crontab(hour=17, minute=30, day_of_week="1-5"),
    },
}
