"""Candlestick pattern + filter konteks. SPEC.md Bagian 7.3.

Pure function: DataFrame OHLCV masuk, list dict pattern keluar. Setiap
pattern reversal (bullish/bearish) HANYA dilaporkan kalau konteksnya benar
(dekat support/resistance, atau setelah tren berlawanan minimal 5 bar) —
bukan cuma deteksi bentuk, sesuai instruksi eksplisit SPEC.md Bagian 7.3.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

MIN_TREND_BARS = 5
NEAR_LEVEL_TOLERANCE_PCT = 0.01  # 1% — "dekat support/resistance"

# Reliability score default per pattern. SPEC.md tidak memberi angka pasti;
# nilai berikut adalah estimasi wajar berbasis keandalan relatif pattern
# candlestick klasik (multi-candle & engulfing > single-candle sederhana).
RELIABILITY = {
    "doji": 40,
    "marubozu": 65,
    "hammer": 60,
    "inverted_hammer": 55,
    "shooting_star": 60,
    "hanging_man": 55,
    "bullish_engulfing": 70,
    "bearish_engulfing": 70,
    "morning_star": 78,
    "evening_star": 78,
    "piercing_line": 65,
    "dark_cloud_cover": 65,
    "three_white_soldiers": 75,
    "three_black_crows": 75,
}


@dataclass(frozen=True, slots=True)
class PatternMatch:
    name: str
    direction: str  # "bullish" | "bearish" | "neutral"
    bar_index: int
    reliability_score: float


def _body(row: pd.Series) -> float:
    return abs(row["close"] - row["open"])


def _range(row: pd.Series) -> float:
    return row["high"] - row["low"]


def _upper_wick(row: pd.Series) -> float:
    return row["high"] - max(row["open"], row["close"])


def _lower_wick(row: pd.Series) -> float:
    return min(row["open"], row["close"]) - row["low"]


def _is_bullish_candle(row: pd.Series) -> bool:
    return row["close"] > row["open"]


def _is_bearish_candle(row: pd.Series) -> bool:
    return row["close"] < row["open"]


def _is_downtrend(df: pd.DataFrame, pos: int, min_bars: int = MIN_TREND_BARS) -> bool:
    """True kalau `min_bars` bar SEBELUM `pos` (tidak termasuk bar di `pos`
    sendiri) menurun monoton — "downtrend minimal 5 bar" secara ketat,
    bukan cuma perbandingan titik awal-akhir (yang gampang salah positif
    kalau harga sebenarnya zig-zag/flat)."""
    if pos < min_bars:
        return False
    closes = df["close"].iloc[pos - min_bars : pos]
    return bool((closes.diff().dropna() < 0).all())


def _is_uptrend(df: pd.DataFrame, pos: int, min_bars: int = MIN_TREND_BARS) -> bool:
    if pos < min_bars:
        return False
    closes = df["close"].iloc[pos - min_bars : pos]
    return bool((closes.diff().dropna() > 0).all())


def _near_level(price: float, levels: pd.DataFrame | None, level_type: str) -> bool:
    if levels is None or levels.empty:
        return False
    subset = levels[levels["level_type"] == level_type]
    if subset.empty:
        return False
    return bool((subset["price"].sub(price).abs() / price <= NEAR_LEVEL_TOLERANCE_PCT).any())


def _bullish_reversal_context_ok(df: pd.DataFrame, pos: int, levels: pd.DataFrame | None) -> bool:
    """SPEC.md Bagian 7.3: bullish reversal valid kalau dekat support ATAU
    setelah downtrend minimal 5 bar. `pos` adalah index bar PERTAMA pattern
    (bukan bar terakhir) — supaya bar-bar pattern itu sendiri (yang sedang
    naik untuk pattern bullish) tidak ikut mengotori pengecekan tren."""
    return _is_downtrend(df, pos) or _near_level(df["low"].iloc[pos], levels, "support")


def _bearish_reversal_context_ok(df: pd.DataFrame, pos: int, levels: pd.DataFrame | None) -> bool:
    return _is_uptrend(df, pos) or _near_level(df["high"].iloc[pos], levels, "resistance")


# --- Deteksi bentuk (shape-only, belum difilter konteks) -------------------


def _is_doji(row: pd.Series) -> bool:
    range_ = _range(row)
    return range_ > 0 and _body(row) <= 0.1 * range_


def _is_marubozu(row: pd.Series) -> bool:
    range_ = _range(row)
    return range_ > 0 and _body(row) >= 0.95 * range_


def _is_hammer_shape(row: pd.Series) -> bool:
    """Body kecil di atas range, lower wick panjang (>=2x body), upper wick kecil.
    Bentuk ini sama untuk Hammer (konteks downtrend) & Hanging Man (uptrend)."""
    body = _body(row)
    if body == 0:
        return False
    return _lower_wick(row) >= 2 * body and _upper_wick(row) <= 0.3 * body


def _is_star_shape_bottom(row: pd.Series) -> bool:
    """Body kecil di bawah range, upper wick panjang. Bentuk ini sama untuk
    Inverted Hammer (konteks downtrend) & Shooting Star (uptrend)."""
    body = _body(row)
    if body == 0:
        return False
    return _upper_wick(row) >= 2 * body and _lower_wick(row) <= 0.3 * body


def _is_bullish_engulfing_shape(prev: pd.Series, cur: pd.Series) -> bool:
    return (
        _is_bearish_candle(prev)
        and _is_bullish_candle(cur)
        and cur["open"] <= prev["close"]
        and cur["close"] >= prev["open"]
        and _body(cur) > _body(prev)
    )


def _is_bearish_engulfing_shape(prev: pd.Series, cur: pd.Series) -> bool:
    return (
        _is_bullish_candle(prev)
        and _is_bearish_candle(cur)
        and cur["open"] >= prev["close"]
        and cur["close"] <= prev["open"]
        and _body(cur) > _body(prev)
    )


def _is_piercing_line_shape(prev: pd.Series, cur: pd.Series) -> bool:
    prev_mid = (prev["open"] + prev["close"]) / 2
    return (
        _is_bearish_candle(prev)
        and _is_bullish_candle(cur)
        and cur["open"] < prev["low"]
        and prev_mid < cur["close"] < prev["open"]
    )


def _is_dark_cloud_cover_shape(prev: pd.Series, cur: pd.Series) -> bool:
    prev_mid = (prev["open"] + prev["close"]) / 2
    return (
        _is_bullish_candle(prev)
        and _is_bearish_candle(cur)
        and cur["open"] > prev["high"]
        and prev["open"] < cur["close"] < prev_mid
    )


def _is_morning_star_shape(first: pd.Series, second: pd.Series, third: pd.Series) -> bool:
    first_mid = (first["open"] + first["close"]) / 2
    return (
        _is_bearish_candle(first)
        and _body(first) > 0
        and _body(second) <= 0.5 * _body(first)
        and _is_bullish_candle(third)
        and third["close"] > first_mid
    )


def _is_evening_star_shape(first: pd.Series, second: pd.Series, third: pd.Series) -> bool:
    first_mid = (first["open"] + first["close"]) / 2
    return (
        _is_bullish_candle(first)
        and _body(first) > 0
        and _body(second) <= 0.5 * _body(first)
        and _is_bearish_candle(third)
        and third["close"] < first_mid
    )


def _is_three_white_soldiers_shape(a: pd.Series, b: pd.Series, c: pd.Series) -> bool:
    return (
        _is_bullish_candle(a)
        and _is_bullish_candle(b)
        and _is_bullish_candle(c)
        and b["close"] > a["close"]
        and c["close"] > b["close"]
        and a["open"] < b["open"] < a["close"]
        and b["open"] < c["open"] < b["close"]
    )


def _is_three_black_crows_shape(a: pd.Series, b: pd.Series, c: pd.Series) -> bool:
    return (
        _is_bearish_candle(a)
        and _is_bearish_candle(b)
        and _is_bearish_candle(c)
        and b["close"] < a["close"]
        and c["close"] < b["close"]
        and a["close"] < b["open"] < a["open"]
        and b["close"] < c["open"] < b["open"]
    )


def detect_candlestick_patterns(df: pd.DataFrame, levels: pd.DataFrame | None = None) -> list[PatternMatch]:
    """Deteksi semua pattern candlestick SPEC.md Bagian 7.3 pada `df`.

    `levels` (opsional): output `detect_price_levels()` — dipakai untuk cek
    "dekat support/resistance" pada filter konteks. Kalau tidak diberikan,
    filter konteks hanya memakai syarat tren (downtrend/uptrend >=5 bar).
    """
    matches: list[PatternMatch] = []
    n = len(df)

    for i in range(n):
        row = df.iloc[i]

        if _is_doji(row):
            matches.append(PatternMatch("doji", "neutral", i, RELIABILITY["doji"]))
        elif _is_marubozu(row):
            direction = "bullish" if _is_bullish_candle(row) else "bearish"
            matches.append(PatternMatch("marubozu", direction, i, RELIABILITY["marubozu"]))

        if _is_hammer_shape(row):
            if _bullish_reversal_context_ok(df, i, levels):
                matches.append(PatternMatch("hammer", "bullish", i, RELIABILITY["hammer"]))
            elif _bearish_reversal_context_ok(df, i, levels):
                matches.append(PatternMatch("hanging_man", "bearish", i, RELIABILITY["hanging_man"]))

        if _is_star_shape_bottom(row):
            if _bullish_reversal_context_ok(df, i, levels):
                matches.append(PatternMatch("inverted_hammer", "bullish", i, RELIABILITY["inverted_hammer"]))
            elif _bearish_reversal_context_ok(df, i, levels):
                matches.append(PatternMatch("shooting_star", "bearish", i, RELIABILITY["shooting_star"]))

        if i >= 1:
            prev = df.iloc[i - 1]
            pattern_start = i - 1  # bar pertama pattern 2-candle

            if _is_bullish_engulfing_shape(prev, row) and _bullish_reversal_context_ok(df, pattern_start, levels):
                matches.append(PatternMatch("bullish_engulfing", "bullish", i, RELIABILITY["bullish_engulfing"]))

            if _is_bearish_engulfing_shape(prev, row) and _bearish_reversal_context_ok(df, pattern_start, levels):
                matches.append(PatternMatch("bearish_engulfing", "bearish", i, RELIABILITY["bearish_engulfing"]))

            if _is_piercing_line_shape(prev, row) and _bullish_reversal_context_ok(df, pattern_start, levels):
                matches.append(PatternMatch("piercing_line", "bullish", i, RELIABILITY["piercing_line"]))

            if _is_dark_cloud_cover_shape(prev, row) and _bearish_reversal_context_ok(df, pattern_start, levels):
                matches.append(PatternMatch("dark_cloud_cover", "bearish", i, RELIABILITY["dark_cloud_cover"]))

        if i >= 2:
            first, second, third = df.iloc[i - 2], df.iloc[i - 1], row
            pattern_start = i - 2  # bar pertama pattern 3-candle

            if _is_morning_star_shape(first, second, third) and _bullish_reversal_context_ok(df, pattern_start, levels):
                matches.append(PatternMatch("morning_star", "bullish", i, RELIABILITY["morning_star"]))

            if _is_evening_star_shape(first, second, third) and _bearish_reversal_context_ok(df, pattern_start, levels):
                matches.append(PatternMatch("evening_star", "bearish", i, RELIABILITY["evening_star"]))

            if _is_three_white_soldiers_shape(first, second, third) and _bullish_reversal_context_ok(
                df, pattern_start, levels
            ):
                matches.append(
                    PatternMatch("three_white_soldiers", "bullish", i, RELIABILITY["three_white_soldiers"])
                )

            if _is_three_black_crows_shape(first, second, third) and _bearish_reversal_context_ok(
                df, pattern_start, levels
            ):
                matches.append(PatternMatch("three_black_crows", "bearish", i, RELIABILITY["three_black_crows"]))

    return matches
