"""YFinance-based MarketAdapter untuk IDX. SPEC.md Bagian 6.2.

Provider gratis, cocok untuk daily OHLCV. Intraday (1m/5m) terbatas oleh
yfinance (maksimal ~60 hari ke belakang) — cukup untuk mode degraded
(swing & investing), tidak untuk scalping/day trading real-time.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pandas as pd
import yfinance as yf

from app.services.market_data.base import (
    FundamentalDTO,
    InstrumentDTO,
    MarketAdapter,
    MarketCalendar,
    MarketSession,
    QuoteDTO,
)

IDX_SUFFIX = ".JK"

# Timeframe SPEC (Bagian 1.1 / 7) -> interval yfinance
_TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "60m",
    "4h": "60m",  # yfinance tidak punya 4h native; di-resample di caller.
    "1d": "1d",
    "1w": "1wk",
    "1mo": "1mo",
}


def to_yf_symbol(symbol: str) -> str:
    return f"{symbol.upper()}{IDX_SUFFIX}"


def from_yf_symbol(yf_symbol: str) -> str:
    return yf_symbol.upper().removesuffix(IDX_SUFFIX)


class YFinanceIDXAdapter:
    """Implementasi `MarketAdapter` untuk Bursa Efek Indonesia via yfinance."""

    exchange = "IDX"

    def list_instruments(self) -> list[InstrumentDTO]:
        raise NotImplementedError(
            "yfinance tidak menyediakan daftar emiten IDX. Gunakan sumber "
            "statis (mis. daftar LQ45/IDX konstituen) yang di-seed manual "
            "atau di-scrape terpisah, lalu isi via sync_instruments job."
        )

    def fetch_ohlcv(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> pd.DataFrame:
        if timeframe not in _TIMEFRAME_MAP:
            raise ValueError(f"unsupported timeframe: {timeframe!r}")

        yf_symbol = to_yf_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        raw = ticker.history(
            start=start,
            end=end,
            interval=_TIMEFRAME_MAP[timeframe],
            auto_adjust=True,  # split & dividend adjusted close, SPEC 6.3
            actions=False,
        )

        if raw.empty:
            return _empty_ohlcv_frame()

        return _normalize_yf_dataframe(raw)

    def fetch_quote(self, symbols: list[str]) -> list[QuoteDTO]:
        quotes: list[QuoteDTO] = []
        for symbol in symbols:
            yf_symbol = to_yf_symbol(symbol)
            info = yf.Ticker(yf_symbol).fast_info
            price = Decimal(str(info["last_price"]))
            prev_close = Decimal(str(info["previous_close"]))
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else Decimal(0)
            quotes.append(
                QuoteDTO(
                    symbol=symbol,
                    price=price,
                    change=change,
                    change_pct=change_pct,
                    volume=int(info.get("last_volume", 0) or 0),
                    ts=datetime.now(),
                )
            )
        return quotes

    def fetch_fundamentals(self, symbol: str) -> list[FundamentalDTO]:
        yf_symbol = to_yf_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        financials = ticker.quarterly_financials
        balance_sheet = ticker.quarterly_balance_sheet
        cashflow = ticker.quarterly_cashflow

        results: list[FundamentalDTO] = []
        for period_ts in financials.columns:
            period: date = period_ts.date() if hasattr(period_ts, "date") else period_ts
            results.append(
                FundamentalDTO(
                    symbol=symbol,
                    period=period,
                    period_type="quarterly",
                    revenue=_safe_decimal(financials, "Total Revenue", period_ts),
                    net_income=_safe_decimal(financials, "Net Income", period_ts),
                    total_equity=_safe_decimal(
                        balance_sheet, "Stockholders Equity", period_ts
                    ),
                    total_assets=_safe_decimal(balance_sheet, "Total Assets", period_ts),
                    total_debt=_safe_decimal(balance_sheet, "Total Debt", period_ts),
                    operating_cf=_safe_decimal(
                        cashflow, "Operating Cash Flow", period_ts
                    ),
                    free_cash_flow=_safe_decimal(cashflow, "Free Cash Flow", period_ts),
                )
            )
        return results

    def market_calendar(self) -> MarketCalendar:
        # Jam bursa IDX (WIB): Sesi I 09:00-11:30, Sesi II 13:30-15:00 (Jum'at 14:00-16:00).
        return MarketCalendar(
            timezone="Asia/Jakarta",
            sessions=[
                MarketSession("09:00", "11:30"),
                MarketSession("13:30", "15:00"),
            ],
            trading_days=[0, 1, 2, 3, 4],  # Senin-Jumat
        )


def _empty_ohlcv_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["open", "high", "low", "close", "volume", "value", "frequency"]
    ).astype(
        {
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "int64",
        }
    )


def _normalize_yf_dataframe(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )[["open", "high", "low", "close", "volume"]].copy()

    df.index.name = "ts"
    if df.index.tz is None:
        df.index = df.index.tz_localize("Asia/Jakarta").tz_convert("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    # yfinance tidak menyediakan turnover (value) & frequency untuk IDX;
    # aproksimasi value dari close * volume, frequency tidak tersedia.
    df["value"] = df["close"] * df["volume"]
    df["frequency"] = pd.NA

    return df


def _safe_decimal(df: pd.DataFrame, row_label: str, col) -> Decimal | None:
    if row_label not in df.index or col not in df.columns:
        return None
    value = df.loc[row_label, col]
    if pd.isna(value):
        return None
    return Decimal(str(value))
