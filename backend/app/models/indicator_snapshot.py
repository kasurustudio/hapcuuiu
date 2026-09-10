from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IndicatorSnapshot(Base):
    """Cache hasil perhitungan indikator. SPEC.md Bagian 5.1."""

    __tablename__ = "indicator_snapshots"

    instrument_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(5), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
