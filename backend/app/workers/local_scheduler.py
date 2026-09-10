"""Scheduler in-process (APScheduler) untuk build desktop — pengganti
Celery Beat + worker terpisah yang dipakai jalur hosted.

Jalur hosted (Postgres) tetap pakai Celery (`app/workers/celery_app.py`)
sebagai service terpisah — lihat DEPLOYMENT.md. Modul ini HANYA aktif saat
`DATABASE_URL` adalah SQLite (heuristik: SQLite == desktop, sesuai
`init_db_schema()` di `core/database.py`), supaya tidak dobel-jadwal kalau
suatu saat app yang sama dijalankan lagi di mode hosted.

Jadwal sama persis dengan SPEC.md Bagian 6.4 (sync_instruments 06:00 WIB
harian, ingest_daily_ohlcv 17:30 WIB hari bursa), tapi dieksekusi sebagai
thread di dalam proses yang sama — cocok untuk aplikasi single-user yang
jalan selama app dibuka, tanpa perlu Redis/broker terpisah.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal
from app.services.ingest import ingest_daily_ohlcv as _ingest_daily_ohlcv
from app.services.ingest import sync_instruments as _sync_instruments

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_sync_instruments() -> None:
    db = SessionLocal()
    try:
        result = _sync_instruments(db)
        logger.info("local_scheduler sync_instruments: %s", result)
    except Exception:  # noqa: BLE001 — job scheduler tidak boleh mati karena 1 kegagalan
        logger.exception("local_scheduler sync_instruments gagal")
    finally:
        db.close()


def _run_ingest_daily_ohlcv() -> None:
    db = SessionLocal()
    try:
        result = _ingest_daily_ohlcv(db)
        logger.info("local_scheduler ingest_daily_ohlcv: %s", result)
    except Exception:  # noqa: BLE001
        logger.exception("local_scheduler ingest_daily_ohlcv gagal")
    finally:
        db.close()


def start_local_scheduler() -> BackgroundScheduler:
    """Idempotent: memanggil ini berkali-kali tidak membuat scheduler ganda."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    scheduler = BackgroundScheduler(timezone="Asia/Jakarta")
    scheduler.add_job(
        _run_sync_instruments,
        CronTrigger(hour=6, minute=0),
        id="sync_instruments",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_ingest_daily_ohlcv,
        CronTrigger(hour=17, minute=30, day_of_week="mon-fri"),
        id="ingest_daily_ohlcv",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("local_scheduler started (Asia/Jakarta): sync_instruments 06:00, ingest_daily_ohlcv 17:30 Sen-Jum")
    return scheduler


def stop_local_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
