from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Signal(Base):
    """Sinyal yang dihasilkan signal engine. SPEC.md Bagian 5.1 & 8.7."""

    __tablename__ = "signals"
    __table_args__ = (Index("ix_signals_instrument_mode_generated", "instrument_id", "mode", "generated_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("instruments.id"), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    confidence: Mapped[str] = mapped_column(String(10), nullable=False)

    reference_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    entry_low: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    entry_high: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    entry_trigger: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    tp1: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    tp2: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    tp3: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    risk_reward: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    atr_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)

    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rationale: Mapped[dict] = mapped_column(JSON, nullable=False)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
