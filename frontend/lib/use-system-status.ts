"use client";

import { useEffect, useState } from "react";
import { api, type SystemStatus } from "@/lib/api";
import { useBackendReady } from "@/lib/use-backend-ready";

/**
 * Fetch `/system/status` sekali backend siap, lalu poll ulang tiap
 * `pollMs` selama bootstrap masih "running" (sync data awal sedang
 * jalan) — berhenti polling begitu status "done"/"error"/"idle".
 */
export function useSystemStatus(pollMs = 3000) {
  const { ready: backendReady, timedOut: backendTimedOut } = useBackendReady();
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    if (!backendReady) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const next = await api.systemStatus();
        if (cancelled) return;
        setStatus(next);
        if (next.bootstrap.status === "running") {
          timer = setTimeout(poll, pollMs);
        }
      } catch {
        // backend sempat tidak terjangkau - biarkan status lama, tidak retry agresif di sini
      }
    }

    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [backendReady, pollMs]);

  return { backendReady, backendTimedOut, status };
}
