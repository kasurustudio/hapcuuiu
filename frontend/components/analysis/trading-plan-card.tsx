import { Card } from "@/components/ui/card";

/**
 * Signal Engine (skor komposit, entry zone, stop loss, take profit,
 * position sizing per mode) belum dibangun — direncanakan Fase 3 sesuai
 * roadmap SPEC.md Bagian 17. Kartu ini sengaja jadi placeholder jujur,
 * bukan diisi angka fabrikasi dari data harga real (itu akan terlihat
 * seperti rekomendasi trading sungguhan padahal bukan — melanggar
 * CLAUDE.md soal klaim prediktif).
 */
export function TradingPlanCard() {
  return (
    <Card title="Rencana Trading">
      <p className="text-sm text-neutral-500">
        Rekomendasi entry zone, stop loss, take profit, dan position sizing belum tersedia —
        Signal Engine (Fase 3) belum dibangun. Chart di samping menampilkan data harga & level
        Support/Resistance real, tanpa rekomendasi aksi apapun.
      </p>
    </Card>
  );
}
