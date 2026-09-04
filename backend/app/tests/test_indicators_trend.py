import numpy as np
import pandas as pd
import pytest

from app.services.indicators.trend import (
    adx,
    ema,
    ichimoku,
    macd,
    parabolic_sar,
    sma,
    supertrend,
)


def test_sma_matches_manual_average_of_consecutive_integers():
    close = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype="float64")
    result = sma(close, period=3)
    expected = [np.nan, np.nan, 2, 3, 4, 5, 6, 7, 8, 9]
    for got, want in zip(result.tolist(), expected):
        if np.isnan(want):
            assert np.isnan(got)
        else:
            assert got == pytest.approx(want, abs=0.01)


def test_ema_matches_hand_computed_values():
    # alpha = 2/(period+1) = 0.5 untuk period=3, adjust=False:
    # ema0=1; ema1=0.5*2+0.5*1=1.5; ema2=0.5*3+0.5*1.5=2.25
    # ema3=0.5*4+0.5*2.25=3.125; ema4=0.5*5+0.5*3.125=4.0625
    close = pd.Series([1, 2, 3, 4, 5], dtype="float64")
    result = ema(close, period=3)
    expected = [1, 1.5, 2.25, 3.125, 4.0625]
    for got, want in zip(result.tolist(), expected):
        assert got == pytest.approx(want, abs=0.01)


def _manual_ema(values: list[float], period: int) -> list[float]:
    """Reimplementasi EMA independen (loop python biasa) untuk cross-check
    MACD — sengaja tidak memanggil trend.ema() supaya jadi verifikasi silang
    yang sungguhan, bukan tautologi."""
    alpha = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(alpha * v + (1 - alpha) * out[-1])
    return out


def test_macd_matches_independently_recomputed_ema_difference():
    values = [10, 11, 12, 11, 13, 14, 15, 14, 16, 17, 18, 17, 19, 20, 21, 20, 22, 23, 24, 23, 25, 26, 27, 26, 28, 29, 30]
    close = pd.Series(values, dtype="float64")

    result = macd(close, fast=3, slow=6, signal=2)

    manual_fast = _manual_ema(values, 3)
    manual_slow = _manual_ema(values, 6)
    manual_macd_line = [f - s for f, s in zip(manual_fast, manual_slow)]
    manual_signal = _manual_ema(manual_macd_line, 2)

    for i in range(len(values)):
        assert result["macd"].iloc[i] == pytest.approx(manual_macd_line[i], abs=0.01)
        assert result["signal"].iloc[i] == pytest.approx(manual_signal[i], abs=0.01)
        assert result["histogram"].iloc[i] == pytest.approx(
            manual_macd_line[i] - manual_signal[i], abs=0.01
        )


def _manual_wilder_smooth(values: list[float], period: int) -> list[float]:
    out = [np.nan] * (period - 1)
    initial = sum(values[:period]) / period
    out.append(initial)
    prev = initial
    for v in values[period:]:
        prev = (prev * (period - 1) + v) / period
        out.append(prev)
    return out


def _manual_adx(df: pd.DataFrame, period: int) -> tuple[list, list, list]:
    """Implementasi ADX independen (algoritma Wilder standar), ditulis
    ulang dari nol di test — bukan memanggil app.services.indicators.trend."""
    highs = df["high"].tolist()
    lows = df["low"].tolist()
    closes = df["close"].tolist()
    n = len(df)

    plus_dm = [0.0]
    minus_dm = [0.0]
    tr = [highs[0] - lows[0]]
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if (up > down and up > 0) else 0.0)
        minus_dm.append(down if (down > up and down > 0) else 0.0)
        tr.append(
            max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        )

    atr = _manual_wilder_smooth(tr, period)
    s_plus_dm = _manual_wilder_smooth(plus_dm, period)
    s_minus_dm = _manual_wilder_smooth(minus_dm, period)

    plus_di = [100 * p / a if a and not np.isnan(a) else np.nan for p, a in zip(s_plus_dm, atr)]
    minus_di = [100 * m / a if a and not np.isnan(a) else np.nan for m, a in zip(s_minus_dm, atr)]
    dx = [
        100 * abs(p - m) / (p + m) if not (np.isnan(p) or np.isnan(m)) and (p + m) != 0 else np.nan
        for p, m in zip(plus_di, minus_di)
    ]
    adx_line = _manual_wilder_smooth([d for d in dx if not np.isnan(d)], period)
    # padding NaN di depan supaya sejajar index penuh
    pad = [np.nan] * (n - len(adx_line))
    adx_line = pad + adx_line

    return adx_line, plus_di, minus_di


