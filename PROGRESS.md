# Progress

## Fase 2 — Mesin Analisis ✅ Selesai (2026-09-04)

Sesuai roadmap SPEC.md Bagian 17. Dipicu oleh permintaan user untuk mulai
menyiapkan logic asli (bukan mock) supaya platform bisa dipakai — disepakati
prioritas "semua mode termasuk Scalping/Day Trading" untuk arah jangka
panjang, dengan data intraday real-time ditunda sampai ada vendor berbayar
(lihat catatan "Ditunda" di bawah). Fase 2 sendiri mode-agnostic (indikator
teknikal murni), jadi tidak terpengaruh keputusan itu.

### Apa yang selesai

1. **Tick size utility** (`app/core/tick.py`) — `round_to_tick()`/
   `get_tick_size()` sesuai tabel SPEC.md Bagian 8.8, pakai `Decimal`.
2. **~30 indikator teknikal** di `app/services/indicators/`, dipecah per
   kategori sesuai SPEC.md Bagian 7.1, semua pure function (DataFrame
   masuk, Series/DataFrame keluar, tanpa I/O):
   - `trend.py` — SMA, EMA, MACD, ADX+DI, Parabolic SAR, SuperTrend, Ichimoku
   - `momentum.py` — RSI (+deteksi divergence fractal), Stochastic,
     Stochastic RSI, CCI, Williams %R, ROC, MFI
   - `volatility.py` — ATR/ATR%, Bollinger Bands+Bandwidth+%B, Keltner
     Channel, Donchian Channel, Historical Volatility
   - `volume.py` — Volume MA, Relative Volume, OBV, VWAP (reset harian),
     Anchored VWAP, Accumulation/Distribution, Volume Profile (POC/VAH/VAL)
   - `structure.py` — Pivot Points (Classic/Fibonacci/Camarilla, harian &
     mingguan), Fibonacci retracement/extension, Swing High/Low (fractal)
   - `common.py` — `wilder_smooth()`/`true_range()` dipakai bersama
     (ATR/ADX/RSI semua pakai smoothing Wilder yang sama, bukan EMA biasa)
   - `snapshot.py` — merangkai semua di atas jadi satu snapshot nilai
     terbaru per kategori (bentuknya = `indicator_snapshots.payload`)
3. **Detektor Support/Resistance** (`app/services/levels/detector.py`) —
   6 langkah algoritma SPEC.md Bagian 7.2 diimplementasikan apa adanya:
   swing fractal (n=5, 250 bar) → clustering toleransi 0.5×ATR → scoring
   strength 5 komponen berbobot (touch_count 30%, volume 25%, recency
   decay 20%, rejection wick 15%, timeframe weight 10%) → tambah level dari
   POC volume profile/pivot/round number/EMA50-200/52w high-low → filter
   strength>=40, maks 8 per sisi → klasifikasi support/resistance +
   `role_flipped`.
4. **Candlestick pattern + filter konteks** (`app/services/patterns/
   candlestick.py`) — 12 pattern (Doji, Marubozu, Hammer/Hanging Man,
   Inverted Hammer/Shooting Star, Bullish/Bearish Engulfing, Morning/
   Evening Star, Piercing Line/Dark Cloud Cover, Three White Soldiers/
   Black Crows). **Filter konteks diimplementasikan sungguhan** (bukan
   cuma deteksi bentuk) — pattern reversal hanya dilaporkan kalau ada
   downtrend/uptrend monoton >=5 bar SEBELUM pattern, atau dekat level
   support/resistance; kalau tidak, pattern-nya di-skip sama sekali. Diuji
   eksplisit dengan test negatif (`test_hammer_shape_without_any_context_
   is_not_reported`).
5. **Endpoint API** (SPEC.md Bagian 13): `GET /instruments/{symbol}/
   indicators`, `/levels`, `/patterns` — `/patterns` memakai level S/R dari
   `/levels` sebagai konteks, jadi kedua endpoint konsisten satu sama lain.
   Gate `INSUFFICIENT_DATA` (422) kalau data OHLCV kurang dari 60 bar.

### Verifikasi

- **146 test lolos** (naik dari 27 di akhir Fase 1), coverage total **95%**
  (syarat CLAUDE.md 70%), semua modul indikator/levels/patterns baru di
  **90-100%** coverage individual.
