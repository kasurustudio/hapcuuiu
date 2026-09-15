from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InstrumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    exchange: str
    name: str
    sector: str | None
    sub_sector: str | None
    board: str | None
    lot_size: int
    is_active: bool
    listed_at: date | None


class InstrumentSummaryOut(BaseModel):
    """Ringkasan harga terbaru per instrumen, dipakai Dashboard (top
    gainer/loser) — dihitung dari 2 bar OHLCV harian terakhir, bukan dari
    Signal (Signal Engine/Fase 3 belum ada, lihat instruments.py)."""

    symbol: str
    name: str
    sector: str | None
    last_price: Decimal | None
    prev_close: Decimal | None
    change_pct: float | None
    last_bar_at: datetime | None


class OHLCVBarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    value: Decimal | None
    frequency: int | None
