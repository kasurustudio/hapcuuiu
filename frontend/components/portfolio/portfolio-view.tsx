"use client";

import { useMemo } from "react";
import Link from "next/link";
import { getPositions } from "@/lib/mock-data";
import { MODE_LABEL } from "@/lib/types";
import { formatDate, formatPct, formatRupiah } from "@/lib/format";
import { Card } from "@/components/ui/card";

export function PortfolioView() {
  const positions = useMemo(() => getPositions(), []);

  const rows = positions.map((p) => {
    const marketValue = p.currentPrice * p.qty;
    const costBasis = p.avgEntry * p.qty;
    const unrealizedPnl = p.side === "long" ? marketValue - costBasis : costBasis - marketValue;
    const pnlPct = (unrealizedPnl / costBasis) * 100;
    return { ...p, marketValue, costBasis, unrealizedPnl, pnlPct };
  });

  const totalMarketValue = rows.reduce((sum, r) => sum + r.marketValue, 0);
  const totalCost = rows.reduce((sum, r) => sum + r.costBasis, 0);
  const totalPnl = rows.reduce((sum, r) => sum + r.unrealizedPnl, 0);
  const totalPnlPct = totalCost > 0 ? (totalPnl / totalCost) * 100 : 0;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Portfolio</h1>
        <p className="text-sm text-neutral-500">Posisi terbuka, P/L, dan alokasi modal.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <div className="text-xs text-neutral-500">Nilai Portfolio</div>
          <div className="mt-1 font-mono text-2xl tabular-nums">{formatRupiah(totalMarketValue)}</div>
        </Card>
        <Card>
          <div className="text-xs text-neutral-500">Unrealized P/L</div>
          <div className={`mt-1 font-mono text-2xl tabular-nums ${totalPnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {formatRupiah(totalPnl)}
          </div>
          <div className={`text-xs ${totalPnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {formatPct(totalPnlPct)}
          </div>
        </Card>
        <Card>
          <div className="text-xs text-neutral-500">Posisi Terbuka</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">{rows.length}</div>
        </Card>
      </div>

      <Card title="Alokasi per Posisi">
        <div className="flex flex-col gap-2">
          {rows.map((r) => {
            const pct = totalMarketValue > 0 ? (r.marketValue / totalMarketValue) * 100 : 0;
            return (
              <div key={r.id} className="flex items-center gap-3 text-sm">
                <span className="w-16 shrink-0 font-medium">{r.symbol}</span>
                <div className="h-2 flex-1 rounded-full bg-neutral-800">
                  <div className="h-2 rounded-full bg-sky-500" style={{ width: `${pct}%` }} />
                </div>
                <span className="w-14 shrink-0 text-right font-mono text-xs tabular-nums text-neutral-400">
                  {pct.toFixed(1)}%
                </span>
              </div>
            );
          })}
        </div>
      </Card>

      <Card title="Posisi Terbuka">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[880px] text-sm">
            <thead>
              <tr className="border-b border-white/10 text-left text-xs text-neutral-500">
                <th className="py-2 pr-4 font-normal">Simbol</th>
                <th className="py-2 pr-4 font-normal">Mode</th>
                <th className="py-2 pr-4 font-normal">Qty</th>
                <th className="py-2 pr-4 font-normal">Avg Entry</th>
                <th className="py-2 pr-4 font-normal">Harga Sekarang</th>
                <th className="py-2 pr-4 font-normal">SL</th>
                <th className="py-2 pr-4 font-normal">TP</th>
                <th className="py-2 pr-4 font-normal">P/L</th>
                <th className="py-2 pr-4 font-normal">Dibuka</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-white/5 last:border-0 hover:bg-white/5">
                  <td className="py-2.5 pr-4">
                    <Link href={`/analysis/${r.symbol}`} className="font-medium hover:underline">
                      {r.symbol}
                    </Link>
                    <div className="text-xs text-neutral-500">{r.name}</div>
                  </td>
                  <td className="py-2.5 pr-4 text-xs text-neutral-400">{MODE_LABEL[r.mode]}</td>
                  <td className="py-2.5 pr-4 font-mono tabular-nums">{r.qty.toLocaleString("id-ID")}</td>
                  <td className="py-2.5 pr-4 font-mono tabular-nums">{formatRupiah(r.avgEntry)}</td>
                  <td className="py-2.5 pr-4 font-mono tabular-nums">{formatRupiah(r.currentPrice)}</td>
                  <td className="py-2.5 pr-4 font-mono text-xs tabular-nums text-red-400">
                    {formatRupiah(r.stopLoss)}
                  </td>
                  <td className="py-2.5 pr-4 font-mono text-xs tabular-nums text-emerald-400">
                    {formatRupiah(r.takeProfit)}
                  </td>
                  <td className={`py-2.5 pr-4 font-mono tabular-nums ${r.unrealizedPnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {formatRupiah(r.unrealizedPnl)}
                    <div className="text-xs">{formatPct(r.pnlPct)}</div>
                  </td>
                  <td className="py-2.5 pr-4 text-xs text-neutral-500">{formatDate(r.openedAt)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
