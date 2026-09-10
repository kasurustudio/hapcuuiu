from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Alert(Base):
    """Alert user (price cross, entry zone, dsb). SPEC.md Bagian 5.1."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("instruments.id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    condition: Mapped[dict] = mapped_column(JSON, nullable=False)
    # JSON (bukan ARRAY Postgres) supaya portabel ke SQLite (desktop build).
    channels: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
