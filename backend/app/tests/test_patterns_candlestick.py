import pandas as pd
import pytest

from app.services.patterns.candlestick import (
    _is_downtrend,
    _is_uptrend,
    _near_level,
    detect_candlestick_patterns,
)


def _neutral_bar(close: float, declining: bool) -> dict:
    """Bar netral (bukan pattern apa pun) yang closenya turun/naik bertahap,
    dipakai sebagai 'precursor' tren tanpa memicu shape pattern lain."""
    open_ = close + 1 if declining else close - 1
    return {
        "open": open_,
        "close": close,
        "high": max(open_, close) + 0.5,
        "low": min(open_, close) - 0.5,
        "volume": 1000,
    }


def _downtrend_precursor(n: int = 6, start: float = 110) -> list[dict]:
    bars = []
    price = start
    for _ in range(n):
        bars.append(_neutral_bar(price, declining=True))
        price -= 2
    return bars


def _uptrend_precursor(n: int = 6, start: float = 90) -> list[dict]:
    bars = []
    price = start
    for _ in range(n):
        bars.append(_neutral_bar(price, declining=False))
        price += 2
    return bars


def _flat_precursor(n: int = 6, level: float = 100) -> list[dict]:
    """Precursor tanpa tren jelas (harga zig-zag di sekitar level yang
    sama) — dipakai untuk membuktikan filter konteks BENAR-BENAR menolak
    pattern kalau tidak ada tren maupun level S/R terdekat."""
    bars = []
    for i in range(n):
        price = level + (1 if i % 2 == 0 else -1)
        bars.append(_neutral_bar(price, declining=(i % 2 == 0)))
    return bars


HAMMER_SHAPE_BAR = {"open": 100, "close": 101, "high": 101.2, "low": 95, "volume": 5000}
STAR_SHAPE_BAR = {"open": 100, "close": 99, "high": 106, "low": 98.8, "volume": 5000}
DOJI_BAR = {"open": 100, "close": 100.05, "high": 102, "low": 98, "volume": 3000}
BULLISH_MARUBOZU_BAR = {"open": 100, "close": 110, "high": 110.1, "low": 99.9, "volume": 4000}
BEARISH_MARUBOZU_BAR = {"open": 110, "close": 100, "high": 110.1, "low": 99.9, "volume": 4000}


def _build_df(bars: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(bars)


def _find(matches, name: str, bar_index: int):
    return [m for m in matches if m.name == name and m.bar_index == bar_index]


def test_downtrend_and_uptrend_context_helpers():
    df = _build_df(_downtrend_precursor(6) + [HAMMER_SHAPE_BAR])
    assert _is_downtrend(df, 6) is True
    assert _is_uptrend(df, 6) is False

    df2 = _build_df(_uptrend_precursor(6) + [HAMMER_SHAPE_BAR])
    assert _is_uptrend(df2, 6) is True
    assert _is_downtrend(df2, 6) is False


def test_near_level_true_within_tolerance_false_outside():
    levels = pd.DataFrame({"price": [100.0, 200.0], "level_type": ["support", "resistance"]})
    assert _near_level(100.5, levels, "support") is True  # 0.5% dari 100
    assert _near_level(105.0, levels, "support") is False  # 5% dari 100, di luar toleransi 1%


def test_near_level_handles_none_and_empty():
    assert _near_level(100.0, None, "support") is False
    assert _near_level(100.0, pd.DataFrame(columns=["price", "level_type"]), "support") is False


def test_doji_always_detected_regardless_of_context():
    df = _build_df(_flat_precursor(6) + [DOJI_BAR])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "doji", 6)
    assert len(found) == 1
    assert found[0].direction == "neutral"


def test_marubozu_detected_with_correct_direction():
    df = _build_df(_flat_precursor(6) + [BULLISH_MARUBOZU_BAR])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "marubozu", 6)
    assert len(found) == 1
    assert found[0].direction == "bullish"

    df2 = _build_df(_flat_precursor(6) + [BEARISH_MARUBOZU_BAR])
    matches2 = detect_candlestick_patterns(df2)
    found2 = _find(matches2, "marubozu", 6)
    assert found2[0].direction == "bearish"


def test_hammer_shape_after_downtrend_is_labeled_hammer_bullish():
    df = _build_df(_downtrend_precursor(6) + [HAMMER_SHAPE_BAR])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "hammer", 6)
    assert len(found) == 1
    assert found[0].direction == "bullish"
    # Tidak boleh juga muncul sebagai hanging_man di bar yang sama.
    assert _find(matches, "hanging_man", 6) == []


def test_same_shape_after_uptrend_is_labeled_hanging_man_bearish():
    # SPEC.md: bentuk Hammer & Hanging Man identik — konteks tren yang
    # membedakan interpretasinya.
    df = _build_df(_uptrend_precursor(6) + [HAMMER_SHAPE_BAR])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "hanging_man", 6)
    assert len(found) == 1
    assert found[0].direction == "bearish"
    assert _find(matches, "hammer", 6) == []


def test_hammer_shape_without_any_context_is_not_reported():
    # INI TES INTI dari instruksi SPEC.md Bagian 7.3: "pattern hanya valid
    # jika muncul di konteks yang benar ... implementasikan filter konteks
    # ini, jangan hanya deteksi bentuk." Tanpa downtrend/uptrend/level
    # terdekat, hammer shape TIDAK BOLEH dilaporkan sama sekali.
    df = _build_df(_flat_precursor(6) + [HAMMER_SHAPE_BAR])
    matches = detect_candlestick_patterns(df)
    assert _find(matches, "hammer", 6) == []
    assert _find(matches, "hanging_man", 6) == []


