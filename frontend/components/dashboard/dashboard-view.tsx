"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type InstrumentSummary } from "@/lib/api";
import { useSystemStatus } from "@/lib/use-system-status";
import { getWatchlist } from "@/lib/mock-data";
import { formatPct, formatRupiah } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { DataStatusBanner } from "@/components/ui/data-status-banner";

type SummaryWithChange = InstrumentSummary & { change_pct: number; last_price: string };

export function DashboardView() {
  const { backendReady, backendTimedOut, status } = useSystemStatus();
  const [summary, setSummary] = useState<InstrumentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Watchlist belum punya backend (lihat PROGRESS.md) — kartu ini tetap
  // pakai data mock sampai tabel & API watchlist dibangun.
  const watchlist = getWatchlist();

  useEffect(() => {
    if (!backendReady) return;
    let cancelled = false;
    api
      .instrumentsSummary()
      .then((rows) => {
        if (!cancelled) setSummary(rows);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Gagal memuat data.");
      });
    return () => {
      cancelled = true;
    };
    // Poll ulang tiap kali bootstrap baru saja selesai supaya harga yang
    // awalnya kosong ikut terisi tanpa perlu reload manual.
  }, [backendReady, status?.bootstrap.status]);

  const withPrice = (summary ?? []).filter(
    (s): s is SummaryWithChange => s.change_pct !== null && s.last_price !== null
  );
  const gainers = [...withPrice].sort((a, b) => b.change_pct - a.change_pct).slice(0, 5);
  const losers = [...withPrice].sort((a, b) => a.change_pct - b.change_pct).slice(0, 5);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-neutral-500">Ringkasan harga LQ45 dari data real Yahoo Finance.</p>
      </div>

      <DataStatusBanner backendReady={backendReady} backendTimedOut={backendTimedOut} systemStatus={status} />
      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <div className="text-xs text-neutral-500">IHSG</div>
          <div className="mt-1 text-sm text-neutral-500">
            Belum tersedia — indeks komposit di luar cakupan 48 emiten LQ45 yang di-ingest saat
            ini.
          </div>
        </Card>
        <Card>
          <div className="text-xs text-neutral-500">Instrumen Terpantau</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">
            {status?.instrument_count ?? "–"}
          </div>
          <div className="text-xs text-neutral-500">emiten LQ45 dari Yahoo Finance</div>
        </Card>
        <Card>
          <div className="text-xs text-neutral-500">Watchlist Aktif</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">{watchlist.length}</div>
          <Link href="/watchlist" className="text-xs text-sky-400 hover:underline">
            Lihat watchlist →
          </Link>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Top Gainer">
          <MoversList rows={gainers} empty="Belum ada data harga." />
        </Card>
        <Card title="Top Loser">
          <MoversList rows={losers} empty="Belum ada data harga." />
        </Card>
      </div>

      <Card title="Rekomendasi Trading">
        <p className="text-sm text-neutral-500">
          Signal Engine (skor komposit, entry zone, stop loss, take profit per mode) belum
          dibangun — direncanakan Fase 3 sesuai roadmap SPEC.md Bagian 17. Bagian ini akan
          menampilkan rekomendasi otomatis begitu tersedia, selalu disertai disclaimer bukan
          nasihat investasi.
        </p>
      </Card>
    </div>
  );
}

function MoversList({ rows, empty }: { rows: SummaryWithChange[]; empty: string }) {
  if (rows.length === 0) {
    return <p className="text-sm text-neutral-500">{empty}</p>;
  }
  return (
    <ul className="space-y-2">
      {rows.map((s) => (
        <li key={s.symbol} className="flex items-center justify-between text-sm">
          <Link href={`/analysis?symbol=${s.symbol}`} className="font-medium hover:underline">
            {s.symbol}
          </Link>
          <div className="flex items-center gap-3">
            <span className="font-mono tabular-nums text-neutral-400">
              {formatRupiah(Number(s.last_price))}
            </span>
            <span className={s.change_pct >= 0 ? "text-emerald-400" : "text-red-400"}>
              {formatPct(s.change_pct)}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
