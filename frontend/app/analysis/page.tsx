import { Suspense } from "react";
import { AnalysisView } from "@/components/analysis/analysis-view";

export const metadata = { title: "Analysis" };

// Simbol dibaca dari query string (?symbol=BBCA), bukan dynamic route
// segment — supaya kompatibel dengan static export (Tauri desktop build,
// lihat next.config.ts) tanpa perlu generateStaticParams untuk tiap simbol.
export default function AnalysisPage() {
  return (
    <Suspense fallback={null}>
      <AnalysisView />
    </Suspense>
  );
}
