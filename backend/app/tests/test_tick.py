from decimal import Decimal

import pytest

from app.core.tick import get_tick_size, round_to_tick


@pytest.mark.parametrize(
    "price,expected_tick",
    [
        (Decimal(50), Decimal(1)),
        (Decimal(199), Decimal(1)),
        (Decimal(200), Decimal(2)),  # batas bawah inklusif
        (Decimal(499), Decimal(2)),
        (Decimal(500), Decimal(5)),  # batas bawah inklusif
        (Decimal(1999), Decimal(5)),
        (Decimal(2000), Decimal(10)),  # batas bawah inklusif
        (Decimal(4999), Decimal(10)),
        (Decimal(5000), Decimal(25)),  # batas bawah inklusif
        (Decimal(50000), Decimal(25)),
    ],
)
def test_get_tick_size_matches_spec_table(price, expected_tick):
    assert get_tick_size(price) == expected_tick


def test_round_to_tick_down_floors_to_valid_multiple():
    # 9253 di rentang >=5000 -> tick 25. 9253/25 = 370.12 -> floor 370*25 = 9250
    assert round_to_tick(Decimal(9253), "down") == Decimal(9250)


def test_round_to_tick_up_ceils_to_valid_multiple():
    assert round_to_tick(Decimal(9253), "up") == Decimal(9275)


def test_round_to_tick_nearest_rounds_down_when_below_half():
    # 370.12 -> pembulatan terdekat ke 370, bukan 371
    assert round_to_tick(Decimal(9253), "nearest") == Decimal(9250)


def test_round_to_tick_nearest_rounds_up_when_above_half():
    # 9265/25 = 370.6 -> pembulatan terdekat ke 371
    assert round_to_tick(Decimal(9265), "nearest") == Decimal(9275)


def test_round_to_tick_mid_range_tick_size_5():
    # 1502 di rentang 500-1999 -> tick 5. 1502/5 = 300.4 -> floor 300*5 = 1500
    assert round_to_tick(Decimal(1502), "down") == Decimal(1500)


def test_round_to_tick_exact_multiple_unchanged():
    assert round_to_tick(Decimal(150), "up") == Decimal(150)
    assert round_to_tick(Decimal(150), "down") == Decimal(150)
    assert round_to_tick(Decimal(150), "nearest") == Decimal(150)


def test_round_to_tick_rejects_non_positive_price():
    with pytest.raises(ValueError):
        round_to_tick(Decimal(0))
    with pytest.raises(ValueError):
        round_to_tick(Decimal(-100))


def test_round_to_tick_result_is_always_multiple_of_tick():
    for raw in [Decimal("123.4"), Decimal("321.9"), Decimal("1876.3"), Decimal("3333.3"), Decimal("12345.6")]:
        rounded = round_to_tick(raw, "nearest")
        tick = get_tick_size(rounded)
        assert rounded % tick == 0
