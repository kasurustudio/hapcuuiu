"""Abstract market data layer. SPEC.md Bagian 6.1.

Menambahkan market baru (US, crypto) hanya perlu implementasi
`MarketAdapter` baru — engine analisis tidak boleh tahu asal data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

import pandas as pd


@dataclass(frozen=True, slots=True)
class InstrumentDTO:
    symbol: str
    exchange: str
    name: str
    sector: str | None = None
    sub_sector: str | None = None
    board: str | None = None
    lot_size: int = 100
    is_active: bool = True
    listed_at: date | None = None


@dataclass(frozen=True, slots=True)
class QuoteDTO:
    symbol: str
    price: Decimal
    change: Decimal
    change_pct: Decimal
    volume: int
    ts: datetime


@dataclass(frozen=True, slots=True)
class FundamentalDTO:
    symbol: str
    period: date
    period_type: str  # quarterly|annual|ttm
    revenue: Decimal | None = None
    net_income: Decimal | None = None
    total_equity: Decimal | None = None
    total_assets: Decimal | None = None
    total_debt: Decimal | None = None
    operating_cf: Decimal | None = None
    free_cash_flow: Decimal | None = None
    eps: Decimal | None = None
    bvps: Decimal | None = None
    dps: Decimal | None = None
    shares_out: int | None = None


@dataclass(frozen=True, slots=True)
class MarketSession:
    """Satu sesi perdagangan dalam sehari, jam lokal exchange."""

    open_time: str  # "09:00"
    close_time: str  # "12:00"


@dataclass(frozen=True, slots=True)
class MarketCalendar:
    timezone: str
    sessions: list[MarketSession]
    trading_days: list[int]  # 0=Senin .. 6=Minggu


class MarketAdapter(Protocol):
    """Kontrak yang harus dipenuhi setiap adapter market. SPEC.md Bagian 6.1."""

    def list_instruments(self) -> list[InstrumentDTO]: ...

    def fetch_ohlcv(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> pd.DataFrame: ...

    def fetch_quote(self, symbols: list[str]) -> list[QuoteDTO]: ...

    def fetch_fundamentals(self, symbol: str) -> list[FundamentalDTO]: ...

    def market_calendar(self) -> MarketCalendar: ...


OHLCV_COLUMNS = ["open", "high", "low", "close", "volume", "value", "frequency"]
