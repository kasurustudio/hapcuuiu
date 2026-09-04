/**
 * Tipe data mengikuti kontrak SPEC.md Bagian 5 (skema DB) & Bagian 8.7
 * (struktur output Signal). Dipakai untuk data mock di prototipe ini, dan
 * nanti dipakai ulang begitu API asli terhubung (bentuknya sama).
 */

export type Mode = "scalping" | "day" | "swing" | "investing";

export const MODE_LABEL: Record<Mode, string> = {
  scalping: "Scalping",
  day: "Day Trading",
  swing: "Swing Trading",
  investing: "Investing",
};

export type Action = "strong_buy" | "buy" | "hold" | "reduce" | "sell";

export const ACTION_LABEL: Record<Action, string> = {
  strong_buy: "Strong Buy",
  buy: "Buy",
  hold: "Hold",
  reduce: "Reduce",
  sell: "Sell",
};

export type Confidence = "low" | "medium" | "high";

export interface Candle {
  time: string; // "YYYY-MM-DD"
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PriceLevel {
  price: number;
  strength: number; // 0..100
  type: "support" | "resistance";
}

export interface EntryPlan {
  method: "buy_on_weakness" | "buy_on_breakout";
  zoneLow: number;
  zoneHigh: number;
  triggerBreakout: number;
  sources: string[];
}

export interface StopLoss {
  price: number;
  distancePct: number;
  method: "structure" | "atr" | "max_risk";
  reason: string;
}

export interface Target {
  level: "TP1" | "TP2" | "TP3";
  price: number;
  rMultiple: number;
  exitPct: number;
  note: string;
}

export interface PositionSizing {
  equityInput: number;
  riskPerTradePct: number;
  lots: number;
  shares: number;
  capitalRequired: number;
  actualRisk: number;
}

export interface ScoresBreakdown {
  trend: number;
  momentum: number;
  volume: number;
  volatility: number;
  structure: number;
  fundamental: number | null;
}

export interface Rationale {
  bullish: string[];
  bearish: string[];
  invalidation: string;
}

export interface Signal {
  symbol: string;
  name: string;
  mode: Mode;
  generatedAt: string;
  validUntil: string;
  referencePrice: number;
  changePct: number;
  action: Action;
  direction: "long" | "short" | "neutral";
  score: number;
  confidence: Confidence;
  entry: EntryPlan;
  stopLoss: StopLoss;
  targets: Target[];
  riskReward: number;
  positionSizing: PositionSizing;
  scoresBreakdown: ScoresBreakdown;
  rationale: Rationale;
  levels: PriceLevel[];
  sector: string;
}

export interface WatchlistItem {
  symbol: string;
  name: string;
  addedAt: string;
  alertActive: boolean;
}

export interface Position {
  id: number;
  symbol: string;
  name: string;
  side: "long" | "short";
  qty: number;
  avgEntry: number;
  currentPrice: number;
  stopLoss: number;
  takeProfit: number;
  openedAt: string;
  mode: Mode;
}
