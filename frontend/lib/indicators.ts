/**
 * Indikator teknikal pure function: array candle masuk, array {time,value}
 * keluar, tanpa I/O — sama seperti prinsip SPEC.md Bagian 4.3 untuk backend
 * (`services/indicators/`). Dipakai di sini untuk menghitung indikator
 * sungguhan dari data candle mock, bukan angka acak.
 */

import type { Candle } from "./types";

export interface SeriesPoint {
  time: string;
  value: number;
}

/** RSI Wilder's smoothing, periode default 14. SPEC.md Bagian 7.1. */
export function computeRSI(candles: Candle[], period = 14): SeriesPoint[] {
  if (candles.length <= period) return [];

  const result: SeriesPoint[] = [];
  let avgGain = 0;
  let avgLoss = 0;

  for (let i = 1; i <= period; i++) {
    const delta = candles[i].close - candles[i - 1].close;
    avgGain += Math.max(delta, 0);
    avgLoss += Math.max(-delta, 0);
  }
  avgGain /= period;
  avgLoss /= period;

  const rsiAt = (gain: number, loss: number): number => {
    if (loss === 0) return 100;
    const rs = gain / loss;
    return 100 - 100 / (1 + rs);
  };

  result.push({ time: candles[period].time, value: rsiAt(avgGain, avgLoss) });

  for (let i = period + 1; i < candles.length; i++) {
    const delta = candles[i].close - candles[i - 1].close;
    const gain = Math.max(delta, 0);
    const loss = Math.max(-delta, 0);
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    result.push({ time: candles[i].time, value: rsiAt(avgGain, avgLoss) });
  }

  return result;
}
