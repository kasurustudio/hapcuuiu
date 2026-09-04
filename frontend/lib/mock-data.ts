/**
 * Data dummy untuk prototipe UI (SPEC.md tidak menyediakan data live sampai
 * backend + signal engine selesai — lihat CLAUDE.md soal urutan fase).
 *
 * Semua angka di sini dihasilkan deterministik (seeded PRNG dari simbol),
 * BUKAN Math.random() murni, supaya render server & client cocok saat
 * hydration Next.js. Struktur data mengikuti kontrak asli di SPEC.md
 * Bagian 5 & 8.7 apa adanya, supaya nanti tinggal ganti sumber data (mock
 * -> API asli) tanpa ubah bentuk komponen.
 *
 * Gate "R:R di bawah minimum mode -> aksi dipaksa hold" (SPEC.md Bagian
 * 8.3 & CLAUDE.md "Jangan pernah mengembalikan sinyal buy jika R:R <
 * minimum mode") tetap diterapkan di sini, supaya prototipe konsisten
 * dengan aturan produk yang sebenarnya.
 */

import { mulberry32, stringSeed } from "./prng";
import { roundToTick } from "./tick";
import type {
  Action,
  Candle,
  Confidence,
  Mode,
  Position,
  PriceLevel,
  Signal,
  WatchlistItem,
} from "./types";

export const TODAY = new Date("2026-09-04T00:00:00Z");

export interface InstrumentSeed {
  symbol: string;
  name: string;
  sector: string;
  basePrice: number;
}

export const INSTRUMENTS: InstrumentSeed[] = [
  { symbol: "BBCA", name: "Bank Central Asia Tbk", sector: "Financials", basePrice: 9800 },
  { symbol: "BBRI", name: "Bank Rakyat Indonesia Tbk", sector: "Financials", basePrice: 4210 },
  { symbol: "BBNI", name: "Bank Negara Indonesia Tbk", sector: "Financials", basePrice: 5225 },
  { symbol: "BMRI", name: "Bank Mandiri Tbk", sector: "Financials", basePrice: 6325 },
  { symbol: "TLKM", name: "Telkom Indonesia Tbk", sector: "Infrastructures", basePrice: 2890 },
  { symbol: "ASII", name: "Astra International Tbk", sector: "Consumer Cyclicals", basePrice: 4920 },
  { symbol: "UNVR", name: "Unilever Indonesia Tbk", sector: "Consumer Non-Cyclicals", basePrice: 2180 },
  { symbol: "ICBP", name: "Indofood CBP Sukses Makmur Tbk", sector: "Consumer Non-Cyclicals", basePrice: 11025 },
  { symbol: "INDF", name: "Indofood Sukses Makmur Tbk", sector: "Consumer Non-Cyclicals", basePrice: 7225 },
  { symbol: "KLBF", name: "Kalbe Farma Tbk", sector: "Healthcare", basePrice: 1495 },
  { symbol: "ANTM", name: "Aneka Tambang Tbk", sector: "Basic Materials", basePrice: 1615 },
  { symbol: "ADRO", name: "Alamtri Resources Indonesia Tbk", sector: "Energy", basePrice: 2430 },
  { symbol: "PGAS", name: "Perusahaan Gas Negara Tbk", sector: "Energy", basePrice: 1520 },
  { symbol: "SMGR", name: "Semen Indonesia Tbk", sector: "Basic Materials", basePrice: 3415 },
  { symbol: "PTBA", name: "Bukit Asam Tbk", sector: "Energy", basePrice: 2510 },
  { symbol: "MDKA", name: "Merdeka Copper Gold Tbk", sector: "Basic Materials", basePrice: 2110 },
  { symbol: "GOTO", name: "GoTo Gojek Tokopedia Tbk", sector: "Technology", basePrice: 68 },
  { symbol: "BUKA", name: "Bukalapak.com Tbk", sector: "Technology", basePrice: 132 },
  { symbol: "ARTO", name: "Bank Jago Tbk", sector: "Financials", basePrice: 2615 },
  { symbol: "AMRT", name: "Sumber Alfaria Trijaya Tbk", sector: "Consumer Non-Cyclicals", basePrice: 2825 },
  { symbol: "CPIN", name: "Charoen Pokphand Indonesia Tbk", sector: "Consumer Non-Cyclicals", basePrice: 4830 },
  { symbol: "JPFA", name: "Japfa Comfeed Indonesia Tbk", sector: "Consumer Non-Cyclicals", basePrice: 1330 },
  { symbol: "EXCL", name: "XL Axiata Tbk", sector: "Infrastructures", basePrice: 2415 },
  { symbol: "TOWR", name: "Sarana Menara Nusantara Tbk", sector: "Infrastructures", basePrice: 755 },
];

