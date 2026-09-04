"""Indikator volume. SPEC.md Bagian 7.1.

Pure function: DataFrame OHLCV masuk, Series/DataFrame/dataclass keluar.
`vwap()` butuh DataFrame dengan DatetimeIndex (kolom `ts` sebagai index)
supaya bisa reset per sesi harian.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def volume_ma(volume: pd.Series, period: int = 20) -> pd.Series:
    """Volume Moving Average."""
    return volume.rolling(period).mean()


def relative_volume(volume: pd.Series, period: int = 20) -> pd.Series:
    """Relative Volume = volume / SMA(volume, period)."""
    return volume / volume_ma(volume, period)


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On Balance Volume."""
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def typical_price(df: pd.DataFrame) -> pd.Series:
    return (df["high"] + df["low"] + df["close"]) / 3


def vwap(df: pd.DataFrame) -> pd.Series:
    """VWAP harian, reset tiap sesi (per tanggal kalender pada index).

    DataFrame `df` wajib punya DatetimeIndex.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("vwap() butuh DataFrame dengan DatetimeIndex")

    tp = typical_price(df)
    tp_vol = tp * df["volume"]
    session = df.index.date

    cum_tp_vol = tp_vol.groupby(session).cumsum()
    cum_vol = df["volume"].groupby(session).cumsum()
    return cum_tp_vol / cum_vol


def anchored_vwap(df: pd.DataFrame, anchor_index) -> pd.Series:
    """VWAP dihitung kumulatif dari titik anchor (mis. swing point) sampai
    akhir data — TIDAK reset harian, beda dengan `vwap()`. Bar sebelum
    anchor bernilai NaN.
    """
    tp = typical_price(df)
    tp_vol = tp * df["volume"]

    result = pd.Series(np.nan, index=df.index)
    anchor_pos = df.index.get_loc(anchor_index)

    window_tp_vol = tp_vol.iloc[anchor_pos:]
    window_vol = df["volume"].iloc[anchor_pos:]
    result.iloc[anchor_pos:] = (window_tp_vol.cumsum() / window_vol.cumsum()).to_numpy()

    return result


def accumulation_distribution(df: pd.DataFrame) -> pd.Series:
    """Accumulation/Distribution Line."""
    high_low_range = df["high"] - df["low"]
    money_flow_multiplier = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / high_low_range
    money_flow_multiplier = money_flow_multiplier.where(high_low_range != 0, 0.0)
    money_flow_volume = money_flow_multiplier * df["volume"]
    return money_flow_volume.cumsum()


@dataclass(frozen=True, slots=True)
class VolumeProfileResult:
    poc: float  # Point of Control — harga dengan volume tertinggi
    vah: float  # Value Area High
    val: float  # Value Area Low
    buckets: pd.DataFrame  # kolom: price_low, price_high, volume


def volume_profile(
    df: pd.DataFrame, num_buckets: int = 50, value_area_pct: float = 0.7
) -> VolumeProfileResult:
    """Volume Profile: distribusi volume per level harga (POC, VAH, VAL).
    SPEC.md Bagian 7.1: "bucket 50 level harga"."""
    price_min = df["low"].min()
    price_max = df["high"].max()

    if price_min == price_max:
        mid = float(price_min)
        buckets = pd.DataFrame(
            {"price_low": [mid], "price_high": [mid], "volume": [float(df["volume"].sum())]}
        )
        return VolumeProfileResult(poc=mid, vah=mid, val=mid, buckets=buckets)

    edges = np.linspace(price_min, price_max, num_buckets + 1)
    tp = typical_price(df)
    bucket_idx = np.clip(np.digitize(tp, edges) - 1, 0, num_buckets - 1)

    bucket_volume = np.zeros(num_buckets)
    for idx, vol in zip(bucket_idx, df["volume"]):
        bucket_volume[idx] += vol

    buckets = pd.DataFrame(
        {
            "price_low": edges[:-1],
            "price_high": edges[1:],
            "volume": bucket_volume,
        }
    )
    buckets["price_mid"] = (buckets["price_low"] + buckets["price_high"]) / 2

    poc_row = buckets.loc[buckets["volume"].idxmax()]
    poc = float(poc_row["price_mid"])

    total_volume = buckets["volume"].sum()
    target_volume = total_volume * value_area_pct

    ordered = buckets.sort_values("volume", ascending=False)
    cum = 0.0
    included_idx = []
    for idx, row in ordered.iterrows():
        cum += row["volume"]
        included_idx.append(idx)
        if cum >= target_volume:
            break

    included = buckets.loc[included_idx]
    vah = float(included["price_high"].max())
    val = float(included["price_low"].min())

    return VolumeProfileResult(poc=poc, vah=vah, val=val, buckets=buckets.drop(columns=["price_mid"]))
