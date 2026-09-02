from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OHLCV(Base):
    """Hypertable TimescaleDB, partisi per bulan. SPEC.md Bagian 5.1.

    Harga disimpan sebagai NUMERIC(18,4) — jangan pernah float (Bagian 4.3).
    """

    __tablename__ = "ohlcv"

    instrument_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("instruments.id"), primary_key=True
    )
    timeframe: Mapped[str] = mapped_column(String(5), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)

    open: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    value: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    frequency: Mapped[int | None] = mapped_column(Integer, nullable=True)
