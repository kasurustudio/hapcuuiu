"""Bootstrap data awal untuk mode desktop (SQLite).

Menjalankan `sync_instruments` + `ingest_daily_ohlcv` sekali secara otomatis
saat aplikasi pertama kali dibuka kalau database masih kosong — supaya user
tidak perlu menunggu jadwal `local_scheduler` (06:00/17:30 WIB) pertama kali
setelah install (lihat app/main.py lifespan).

Jalan di background thread terpisah dari request lifecycle FastAPI, pakai
`SessionLocal` sendiri (bukan dependency injection request-scoped) — sama
seperti pola job scheduler di app/workers/local_scheduler.py.
"""

from __future__ import annotations

import logging
import threading

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.instrument import Instrument
from app.services.ingest import ingest_daily_ohlcv, sync_instruments

logger = logging.getLogger(__name__)


class BootstrapState:
    """Status bootstrap in-memory, dibaca endpoint `/system/status`. Satu
    instance per proses — cukup untuk desktop single-user, tidak perlu
    disimpan ke DB."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status = "idle"
        self._detail: str | None = None

    def set(self, status: str, detail: str | None = None) -> None:
        with self._lock:
            self._status = status
            self._detail = detail

    def snapshot(self) -> dict:
        with self._lock:
            return {"status": self._status, "detail": self._detail}


bootstrap_state = BootstrapState()


def needs_bootstrap(db: Session) -> bool:
    """True kalau tabel instruments masih kosong — tanda database baru
    (install pertama kali), belum pernah di-sync sama sekali."""
    return db.query(Instrument).count() == 0


def run_bootstrap_sync() -> None:
    """Jalankan sync_instruments + ingest_daily_ohlcv sekali. Kegagalan
    (mis. tidak ada akses internet) dicatat sebagai status error, TIDAK
    dilempar sebagai exception ke thread caller — thread daemon background
    tidak boleh membuat proses utama crash."""
    bootstrap_state.set("running")
    db = SessionLocal()
    try:
        sync_result = sync_instruments(db)
        logger.info("bootstrap: sync_instruments selesai (%s)", sync_result)
        ingest_result = ingest_daily_ohlcv(db)
        logger.info("bootstrap: ingest_daily_ohlcv selesai (%s)", ingest_result)
        bootstrap_state.set("done")
    except Exception as exc:  # noqa: BLE001 - lihat docstring, tidak boleh crash proses
        logger.exception("bootstrap: gagal")
        bootstrap_state.set("error", detail=str(exc))
    finally:
        db.close()


def start_bootstrap_if_needed() -> threading.Thread | None:
    """Cek apakah bootstrap perlu dijalankan; kalau ya, jalankan di
    background thread supaya tidak memblokir startup FastAPI (ingest ~48
    simbol x 5 tahun data bisa makan waktu beberapa menit). Return None
    kalau tidak perlu (database sudah pernah di-sync sebelumnya)."""
    db = SessionLocal()
    try:
        if not needs_bootstrap(db):
            return None
    finally:
        db.close()

    thread = threading.Thread(target=run_bootstrap_sync, name="bootstrap-ingest", daemon=True)
    thread.start()
    return thread
