import { listInstruments } from "@/lib/api";

export default async function Home() {
  let instrumentCount: number | null = null;
  let error: string | null = null;

  try {
    const instruments = await listInstruments();
    instrumentCount = instruments.length;
  } catch {
    error = "Backend belum aktif atau tidak dapat dihubungi.";
  }

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-4 px-6 py-16">
      <h1 className="text-2xl font-semibold">
        Multi-Strategy Stock Analysis Platform
      </h1>
      <p className="text-sm text-neutral-500 dark:text-neutral-400">
        Fase 1 — Fondasi: autentikasi, skema database, dan ingest data OHLCV
        IDX sudah tersedia via API backend. Halaman analisis penuh (chart,
        screener, watchlist) menyusul di fase-fase berikutnya (lihat
        SPEC.md Bagian 17).
      </p>
      <div className="rounded-lg border border-black/10 dark:border-white/10 p-4 text-sm">
        {error ? (
          <p className="text-amber-600 dark:text-amber-400">{error}</p>
        ) : (
          <p>
            Instrumen tersimpan di database:{" "}
            <span className="font-mono">{instrumentCount}</span>
          </p>
        )}
      </div>
    </main>
  );
}
