from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Fundamental(Base):
    """Data fundamental untuk mode investing. SPEC.md Bagian 5.1 & 10."""

    __tablename__ = "fundamentals"

    instrument_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    period: Mapped[date] = mapped_column(Date, primary_key=True)
    period_type: Mapped[str] = mapped_column(String(10), primary_key=True)

    revenue: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    net_income: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    total_equity: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    total_assets: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    total_debt: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    operating_cf: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    free_cash_flow: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    eps: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    bvps: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    dps: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    shares_out: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
