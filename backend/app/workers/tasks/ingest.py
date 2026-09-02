"""Job ingest data. SPEC.md Bagian 6.4.

- `sync_instruments`: seed/refresh daftar emiten (Fase 1: dari seed statis LQ45).
- `ingest_daily_ohlcv`: tarik OHLCV harian dari MarketAdapter dan upsert ke DB.

Validasi data quality (Bagian 6.3) sengaja TIDAK dijalankan di sini — ingest
menyimpan data mentah apa adanya sebagai source of truth. Validator dijalankan
di titik konsumsi (perhitungan indikator/sinyal, Fase 2/3), supaya data mentah
tidak pernah hilang meskipun aturan validasi berubah di kemudian hari.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.instrument import Instrument
from app.models.ohlcv import OHLCV
from app.services.market_data.lq45_seed import LQ45_SEED
from app.services.market_data.yfinance_idx import YFinanceIDXAdapter
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

BACKFILL_YEARS = 5


@celery_app.task(name="app.workers.tasks.ingest.sync_instruments")
def sync_instruments() -> dict:
    """Seed/refresh daftar instrumen IDX dari LQ45_SEED (Fase 1).

    Idempotent: upsert berdasarkan (symbol, exchange).
    """
    db = SessionLocal()
    try:
        return _sync_instruments(db)
    finally:
        db.close()


def _sync_instruments(db: Session) -> dict:
    created = 0
    updated = 0
    for seed in LQ45_SEED:
        existing = (
            db.query(Instrument)
            .filter(Instrument.symbol == seed.symbol, Instrument.exchange == "IDX")
            .one_or_none()
        )
        if existing is None:
            db.add(
                Instrument(
                    symbol=seed.symbol,
                    exchange="IDX",
                    name=seed.name,
                    sector=seed.sector,
                    lot_size=100,
                    is_active=True,
                )
            )
            created += 1
        else:
            existing.name = seed.name
            existing.sector = seed.sector
            existing.is_active = True
            updated += 1
    db.commit()
    logger.info("sync_instruments: created=%d updated=%d", created, updated)
    return {"created": created, "updated": updated}


@celery_app.task(name="app.workers.tasks.ingest.ingest_daily_ohlcv")
def ingest_daily_ohlcv(symbols: list[str] | None = None) -> dict:
    """Tarik OHLCV harian untuk instrumen aktif dan upsert ke tabel `ohlcv`.

    Backfill default 5 tahun (SPEC.md Bagian 15 — "Backfill historis: 5 tahun
    daily"). Jika `symbols` diberikan, hanya proses simbol tersebut (dipakai
    untuk backfill manual/terarah).
    """
    db = SessionLocal()
    try:
        return _ingest_daily_ohlcv(db, symbols=symbols)
    finally:
        db.close()


def _ingest_daily_ohlcv(db: Session, symbols: list[str] | None = None) -> dict:
    adapter = YFinanceIDXAdapter()

    query = db.query(Instrument).filter(Instrument.exchange == "IDX", Instrument.is_active.is_(True))
    if symbols:
        query = query.filter(Instrument.symbol.in_(symbols))
    instruments = query.all()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365 * BACKFILL_YEARS)

    results: dict[str, int | str] = {}
    for instrument in instruments:
        try:
            df = adapter.fetch_ohlcv(instrument.symbol, "1d", start, end)
        except Exception as exc:  # noqa: BLE001 — ingest tidak boleh gagal total karena 1 simbol
            logger.exception("gagal fetch OHLCV untuk %s", instrument.symbol)
            results[instrument.symbol] = f"error: {exc}"
            continue

        row_count = _upsert_ohlcv(db, instrument.id, "1d", df)
        results[instrument.symbol] = row_count

    db.commit()
    return results


def _upsert_ohlcv(db: Session, instrument_id: int, timeframe: str, df) -> int:
    if df.empty:
        return 0

    rows = []
    for ts, row in df.iterrows():
        frequency = row.get("frequency")
        rows.append(
            {
                "instrument_id": instrument_id,
                "timeframe": timeframe,
                "ts": ts.to_pydatetime(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
                "value": float(row["value"]) if row.get("value") == row.get("value") else None,
                "frequency": None if frequency != frequency else frequency,
            }
        )

    stmt = pg_insert(OHLCV).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["instrument_id", "timeframe", "ts"],
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
            "value": stmt.excluded.value,
            "frequency": stmt.excluded.frequency,
        },
    )
    db.execute(stmt)
    return len(rows)
