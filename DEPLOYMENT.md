# Deployment — Fase 1

Panduan menyambungkan tiga bagian yang sudah dibuat: **frontend (Vercel)**,
**backend (Railway)**, dan **database (Supabase)**.

> Catatan: dokumen ini di luar cakupan SPEC.md (yang fokus ke arsitektur
> aplikasi, bukan platform hosting spesifik). Disusun terpisah supaya
> SPEC.md tetap jadi rujukan teknis murni.

---

## 1. Database — Supabase

1. Buat project baru di [supabase.com](https://supabase.com).
2. Ambil connection string di **Project Settings → Database → Connection
   string** (pilih mode **Session** atau **Transaction pooler** — untuk
   Alembic/migrasi gunakan **Session** / direct connection, bukan pooler
   `pgbouncer` transaction mode yang tidak mendukung prepared statements).
3. Format untuk `DATABASE_URL` backend (driver `psycopg`, bukan `psycopg2`):
   ```
   postgresql+psycopg://postgres:<password>@<host>:5432/postgres
   ```
4. **Penting — TimescaleDB:** Supabase managed Postgres **tidak
   menyediakan** extension TimescaleDB. Migrasi
   (`backend/alembic/versions/0001_initial_schema.py`) sudah disesuaikan
   agar ini aman: langkah `create_hypertable` dibungkus pengecekan
   `pg_available_extensions`, jadi kalau extension tidak ada, langkah itu
   di-skip otomatis dan `ohlcv` tetap jadi tabel Postgres biasa (fungsional
   penuh, hanya tanpa partisi/kompresi otomatis TimescaleDB). Sudah diuji
   lokal terhadap Postgres 16 tanpa TimescaleDB — migrasi selesai bersih.
5. Migrasi dijalankan otomatis saat backend start (lihat `railway.json`
   Bagian 2), atau manual:
   ```bash
   cd backend
   export DATABASE_URL="postgresql+psycopg://postgres:<password>@<host>:5432/postgres"
   alembic upgrade head
   ```

---

## 2. Backend — Railway

Railway dipilih karena mendukung Dockerfile langsung dan cocok untuk
proses long-running (FastAPI + Celery worker/beat), berbeda dari Vercel
yang serverless-only.

### Setup

1. Buat project baru di [railway.app](https://railway.app) → **Deploy from
   GitHub repo** → pilih repo ini.
2. Karena ini monorepo, di **Settings → Root Directory** set ke `backend`.
   Railway akan otomatis mendeteksi `backend/railway.json` dan build lewat
   `Dockerfile` yang sudah ada.
3. Tambahkan **Redis** ke project (Railway → **+ New → Database → Redis**).
   Railway otomatis menyediakan env var `REDIS_URL` yang bisa direferensi
   service lain lewat `${{Redis.REDIS_URL}}`.
4. Set environment variables di service backend (web):
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | connection string Supabase (Bagian 1) |
   | `REDIS_URL` | `${{Redis.REDIS_URL}}` (referensi otomatis Railway) |
   | `CELERY_BROKER_URL` | `${{Redis.REDIS_URL}}/1` |
   | `CELERY_RESULT_BACKEND` | `${{Redis.REDIS_URL}}/2` |
   | `JWT_SECRET_KEY` | random string panjang (`openssl rand -hex 32`) |
   | `CORS_ORIGINS` | URL frontend Vercel, mis. `https://hapcuuiu-mu.vercel.app` |
   | `MARKET_DATA_PROVIDER_IDX` | `yfinance` |
5. Deploy. Service ini otomatis menjalankan `alembic upgrade head` sebelum
   `uvicorn` start (lihat `startCommand` di `backend/railway.json`).
6. Setelah live, catat domain publik Railway-nya (Settings → Networking →
   **Generate Domain**), mis. `https://hapcuuiu-backend.up.railway.app`.

### Celery worker & beat (opsional untuk Fase 1, dibutuhkan mulai job ingest terjadwal aktif)

Buat **dua service tambahan** di project Railway yang sama, masing-masing
"Deploy from GitHub repo" ke repo yang sama dengan **Root Directory**
`backend` juga, lalu override **Custom Start Command** di
**Settings → Deploy** (ini menggantikan `startCommand` di `railway.json`):

- Service `celery-worker`: `celery -A app.workers.celery_app worker --loglevel=info`
- Service `celery-beat`: `celery -A app.workers.celery_app beat --loglevel=info`

Set environment variables yang sama seperti service web (`DATABASE_URL`,
`REDIS_URL`, dst) di kedua service ini juga.

---

## 3. Frontend — Vercel

1. Project Vercel → **Settings → General → Root Directory** → `frontend`
   (ini penyebab 404 sebelumnya — sudah terkonfirmasi benar sekarang).
2. **Settings → Environment Variables** → tambahkan:
   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_BASE_URL` | `https://<domain-backend-railway>/api/v1` |
3. Redeploy (Deployments → ⋯ → Redeploy) supaya env var baru terpakai —
   Next.js meng-inline `NEXT_PUBLIC_*` saat build, jadi perlu build ulang,
   bukan cukup restart.

---

## 4. Verifikasi akhir

1. `https://<domain-backend-railway>/healthz` → `{"status":"ok"}`
2. `https://<domain-backend-railway>/api/v1/instruments` → `[]` (kosong,
   sampai `sync_instruments` dijalankan — lihat Bagian 5)
3. Buka frontend Vercel → kotak status harusnya berubah dari "Backend
   belum aktif" menjadi "Instrumen tersimpan di database: 0"

## 5. Seed data awal (sekali jalan)

`sync_instruments` dan `ingest_daily_ohlcv` berjalan otomatis lewat Celery
Beat (jadwal di `backend/app/workers/celery_app.py`, mengikuti SPEC.md
Bagian 6.4). Untuk seed langsung tanpa menunggu jadwal, jalankan dari mesin
lokal dengan `DATABASE_URL` diarahkan ke Supabase:

```bash
cd backend
export DATABASE_URL="postgresql+psycopg://postgres:<password>@<host>:5432/postgres"
.venv/bin/python -c "
from app.core.database import SessionLocal
from app.workers.tasks.ingest import _sync_instruments, _ingest_daily_ohlcv
db = SessionLocal()
print(_sync_instruments(db))
print(_ingest_daily_ohlcv(db))
db.close()
"
```

`_ingest_daily_ohlcv` butuh akses jaringan keluar ke Yahoo Finance
(`query1.finance.yahoo.com`) — jalankan dari mesin/environment yang punya
akses itu (lihat catatan di `PROGRESS.md` soal ini belum diverifikasi live
dari sandbox pengembangan).
