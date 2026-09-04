"use client";

import { useMemo } from "react";
import { generateCandles, getSignal } from "@/lib/mock-data";
import { computeRSI } from "@/lib/indicators";
import { useModeStore } from "@/lib/store";
import { formatPct, formatRupiah } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { SignalDisclaimer } from "@/components/ui/signal-disclaimer";
import { PriceChart } from "@/components/price-chart";
import { RsiChart } from "@/components/rsi-chart";
import { TradingPlanCard } from "@/components/analysis/trading-plan-card";
import { DetailTabs } from "@/components/analysis/detail-tabs";
import { SymbolSelect } from "@/components/analysis/symbol-select";

export function AnalysisView({ symbol }: { symbol: string }) {
  const mode = useModeStore((s) => s.mode);

  const signal = useMemo(() => getSignal(symbol, mode), [symbol, mode]);
  const candles = useMemo(() => generateCandles(symbol, 200), [symbol]);
  const rsiSeries = useMemo(() => computeRSI(candles), [candles]);

  const positive = signal.changePct >= 0;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold">{signal.symbol}</h1>
              <span className="text-sm text-neutral-400">{signal.name}</span>
            </div>
            <div className="mt-0.5 flex items-baseline gap-2">
              <span className="font-mono text-lg tabular-nums">{formatRupiah(signal.referencePrice)}</span>
              <span className={`text-sm font-medium ${positive ? "text-emerald-400" : "text-red-400"}`}>
                {formatPct(signal.changePct)}
              </span>
            </div>
          </div>
        </div>
        <SymbolSelect symbol={signal.symbol} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-4 lg:col-span-2">
          <Card>
            <PriceChart
              candles={candles}
              entryZone={{ low: signal.entry.zoneLow, high: signal.entry.zoneHigh }}
              stopLoss={signal.stopLoss.price}
              targets={signal.targets}
              levels={signal.levels}
            />
          </Card>
          <Card title="RSI (14)">
            <RsiChart data={rsiSeries} />
          </Card>
        </div>

        <div className="flex flex-col gap-4">
          <TradingPlanCard signal={signal} />
          <SignalDisclaimer className="px-1" />
        </div>
      </div>

      <DetailTabs signal={signal} />
    </div>
  );
}