export function findInstrument(symbol: string): InstrumentSeed | undefined {
  return INSTRUMENTS.find((i) => i.symbol.toUpperCase() === symbol.toUpperCase());
}

const MODE_WEIGHTS: Record<Mode, ScoresBreakdownWeights> = {
  scalping: { trend: 0.15, momentum: 0.3, volume: 0.3, volatility: 0.15, structure: 0.1, fundamental: 0 },
  day: { trend: 0.25, momentum: 0.25, volume: 0.25, volatility: 0.1, structure: 0.15, fundamental: 0 },
  swing: { trend: 0.3, momentum: 0.2, volume: 0.15, volatility: 0.1, structure: 0.25, fundamental: 0 },
  investing: { trend: 0.2, momentum: 0.1, volume: 0.05, volatility: 0.05, structure: 0.15, fundamental: 0.45 },
};

interface ScoresBreakdownWeights {
  trend: number;
  momentum: number;
  volume: number;
  volatility: number;
  structure: number;
  fundamental: number;
}

interface ModeConfig {
  atrMultiplierSl: number;
  riskPerTradePct: number;
  tpR: [number, number, number];
  minRiskReward: number;
  swingLookback: number;
}

const MODE_CONFIG: Record<Mode, ModeConfig> = {
  scalping: { atrMultiplierSl: 1.0, riskPerTradePct: 0.005, tpR: [1.0, 1.5, 2.0], minRiskReward: 1.2, swingLookback: 10 },
  day: { atrMultiplierSl: 1.5, riskPerTradePct: 0.01, tpR: [1.0, 2.0, 3.0], minRiskReward: 1.5, swingLookback: 20 },
  swing: { atrMultiplierSl: 2.0, riskPerTradePct: 0.015, tpR: [1.5, 2.5, 4.0], minRiskReward: 2.0, swingLookback: 40 },
  investing: { atrMultiplierSl: 3.0, riskPerTradePct: 0.02, tpR: [2.0, 4.0, 6.0], minRiskReward: 2.5, swingLookback: 60 },
};

const DEFAULT_EQUITY = 100_000_000;
const LOT_SIZE = 100;

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function addDays(d: Date, days: number): Date {
  const copy = new Date(d);
  copy.setUTCDate(copy.getUTCDate() + days);
  return copy;
}

/** Random walk deterministik dari basePrice, mundur dari TODAY. */
export function generateCandles(symbol: string, count = 200): Candle[] {
  const seed = findInstrument(symbol);
  const basePrice = seed?.basePrice ?? 1000;
  const rng = mulberry32(stringSeed(symbol + ":candles"));

  const drift = (rng() - 0.42) * 0.0025; // sedikit bias naik rata-rata
  const volPct = 0.012 + rng() * 0.014; // 1.2%-2.6% volatilitas harian

  // Bangun mundur dari harga hari ini (basePrice) ke belakang.
  const closes: number[] = new Array(count);
  closes[count - 1] = basePrice;
  for (let i = count - 2; i >= 0; i--) {
    const shock = (rng() - 0.5) * 2 * volPct;
    const prevClose = closes[i + 1] / (1 + drift + shock);
    closes[i] = Math.max(prevClose, 10);
  }

  // Kumpulkan `count` tanggal hari bursa (Senin-Jumat) mundur dari TODAY,
  // lalu balik urutannya jadi kronologis. Dibangun mundur (bukan maju dari
  // TODAY-count hari kalender) supaya bar terakhir selalu jatuh persis di
  // TODAY meski ada akhir pekan yang dilewati.
  const tradingDates: Date[] = [];
  let dateCursor = new Date(TODAY);
  while (tradingDates.length < count) {
    if (dateCursor.getUTCDay() !== 0 && dateCursor.getUTCDay() !== 6) {
      tradingDates.push(new Date(dateCursor));
    }
    dateCursor = addDays(dateCursor, -1);
  }
  tradingDates.reverse();

  const candles: Candle[] = [];
  let prevClose = closes[0] * (1 - drift);

  for (let i = 0; i < count; i++) {
    const close = closes[i];
    const open = i === 0 ? close : prevClose;
    const intraVol = close * volPct * 0.6;
    const high = Math.max(open, close) + rng() * intraVol;
    const low = Math.min(open, close) - rng() * intraVol;
    const volume = Math.round(500_000 + rng() * 4_500_000);

    candles.push({
      time: isoDate(tradingDates[i]),
      open: roundToTick(open),
      high: roundToTick(high),
      low: roundToTick(Math.max(low, 1)),
      close: roundToTick(close),
      volume,
    });

    prevClose = close;
  }

  return candles;
}

