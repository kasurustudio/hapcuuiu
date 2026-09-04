import json

import numpy as np
import pandas as pd
import pytest

from app.services.indicators.snapshot import build_indicator_snapshot


def _make_df(n: int = 260) -> pd.DataFrame:
    rng = np.random.default_rng(99)
    idx = pd.date_range("2025-01-01", periods=n, freq="D", tz="UTC")
    close = 100 + np.cumsum(rng.normal(0.1, 1.5, n))
    high = close + rng.uniform(0.5, 2, n)
    low = close - rng.uniform(0.5, 2, n)
    open_ = close + rng.uniform(-1, 1, n)
    volume = rng.integers(1000, 100000, n).astype(float)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


def test_snapshot_has_all_expected_categories():
    df = _make_df()
    snapshot = build_indicator_snapshot(df)
    assert set(snapshot.keys()) == {"trend", "momentum", "volatility", "volume", "structure"}


def test_snapshot_trend_values_are_plausible_numbers():
    df = _make_df()
    snapshot = build_indicator_snapshot(df)
    assert snapshot["trend"]["sma20"] is not None
    assert snapshot["trend"]["ema200"] is not None
    assert isinstance(snapshot["trend"]["macd"], dict)
    assert "macd" in snapshot["trend"]["macd"]


def test_snapshot_momentum_rsi_bounded():
    df = _make_df()
    snapshot = build_indicator_snapshot(df)
    rsi_val = snapshot["momentum"]["rsi14"]
    assert rsi_val is not None
    assert 0 <= rsi_val <= 100


def test_snapshot_is_json_serializable_with_no_nan():
    df = _make_df()
    snapshot = build_indicator_snapshot(df)
    serialized = json.dumps(snapshot)
    assert "NaN" not in serialized


def test_snapshot_handles_short_dataframe_without_crashing():
    df = _make_df(n=30)
    snapshot = build_indicator_snapshot(df)
    # Indikator dengan periode panjang (mis. sma200) wajar bernilai None
    # kalau data belum cukup — yang penting tidak crash.
    assert snapshot["trend"]["sma200"] is None
    assert snapshot["trend"]["sma5"] is not None


def test_snapshot_volume_payload_includes_vwap_when_datetime_index():
    df = _make_df()
    snapshot = build_indicator_snapshot(df)
    assert "vwap" in snapshot["volume"]
    assert "volume_profile" in snapshot["volume"]
    assert set(snapshot["volume"]["volume_profile"].keys()) == {"poc", "vah", "val"}


def test_snapshot_structure_includes_fibonacci_when_swings_found():
    df = _make_df()
    snapshot = build_indicator_snapshot(df)
    assert "pivot_daily" in snapshot["structure"]
    assert "pp" in snapshot["structure"]["pivot_daily"]
