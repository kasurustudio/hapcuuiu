import Link from "next/link";
import type { Signal } from "@/lib/types";
import { formatPct, formatRupiah } from "@/lib/format";
import { ActionBadge } from "@/components/ui/action-badge";
import { Sparkline } from "@/components/ui/sparkline";
import { generateCandles } from "@/lib/mock-data";

export function ResultsTable({ signals }: { signals: Signal[] }) {
  if (signals.length === 0) {
    return <p className="py-8 text-center text-sm text-neutral-500">Tidak ada emiten yang cocok dengan filter ini.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[860px] text-sm">
        <thead>
          <tr className="border-b border-white/10 text-left text-xs text-neutral-500">
            <th className="py-2 pr-4 font-normal">Simbol</th>
            <th className="py-2 pr-4 font-normal">Harga</th>
            <th className="py-2 pr-4 font-normal">%</th>
            <th className="py-2 pr-4 font-normal">Skor</th>
            <th className="py-2 pr-4 font-normal">Aksi</th>
            <th className="py-2 pr-4 font-normal">Entry Zone</th>
            <th className="py-2 pr-4 font-normal">SL</th>
            <th className="py-2 pr-4 font-normal">TP1</th>
            <th className="py-2 pr-4 font-normal">R:R</th>
            <th className="py-2 pr-4 font-normal">30D</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((s) => {
            const spark = generateCandles(s.symbol, 30).map((c) => c.close);
            return (
              <tr key={s.symbol} className="border-b border-white/5 last:border-0 hover:bg-white/5">
                <td className="py-2.5 pr-4">
                  <Link href={`/analysis?symbol=${s.symbol}`} className="font-medium hover:underline">
                    {s.symbol}
                  </Link>
                </td>
                <td className="py-2.5 pr-4 font-mono tabular-nums">{formatRupiah(s.referencePrice)}</td>
                <td
                  className={`py-2.5 pr-4 font-mono tabular-nums ${
                    s.changePct >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {formatPct(s.changePct)}
                </td>
                <td className="py-2.5 pr-4 font-mono tabular-nums">{s.score.toFixed(1)}</td>
                <td className="py-2.5 pr-4">
                  <ActionBadge action={s.action} />
                </td>
                <td className="py-2.5 pr-4 whitespace-nowrap font-mono text-xs tabular-nums text-neutral-400">
                  {formatRupiah(s.entry.zoneLow)}–{formatRupiah(s.entry.zoneHigh).replace("Rp ", "")}
                </td>
                <td className="py-2.5 pr-4 font-mono text-xs tabular-nums text-red-400">
                  {formatRupiah(s.stopLoss.price)}
                </td>
                <td className="py-2.5 pr-4 font-mono text-xs tabular-nums text-emerald-400">
                  {formatRupiah(s.targets[0].price)}
                </td>
                <td className="py-2.5 pr-4 font-mono tabular-nums">{s.riskReward.toFixed(2)}</td>
                <td className="py-2.5 pr-4">
                  <Sparkline values={spark} positive={s.changePct >= 0} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
