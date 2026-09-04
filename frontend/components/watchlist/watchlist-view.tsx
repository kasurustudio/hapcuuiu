"use client";

import { useMemo } from "react";
import Link from "next/link";
import { getSignal, getWatchlist } from "@/lib/mock-data";
import { useModeStore } from "@/lib/store";
import { MODE_LABEL } from "@/lib/types";
import { formatDate, formatPct, formatRupiah } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { ActionBadge } from "@/components/ui/action-badge";
import { ScoreBar } from "@/components/ui/score-bar";

export function WatchlistView() {
  const mode = useModeStore((s) => s.mode);
  const items = useMemo(() => getWatchlist(), []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Watchlist</h1>
        <p className="text-sm text-neutral-500">
          Sinyal ditampilkan untuk mode <span className="text-neutral-300">{MODE_LABEL[mode]}</span>.
        </p>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-white/10 text-left text-xs text-neutral-500">
                <th className="py-2 pr-4 font-normal">Simbol</th>
                <th className="py-2 pr-4 font-normal">Harga</th>
                <th className="py-2 pr-4 font-normal">%</th>
                <th className="py-2 pr-4 font-normal">Skor</th>
                <th className="py-2 pr-4 font-normal">Aksi</th>
                <th className="py-2 pr-4 font-normal">Entry Zone</th>
                <th className="py-2 pr-4 font-normal">Alert</th>
                <th className="py-2 pr-4 font-normal">Ditambahkan</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const signal = getSignal(item.symbol, mode);
                return (
                  <tr key={item.symbol} className="border-b border-white/5 last:border-0 hover:bg-white/5">
                    <td className="py-2.5 pr-4">
                      <Link href={`/analysis/${item.symbol}`} className="font-medium hover:underline">
                        {item.symbol}
                      </Link>
                      <div className="text-xs text-neutral-500">{item.name}</div>
                    </td>
                    <td className="py-2.5 pr-4 font-mono tabular-nums">{formatRupiah(signal.referencePrice)}</td>
                    <td
                      className={`py-2.5 pr-4 font-mono tabular-nums ${
                        signal.changePct >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {formatPct(signal.changePct)}
                    </td>
                    <td className="py-2.5 pr-4">
                      <div className="w-24">
                        <ScoreBar score={signal.score} size="sm" />
                      </div>
                    </td>
                    <td className="py-2.5 pr-4">
                      <ActionBadge action={signal.action} />
                    </td>
                    <td className="py-2.5 pr-4 whitespace-nowrap font-mono text-xs tabular-nums text-neutral-400">
                      {formatRupiah(signal.entry.zoneLow)}–{formatRupiah(signal.entry.zoneHigh).replace("Rp ", "")}
                    </td>
                    <td className="py-2.5 pr-4">
                      <span
                        className={`inline-flex h-2 w-2 rounded-full ${
                          item.alertActive ? "bg-emerald-400" : "bg-neutral-600"
                        }`}
                        title={item.alertActive ? "Alert aktif" : "Alert nonaktif"}
                      />
                    </td>
                    <td className="py-2.5 pr-4 text-xs text-neutral-500">{formatDate(item.addedAt)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
