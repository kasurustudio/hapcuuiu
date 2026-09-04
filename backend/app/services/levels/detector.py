"""Detektor Support/Resistance. SPEC.md Bagian 7.2.

Pure function: DataFrame OHLCV masuk, DataFrame level keluar. Mengikuti
algoritma 6 langkah di SPEC.md apa adanya untuk bagian yang dispesifikasi
persis (swing detection, clustering, formula strength, filter final).
Untuk bagian yang SPEC tidak beri angka pasti (bobot timeframe, strength
sumber tambahan seperti POC/pivot/round number/EMA/52w), dipakai nilai
default yang masuk akal dan didokumentasikan di komentar masing-masing —
bisa dikalibrasi ulang nanti tanpa mengubah struktur algoritma.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

from app.services.indicators.structure import pivot_points, swing_highs_lows, weekly_ohlc
from app.services.indicators.trend import ema
from app.services.indicators.volatility import atr
from app.services.indicators.volume import volume_profile

MAX_LEVELS_PER_SIDE = 8
MIN_STRENGTH = 40.0
SWING_LOOKBACK_BARS = 250
FRACTAL_N = 5

# SPEC.md Bagian 7.2 langkah 3: bobot komponen strength cluster berbasis swing.
WEIGHT_TOUCH_COUNT = 0.30
WEIGHT_VOLUME = 0.25
WEIGHT_RECENCY = 0.20
WEIGHT_WICK = 0.15
WEIGHT_TIMEFRAME = 0.10

# Tidak dispesifikasi presisi di SPEC — bobot relatif antar-timeframe,
# timeframe lebih tinggi dianggap lebih otoritatif untuk S/R.
TIMEFRAME_WEIGHT: dict[str, float] = {
    "1m": 20,
    "5m": 30,
    "15m": 40,
    "1h": 55,
    "4h": 70,
    "1d": 85,
    "1w": 100,
}

# Strength default untuk level dari sumber non-cluster (POC, pivot, dst) —
# tidak diberi formula presisi di SPEC, dipakai nilai tetap yang masuk akal.
SUPPLEMENTARY_STRENGTH = {
    "volume_profile_poc": 75.0,
    "pivot_daily": 65.0,
    "pivot_weekly": 70.0,
    "round_number": 50.0,
    "ema50": 55.0,
    "ema200": 60.0,
    "high_52w": 80.0,
    "low_52w": 80.0,
}


@dataclass(slots=True)
class LevelCandidate:
    price: float
    ts: datetime
    volume: float
    wick_size: float


def _round_number_step(price: float) -> float:
    """SPEC.md Bagian 7.2 langkah 4: kelipatan 50/100/500 tergantung harga."""
    if price < 1000:
        return 50.0
    if price < 10000:
        return 100.0
    return 500.0


def _normalize(values: np.ndarray) -> np.ndarray:
    """Min-max normalize ke rentang 0-100. Semua nilai sama -> 50 (netral)."""
    if len(values) == 0:
        return values
    lo, hi = values.min(), values.max()
    if hi == lo:
        return np.full_like(values, 50.0, dtype="float64")
    return (values - lo) / (hi - lo) * 100


def _recency_decay_score(days_since_test: np.ndarray) -> np.ndarray:
    """SPEC.md Bagian 7.2: recency_decay = exp(-days_since_test / 60), lalu
    diskalakan ke 0-100 supaya sepadan dengan komponen lain."""
    return np.exp(-days_since_test / 60) * 100


def _cluster_candidates(candidates: list[LevelCandidate], tolerance: float) -> list[list[LevelCandidate]]:
    """Bucketing sederhana: urutkan berdasarkan harga, mulai cluster baru
    kalau jarak ke titik sebelumnya > tolerance. SPEC.md Bagian 7.2 langkah 2
    eksplisit mengizinkan "agglomerative clustering sederhana atau bucketing"."""
    if not candidates:
        return []

    ordered = sorted(candidates, key=lambda c: c.price)
    clusters: list[list[LevelCandidate]] = [[ordered[0]]]

    for candidate in ordered[1:]:
        if candidate.price - clusters[-1][-1].price <= tolerance:
            clusters[-1].append(candidate)
        else:
            clusters.append([candidate])

    return clusters


def _swing_based_levels(df: pd.DataFrame, timeframe: str, now: datetime) -> pd.DataFrame:
    recent = df.tail(SWING_LOOKBACK_BARS)
    swings = swing_highs_lows(recent, n=FRACTAL_N)
    atr_series = atr(recent, period=14)
    tolerance = float(atr_series.iloc[-1]) * 0.5 if not np.isnan(atr_series.iloc[-1]) else 0.0

    candidates: list[LevelCandidate] = []
    for idx in recent.index[swings["swing_high"]]:
        row = recent.loc[idx]
        wick = row["high"] - max(row["open"], row["close"])
        candidates.append(LevelCandidate(price=float(row["high"]), ts=idx, volume=float(row.get("volume", 0)), wick_size=float(wick)))
    for idx in recent.index[swings["swing_low"]]:
        row = recent.loc[idx]
        wick = min(row["open"], row["close"]) - row["low"]
        candidates.append(LevelCandidate(price=float(row["low"]), ts=idx, volume=float(row.get("volume", 0)), wick_size=float(wick)))

    clusters = _cluster_candidates(candidates, tolerance)
    if not clusters:
        return pd.DataFrame(
            columns=["price", "strength", "touch_count", "source", "first_seen_at", "last_tested_at"]
        )

    prices = np.array([np.mean([c.price for c in cl]) for cl in clusters])
    touch_counts = np.array([len(cl) for cl in clusters], dtype="float64")
    total_volumes = np.array([sum(c.volume for c in cl) for cl in clusters])
    wick_sizes = np.array([np.mean([c.wick_size for c in cl]) for cl in clusters])
    last_tested = [max(c.ts for c in cl) for cl in clusters]
    first_seen = [min(c.ts for c in cl) for cl in clusters]

    days_since_test = np.array(
        [(pd.Timestamp(now) - pd.Timestamp(t)).total_seconds() / 86400 for t in last_tested]
    )
    days_since_test = np.clip(days_since_test, 0, None)

    touch_norm = _normalize(touch_counts)
    volume_norm = _normalize(total_volumes)
    wick_norm = _normalize(wick_sizes)
    recency = _recency_decay_score(days_since_test)
    timeframe_score = TIMEFRAME_WEIGHT.get(timeframe, 50.0)

    strength = (
        WEIGHT_TOUCH_COUNT * touch_norm
        + WEIGHT_VOLUME * volume_norm
        + WEIGHT_RECENCY * recency
        + WEIGHT_WICK * wick_norm
        + WEIGHT_TIMEFRAME * timeframe_score
    )

    return pd.DataFrame(
        {
            "price": prices,
            "strength": strength,
            "touch_count": touch_counts.astype(int),
            "source": "swing",
            "first_seen_at": first_seen,
            "last_tested_at": last_tested,
        }
    )


def _supplementary_levels(df: pd.DataFrame, current_price: float) -> pd.DataFrame:
    """SPEC.md Bagian 7.2 langkah 4: POC volume profile, pivot harian/
    mingguan, round number psikologis, EMA50/EMA200, high/low 52 minggu."""
    rows: list[dict] = []
    now = df.index[-1]

    # POC volume profile (dari 250 bar terakhir, konsisten dengan swing lookback).
    recent = df.tail(SWING_LOOKBACK_BARS)
    if len(recent) >= 10:
        vp = volume_profile(recent, num_buckets=50)
        rows.append(
            {"price": vp.poc, "strength": SUPPLEMENTARY_STRENGTH["volume_profile_poc"], "source": "volume_profile_poc"}
        )

    # Pivot harian: dari H/L/C bar sebelumnya.
    if len(df) >= 2 and isinstance(df.index, pd.DatetimeIndex):
        prev = df.iloc[-2]
        daily_pivot = pivot_points(prev["high"], prev["low"], prev["close"], method="classic")
        for key in ("pp", "r1", "s1"):
            rows.append(
                {"price": daily_pivot[key], "strength": SUPPLEMENTARY_STRENGTH["pivot_daily"], "source": "pivot_daily"}
            )

        # Pivot mingguan: dari H/L/C minggu sebelumnya.
        try:
            weekly = weekly_ohlc(df)
            if len(weekly) >= 2:
                prev_week = weekly.iloc[-2]
                weekly_pivot = pivot_points(prev_week["high"], prev_week["low"], prev_week["close"], method="classic")
                for key in ("pp", "r1", "s1"):
                    rows.append(
                        {
                            "price": weekly_pivot[key],
                            "strength": SUPPLEMENTARY_STRENGTH["pivot_weekly"],
                            "source": "pivot_weekly",
                        }
                    )
        except TypeError:
            pass

    # Round number psikologis di sekitar harga sekarang.
    step = _round_number_step(current_price)
    nearest = round(current_price / step) * step
    for offset in (-2, -1, 0, 1, 2):
        rows.append(
            {
                "price": nearest + offset * step,
                "strength": SUPPLEMENTARY_STRENGTH["round_number"],
                "source": "round_number",
            }
        )

    # EMA50/EMA200 sebagai dynamic S/R.
    if len(df) >= 50:
        ema50 = ema(df["close"], 50).iloc[-1]
        rows.append({"price": float(ema50), "strength": SUPPLEMENTARY_STRENGTH["ema50"], "source": "ema50"})
    if len(df) >= 200:
        ema200 = ema(df["close"], 200).iloc[-1]
        rows.append({"price": float(ema200), "strength": SUPPLEMENTARY_STRENGTH["ema200"], "source": "ema200"})

    # High/low 52 minggu (dibatasi jumlah bar yang tersedia).
    window = df.tail(252)
    rows.append({"price": float(window["high"].max()), "strength": SUPPLEMENTARY_STRENGTH["high_52w"], "source": "high_52w"})
    rows.append({"price": float(window["low"].min()), "strength": SUPPLEMENTARY_STRENGTH["low_52w"], "source": "low_52w"})

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["touch_count"] = 0
    result["first_seen_at"] = now
    result["last_tested_at"] = now
    return result


def _was_opposite_role_recently(df: pd.DataFrame, price: float, lookback: int = 20) -> bool:
    """role_flipped: level ini pernah berada di sisi berlawanan terhadap
    harga close dalam `lookback` bar terakhir (mis. dulu resistance -
    harga di bawahnya -, sekarang jadi support - harga di atasnya)."""
    if len(df) < 2:
        return False
    current_side = df["close"].iloc[-1] > price
    past_window = df["close"].iloc[-lookback - 1 : -1]
    if past_window.empty:
        return False
    past_sides = past_window > price
    return bool((past_sides != current_side).any())


def detect_price_levels(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Jalankan seluruh pipeline SPEC.md Bagian 7.2 dan kembalikan DataFrame
    level siap-simpan (kolom sama seperti tabel `price_levels`, minus
    `instrument_id` yang diisi caller).

    `df` wajib DataFrame OHLCV dengan DatetimeIndex, minimal beberapa
    puluh bar (idealnya >=250 untuk swing lookback penuh).
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("detect_price_levels() butuh DataFrame dengan DatetimeIndex")
    if df.empty:
        raise ValueError("df kosong")

    now = df.index[-1]
    current_price = float(df["close"].iloc[-1])

    swing_levels = _swing_based_levels(df, timeframe, now)
    supplementary = _supplementary_levels(df, current_price)

    all_levels = pd.concat([swing_levels, supplementary], ignore_index=True)
    all_levels = all_levels[all_levels["strength"] >= MIN_STRENGTH].copy()

    if all_levels.empty:
        return all_levels.assign(level_type=[], role_flipped=[])

    all_levels["level_type"] = np.where(all_levels["price"] < current_price, "support", "resistance")
    all_levels["role_flipped"] = all_levels["price"].apply(lambda p: _was_opposite_role_recently(df, p))
    all_levels["is_active"] = True
    all_levels["timeframe"] = timeframe

    supports = all_levels[all_levels["level_type"] == "support"].sort_values("strength", ascending=False).head(
        MAX_LEVELS_PER_SIDE
    )
    resistances = all_levels[all_levels["level_type"] == "resistance"].sort_values("strength", ascending=False).head(
        MAX_LEVELS_PER_SIDE
    )

    result = pd.concat([supports, resistances], ignore_index=True)
    return result.sort_values(["level_type", "price"]).reset_index(drop=True)
