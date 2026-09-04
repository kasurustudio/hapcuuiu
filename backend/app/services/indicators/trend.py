"""Indikator trend. SPEC.md Bagian 7.1.

Semua fungsi pure: DataFrame OHLCV masuk, Series/DataFrame keluar, tanpa
I/O (CLAUDE.md). DataFrame input wajib punya kolom open/high/low/close
(volume tidak dipakai di modul ini).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.indicators.common import true_range, wilder_smooth


def sma(close: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return close.rolling(window=period).mean()


def ema(close: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return close.ewm(span=period, adjust=False).mean()


def macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    """MACD line, signal line, histogram."""
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "histogram": histogram}
    )


def adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """ADX + DI+/DI-. Wilder's smoothing, formula standar."""
    up_move = df["high"].diff()
    down_move = -df["low"].diff()

    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=df.index,
    )

    tr = true_range(df)
    atr = wilder_smooth(tr, period)
    smoothed_plus_dm = wilder_smooth(plus_dm, period)
    smoothed_minus_dm = wilder_smooth(minus_dm, period)

    plus_di = 100 * smoothed_plus_dm / atr
    minus_di = 100 * smoothed_minus_dm / atr

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx_line = wilder_smooth(dx, period)

    return pd.DataFrame({"adx": adx_line, "plus_di": plus_di, "minus_di": minus_di})


def parabolic_sar(
    df: pd.DataFrame, af_start: float = 0.02, af_step: float = 0.02, af_max: float = 0.2
) -> pd.Series:
    """Parabolic SAR — algoritma iteratif (bukan vektorisasi murni, sesuai
    sifat asli indikator ini: nilai bar-t bergantung pada state bar-(t-1))."""
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    n = len(df)
    sar = np.full(n, np.nan)

    if n < 2:
        return pd.Series(sar, index=df.index)

    uptrend = high[1] >= high[0]
    ep = high[0] if uptrend else low[0]
    af = af_start
    sar[0] = low[0] if uptrend else high[0]

    for i in range(1, n):
        prev_sar = sar[i - 1]
        new_sar = prev_sar + af * (ep - prev_sar)

        if uptrend:
            new_sar = min(new_sar, low[i - 1], low[i - 2] if i >= 2 else low[i - 1])
            if low[i] < new_sar:
                uptrend = False
                new_sar = ep
                ep = low[i]
                af = af_start
            else:
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + af_step, af_max)
        else:
            new_sar = max(new_sar, high[i - 1], high[i - 2] if i >= 2 else high[i - 1])
            if high[i] > new_sar:
                uptrend = True
                new_sar = ep
                ep = high[i]
                af = af_start
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + af_step, af_max)

        sar[i] = new_sar

    return pd.Series(sar, index=df.index)


def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """SuperTrend — nilai garis + arah ("up"/"down")."""
    tr = true_range(df)
    atr = wilder_smooth(tr, period)

    hl2 = (df["high"] + df["low"]) / 2
    upper_basic = hl2 + multiplier * atr
    lower_basic = hl2 - multiplier * atr

    n = len(df)
    upper = np.full(n, np.nan)
    lower = np.full(n, np.nan)
    direction = np.full(n, "up", dtype=object)
    line = np.full(n, np.nan)

    close = df["close"].to_numpy()
    upper_basic_np = upper_basic.to_numpy()
    lower_basic_np = lower_basic.to_numpy()

    start = period  # butuh ATR valid dulu
    if n <= start:
        return pd.DataFrame({"supertrend": line, "direction": direction}, index=df.index)

    upper[start] = upper_basic_np[start]
    lower[start] = lower_basic_np[start]
    direction[start] = "up" if close[start] > lower[start] else "down"
    line[start] = lower[start] if direction[start] == "up" else upper[start]

    for i in range(start + 1, n):
        upper[i] = (
            upper_basic_np[i]
            if (upper_basic_np[i] < upper[i - 1] or close[i - 1] > upper[i - 1])
            else upper[i - 1]
        )
        lower[i] = (
            lower_basic_np[i]
            if (lower_basic_np[i] > lower[i - 1] or close[i - 1] < lower[i - 1])
            else lower[i - 1]
        )

        if direction[i - 1] == "up":
            direction[i] = "down" if close[i] < lower[i] else "up"
        else:
            direction[i] = "up" if close[i] > upper[i] else "down"

        line[i] = lower[i] if direction[i] == "up" else upper[i]

    return pd.DataFrame({"supertrend": line, "direction": direction}, index=df.index)


def ichimoku(
    df: pd.DataFrame, tenkan: int = 9, kijun: int = 26, senkou_b: int = 52
) -> pd.DataFrame:
    """Ichimoku Cloud. Senkou span A/B digeser maju `kijun` bar (proyeksi ke
    depan, konvensi standar)."""
    tenkan_sen = (df["high"].rolling(tenkan).max() + df["low"].rolling(tenkan).min()) / 2
    kijun_sen = (df["high"].rolling(kijun).max() + df["low"].rolling(kijun).min()) / 2
    senkou_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun)
    senkou_b_line = (
        (df["high"].rolling(senkou_b).max() + df["low"].rolling(senkou_b).min()) / 2
    ).shift(kijun)
    chikou_span = df["close"].shift(-kijun)

    return pd.DataFrame(
        {
            "tenkan_sen": tenkan_sen,
            "kijun_sen": kijun_sen,
            "senkou_span_a": senkou_a,
            "senkou_span_b": senkou_b_line,
            "chikou_span": chikou_span,
        }
    )
