import numpy as np
import pandas as pd
import pytest

from app.services.indicators.momentum import (
    cci,
    detect_rsi_divergence,
    mfi,
    roc,
    rsi,
    stochastic,
    stochastic_rsi,
    williams_r,
)


def _manual_wilder_rsi(values: list[float], period: int) -> list[float]:
    """Reimplementasi RSI independen (loop python biasa, bukan memanggil
    app.services.indicators.momentum.rsi) untuk cross-check."""
    gains = [0.0]
    losses = [0.0]
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    out = [np.nan] * period
    avg_gain = sum(gains[1 : period + 1]) / period
    avg_loss = sum(losses[1 : period + 1]) / period
    rs = avg_gain / avg_loss if avg_loss != 0 else np.inf
    out.append(100.0 if avg_loss == 0 else 100 - 100 / (1 + rs))

    for i in range(period + 1, len(values)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else np.inf
        out.append(100.0 if avg_loss == 0 else 100 - 100 / (1 + rs))

    return out


def test_rsi_matches_independent_wilder_reimplementation():
    rng = np.random.default_rng(7)
    values = (100 + np.cumsum(rng.normal(0, 1.2, 60))).tolist()
    close = pd.Series(values)

    result = rsi(close, period=14)
    expected = _manual_wilder_rsi(values, 14)

    for got, want in zip(result.tolist(), expected):
        if np.isnan(want):
            assert np.isnan(got)
        else:
            assert got == pytest.approx(want, abs=0.05)


def test_rsi_is_100_when_price_only_rises():
    close = pd.Series(range(1, 30), dtype="float64")
    result = rsi(close, period=14)
    assert result.iloc[-1] == pytest.approx(100.0)


def test_rsi_bounded_between_0_and_100():
    rng = np.random.default_rng(3)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 2, 100)))
    result = rsi(close, period=14).dropna()
    assert (result >= 0).all()
    assert (result <= 100).all()


def test_stochastic_matches_manual_formula():
    high = pd.Series([10, 12, 11, 13, 14], dtype="float64")
    low = pd.Series([8, 9, 8, 10, 11], dtype="float64")
    close = pd.Series([9, 11, 9, 12, 13], dtype="float64")
    df = pd.DataFrame({"high": high, "low": low, "close": close})

    result = stochastic(df, k_period=3, k_smooth=1, d_period=1)

    # Hitung %K manual per definisi: 100*(close-LL)/(HH-LL) atas window 3 bar.
    expected_k = []
    for i in range(len(df)):
        if i < 2:
            expected_k.append(np.nan)
            continue
        window_high = high.iloc[i - 2 : i + 1].max()
        window_low = low.iloc[i - 2 : i + 1].min()
        expected_k.append(100 * (close.iloc[i] - window_low) / (window_high - window_low))

    for got, want in zip(result["k"].tolist(), expected_k):
        if np.isnan(want):
            assert np.isnan(got)
        else:
            assert got == pytest.approx(want, abs=0.01)


def test_stochastic_bounded_between_0_and_100():
    rng = np.random.default_rng(11)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 80)))
    high = close + rng.uniform(0.1, 1, 80)
    low = close - rng.uniform(0.1, 1, 80)
    df = pd.DataFrame({"high": high, "low": low, "close": close})
    result = stochastic(df).dropna()
    assert (result["k"] >= 0).all() and (result["k"] <= 100).all()
    assert (result["d"] >= 0).all() and (result["d"] <= 100).all()


def test_stochastic_rsi_bounded_between_0_and_100():
    rng = np.random.default_rng(13)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1.5, 100)))
    result = stochastic_rsi(close).dropna()
    assert (result["k"] >= 0).all() and (result["k"] <= 100).all()


def test_cci_matches_manual_formula():
    high = pd.Series([10, 11, 12, 11, 13], dtype="float64")
    low = pd.Series([8, 9, 10, 9, 11], dtype="float64")
    close = pd.Series([9, 10, 11, 10, 12], dtype="float64")
    df = pd.DataFrame({"high": high, "low": low, "close": close})

    result = cci(df, period=3)

    typical = (high + low + close) / 3
    expected = []
    for i in range(len(df)):
        if i < 2:
            expected.append(np.nan)
            continue
        window = typical.iloc[i - 2 : i + 1]
        sma_tp = window.mean()
        mean_dev = (window - sma_tp).abs().mean()
        expected.append((typical.iloc[i] - sma_tp) / (0.015 * mean_dev))

    for got, want in zip(result.tolist(), expected):
        if np.isnan(want):
            assert np.isnan(got)
        else:
            assert got == pytest.approx(want, abs=0.01)


def test_williams_r_matches_manual_formula_and_is_bounded():
    high = pd.Series([10, 11, 12, 11, 13], dtype="float64")
    low = pd.Series([8, 9, 10, 9, 11], dtype="float64")
    close = pd.Series([9, 10, 11, 10, 12], dtype="float64")
    df = pd.DataFrame({"high": high, "low": low, "close": close})

    result = williams_r(df, period=3)

    expected = []
    for i in range(len(df)):
        if i < 2:
            expected.append(np.nan)
            continue
        hh = high.iloc[i - 2 : i + 1].max()
        ll = low.iloc[i - 2 : i + 1].min()
        expected.append(-100 * (hh - close.iloc[i]) / (hh - ll))

    for got, want in zip(result.tolist(), expected):
        if np.isnan(want):
            assert np.isnan(got)
        else:
            assert got == pytest.approx(want, abs=0.01)
            assert -100 <= got <= 0


