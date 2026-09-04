import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { findInstrument } from "@/lib/mock-data";
import { AnalysisView } from "@/components/analysis/analysis-view";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ symbol: string }>;
}): Promise<Metadata> {
  const { symbol } = await params;
  const instrument = findInstrument(symbol);
  return { title: instrument ? `${instrument.symbol} — Analysis` : "Analysis" };
}

export default async function AnalysisPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = await params;
  const instrument = findInstrument(symbol);
  if (!instrument) notFound();

  return <AnalysisView symbol={instrument.symbol} />;
}
