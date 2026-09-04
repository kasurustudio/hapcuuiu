import type { Action, Signal } from "./types";

/** Preset bawaan. SPEC.md Bagian 11.2. Kriteria disederhanakan dari versi
 * lengkap di SPEC (yang butuh indikator penuh dari backend) supaya bisa
 * langsung dievaluasi dari objek Signal mock di prototipe ini. */
export interface ScreenerPreset {
  id: string;
  name: string;
  description: string;
  requiresInvesting?: boolean;
  matches: (s: Signal) => boolean;
}

export const SCREENER_PRESETS: ScreenerPreset[] = [
  {
    id: "momentum_breakout",
    name: "Momentum Breakout",
    description: "Momentum & volume kuat, harga sedang naik",
    matches: (s) => s.scoresBreakdown.momentum > 65 && s.scoresBreakdown.volume > 60 && s.changePct > 0,
  },
  {
    id: "pullback_uptrend",
    name: "Pullback in Uptrend",
    description: "Trend naik, harga sedang koreksi sehat",
    matches: (s) => s.scoresBreakdown.trend > 60 && s.changePct < 0,
  },
  {
    id: "oversold_bounce",
    name: "Oversold Bounce",
    description: "Momentum lemah di dekat support kuat",
    matches: (s) => s.scoresBreakdown.momentum < 45 && s.levels.some((l) => l.type === "support" && l.strength > 60),
  },
  {
    id: "value_investing",
    name: "Value Investing",
    description: "Skor valuasi tinggi (mode Investing)",
    requiresInvesting: true,
    matches: (s) => (s.scoresBreakdown.fundamental ?? 0) > 60,
  },
  {
    id: "dividend_play",
    name: "Dividend Play",
    description: "Kualitas fundamental solid (mode Investing)",
    requiresInvesting: true,
    matches: (s) => (s.scoresBreakdown.fundamental ?? 0) > 55 && s.scoresBreakdown.structure > 50,
  },
  {
    id: "high_volume_scalp",
    name: "High Volume Scalp",
    description: "Volume relatif tinggi, cocok scalping",
    matches: (s) => s.scoresBreakdown.volume > 70,
  },
];

export interface ScreenerFilters {
  search: string;
  minScore: number;
  actions: Action[];
}

export const DEFAULT_FILTERS: ScreenerFilters = {
  search: "",
  minScore: 0,
  actions: [],
};

export function applyFilters(signals: Signal[], filters: ScreenerFilters): Signal[] {
  return signals.filter((s) => {
    if (filters.search) {
      const q = filters.search.toUpperCase();
      if (!s.symbol.includes(q) && !s.name.toUpperCase().includes(q)) return false;
    }
    if (s.score < filters.minScore) return false;
    if (filters.actions.length > 0 && !filters.actions.includes(s.action)) return false;
    return true;
  });
}
