"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type InstrumentSummary } from "@/lib/api";
import { useBackendReady } from "@/lib/use-backend-ready";

export function SymbolSelect({ symbol }: { symbol: string }) {
  const router = useRouter();
  const { ready } = useBackendReady();
  const [instruments, setInstruments] = useState<InstrumentSummary[]>([]);

  useEffect(() => {
    if (!ready) return;
    let cancelled = false;
    api
      .instrumentsSummary()
      .then((rows) => {
        if (!cancelled) setInstruments(rows);
      })
      .catch(() => {
        // biarkan dropdown fallback ke simbol aktif saja kalau fetch gagal
      });
    return () => {
      cancelled = true;
    };
  }, [ready]);

  return (
    <select
      value={symbol}
      onChange={(e) => router.push(`/analysis?symbol=${e.target.value}`)}
      className="rounded-md border border-white/10 bg-neutral-900 px-2.5 py-1.5 text-sm text-neutral-200"
    >
      {instruments.length === 0 && <option value={symbol}>{symbol}</option>}
      {instruments.map((i) => (
        <option key={i.symbol} value={i.symbol}>
          {i.symbol} — {i.name}
        </option>
      ))}
    </select>
  );
}