def test_roc_matches_manual_percentage_change():
    close = pd.Series([10, 12, 15, 14, 18], dtype="float64")
    result = roc(close, period=2)

    expected = [np.nan, np.nan, 50.0, 100 * (14 - 12) / 12, 100 * (18 - 15) / 15]
    for got, want in zip(result.tolist(), expected):
        if np.isnan(want):
            assert np.isnan(got)
        else:
            assert got == pytest.approx(want, abs=0.01)


def test_mfi_matches_manual_formula():
    high = pd.Series([10, 11, 12, 11, 13], dtype="float64")
    low = pd.Series([8, 9, 10, 9, 11], dtype="float64")
    close = pd.Series([9, 10, 11, 10, 12], dtype="float64")
    volume = pd.Series([100, 200, 150, 120, 300], dtype="float64")
    df = pd.DataFrame({"high": high, "low": low, "close": close, "volume": volume})

    result = mfi(df, period=3)

    typical = (high + low + close) / 3
    money_flow = typical * volume
    diff = typical.diff()

    expected = []
    for i in range(len(df)):
        if i < 2:
            expected.append(np.nan)
            continue
        window_idx = range(i - 2, i + 1)
        pos_sum = sum(money_flow.iloc[j] for j in window_idx if diff.iloc[j] > 0)
        neg_sum = sum(money_flow.iloc[j] for j in window_idx if diff.iloc[j] < 0)
        if neg_sum == 0:
            expected.append(100.0)
        else:
            ratio = pos_sum / neg_sum
            expected.append(100 - 100 / (1 + ratio))

    for got, want in zip(result.tolist(), expected):
        if np.isnan(want):
            assert np.isnan(got)
        else:
            assert got == pytest.approx(want, abs=0.01)


def test_mfi_bounded_between_0_and_100():
    rng = np.random.default_rng(17)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 60)))
    high = close + rng.uniform(0.1, 1, 60)
    low = close - rng.uniform(0.1, 1, 60)
    volume = pd.Series(rng.integers(100, 10000, 60).astype(float))
    df = pd.DataFrame({"high": high, "low": low, "close": close, "volume": volume})
    result = mfi(df, period=14).dropna()
    assert (result >= 0).all() and (result <= 100).all()


def test_detect_rsi_divergence_flags_bullish_on_lower_low_price_higher_low_rsi():
    # Dua swing low fractal (n=2) yang jelas: idx5 (harga 90) dan idx14
    # (harga 85, lower-low). RSI di-craft manual (bukan dihitung dari
    # rsi()) supaya independen dari implementasi RSI: RSI di idx14 (40)
    # lebih tinggi dari idx5 (30) -> higher-low RSI -> divergence bullish.
    close = pd.Series(
        [100, 98, 96, 94, 92, 90, 92, 94, 96, 98, 100, 98, 96, 90, 85, 87, 90, 93, 96, 99],
        dtype="float64",
    )
    rsi_values = [50.0] * len(close)
    rsi_values[5] = 30.0
    rsi_values[14] = 40.0
    rsi_series = pd.Series(rsi_values)

    labels = detect_rsi_divergence(close, rsi_series, n=2, lookback=30)

    assert labels.iloc[14] == "bullish"


def test_detect_rsi_divergence_flags_bearish_on_higher_high_price_lower_high_rsi():
    # Dua swing high fractal: idx5 (harga 110) dan idx14 (harga 115,
    # higher-high). RSI di idx14 (55) lebih rendah dari idx5 (70) ->
    # lower-high RSI -> divergence bearish.
    close = pd.Series(
        [100, 102, 104, 106, 108, 110, 108, 106, 104, 102, 100, 102, 104, 110, 115, 113, 110, 107, 104, 101],
        dtype="float64",
    )
    rsi_values = [50.0] * len(close)
    rsi_values[5] = 70.0
    rsi_values[14] = 55.0
    rsi_series = pd.Series(rsi_values)

    labels = detect_rsi_divergence(close, rsi_series, n=2, lookback=30)

    assert labels.iloc[14] == "bearish"


def test_detect_rsi_divergence_no_false_positive_when_rsi_confirms_trend():
    # Lower-low harga DIIKUTI lower-low RSI juga (momentum makin lemah,
    # bukan divergence) -> tidak boleh ada label bullish.
    close = pd.Series(
        [100, 98, 96, 94, 92, 90, 92, 94, 96, 98, 100, 98, 96, 90, 85, 87, 90, 93, 96, 99],
        dtype="float64",
    )
    rsi_values = [50.0] * len(close)
    rsi_values[5] = 40.0
    rsi_values[14] = 30.0  # lebih rendah, konfirmasi tren turun, bukan divergence
    rsi_series = pd.Series(rsi_values)

    labels = detect_rsi_divergence(close, rsi_series, n=2, lookback=30)

    assert labels.iloc[14] != "bullish"
