"use client";

import { useEffect, useRef, useState } from "react";
import { API_BASE } from "@/lib/api";

/**
 * Poll `/healthz` sampai backend sidecar (Python, dibundel Tauri) siap
 * menerima request. Diperlukan karena Tauri me-render frontend statis
 * secara instan, sementara proses sidecar butuh beberapa detik untuk mulai
 * listen — tanpa ini, fetch pertama di halaman bisa gagal dengan
 * "connection refused" pada race condition startup.
 */
export function useBackendReady(pollMs = 800, maxAttempts = 60) {
  const [ready, setReady] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const attemptsRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function check() {
      try {
        const res = await fetch(`${API_BASE}/healthz`);
        if (res.ok) {
          if (!cancelled) setReady(true);
          return;
        }
      } catch {
        // sidecar belum listen - normal di beberapa detik pertama, coba lagi
      }
      attemptsRef.current += 1;
      if (cancelled) return;
      if (attemptsRef.current >= maxAttempts) {
        setTimedOut(true);
        return;
      }
      timer = setTimeout(check, pollMs);
    }

    check();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [pollMs, maxAttempts]);

  return { ready, timedOut };
}
