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
