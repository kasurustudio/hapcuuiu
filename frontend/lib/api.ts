/**
 * Client ke backend lokal (sidecar Python dibundel Tauri, lihat
 * backend/desktop_entrypoint.py). Port sidecar tetap (8756, lihat
 * DEFAULT_PORT di sana) — bukan dipilih dinamis, jadi aman di-hardcode di
 * sini untuk build desktop. Override lewat NEXT_PUBLIC_API_BASE_URL hanya
 * dipakai untuk `next dev` manual (backend hosted via `uvicorn` biasanya
 * jalan di port lain).
 *
 * Bentuk tipe di sini mengikuti response API asli (lihat
 * backend/app/schemas/*.py), BUKAN tipe `Signal` mock di lib/types.ts —
 * signal engine (entry/SL/TP/rekomendasi) belum ada (Fase 3), jadi tidak
 * direpresentasikan di sini sama sekali, bukan diisi nilai palsu.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8756";

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    let code: string | undefined;
    let message = `Request ke ${path} gagal (${res.status})`;
    try {
      const body = await res.json();
      code = body?.detail?.error?.code;
      message = body?.detail?.error?.message ?? message;
    } catch {
      // body bukan JSON / kosong - pakai pesan default di atas
    }
    throw new ApiError(message, res.status, code);
  }
  return res.json() as Promise<T>;
}

export interface InstrumentSummary {
  symbol: string;
  name: string;
  sector: string | null;
  last_price: string | null;
  prev_close: string | null;
  change_pct: number | null;
  last_bar_at: string | null;
}

export interface InstrumentDetail {
  symbol: string;
  exchange: string;
  name: string;
  sector: string | null;
  sub_sector: string | null;
  board: string | null;
  lot_size: number;
  is_active: boolean;
  listed_at: string | null;
}

export interface OhlcvBar {
  ts: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: number;
  value: string | null;
  frequency: number | null;
}

export interface PriceLevelApi {
  price: string;
  level_type: "support" | "resistance";
  strength: number;
  touch_count: number;
  source: string;
  first_seen_at: string;
  last_tested_at: string;
  role_flipped: boolean;
}

export interface PatternApi {
  name: string;
  direction: "bullish" | "bearish";
  ts: string;
  reliability_score: number;
}

/** Bentuk longgar (dict) — struktur lengkap ada di
 * backend/app/services/indicators/snapshot.py, dikelompokkan per kategori
 * (trend/momentum/volatility/volume/structure). */
export type IndicatorSnapshot = Record<string, Record<string, unknown>>;

export interface SystemStatus {
  database: "sqlite" | "postgres";
  instrument_count: number;
  bootstrap: {
    status: "idle" | "running" | "done" | "error";
    detail: string | null;
  };
}

export const api = {
  systemStatus: () => apiFetch<SystemStatus>("/api/v1/system/status"),
  instrumentsSummary: () => apiFetch<InstrumentSummary[]>("/api/v1/instruments/summary"),
  instrument: (symbol: string) => apiFetch<InstrumentDetail>(`/api/v1/instruments/${symbol}`),
  ohlcv: (symbol: string, timeframe = "1d") =>
    apiFetch<OhlcvBar[]>(`/api/v1/instruments/${symbol}/ohlcv?timeframe=${timeframe}`),
  indicators: (symbol: string, timeframe = "1d") =>
    apiFetch<IndicatorSnapshot>(`/api/v1/instruments/${symbol}/indicators?timeframe=${timeframe}`),
  levels: (symbol: string, timeframe = "1d") =>
    apiFetch<PriceLevelApi[]>(`/api/v1/instruments/${symbol}/levels?timeframe=${timeframe}`),
  patterns: (symbol: string, timeframe = "1d") =>
    apiFetch<PatternApi[]>(`/api/v1/instruments/${symbol}/patterns?timeframe=${timeframe}`),
};

export { API_BASE };
