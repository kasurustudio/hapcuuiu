"use client";

import { useEffect } from "react";
import { useModeStore } from "@/lib/store";

/** Memicu rehidrasi zustand persist setelah mount (lihat lib/store.ts). */
export function ModeHydrator() {
  useEffect(() => {
    useModeStore.persist.rehydrate();
  }, []);
  return null;
}
