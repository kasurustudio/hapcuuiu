# Deployment — Fase 1

Panduan menyambungkan tiga bagian yang sudah dibuat: **frontend (Vercel)**,
**backend (Render)**, dan **database (Supabase)** — semuanya di tier
**gratis**, tanpa kartu kredit.

> Catatan: dokumen ini di luar cakupan SPEC.md (yang fokus ke arsitektur
> aplikasi, bukan platform hosting spesifik). Disusun terpisah supaya
> SPEC.md tetap jadi rujukan teknis murni.

## Kenapa bukan Railway

Railway hanya trial 30 hari/$5 kredit, setelah itu wajib upgrade ke plan
Hobby ($5/bulan). Untuk kebutuhan gratis, dipakai kombinasi:

- **Render** (free web service, gratis permanen — bukan trial) untuk API
  FastAPI.
- **GitHub Actions** (gratis untuk repo publik) sebagai pengganti Celery
  Beat untuk job terjadwal (`sync_instruments`, `ingest_daily_ohlcv`).

**Trade-off yang perlu diterima:** Render free tier "tidur" setelah ±15
menit tanpa traffic — request pertama setelah itu lambat (~30-50 detik cold
start), request berikutnya normal. Untuk decision-support tool yang tidak
butuh respons real-time detik-demi-detik, ini trade-off yang wajar demi
gratis. Kalau nanti butuh backend selalu nyala (misalnya untuk fitur alert
real-time di Fase 5, SPEC.md Bagian 6.4 `evaluate_alerts` tiap 30 detik),
lihat Bagian 6 (alternatif berbayar) di bawah.

**Celery/Redis tidak dipakai di jalur gratis ini** — kode Celery
(`backend/app/workers/`) tetap ada dan tidak diubah (dipakai lagi begitu ada
budget untuk worker 24/7), tapi untuk sekarang jadwal ingest dijalankan
lewat GitHub Actions yang memanggil fungsi task yang sama persis (lihat
Bagian 3), jadi tidak ada logika yang terduplikasi.

---

## 1. Database — Supabase