def _make_trending_ohlc(n: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0.3, 1.5, n))
    high = close + rng.uniform(0.5, 2, n)
    low = close - rng.uniform(0.5, 2, n)
    open_ = close + rng.uniform(-1, 1, n)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})


def test_adx_matches_independent_wilder_implementation():
    df = _make_trending_ohlc(40)
    period = 14

    result = adx(df, period=period)
    manual_adx_line, manual_plus_di, manual_minus_di = _manual_adx(df, period)

    for i in range(len(df)):
        if np.isnan(manual_plus_di[i]):
            assert np.isnan(result["plus_di"].iloc[i])
        else:
            assert result["plus_di"].iloc[i] == pytest.approx(manual_plus_di[i], abs=0.05)
        if np.isnan(manual_minus_di[i]):
            assert np.isnan(result["minus_di"].iloc[i])
        else:
            assert result["minus_di"].iloc[i] == pytest.approx(manual_minus_di[i], abs=0.05)


def test_adx_output_within_valid_range():
    df = _make_trending_ohlc(60)
    result = adx(df, period=14)
    valid = result["adx"].dropna()
    assert (valid >= 0).all()
    assert (valid <= 100).all()


def test_parabolic_sar_stays_below_price_in_clear_uptrend():
    n = 30
    close = pd.Series(np.linspace(100, 160, n))
    df = pd.DataFrame({"open": close, "high": close + 1, "low": close - 1, "close": close})
    result = parabolic_sar(df)
    # Setelah beberapa bar warm-up, SAR pada uptrend harus di bawah harga low.
    tail = result.iloc[10:]
    assert (tail.to_numpy() < df["low"].iloc[10:].to_numpy()).all()


def test_parabolic_sar_stays_above_price_in_clear_downtrend():
    n = 30
    close = pd.Series(np.linspace(160, 100, n))
    df = pd.DataFrame({"open": close, "high": close + 1, "low": close - 1, "close": close})
    result = parabolic_sar(df)
    tail = result.iloc[10:]
    assert (tail.to_numpy() > df["high"].iloc[10:].to_numpy()).all()


def test_supertrend_direction_up_means_line_below_close():
    df = _make_trending_ohlc(50)
    result = supertrend(df, period=10, multiplier=3.0)
    combined = pd.concat([result, df["close"]], axis=1).dropna()
    up_rows = combined[combined["direction"] == "up"]
    down_rows = combined[combined["direction"] == "down"]
    assert (up_rows["supertrend"] <= up_rows["close"]).all()
    assert (down_rows["supertrend"] >= down_rows["close"]).all()


def test_ichimoku_tenkan_sen_matches_manual_midpoint():
    df = _make_trending_ohlc(70)
    result = ichimoku(df, tenkan=9, kijun=26, senkou_b=52)

    # Cek beberapa titik acak: tenkan_sen = (highest_high(9)+lowest_low(9))/2
    for i in [10, 30, 50, 69]:
        window = df.iloc[i - 8 : i + 1]
        expected = (window["high"].max() + window["low"].min()) / 2
        assert result["tenkan_sen"].iloc[i] == pytest.approx(expected, abs=0.01)


def test_ichimoku_senkou_span_a_is_shifted_forward_by_kijun():
    df = _make_trending_ohlc(70)
    result = ichimoku(df, tenkan=9, kijun=26, senkou_b=52)

    tenkan = result["tenkan_sen"]
    kijun = result["kijun_sen"]
    unshifted = (tenkan + kijun) / 2

    for i in range(26, 70):
        expected = unshifted.iloc[i - 26]
        actual = result["senkou_span_a"].iloc[i]
        if np.isnan(expected):
            assert np.isnan(actual)
        else:
            assert actual == pytest.approx(expected, abs=0.01)
