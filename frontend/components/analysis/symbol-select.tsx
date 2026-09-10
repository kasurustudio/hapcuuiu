"use client";

import { useRouter } from "next/navigation";
import { INSTRUMENTS } from "@/lib/mock-data";

export function SymbolSelect({ symbol }: { symbol: string }) {
  const router = useRouter();

  return (
    <select
      value={symbol}
      onChange={(e) => router.push(`/analysis?symbol=${e.target.value}`)}
      className="rounded-md border border-white/10 bg-neutral-900 px-2.5 py-1.5 text-sm text-neutral-200"
    >
      {INSTRUMENTS.map((i) => (
        <option key={i.symbol} value={i.symbol}>
          {i.symbol} — {i.name}
        </option>
      ))}
    </select>
  );
}
