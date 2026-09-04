import { ACTION_LABEL, type Action } from "@/lib/types";

/** Warna: hijau bullish/profit, merah bearish/loss, abu netral. SPEC.md 14.3. */
const STYLES: Record<Action, string> = {
  strong_buy: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  buy: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  hold: "bg-neutral-500/15 text-neutral-300 border-neutral-500/30",
  reduce: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  sell: "bg-red-500/15 text-red-400 border-red-500/30",
};

export function ActionBadge({ action, className = "" }: { action: Action; className?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${STYLES[action]} ${className}`}
    >
      {ACTION_LABEL[action]}
    </span>
  );
}
