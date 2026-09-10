"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/analysis", label: "Analysis" },
  { href: "/screener", label: "Screener" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/portfolio", label: "Portfolio" },
];

export function NavLinks() {
  const pathname = usePathname();

  return (
    <nav className="flex items-center gap-1 text-sm">
      {LINKS.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              active ? "bg-white/10 text-white" : "text-neutral-400 hover:text-neutral-200"
            }`}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
