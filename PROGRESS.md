# Progress

## Addendum wiring data real (2026-09-15): Dashboard & Analysis konek ke backend asli

Setelah aplikasi desktop berhasil di-install & dijalankan user (lihat addendum
di bawah untuk perbaikan bug Gatekeeper), user minta platform dikoneksikan ke
data real IHSG/LQ45 supaya analisis sesuai kondisi pasar sungguhan — sebelum
ini seluruh frontend 100% pakai `lib/mock-data.ts`.

**Keputusan scope** (dikonfirmasi eksplisit ke user karena Signal Engine/Fase
3 belum ada): wiring data real dulu untuk Dashboard & Analysis (chart,
indikator, level S/R, candlestick pattern) — rekomendasi trading (entry
zone/SL/TP/position sizing) dan skor Screener TETAP placeholder jujur
("Signal Engine belum tersedia — Fase 3"), BUKAN diisi angka fabrikasi dari
harga real (itu akan terlihat seperti rekomendasi sungguhan padahal bukan,
melanggar CLAUDE.md soal klaim prediktif). Watchlist & Portfolio juga tetap
mock sepenuhnya — backend belum punya tabel/API untuk keduanya sama sekali
(bukan pilihan, tapi keterbatasan yang ada).

### Apa yang selesai

**Backend:**
1. **Bootstrap otomatis saat database kosong** (`app/services/bootstrap.py`
   baru) — `needs_bootstrap()`/`run_bootstrap_sync()` dipanggil di
   `app/main.py` lifespan (jalur SQLite saja) lewat background thread
   supaya tidak memblokir startup FastAPI (ingest ~48 simbol bisa makan
   waktu beberapa menit). Status (`idle`/`running`/`done`/`error`) disimpan
   in-memory (`BootstrapState`, thread-safe), kegagalan jaringan ditangkap
   dan dicatat sebagai `error` — TIDAK melempar exception yang bisa
   men-crash proses utama.
2. **`GET /api/v1/system/status`** (`app/api/v1/system.py` baru) —
   mengembalikan `{database, instrument_count, bootstrap: {status, detail}}`,
   dipoll frontend untuk menampilkan banner status ("menghubungkan...",
   "sedang sync data awal...", atau pesan error jaringan).
3. **`GET /api/v1/instruments/summary`** — harga terbaru + `change_pct`
   dihitung dari 2 bar OHLCV harian terakhir per instrumen (N+1 query
   sengaja dipakai apa adanya, cuma ~48 instrumen lokal). Route didaftarkan
   SEBELUM `/{symbol}` supaya path "/summary" tidak ketangkap jadi
   `symbol="summary"`.
4. **CORS**: `cors_origins` default ditambah `tauri://localhost` (macOS/
   Linux) & `http://tauri.localhost` (Windows) — origin webview Tauri,
   berbeda dari `http://localhost:3000` yang cuma dipakai `next dev`.
5. Semua fungsi baru (`bootstrap.py`, endpoint `/system/status` &
   `/instruments/summary`) punya unit test — **163 test lolos** (naik dari
   151), termasuk test kegagalan bootstrap yang tidak boleh melempar
   exception.

**Frontend:**
6. **`lib/api.ts`** (baru) — client fetch ke backend lokal, base URL
   di-hardcode `http://127.0.0.1:8756` (port sidecar tetap, lihat
   `desktop_entrypoint.py`), override lewat `NEXT_PUBLIC_API_BASE_URL`
   untuk `next dev` manual. Tipe respons mengikuti schema API asli
   (`InstrumentSummary`, `OhlcvBar`, `IndicatorSnapshot`, dst) — BUKAN tipe
   `Signal` mock, supaya tidak ada field entry/SL/TP palsu yang
   "kebetulan" terisi.
7. **`lib/use-backend-ready.ts`** & **`lib/use-system-status.ts`** (baru) —
   poll `/healthz` sampai sidecar Python siap (mengatasi race condition:
   Tauri render frontend statis instan, sedangkan proses Python butuh
   beberapa detik untuk mulai listen), lalu poll `/system/status` selama
   bootstrap masih `running`.
8. **`components/ui/data-status-banner.tsx`** (baru) — banner status
   dipakai bersama Dashboard & Analysis (menghubungkan.../sync awal
   berjalan/gagal jaringan).
9. **Dashboard** (`dashboard-view.tsx`) — Top Gainer/Loser dari
   `/instruments/summary` real; kartu "IHSG" jadi placeholder (indeks
   komposit di luar cakupan 48 LQ45 yang di-ingest); kartu sinyal diganti
   "Instrumen Terpantau" (hitung real); tabel "Sinyal Terbaru" diganti
   card placeholder Signal Engine. `signal-row-table.tsx` dihapus (jadi
   tidak terpakai). Kartu "Watchlist Aktif" tetap pakai mock (tidak ada
   API watchlist).
