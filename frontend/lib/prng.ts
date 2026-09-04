/**
 * PRNG seeded deterministik (mulberry32). Data mock di prototipe ini WAJIB
 * deterministik (bukan Math.random()) supaya render server & client cocok
 * saat hydration Next.js — nilai acak yang beda antara SSR dan client akan
 * menyebabkan hydration error.
 */

export function stringSeed(input: string): number {
  let h = 0;
  for (let i = 0; i < input.length; i++) {
    h = (Math.imul(31, h) + input.charCodeAt(i)) | 0;
  }
  return h >>> 0;
}

export function mulberry32(seed: number): () => number {
  let a = seed;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
