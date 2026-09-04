"""Aturan tick size IDX. SPEC.md Bagian 8.8.

Pure function, pakai Decimal (CLAUDE.md: "Semua harga: Decimal, jangan
float"). Semua harga output signal engine WAJIB lewat `round_to_tick()`.
"""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Literal

# SPEC.md Bagian 8.8: (batas_bawah_inklusif, batas_atas_eksklusif, tick_size)
TICK_TABLE: list[tuple[Decimal, Decimal | None, Decimal]] = [
    (Decimal(0), Decimal(200), Decimal(1)),
    (Decimal(200), Decimal(500), Decimal(2)),
    (Decimal(500), Decimal(2000), Decimal(5)),
    (Decimal(2000), Decimal(5000), Decimal(10)),
    (Decimal(5000), None, Decimal(25)),
]

RoundDirection = Literal["nearest", "up", "down"]


def get_tick_size(price: Decimal) -> Decimal:
    for low, high, tick in TICK_TABLE:
        if price >= low and (high is None or price < high):
            return tick
    return TICK_TABLE[-1][2]


def round_to_tick(price: Decimal, direction: RoundDirection = "nearest") -> Decimal:
    """Bulatkan harga ke kelipatan tick size yang valid di bursa.

    `direction='down'` dipakai untuk stop loss/take profit sell-side supaya
    tidak overshoot; `'up'` untuk batas atas (mis. entry_high); `'nearest'`
    untuk harga referensi/tampilan umum.
    """
    if price <= 0:
        raise ValueError("price harus > 0")

    tick = get_tick_size(price)
    quotient = price / tick

    if direction == "down":
        rounded_quotient = quotient.to_integral_value(rounding=ROUND_DOWN)
    elif direction == "up":
        rounded_quotient = quotient.to_integral_value(rounding=ROUND_CEILING)
    else:
        rounded_quotient = quotient.to_integral_value(rounding=ROUND_HALF_UP)

    return rounded_quotient * tick
