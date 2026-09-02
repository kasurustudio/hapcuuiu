export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface Instrument {
  symbol: string;
  exchange: string;
  name: string;
  sector: string | null;
  sub_sector: string | null;
  board: string | null;
  lot_size: number;
  is_active: boolean;
  listed_at: string | null;
}

export async function listInstruments(): Promise<Instrument[]> {
  const res = await fetch(`${API_BASE_URL}/instruments`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Gagal memuat instrumen: ${res.status}`);
  }
  return res.json();
}
