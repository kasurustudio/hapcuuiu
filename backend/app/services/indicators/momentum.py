"""Indikator momentum. SPEC.md Bagian 7.1.

Pure function: DataFrame OHLCV masuk, Series/DataFrame keluar.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.indicators.common import wilder_smooth


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI Wilder's smoothing (bukan simple moving average)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = wilder_smooth(gain, period)
    avg_loss = wilder_smooth(loss, period)

    rs = avg_gain / avg_loss
    result = 100 - (100 / (1 + rs))
    # Kasus avg_loss == 0 (harga naik terus): RS -> inf, RSI harus 100.
    result = result.where(avg_loss != 0, 100.0)
    return result


def _fractal_extrema_positions(values: pd.Series, n: int, find_max: bool) -> list[int]:
    """Posisi (integer, 0-indexed) titik ekstrem lokal fractal: nilai di
    posisi i adalah maks/min dibanding n bar kiri DAN n bar kanan."""
    arr = values.to_numpy()
    positions = []
    for i in range(n, len(arr) - n):
        window = arr[i - n : i + n + 1]
        center = arr[i]
        if find_max and center == window.max() and (window == center).sum() == 1:
            positions.append(i)
        if not find_max and center == window.min() and (window == center).sum() == 1:
            positions.append(i)
    return positions


def detect_rsi_divergence(close: pd.Series, rsi_series: pd.Series, n: int = 3, lookback: int = 20) -> pd.Series:
    """Deteksi divergence bullish/bearish sederhana: bandingkan swing low/high
    harga terakhir dua kali (fractal, lookback n bar kiri-kanan) dengan RSI
    pada titik yang sama. Return Series label: "bullish" | "bearish" | None
    per bar (index posisi integer 0-based).

    SPEC.md Bagian 7.1: "RSI (14) — plus deteksi divergence bullish/bearish".
    """
    labels = pd.Series([None] * len(close), index=close.index, dtype=object)

    swing_low_pos = _fractal_extrema_positions(close, n, find_max=False)
    swing_high_pos = _fractal_extrema_positions(close, n, find_max=True)

    for i in range(1, len(swing_low_pos)):
        prev_i, cur_i = swing_low_pos[i - 1], swing_low_pos[i]
        if cur_i - prev_i > lookback:
            continue
        price_lower_low = close.iloc[cur_i] < close.iloc[prev_i]
        rsi_higher_low = rsi_series.iloc[cur_i] > rsi_series.iloc[prev_i]
        if price_lower_low and rsi_higher_low:
            labels.iloc[cur_i] = "bullish"

    for i in range(1, len(swing_high_pos)):
        prev_i, cur_i = swing_high_pos[i - 1], swing_high_pos[i]
        if cur_i - prev_i > lookback:
            continue
        price_higher_high = close.iloc[cur_i] > close.iloc[prev_i]
        rsi_lower_high = rsi_series.iloc[cur_i] < rsi_series.iloc[prev_i]
        if price_higher_high and rsi_lower_high:
            labels.iloc[cur_i] = "bearish"

    return labels


def stochastic(df: pd.DataFrame, k_period: int = 14, k_smooth: int = 3, d_period: int = 3) -> pd.DataFrame:
    """Stochastic Oscillator (%K di-smooth, %D = SMA %K)."""
    lowest_low = df["low"].rolling(k_period).min()
    highest_high = df["high"].rolling(k_period).max()
    raw_k = 100 * (df["close"] - lowest_low) / (highest_high - lowest_low)
    k = raw_k.rolling(k_smooth).mean()
    d = k.rolling(d_period).mean()
    return pd.DataFrame({"k": k, "d": d})


def stochastic_rsi(
    close: pd.Series, rsi_period: int = 14, stoch_period: int = 14, k_smooth: int = 3, d_period: int = 3
) -> pd.DataFrame:
    """Stochastic RSI: Stochastic diterapkan pada RSI, bukan pada harga."""
    rsi_series = rsi(close, rsi_period)
    lowest = rsi_series.rolling(stoch_period).min()
    highest = rsi_series.rolling(stoch_period).max()
    raw_k = 100 * (rsi_series - lowest) / (highest - lowest)
    k = raw_k.rolling(k_smooth).mean()
    d = k.rolling(d_period).mean()
    return pd.DataFrame({"k": k, "d": d})


def cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Commodity Channel Index."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    sma_tp = typical_price.rolling(period).mean()
    mean_dev = typical_price.rolling(period).apply(lambda x: (x - x.mean()).abs().mean(), raw=False)
    return (typical_price - sma_tp) / (0.015 * mean_dev)


def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Williams %R."""
    highest_high = df["high"].rolling(period).max()
    lowest_low = df["low"].rolling(period).min()
    return -100 * (highest_high - df["close"]) / (highest_high - lowest_low)


def roc(close: pd.Series, period: int = 12) -> pd.Series:
    """Rate of Change (%)."""
    return 100 * (close - close.shift(period)) / close.shift(period)


def mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Money Flow Index — momentum berbobot volume."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    money_flow = typical_price * df["volume"]

    price_diff = typical_price.diff()
    positive_flow = money_flow.where(price_diff > 0, 0.0)
    negative_flow = money_flow.where(price_diff < 0, 0.0)

    positive_sum = positive_flow.rolling(period).sum()
    negative_sum = negative_flow.rolling(period).sum()

    money_ratio = positive_sum / negative_sum
    result = 100 - (100 / (1 + money_ratio))
    result = result.where(negative_sum != 0, 100.0)
    return result
