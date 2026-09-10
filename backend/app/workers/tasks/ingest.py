"""Task Celery untuk jalur hosted. SPEC.md Bagian 6.4.

Wrapper tipis di atas `app.services.ingest` (logic murni, tanpa Celery) —
lihat docstring modul itu untuk alasan pemisahannya. Jalur desktop (SQLite)
memanggil `app.services.ingest` langsung lewat
`app.workers.local_scheduler`, TIDAK lewat modul ini.
"""

from __future__ import annotations

from app.core.database import SessionLocal
from app.services import ingest as ingest_logic
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.ingest.sync_instruments")
def sync_instruments() -> dict:
    db = SessionLocal()
    try:
        return ingest_logic.sync_instruments(db)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.ingest.ingest_daily_ohlcv")
def ingest_daily_ohlcv(symbols: list[str] | None = None) -> dict:
    db = SessionLocal()
    try:
        return ingest_logic.ingest_daily_ohlcv(db, symbols=symbols)
    finally:
        db.close()
