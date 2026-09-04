"use client";

import { MODE_LABEL, type Mode } from "@/lib/types";
import { useModeStore } from "@/lib/store";

const MODES: Mode[] = ["scalping", "day", "swing", "investing"];

export function ModeSwitcher() {
  const mode = useModeStore((s) => s.mode);
  const setMode = useModeStore((s) => s.setMode);

  return (
    <div className="inline-flex rounded-lg border border-white/10 bg-neutral-900 p-0.5 text-sm">
      {MODES.map((m) => (
        <button
          key={m}
          onClick={() => setMode(m)}
          className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
            mode === m ? "bg-neutral-700 text-white" : "text-neutral-400 hover:text-neutral-200"
          }`}
        >
          {MODE_LABEL[m]}
        </button>
      ))}
    </div>
  );
}