- Banyak indikator diverifikasi lewat **cross-check implementasi independen**
  (bukan cuma re-test angka yang sama): ADX, RSI, dan MACD masing-masing
  punya reimplementasi ulang dari nol di file test (loop Python biasa,
  BUKAN memanggil fungsi yang diuji) untuk membuktikan hasilnya benar
  secara matematis, bukan cuma konsisten dengan dirinya sendiri.
- **1 bug hydration-style ditemukan & diperbaiki saat menulis test**:
  fungsi `_is_downtrend`/`_is_uptrend` di deteksi pattern awalnya cuma
  membandingkan titik awal-akhir window (gampang salah-positif kalau
  harga zig-zag), dan untuk pattern 3-candle sempat memasukkan bar pattern
  itu sendiri ke jendela pengecekan tren (mengotori hasil). Ditemukan lewat
  test negatif yang sengaja dibuat ketat, diperbaiki jadi cek monotonic
  penuh atas bar SEBELUM pattern mulai.
- Endpoint API diuji end-to-end lewat `TestClient` + Postgres asli (bukan
  mock), termasuk jalur `INSUFFICIENT_DATA`.

### Keputusan teknis & alasan

- **Tidak pakai `pandas-ta`** — semua indikator ditulis manual dengan
  pandas/numpy. Alasan: (1) `pandas-ta` punya masalah kompatibilitas
  dikenal dengan numpy>=2.0 (proyek ini pakai numpy 2.2), (2) CLAUDE.md
  tetap mensyaratkan unit test dengan nilai referensi manual meski pakai
  library, jadi tidak menghemat effort testing; nulis manual memberi
  kontrol penuh dan menghindari "bergantung buta pada library".
