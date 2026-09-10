"use client";

import { useMemo } from "react";
import Link from "next/link";
import { getIhsgSummary, getWatchlist, listSignalsForMode } from "@/lib/mock-data";
import { useModeStore } from "@/lib/store";
import { MODE_LABEL } from "@/lib/types";
import { formatPct } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { ActionBadge } from "@/components/ui/action-badge";
import { SignalRowTable } from "@/components/dashboard/signal-row-table";

export function DashboardView() {
  const mode = useModeStore((s) => s.mode);
  const ihsg = useMemo(() => getIhsgSummary(), []);
  const signals = useMemo(() => listSignalsForMode(mode), [mode]);
  const watchlist = useMemo(() => getWatchlist(), []);

  const gainers = [...signals].sort((a, b) => b.changePct - a.changePct).slice(0, 5);
  const losers = [...signals].sort((a, b) => a.changePct - b.changePct).slice(0, 5);
  const topSignals = signals.slice(0, 8);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-neutral-500">
          Ringkasan pasar dan sinyal terbaru untuk mode <span className="text-neutral-300">{MODE_LABEL[mode]}</span>.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <div className="text-xs text-neutral-500">IHSG</div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="font-mono text-2xl tabular-nums">{ihsg.value.toLocaleString("id-ID")}</span>
            <span className={`text-sm font-medium ${ihsg.changePct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {formatPct(ihsg.changePct)}
            </span>
          </div>
        </Card>
        <Card>
          <div className="text-xs text-neutral-500">Sinyal Strong Buy/Buy</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">
            {signals.filter((s) => s.action === "strong_buy" || s.action === "buy").length}
          </div>
          <div className="text-xs text-neutral-500">dari {signals.length} emiten dipantau</div>
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
          <MoversList signals={gainers} />
        </Card>
        <Card title="Top Loser">
          <MoversList signals={losers} />
        </Card>
      </div>

      <Card title={`Sinyal Terbaru — ${MODE_LABEL[mode]}`}>
        <SignalRowTable signals={topSignals} />
      </Card>
    </div>
  );
}

function MoversList({ signals }: { signals: ReturnType<typeof listSignalsForMode> }) {
  return (
    <ul className="space-y-2">
      {signals.map((s) => (
        <li key={s.symbol} className="flex items-center justify-between text-sm">
          <Link href={`/analysis?symbol=${s.symbol}`} className="font-medium hover:underline">
            {s.symbol}
          </Link>
          <div className="flex items-center gap-2">
            <span className={s.changePct >= 0 ? "text-emerald-400" : "text-red-400"}>
              {formatPct(s.changePct)}
            </span>
            <ActionBadge action={s.action} />
          </div>
        </li>
      ))}
    </ul>
  );
}
