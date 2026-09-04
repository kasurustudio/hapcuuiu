import numpy as np
import pandas as pd
import pytest

from app.services.indicators.structure import (
    fibonacci_extension,
    fibonacci_retracement,
    pivot_points,
    swing_highs_lows,
    weekly_ohlc,
)


def test_pivot_points_classic_matches_hand_computed_values():
    result = pivot_points(high=110, low=90, close=100, method="classic")
    assert result["pp"] == pytest.approx(100)
    assert result["r1"] == pytest.approx(110)
    assert result["s1"] == pytest.approx(90)
    assert result["r2"] == pytest.approx(120)
    assert result["s2"] == pytest.approx(80)
    assert result["r3"] == pytest.approx(130)
    assert result["s3"] == pytest.approx(70)


def test_pivot_points_fibonacci_matches_hand_computed_values():
    result = pivot_points(high=110, low=90, close=100, method="fibonacci")
    assert result["pp"] == pytest.approx(100)
    assert result["r1"] == pytest.approx(107.64)
    assert result["s1"] == pytest.approx(92.36)
    assert result["r2"] == pytest.approx(112.36)
    assert result["s2"] == pytest.approx(87.64)
    assert result["r3"] == pytest.approx(120)
    assert result["s3"] == pytest.approx(80)


def test_pivot_points_camarilla_matches_hand_computed_values():
    result = pivot_points(high=110, low=90, close=100, method="camarilla")
    assert result["r1"] == pytest.approx(101.8333, abs=0.001)
    assert result["s1"] == pytest.approx(98.1667, abs=0.001)
    assert result["r2"] == pytest.approx(103.6667, abs=0.001)
    assert result["s2"] == pytest.approx(96.3333, abs=0.001)
    assert result["r3"] == pytest.approx(105.5, abs=0.001)
    assert result["s3"] == pytest.approx(94.5, abs=0.001)
    assert result["r4"] == pytest.approx(111.0, abs=0.001)
    assert result["s4"] == pytest.approx(89.0, abs=0.001)


def test_pivot_points_rejects_unknown_method():
    with pytest.raises(ValueError):
        pivot_points(110, 90, 100, method="not_a_method")


def test_weekly_ohlc_aggregates_correctly():
    idx = pd.date_range("2026-01-05", periods=10, freq="D")  # Senin 5 Jan - Rabu 14 Jan
    df = pd.DataFrame(
        {
            "open": [10, 11, 12, 13, 14, 20, 21, 22, 23, 24],
            "high": [15, 16, 17, 18, 19, 25, 26, 27, 28, 29],
            "low": [5, 6, 7, 8, 9, 15, 16, 17, 18, 19],
            "close": [12, 13, 14, 15, 16, 22, 23, 24, 25, 26],
            "volume": [100] * 10,
        },
        index=idx,
    )

    result = weekly_ohlc(df)

    # Minggu pertama (Senin 5 Jan - Minggu 11 Jan): 7 bar pertama (index 0-6).
    week1 = result.iloc[0]
    assert week1["open"] == 10
    assert week1["high"] == 26  # max(high[0:7]) = max(15,16,17,18,19,25,26)
    assert week1["low"] == 5
    assert week1["close"] == 23  # close bar terakhir minggu itu (index 6)
    assert week1["volume"] == 700


def test_weekly_ohlc_requires_datetime_index():
    df = pd.DataFrame({"open": [1], "high": [2], "low": [0], "close": [1]})
    with pytest.raises(TypeError):
        weekly_ohlc(df)


def test_fibonacci_retracement_matches_hand_computed_values():
    result = fibonacci_retracement(swing_low=100, swing_high=150)
    assert result[0.236] == pytest.approx(138.2)
    assert result[0.382] == pytest.approx(130.9)
    assert result[0.5] == pytest.approx(125.0)
    assert result[0.618] == pytest.approx(119.1)
    assert result[0.786] == pytest.approx(110.7)


def test_fibonacci_extension_matches_hand_computed_values():
    result = fibonacci_extension(swing_low=100, swing_high=150)
    assert result[1.272] == pytest.approx(163.6)
    assert result[1.618] == pytest.approx(180.9)
    assert result[2.0] == pytest.approx(200.0)


def test_swing_highs_lows_detects_exact_fractal_points():
    # n=2: titik ekstrem harus lebih tinggi/rendah dari 2 bar kiri & kanan.
    high = [10, 11, 12, 15, 12, 11, 10, 9, 10, 12, 14, 13, 12]
    low = [8, 9, 10, 11, 9, 8, 7, 6, 7, 9, 11, 10, 9]
    df = pd.DataFrame({"high": high, "low": low, "close": high})

    result = swing_highs_lows(df, n=2)

    # Swing high jelas di index 3 (nilai 15, puncak lokal).
    assert result["swing_high"].iloc[3] == True  # noqa: E712
    # Swing low jelas di index 7 (nilai 6, lembah lokal).
    assert result["swing_low"].iloc[7] == True  # noqa: E712

    # Titik pertama/terakhir (kurang dari n bar tetangga) tidak pernah true.
    assert result["swing_high"].iloc[0] == False  # noqa: E712
    assert result["swing_low"].iloc[0] == False  # noqa: E712
    assert result["swing_high"].iloc[-1] == False  # noqa: E712


def test_swing_highs_lows_no_flag_on_flat_series():
    df = pd.DataFrame({"high": [10.0] * 15, "low": [5.0] * 15, "close": [7.0] * 15})
    result = swing_highs_lows(df, n=3)
    assert not result["swing_high"].any()
    assert not result["swing_low"].any()
