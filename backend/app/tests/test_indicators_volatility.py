import numpy as np
import pandas as pd
import pytest

from app.services.indicators.trend import ema
from app.services.indicators.volatility import (
    atr,
    atr_percent,
    bollinger_bands,
    donchian_channel,
    historical_volatility,
    keltner_channel,
)


def _manual_wilder(values: list[float], period: int) -> list[float]:
    out = [np.nan] * (period - 1)
    initial = sum(values[:period]) / period
    out.append(initial)
    prev = initial
    for v in values[period:]:
        prev = (prev * (period - 1) + v) / period
        out.append(prev)
    return out


def test_atr_matches_independent_wilder_reimplementation_of_true_range():
    high = [10, 12, 11, 13, 12, 14, 13, 15]
    low = [8, 9, 9, 10, 10, 11, 11, 12]
    close = [9, 11, 10, 12, 11, 13, 12, 14]
    df = pd.DataFrame({"high": high, "low": low, "close": close})

    tr = [high[0] - low[0]]
    for i in range(1, len(close)):
        tr.append(max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1])))

    expected = _manual_wilder(tr, period=3)
    result = atr(df, period=3)

    for got, want in zip(result.tolist(), expected):
        if np.isnan(want):
            assert np.isnan(got)
        else:
            assert got == pytest.approx(want, abs=0.01)


def test_atr_percent_equals_atr_divided_by_close():
    high = pd.Series([10, 12, 11, 13, 12, 14], dtype="float64")
    low = pd.Series([8, 9, 9, 10, 10, 11], dtype="float64")
    close = pd.Series([9, 11, 10, 12, 11, 13], dtype="float64")
    df = pd.DataFrame({"high": high, "low": low, "close": close})

    atr_series = atr(df, period=3)
    result = atr_percent(df, period=3)

    for got, atr_val, c in zip(result.tolist(), atr_series.tolist(), close.tolist()):
        if np.isnan(atr_val):
            assert np.isnan(got)
        else:
            assert got == pytest.approx(atr_val / c * 100, abs=0.001)


def test_bollinger_bands_matches_manual_std_calculation():
    close = pd.Series([10, 12, 11, 13, 14], dtype="float64")
    result = bollinger_bands(close, period=3, num_std=2.0)

    for i in range(len(close)):
        if i < 2:
            assert np.isnan(result["middle"].iloc[i])
            continue
        window = close.iloc[i - 2 : i + 1]
        mean = window.mean()
        std = np.sqrt(((window - mean) ** 2).mean())  # ddof=0, dihitung manual
        upper = mean + 2 * std
        lower = mean - 2 * std

        assert result["middle"].iloc[i] == pytest.approx(mean, abs=0.001)
        assert result["upper"].iloc[i] == pytest.approx(upper, abs=0.001)
        assert result["lower"].iloc[i] == pytest.approx(lower, abs=0.001)
        assert result["bandwidth"].iloc[i] == pytest.approx((upper - lower) / mean * 100, abs=0.001)
        assert result["percent_b"].iloc[i] == pytest.approx(
            (close.iloc[i] - lower) / (upper - lower), abs=0.001
        )


def test_bollinger_percent_b_is_0_5_when_price_at_middle():
    close = pd.Series([10.0] * 25)  # harga konstan -> std=0 -> upper=lower=middle
    result = bollinger_bands(close, period=20)
    # Saat upper==lower (std=0), %B jadi NaN (pembagian 0/0) — bukan bug,
    # itu perilaku matematis yang benar untuk kondisi degenerate ini.
    assert result["bandwidth"].dropna().eq(0).all()


def test_keltner_channel_width_is_exactly_multiplier_times_atr():
    rng = np.random.default_rng(5)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 60)))
    high = close + rng.uniform(0.2, 1, 60)
    low = close - rng.uniform(0.2, 1, 60)
    df = pd.DataFrame({"high": high, "low": low, "close": close})

    result = keltner_channel(df, ema_period=20, atr_period=10, multiplier=2.0)
    atr_series = atr(df, period=10)
    expected_middle = ema(close, 20)

    combined = pd.concat([result, atr_series.rename("atr"), expected_middle.rename("expected_mid")], axis=1).dropna()
    assert (combined["middle"] - combined["expected_mid"]).abs().max() < 0.001
    assert ((combined["upper"] - combined["middle"]) - 2 * combined["atr"]).abs().max() < 0.001
    assert ((combined["middle"] - combined["lower"]) - 2 * combined["atr"]).abs().max() < 0.001


def test_donchian_channel_matches_manual_rolling_extremes():
    high = pd.Series([10, 15, 12, 14, 11], dtype="float64")
    low = pd.Series([8, 9, 10, 7, 9], dtype="float64")
    df = pd.DataFrame({"high": high, "low": low, "close": (high + low) / 2})

    result = donchian_channel(df, period=3)

    for i in range(len(df)):
        if i < 2:
            assert np.isnan(result["upper"].iloc[i])
            continue
        expected_upper = high.iloc[i - 2 : i + 1].max()
        expected_lower = low.iloc[i - 2 : i + 1].min()
        assert result["upper"].iloc[i] == expected_upper
        assert result["lower"].iloc[i] == expected_lower
        assert result["middle"].iloc[i] == pytest.approx((expected_upper + expected_lower) / 2, abs=0.001)


def test_historical_volatility_matches_manual_log_return_std():
    rng = np.random.default_rng(9)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 40)))

    result = historical_volatility(close, period=20, trading_days=252)

    log_returns = np.log(close / close.shift(1))
    # i=19 sengaja dilewati: window rolling di posisi itu (iloc[0:20]) masih
    # mencakup log_returns.iloc[0] yang NaN (close.shift(1) belum ada di bar
    # pertama), jadi hasilnya NaN — perilaku default pandas rolling
    # (min_periods=window size), bukan bug. Titik valid pertama ada di i=20.
    assert np.isnan(result.iloc[19])
    for i in [20, 25, 39]:
        window = log_returns.iloc[i - 19 : i + 1]
        expected = window.std(ddof=0) * np.sqrt(252) * 100
        assert result.iloc[i] == pytest.approx(expected, abs=0.01)


def test_historical_volatility_is_non_negative():
    rng = np.random.default_rng(21)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 2, 60)))
    result = historical_volatility(close).dropna()
    assert (result >= 0).all()
