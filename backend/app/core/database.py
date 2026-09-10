from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

is_sqlite = settings.database_url.startswith("sqlite")

# SQLite: satu file dipakai lintas thread (uvicorn/FastAPI + scheduler
# lokal jalan di thread berbeda) — check_same_thread=False aman di sini
# karena akses selalu lewat SessionLocal per-request/per-job, bukan satu
# koneksi dibagi antar thread secara bersamaan.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args={"check_same_thread": False} if is_sqlite else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db_schema() -> None:
    """Buat skema langsung dari model (tanpa Alembic) untuk jalur SQLite
    desktop — tidak ada langkah migrasi eksternal di app yang dibundel.
    Deployment hosted (Postgres) TETAP pakai Alembic (`alembic upgrade
    head`), bukan fungsi ini, supaya fitur khusus Postgres (mis. hypertable
    TimescaleDB) tidak ter-skip diam-diam.
    """
    if not is_sqlite:
        return

    from app.models import (  # noqa: F401  registrasi semua model ke Base.metadata
        Alert,
        Fundamental,
        IndicatorSnapshot,
        Instrument,
        OHLCV,
        Position,
        PriceLevel,
        Signal,
        User,
    )

    Base.metadata.create_all(engine)
