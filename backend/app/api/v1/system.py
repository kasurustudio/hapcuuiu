from fastapi import APIRouter

from app.core.database import is_sqlite
from app.core.deps import DbSession
from app.models.instrument import Instrument
from app.services.bootstrap import bootstrap_state

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
def get_system_status(db: DbSession) -> dict:
    """Dipakai frontend desktop untuk tahu kapan data awal (sync instrumen +
    ingest OHLCV pertama kali) selesai, supaya bisa menampilkan status
    "sedang mengambil data..." alih-alih chart kosong membingungkan.
    Jalur hosted (Postgres) selalu `bootstrap.status = "idle"` — bootstrap
    otomatis cuma berlaku untuk mode desktop SQLite (lihat app/main.py)."""
    return {
        "database": "sqlite" if is_sqlite else "postgres",
        "instrument_count": db.query(Instrument).count(),
        "bootstrap": bootstrap_state.snapshot(),
    }
