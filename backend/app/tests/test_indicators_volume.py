import numpy as np
import pandas as pd
import pytest

from app.services.indicators.volume import (
    accumulation_distribution,
    anchored_vwap,
    obv,
    relative_volume,
    volume_ma,
    volume_profile,
    vwap,
)


def test_volume_ma_matches_manual_average():
    volume = pd.Series([100, 200, 150, 300, 120, 80], dtype="float64")
    result = volume_ma(volume, period=3)

    for i in range(len(volume)):
        if i < 2:
            assert np.isnan(result.iloc[i])
        else:
            assert result.iloc[i] == pytest.approx(volume.iloc[i - 2 : i + 1].mean(), abs=0.001)


def test_relative_volume_equals_volume_over_its_moving_average():
    volume = pd.Series([100, 200, 150, 300, 120, 80], dtype="float64")
    ma = volume_ma(volume, period=3)
    result = relative_volume(volume, period=3)

    for got, v, m in zip(result.tolist(), volume.tolist(), ma.tolist()):
        if np.isnan(m):
            assert np.isnan(got)
        else:
            assert got == pytest.approx(v / m, abs=0.001)


def test_obv_matches_manual_cumulative_calculation():
    close = pd.Series([10, 11, 10, 12, 12, 11], dtype="float64")
    volume = pd.Series([100, 200, 150, 300, 120, 80], dtype="float64")

    result = obv(close, volume)
    expected = [0, 200, 50, 350, 350, 270]

    for got, want in zip(result.tolist(), expected):
        assert got == pytest.approx(want, abs=0.001)


def _make_two_session_df() -> pd.DataFrame:
    idx = pd.DatetimeIndex(
        [
            "2026-01-01 09:00",
            "2026-01-01 10:00",
            "2026-01-01 11:00",
            "2026-01-02 09:00",
            "2026-01-02 10:00",
        ]
    )
    high = [10, 11, 12, 13, 14]
    low = [9, 10, 11, 12, 13]
    close = [9.5, 10.5, 11.5, 12.5, 13.5]
    volume = [100, 200, 150, 80, 120]
    return pd.DataFrame({"high": high, "low": low, "close": close, "volume": volume}, index=idx)


def test_vwap_matches_manual_calculation_and_resets_per_session():
    df = _make_two_session_df()
    result = vwap(df)

    tp = (df["high"] + df["low"] + df["close"]) / 3
    tp_vol = tp * df["volume"]

    # Sesi 1 (3 bar pertama): kumulatif tanpa reset.
    expected_session1 = [
        tp_vol.iloc[0] / df["volume"].iloc[0],
        tp_vol.iloc[0:2].sum() / df["volume"].iloc[0:2].sum(),
        tp_vol.iloc[0:3].sum() / df["volume"].iloc[0:3].sum(),
    ]
    for got, want in zip(result.iloc[0:3].tolist(), expected_session1):
        assert got == pytest.approx(want, abs=0.001)

    # Sesi 2 (2 bar terakhir): HARUS reset, tidak melanjutkan kumulatif sesi 1.
    expected_session2 = [
        tp_vol.iloc[3] / df["volume"].iloc[3],
        tp_vol.iloc[3:5].sum() / df["volume"].iloc[3:5].sum(),
    ]
    for got, want in zip(result.iloc[3:5].tolist(), expected_session2):
        assert got == pytest.approx(want, abs=0.001)


def test_vwap_requires_datetime_index():
    df = pd.DataFrame({"high": [10], "low": [9], "close": [9.5], "volume": [100]})
    with pytest.raises(TypeError):
        vwap(df)


