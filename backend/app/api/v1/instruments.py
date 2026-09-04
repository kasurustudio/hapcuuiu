from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DbSession
from app.models.instrument import Instrument
from app.models.ohlcv import OHLCV
from app.schemas.analysis import PatternOut, PriceLevelOut
from app.schemas.instrument import InstrumentOut, OHLCVBarOut
from app.services.indicators.snapshot import build_indicator_snapshot
from app.services.levels.detector import detect_price_levels
from app.services.patterns.candlestick import detect_candlestick_patterns

router = APIRouter(prefix="/instruments", tags=["instruments"])

# SPEC.md Bagian 6.3 mensyaratkan minimum bar per mode (100-300) untuk
# GATE SINYAL — itu urusan signal engine di Fase 3. Endpoint indikator di
# sini mode-agnostic (belum ada konsep mode di Fase 2), jadi dipakai batas
# minimum generik yang cukup untuk indikator dengan periode terpanjang
# (Ichimoku senkou span butuh ~78 bar) supaya output tidak degenerate.
MIN_BARS_FOR_ANALYSIS = 60


@router.get("", response_model=list[InstrumentOut])
def list_instruments(
    db: DbSession,
    search: str | None = Query(default=None, description="Cari berdasarkan symbol/nama"),
    sector: str | None = None,
    exchange: str | None = None,
) -> list[Instrument]:
    query = db.query(Instrument)
    if search:
        like = f"%{search.upper()}%"
        query = query.filter(
            (Instrument.symbol.ilike(like)) | (Instrument.name.ilike(like))
        )
    if sector:
        query = query.filter(Instrument.sector == sector)
    if exchange:
        query = query.filter(Instrument.exchange == exchange)
    return query.order_by(Instrument.symbol).all()


def _get_instrument_or_404(db: DbSession, symbol: str) -> Instrument:
    instrument = (
        db.query(Instrument).filter(Instrument.symbol == symbol.upper()).one_or_none()
    )
    if instrument is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "INSTRUMENT_NOT_FOUND",
                    "message": f"Instrumen {symbol!r} tidak ditemukan.",
                }
            },
        )
    return instrument


@router.get("/{symbol}", response_model=InstrumentOut)
def get_instrument(symbol: str, db: DbSession) -> Instrument:
    return _get_instrument_or_404(db, symbol)


@router.get("/{symbol}/ohlcv", response_model=list[OHLCVBarOut])
def get_instrument_ohlcv(
    symbol: str,
    db: DbSession,
    timeframe: str = Query(default="1d"),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
) -> list[OHLCV]:
    instrument = _get_instrument_or_404(db, symbol)

    query = db.query(OHLCV).filter(
        OHLCV.instrument_id == instrument.id, OHLCV.timeframe == timeframe
    )
    if from_ is not None:
        query = query.filter(OHLCV.ts >= from_)
    if to is not None:
        query = query.filter(OHLCV.ts <= to)

    return query.order_by(OHLCV.ts).all()


def _load_ohlcv_dataframe(db: DbSession, instrument_id: int, timeframe: str) -> pd.DataFrame:
    rows = (
        db.query(OHLCV)
        .filter(OHLCV.instrument_id == instrument_id, OHLCV.timeframe == timeframe)
        .order_by(OHLCV.ts)
        .all()
    )
    if not rows:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    index = pd.DatetimeIndex([row.ts if row.ts.tzinfo else row.ts.replace(tzinfo=timezone.utc) for row in rows])
    return pd.DataFrame(
        {
            "open": [float(row.open) for row in rows],
            "high": [float(row.high) for row in rows],
            "low": [float(row.low) for row in rows],
            "close": [float(row.close) for row in rows],
            "volume": [float(row.volume) for row in rows],
        },
        index=index,
    )


def _require_sufficient_data(df: pd.DataFrame, symbol: str, timeframe: str) -> None:
    if len(df) < MIN_BARS_FOR_ANALYSIS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "INSUFFICIENT_DATA",
                    "message": (
                        f"Data OHLCV {symbol!r} timeframe {timeframe!r} kurang dari "
                        f"{MIN_BARS_FOR_ANALYSIS} bar, belum cukup untuk analisis."
                    ),
                    "details": {"available_bars": len(df), "required_bars": MIN_BARS_FOR_ANALYSIS},
                }
            },
        )


@router.get("/{symbol}/indicators")
def get_instrument_indicators(
    symbol: str,
    db: DbSession,
    timeframe: str = Query(default="1d"),
) -> dict:
    """SPEC.md Bagian 13. Mengembalikan snapshot nilai indikator terbaru
    (bentuk sama seperti `indicator_snapshots.payload`)."""
    instrument = _get_instrument_or_404(db, symbol)
    df = _load_ohlcv_dataframe(db, instrument.id, timeframe)
    _require_sufficient_data(df, symbol, timeframe)
    return build_indicator_snapshot(df)


@router.get("/{symbol}/levels", response_model=list[PriceLevelOut])
def get_instrument_levels(
    symbol: str,
    db: DbSession,
    timeframe: str = Query(default="1d"),
) -> list[dict]:
    """SPEC.md Bagian 13 & 7.2."""
    instrument = _get_instrument_or_404(db, symbol)
    df = _load_ohlcv_dataframe(db, instrument.id, timeframe)
    _require_sufficient_data(df, symbol, timeframe)

    levels_df = detect_price_levels(df, timeframe=timeframe)
    return levels_df.to_dict(orient="records")


@router.get("/{symbol}/patterns", response_model=list[PatternOut])
def get_instrument_patterns(
    symbol: str,
    db: DbSession,
    timeframe: str = Query(default="1d"),
) -> list[dict]:
    """SPEC.md Bagian 13 & 7.3. Pattern candlestick dengan filter konteks,
    memakai level S/R yang sama (`/levels`) supaya konsisten."""
    instrument = _get_instrument_or_404(db, symbol)
    df = _load_ohlcv_dataframe(db, instrument.id, timeframe)
    _require_sufficient_data(df, symbol, timeframe)

    levels_df = detect_price_levels(df, timeframe=timeframe)
    matches = detect_candlestick_patterns(df, levels=levels_df)
    return [
        {
            "name": m.name,
            "direction": m.direction,
            "ts": df.index[m.bar_index],
            "reliability_score": m.reliability_score,
        }
        for m in matches
    ]
