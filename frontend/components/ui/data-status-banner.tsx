import type { SystemStatus } from "@/lib/api";

/**
 * Banner status koneksi/data untuk halaman yang fetch dari backend lokal —
 * dipakai Dashboard & Analysis supaya user tahu kenapa data kosong (belum
 * konek, sedang sync awal, atau gagal karena tidak ada internet) alih-alih
 * melihat chart/tabel kosong tanpa penjelasan.
 */
export function DataStatusBanner({
  backendReady,
  backendTimedOut,
  systemStatus,
}: {
  backendReady: boolean;
  backendTimedOut: boolean;
  systemStatus: SystemStatus | null;
}) {
  if (!backendReady) {
    if (backendTimedOut) {
      return (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-200">
          Tidak bisa terhubung ke backend lokal. Coba tutup dan buka ulang aplikasi.
        </div>
      );
    }
    return (
      <div className="rounded-lg border border-sky-500/20 bg-sky-500/5 px-4 py-3 text-sm text-sky-200">
        Menghubungkan ke backend lokal…
      </div>
    );
  }

  if (systemStatus?.bootstrap.status === "running") {
    return (
      <div className="rounded-lg border border-sky-500/20 bg-sky-500/5 px-4 py-3 text-sm text-sky-200">
        Sedang mengambil data awal dari Yahoo Finance untuk pertama kali — proses ini bisa
        memakan waktu beberapa menit. Anda bisa tetap menjelajahi halaman lain sementara.
      </div>
    );
  }

  if (systemStatus?.bootstrap.status === "error") {
    return (
      <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-sm text-amber-200">
        Sinkronisasi data awal gagal (kemungkinan tidak ada koneksi internet). Data harga mungkin
        kosong/tertunda — data instrumen tetap tersedia. Sinkronisasi otomatis akan dicoba lagi
        sesuai jadwal (06:00 &amp; 17:30 WIB hari bursa).
      </div>
    );
  }

  return null;
}