10. **Analysis** (`analysis-view.tsx`) — fetch instrumen/OHLCV/indikator/
    level/pattern real per simbol, masing-masing endpoint ditangani
    independen (satu gagal 422 INSUFFICIENT_DATA tidak menggagalkan yang
    lain). `PriceChart` diubah: prop `entryZone`/`stopLoss`/`targets` jadi
    optional (undefined kalau Signal Engine belum tersedia, bukan overlay
    kosong/error). RSI dihitung client-side dari candle real (`computeRSI`,
    fungsi yang sama dipakai mock sebelumnya, sekarang dapat data
    sungguhan). `TradingPlanCard` diganti placeholder jujur. `DetailTabs`
    ditulis ulang total: tab Teknikal menampilkan nilai indikator mentah
    (bukan skor komposit 0-100 yang fabrikasi), tab Level & Pattern
    sekarang REAL (sebelumnya "Pattern" masih placeholder di addendum UI
    prototype), tab Ringkasan/Fundamental/Riwayat tetap "belum tersedia".
    `SymbolSelect` diubah fetch daftar 48 instrumen real (bukan ~8 simbol
    mock) dari `/instruments/summary`.
11. Bug ditemukan & diperbaiki saat verifikasi E2E (lihat bawah): panel
    chart macet permanen di "Memuat data harga…" untuk simbol yang memang
    belum ada OHLCV — endpoint `/ohlcv` mengembalikan `200 []` (bukan
    error) untuk data kosong, jadi butuh flag `ohlcvLoaded` terpisah dari
    "belum ada data" untuk membedakan sedang-loading vs sudah-selesai-tapi-
    kosong.

### Verifikasi

- **Backend**: 163 test lolos (`pytest app/tests`).
- **Frontend**: `npm run build` bersih (lint + typecheck + static export).
- **End-to-end nyata** (bukan cuma unit test): backend dijalankan sungguhan
  (`desktop_entrypoint.py`, SQLite baru) + `frontend/out` diserve statis
  (`serve`, supaya clean-URL routing sama seperti cara Tauri menyajikan
  static export — `python -m http.server` TIDAK merepresentasikan ini
  dengan benar, sempat menghasilkan 404 palsu di test awal), diverifikasi
  Playwright headless Chromium sungguhan ke 6 halaman: `/` sukses fetch
  `/instruments/summary` real (48 instrumen ter-sync), `/analysis` fetch
  instrumen/OHLCV/indikator/level/pattern real dengan graceful degradation
  (`INSUFFICIENT_DATA` 422 karena sandbox ini tidak punya akses internet ke
  Yahoo Finance → 0 bar OHLCV → pesan "Data historis belum cukup", bukan
  crash/blank), Screener/Watchlist/Portfolio tidak berubah (mock, 0 error).
  0 console/page error kecuali 422 yang memang disengaja (log jaringan
  browser normal untuk response non-2xx yang sudah ditangani `try/catch`).
- **Bootstrap lifecycle** diverifikasi manual: `sync_instruments` berhasil
  (48 instrumen, tidak butuh jaringan), `ingest_daily_ohlcv` gagal per-
  simbol karena sandbox tidak ada akses ke Yahoo Finance (`bootstrap.status`
  jadi `error` dengan pesan jelas, TIDAK meng-crash server) — perilaku yang
  benar untuk kondisi tanpa internet; di mesin user dengan internet asli,
  ini akan `status: done` dan mengisi harga sungguhan.

### Ditunda / butuh tindak lanjut

- **Belum diverifikasi dengan data internet sungguhan** — sandbox sesi ini
  tidak punya akses ke Yahoo Finance, jadi alur "bootstrap sukses → harga
  benar-benar terisi di UI" cuma diverifikasi secara struktural (graceful
  degradation saat gagal), bukan hasil akhir dengan angka riil. User perlu
  membuka aplikasi desktop sekali dengan internet aktif untuk memvalidasi
  ini end-to-end.
- **Signal Engine (Fase 3)** — rekomendasi entry/SL/TP, skor Screener,
  gate R:R minimum — belum dibangun, sengaja di luar scope addendum ini
  (lihat "Keputusan scope" di atas). Halaman Analysis/Dashboard sudah
  siap menampilkannya begitu tersedia (placeholder sudah di tempat yang
  tepat).
