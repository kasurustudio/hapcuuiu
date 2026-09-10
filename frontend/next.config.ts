import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export: dibutuhkan supaya frontend bisa dibundel jadi file
  // statis di dalam app desktop (Tauri) tanpa perlu Node.js runtime
  // menyala di background. Backend (FastAPI, dibundel terpisah lewat
  // PyInstaller) yang jadi satu-satunya "server" — lihat backend/
  // desktop_entrypoint.py & desktop/ (Tauri shell).
  output: "export",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