- **Konfigurasi mode (`config/modes.yaml`) belum dibaca di sini** — loader
  config mode adalah item eksplisit Fase 3 (Bagian 17: "Loader konfigurasi
  mode dari YAML"). Endpoint `/indicators` di Fase 2 karena itu
  mode-agnostic: mengembalikan semua indikator dengan periode default
  SPEC.md Bagian 7.1, bukan subset per-mode. Parameter `set=` yang
  disebut contoh URL SPEC.md Bagian 13 belum diimplementasikan — nanti
  tersambung begitu modes.yaml loader ada di Fase 3.
- **Bobot timeframe & strength sumber tambahan (POC/pivot/round number/
  EMA/52w) di detector S/R pakai nilai default yang saya tentukan sendiri**
  — SPEC.md Bagian 7.2 memberi formula presisi untuk strength cluster
  berbasis swing (5 komponen berbobot), tapi tidak memberi angka pasti
  untuk bobot antar-timeframe atau strength level dari sumber non-swing.
  Didokumentasikan di komentar `detector.py`, gampang dikalibrasi ulang.
- **Minimum data endpoint (60 bar)** dipilih independen dari
  `MIN_BARS_BY_MODE` di `validator.py` (100-300 tergantung mode) — gate
  mode-based itu urusan signal engine Fase 3. 60 bar dipilih supaya cukup
  untuk indikator dengan periode terpanjang di sini (Ichimoku senkou
  ~78 bar sebenarnya masih bisa NaN di bar-bar awal, tapi tidak
  menghalangi indikator lain yang lebih pendek).

### Ditunda / butuh tindak lanjut

- **Data intraday real-time (Scalping/Day Trading) belum ada** — user
  memilih "pakai yang gratis dulu": rencana ke depan adalah ingest lebih
  sering (tiap 15-30 menit saat jam bursa via GitHub Actions, masih
  gratis) memakai kapabilitas intraday terbatas `yfinance`, dengan
  Scalping tetap ditandai degraded sesuai desain SPEC.md sendiri (Bagian
  6.2) sampai ada vendor data berbayar. Belum diimplementasikan — nunggu
  signal engine (Fase 3) yang akan menentukan gate liquidity/data quality
  per mode.
- **Volume Profile pakai bucketing sederhana** (assign volume bar
  berdasarkan typical price ke 1 bucket), bukan distribusi volume across
  the bar's high-low range. Cukup untuk POC/VAH/VAL yang wajar, tapi versi
  production-grade biasanya mendistribusikan volume merata di sepanjang
  range bar.
- **Chart pattern** (Double Top/Bottom, Head & Shoulders, dst — SPEC.md
  Bagian 7.3, ditandai "Fase 2" di situ tapi merujuk ke fase rollout
  MARKET bukan fase roadmap Bagian 17) sengaja TIDAK dikerjakan — roadmap
  Bagian 17 Fase 2 eksplisit hanya minta "deteksi candlestick pattern",
  bukan chart pattern.

## Addendum UI prototype (2026-09-04): frontend dengan data dummy, sebelum backend

User minta lihat prototipe UI dulu di Vercel sebelum setup backend lebih jauh.
Dibangun 5 halaman utama pakai **data mock deterministik** (bukan API asli):

- `/` Dashboard — ringkasan IHSG, top gainer/loser, sinyal terbaru sesuai mode aktif
- `/analysis/[symbol]` — halaman inti sesuai SPEC.md Bagian 14.2: candlestick
  chart (`lightweight-charts`) dengan overlay entry zone/SL/TP/S-R, mini
  chart RSI(14) asli (dihitung dari data candle, bukan acak), panel rencana
  trading + position sizing, tab Ringkasan/Teknikal/Fundamental/Level/
  Pattern/Riwayat (tab yang datanya belum ada — Pattern, Riwayat — diberi
  keterangan jujur "belum tersedia, direncanakan Fase X", bukan data palsu)
- `/screener` — preset SPEC.md Bagian 11.2 (Momentum Breakout, dst, dengan
  kriteria yang disederhanakan supaya bisa dievaluasi dari objek Signal
  mock) + filter skor/aksi/pencarian yang benar-benar berfungsi
- `/watchlist`, `/portfolio` — sesuai SPEC.md Bagian 14.1

**Keputusan teknis:**
- Mode switcher global (Scalp/Day/Swing/Invest) pakai Zustand + localStorage
  (`lib/store.ts`), mengubah entry/SL/TP di seluruh app tanpa reload —
  acceptance criteria SPEC.md Bagian 16.6 dicek manual via Playwright, lolos.
- Semua angka mock **deterministik** (seeded PRNG di `lib/prng.ts`, bukan
  `Math.random()`) supaya render server & client cocok saat hydration
  Next.js. Logika kalkulasi entry/SL/TP/position sizing/tick size di
  `lib/mock-data.ts` & `lib/tick.ts` sengaja meniru rumus asli di SPEC.md
  Bagian 8.4-8.6 & 8.8 (bukan angka acak murni), termasuk gate "R:R di
  bawah minimum mode -> paksa hold" dari CLAUDE.md.
- **Bug hydration nyata ditemukan & diperbaiki** lewat testing Playwright
  sungguhan (bukan cuma `tsc`/build): fungsi shuffle rationale bullish/
  bearish awalnya pakai `.sort(() => rng()-0.5)` — pola ini
  implementation-defined, hasilnya beda antara V8 Node (SSR) dan V8
  Chromium (hydration client), menyebabkan React hydration mismatch.
  Diganti Fisher-Yates shuffle deterministik (`pickTemplates` di
  `lib/mock-data.ts`).
- **Bug dark mode ditemukan & diperbaiki**: `className="dark"` di `<html>`
  tidak berefek karena Tailwind v4 di setup default masih pakai deteksi
  `prefers-color-scheme`, bukan class strategy — seluruh app diam-diam
  render mode terang (body background putih), bikin teks abu-abu jadi
  hampir tidak kebaca di atas card gelap. Diperbaiki dengan set warna dark
  langsung di `:root` (`app/globals.css`), sesuai SPEC.md Bagian 14.3
  "Dark mode wajib".
- Diverifikasi dengan Playwright headless Chromium sungguhan (bukan cuma
  curl/tsc): 0 console error/pageerror di kelima halaman, di keempat mode,
  build production (`npm run build` + `next start`) dicek langsung,
  termasuk screenshot visual tiap halaman.

**Yang sengaja belum dikerjakan** (di luar scope "lihat prototipe dulu"):
autentikasi login di frontend, koneksi ke backend asli (halaman Dashboard
tadinya fetch API instruments — sekarang full mock, `lib/api.ts` lama
dihapus karena tidak dipakai; akan dibuat ulang saat wiring API asli),
halaman journal/backtest/alerts/settings (tidak diminta di scope prototipe
ini).

## Addendum deployment #2 (2026-09-02): pindah dari Railway ke Render + GitHub Actions

User menyampaikan Railway hanya trial 30 hari/$5, lalu wajib berbayar — minta
opsi tanpa biaya. Disusun ulang jalur deploy backend:

- **`backend/render.yaml`** ditambahkan — Blueprint Render (`plan: free`,
  build dari Dockerfile yang sudah ada, health check `/healthz`, migrasi
  otomatis jalan di `dockerCommand` sebelum `uvicorn` start).
- **Celery worker/beat tidak dipakai di jalur gratis ini** — Render free
  tier tidak menyediakan background worker gratis, dan menjalankan
  Redis+worker 24/7 di tempat lain berarti biaya lagi. Sebagai gantinya:
  - `backend/scripts/run_ingest.py` ditambahkan — entry point yang
    memanggil fungsi task Celery yang sama persis
    (`app.workers.tasks.ingest._sync_instruments` /
    `_ingest_daily_ohlcv`), tanpa logika terduplikasi.
  - `.github/workflows/sync-instruments.yml` dan
    `.github/workflows/ingest-daily-ohlcv.yml` ditambahkan — cron GitHub
    Actions (gratis untuk repo publik) menggantikan jadwal Celery Beat
    persis sesuai SPEC.md Bagian 6.4 (06:00 WIB dan 17:30 WIB hari bursa).
  - Kode Celery (`backend/app/workers/`, `railway.json`) **tidak dihapus**
    — tetap tersedia kalau nanti ada budget untuk worker 24/7 (didoku­
    mentasikan sebagai opsi di `DEPLOYMENT.md` Bagian 6, bersama Fly.io).
- **`DEPLOYMENT.md` ditulis ulang**: Render + GitHub Actions + Supabase
  jadi jalur utama (gratis, tanpa kartu kredit), Railway/Fly.io jadi
  alternatif opsional untuk kalau butuh backend selalu nyala.
- Trade-off yang didokumentasikan ke user: Render free tier tidur setelah
  ±15 menit idle (cold start ~30-50 detik pada request pertama setelah
  itu) — dianggap dapat diterima untuk decision-support tool yang belum
  butuh respons real-time.
- Diuji lokal: `python -m scripts.run_ingest sync_instruments` berhasil
  jalan terhadap Postgres lokal (hasil `{'created': 0, 'updated': 48}`,
  karena instrumen sudah ter-seed dari sesi sebelumnya). Syntax kedua
  workflow YAML divalidasi dengan `yaml.safe_load`. Test suite (27 test)
  tetap hijau setelah perubahan ini.

## Addendum deployment #1 (2026-09-02, setelah Fase 1)

Menindaklanjuti setup deploy user (Vercel untuk frontend, rencana Supabase +
Railway untuk backend):

- **Migrasi `0001_initial_schema.py` diubah**: langkah `create_hypertable`
  TimescaleDB sekarang dibungkus pengecekan `pg_available_extensions` —
  di-skip otomatis kalau extension tidak tersedia di server (mis. Supabase
  managed Postgres tidak menyediakan TimescaleDB). Diverifikasi ulang
  terhadap Postgres 16 lokal tanpa TimescaleDB: migrasi selesai bersih,
  seluruh 9 tabel terbentuk. `ohlcv` tetap fungsional penuh sebagai tabel
  Postgres biasa tanpa hypertable di lingkungan seperti itu.
- **`backend/railway.json`** ditambahkan untuk deploy backend ke Railway
  (build via Dockerfile yang sudah ada, start command menjalankan
  `alembic upgrade head` lalu `uvicorn`).
- **`DEPLOYMENT.md`** ditambahkan: panduan step-by-step menyambungkan
  Vercel (frontend) ↔ Railway (backend + Celery worker/beat) ↔ Supabase
  (database), termasuk env var yang dibutuhkan tiap sisi dan cara seed
  data awal manual.
- Root cause 404 awal di Vercel sudah terkonfirmasi user: Root Directory
  belum diarahkan ke `frontend` — sudah diperbaiki di sisi user, frontend
  sekarang live dan menampilkan fallback "Backend belum aktif" dengan
  benar (perilaku yang memang diharapkan sebelum backend di-deploy).

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