function average(values: number[]): number {
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function computeATR(candles: Candle[], period = 14): number {
  const recent = candles.slice(-period);
  const trueRanges = recent.map((c, i) => {
    if (i === 0) return c.high - c.low;
    const prevClose = recent[i - 1].close;
    return Math.max(c.high - c.low, Math.abs(c.high - prevClose), Math.abs(c.low - prevClose));
  });
  return average(trueRanges);
}

/** Deteksi S/R sederhana untuk kebutuhan visual prototipe (bukan algoritma
 * clustering lengkap SPEC.md Bagian 7.2 — itu bagian Fase 2 di backend). */
export function deriveLevels(candles: Candle[]): PriceLevel[] {
  const window = candles.slice(-60, -1);
  const close = candles[candles.length - 1].close;

  const highs = [...window].sort((a, b) => b.high - a.high);
  const lows = [...window].sort((a, b) => a.low - b.low);

  const resistances = highs
    .filter((c) => c.high > close)
    .slice(0, 6)
    .reduce<PriceLevel[]>((acc, c) => {
      if (acc.some((l) => Math.abs(l.price - c.high) / close < 0.01)) return acc;
      acc.push({ price: roundToTick(c.high), strength: 0, type: "resistance" });
      return acc;
    }, [])
    .slice(0, 2);

  const supports = lows
    .filter((c) => c.low < close)
    .slice(0, 6)
    .reduce<PriceLevel[]>((acc, c) => {
      if (acc.some((l) => Math.abs(l.price - c.low) / close < 0.01)) return acc;
      acc.push({ price: roundToTick(c.low), strength: 0, type: "support" });
      return acc;
    }, [])
    .slice(0, 2);

  const rng = mulberry32(stringSeed(String(close)));
  const withStrength = [...resistances, ...supports].map((l) => ({
    ...l,
    strength: Math.round(45 + rng() * 50),
  }));

  return withStrength;
}

const BULLISH_TEMPLATES = [
  (s: string) => `Harga bertahan di atas EMA20 dan EMA50 selama beberapa bar terakhir pada ${s}`,
  () => `MACD histogram berbalik positif dalam beberapa bar terakhir`,
  () => `Volume di atas rata-rata 20 hari, mengindikasikan minat beli meningkat`,
  () => `RSI bergerak naik dari area netral, momentum masih mendukung`,
  (s: string) => `Harga ${s} baru saja memantul dari zona support dengan strength tinggi`,
  () => `Struktur higher-high/higher-low masih terjaga pada timeframe utama`,
];

const BEARISH_TEMPLATES = [
  () => `RSI mendekati area overbought, potensi koreksi jangka pendek`,
  (s: string) => `Resistance kuat di atas membatasi ruang gerak naik ${s}`,
  () => `Volume mulai mengecil saat harga naik — konfirmasi kurang solid`,
  () => `Volatilitas (ATR%) meningkat, risiko whipsaw lebih tinggi dari biasanya`,
];

/**
 * Fisher-Yates shuffle deterministik. PENTING: bukan `.sort(() => rng()-0.5)`
 * — pola itu implementation-defined (jumlah & urutan panggilan comparator
 * bisa beda antar mesin JS, mis. V8 Node vs V8 Chromium), jadi bisa
 * menghasilkan urutan berbeda antara SSR (Node) dan hydration di browser
 * meski seed sama -> hydration mismatch React. Fisher-Yates memanggil rng()
 * dengan jumlah & urutan yang pasti sama di mesin JS manapun.
 */
function pickTemplates(
  templates: ((s: string) => string)[],
  rng: () => number,
  n: number,
  symbol: string
): string[] {
  const arr = [...templates];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr.slice(0, n).map((fn) => fn(symbol));
}

/** Bangun objek Signal lengkap mengikuti skema SPEC.md Bagian 8.7. */
export function buildSignal(symbol: string, mode: Mode): Signal {
  const seed = findInstrument(symbol);
  if (!seed) throw new Error(`unknown instrument: ${symbol}`);

  const candles = generateCandles(symbol, 200);
  const last = candles[candles.length - 1];
  const prev = candles[candles.length - 2];
  const close = last.close;
  const changePct = ((close - prev.close) / prev.close) * 100;
  const atr = computeATR(candles);
  const levels = deriveLevels(candles);
  const config = MODE_CONFIG[mode];
  const weights = MODE_WEIGHTS[mode];

  const rng = mulberry32(stringSeed(`${symbol}:${mode}`));
  const categoryScore = () => Math.round(35 + rng() * 60);

  const scoresBreakdown = {
    trend: categoryScore(),
    momentum: categoryScore(),
    volume: categoryScore(),
    volatility: categoryScore(),
    structure: categoryScore(),
    fundamental: mode === "investing" ? categoryScore() : null,
  };

  const weightedSum =
    scoresBreakdown.trend * weights.trend +
    scoresBreakdown.momentum * weights.momentum +
    scoresBreakdown.volume * weights.volume +
    scoresBreakdown.volatility * weights.volatility +
    scoresBreakdown.structure * weights.structure +
    (scoresBreakdown.fundamental ?? 0) * weights.fundamental;
  const totalWeight =
    weights.trend + weights.momentum + weights.volume + weights.volatility + weights.structure + weights.fundamental;
  const score = Math.round((weightedSum / totalWeight) * 10) / 10;

  // Entry zone: gabungan support terdekat + jarak ATR (SPEC.md Bagian 8.4, disederhanakan).
  const nearestSupport = levels.find((l) => l.type === "support");
  const zoneLow = roundToTick((nearestSupport?.price ?? close - atr) , "down");
  const zoneHigh = roundToTick(zoneLow + atr * 0.4, "up");
  const entryRef = roundToTick((zoneLow + zoneHigh) / 2);
  const triggerBreakout = roundToTick(Math.max(zoneHigh, last.high) + 1, "up");

  const swingLow = Math.min(...candles.slice(-config.swingLookback).map((c) => c.low));
  const slStructure = swingLow - 0.5 * atr;
  const slAtr = entryRef - config.atrMultiplierSl * atr;
  const stopLossPrice = roundToTick(Math.max(slStructure, slAtr, entryRef * 0.7), "down");
  const distancePct = Math.round(((entryRef - stopLossPrice) / entryRef) * 10000) / 100;

  const R = entryRef - stopLossPrice;
  const resistances = levels.filter((l) => l.type === "resistance").sort((a, b) => a.price - b.price);
  const targets: Signal["targets"] = (["TP1", "TP2", "TP3"] as const).map((level, idx) => {
    let tpPrice = entryRef + config.tpR[idx] * R;
    const near = resistances.find((r) => Math.abs(r.price - tpPrice) < 0.5 * atr && r.strength > 60);
    if (near) tpPrice = near.price - 1;
    return {
      level,
      price: roundToTick(tpPrice, "down"),
      rMultiple: config.tpR[idx],
      exitPct: idx === 0 ? 40 : 30,
      note:
        idx === 0
          ? "Geser SL ke breakeven setelah tercapai"
          : idx === 1
            ? "Aktifkan trailing stop Chandelier"
            : "Target akhir atau trailing sampai kena",
    };
  });

  const riskReward = Math.round((targets[1].price - entryRef) / R * 100) / 100;

  let action: Action;
  let confidence: Confidence;
  if (score >= 80) {
    action = "strong_buy";
    confidence = "high";
  } else if (score >= 65) {
    action = "buy";
    confidence = "medium";
  } else if (score >= 45) {
    action = "hold";
    confidence = "medium";
  } else if (score >= 30) {
    action = "reduce";
    confidence = "medium";
  } else {
    action = "sell";
    confidence = "high";
  }

  // Gate wajib SPEC.md Bagian 8.3 / CLAUDE.md: R:R < minimum mode -> paksa hold.
  if ((action === "buy" || action === "strong_buy") && riskReward < config.minRiskReward) {
    action = "hold";
    confidence = "medium";
  }

  const riskPerShare = entryRef - stopLossPrice;
  const rawShares = (DEFAULT_EQUITY * config.riskPerTradePct) / riskPerShare;
  const lots = Math.max(Math.floor(rawShares / LOT_SIZE), 0);

  const generatedAt = TODAY.toISOString();
  const validUntilDays = mode === "scalping" ? 0 : mode === "day" ? 0 : mode === "swing" ? 7 : 30;
  const validUntil = addDays(TODAY, Math.max(validUntilDays, 1)).toISOString();

  return {
    symbol: seed.symbol,
    name: seed.name,
    mode,
    generatedAt,
    validUntil,
    referencePrice: close,
    changePct: Math.round(changePct * 100) / 100,
    action,
    direction: action === "sell" ? "short" : "long",
    score,
    confidence,
    entry: {
      method: mode === "day" || mode === "scalping" ? "buy_on_breakout" : "buy_on_weakness",
      zoneLow,
      zoneHigh,
      triggerBreakout,
      sources: [
        nearestSupport ? `support_${nearestSupport.price}_strength_${nearestSupport.strength}` : "ema20",
        "ema20",
      ],
    },
    stopLoss: {
      price: stopLossPrice,
      distancePct,
      method: slStructure > slAtr ? "structure" : "atr",
      reason:
        slStructure > slAtr
          ? `0.5 ATR di bawah swing low ${Math.round(swingLow)}`
          : `${config.atrMultiplierSl}x ATR(14) di bawah entry`,
    },
    targets,
    riskReward,
    positionSizing: {
      equityInput: DEFAULT_EQUITY,
      riskPerTradePct: config.riskPerTradePct * 100,
      lots,
      shares: lots * LOT_SIZE,
      capitalRequired: lots * LOT_SIZE * entryRef,
      actualRisk: lots * LOT_SIZE * riskPerShare,
    },
    scoresBreakdown,
    rationale: {
      bullish: pickTemplates(BULLISH_TEMPLATES, mulberry32(stringSeed(symbol + mode + "bull")), 3, seed.symbol),
      bearish: pickTemplates(BEARISH_TEMPLATES, mulberry32(stringSeed(symbol + mode + "bear")), 2, seed.symbol),
      invalidation: `Sinyal batal jika harga close di bawah ${Math.round(stopLossPrice)} atau volume mengering signifikan`,
    },
    levels,
    sector: seed.sector,
  };
}

const signalCache = new Map<string, Signal>();

export function getSignal(symbol: string, mode: Mode): Signal {
  const key = `${symbol}:${mode}`;
  let cached = signalCache.get(key);
  if (!cached) {
    cached = buildSignal(symbol, mode);
    signalCache.set(key, cached);
  }
  return cached;
}

export function listSignalsForMode(mode: Mode): Signal[] {
  return INSTRUMENTS.map((i) => getSignal(i.symbol, mode)).sort((a, b) => b.score - a.score);
}

const WATCHLIST_SYMBOLS = ["BBCA", "TLKM", "ASII", "GOTO", "ANTM", "ARTO"];

export function getWatchlist(): WatchlistItem[] {
  return WATCHLIST_SYMBOLS.map((symbol, idx) => {
    const seed = findInstrument(symbol)!;
    return {
      symbol,
      name: seed.name,
      addedAt: addDays(TODAY, -(10 + idx * 3)).toISOString(),
      alertActive: idx % 2 === 0,
    };
  });
}

const POSITION_SEED: { symbol: string; side: "long" | "short"; qty: number; entryOffsetPct: number; mode: Mode }[] = [
  { symbol: "BBCA", side: "long", qty: 400, entryOffsetPct: -3.5, mode: "swing" },
  { symbol: "ANTM", side: "long", qty: 2000, entryOffsetPct: -8, mode: "swing" },
  { symbol: "TLKM", side: "long", qty: 1000, entryOffsetPct: 2, mode: "investing" },
  { symbol: "GOTO", side: "long", qty: 50000, entryOffsetPct: -12, mode: "day" },
];

export function getPositions(): Position[] {
  return POSITION_SEED.map((p, idx) => {
    const seed = findInstrument(p.symbol)!;
    const candles = generateCandles(p.symbol, 200);
    const currentPrice = candles[candles.length - 1].close;
    const avgEntry = roundToTick(currentPrice * (1 - p.entryOffsetPct / 100));
    const atr = computeATR(candles);
    return {
      id: idx + 1,
      symbol: p.symbol,
      name: seed.name,
      side: p.side,
      qty: p.qty,
      avgEntry,
      currentPrice,
      stopLoss: roundToTick(avgEntry - atr * 2, "down"),
      takeProfit: roundToTick(avgEntry + atr * 4, "up"),
      openedAt: addDays(TODAY, -(15 + idx * 7)).toISOString(),
      mode: p.mode,
    };
  });
}

export function getIhsgSummary() {
  const rng = mulberry32(stringSeed("IHSG" + isoDate(TODAY)));
  const value = 7850 + Math.round(rng() * 200);
  const changePct = Math.round((rng() * 2 - 0.6) * 100) / 100;
  return { value, changePct };
}
