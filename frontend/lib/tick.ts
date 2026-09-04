/**
 * Aturan tick size IDX. SPEC.md Bagian 8.8.
 * Pure function, sama seperti versi Python di backend — dipakai di sini
 * untuk membulatkan angka mock supaya realistis (kelipatan tick yang valid).
 */

const TICK_TABLE: [number, number | null, number][] = [
  [0, 200, 1],
  [200, 500, 2],
  [500, 2000, 5],
  [2000, 5000, 10],
  [5000, null, 25],
];

export function getTickSize(price: number): number {
  for (const [low, high, tick] of TICK_TABLE) {
    if (price >= low && (high === null || price < high)) return tick;
  }
  return 25;
}

export function roundToTick(
  price: number,
  direction: "nearest" | "up" | "down" = "nearest"
): number {
  const tick = getTickSize(price);
  if (direction === "down") return Math.floor(price / tick) * tick;
  if (direction === "up") return Math.ceil(price / tick) * tick;
  return Math.round(price / tick) * tick;
}
