"use client";

import { useState } from "react";
import type { IndicatorSnapshot, PatternApi, PriceLevelApi } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { Card } from "@/components/ui/card";

const TABS = ["Ringkasan", "Teknikal", "Fundamental", "Level", "Pattern", "Riwayat"] as const;
type Tab = (typeof TABS)[number];

const NOT_AVAILABLE = "belum tersedia — Signal Engine (Fase 3) belum dibangun.";

function fmt(value: unknown, digits = 2): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "–";
  return value.toLocaleString("id-ID", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function num(value: unknown): number | null {
  return typeof value === "number" && !Number.isNaN(value) ? value : null;
}

function RingkasanTab() {
  return <p className="text-sm text-neutral-500">Ringkasan rasional bullish/bearish {NOT_AVAILABLE}</p>;
}

function TeknikalTab({ indicators, error }: { indicators: IndicatorSnapshot | null; error: string | null }) {
  if (error) return <p className="text-sm text-amber-300">{error}</p>;
  if (!indicators) return <p className="text-sm text-neutral-500">Memuat…</p>;

  const trend = indicators.trend ?? {};
  const momentum = indicators.momentum ?? {};
  const volatility = indicators.volatility ?? {};
  const volume = indicators.volume ?? {};
  const macd = trend.macd as Record<string, unknown> | undefined;

  const rows: [string, string][] = [
    ["EMA 20", fmt(num(trend.ema20), 0)],
    ["EMA 50", fmt(num(trend.ema50), 0)],
    ["MACD", fmt(num(macd?.macd), 2)],
    ["MACD Signal", fmt(num(macd?.signal), 2)],
    ["ADX", fmt(num((trend.adx as Record<string, unknown> | undefined)?.adx), 1)],
    ["RSI (14)", fmt(num(momentum.rsi14), 1)],
    ["Stochastic RSI", fmt(num((momentum.stochastic_rsi as Record<string, unknown> | undefined)?.k), 1)],
    ["ATR % (14)", `${fmt(num(volatility.atr_percent), 2)}%`],
    ["Volume Relatif", fmt(num(volume.relative_volume), 2)],
  ];

  return (
    <div className="max-w-md space-y-1.5 text-sm">
      {rows.map(([label, value]) => (
        <div key={label} className="flex items-center justify-between">
          <span className="text-neutral-400">{label}</span>
          <span className="font-mono tabular-nums">{value}</span>
        </div>
      ))}
      <p className="pt-2 text-xs text-neutral-500">
        Nilai indikator murni (SPEC.md Bagian 7.1), belum diberi bobot/skor komposit — skoring
        sinyal per mode {NOT_AVAILABLE}
      </p>
    </div>
  );
}

function FundamentalTab() {
  return (
    <p className="text-sm text-neutral-500">
      Rasio PER/PBV/ROE/DER dan estimasi fair value (SPEC.md Bagian 10) direncanakan Fase 8 —
      belum ada di sini.
    </p>
  );
}

function LevelTab({ levels, error }: { levels: PriceLevelApi[]; error: string | null }) {
  if (error) return <p className="text-sm text-amber-300">{error}</p>;
  const supports = levels.filter((l) => l.level_type === "support");
  const resistances = levels.filter((l) => l.level_type === "resistance");
  if (levels.length === 0) return <p className="text-sm text-neutral-500">Belum ada level terdeteksi.</p>;
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div>
        <h4 className="mb-2 text-sm font-medium text-sky-400">Support</h4>
        <ul className="space-y-1 text-sm">
          {supports.map((l) => (
            <li key={l.price} className="flex justify-between font-mono">
              <span>{Number(l.price).toLocaleString("id-ID")}</span>
              <span className="text-neutral-500">strength {Math.round(l.strength)}</span>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h4 className="mb-2 text-sm font-medium text-amber-400">Resistance</h4>
        <ul className="space-y-1 text-sm">
          {resistances.map((l) => (
            <li key={l.price} className="flex justify-between font-mono">
              <span>{Number(l.price).toLocaleString("id-ID")}</span>
              <span className="text-neutral-500">strength {Math.round(l.strength)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function PatternTab({ patterns, error }: { patterns: PatternApi[]; error: string | null }) {
  if (error) return <p className="text-sm text-amber-300">{error}</p>;
  if (patterns.length === 0) {
    return <p className="text-sm text-neutral-500">Tidak ada candlestick pattern terdeteksi baru-baru ini.</p>;
  }
  return (
    <ul className="space-y-2 text-sm">
      {patterns.map((p, i) => (
        <li key={`${p.name}-${p.ts}-${i}`} className="flex items-center justify-between">
          <div>
            <span className="font-medium">{p.name}</span>
            <span className="ml-2 text-xs text-neutral-500">{formatDate(p.ts)}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={p.direction === "bullish" ? "text-emerald-400" : "text-red-400"}>
              {p.direction === "bullish" ? "Bullish" : "Bearish"}
            </span>
            <span className="text-xs text-neutral-500">skor {Math.round(p.reliability_score)}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function DetailTabs({
  indicators,
  indicatorsError,
  levels,
  levelsError,
  patterns,
  patternsError,
}: {
  indicators: IndicatorSnapshot | null;
  indicatorsError: string | null;
  levels: PriceLevelApi[];
  levelsError: string | null;
  patterns: PatternApi[];
  patternsError: string | null;
}) {
  const [tab, setTab] = useState<Tab>("Ringkasan");

  return (
    <Card>
      <div className="mb-4 flex flex-wrap gap-1 border-b border-white/10 pb-2">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === t ? "bg-white/10 text-white" : "text-neutral-400 hover:text-neutral-200"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Ringkasan" && <RingkasanTab />}
      {tab === "Teknikal" && <TeknikalTab indicators={indicators} error={indicatorsError} />}
      {tab === "Fundamental" && <FundamentalTab />}
      {tab === "Level" && <LevelTab levels={levels} error={levelsError} />}
      {tab === "Pattern" && <PatternTab patterns={patterns} error={patternsError} />}
      {tab === "Riwayat" && (
        <p className="text-sm text-neutral-500">Riwayat sinyal sebelumnya untuk simbol ini {NOT_AVAILABLE}</p>
      )}
    </Card>
  );
}
