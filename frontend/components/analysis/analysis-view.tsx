"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  api,
  ApiError,
  type IndicatorSnapshot,
  type InstrumentDetail,
  type OhlcvBar,
  type PatternApi,
  type PriceLevelApi,
} from "@/lib/api";
import { useSystemStatus } from "@/lib/use-system-status";
import { computeRSI } from "@/lib/indicators";
import { formatPct, formatRupiah } from "@/lib/format";
import type { Candle, PriceLevel } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { SignalDisclaimer } from "@/components/ui/signal-disclaimer";
import { DataStatusBanner } from "@/components/ui/data-status-banner";
import { PriceChart } from "@/components/price-chart";
import { RsiChart } from "@/components/rsi-chart";
import { TradingPlanCard } from "@/components/analysis/trading-plan-card";
import { DetailTabs } from "@/components/analysis/detail-tabs";
import { SymbolSelect } from "@/components/analysis/symbol-select";

// BBCA dipakai sebagai default kalau tidak ada ?symbol= di URL — simbol ini
// juga dipakai sebagai contoh baku di test backend (lihat
// backend/app/tests/test_instruments_api.py), jadi konsisten ada di seed.
const DEFAULT_SYMBOL = "BBCA";

function toJakartaDate(iso: string): string {
  // Timestamp disimpan UTC, ditampilkan Asia/Jakarta (CLAUDE.md).
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Jakarta",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(iso));
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "00";
  return `${get("year")}-${get("month")}-${get("day")}`;
}

function toCandles(bars: OhlcvBar[]): Candle[] {
  return bars.map((b) => ({
    time: toJakartaDate(b.ts),
    open: Number(b.open),
    high: Number(b.high),
    low: Number(b.low),
    close: Number(b.close),
    volume: b.volume,
  }));
}

function toPriceLevels(levels: PriceLevelApi[]): PriceLevel[] {
  return levels.map((l) => ({
    price: Number(l.price),
    strength: Math.round(l.strength),
    type: l.level_type as "support" | "resistance",
  }));
}

function describeError(err: unknown): string {
  if (err instanceof ApiError && err.code === "INSUFFICIENT_DATA") {
    return "Data historis belum cukup untuk analisis ini (minimal 60 bar).";
  }
  return err instanceof Error ? err.message : "Gagal memuat data.";
}

interface Errors {
  instrument?: string;
  ohlcv?: string;
  indicators?: string;
  levels?: string;
  patterns?: string;
}

export function AnalysisView() {
  const { backendReady, backendTimedOut, status } = useSystemStatus();
  const searchParams = useSearchParams();
  const symbol = (searchParams.get("symbol") || DEFAULT_SYMBOL).toUpperCase();

  const [instrument, setInstrument] = useState<InstrumentDetail | null>(null);
  const [bars, setBars] = useState<OhlcvBar[]>([]);
  const [ohlcvLoaded, setOhlcvLoaded] = useState(false);
  const [indicators, setIndicators] = useState<IndicatorSnapshot | null>(null);
  const [levels, setLevels] = useState<PriceLevelApi[]>([]);
  const [patterns, setPatterns] = useState<PatternApi[]>([]);
  const [errors, setErrors] = useState<Errors>({});

  useEffect(() => {
    if (!backendReady) return;
    let cancelled = false;

    setInstrument(null);
    setBars([]);
    setOhlcvLoaded(false);
    setIndicators(null);
    setLevels([]);
    setPatterns([]);
    setErrors({});

    api
      .instrument(symbol)
      .then((v) => !cancelled && setInstrument(v))
      .catch((e) => !cancelled && setErrors((s) => ({ ...s, instrument: describeError(e) })));
    api
      .ohlcv(symbol)
      .then((v) => {
        if (cancelled) return;
        setBars(v);
        setOhlcvLoaded(true);
      })
      .catch((e) => {
        if (cancelled) return;
        setErrors((s) => ({ ...s, ohlcv: describeError(e) }));
        setOhlcvLoaded(true);
      });
    api
      .indicators(symbol)
      .then((v) => !cancelled && setIndicators(v))
      .catch((e) => !cancelled && setErrors((s) => ({ ...s, indicators: describeError(e) })));
    api
      .levels(symbol)
      .then((v) => !cancelled && setLevels(v))
      .catch((e) => !cancelled && setErrors((s) => ({ ...s, levels: describeError(e) })));
    api
      .patterns(symbol)
      .then((v) => !cancelled && setPatterns(v))
      .catch((e) => !cancelled && setErrors((s) => ({ ...s, patterns: describeError(e) })));

    return () => {
      cancelled = true;
    };
    // Poll ulang kalau bootstrap baru saja selesai supaya candle yang
    // awalnya kosong ikut terisi tanpa reload manual.
  }, [backendReady, symbol, status?.bootstrap.status]);

  const candles = toCandles(bars);
  const rsiSeries = computeRSI(candles);
  const priceLevels = toPriceLevels(levels);

  const lastBar = bars[bars.length - 1];
  const prevBar = bars[bars.length - 2];
  const lastPrice = lastBar ? Number(lastBar.close) : null;
  const changePct =
    lastBar && prevBar && Number(prevBar.close) !== 0
      ? ((Number(lastBar.close) - Number(prevBar.close)) / Number(prevBar.close)) * 100
      : null;

  return (
    <div className="flex flex-col gap-6">
      <DataStatusBanner backendReady={backendReady} backendTimedOut={backendTimedOut} systemStatus={status} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold">{symbol}</h1>
              <span className="text-sm text-neutral-400">{instrument?.name ?? errors.instrument ?? "Memuat…"}</span>
            </div>
            <div className="mt-0.5 flex items-baseline gap-2">
              <span className="font-mono text-lg tabular-nums">
                {lastPrice !== null ? formatRupiah(lastPrice) : "–"}
              </span>
              {changePct !== null && (
                <span className={`text-sm font-medium ${changePct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {formatPct(changePct)}
                </span>
              )}
            </div>
          </div>
        </div>
        <SymbolSelect symbol={symbol} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-4 lg:col-span-2">
          <Card>
            {errors.ohlcv ? (
              <p className="py-16 text-center text-sm text-amber-300">{errors.ohlcv}</p>
            ) : !ohlcvLoaded ? (
              <p className="py-16 text-center text-sm text-neutral-500">Memuat data harga…</p>
            ) : candles.length === 0 ? (
              <p className="py-16 text-center text-sm text-neutral-500">
                Belum ada data harga historis untuk simbol ini.
              </p>
            ) : (
              <PriceChart candles={candles} levels={priceLevels} />
            )}
          </Card>
          <Card title="RSI (14)">
            {candles.length > 0 ? (
              <RsiChart data={rsiSeries} />
            ) : (
              <p className="text-sm text-neutral-500">–</p>
            )}
          </Card>
        </div>

        <div className="flex flex-col gap-4">
          <TradingPlanCard />
          <SignalDisclaimer className="px-1" />
        </div>
      </div>

      <DetailTabs
        indicators={indicators}
        indicatorsError={errors.indicators ?? null}
        levels={levels}
        levelsError={errors.levels ?? null}
        patterns={patterns}
        patternsError={errors.patterns ?? null}
      />
    </div>
  );
}
