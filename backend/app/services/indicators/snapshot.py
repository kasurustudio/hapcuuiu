"""Rangkai semua indikator jadi satu snapshot (nilai terbaru saja).

Pure function: DataFrame OHLCV masuk, dict keluar — bentuknya cocok dengan
`indicator_snapshots.payload` (SPEC.md Bagian 5.1: "payload JSONB —
{rsi14: 58.2, ema20: 9250, ...}"). Periode yang dipakai di sini adalah
default umum (SPEC.md Bagian 7.1); pemilihan indikator per-mode dari
`config/modes.yaml` adalah scope Fase 3 (signal engine), belum di sini.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.indicators import momentum, structure, trend, volatility, volume as vol_ind


def _clean(value) -> float | None:
    """Konversi numpy scalar / NaN ke tipe JSON-serializable (None kalau NaN)."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return float(value)


def _latest(series: pd.Series) -> float | None:
    if series is None or len(series) == 0:
        return None
    return _clean(series.iloc[-1])


def _latest_row(df: pd.DataFrame) -> dict:
    if df is None or len(df) == 0:
        return {}
    return {col: _clean(df[col].iloc[-1]) for col in df.columns}


def build_indicator_snapshot(df: pd.DataFrame) -> dict:
    """Hitung seluruh indikator SPEC.md Bagian 7.1 dan ambil nilai
    terbarunya saja. `df` wajib DataFrame OHLCV (open/high/low/close/volume)
    dengan DatetimeIndex, minimal beberapa puluh bar.
    """
    close = df["close"]

    trend_payload = {
        "sma5": _latest(trend.sma(close, 5)),
        "sma10": _latest(trend.sma(close, 10)),
        "sma20": _latest(trend.sma(close, 20)),
        "sma50": _latest(trend.sma(close, 50)),
        "sma100": _latest(trend.sma(close, 100)),
        "sma200": _latest(trend.sma(close, 200)),
        "ema8": _latest(trend.ema(close, 8)),
        "ema13": _latest(trend.ema(close, 13)),
        "ema21": _latest(trend.ema(close, 21)),
        "ema50": _latest(trend.ema(close, 50)),
        "ema200": _latest(trend.ema(close, 200)),
        "macd": _latest_row(trend.macd(close)),
        "adx": _latest_row(trend.adx(df)),
        "parabolic_sar": _latest(trend.parabolic_sar(df)),
        "supertrend": _latest_row(trend.supertrend(df)),
        "ichimoku": _latest_row(trend.ichimoku(df)),
    }

    rsi_series = momentum.rsi(close, 14)
    divergence = momentum.detect_rsi_divergence(close, rsi_series)
    momentum_payload = {
        "rsi14": _latest(rsi_series),
        "rsi14_divergence": divergence.iloc[-1] if len(divergence) else None,
        "stochastic": _latest_row(momentum.stochastic(df)),
        "stochastic_rsi": _latest_row(momentum.stochastic_rsi(close)),
        "cci20": _latest(momentum.cci(df, 20)),
        "williams_r14": _latest(momentum.williams_r(df, 14)),
        "roc12": _latest(momentum.roc(close, 12)),
        "mfi14": _latest(momentum.mfi(df, 14)) if "volume" in df.columns else None,
    }

    volatility_payload = {
        "atr14": _latest(volatility.atr(df, 14)),
        "atr_percent": _latest(volatility.atr_percent(df, 14)),
        "bollinger": _latest_row(volatility.bollinger_bands(close)),
        "keltner": _latest_row(volatility.keltner_channel(df)),
        "donchian": _latest_row(volatility.donchian_channel(df)),
        "historical_volatility": _latest(volatility.historical_volatility(close)),
    }

    volume_payload = {}
    if "volume" in df.columns:
        volume_payload = {
            "volume_ma20": _latest(vol_ind.volume_ma(df["volume"], 20)),
            "relative_volume": _latest(vol_ind.relative_volume(df["volume"], 20)),
            "obv": _latest(vol_ind.obv(close, df["volume"])),
            "accumulation_distribution": _latest(vol_ind.accumulation_distribution(df)),
        }
        if isinstance(df.index, pd.DatetimeIndex):
            volume_payload["vwap"] = _latest(vol_ind.vwap(df))
        if len(df) >= 10:
            vp = vol_ind.volume_profile(df.tail(250))
            volume_payload["volume_profile"] = {"poc": vp.poc, "vah": vp.vah, "val": vp.val}

    structure_payload = {}
    if len(df) >= 2:
        prev = df.iloc[-2]
        structure_payload["pivot_daily"] = structure.pivot_points(
            float(prev["high"]), float(prev["low"]), float(prev["close"]), method="classic"
        )
    swings = structure.swing_highs_lows(df, n=5)
    swing_lows = df.index[swings["swing_low"]]
    swing_highs = df.index[swings["swing_high"]]
    if len(swing_lows) and len(swing_highs):
        last_low = float(df.loc[swing_lows[-1], "low"])
        last_high = float(df.loc[swing_highs[-1], "high"])
        if last_high > last_low:
            structure_payload["fibonacci_retracement"] = structure.fibonacci_retracement(last_low, last_high)
            structure_payload["fibonacci_extension"] = structure.fibonacci_extension(last_low, last_high)

    return {
        "trend": trend_payload,
        "momentum": momentum_payload,
        "volatility": volatility_payload,
        "volume": volume_payload,
        "structure": structure_payload,
    }
