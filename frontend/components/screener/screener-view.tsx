"use client";

import { useMemo, useState } from "react";
import { listSignalsForMode } from "@/lib/mock-data";
import { useModeStore } from "@/lib/store";
import { MODE_LABEL, type Action } from "@/lib/types";
import { applyFilters, DEFAULT_FILTERS, SCREENER_PRESETS, type ScreenerFilters } from "@/lib/screener-presets";
import { Card } from "@/components/ui/card";
import { ResultsTable } from "@/components/screener/results-table";

const ACTION_OPTIONS: Action[] = ["strong_buy", "buy", "hold", "reduce", "sell"];

export function ScreenerView() {
  const mode = useModeStore((s) => s.mode);
  const allSignals = useMemo(() => listSignalsForMode(mode), [mode]);

  const [activePreset, setActivePreset] = useState<string | null>(null);
  const [filters, setFilters] = useState<ScreenerFilters>(DEFAULT_FILTERS);

  const preset = SCREENER_PRESETS.find((p) => p.id === activePreset);
  const presetFiltered = preset ? allSignals.filter(preset.matches) : allSignals;
  const results = applyFilters(presetFiltered, filters).sort((a, b) => b.score - a.score);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Screener</h1>
        <p className="text-sm text-neutral-500">
          Mode aktif: <span className="text-neutral-300">{MODE_LABEL[mode]}</span> — {allSignals.length} emiten
          dipantau
        </p>
      </div>

      <Card title="Preset">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActivePreset(null)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
              activePreset === null
                ? "border-white/30 bg-white/10 text-white"
                : "border-white/10 text-neutral-400 hover:text-neutral-200"
            }`}
          >
            Semua
          </button>
          {SCREENER_PRESETS.map((p) => (
            <button
              key={p.id}
              onClick={() => setActivePreset(p.id)}
              title={p.description}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                activePreset === p.id
                  ? "border-white/30 bg-white/10 text-white"
                  : "border-white/10 text-neutral-400 hover:text-neutral-200"
              }`}
            >
              {p.name}
            </button>
          ))}
        </div>
        {preset?.requiresInvesting && mode !== "investing" && (
          <p className="mt-3 text-xs text-amber-400">
            Preset ini paling relevan di mode Investing (skor fundamental hanya dihitung di mode itu — SPEC.md
            Bagian 9). Ganti mode di pojok kanan atas untuk hasil yang lebih bermakna.
          </p>
        )}
      </Card>

      <Card title="Filter">
        <div className="flex flex-wrap items-end gap-4">
          <label className="flex flex-col gap-1 text-xs text-neutral-400">
            Cari simbol/nama
            <input
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
              placeholder="mis. BBCA"
              className="w-40 rounded-md border border-white/10 bg-neutral-900 px-2.5 py-1.5 text-sm text-neutral-200"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs text-neutral-400">
            Skor minimum: <span className="text-neutral-200">{filters.minScore}</span>
            <input
              type="range"
              min={0}
              max={100}
              value={filters.minScore}
              onChange={(e) => setFilters((f) => ({ ...f, minScore: Number(e.target.value) }))}
              className="w-40 accent-sky-500"
            />
          </label>

          <div className="flex flex-col gap-1 text-xs text-neutral-400">
            Aksi
            <div className="flex flex-wrap gap-1.5">
              {ACTION_OPTIONS.map((a) => {
                const active = filters.actions.includes(a);
                return (
                  <button
                    key={a}
                    onClick={() =>
                      setFilters((f) => ({
                        ...f,
                        actions: active ? f.actions.filter((x) => x !== a) : [...f.actions, a],
                      }))
                    }
                    className={`rounded-md border px-2 py-1 text-xs capitalize transition-colors ${
                      active
                        ? "border-white/30 bg-white/10 text-white"
                        : "border-white/10 text-neutral-400 hover:text-neutral-200"
                    }`}
                  >
                    {a.replace("_", " ")}
                  </button>
                );
              })}
            </div>
          </div>

          {(filters.search || filters.minScore > 0 || filters.actions.length > 0) && (
            <button
              onClick={() => setFilters(DEFAULT_FILTERS)}
              className="rounded-md px-2.5 py-1.5 text-xs text-neutral-400 underline hover:text-neutral-200"
            >
              Reset filter
            </button>
          )}
        </div>
      </Card>

      <Card title={`Hasil (${results.length})`}>
        <ResultsTable signals={results} />
      </Card>
    </div>
  );
}
