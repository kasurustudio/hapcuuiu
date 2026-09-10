"""Lokasi file data lokal untuk build desktop (SQLite, dsb).

Dipakai hanya kalau `DATABASE_URL` tidak di-set eksplisit (mis. lewat
docker-compose/.env di jalur hosted) — di situ default tetap Postgres.
Default SQLite ini yang dipakai sidecar desktop, mengikuti konvensi lokasi
data aplikasi per OS.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "StockAnalysisPlatform"


def get_app_data_dir() -> Path:
    """Direktori data aplikasi, dibuat kalau belum ada."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    app_dir = base / APP_DIR_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_default_sqlite_url() -> str:
    db_path = get_app_data_dir() / "stockapp.db"
    return f"sqlite:///{db_path}"
