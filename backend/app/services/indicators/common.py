"""Fungsi bantu yang dipakai lintas kategori indikator (trend, momentum,
volatilitas). Pure function, tanpa I/O — SPEC.md Bagian 4.3.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    ranges = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """Wilder's smoothing (dipakai ATR/ADX/RSI) — beda dengan EMA biasa:
    alpha = 1/period, dan nilai awal adalah rata-rata sederhana `period` bar
    pertama, bukan nilai bar pertama."""
    result = pd.Series(np.nan, index=series.index, dtype="float64")
    if len(series) < period:
        return result

    first_valid_pos = series.first_valid_index()
    if first_valid_pos is None:
        return result
    start_pos = series.index.get_loc(first_valid_pos)

    initial = series.iloc[start_pos : start_pos + period].mean()
    result.iloc[start_pos + period - 1] = initial

    prev = initial
    for i in range(start_pos + period, len(series)):
        current = (prev * (period - 1) + series.iloc[i]) / period
        result.iloc[i] = current
        prev = current

    return result
