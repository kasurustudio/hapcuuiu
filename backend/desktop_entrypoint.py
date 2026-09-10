"""Entry point untuk sidecar desktop (dibundel PyInstaller).

Dipanggil oleh shell Tauri sebagai proses eksternal (`externalBin`). Tidak
dipakai untuk deployment hosted (Docker/Render pakai `uvicorn app.main:app`
langsung lewat CLI, lihat backend/Dockerfile & backend/render.yaml).

Port bisa di-override lewat env var `STOCKAPP_PORT` — default port tetap
dipakai kalau Tauri tidak mengoper apa pun, supaya gampang dites manual.
"""

from __future__ import annotations

import logging
import os
import sys

import uvicorn

# Import langsung objek `app` (bukan string "app.main:app") supaya
# PyInstaller ikut menganalisis & membundel seluruh dependency FastAPI/
# SQLAlchemy/pandas di baliknya lewat static import analysis. String-based
# import (dipakai kalau butuh --reload/multi-worker) TIDAK akan ketahuan
# oleh PyInstaller karena importnya baru terjadi saat runtime.
from app.main import app  # noqa: E402

DEFAULT_PORT = 8756


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    port = int(os.environ.get("STOCKAPP_PORT", DEFAULT_PORT))

    # Cetak port ke stdout supaya proses pemanggil (Tauri) bisa membaca port
    # aktual kalau nanti port-nya dibuat dinamis (mis. 0 = pilih port bebas).
    print(f"STOCKAPP_BACKEND_PORT={port}", flush=True)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    sys.exit(main())