1. Buat project baru di [supabase.com](https://supabase.com).
2. Ambil connection string di **Project Settings → Database → Connect →
   tab "Session pooler"** — **JANGAN** pakai tab "Direct connection":
   host `db.<ref>.supabase.co` itu **IPv6-only**, dan banyak platform
   hosting tidak punya akses keluar IPv6 sehingga akan timeout. Host
   pooler (`aws-0-<region>.pooler.supabase.com`) IPv4-compatible. Pakai
   mode **Session** (bukan **Transaction**/port 6543) karena Alembic butuh
   prepared statement yang tidak didukung mode Transaction.
3. Format `DATABASE_URL` (driver `psycopg`, bukan `psycopg2`), username
   pooler formatnya `postgres.<project-ref>` (bukan cuma `postgres`):
   ```
   postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```
   **Kalau password mengandung karakter spesial** (`@ : / ? # [ ] %` dsb),
   wajib di-URL-encode (mis. `@` → `%40`) sebelum ditempel ke connection
   string, kalau tidak parser URL akan salah membaca batas
   userinfo/host/path. Contoh di Python: `urllib.parse.quote(password,
   safe='')`. Kalau ragu, paling aman **reset password DB** di dashboard
   (Project Settings → Database → Reset Database Password) — password
   baru dari Supabase biasanya alfanumerik saja, tidak perlu encoding.
4. **Penting — TimescaleDB:** Supabase managed Postgres **tidak
   menyediakan** extension TimescaleDB. Migrasi
   (`backend/alembic/versions/0001_initial_schema.py`) sudah disesuaikan
   agar ini aman: langkah `create_hypertable` dibungkus pengecekan
   `pg_available_extensions`, jadi kalau extension tidak ada, langkah itu
   di-skip otomatis dan `ohlcv` tetap jadi tabel Postgres biasa (fungsional
   penuh, hanya tanpa partisi/kompresi otomatis TimescaleDB). Sudah diuji
   lokal terhadap Postgres 16 tanpa TimescaleDB — migrasi selesai bersih.
5. Migrasi dijalankan otomatis saat backend start di Render (lihat
   `backend/render.yaml` Bagian 2).

> **Catatan:** sandbox pengembangan Claude Code (tempat kode ini ditulis)
> memblokir koneksi keluar ke port database (5432) sepenuhnya —
> terkonfirmasi lewat tes socket langsung (port 443 ke host yang sama
> berhasil connect, port 5432 selalu timeout). Jadi koneksi ke Supabase
> **tidak bisa diverifikasi dari sandbox itu**, hanya bisa diverifikasi
> dari tempat kode benar-benar berjalan (Render, GitHub Actions, atau
> mesin lokal developer — semuanya punya akses jaringan normal).

---

## 2. Backend — Render

1. Buat akun di [render.com](https://render.com) (gratis, tanpa kartu
   kredit untuk free tier).
2. **New → Blueprint** → hubungkan repo GitHub ini. Render akan otomatis
   mendeteksi `backend/render.yaml` (sudah disiapkan: `plan: free`,
   `rootDir: backend`, build dari `Dockerfile` yang sudah ada, health check
   `/healthz`).
   - Kalau lebih suka setup manual tanpa Blueprint: **New → Web Service**
     → pilih repo → **Root Directory** = `backend` → **Runtime** = Docker
     → **Health Check Path** = `/healthz`.
3. Isi environment variables (di layar setup Blueprint, atau
   **Environment** tab kalau manual):
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | connection string Supabase (Bagian 1) |
   | `JWT_SECRET_KEY` | random string panjang (`openssl rand -hex 32`) |
   | `CORS_ORIGINS` | URL frontend Vercel, mis. `https://hapcuuiu-mu.vercel.app` |
4. Deploy. Render otomatis menjalankan `alembic upgrade head` sebelum
   `uvicorn` start (lihat `dockerCommand` di `backend/render.yaml`).
5. Setelah live, catat domain publiknya, mis.
   `https://hapcuuiu-backend.onrender.com`.
6. **Redis tidak perlu diisi** — jalur gratis ini tidak menjalankan Celery
   worker, jadi env var terkait Redis/Celery boleh dikosongkan.

---

## 3. Job terjadwal — GitHub Actions (pengganti Celery Beat)

Sudah disiapkan dua workflow di `.github/workflows/`:

- `sync-instruments.yml` — jalan tiap hari jam 06:00 WIB (SPEC.md Bagian 6.4)
- `ingest-daily-ohlcv.yml` — jalan tiap hari bursa jam 17:30 WIB

Keduanya memanggil `backend/scripts/run_ingest.py`, yang menjalankan fungsi
task Celery yang sama persis (`app.workers.tasks.ingest`) tanpa perlu
broker Redis/worker menyala 24 jam.

**Setup wajib:** tambahkan secret di GitHub repo → **Settings → Secrets
and variables → Actions → New repository secret**:
| Name | Value |
|---|---|
| `DATABASE_URL` | connection string Supabase yang sama seperti Bagian 1/2 |

Setelah secret ini ada, kedua workflow otomatis jalan sesuai jadwal. Untuk
trigger manual (tidak perlu tunggu jadwal): tab **Actions** di GitHub →
pilih workflow → **Run workflow**.

---

## 4. Frontend — Vercel

1. Project Vercel → **Settings → General → Root Directory** → `frontend`.
2. **Settings → Environment Variables** → tambahkan:
   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_BASE_URL` | `https://<domain-backend-render>/api/v1` |
3. Redeploy (Deployments → ⋯ → Redeploy) supaya env var baru terpakai —
   Next.js meng-inline `NEXT_PUBLIC_*` saat build, jadi perlu build ulang,
   bukan cukup restart.

---

## 5. Verifikasi akhir

1. `https://<domain-backend-render>/healthz` → `{"status":"ok"}` (request
   pertama bisa lambat kalau baru bangun dari sleep, ini normal)
2. `https://<domain-backend-render>/api/v1/instruments` → `[]` sampai
   workflow `sync-instruments` jalan (jadwal, atau trigger manual di
   Bagian 3)
3. Buka frontend Vercel → kotak status berubah dari "Backend belum aktif"
   menjadi "Instrumen tersimpan di database: ..."

---

## 6. Alternatif berbayar (kalau nanti butuh backend selalu nyala)

Kalau ke depannya butuh Celery worker 24/7 (mis. untuk alert real-time
Fase 5, atau supaya tidak ada cold start Render), dua opsi:

- **Fly.io** — bayar-sesuai-pakai (~$2-5/bulan untuk 1 VM kecil), tanpa
  batas trial waktu seperti Railway. Bisa jalankan `docker-compose.yml`
  yang sudah ada (backend + celery-worker + celery-beat + Redis) hampir
  apa adanya lewat `fly launch`.
- **Railway** — `backend/railway.json` sudah disiapkan kalau mau pakai ini
  (lihat riwayat commit sebelumnya), tapi trial 30 hari/$5 kemudian
  berbayar $5/bulan (plan Hobby).

Migrasi dari Render+GitHub Actions ke salah satu opsi ini tidak perlu ubah
kode aplikasi — cukup ganti tempat deploy dan hidupkan kembali service
`celery-worker`/`celery-beat` yang kodenya sudah ada di
`backend/app/workers/`.
