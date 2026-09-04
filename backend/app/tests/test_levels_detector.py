from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from app.services.levels.detector import (
    LevelCandidate,
    MAX_LEVELS_PER_SIDE,
    MIN_STRENGTH,
    _cluster_candidates,
    _normalize,
    _recency_decay_score,
    _round_number_step,
    _was_opposite_role_recently,
    detect_price_levels,
)


def test_normalize_min_max_to_0_100_range():
    values = np.array([10.0, 20.0, 30.0, 40.0])
    result = _normalize(values)
    assert result[0] == pytest.approx(0.0)
    assert result[-1] == pytest.approx(100.0)
    assert result[1] == pytest.approx(100 / 3)


def test_normalize_all_equal_returns_neutral_50():
    values = np.array([5.0, 5.0, 5.0])
    result = _normalize(values)
    assert (result == 50.0).all()


def test_recency_decay_matches_spec_formula():
    days = np.array([0.0, 60.0, 120.0])
    result = _recency_decay_score(days)
    expected = np.exp(-days / 60) * 100
    np.testing.assert_allclose(result, expected)
    # Baru saja diuji (0 hari) -> skor 100. 60 hari -> meluruh ke ~36.8.
    assert result[0] == pytest.approx(100.0)
    assert result[1] == pytest.approx(36.79, abs=0.01)


def test_round_number_step_matches_spec_thresholds():
    assert _round_number_step(150) == 50
    assert _round_number_step(999) == 50
    assert _round_number_step(1000) == 100
    assert _round_number_step(9999) == 100
    assert _round_number_step(10000) == 500


def test_cluster_candidates_groups_within_tolerance():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candidates = [
        LevelCandidate(price=100.0, ts=now, volume=10, wick_size=1),
        LevelCandidate(price=100.4, ts=now, volume=10, wick_size=1),
        LevelCandidate(price=100.8, ts=now, volume=10, wick_size=1),
        LevelCandidate(price=105.0, ts=now, volume=10, wick_size=1),  # jauh -> cluster baru
    ]
    clusters = _cluster_candidates(candidates, tolerance=0.5)
    assert len(clusters) == 2
    assert len(clusters[0]) == 3
    assert len(clusters[1]) == 1


def test_cluster_candidates_empty_input():
    assert _cluster_candidates([], tolerance=1.0) == []


def test_was_opposite_role_recently_detects_flip():
    # Harga dulu di bawah 100 (level = resistance), sekarang di atas 100
    # (level jadi support) -> role_flipped harus True.
    close = pd.Series([90, 92, 95, 98, 101, 103], dtype="float64")
    df = pd.DataFrame({"close": close})
    assert _was_opposite_role_recently(df, price=100.0, lookback=5) is True


def test_was_opposite_role_recently_false_when_role_stable():
    # Harga selalu di atas 100 -> level tetap support, tidak pernah flip.
    close = pd.Series([101, 102, 103, 104, 105, 106], dtype="float64")
    df = pd.DataFrame({"close": close})
    assert _was_opposite_role_recently(df, price=100.0, lookback=5) is False


def _make_ohlcv_with_repeated_support(n: int = 300) -> pd.DataFrame:
    """Bangun data harga sintetis dengan level support yang jelas disentuh
    berkali-kali di harga ~95, supaya detector punya sesuatu yang nyata
    untuk dicluster."""
    rng = np.random.default_rng(123)
    idx = pd.date_range("2025-01-01", periods=n, freq="D")

    close = 100 + rng.normal(0, 1, n).cumsum() * 0.05
    close = np.clip(close, 90, 130)

    # Paksa beberapa titik menyentuh ~95 supaya jadi swing low berulang.
    touch_positions = [40, 90, 140, 190, 240]
    for pos in touch_positions:
        close[pos] = 95.0 + rng.normal(0, 0.05)

    high = close + rng.uniform(0.3, 1.5, n)
    low = close - rng.uniform(0.3, 1.5, n)
    open_ = close + rng.uniform(-0.5, 0.5, n)
    volume = rng.integers(1000, 50000, n).astype(float)

    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


def test_detect_price_levels_requires_datetime_index():
    df = pd.DataFrame({"open": [1], "high": [2], "low": [0], "close": [1], "volume": [100]})
    with pytest.raises(TypeError):
        detect_price_levels(df, timeframe="1d")


def test_detect_price_levels_rejects_empty_dataframe():
    df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df.index = pd.DatetimeIndex([])
    with pytest.raises(ValueError):
        detect_price_levels(df, timeframe="1d")


def test_detect_price_levels_respects_max_levels_per_side():
    df = _make_ohlcv_with_repeated_support()
    result = detect_price_levels(df, timeframe="1d")

    assert (result[result["level_type"] == "support"].shape[0]) <= MAX_LEVELS_PER_SIDE
    assert (result[result["level_type"] == "resistance"].shape[0]) <= MAX_LEVELS_PER_SIDE


def test_detect_price_levels_all_strengths_above_minimum():
    df = _make_ohlcv_with_repeated_support()
    result = detect_price_levels(df, timeframe="1d")
    assert (result["strength"] >= MIN_STRENGTH).all()
    assert (result["strength"] <= 100.0 + 1e-6).all()


def test_detect_price_levels_classification_matches_current_price():
    df = _make_ohlcv_with_repeated_support()
    current_price = df["close"].iloc[-1]
    result = detect_price_levels(df, timeframe="1d")

    supports = result[result["level_type"] == "support"]
    resistances = result[result["level_type"] == "resistance"]
    assert (supports["price"] < current_price).all()
    assert (resistances["price"] > current_price).all()


def test_detect_price_levels_includes_expected_sources():
    df = _make_ohlcv_with_repeated_support()
    result = detect_price_levels(df, timeframe="1d")
    sources = set(result["source"].unique())
    # Minimal beberapa sumber dari SPEC.md Bagian 7.2 langkah 4 harus muncul
    # (tidak semua dijamin lolos filter strength>=40, tapi round_number dan
    # swing seharusnya konsisten muncul di data sintetis ini).
    assert "round_number" in sources or "swing" in sources
