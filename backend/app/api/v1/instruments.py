from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DbSession
from app.models.instrument import Instrument
from app.models.ohlcv import OHLCV
from app.schemas.instrument import InstrumentOut, OHLCVBarOut

router = APIRouter(prefix="/instruments", tags=["instruments"])


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
