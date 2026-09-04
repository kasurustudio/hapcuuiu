"""Indikator volatilitas. SPEC.md Bagian 7.1.

Pure function: DataFrame OHLCV masuk, Series/DataFrame keluar.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.indicators.common import true_range, wilder_smooth


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (Wilder's smoothing)."""
    return wilder_smooth(true_range(df), period)


def atr_percent(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR% = ATR / close * 100."""
    return atr(df, period) / df["close"] * 100


def bollinger_bands(close: pd.Series, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands + Bandwidth + %B."""
    middle = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)
    upper = middle + num_std * std
    lower = middle - num_std * std
    bandwidth = (upper - lower) / middle * 100
    percent_b = (close - lower) / (upper - lower)
    return pd.DataFrame(
        {
            "middle": middle,
            "upper": upper,
            "lower": lower,
            "bandwidth": bandwidth,
            "percent_b": percent_b,
        }
    )


def keltner_channel(
    df: pd.DataFrame, ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0
) -> pd.DataFrame:
    """Keltner Channel: basis EMA, lebar kelipatan ATR."""
    middle = df["close"].ewm(span=ema_period, adjust=False).mean()
    atr_series = atr(df, atr_period)
    upper = middle + multiplier * atr_series
    lower = middle - multiplier * atr_series
    return pd.DataFrame({"middle": middle, "upper": upper, "lower": lower})


def donchian_channel(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Donchian Channel: highest high / lowest low `period` bar."""
    upper = df["high"].rolling(period).max()
    lower = df["low"].rolling(period).min()
    middle = (upper + lower) / 2
    return pd.DataFrame({"upper": upper, "lower": lower, "middle": middle})


def historical_volatility(close: pd.Series, period: int = 20, trading_days: int = 252) -> pd.Series:
    """Historical Volatility tahunan (%), dari std log return `period` hari."""
    log_returns = np.log(close / close.shift(1))
    return log_returns.rolling(period).std(ddof=0) * np.sqrt(trading_days) * 100