- **Watchlist & Portfolio backend** — belum ada tabel/API sama sekali
  (Watchlist) atau API CRUD (Portfolio, tabelnya sudah ada dari Fase 1).
  Kedua halaman ini tetap 100% mock.
- **`/instruments/summary` N+1 query** — cukup untuk ~48 instrumen lokal
  desktop single-user, tapi bukan pola yang scale kalau nanti universe
  instrumen bertambah signifikan.

## Addendum desktop app (2026-09-10): pivot ke aplikasi desktop (Tauri), drop hosting

User bertanya apakah logic bisa dibundel jadi aplikasi macOS/desktop supaya
tidak perlu hosting. Setelah dikonfirmasi feasible, user memutuskan dua hal
eksplisit: **full pindah ke desktop, drop versi web** (karena dipakai
sendiri), dan wrapper **Tauri** (bukan Electron, footprint lebih kecil).

**Penting**: sesi ini jalan di sandbox Linux, jadi `.dmg`/`.app` macOS asli
TIDAK dihasilkan langsung di sini — itu butuh toolchain Apple (Xcode/
codesign) yang cuma ada di macOS asli. Yang disiapkan: seluruh source code
+ workflow GitHub Actions yang build otomatis di runner `macos-latest`
(gratis untuk repo publik), atau bisa dijalankan manual oleh user di Mac
sendiri kapan saja (lihat `desktop/src-tauri/binaries/README.md`).

### Apa yang selesai

1. **Portabilitas database (Postgres → SQLite)** — kolom `JSONB`/`ARRAY`
   (khusus Postgres) di `indicator_snapshot.py`, `signal.py`, `alert.py`
   diganti tipe generik SQLAlchemy `JSON` (jalan di kedua dialect).
   `server_default="now()"` (raw SQL Postgres) diganti `func.now()`
   (dialect-aware) di `signal.py`/`user.py`. Jalur hosted (Postgres +
   Alembic) tidak berubah — hanya jadi kompatibel tambahan dengan SQLite.
2. **Config default ke SQLite lokal** (`app/core/paths.py` baru) —
   `get_app_data_dir()` resolve lokasi data app per-OS sesuai konvensi
   (macOS: `~/Library/Application Support/`, Linux: XDG_DATA_HOME, Windows:
   `%APPDATA%`). `DATABASE_URL` di `config.py` sekarang default `None` lalu
   diisi otomatis ke SQLite di folder itu lewat `model_validator` — kalau
   `DATABASE_URL` di-set eksplisit (jalur hosted/Render), tidak berubah.
   `database.py` menambah `init_db_schema()` yang jalan `create_all()` HANYA
   saat SQLite (jalur hosted tetap wajib lewat Alembic).
3. **Scheduler lokal pengganti Celery Beat** (`app/workers/local_scheduler.py`
   baru, pakai `APScheduler`) — job `sync_instruments` (06:00 WIB) dan
   `ingest_daily_ohlcv` (17:30 WIB hari bursa) jalan in-process, tidak butuh
   Redis/worker terpisah. Diaktifkan otomatis di `app/main.py` lifespan
   HANYA saat mode SQLite; jalur hosted tetap pakai GitHub Actions cron
   yang sudah ada (`ingest-daily-ohlcv.yml`/`sync-instruments.yml`).
4. **Refactor pemisahan logic dari Celery** (`app/services/ingest.py` baru)
   — `sync_instruments`/`ingest_daily_ohlcv`/`_upsert_ohlcv` dipindah ke
   modul tanpa dependency Celery sama sekali (termasuk upsert dialect-aware
   SQLite/Postgres). `app/workers/tasks/ingest.py` jadi wrapper tipis yang
   cuma nambah decorator `@celery_app.task`. **Alasan arsitektural**: bukan
   cuma menghindari duplikasi kode, tapi PyInstaller (bundler sidecar
   desktop) melakukan static analysis import — import Celery memicu
   `kombu.utils.imports.symbol_by_name` yang dynamic-lookup modul
   `celery.fixups.django`, tidak kelihatan oleh PyInstaller dan bikin
   binary crash saat runtime. Dengan pemisahan ini, dependency graph
   sidecar desktop tidak pernah menyentuh Celery sama sekali.
