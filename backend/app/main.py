from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import init_db_schema, is_sqlite

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # SQLite (build desktop): buat skema langsung dari model (tanpa Alembic)
    # dan jalankan scheduler in-process (tanpa Celery/Redis terpisah).
    # Postgres (hosted): migrasi & scheduling dilakukan proses lain
    # (alembic upgrade head, Celery worker/beat) — lihat DEPLOYMENT.md.
    init_db_schema()
    if is_sqlite:
        from app.workers.local_scheduler import start_local_scheduler, stop_local_scheduler

        start_local_scheduler()

    yield

    if is_sqlite:
        stop_local_scheduler()


app = FastAPI(
    title="Multi-Strategy Stock Analysis Platform API",
    description=(
        "Decision support tool untuk analisis saham. Bukan platform trading — "
        "tidak ada eksekusi order ke broker. Lihat SPEC.md Bagian 0 & 3.2."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/healthz", tags=["ops"])
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz", tags=["ops"])
def readyz() -> dict:
    return {"status": "ready"}
