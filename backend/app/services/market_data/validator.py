"""Data quality validator. SPEC.md Bagian 6.3.

Pure functions: DataFrame masuk, DataFrame (+ flags) keluar. Tidak ada I/O.
Data harus lolos validator ini sebelum masuk ke engine indikator/sinyal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

# SPEC.md Bagian 6.3: minimum bar per mode.
MIN_BARS_BY_MODE = {
    "scalping": 300,
    "day": 100,
    "swing": 200,
    "investing": 200,
}

# SPEC.md Bagian 6.3: lonjakan close > 35% dicurigai corporate action
# (split/reverse split) jika bukan hasil akumulasi hari ARA/ARB berturut-turut.
CORPORATE_ACTION_JUMP_THRESHOLD = 0.35

# Forward fill NaN di tengah series maksimal 2 bar berturut-turut.
MAX_FORWARD_FILL_BARS = 2


class InsufficientDataError(Exception):
    """Data historis kurang dari minimum bar yang disyaratkan mode."""

    def __init__(self, mode: str, required: int, actual: int):
        self.mode = mode
        self.required = required
        self.actual = actual
        super().__init__(
            f"insufficient_data: mode={mode!r} butuh minimal {required} bar, "
            f"tersedia {actual} bar"
        )


class UnrecoverableGapError(Exception):
    """NaN beruntun di tengah series melebihi batas forward-fill yang diizinkan."""

    def __init__(self, gap_length: int, at_index):
        self.gap_length = gap_length
        self.at_index = at_index
        super().__init__(
            f"gap NaN {gap_length} bar berturut-turut di sekitar {at_index} — "
            f"melebihi batas forward-fill {MAX_FORWARD_FILL_BARS} bar"
        )


@dataclass(slots=True)
class ValidationResult:
    df: pd.DataFrame
    dropped_suspend_bars: int = 0
    corporate_action_flags: list[dict] = field(default_factory=list)
    forward_filled_bars: int = 0


def _drop_suspend_bars(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Buang bar dengan volume=0 pada jam perdagangan aktif (suspend)."""
    suspend_mask = df["volume"] == 0
    dropped = int(suspend_mask.sum())
    return df.loc[~suspend_mask].copy(), dropped


def _detect_corporate_actions(df: pd.DataFrame) -> list[dict]:
    """Flag lonjakan harga mencurigakan untuk review manual.

    Catatan: pengecualian "hari ARA/ARB berturut-turut" memerlukan tabel
    batas auto-rejection IDX (dihitung berbasis tick size, lihat SPEC.md
    Bagian 8.8) yang diimplementasikan di Fase 2. Untuk Fase 1, semua
    lonjakan > threshold ditandai untuk review manual — belum di-exclude
    otomatis, supaya tidak ada data corrupt yang lolos diam-diam.
    """
    flags: list[dict] = []
    close = df["close"]
    pct_change = close.pct_change(fill_method=None).abs()
    for ts, change in pct_change.items():
        if pd.notna(change) and change > CORPORATE_ACTION_JUMP_THRESHOLD:
            flags.append(
                {
                    "ts": ts,
                    "pct_change": float(change),
                    "reason": "price_jump_exceeds_threshold",
                    "requires_manual_review": True,
                }
            )
    return flags


def _forward_fill_short_gaps(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Forward fill NaN maksimal 2 bar berturut-turut; lebih dari itu → reject."""
    price_cols = ["open", "high", "low", "close"]
    na_mask = df[price_cols].isna().any(axis=1)

    if not na_mask.any():
        return df, 0

    # Cari run-length NaN berturut-turut.
    group_id = (~na_mask).cumsum()
    run_lengths = na_mask.groupby(group_id).sum()
    max_run = int(run_lengths.max()) if len(run_lengths) else 0

    if max_run > MAX_FORWARD_FILL_BARS:
        bad_group = run_lengths.idxmax()
        bad_index = df.index[(group_id == bad_group) & na_mask][0]
        raise UnrecoverableGapError(max_run, bad_index)

    filled = df.copy()
    filled[price_cols] = filled[price_cols].ffill(limit=MAX_FORWARD_FILL_BARS)
    filled_count = int(na_mask.sum())
    return filled, filled_count


def validate_ohlcv(df: pd.DataFrame, mode: str) -> ValidationResult:
    """Jalankan seluruh aturan data quality SPEC.md Bagian 6.3.

    Urutan: buang bar suspend -> deteksi corporate action -> forward-fill
    gap pendek -> cek minimum bar. Melempar `InsufficientDataError` atau
    `UnrecoverableGapError` jika data tidak layak dipakai engine.
    """
    if mode not in MIN_BARS_BY_MODE:
        raise ValueError(f"unknown mode: {mode!r}")

    working = df.sort_index().copy()

    working, dropped = _drop_suspend_bars(working)
    corporate_action_flags = _detect_corporate_actions(working)
    working, filled_count = _forward_fill_short_gaps(working)

    required = MIN_BARS_BY_MODE[mode]
    actual = len(working)
    if actual < required:
        raise InsufficientDataError(mode=mode, required=required, actual=actual)

    return ValidationResult(
        df=working,
        dropped_suspend_bars=dropped,
        corporate_action_flags=corporate_action_flags,
        forward_filled_bars=filled_count,
    )
