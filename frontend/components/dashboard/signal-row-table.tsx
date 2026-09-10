import Link from "next/link";
import type { Signal } from "@/lib/types";
import { formatPct, formatRupiah } from "@/lib/format";
import { ActionBadge } from "@/components/ui/action-badge";
import { ScoreBar } from "@/components/ui/score-bar";

export function SignalRowTable({ signals }: { signals: Signal[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-left text-xs text-neutral-500">
            <th className="py-2 pr-4 font-normal">Simbol</th>
            <th className="py-2 pr-4 font-normal">Harga</th>
            <th className="py-2 pr-4 font-normal">Perubahan</th>
            <th className="py-2 pr-4 font-normal">Skor</th>
            <th className="py-2 pr-4 font-normal">Aksi</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((s) => (
            <tr key={s.symbol} className="border-b border-white/5 last:border-0 hover:bg-white/5">
              <td className="py-2.5 pr-4">
                <Link href={`/analysis?symbol=${s.symbol}`} className="font-medium hover:underline">
                  {s.symbol}
                </Link>
                <div className="text-xs text-neutral-500">{s.sector}</div>
              </td>
              <td className="py-2.5 pr-4 font-mono tabular-nums">{formatRupiah(s.referencePrice)}</td>
              <td
                className={`py-2.5 pr-4 font-mono tabular-nums ${
                  s.changePct >= 0 ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {formatPct(s.changePct)}
              </td>
              <td className="py-2.5 pr-4">
                <div className="w-28">
                  <ScoreBar score={s.score} size="sm" />
                </div>
              </td>
              <td className="py-2.5 pr-4">
                <ActionBadge action={s.action} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
