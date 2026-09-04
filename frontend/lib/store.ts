"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Mode } from "./types";

interface ModeState {
  mode: Mode;
  setMode: (mode: Mode) => void;
}

/** Mode switcher global (SPEC.md Fase 4 item 15) — memilih mode di satu
 * halaman mengubah entry/SL/TP di seluruh aplikasi tanpa reload. */
export const useModeStore = create<ModeState>()(
  persist(
    (set) => ({
      mode: "swing",
      setMode: (mode) => set({ mode }),
    }),
    {
      name: "stockapp-mode",
      // Rehidrasi manual (lihat components/mode-hydrator.tsx) supaya render
      // pertama di client selalu cocok dengan SSR ("swing"), baru diganti
      // ke nilai localStorage setelah mount — mencegah hydration mismatch.
      skipHydration: true,
    }
  )
);
