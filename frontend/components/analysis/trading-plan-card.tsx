import type { Signal } from "@/lib/types";
import { formatRupiah } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { ActionBadge } from "@/components/ui/action-badge";
import { ScoreBar } from "@/components/ui/score-bar";

function Row({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <span className="text-neutral-400">{label}</span>
      <div className="text-right">
        <div className="font-mono tabular-nums">{value}</div>
        {sub && <div className="text-xs text-neutral-500">{sub}</div>}
      </div>
    </div>
  );
}

export function TradingPlanCard({ signal }: { signal: Signal }) {
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm text-neutral-400">Skor Komposit</span>
          <ActionBadge action={signal.action} />
        </div>
        <ScoreBar score={signal.score} />
        <p className="mt-2 text-xs text-neutral-500">
          Confidence: <span className="capitalize text-neutral-300">{signal.confidence}</span>
        </p>
      </Card>

      <Card title="Rencana Trading">
        <Row
          label="Entry Zone"
          value={`${formatRupiah(signal.entry.zoneLow)} – ${formatRupiah(signal.entry.zoneHigh)}`}
        />
        <Row label="Trigger Breakout" value={formatRupiah(signal.entry.triggerBreakout)} />
        <div className="my-2 border-t border-white/5" />
        <Row
          label="Stop Loss"
          value={formatRupiah(signal.stopLoss.price)}
          sub={`-${signal.stopLoss.distancePct.toFixed(2)}% · ${signal.stopLoss.reason}`}
        />
        <div className="my-2 border-t border-white/5" />
        {signal.targets.map((t) => (
          <Row
            key={t.level}
            label={`${t.level} (+${t.rMultiple.toFixed(1)}R)`}
            value={formatRupiah(t.price)}
            sub={`Jual ${t.exitPct}% · ${t.note}`}
          />
        ))}
        <div className="my-2 border-t border-white/5" />
        <Row label="Risk / Reward" value={`${signal.riskReward.toFixed(2)}`} />
      </Card>

      <Card title="Position Sizing">
        <Row label="Modal" value={formatRupiah(signal.positionSizing.equityInput)} />
        <Row label="Risk / Trade" value={`${signal.positionSizing.riskPerTradePct.toFixed(2)}%`} />
        <Row label="Jumlah Lot" value={`${signal.positionSizing.lots} lot`} />
        <Row label="Kebutuhan Modal" value={formatRupiah(signal.positionSizing.capitalRequired)} />
        <Row label="Risiko Aktual" value={formatRupiah(signal.positionSizing.actualRisk)} />
      </Card>
    </div>
  );
}
