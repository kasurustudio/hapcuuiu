import Link from "next/link";
import { ModeHydrator } from "@/components/mode-hydrator";
import { ModeSwitcher } from "@/components/mode-switcher";
import { NavLinks } from "@/components/layout/nav-links";
import { DisclaimerFooter } from "@/components/disclaimer-footer";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <ModeHydrator />
      <header className="sticky top-0 z-10 border-b border-white/10 bg-neutral-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-sm font-semibold tracking-tight">
              Stock Analysis Platform
            </Link>
            <NavLinks />
          </div>
          <ModeSwitcher />
        </div>
      </header>
      <div className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">{children}</div>
      <DisclaimerFooter />
    </div>
  );
}