def test_hammer_shape_near_support_level_is_reported_without_downtrend():
    df = _build_df(_flat_precursor(6) + [HAMMER_SHAPE_BAR])
    # Low bar pattern = 95 -> beri level support persis di situ.
    levels = pd.DataFrame({"price": [95.0], "level_type": ["support"]})
    matches = detect_candlestick_patterns(df, levels=levels)
    found = _find(matches, "hammer", 6)
    assert len(found) == 1


def test_star_shape_after_downtrend_is_inverted_hammer_bullish():
    df = _build_df(_downtrend_precursor(6) + [STAR_SHAPE_BAR])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "inverted_hammer", 6)
    assert len(found) == 1
    assert found[0].direction == "bullish"


def test_star_shape_after_uptrend_is_shooting_star_bearish():
    df = _build_df(_uptrend_precursor(6) + [STAR_SHAPE_BAR])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "shooting_star", 6)
    assert len(found) == 1
    assert found[0].direction == "bearish"


def test_bullish_engulfing_detected_after_downtrend():
    prev_bar = {"open": 100, "close": 95, "high": 100.2, "low": 94.8, "volume": 2000}
    engulf_bar = {"open": 94.5, "close": 101, "high": 101.2, "low": 94.3, "volume": 6000}
    df = _build_df(_downtrend_precursor(6) + [prev_bar, engulf_bar])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "bullish_engulfing", 7)
    assert len(found) == 1


def test_bullish_engulfing_shape_without_context_not_reported():
    prev_bar = {"open": 100, "close": 95, "high": 100.2, "low": 94.8, "volume": 2000}
    engulf_bar = {"open": 94.5, "close": 101, "high": 101.2, "low": 94.3, "volume": 6000}
    df = _build_df(_flat_precursor(6) + [prev_bar, engulf_bar])
    matches = detect_candlestick_patterns(df)
    assert _find(matches, "bullish_engulfing", 7) == []


def test_bearish_engulfing_detected_after_uptrend():
    prev_bar = {"open": 100, "close": 105, "high": 105.2, "low": 99.8, "volume": 2000}
    engulf_bar = {"open": 105.5, "close": 99, "high": 105.7, "low": 98.8, "volume": 6000}
    df = _build_df(_uptrend_precursor(6) + [prev_bar, engulf_bar])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "bearish_engulfing", 7)
    assert len(found) == 1


def test_piercing_line_detected_after_downtrend():
    prev_bar = {"open": 105, "close": 100, "high": 105.2, "low": 99.8, "volume": 2000}
    piercing_bar = {"open": 99, "close": 103, "high": 103.2, "low": 98.8, "volume": 5000}
    df = _build_df(_downtrend_precursor(6) + [prev_bar, piercing_bar])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "piercing_line", 7)
    assert len(found) == 1
    assert found[0].direction == "bullish"


def test_dark_cloud_cover_detected_after_uptrend():
    prev_bar = {"open": 100, "close": 105, "high": 105.2, "low": 99.8, "volume": 2000}
    dark_bar = {"open": 106, "close": 102, "high": 106.2, "low": 101.8, "volume": 5000}
    df = _build_df(_uptrend_precursor(6) + [prev_bar, dark_bar])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "dark_cloud_cover", 7)
    assert len(found) == 1
    assert found[0].direction == "bearish"


def test_morning_star_detected_after_downtrend():
    first = {"open": 105, "close": 98, "high": 105.2, "low": 97.8, "volume": 3000}
    second = {"open": 97, "close": 96.5, "high": 97.5, "low": 96, "volume": 1000}
    third = {"open": 97, "close": 103, "high": 103.2, "low": 96.8, "volume": 4000}
    df = _build_df(_downtrend_precursor(6) + [first, second, third])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "morning_star", 8)
    assert len(found) == 1
    assert found[0].direction == "bullish"


def test_evening_star_detected_after_uptrend():
    first = {"open": 95, "close": 102, "high": 102.2, "low": 94.8, "volume": 3000}
    second = {"open": 103, "close": 103.5, "high": 104, "low": 102.5, "volume": 1000}
    third = {"open": 103, "close": 97, "high": 103.2, "low": 96.8, "volume": 4000}
    df = _build_df(_uptrend_precursor(6) + [first, second, third])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "evening_star", 8)
    assert len(found) == 1
    assert found[0].direction == "bearish"


def test_three_white_soldiers_detected_after_downtrend():
    a = {"open": 95, "close": 100, "high": 100.2, "low": 94.8, "volume": 2000}
    b = {"open": 97, "close": 104, "high": 104.2, "low": 96.8, "volume": 2200}
    c = {"open": 101, "close": 108, "high": 108.2, "low": 100.8, "volume": 2400}
    df = _build_df(_downtrend_precursor(6) + [a, b, c])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "three_white_soldiers", 8)
    assert len(found) == 1
    assert found[0].direction == "bullish"


def test_three_black_crows_detected_after_uptrend():
    a = {"open": 105, "close": 100, "high": 105.2, "low": 99.8, "volume": 2000}
    b = {"open": 103, "close": 96, "high": 103.2, "low": 95.8, "volume": 2200}
    c = {"open": 99, "close": 92, "high": 99.2, "low": 91.8, "volume": 2400}
    df = _build_df(_uptrend_precursor(6) + [a, b, c])
    matches = detect_candlestick_patterns(df)
    found = _find(matches, "three_black_crows", 8)
    assert len(found) == 1
    assert found[0].direction == "bearish"


def test_reliability_score_is_positive_number_for_every_match():
    df = _build_df(_downtrend_precursor(6) + [HAMMER_SHAPE_BAR])
    matches = detect_candlestick_patterns(df)
    assert len(matches) > 0
    for m in matches:
        assert m.reliability_score > 0