5. **Bundle backend Python jadi sidecar binary** (PyInstaller) —
   `backend/desktop_entrypoint.py` (pakai `from app.main import app` +
   `uvicorn.run(app, ...)` dengan objek bukan string, supaya semua import
   bisa dilacak statis oleh PyInstaller), `backend/desktop.spec` (hidden
   imports untuk uvicorn/apscheduler/app + beberapa modul dynamic-import
   seperti `passlib.handlers.argon2`, `email_validator`), dan
   `backend/requirements-desktop.txt` terpisah dari `requirements.txt`
   hosted (tidak mempengaruhi image Docker Render). Diverifikasi end-to-end
   lokal: binary/entrypoint jalan penuh — startup → auto-create schema
   SQLite → scheduler APScheduler start dengan job & timezone benar →
   `/healthz` 200 → shutdown bersih dengan scheduler ikut berhenti.
6. **Frontend jadi static export** — `next.config.ts` ditambah
   `output: "export"` (wajib untuk Tauri, webview-nya cuma load file
   statis, tidak ada runtime Node/SSR). Konsekuensi: route dinamis
   `/analysis/[symbol]` diganti jadi `/analysis?symbol=...` (query param
   via `useSearchParams`), karena static export tidak generate halaman
   dinamis tanpa `generateStaticParams` lengkap semua kemungkinan symbol.
   Semua link internal (dashboard, watchlist, portfolio, screener) ikut
   diupdate. Diverifikasi: `npm run build` sukses, hasil `frontend/out/`
   berisi file `.html` flat (`analysis.html`, dst) sesuai ekspektasi Tauri
   `frontendDist`.
7. **Scaffold shell Tauri v2** (`desktop/`) — `Cargo.toml`/`tauri.conf.json`
   (window 1440x900, bundle target `dmg`+`app`, ikon dibuat manual dengan
   desain candlestick sederhana), `src-tauri/src/lib.rs` mengelola siklus
   hidup sidecar backend: spawn via `tauri-plugin-shell`, alirkan
   stdout/stderr ke konsol untuk debug, dan **kill eksplisit saat app
   exit** (`RunEvent::Exit`) supaya proses backend tidak jadi orphan
   setelah window ditutup. `capabilities/default.json` grant
   `shell:allow-execute` scoped khusus ke sidecar `stockapp-backend`.
8. **GitHub Actions `build-macos.yml`** — jalan di `macos-latest`
   (workflow_dispatch + push ke branch ini yang menyentuh
   `backend|frontend|desktop`): build sidecar PyInstaller → rename sesuai
   target triple Rust (`rustc -Vv`) → build frontend static export →
   `npm run tauri build` → upload `.dmg` sebagai artifact workflow. Ini
   satu-satunya jalur yang benar-benar mengkompilasi & memvalidasi kode
   Rust/Tauri (sandbox Linux sesi ini tidak bisa cross-compile untuk
   macOS, dan `libwebkit2gtk` untuk sanity-check native Linux gagal
   diinstal karena mirror `apt` Ubuntu di sandbox rusak/404 untuk banyak
   dependency transitif — bukan masalah kode, jadi dilewati).

### Verifikasi

- **151 test lolos** (backend, tidak berubah dari sebelumnya — perubahan
  DB/config/scheduler tidak memecah test hosted yang sudah ada).
- Lifecycle sidecar diverifikasi manual dua kali (setelah dua bug packaging
  ditemukan, lihat bawah): jalankan `desktop_entrypoint.py` langsung
  (bukan lewat PyInstaller) DAN lewat binary hasil `pyinstaller
  desktop.spec` — keduanya startup bersih, `/healthz` 200, shutdown bersih.
- Frontend: `npm run build` bersih (lint+typecheck+export), 5 halaman
  ter-generate sebagai static HTML.
- File YAML `build-macos.yml` divalidasi `yaml.safe_load`.
- **`build-macos.yml` sudah jalan sungguhan di `macos-latest` dan SUKSES**
  (run otomatis dari push, selesai ~7 menit) — ini validasi nyata pertama
  bahwa kode Rust/Tauri benar-benar compile (tidak bisa dicek di sandbox
  Linux sesi ini). Artifact `.dmg` berhasil dihasilkan dan diupload
  (~20 MB). Belum dicoba install/jalan di mesin macOS fisik — Gatekeeper
  kemungkinan minta klik-kanan-buka karena `.dmg` unsigned/belum
  di-notarize.

### Keputusan teknis & alasan

- **Jalur hosted (Render/Postgres/Alembic/Celery) tidak dihapus**, meski
  user memilih "drop versi web" untuk pemakaian sendiri — kode dibiarkan
  tetap ada dan tetap lolos test, karena menghapusnya berisiko lebih besar
  daripada manfaatnya (gampang diaktifkan lagi kalau suatu saat butuh
  akses multi-device/multi-user), dan pemisahan sudah bersih lewat flag
  `is_sqlite` tanpa duplikasi logic.
