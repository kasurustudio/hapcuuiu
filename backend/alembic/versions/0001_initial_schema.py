"""Initial schema — SPEC.md Bagian 5.1

Revision ID: 0001
Revises:
Create Date: 2026-09-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("disclaimer_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "instruments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("exchange", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("sub_sector", sa.String(100), nullable=True),
        sa.Column("board", sa.String(20), nullable=True),
        sa.Column("lot_size", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("listed_at", sa.Date(), nullable=True),
        sa.UniqueConstraint("symbol", "exchange", name="uq_instruments_symbol_exchange"),
    )
    op.create_index("ix_instruments_symbol", "instruments", ["symbol"])

    op.create_table(
        "ohlcv",
        sa.Column("instrument_id", sa.BigInteger(), sa.ForeignKey("instruments.id"), primary_key=True),
        sa.Column("timeframe", sa.String(5), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("open", sa.Numeric(18, 4), nullable=False),
        sa.Column("high", sa.Numeric(18, 4), nullable=False),
        sa.Column("low", sa.Numeric(18, 4), nullable=False),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("value", sa.Numeric(20, 2), nullable=True),
        sa.Column("frequency", sa.Integer(), nullable=True),
    )

    op.create_table(
        "indicator_snapshots",
        sa.Column("instrument_id", sa.BigInteger(), primary_key=True),
        sa.Column("timeframe", sa.String(5), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
    )

    op.create_table(
        "signals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("instrument_id", sa.BigInteger(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("confidence", sa.String(10), nullable=False),
        sa.Column("reference_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("entry_low", sa.Numeric(18, 4), nullable=True),
        sa.Column("entry_high", sa.Numeric(18, 4), nullable=True),
        sa.Column("entry_trigger", sa.Numeric(18, 4), nullable=True),
        sa.Column("stop_loss", sa.Numeric(18, 4), nullable=True),
        sa.Column("tp1", sa.Numeric(18, 4), nullable=True),
        sa.Column("tp2", sa.Numeric(18, 4), nullable=True),
        sa.Column("tp3", sa.Numeric(18, 4), nullable=True),
        sa.Column("risk_reward", sa.Numeric(6, 2), nullable=True),
        sa.Column("atr_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rationale", postgresql.JSONB(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_signals_instrument_mode_generated",
        "signals",
        ["instrument_id", "mode", sa.text("generated_at DESC")],
    )

    op.create_table(
        "price_levels",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("instrument_id", sa.BigInteger(), nullable=False),
        sa.Column("timeframe", sa.String(5), nullable=False),
        sa.Column("level_type", sa.String(20), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("strength", sa.Numeric(5, 2), nullable=False),
        sa.Column("touch_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source", sa.String(30), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "fundamentals",
        sa.Column("instrument_id", sa.BigInteger(), primary_key=True),
        sa.Column("period", sa.Date(), primary_key=True),
        sa.Column("period_type", sa.String(10), primary_key=True),
        sa.Column("revenue", sa.Numeric(20, 2), nullable=True),
        sa.Column("net_income", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_equity", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_assets", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_debt", sa.Numeric(20, 2), nullable=True),
        sa.Column("operating_cf", sa.Numeric(20, 2), nullable=True),
        sa.Column("free_cash_flow", sa.Numeric(20, 2), nullable=True),
        sa.Column("eps", sa.Numeric(18, 4), nullable=True),
        sa.Column("bvps", sa.Numeric(18, 4), nullable=True),
        sa.Column("dps", sa.Numeric(18, 4), nullable=True),
        sa.Column("shares_out", sa.BigInteger(), nullable=True),
    )

    op.create_table(
        "positions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("instrument_id", sa.BigInteger(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("mode", sa.String(20), nullable=True),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("qty", sa.BigInteger(), nullable=False),
        sa.Column("avg_entry", sa.Numeric(18, 4), nullable=False),
        sa.Column("stop_loss", sa.Numeric(18, 4), nullable=True),
        sa.Column("take_profit", sa.Numeric(18, 4), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exit_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("realized_pnl", sa.Numeric(20, 2), nullable=True),
        sa.Column("fees", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("signal_id", sa.BigInteger(), sa.ForeignKey("signals.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("emotion_tag", sa.String(30), nullable=True),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("instrument_id", sa.BigInteger(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("alert_type", sa.String(30), nullable=False),
        sa.Column("condition", postgresql.JSONB(), nullable=False),
        sa.Column("channels", postgresql.ARRAY(sa.String(50)), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
    )

    # TimescaleDB hypertable — partisi per bulan (SPEC.md Bagian 5.1).
    # Tersedia di image timescale/timescaledb yang dipakai docker-compose.yml,
    # TAPI tidak tersedia di managed Postgres seperti Supabase. Dibungkus DO
    # block: kalau extension tidak ada di server ini, langkah ini di-skip
    # dengan aman dan `ohlcv` tetap jadi tabel Postgres biasa (tetap benar
    # secara fungsional, hanya tanpa partisi otomatis TimescaleDB).
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb'
            ) THEN
                CREATE EXTENSION IF NOT EXISTS timescaledb;
                PERFORM create_hypertable(
                    'ohlcv', 'ts',
                    chunk_time_interval => INTERVAL '1 month',
                    migrate_data => true,
                    if_not_exists => true
                );
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("positions")
    op.drop_table("fundamentals")
    op.drop_table("price_levels")
    op.drop_index("ix_signals_instrument_mode_generated", table_name="signals")
    op.drop_table("signals")
    op.drop_table("indicator_snapshots")
    op.drop_table("ohlcv")
    op.drop_index("ix_instruments_symbol", table_name="instruments")
    op.drop_table("instruments")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
