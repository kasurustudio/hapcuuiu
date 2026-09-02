# Progress

## Fase 1 — Fondasi ✅ Selesai (2026-09-02)

Sesuai roadmap SPEC.md Bagian 17.

### Apa yang selesai

1. **Scaffold monorepo** — `backend/` (FastAPI) dan `frontend/` (Next.js 15 App
   Router + TypeScript + Tailwind), `docker-compose.yml` (Postgres+TimescaleDB,
   Redis, backend, celery-worker, celery-beat, frontend).
2. **Migrasi database** — `backend/alembic/versions/0001_initial_schema.py`
   membuat seluruh 9 tabel dari SPEC.md Bagian 5.1 (`users`, `instruments`,
   `ohlcv`, `indicator_snapshots`, `signals`, `price_levels`, `fundamentals`,
   `positions`, `alerts`) plus TimescaleDB hypertable untuk `ohlcv`.
3. **`MarketAdapter`** (`app/services/market_data/base.py`) — Protocol +
   DTO sesuai Bagian 6.1, dan implementasi `YFinanceIDXAdapter` untuk IDX
   (suffix `.JK`, auto-adjust split/dividen).
4. **Validator data quality** (`app/services/market_data/validator.py`) —
   seluruh aturan Bagian 6.3: buang bar suspend (volume=0), flag lonjakan
   harga >35% untuk review manual, forward-fill gap NaN maksimal 2 bar
   (lebih dari itu ditolak), dan minimum bar per mode
   (scalping=300, day=100, swing=200, investing=200).
5. **Job ingest** (`app/workers/tasks/ingest.py` + `celery_app.py`) —
   `sync_instruments` (seed dari `lq45_seed.py`, 48 emiten) dan
   `ingest_daily_ohlcv` (backfill 5 tahun, upsert idempotent).
6. **Auth** — register/login/refresh/me + accept-disclaimer. JWT access
   (15 menit) + refresh (7 hari), password hashing argon2id.
7. **API instruments/ohlcv** — `GET /instruments`, `/instruments/{symbol}`,
   `/instruments/{symbol}/ohlcv` (filter timeframe + rentang tanggal).

### Verifikasi

- **27 unit/integration test, semua hijau** (`pytest app/tests`), coverage
  keseluruhan **88%** (target SPEC Bagian 16.10 adalah 70% — tercapai).
  Modul yang butuh koneksi jaringan langsung ke Yahoo Finance
  (`yfinance_idx.py` bagian fetch, orkestrasi `ingest_daily_ohlcv`) tidak
  bisa diuji end-to-end di sandbox ini karena **tidak ada akses jaringan
  keluar ke Yahoo Finance** — lihat "Ditunda" di bawah.
- Migrasi Alembic diverifikasi jalan bersih terhadap Postgres 16 lokal
  (seluruh 9 tabel + index + FK berhasil dibuat). Langkah pembuatan
  hypertable TimescaleDB tidak bisa diuji di sandbox ini (extension
  `timescaledb` tidak terpasang di Postgres lokal sandbox), tapi akan
  berjalan normal di `docker-compose.yml` karena image yang dipakai adalah
  `timescale/timescaledb:2.15.3-pg16`.
- **Integrasi end-to-end diverifikasi manual**: backend (`uvicorn`) +
  frontend (`next dev`) dijalankan bersamaan secara lokal, `sync_instruments`
  dipanggil langsung (tanpa broker Celery) untuk seed 48 emiten LQ45, dan
  halaman utama frontend berhasil menampilkan
  "Instrumen tersimpan di database: 48" hasil fetch dari API backend.
- Frontend: `npm run build`, `npm run lint`, dan `tsc --noEmit` semua bersih.

### Keputusan teknis & alasan

- **Validator tidak dijalankan saat ingest**, hanya di titik konsumsi
  (perhitungan indikator/sinyal, Fase 2/3). Alasan: `ohlcv` harus jadi
  source of truth data mentah; kalau aturan validasi berubah di kemudian
  hari, data historis tidak boleh sudah hilang/berubah akibat validasi lama.
- **Deteksi corporate action (Bagian 6.3) belum exclude otomatis hari
  ARA/ARB** — itu butuh tabel batas auto-rejection IDX yang baru
  diimplementasikan di Fase 2 bersama `round_to_tick()` (Bagian 8.8). Untuk
  Fase 1, semua lonjakan >35% ditandai `requires_manual_review: true`,
  bukan langsung di-exclude, supaya tidak ada data corrupt yang lolos diam-diam.
- **`YFinanceIDXAdapter.list_instruments()` melempar `NotImplementedError`**
  — yfinance tidak menyediakan daftar emiten. Daftar awal di-seed statis
  dari `lq45_seed.py` (48 simbol blue-chip IDX). Ini titik awal, bukan
  sumber kebenaran yang selalu ter-update; SPEC.md Bagian 6.2 menyebut
  scraping IDX/vendor lokal sebagai kandidat jangka panjang.
- **Refresh token JWT bersifat stateless** (tidak ada tabel token di DB),
  jadi belum bisa di-revoke sebelum expiry meskipun sudah "rotating" secara
  fungsional (token baru tiap `/auth/refresh`). Revocation list adalah
  perbaikan security yang disarankan sebelum produksi, di luar Bagian 5
  schema yang diberikan SPEC.

### Ditunda / butuh tindak lanjut

- **Tidak ada akses jaringan keluar ke Yahoo Finance di sandbox ini**
  (dikonfirmasi: `curl` ke `query1.finance.yahoo.com` gagal), jadi backfill
  5 tahun data OHLCV riil untuk 48 emiten LQ45 **belum benar-benar
  dijalankan/diverifikasi dengan data live**. Kode `ingest_daily_ohlcv`
  dan `YFinanceIDXAdapter.fetch_ohlcv` sudah diimplementasikan sesuai
  kontrak `MarketAdapter` dan diuji secara struktural (upsert idempotent,
  error handling per-simbol), tapi perlu dijalankan sekali di environment
  dengan akses jaringan keluar (mis. lewat `docker-compose up` di mesin
  developer) untuk validasi penuh acceptance criteria
  "data 5 tahun untuk 50 emiten LQ45 tersimpan dan bisa diambil via API".
- Docker daemon tidak tersedia di sandbox ini, jadi `docker-compose.yml`
  belum bisa di-build/dijalankan langsung di sini — sudah divalidasi secara
  manual dengan menjalankan backend & frontend native (lihat bagian
  Verifikasi) yang menguji jalur kode yang sama.
- Belum ada CI (GitHub Actions) untuk menjalankan test suite otomatis —
  disarankan ditambahkan sebelum Fase 2 berkembang lebih jauh.

## Fase berikutnya

Fase 2 — Mesin Analisis (indikator, deteksi S/R, candlestick pattern,
`round_to_tick()`) — **belum dimulai**, menunggu review Fase 1.
