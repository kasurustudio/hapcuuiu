"use client";

import { useState } from "react";
import type { Signal } from "@/lib/types";
import { Card } from "@/components/ui/card";

const TABS = ["Ringkasan", "Teknikal", "Fundamental", "Level", "Pattern", "Riwayat"] as const;
type Tab = (typeof TABS)[number];

function RingkasanTab({ signal }: { signal: Signal }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div>
        <h4 className="mb-2 text-sm font-medium text-emerald-400">Alasan Bullish ✓</h4>
        <ul className="space-y-1.5 text-sm text-neutral-300">
          {signal.rationale.bullish.map((line, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-emerald-400">•</span>
              {line}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h4 className="mb-2 text-sm font-medium text-red-400">Alasan Bearish ✗</h4>
        <ul className="space-y-1.5 text-sm text-neutral-300">
          {signal.rationale.bearish.map((line, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-red-400">•</span>
              {line}
            </li>
          ))}
        </ul>
      </div>
      <div className="sm:col-span-2 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-sm text-amber-200">
        <span className="font-medium">Kondisi pembatalan: </span>
        {signal.rationale.invalidation}
      </div>
    </div>
  );
}

function TeknikalTab({ signal }: { signal: Signal }) {
  const rows = [
    ["Trend", signal.scoresBreakdown.trend],
    ["Momentum", signal.scoresBreakdown.momentum],
    ["Volume", signal.scoresBreakdown.volume],
    ["Volatilitas", signal.scoresBreakdown.volatility],
    ["Struktur", signal.scoresBreakdown.structure],
  ] as const;

  return (
    <div className="max-w-md space-y-2">
      {rows.map(([label, value]) => (
        <div key={label} className="flex items-center gap-3 text-sm">
          <span className="w-24 text-neutral-400">{label}</span>
          <div className="h-1.5 flex-1 rounded-full bg-neutral-800">
            <div className="h-1.5 rounded-full bg-sky-500" style={{ width: `${value}%` }} />
          </div>
          <span className="w-8 text-right font-mono">{value}</span>
        </div>
      ))}
    </div>
  );
}

function FundamentalTab({ signal }: { signal: Signal }) {
  if (signal.scoresBreakdown.fundamental === null) {
    return (
      <p className="text-sm text-neutral-500">
        Skor fundamental hanya dihitung untuk mode Investing (SPEC.md Bagian 9). Ganti mode di
        pojok kanan atas untuk melihat contohnya.
      </p>
    );
  }
  return (
    <div className="max-w-md space-y-2 text-sm">
      <div className="flex items-center gap-3">
        <span className="w-24 text-neutral-400">Skor Valuasi</span>
        <div className="h-1.5 flex-1 rounded-full bg-neutral-800">
          <div
            className="h-1.5 rounded-full bg-violet-500"
            style={{ width: `${signal.scoresBreakdown.fundamental}%` }}
          />
        </div>
        <span className="w-8 text-right font-mono">{signal.scoresBreakdown.fundamental}</span>
      </div>
      <p className="pt-2 text-xs text-neutral-500">
        Rasio PER/PBV/ROE/DER dan estimasi fair value (SPEC.md Bagian 10) akan tersedia di Fase 8
        — belum ada di prototipe ini.
      </p>
    </div>
  );
}

function LevelTab({ signal }: { signal: Signal }) {
  const supports = signal.levels.filter((l) => l.type === "support");
  const resistances = signal.levels.filter((l) => l.type === "resistance");
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div>
        <h4 className="mb-2 text-sm font-medium text-sky-400">Support</h4>
        <ul className="space-y-1 text-sm">
          {supports.map((l) => (
            <li key={l.price} className="flex justify-between font-mono">
              <span>{l.price.toLocaleString("id-ID")}</span>
              <span className="text-neutral-500">strength {l.strength}</span>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h4 className="mb-2 text-sm font-medium text-amber-400">Resistance</h4>
        <ul className="space-y-1 text-sm">
          {resistances.map((l) => (
            <li key={l.price} className="flex justify-between font-mono">
              <span>{l.price.toLocaleString("id-ID")}</span>
              <span className="text-neutral-500">strength {l.strength}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export function DetailTabs({ signal }: { signal: Signal }) {
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

      {tab === "Ringkasan" && <RingkasanTab signal={signal} />}
      {tab === "Teknikal" && <TeknikalTab signal={signal} />}
      {tab === "Fundamental" && <FundamentalTab signal={signal} />}
      {tab === "Level" && <LevelTab signal={signal} />}
      {tab === "Pattern" && (
        <p className="text-sm text-neutral-500">
          Deteksi candlestick & chart pattern (SPEC.md Bagian 7.3) direncanakan Fase 2 — belum ada
          di prototipe ini.
        </p>
      )}
      {tab === "Riwayat" && (
        <p className="text-sm text-neutral-500">
          Riwayat sinyal sebelumnya untuk simbol ini akan tersedia setelah signal engine
          tersambung ke database sungguhan (Fase 3).
        </p>
      )}
    </Card>
  );
}
