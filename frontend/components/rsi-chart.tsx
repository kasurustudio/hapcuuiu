"use client";

import { useEffect, useRef } from "react";
import { ColorType, LineSeries, LineStyle, createChart } from "lightweight-charts";
import type { SeriesPoint } from "@/lib/indicators";

export function RsiChart({ data }: { data: SeriesPoint[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

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
        vertLines: { visible: false },
        horzLines: { color: "rgba(255,255,255,0.05)" },
      },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.1)" },
      timeScale: { borderColor: "rgba(255,255,255,0.1)", visible: false },
      autoSize: true,
    });

    const series = chart.addSeries(LineSeries, {
      color: "#a78bfa",
      lineWidth: 2,
    });
    series.setData(data);
    series.applyOptions({ autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 100 } }) });

    series.createPriceLine({ price: 70, color: "rgba(248,113,113,0.5)", lineWidth: 1, lineStyle: LineStyle.Dashed, title: "70" });
    series.createPriceLine({ price: 30, color: "rgba(52,211,153,0.5)", lineWidth: 1, lineStyle: LineStyle.Dashed, title: "30" });

    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [data]);

  return <div ref={containerRef} className="h-[110px] w-full" />;
}