def test_anchored_vwap_does_not_reset_across_session_boundary():
    df = _make_two_session_df()
    anchor = df.index[1]  # bar kedua sesi 1
    result = anchored_vwap(df, anchor)

    assert np.isnan(result.iloc[0])  # sebelum anchor -> NaN

    tp = (df["high"] + df["low"] + df["close"]) / 3
    tp_vol = tp * df["volume"]

    # Dari anchor (posisi 1) sampai akhir, TIDAK reset walau lintas sesi.
    expected = []
    cum_tp_vol = 0.0
    cum_vol = 0.0
    for i in range(1, len(df)):
        cum_tp_vol += tp_vol.iloc[i]
        cum_vol += df["volume"].iloc[i]
        expected.append(cum_tp_vol / cum_vol)

    for got, want in zip(result.iloc[1:].tolist(), expected):
        assert got == pytest.approx(want, abs=0.001)


def test_accumulation_distribution_matches_manual_formula():
    high = pd.Series([10, 12, 11], dtype="float64")
    low = pd.Series([8, 9, 9], dtype="float64")
    close = pd.Series([9, 11, 10], dtype="float64")
    volume = pd.Series([100, 200, 150], dtype="float64")
    df = pd.DataFrame({"high": high, "low": low, "close": close, "volume": volume})

    result = accumulation_distribution(df)

    mult = [
        ((9 - 8) - (10 - 9)) / (10 - 8),
        ((11 - 9) - (12 - 11)) / (12 - 9),
        ((10 - 9) - (11 - 10)) / (11 - 9),
    ]
    mfv = [m * v for m, v in zip(mult, volume.tolist())]
    expected_cumsum = [mfv[0], mfv[0] + mfv[1], mfv[0] + mfv[1] + mfv[2]]

    for got, want in zip(result.tolist(), expected_cumsum):
        assert got == pytest.approx(want, abs=0.001)


def test_accumulation_distribution_handles_zero_range_bar():
    # high == low (bar tanpa range) -> tidak boleh ZeroDivisionError/NaN merambat.
    df = pd.DataFrame(
        {"high": [10, 10, 11], "low": [10, 10, 9], "close": [10, 10, 10], "volume": [100, 50, 80]}
    )
    result = accumulation_distribution(df)
    assert not result.isna().any()


def test_volume_profile_bucket_volume_sums_to_total_volume():
    rng = np.random.default_rng(1)
    close = 100 + np.cumsum(rng.normal(0, 1, 200))
    df = pd.DataFrame(
        {
            "high": close + rng.uniform(0.1, 1, 200),
            "low": close - rng.uniform(0.1, 1, 200),
            "close": close,
            "volume": rng.integers(100, 5000, 200).astype(float),
        }
    )

    result = volume_profile(df, num_buckets=50)

    assert result.buckets["volume"].sum() == pytest.approx(df["volume"].sum(), abs=0.01)
    assert len(result.buckets) == 50


def test_volume_profile_poc_is_within_price_range_and_val_le_vah():
    rng = np.random.default_rng(2)
    close = 100 + np.cumsum(rng.normal(0, 1, 200))
    df = pd.DataFrame(
        {
            "high": close + rng.uniform(0.1, 1, 200),
            "low": close - rng.uniform(0.1, 1, 200),
            "close": close,
            "volume": rng.integers(100, 5000, 200).astype(float),
        }
    )

    result = volume_profile(df, num_buckets=50)

    assert df["low"].min() <= result.poc <= df["high"].max()
    assert result.val <= result.poc <= result.vah


def test_volume_profile_poc_bucket_has_max_volume():
    rng = np.random.default_rng(4)
    close = 100 + np.cumsum(rng.normal(0, 1, 150))
    df = pd.DataFrame(
        {
            "high": close + rng.uniform(0.1, 1, 150),
            "low": close - rng.uniform(0.1, 1, 150),
            "close": close,
            "volume": rng.integers(100, 5000, 150).astype(float),
        }
    )
    result = volume_profile(df, num_buckets=50)
    max_bucket_volume = result.buckets["volume"].max()
    poc_bucket = result.buckets[
        (result.buckets["price_low"] <= result.poc) & (result.buckets["price_high"] >= result.poc)
    ]
    assert poc_bucket["volume"].iloc[0] == pytest.approx(max_bucket_volume, abs=0.01)