- **SQLite dipilih (bukan Postgres embedded/DuckDB)** — satu file, tanpa
  proses server terpisah, didukung native oleh SQLAlchemy, cukup untuk
  beban single-user desktop app.
- **APScheduler `BackgroundScheduler` in-process** (bukan Celery+Redis
  lokal) — jauh lebih ringan untuk single-user desktop, tidak butuh
  Redis/broker terpisah yang harus di-manage siklus hidupnya oleh Tauri.
- **Wiring frontend ke API asli (menggantikan `lib/mock-data.ts`) SENGAJA
  belum dikerjakan di addendum ini** — di luar scope permintaan user
  ("bisa dibundel jadi desktop app?"), dan sudah didokumentasikan sebagai
  langkah terpisah sejak addendum UI prototype. Prasyarat packaging
  desktop (DB/scheduler/sidecar/Tauri) yang jadi fokus di sini.

### Ditunda / butuh tindak lanjut

- **Bug instalasi nyata di macOS user — SUDAH DIPERBAIKI & DIKONFIRMASI**:
  `.dmg` build pertama (unsigned sama sekali) ditolak Gatekeeper dengan
  pesan **"is damaged and can't be opened"**. Root cause sebenarnya
  **dua lapis**, ditemukan lewat diagnostik langsung di mesin user
  (`codesign -dv --verbose=4` dan `spctl -a -vvv` pada `.app` terinstall):
  1. Build pertama sama sekali tidak bertanda tangan → tidak bisa
     dieksekusi di Apple Silicon sama sekali (AMFI/kernel menolak kode
     tanpa signature apapun, bukan cuma Gatekeeper). **Fix**: ditambahkan
     `"signingIdentity": "-"` di `desktop/src-tauri/tauri.conf.json`
     (bundle.macOS) supaya Tauri ad-hoc-sign `.app`, plus
     `codesign --force -s - --timestamp -v` eksplisit pada binary sidecar
     sebelum di-bundle (`build-macos.yml`). Dikonfirmasi lewat
     `codesign -dv` di mesin user: `Signature=adhoc`, valid, tanpa error.
  2. **Setelah** ad-hoc signature valid, `spctl -a -vvv` tetap melaporkan
     `rejected` — dikonfirmasi ini SELALU terjadi untuk signature ad-hoc
     (bukan Apple Developer ID resmi) terhadap file yang membawa xattr
     `com.apple.quarantine` (ditambahkan otomatis oleh Chrome saat
     download, dikonfirmasi lewat `xattr -l` — `com.apple.quarantine:
     0381;...;Chrome;...`). Percobaan `xattr -cr` sebelumnya oleh user
     ternyata tidak benar-benar menghapus flag ini (kemungkinan sempat
     dijalankan saat file masih di dalam `.dmg` yang read-only, sebelum
     di-drag ke Applications, jadi copy baru di Applications tetap bawa
     quarantine). **Fix final**: `sudo xattr -dr com.apple.quarantine
     "/Applications/Stock Analysis Platform.app"` (bukan `xattr -cr` biasa
     — perlu `sudo` dan target spesifik `com.apple.quarantine`, bukan
     bersih semua attribute). Setelah ini, app terbuka normal.
  **Kesimpulan untuk update `.dmg` berikutnya**: karena ad-hoc signing
  tidak lolos assessment Gatekeeper (`spctl`) sama sekali (beda dari
  Developer ID bersertifikat + notarized, yang cuma dapat warning dengan
  tombol "Open Anyway"), user WAJIB menjalankan
  `sudo xattr -dr com.apple.quarantine "<path .app>"` setiap kali
  install ulang dari download baru — bukan cuma klik-kanan-buka. Ini
  didokumentasikan di `desktop/src-tauri/binaries/README.md` sebagai
  langkah wajib pasca-install (lihat commit berikutnya).
- **Auto-update aplikasi desktop belum ada** — Tauri punya plugin updater
  bawaan, belum diintegrasikan; untuk saat ini update = download `.dmg`
  baru dari artifact GitHub Actions tiap ada perubahan.
- **Wiring frontend ke backend asli** (lihat keputusan teknis di atas)
  masih pending, terpisah dari packaging desktop ini.
- **Sanity-check compile Rust/Tauri secara native di Linux TIDAK berhasil
  dilakukan** di sandbox ini (`libwebkit2gtk-4.1-dev` dan dependency
  transitifnya gagal `apt-get install` karena mirror Ubuntu 404 untuk
  banyak paket tidak terkait) — bukan blocker karena target build
  sesungguhnya adalah `build-macos.yml`, tapi berarti validasi pertama
  kode Rust ini baru terjadi saat workflow itu dijalankan.

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
