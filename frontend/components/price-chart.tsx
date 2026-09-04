"use client";

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  LineStyle,
  createChart,
  type IChartApi,
} from "lightweight-charts";
import type { Candle, PriceLevel } from "@/lib/types";

const UP = "#34d399";
const DOWN = "#f87171";

export function PriceChart({
  candles,
  entryZone,
  stopLoss,
  targets,
  levels,
}: {
  candles: Candle[];
  entryZone: { low: number; high: number };
  stopLoss: number;
  targets: { level: string; price: number }[];
  levels: PriceLevel[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a3a3a3",
        fontSize: 11,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.05)" },
        horzLines: { color: "rgba(255,255,255,0.05)" },
      },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.1)" },
      timeScale: { borderColor: "rgba(255,255,255,0.1)" },
      crosshair: { mode: 0 },
      autoSize: true,
    });
    chartRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: UP,
      downColor: DOWN,
      borderVisible: false,
      wickUpColor: UP,
      wickDownColor: DOWN,
    });
    candleSeries.setData(candles);

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
      lastValueVisible: false,
      priceLineVisible: false,
    });
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
      visible: false, // sembunyikan angka skala volume supaya tidak numpuk dengan label entry/SL
    });
    volumeSeries.setData(
      candles.map((c) => ({
        time: c.time,
        value: c.volume,
        color: c.close >= c.open ? "rgba(52,211,153,0.5)" : "rgba(248,113,113,0.5)",
      }))
    );

    // Overlay zona entry (SPEC.md Bagian 14.2: kotak hijau transparan,
    // disederhanakan jadi dua garis batas zona).
    candleSeries.createPriceLine({
      price: entryZone.low,
      color: "#60a5fa",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      title: "Entry Low",
    });
    candleSeries.createPriceLine({
      price: entryZone.high,
      color: "#60a5fa",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      title: "Entry High",
    });

    candleSeries.createPriceLine({
      price: stopLoss,
      color: DOWN,
      lineWidth: 2,
      lineStyle: LineStyle.Dashed,
      title: "Stop Loss",
    });

    targets.forEach((t) => {
      candleSeries.createPriceLine({
        price: t.price,
        color: UP,
        lineWidth: 1,
        lineStyle: LineStyle.Solid,
        title: t.level,
      });
    });

    // Lewati level S/R yang berdempetan (<0.8%) dengan zona entry/SL/target
    // supaya label price-line tidak bertumpuk (keterbacaan chart).
    const occupiedPrices = [entryZone.low, entryZone.high, stopLoss, ...targets.map((t) => t.price)];
    const visibleLevels = levels.filter(
      (l) => !occupiedPrices.some((p) => Math.abs(l.price - p) / p < 0.008)
    );

    visibleLevels.forEach((l) => {
      candleSeries.createPriceLine({
        price: l.price,
        color: l.type === "support" ? "rgba(96,165,250,0.4)" : "rgba(251,191,36,0.4)",
        lineWidth: l.strength > 70 ? 2 : 1,
        lineStyle: LineStyle.Dotted,
        title: `${l.type === "support" ? "S" : "R"} ${l.strength}`,
      });
    });

    chart.timeScale().fitContent();

    return () => {
      chart.remove();
      chartRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candles, entryZone.low, entryZone.high, stopLoss, JSON.stringify(targets), JSON.stringify(levels)]);

  return <div ref={containerRef} className="h-[420px] w-full" />;
}
