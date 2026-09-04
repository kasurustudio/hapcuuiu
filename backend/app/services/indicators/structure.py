"""Struktur harga: pivot points, fibonacci, swing high/low. SPEC.md Bagian 7.1.

Pure function: input skalar (H/L/C) atau DataFrame OHLCV, output dict/Series.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PIVOT_METHODS = ("classic", "fibonacci", "camarilla")


def pivot_points(high: float, low: float, close: float, method: str = "classic") -> dict[str, float]:
    """Pivot point + level support/resistance dari H/L/C periode sebelumnya
    (harian atau mingguan — tergantung H/L/C yang di-pass caller).
    """
    if method not in PIVOT_METHODS:
        raise ValueError(f"unknown pivot method: {method!r}, pilihan: {PIVOT_METHODS}")

    range_ = high - low
    pp = (high + low + close) / 3

    if method == "classic":
        return {
            "pp": pp,
            "r1": 2 * pp - low,
            "s1": 2 * pp - high,
            "r2": pp + range_,
            "s2": pp - range_,
            "r3": high + 2 * (pp - low),
            "s3": low - 2 * (high - pp),
        }

    if method == "fibonacci":
        return {
            "pp": pp,
            "r1": pp + 0.382 * range_,
            "s1": pp - 0.382 * range_,
            "r2": pp + 0.618 * range_,
            "s2": pp - 0.618 * range_,
            "r3": pp + 1.0 * range_,
            "s3": pp - 1.0 * range_,
        }

    # camarilla — pivot (pp) tidak dipakai secara resmi, tapi tetap
    # disertakan untuk konsistensi struktur output antar-method.
    return {
        "pp": pp,
        "r1": close + range_ * 1.1 / 12,
        "s1": close - range_ * 1.1 / 12,
        "r2": close + range_ * 1.1 / 6,
        "s2": close - range_ * 1.1 / 6,
        "r3": close + range_ * 1.1 / 4,
        "s3": close - range_ * 1.1 / 4,
        "r4": close + range_ * 1.1 / 2,
        "s4": close - range_ * 1.1 / 2,
    }


def weekly_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    """Resample OHLCV harian ke mingguan (dipakai untuk pivot mingguan).
    DataFrame `df` wajib punya DatetimeIndex.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("weekly_ohlc() butuh DataFrame dengan DatetimeIndex")

    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "volume" in df.columns:
        agg["volume"] = "sum"
    return df.resample("W-MON", closed="left", label="left").agg(agg).dropna()


FIB_RETRACEMENT_RATIOS = (0.236, 0.382, 0.5, 0.618, 0.786)
FIB_EXTENSION_RATIOS = (1.272, 1.618, 2.0)


def fibonacci_retracement(
    swing_low: float, swing_high: float, ratios: tuple[float, ...] = FIB_RETRACEMENT_RATIOS
) -> dict[float, float]:
    """Level retracement antara swing_low dan swing_high (uptrend pullback)."""
    diff = swing_high - swing_low
    return {ratio: swing_high - ratio * diff for ratio in ratios}


def fibonacci_extension(
    swing_low: float, swing_high: float, ratios: tuple[float, ...] = FIB_EXTENSION_RATIOS
) -> dict[float, float]:
    """Level extension di atas swing_high, diproyeksikan dari swing_low."""
    diff = swing_high - swing_low
    return {ratio: swing_low + ratio * diff for ratio in ratios}


def swing_highs_lows(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Deteksi swing high/low fractal: titik dengan high/low tertinggi/
    terendah dibanding `n` bar di kiri DAN kanan. SPEC.md Bagian 7.1 & 7.2:
    "fractal, lookback 5 bar kiri-kanan"."""
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    n_bars = len(df)

    swing_high = np.zeros(n_bars, dtype=bool)
    swing_low = np.zeros(n_bars, dtype=bool)

    for i in range(n, n_bars - n):
        high_window = high[i - n : i + n + 1]
        low_window = low[i - n : i + n + 1]
        if high[i] == high_window.max() and (high_window == high[i]).sum() == 1:
            swing_high[i] = True
        if low[i] == low_window.min() and (low_window == low[i]).sum() == 1:
            swing_low[i] = True

    return pd.DataFrame({"swing_high": swing_high, "swing_low": swing_low}, index=df.index)
