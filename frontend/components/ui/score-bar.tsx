function colorFor(score: number): string {
  if (score >= 65) return "bg-emerald-500";
  if (score >= 45) return "bg-neutral-400";
  if (score >= 30) return "bg-amber-500";
  return "bg-red-500";
}

export function ScoreBar({ score, size = "md" }: { score: number; size?: "sm" | "md" }) {
  const height = size === "sm" ? "h-1.5" : "h-2.5";
  return (
    <div className="flex items-center gap-2">
      <div className={`flex-1 rounded-full bg-neutral-800 ${height}`}>
        <div
          className={`${height} rounded-full ${colorFor(score)}`}
          style={{ width: `${Math.min(Math.max(score, 0), 100)}%` }}
        />
      </div>
      <span className="w-10 shrink-0 text-right font-mono text-sm tabular-nums">{score.toFixed(1)}</span>
    </div>
  );
}
