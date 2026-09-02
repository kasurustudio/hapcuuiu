from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from app.services.market_data.validator import (
    CORPORATE_ACTION_JUMP_THRESHOLD,
    InsufficientDataError,
    MIN_BARS_BY_MODE,
    UnrecoverableGapError,
    validate_ohlcv,
)


def make_ohlcv(n: int, start_price: float = 1000.0) -> pd.DataFrame:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    idx = [start + timedelta(days=i) for i in range(n)]
    prices = [start_price + i for i in range(n)]
    return pd.DataFrame(
        {
            "open": prices,
            "high": [p + 5 for p in prices],
            "low": [p - 5 for p in prices],
            "close": prices,
            "volume": [1000] * n,
        },
        index=pd.DatetimeIndex(idx, name="ts"),
    )


def test_raises_insufficient_data_below_mode_minimum():
    df = make_ohlcv(MIN_BARS_BY_MODE["swing"] - 1)
    with pytest.raises(InsufficientDataError) as exc_info:
        validate_ohlcv(df, mode="swing")
    assert exc_info.value.mode == "swing"
    assert exc_info.value.required == MIN_BARS_BY_MODE["swing"]


def test_accepts_data_at_exact_minimum():
    df = make_ohlcv(MIN_BARS_BY_MODE["day"])
    result = validate_ohlcv(df, mode="day")
    assert len(result.df) == MIN_BARS_BY_MODE["day"]


def test_drops_suspend_bars_with_zero_volume():
    df = make_ohlcv(MIN_BARS_BY_MODE["swing"] + 5)
    df.iloc[3, df.columns.get_loc("volume")] = 0
    df.iloc[7, df.columns.get_loc("volume")] = 0
    result = validate_ohlcv(df, mode="swing")
    assert result.dropped_suspend_bars == 2
    assert (result.df["volume"] == 0).sum() == 0


def test_flags_corporate_action_price_jump():
    df = make_ohlcv(MIN_BARS_BY_MODE["swing"] + 1)
    jump_idx = 20
    close_col = df.columns.get_loc("close")
    prev_close = df.iloc[jump_idx - 1, close_col]
    df.iloc[jump_idx, close_col] = prev_close * (1 + CORPORATE_ACTION_JUMP_THRESHOLD + 0.05)

    result = validate_ohlcv(df, mode="swing")
    assert len(result.corporate_action_flags) == 1
    assert result.corporate_action_flags[0]["requires_manual_review"] is True


def test_forward_fills_short_gap_of_two_bars():
    df = make_ohlcv(MIN_BARS_BY_MODE["swing"] + 10)
    price_cols = ["open", "high", "low", "close"]
    df.iloc[10:12, [df.columns.get_loc(c) for c in price_cols]] = None

    result = validate_ohlcv(df, mode="swing")
    assert result.forward_filled_bars == 2
    assert result.df[price_cols].isna().sum().sum() == 0


def test_rejects_gap_longer_than_two_bars():
    df = make_ohlcv(MIN_BARS_BY_MODE["swing"] + 10)
    price_cols = ["open", "high", "low", "close"]
    df.iloc[10:13, [df.columns.get_loc(c) for c in price_cols]] = None  # 3 bar gap

    with pytest.raises(UnrecoverableGapError) as exc_info:
        validate_ohlcv(df, mode="swing")
    assert exc_info.value.gap_length == 3


def test_unknown_mode_raises_value_error():
    df = make_ohlcv(10)
    with pytest.raises(ValueError):
        validate_ohlcv(df, mode="not_a_mode")
