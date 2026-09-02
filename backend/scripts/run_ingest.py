"""Entry point untuk job ingest terjadwal via GitHub Actions.

Pengganti Celery Beat untuk deployment tanpa infrastruktur worker 24/7
(mis. Render free tier, yang tidak mendukung background worker gratis).
Memanggil fungsi task yang PERSIS SAMA dengan yang dipakai Celery
(`app.workers.tasks.ingest`), supaya tidak ada logika terduplikasi antara
jalur Celery dan jalur cron GitHub Actions.

Dipanggil dari GitHub Actions sebagai:
    python -m scripts.run_ingest sync_instruments
    python -m scripts.run_ingest ingest_daily_ohlcv
"""

from __future__ import annotations

import sys

from app.core.database import SessionLocal
from app.workers.tasks.ingest import _ingest_daily_ohlcv, _sync_instruments

TASKS = {
    "sync_instruments": _sync_instruments,
    "ingest_daily_ohlcv": _ingest_daily_ohlcv,
}


def main(task_name: str) -> None:
    task_fn = TASKS.get(task_name)
    if task_fn is None:
        raise SystemExit(f"unknown task {task_name!r}, pilihan: {sorted(TASKS)}")

    db = SessionLocal()
    try:
        result = task_fn(db)
    finally:
        db.close()

    print(f"{task_name}: {result}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m scripts.run_ingest <sync_instruments|ingest_daily_ohlcv>")
    main(sys.argv[1])
