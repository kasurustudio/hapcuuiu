# SPEC — Web Application: Multi-Strategy Stock Analysis Platform

> Dokumen ini adalah spesifikasi teknis lengkap untuk dibaca oleh Claude Code.
> Taruh file ini di root repository dengan nama `SPEC.md`, lalu jalankan
> Claude Code dan minta implementasi per-fase (lihat Bagian 17).

**Versi:** 1.0
**Tanggal:** 2026-09-02
**Status:** Draft untuk implementasi

---

## 0. Disclaimer Wajib (harus diimplementasikan di dalam produk)

Aplikasi ini adalah **decision support tool**, bukan penasihat investasi. Setiap
output sinyal, harga beli, dan harga jual adalah hasil kalkulasi rule-based
terhadap data historis, bukan jaminan hasil di masa depan.

Requirement produk:
- Banner disclaimer permanen di footer setiap halaman.
- Modal disclaimer yang harus di-acknowledge saat pertama kali login, disimpan
  di `users.disclaimer_accepted_at`.
- Setiap kartu sinyal menampilkan label kecil: *"Bukan rekomendasi investasi.
  Hasil kalkulasi teknikal otomatis."*
- Tidak boleh ada wording yang menjanjikan profit ("pasti naik", "sure win", dsb).

---

## 1. Ringkasan Produk

Web application untuk analisis saham yang mendukung **empat gaya trading**
dalam satu platform, dengan output berupa rekomendasi konkret:
level harga beli (entry), stop loss, target jual bertingkat (TP1/TP2/TP3),
ukuran posisi, dan rasio risk/reward.

### 1.1 Empat Mode

| Mode | Holding Period | Timeframe Utama | Fokus Analisis |
|---|---|---|---|
| **Scalping** | detik–menit | 1m, 5m | Order flow, VWAP, bid-ask, momentum mikro |
| **Day Trading** | intraday, tutup sebelum closing | 5m, 15m, 1H | Breakout, VWAP, volume profile, gap |
| **Swing Trading** | 2 hari–8 minggu | 1H, 4H, Daily | Trend following, S/R, chart pattern, Fibonacci |
| **Investing** | > 6 bulan | Daily, Weekly, Monthly | Fundamental + valuasi + trend jangka panjang |

Mode dipilih user di UI dan **mengubah seluruh parameter engine**: indikator
yang dipakai, bobot scoring, lebar stop loss, target profit, dan minimum
liquidity filter.

### 1.2 Market yang Didukung

- **Fase 1 (MVP):** IDX (Bursa Efek Indonesia) — satuan lot = 100 lembar,
  tick size berjenjang, jam perdagangan sesi I & II, auto-rejection (ARA/ARB).
- **Fase 2:** US market (NASDAQ, NYSE) — fractional share, extended hours.
- **Fase 3:** Crypto (opsional, 24/7).

Data layer harus **abstract** sejak awal (`MarketAdapter` interface) supaya
penambahan market tidak mengubah engine analisis.

---

## 2. Persona & User Stories

### Persona A — Scalper/Day Trader
> "Saya butuh tahu dalam 3 detik: saham ini layak masuk sekarang atau tidak,
> di harga berapa, stop di mana, dan keluar di mana."

- US-01: Sebagai day trader, saya ingin melihat watchlist real-time dengan
  sinyal aktif supaya bisa eksekusi cepat.
- US-02: Sebagai scalper, saya ingin alert saat harga menyentuh entry zone.
- US-03: Sebagai day trader, saya ingin melihat VWAP dan volume profile pada chart.

### Persona B — Swing Trader
- US-04: Sebagai swing trader, saya ingin menjalankan screener untuk mencari
  saham yang baru breakout dengan volume konfirmasi.
- US-05: Sebagai swing trader, saya ingin melihat level Fibonacci dan
  support/resistance otomatis dengan skor kekuatan.
- US-06: Sebagai swing trader, saya ingin backtest strategi saya di 3 tahun terakhir.

### Persona C — Investor
- US-07: Sebagai investor, saya ingin melihat skor fundamental (PER, PBV, ROE,
  DER, growth) dibanding rata-rata sektor.
- US-08: Sebagai investor, saya ingin estimasi fair value dan margin of safety.
- US-09: Sebagai investor, saya ingin alert saat harga masuk zona diskon.

### Lintas Persona
- US-10: Sebagai user, saya ingin mencatat transaksi dan melihat performa portofolio.
- US-11: Sebagai user, saya ingin melihat jurnal trading dengan win rate dan
  average R multiple.

---

## 3. Ruang Lingkup

### 3.1 In Scope (MVP — Fase 1)
- Autentikasi (email + password, JWT).
- Ingest data OHLCV harian dan intraday untuk saham IDX.
- Perhitungan ~25 indikator teknikal.
- Deteksi otomatis support/resistance, trendline, dan chart pattern dasar.
- Signal engine dengan output entry/SL/TP per mode.
- Chart interaktif dengan overlay indikator dan level rekomendasi.
- Screener dengan filter tersimpan.
- Watchlist + alert (in-app dan email).
- Portfolio tracker manual + jurnal trading.

### 3.2 Out of Scope (MVP)
- Eksekusi order langsung ke broker (integrasi API broker).
- Social/copy trading.
- Mobile native app (web responsive dulu).
- Machine learning / prediksi harga berbasis model.

### 3.3 Non-Goals (permanen)
- Tidak membuat klaim prediksi harga masa depan.
- Tidak memberikan personalized investment advice yang diatur regulator.

---

## 4. Arsitektur & Tech Stack

### 4.1 Stack yang Direkomendasikan

```
Frontend   : Next.js 15 (App Router) + TypeScript + TailwindCSS + shadcn/ui
Charting   : lightweight-charts (TradingView) untuk price chart
             Recharts untuk chart statistik/backtest
State      : TanStack Query (server state) + Zustand (UI state)
Backend    : FastAPI (Python 3.12) — dipilih karena ekosistem analisis numerik
Compute    : pandas, numpy, pandas-ta (atau implementasi manual, lihat 7.1)
Database   : PostgreSQL 16 + TimescaleDB extension (hypertable untuk OHLCV)
Cache      : Redis (quote real-time, hasil screener, rate limit)
Queue      : Celery + Redis (job ingest, recompute indikator, backtest)
Realtime   : WebSocket (FastAPI) untuk push quote & alert
Auth       : JWT access + refresh token, argon2 password hashing
Deploy     : Docker Compose (dev), containerized (prod)
Testing    : pytest (backend), vitest + playwright (frontend)
```

### 4.2 Struktur Repository

```
/
├── SPEC.md                       # dokumen ini
├── CLAUDE.md                     # instruksi khusus untuk Claude Code
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/                 # config, security, deps
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── api/v1/               # routers
│   │   ├── services/
│   │   │   ├── market_data/      # adapters per-market
│   │   │   ├── indicators/       # perhitungan indikator
│   │   │   ├── levels/           # S/R, fibonacci, pivot
│   │   │   ├── patterns/         # candlestick & chart pattern
│   │   │   ├── signals/          # signal engine per mode
│   │   │   ├── risk/             # position sizing, R:R
│   │   │   ├── screener/
│   │   │   ├── backtest/
│   │   │   └── fundamental/
│   │   ├── workers/              # celery tasks
│   │   └── tests/
│   └── alembic/
└── frontend/
    ├── app/                      # routes
    ├── components/
    ├── lib/
    └── hooks/
```

### 4.3 Prinsip Arsitektur (wajib dipatuhi)

1. **Pure functions untuk semua indikator.** Input `pd.DataFrame` OHLCV →
   output Series/DataFrame. Tidak ada I/O di dalam fungsi indikator. Ini
   membuat unit test dan backtest deterministik.
2. **Config-driven, bukan hard-coded.** Semua parameter mode ada di file
   konfigurasi (lihat Bagian 9), bukan tersebar di kode.
3. **Signal engine tidak boleh tahu asal data.** Terima DataFrame + config,
   keluarkan objek `Signal`.
4. **Semua timestamp disimpan UTC** di database, dikonversi ke `Asia/Jakarta`
   hanya di layer presentasi.
5. **Harga disimpan sebagai `NUMERIC(18,4)`**, jangan pernah float, untuk
   menghindari error pembulatan pada kalkulasi P/L.

---

## 5. Data Model

### 5.1 Tabel Inti

```sql
-- Master instrumen
CREATE TABLE instruments (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,      -- 'BBCA'
    exchange        VARCHAR(10) NOT NULL,      -- 'IDX'
    name            VARCHAR(255) NOT NULL,
    sector          VARCHAR(100),
    sub_sector      VARCHAR(100),
    board           VARCHAR(20),               -- Utama/Pengembangan/Ekonomi Baru
    lot_size        INTEGER NOT NULL DEFAULT 100,
    is_active       BOOLEAN DEFAULT TRUE,
    listed_at       DATE,
    UNIQUE (symbol, exchange)
);

-- OHLCV — hypertable TimescaleDB, partisi per bulan
CREATE TABLE ohlcv (
    instrument_id   BIGINT NOT NULL REFERENCES instruments(id),
    timeframe       VARCHAR(5) NOT NULL,       -- 1m,5m,15m,1h,4h,1d,1w
    ts              TIMESTAMPTZ NOT NULL,
    open            NUMERIC(18,4) NOT NULL,
    high            NUMERIC(18,4) NOT NULL,
    low             NUMERIC(18,4) NOT NULL,
    close           NUMERIC(18,4) NOT NULL,
    volume          BIGINT NOT NULL,
    value           NUMERIC(20,2),             -- turnover (Rp)
    frequency       INTEGER,                   -- jumlah transaksi
    PRIMARY KEY (instrument_id, timeframe, ts)
);
SELECT create_hypertable('ohlcv','ts', chunk_time_interval => INTERVAL '1 month');

-- Snapshot indikator (cache hasil perhitungan)
CREATE TABLE indicator_snapshots (
    instrument_id   BIGINT NOT NULL,
    timeframe       VARCHAR(5) NOT NULL,
    ts              TIMESTAMPTZ NOT NULL,
    payload         JSONB NOT NULL,            -- {rsi14: 58.2, ema20: 9250, ...}
    PRIMARY KEY (instrument_id, timeframe, ts)
);

-- Sinyal yang dihasilkan engine
CREATE TABLE signals (
    id                  BIGSERIAL PRIMARY KEY,
    instrument_id       BIGINT NOT NULL REFERENCES instruments(id),
    mode                VARCHAR(20) NOT NULL,  -- scalping|day|swing|investing
    direction           VARCHAR(10) NOT NULL,  -- long|short|neutral
    action              VARCHAR(20) NOT NULL,  -- strong_buy|buy|hold|reduce|sell
    score               NUMERIC(5,2) NOT NULL, -- 0..100
    confidence          VARCHAR(10) NOT NULL,  -- low|medium|high
    reference_price     NUMERIC(18,4) NOT NULL,
    entry_low           NUMERIC(18,4),
    entry_high          NUMERIC(18,4),
    entry_trigger       NUMERIC(18,4),
    stop_loss           NUMERIC(18,4),
    tp1                 NUMERIC(18,4),
    tp2                 NUMERIC(18,4),
    tp3                 NUMERIC(18,4),
    risk_reward         NUMERIC(6,2),
    atr_value           NUMERIC(18,4),
    valid_until         TIMESTAMPTZ,
    rationale           JSONB NOT NULL,        -- lihat 8.6
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    invalidated_at      TIMESTAMPTZ
);
CREATE INDEX ON signals (instrument_id, mode, generated_at DESC);

-- Support / Resistance terdeteksi
CREATE TABLE price_levels (
    id              BIGSERIAL PRIMARY KEY,
    instrument_id   BIGINT NOT NULL,
    timeframe       VARCHAR(5) NOT NULL,
    level_type      VARCHAR(20) NOT NULL,  -- support|resistance|pivot|fib|vwap
    price           NUMERIC(18,4) NOT NULL,
    strength        NUMERIC(5,2) NOT NULL, -- 0..100
    touch_count     INTEGER DEFAULT 0,
    source          VARCHAR(30),           -- swing|volume_profile|fib_0.618|...
    first_seen_at   TIMESTAMPTZ,
    last_tested_at  TIMESTAMPTZ,
    is_active       BOOLEAN DEFAULT TRUE
);

-- Data fundamental (untuk mode investing)
CREATE TABLE fundamentals (
    instrument_id   BIGINT NOT NULL,
    period          DATE NOT NULL,         -- akhir kuartal
    period_type     VARCHAR(10),           -- quarterly|annual|ttm
    revenue         NUMERIC(20,2),
    net_income      NUMERIC(20,2),
    total_equity    NUMERIC(20,2),
    total_assets    NUMERIC(20,2),
    total_debt      NUMERIC(20,2),
    operating_cf    NUMERIC(20,2),
    free_cash_flow  NUMERIC(20,2),
    eps             NUMERIC(18,4),
    bvps            NUMERIC(18,4),
    dps             NUMERIC(18,4),
    shares_out      BIGINT,
    PRIMARY KEY (instrument_id, period, period_type)
);

-- Portfolio & jurnal
CREATE TABLE positions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    instrument_id   BIGINT NOT NULL,
    mode            VARCHAR(20),
    side            VARCHAR(10) NOT NULL,
    qty             BIGINT NOT NULL,
    avg_entry       NUMERIC(18,4) NOT NULL,
    stop_loss       NUMERIC(18,4),
    take_profit     NUMERIC(18,4),
    opened_at       TIMESTAMPTZ NOT NULL,
    closed_at       TIMESTAMPTZ,
    exit_price      NUMERIC(18,4),
    realized_pnl    NUMERIC(20,2),
    fees            NUMERIC(18,4) DEFAULT 0,
    signal_id       BIGINT REFERENCES signals(id),
    notes           TEXT,
    emotion_tag     VARCHAR(30)            -- untuk jurnal: disiplin|fomo|revenge|...
);

CREATE TABLE alerts (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    instrument_id   BIGINT NOT NULL,
    alert_type      VARCHAR(30) NOT NULL,  -- price_cross|entry_zone|sl_hit|signal_new
    condition       JSONB NOT NULL,
    channels        VARCHAR(50)[],         -- {in_app,email}
    is_active       BOOLEAN DEFAULT TRUE,
    triggered_at    TIMESTAMPTZ
);
```

---

## 6. Sumber Data

### 6.1 Interface Adapter

```python
class MarketAdapter(Protocol):
    def list_instruments(self) -> list[InstrumentDTO]: ...
    def fetch_ohlcv(self, symbol: str, timeframe: str,
                    start: datetime, end: datetime) -> pd.DataFrame: ...
    def fetch_quote(self, symbols: list[str]) -> list[QuoteDTO]: ...
    def fetch_fundamentals(self, symbol: str) -> list[FundamentalDTO]: ...
    def market_calendar(self) -> MarketCalendar: ...
```

### 6.2 Kandidat Provider

| Market | Provider | Catatan |
|---|---|---|
| IDX | `yfinance` (suffix `.JK`) | Gratis, cukup untuk daily; intraday terbatas |
| IDX | Data vendor lokal berbayar | Untuk intraday 1m dan order book |
| IDX | Scraping IDX/IDNFinancials | Untuk laporan keuangan; hormati ToS & robots.txt |
| US | `yfinance`, Alpha Vantage, Polygon.io | Polygon untuk intraday berkualitas |

**Requirement:** provider di-set via environment variable. Sistem harus tetap
berfungsi dengan provider gratis saja (mode degraded: hanya daily/swing/investing,
scalping & day trading dinonaktifkan dengan pesan jelas ke user).

### 6.3 Aturan Data Quality

Sebelum data masuk ke engine, wajib lewat validator:
- Buang bar dengan `volume = 0` pada jam perdagangan aktif (suspend).
- Deteksi dan tandai stock split / corporate action: jika `|close[t]/close[t-1] - 1| > 0.35`
  dan bukan hari ARA/ARB → flag untuk review, jangan langsung dipakai.
- Sesuaikan harga historis untuk dividen dan split (`adjusted_close`).
- Minimal 200 bar untuk mode swing/investing, 100 bar untuk day, 300 bar untuk
  scalping. Kurang dari itu → `insufficient_data`, jangan keluarkan sinyal.
- Nilai `NaN` di tengah series → forward fill maksimal 2 bar, lebih dari itu tolak.

### 6.4 Jadwal Ingest (Celery Beat)

| Job | Jadwal (WIB) | Deskripsi |
|---|---|---|
| `sync_instruments` | 06:00 harian | Refresh daftar emiten |
| `ingest_daily_ohlcv` | 17:30 hari bursa | Tarik data EOD |
| `ingest_intraday` | tiap 1 menit saat market open | Bar 1m & 5m |
| `compute_indicators_daily` | 17:45 hari bursa | Recompute + snapshot |
| `generate_signals_swing` | 18:00 hari bursa | Sinyal swing & investing |
| `generate_signals_intraday` | tiap 5 menit saat open | Sinyal day & scalping |
| `detect_levels` | 18:15 hari bursa | Refresh S/R |
| `evaluate_alerts` | tiap 30 detik saat open | Cek kondisi alert |
| `sync_fundamentals` | mingguan | Laporan keuangan baru |

---

## 7. Modul Indikator Teknikal

### 7.1 Daftar Indikator Wajib

Implementasikan sebagai pure function di `services/indicators/`. Boleh memakai
`pandas-ta`, **tetapi** setiap indikator harus punya unit test dengan expected
value yang dihitung manual, agar tidak bergantung buta pada library.

**Trend**
- SMA (5, 10, 20, 50, 100, 200)
- EMA (8, 13, 21, 50, 200)
- MACD (12, 26, 9) — line, signal, histogram
- ADX + DI+ / DI− (14)
- Ichimoku Cloud (9, 26, 52)
- Parabolic SAR (0.02, 0.2)
- SuperTrend (10, 3.0)

**Momentum**
- RSI (14) — plus deteksi divergence bullish/bearish
- Stochastic (14, 3, 3)
- Stochastic RSI (14, 14, 3, 3)
- CCI (20)
- Williams %R (14)
- ROC (12)
- MFI (14) — momentum berbobot volume

**Volatilitas**
- ATR (14) dan ATR% (`ATR / close × 100`)
- Bollinger Bands (20, 2) + Bandwidth + %B
- Keltner Channel (20, 2×ATR)
- Donchian Channel (20)
- Historical Volatility (annualized, 20d)

**Volume**
- Volume MA (20)
- Relative Volume: `volume / SMA(volume, 20)`
- OBV (On Balance Volume)
- VWAP (harian, reset tiap sesi) — **kritikal untuk day trading & scalping**
- Anchored VWAP (dari swing point yang dipilih user)
- Accumulation/Distribution Line
- Volume Profile (POC, VAH, VAL) — bucket 50 level harga

**Struktur Harga**
- Pivot Points: Classic, Fibonacci, Camarilla (harian & mingguan)
- Fibonacci retracement (0.236, 0.382, 0.5, 0.618, 0.786) dan
  extension (1.272, 1.618, 2.0) dari swing terakhir
- Swing High/Low detection (fractal, lookback 5 bar kiri-kanan)

### 7.2 Deteksi Support & Resistance

Algoritma yang harus diimplementasikan (`services/levels/detector.py`):

```
1. Cari semua swing high/low dengan fractal (n=5) pada 250 bar terakhir.
2. Cluster level yang berdekatan dengan toleransi = 0.5 × ATR(14).
   Gunakan agglomerative clustering sederhana atau bucketing.
3. Untuk setiap cluster hitung skor kekuatan (0–100):
     strength = w1*normalize(touch_count)        # w1 = 0.30
              + w2*normalize(total_volume_at_level)  # w2 = 0.25
              + w3*recency_decay(last_tested)     # w3 = 0.20
              + w4*normalize(rejection_wick_size) # w4 = 0.15
              + w5*timeframe_weight               # w5 = 0.10
   recency_decay = exp(-days_since_test / 60)
4. Tambahkan level dari sumber lain: POC volume profile, pivot harian/mingguan,
   round number psikologis (kelipatan 50/100/500 tergantung harga),
   EMA50/EMA200 (dynamic S/R), high/low 52 minggu.
5. Simpan hanya level dengan strength >= 40. Maksimal 8 support & 8 resistance.
6. Klasifikasi: level di bawah harga = support, di atas = resistance.
   Level yang ditembus berubah peran (support jadi resistance dan sebaliknya) —
   tandai dengan flag `role_flipped`.
```

### 7.3 Pattern Recognition

**Candlestick (minimal):** Hammer, Inverted Hammer, Shooting Star, Hanging Man,
Bullish/Bearish Engulfing, Morning/Evening Star, Doji, Three White Soldiers,
Three Black Crows, Piercing Line, Dark Cloud Cover, Marubozu.

Setiap pattern mengembalikan `{name, direction, bar_index, reliability_score}`.
**Penting:** pattern hanya valid jika muncul di konteks yang benar — bullish
reversal pattern hanya dihitung jika muncul dekat support atau setelah downtrend
minimal 5 bar. Implementasikan filter konteks ini, jangan hanya deteksi bentuk.

**Chart pattern (Fase 2):** Double Top/Bottom, Head & Shoulders (+ inverse),
Ascending/Descending/Symmetrical Triangle, Bull/Bear Flag, Cup & Handle,
Falling/Rising Wedge. Output menyertakan `breakout_level` dan
`measured_target` (proyeksi tinggi pola).

---

## 8. Signal Engine — Inti Aplikasi

Ini bagian paling penting. Output harus konkret: **di harga berapa beli, di
harga berapa jual, di harga berapa cut loss.**

### 8.1 Alur Pipeline

```
OHLCV → validasi → indikator → deteksi level → deteksi pattern
      → scoring per-kategori → composite score → keputusan aksi
      → kalkulasi entry/SL/TP → position sizing → objek Signal
```

### 8.2 Composite Score (0–100)

Skor dihitung dari 6 kategori. **Bobot berbeda per mode** (lihat Bagian 9).

| Kategori | Isi | Rentang |
|---|---|---|
| `trend` | Posisi harga vs EMA, susunan MA, ADX, SuperTrend, Ichimoku | 0–100 |
| `momentum` | RSI, MACD histogram, Stochastic, ROC, divergence | 0–100 |
| `volume` | Relative volume, OBV slope, MFI, akumulasi/distribusi | 0–100 |
| `volatility` | ATR%, Bollinger bandwidth, squeeze detection | 0–100 |
| `structure` | Jarak ke support/resistance, posisi dalam range, pattern | 0–100 |
| `fundamental` | Skor valuasi & kualitas (hanya mode investing) | 0–100 |

```
composite = Σ (category_score × weight) / Σ weight
```

**Contoh perhitungan sub-skor trend:**
```
trend_score = 0
if close > ema20:      trend_score += 20
if ema20 > ema50:      trend_score += 20
if ema50 > ema200:     trend_score += 20
if adx > 25:           trend_score += 20
elif adx > 20:         trend_score += 10
if supertrend == "up": trend_score += 20
```
Setiap sub-skor harus terdokumentasi dan dapat ditelusuri (masuk ke `rationale`).

### 8.3 Pemetaan Skor ke Aksi

| Composite Score | Aksi | Confidence |
|---|---|---|
| ≥ 80 | `strong_buy` | high |
| 65–79 | `buy` | medium–high |
| 45–64 | `hold` / `watch` | medium |
| 30–44 | `reduce` | medium |
| < 30 | `sell` / `avoid` | high |

**Gate wajib (hard filter).** Jika salah satu tidak terpenuhi, aksi dipaksa
menjadi `hold` apa pun skornya:
- Likuiditas: rata-rata nilai transaksi 20 hari ≥ threshold per mode.
- Data cukup (lihat 6.3).
- Bukan saham dalam status suspend / UMA / notasi khusus.
- Untuk long: harga tidak sedang ARA (tidak bisa dieksekusi wajar).
- Risk/Reward hasil kalkulasi ≥ minimum per mode. **Jika R:R di bawah minimum,
  sinyal tidak dikeluarkan** — ini mencegah rekomendasi entry buruk.

### 8.4 Kalkulasi Entry Price

Entry bukan satu angka, tapi **zona** + **trigger konfirmasi**.

```python
def calculate_entry(df, levels, config) -> EntryPlan:
    close = df['close'].iloc[-1]
    atr   = df['atr14'].iloc[-1]

    # 1. Kandidat entry dari berbagai sumber
    candidates = []
    nearest_support = find_nearest_support(levels, close)
    if nearest_support:
        candidates.append((nearest_support.price, nearest_support.strength))

    for ma in ['ema20', 'ema50']:                 # dynamic support
        v = df[ma].iloc[-1]
        if v < close and (close - v) / close < config.max_entry_distance_pct:
            candidates.append((v, 60))

    for fib in [0.382, 0.5, 0.618]:               # retracement zone
        p = fib_retracement(df, fib)
        if p < close:
            candidates.append((p, 55 + fib * 20))

    if config.mode in ('day', 'scalping'):        # VWAP sebagai magnet
        candidates.append((df['vwap'].iloc[-1], 70))

    # 2. Konfluensi: level yang berdekatan saling menguatkan
    zone = cluster_and_pick_best(candidates, tolerance=0.5 * atr)

    entry_low  = zone.price - 0.25 * atr
    entry_high = zone.price + 0.25 * atr

    # 3. Trigger: harga beli baru sah jika ada konfirmasi
    entry_trigger = max(entry_high, df['high'].iloc[-1] + config.tick_size)

    return EntryPlan(entry_low, entry_high, entry_trigger, zone.sources)
```

**Dua metode entry yang harus didukung, user bisa pilih:**
- **Buy on Weakness (BoW):** pasang limit order di dalam zona `entry_low..entry_high`.
  Cocok untuk swing & investing. Risiko: harga tidak turun ke zona.
- **Buy on Breakout (BoB):** beli saat harga menembus `entry_trigger` disertai
  volume ≥ 1.5× rata-rata. Cocok untuk day trading & momentum. Risiko: false breakout.

Semua harga output **wajib dibulatkan ke tick size bursa** (lihat 8.8).

### 8.5 Kalkulasi Stop Loss & Take Profit

**Stop Loss** — ambil yang paling ketat dari tiga metode:

```python
def calculate_stop_loss(df, levels, entry, config) -> Decimal:
    atr = df['atr14'].iloc[-1]

    # Metode 1: struktur — di bawah swing low terakhir
    swing_low = last_swing_low(df, lookback=config.swing_lookback)
    sl_structure = swing_low - 0.5 * atr

    # Metode 2: volatilitas — kelipatan ATR
    sl_atr = entry - config.atr_multiplier_sl * atr

    # Metode 3: batas risiko maksimum yang diizinkan mode
    sl_maxrisk = entry * (1 - config.max_risk_pct)

    sl = max(sl_structure, sl_atr, sl_maxrisk)   # paling dekat ke entry
    return round_to_tick(sl, direction='down')
```

**Take Profit** — tiga tingkat, berbasis R multiple **dan** divalidasi terhadap
resistance nyata:

```python
def calculate_take_profit(entry, sl, levels, df, config) -> list[Decimal]:
    R = entry - sl                                  # 1R dalam rupiah
    resistances = sorted([l for l in levels
                          if l.type == 'resistance' and l.price > entry],
                         key=lambda l: l.price)

    tp1 = entry + config.tp1_r * R                  # default 1.0R
    tp2 = entry + config.tp2_r * R                  # default 2.0R
    tp3 = entry + config.tp3_r * R                  # default 3.0R

    # Snap ke resistance terdekat jika berjarak < 0.5 ATR
    # (jual sedikit sebelum resistance kuat, jangan menunggu ditembus)
    atr = df['atr14'].iloc[-1]
    tps = []
    for tp in (tp1, tp2, tp3):
        near = nearest(resistances, tp)
        if near and abs(near.price - tp) < 0.5 * atr and near.strength > 60:
            tp = near.price - config.tick_size    # sedikit di bawah resistance
        tps.append(round_to_tick(tp, direction='down'))

    # Tambahan untuk swing: fibonacci extension 1.618 sebagai TP3 alternatif
    if config.mode == 'swing':
        fib_ext = fib_extension(df, 1.618)
        if fib_ext > tps[1]:
            tps[2] = round_to_tick(min(tps[2], fib_ext), 'down')

    return tps
```

**Skema keluar bertingkat (default, bisa diubah user):**
| Level | Porsi dijual | Aksi lanjutan |
|---|---|---|
| TP1 (1R) | 40% | Geser SL ke breakeven (entry) |
| TP2 (2R) | 30% | Aktifkan trailing stop |
| TP3 (3R) | 30% | Keluar penuh, atau trailing sampai kena |

**Trailing stop** memakai Chandelier Exit:
`trail = highest_high(22) - 3 × ATR(22)`. Untuk day trading gunakan
`highest_high(10) - 2 × ATR(10)`.

### 8.6 Position Sizing

```python
def calculate_position_size(equity, entry, stop_loss, config, lot_size=100):
    risk_amount   = equity * config.risk_per_trade_pct     # mis. 1% dari modal
    risk_per_share = entry - stop_loss
    if risk_per_share <= 0:
        raise InvalidSignal("stop loss harus di bawah entry untuk posisi long")

    raw_shares = risk_amount / risk_per_share
    lots       = floor(raw_shares / lot_size)              # IDX: 1 lot = 100 lembar

    # Batas eksposur: satu posisi maksimal N% dari modal
    max_lots_by_exposure = floor((equity * config.max_position_pct)
                                 / (entry * lot_size))
    lots = min(lots, max_lots_by_exposure)

    # Batas likuiditas: jangan ambil > 2% dari rata-rata volume harian
    lots = min(lots, floor(avg_daily_volume * 0.02 / lot_size))

    return PositionSize(
        lots=max(lots, 0),
        shares=lots * lot_size,
        capital_required=lots * lot_size * entry,
        actual_risk=lots * lot_size * risk_per_share,
        risk_pct_of_equity=(lots * lot_size * risk_per_share) / equity
    )
```

### 8.7 Struktur Output Signal (JSON)

Ini kontrak API yang dikonsumsi frontend. Bentuknya harus persis seperti ini:

```json
{
  "symbol": "BBCA",
  "name": "Bank Central Asia Tbk",
  "mode": "swing",
  "generated_at": "2026-09-02T11:00:00+07:00",
  "valid_until": "2026-09-09T11:00:00+07:00",
  "reference_price": 9250,
  "action": "buy",
  "direction": "long",
  "score": 74.5,
  "confidence": "medium",
  "entry": {
    "method": "buy_on_weakness",
    "zone_low": 9100,
    "zone_high": 9200,
    "trigger_breakout": 9350,
    "sources": ["support_9150_strength_78", "ema20_9180", "fib_0.618_9120"]
  },
  "stop_loss": {
    "price": 8900,
    "distance_pct": 3.26,
    "method": "structure",
    "reason": "0.5 ATR di bawah swing low 8975"
  },
  "targets": [
    {"level": "TP1", "price": 9550, "r_multiple": 1.0, "exit_pct": 40,
     "note": "Geser SL ke breakeven setelah tercapai"},
    {"level": "TP2", "price": 9850, "r_multiple": 2.0, "exit_pct": 30,
     "note": "Aktifkan trailing stop Chandelier"},
    {"level": "TP3", "price": 10150, "r_multiple": 3.0, "exit_pct": 30,
     "note": "Dekat resistance kuat 10200 (strength 82)"}
  ],
  "risk_reward": 2.15,
  "position_sizing": {
    "equity_input": 100000000,
    "risk_per_trade_pct": 1.0,
    "lots": 32,
    "shares": 3200,
    "capital_required": 29600000,
    "actual_risk": 800000
  },
  "scores_breakdown": {
    "trend": 80, "momentum": 68, "volume": 72,
    "volatility": 60, "structure": 78, "fundamental": null
  },
  "rationale": {
    "bullish": [
      "Harga bertahan di atas EMA20 dan EMA50 selama 12 bar terakhir",
      "MACD histogram berbalik positif sejak 3 bar lalu",
      "Volume 1.8x rata-rata 20 hari pada bar terakhir",
      "Bullish engulfing terbentuk tepat di support 9150"
    ],
    "bearish": [
      "RSI 68 mendekati area overbought",
      "Resistance kuat di 10200 membatasi ruang naik"
    ],
    "invalidation": "Sinyal batal jika close harian di bawah 8900 atau volume mengering di bawah 0.5x rata-rata selama 3 hari"
  },
  "levels": {
    "supports":   [{"price": 9150, "strength": 78}, {"price": 8900, "strength": 65}],
    "resistances":[{"price": 9600, "strength": 55}, {"price": 10200, "strength": 82}]
  },
  "disclaimer": "Hasil kalkulasi teknikal otomatis. Bukan rekomendasi investasi."
}
```

### 8.8 Aturan Tick Size IDX (wajib)

Semua harga output harus valid sesuai fraksi harga bursa:

| Rentang Harga (Rp) | Tick Size |
|---|---|
| < 200 | 1 |
| 200 – 499 | 2 |
| 500 – 1.999 | 5 |
| 2.000 – 4.999 | 10 |
| ≥ 5.000 | 25 |

```python
TICK_TABLE = [(0,200,1),(200,500,2),(500,2000,5),(2000,5000,10),(5000,None,25)]

def round_to_tick(price, direction='nearest'):
    tick = get_tick_size(price)
    if direction == 'down':    return floor(price / tick) * tick
    if direction == 'up':      return ceil(price / tick) * tick
    return round(price / tick) * tick
```

Juga hitung batas ARA/ARB harian dan tampilkan sebagai anotasi di chart.

---

## 9. Konfigurasi Per Mode

Simpan sebagai YAML di `backend/app/config/modes.yaml`. Semua angka di bawah
adalah **default yang bisa diubah user** di halaman Settings.

```yaml
scalping:
  timeframes: [1m, 5m]
  primary_timeframe: 1m
  weights: {trend: 0.15, momentum: 0.30, volume: 0.30, volatility: 0.15, structure: 0.10, fundamental: 0.0}
  atr_period: 14
  atr_multiplier_sl: 1.0
  max_risk_pct: 0.008           # 0.8% dari harga entry
  risk_per_trade_pct: 0.005     # 0.5% dari modal
  max_position_pct: 0.15
  tp_r: [1.0, 1.5, 2.0]
  min_risk_reward: 1.2
  min_avg_value_20d: 20000000000   # Rp 20 M/hari — butuh likuiditas tinggi
  swing_lookback: 10
  signal_ttl_minutes: 15
  key_indicators: [vwap, ema8, ema21, rsi7, relative_volume, volume_profile]
  notes: "Hanya aktif saat jam bursa. Wajib data intraday real-time."

day:
  timeframes: [5m, 15m, 1h]
  primary_timeframe: 15m
  weights: {trend: 0.25, momentum: 0.25, volume: 0.25, volatility: 0.10, structure: 0.15, fundamental: 0.0}
  atr_multiplier_sl: 1.5
  max_risk_pct: 0.02
  risk_per_trade_pct: 0.01
  max_position_pct: 0.25
  tp_r: [1.0, 2.0, 3.0]
  min_risk_reward: 1.5
  min_avg_value_20d: 5000000000
  swing_lookback: 20
  signal_ttl_minutes: 120
  force_close_before: "15:45"   # WIB, jangan bawa posisi menginap
  key_indicators: [vwap, ema9, ema21, macd, rsi14, atr, pivot_daily, relative_volume]

swing:
  timeframes: [1h, 4h, 1d]
  primary_timeframe: 1d
  weights: {trend: 0.30, momentum: 0.20, volume: 0.15, volatility: 0.10, structure: 0.25, fundamental: 0.0}
  atr_multiplier_sl: 2.0
  max_risk_pct: 0.07
  risk_per_trade_pct: 0.015
  max_position_pct: 0.30
  tp_r: [1.5, 2.5, 4.0]
  min_risk_reward: 2.0
  min_avg_value_20d: 1000000000
  swing_lookback: 40
  signal_ttl_days: 7
  key_indicators: [ema20, ema50, ema200, macd, rsi14, adx, bollinger, fibonacci, obv]

investing:
  timeframes: [1d, 1w, 1mo]
  primary_timeframe: 1w
  weights: {trend: 0.20, momentum: 0.10, volume: 0.05, volatility: 0.05, structure: 0.15, fundamental: 0.45}
  atr_multiplier_sl: 3.0
  max_risk_pct: 0.15
  risk_per_trade_pct: 0.02
  max_position_pct: 0.40
  tp_r: [2.0, 4.0, 6.0]
  min_risk_reward: 2.5
  min_avg_value_20d: 500000000
  swing_lookback: 60
  signal_ttl_days: 30
  use_fair_value: true
  key_indicators: [sma50, sma200, rsi14_weekly, per, pbv, roe, der, dividend_yield, earnings_growth]
  notes: "Stop loss lebih berfungsi sebagai batas tesis salah, bukan trigger otomatis."
```

---

## 10. Modul Fundamental (Mode Investing)

### 10.1 Rasio yang Dihitung

- **Valuasi:** PER, PBV, PSR, EV/EBITDA, PEG, Dividend Yield, Earnings Yield
- **Profitabilitas:** ROE, ROA, ROIC, Net Margin, Operating Margin, Gross Margin
- **Kesehatan:** DER, Current Ratio, Quick Ratio, Interest Coverage, Net Debt/EBITDA
- **Pertumbuhan:** Revenue CAGR 3Y & 5Y, EPS CAGR, growth QoQ dan YoY
- **Kualitas:** Free Cash Flow margin, konsistensi laba (jumlah kuartal untung
  dari 12 terakhir), Piotroski F-Score (0–9)

### 10.2 Skor Fundamental (0–100)

```
fundamental_score = 0.30 × valuation_score      # relatif terhadap median sektor
                  + 0.25 × profitability_score
                  + 0.20 × financial_health_score
                  + 0.15 × growth_score
                  + 0.10 × quality_score
```

Penting: **valuasi dinilai relatif terhadap sektor**, bukan absolut. PER 25 murah
untuk consumer goods, mahal untuk perbankan. Simpan median rasio per sektor dan
bandingkan dengan percentile.

### 10.3 Estimasi Fair Value

Hitung dengan tiga metode, tampilkan sebagai rentang, bukan angka tunggal:

1. **Relative valuation:** `fair = EPS_ttm × PER_median_sektor` dan
   `fair = BVPS × PBV_median_sektor`
2. **DCF sederhana:** proyeksi FCF 5 tahun dengan growth rate historis
   (dibatasi maksimal 15%), terminal growth 3%, discount rate = risk-free rate
   Indonesia + equity risk premium (default 8.5%).
3. **Dividend Discount Model:** hanya untuk emiten dengan riwayat dividen ≥ 5 tahun.

```
fair_value_range = [percentile_25(metode), percentile_75(metode)]
margin_of_safety = (fair_value_low - current_price) / fair_value_low × 100
```

Rekomendasi beli untuk investing: harga di bawah `fair_value_low × (1 - MoS_target)`,
default MoS target 20%. **Wajib tampilkan asumsi input DCF di UI** agar user
bisa menilai sendiri, dan tandai bahwa ini estimasi dengan sensitivitas tinggi.

---

## 11. Screener

### 11.1 Filter yang Tersedia

**Teknikal:** harga (range), rentang skor komposit, aksi (`strong_buy`/`buy`/...),
RSI, posisi vs EMA/SMA tertentu, golden/death cross dalam N hari, MACD cross,
relative volume, ATR%, jarak ke support/resistance (%), breakout high 20/50/250 hari,
Bollinger squeeze, pattern terdeteksi.

**Fundamental:** PER, PBV, ROE, DER, dividend yield, market cap, revenue growth,
sektor, papan pencatatan.

**Likuiditas:** rata-rata nilai transaksi 20 hari, frekuensi transaksi.

### 11.2 Preset Bawaan (harus tersedia sejak MVP)

| Preset | Kriteria |
|---|---|
| Momentum Breakout | Close > high 20 hari, relvol > 2.0, RSI 55–70, ADX > 25 |
| Pullback in Uptrend | EMA50 > EMA200, harga menyentuh EMA20, RSI 40–55, volume mengecil |
| Oversold Bounce | RSI < 30, harga di support strength > 65, bullish candle pattern |
| Value Investing | PER < median sektor, PBV < 1.5, ROE > 15%, DER < 1.0 |
| Dividend Play | Yield > 4%, payout < 70%, dividen konsisten ≥ 5 tahun |
| High Volume Scalp | Relvol > 3.0, spread ketat, nilai transaksi > Rp 20 M |

Hasil screener menampilkan kolom: simbol, harga, perubahan %, skor, aksi,
entry zone, SL, TP1, R:R, dan mini sparkline 30 hari.

---

## 12. Backtesting

### 12.1 Requirement

- Pilih mode, simbol (atau universe), rentang tanggal, modal awal.
- Eksekusi mengikuti aturan signal engine yang sama persis dengan live —
  gunakan **kode engine yang sama**, bukan duplikat, agar tidak ada divergensi.
- **Anti look-ahead bias:** pada bar ke-`t`, engine hanya boleh melihat data
  `[0..t]`. Tulis test khusus yang memverifikasi ini.
- Model eksekusi realistis:
  - Entry limit terisi hanya jika `low <= limit_price` pada bar berikutnya.
  - Slippage default 0.1% (konfigurabel; untuk scalping 0.2%).
  - Biaya broker IDX default: beli 0.15%, jual 0.25% (sudah termasuk PPh final 0.1%).
  - Gap: jika open melompati SL, eksekusi di open, bukan di harga SL.

### 12.2 Metrik Output

Total return, CAGR, max drawdown (%, durasi, tanggal), win rate, profit factor,
expectancy per trade (dalam R), average win/loss, Sharpe ratio, Sortino ratio,
Calmar ratio, jumlah trade, average holding period, consecutive loss terpanjang.

Visualisasi: equity curve, drawdown underwater chart, distribusi R multiple,
P/L per bulan (heatmap), daftar semua trade.

---

## 13. API Endpoints

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me

GET    /api/v1/instruments?search=&sector=&exchange=
GET    /api/v1/instruments/{symbol}
GET    /api/v1/instruments/{symbol}/ohlcv?timeframe=1d&from=&to=
GET    /api/v1/instruments/{symbol}/indicators?timeframe=1d&set=swing
GET    /api/v1/instruments/{symbol}/levels?timeframe=1d
GET    /api/v1/instruments/{symbol}/patterns?timeframe=1d
GET    /api/v1/instruments/{symbol}/fundamentals

GET    /api/v1/analysis/{symbol}?mode=swing&equity=100000000
       → objek Signal lengkap (Bagian 8.7). Endpoint utama aplikasi.
POST   /api/v1/analysis/batch          # body: {symbols: [], mode}
GET    /api/v1/signals?mode=&action=&min_score=&limit=

POST   /api/v1/screener/run            # body: filter object
GET    /api/v1/screener/presets
POST   /api/v1/screener/saved
GET    /api/v1/screener/saved

GET    /api/v1/watchlists
POST   /api/v1/watchlists
POST   /api/v1/watchlists/{id}/items
DELETE /api/v1/watchlists/{id}/items/{symbol}

GET    /api/v1/positions
POST   /api/v1/positions
PATCH  /api/v1/positions/{id}
GET    /api/v1/portfolio/summary
GET    /api/v1/portfolio/journal?from=&to=

GET    /api/v1/alerts
POST   /api/v1/alerts
DELETE /api/v1/alerts/{id}

POST   /api/v1/backtest/run            # async, return job_id
GET    /api/v1/backtest/{job_id}

WS     /api/v1/ws/quotes?symbols=BBCA,BBRI
WS     /api/v1/ws/alerts
```

Semua response error memakai format konsisten:
```json
{"error": {"code": "INSUFFICIENT_DATA", "message": "...", "details": {}}}
```

---

## 14. Halaman & Komponen Frontend

### 14.1 Daftar Halaman

| Route | Isi |
|---|---|
| `/` | Dashboard: ringkasan pasar, IHSG, top gainer/loser, sinyal terbaru sesuai mode aktif, watchlist |
| `/analysis/[symbol]` | **Halaman utama.** Chart + panel rekomendasi + breakdown skor |
| `/screener` | Filter builder, preset, tabel hasil |
| `/watchlist` | Manajemen watchlist, tabel dengan sinyal live |
| `/portfolio` | Posisi terbuka, P/L, alokasi, exposure |
| `/journal` | Riwayat trade, statistik, catatan & emotion tag |
| `/backtest` | Setup dan hasil backtest |
| `/alerts` | Kelola alert |
| `/settings` | Preferensi mode, modal, risk per trade, biaya broker, tema |

### 14.2 Halaman Analysis — Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ BBCA  Bank Central Asia   Rp 9.250  ▲ +1.65%   [Scalp|Day|Swing|Invest] │
├───────────────────────────────────────────┬──────────────────────┤
│                                           │  SKOR: 74.5  BUY     │
│           CANDLESTICK CHART               │  ████████░░  medium  │
│  (lightweight-charts)                     ├──────────────────────┤
│  Overlay:                                 │  RENCANA TRADING     │
│   • zona entry (kotak hijau transparan)   │  Entry  9.100–9.200  │
│   • garis stop loss (merah putus-putus)   │  Trigger      9.350  │
│   • garis TP1/TP2/TP3 (hijau)             │  Stop Loss    8.900  │
│   • level S/R (tebal ∝ strength)          │  TP1  9.550  (+40%)  │
│   • EMA/VWAP sesuai mode                  │  TP2  9.850  (+30%)  │
│                                           │  TP3 10.150  (+30%)  │
│  Panel bawah: Volume, RSI, MACD           │  R:R          2.15   │
│                                           ├──────────────────────┤
│                                           │  POSITION SIZING     │
│                                           │  Modal: [input]      │
│                                           │  Risk: [1%]          │
│                                           │  → 32 lot            │
│                                           │  → Rp 29.600.000     │
│                                           │  → Risiko Rp 800.000 │
├───────────────────────────────────────────┴──────────────────────┤
│ [Ringkasan] [Teknikal] [Fundamental] [Level] [Pattern] [Riwayat] │
│  Alasan Bullish ✓ / Alasan Bearish ✗ / Kondisi Pembatalan        │
└──────────────────────────────────────────────────────────────────┘
```

### 14.3 Aturan UI

- Warna: hijau untuk bullish/profit, merah untuk bearish/loss, abu untuk netral.
  Sediakan mode colorblind-safe (biru/oranye) di settings.
- Angka rupiah diformat dengan pemisah titik: `Rp 9.250`.
- Persentase selalu 2 desimal dengan tanda: `+1.65%`.
- Skor ditampilkan sebagai angka **dan** progress bar berwarna.
- Setiap rekomendasi harus punya tooltip "kenapa?" yang membuka breakdown.
- Loading state pakai skeleton, bukan spinner penuh layar.
- Dark mode wajib (trader sering bekerja lama di depan layar).

---

## 15. Kebutuhan Non-Fungsional

| Aspek | Target |
|---|---|
| Latensi API analisis (cached) | p95 < 300 ms |
| Latensi API analisis (cold compute) | p95 < 2 s |
| Latensi screener 800 emiten | < 5 s |
| Update quote via WebSocket | < 2 s dari sumber |
| Uptime saat jam bursa | 99.5% |
| Concurrent user (fase 1) | 200 |
| Backfill historis | 5 tahun daily, 60 hari intraday |

**Keamanan:** password argon2id; JWT access 15 menit + refresh 7 hari (rotating);
rate limit per user (100 req/menit umum, 10 req/menit untuk backtest); semua
input divalidasi Pydantic; parameterized query (tidak ada string SQL yang
dirangkai); secrets hanya via environment variable; audit log untuk perubahan
posisi.

**Observability:** structured logging (JSON), request ID di setiap log,
health check `/healthz` dan `/readyz`, metrik Prometheus (latensi, error rate,
job queue depth, kegagalan ingest).

---

## 16. Acceptance Criteria

Fitur dianggap selesai jika:

1. `GET /api/v1/analysis/BBCA?mode=swing` mengembalikan JSON persis sesuai
   skema 8.7, dengan semua harga valid terhadap tick size.
2. Untuk 20 saham sampel, tidak ada sinyal `buy` dengan R:R di bawah
   `min_risk_reward` mode tersebut.
3. Stop loss selalu di bawah `entry_low` untuk posisi long; TP1 < TP2 < TP3.
4. Unit test indikator: setiap indikator diuji terhadap nilai referensi yang
   dihitung manual, toleransi 0.01.
5. Test anti look-ahead: backtest pada data yang dipotong di titik `t`
   menghasilkan sinyal identik dengan backtest data penuh sampai titik `t`.
6. Mengganti mode di UI mengubah entry/SL/TP tanpa reload halaman.
7. Screener preset "Momentum Breakout" berjalan < 5 detik untuk seluruh emiten IDX.
8. Position sizing selalu menghasilkan kelipatan lot dan risiko aktual
   tidak melebihi `risk_per_trade_pct` dari modal.
9. Disclaimer muncul di semua halaman dan modal acknowledgement tersimpan.
10. Test coverage backend minimal 70%, dan 90% untuk modul `signals/` dan `risk/`.

---

## 17. Roadmap Implementasi (urutan untuk Claude Code)

### Fase 1 — Fondasi (kerjakan pertama)
1. Scaffold monorepo, Docker Compose (Postgres+TimescaleDB, Redis, backend, frontend).
2. Migrasi database untuk seluruh skema Bagian 5.
3. `MarketAdapter` + implementasi adapter yfinance untuk IDX.
4. Job ingest daily OHLCV + validator data quality.
5. Auth (register/login/JWT).
**Selesai jika:** data 5 tahun untuk 50 emiten LQ45 tersimpan dan bisa diambil via API.

### Fase 2 — Mesin Analisis
6. Seluruh indikator Bagian 7.1 + unit test.
7. Detektor support/resistance Bagian 7.2.
8. Deteksi candlestick pattern dengan filter konteks.
9. Utilitas tick size dan pembulatan harga.
**Selesai jika:** `GET /instruments/BBCA/indicators` dan `/levels` mengembalikan data benar.

### Fase 3 — Signal Engine (inti)
10. Loader konfigurasi mode dari YAML.
11. Scoring per kategori + composite.
12. Kalkulator entry, stop loss, take profit.
13. Position sizing.
14. Endpoint `/analysis/{symbol}` sesuai skema 8.7.
**Selesai jika:** acceptance criteria 1–3 dan 8 terpenuhi.

### Fase 4 — Frontend Inti
15. Layout, auth flow, dark mode, mode switcher global.
16. Halaman analysis dengan chart + overlay entry/SL/TP.
17. Dashboard dan watchlist.

### Fase 5 — Screener & Alert
18. Screener engine + preset + UI filter builder.
19. Alert engine + evaluasi berkala + notifikasi in-app/email.

### Fase 6 — Portfolio & Jurnal
20. CRUD posisi, kalkulasi P/L (termasuk biaya broker), ringkasan portofolio.
21. Jurnal trading dengan statistik R multiple dan win rate.

### Fase 7 — Backtesting
22. Engine backtest memakai signal engine yang sama, model eksekusi realistis.
23. Halaman hasil dengan equity curve dan metrik.

### Fase 8 — Fundamental & Investing
24. Ingest laporan keuangan, kalkulasi rasio, median sektor.
25. Skor fundamental dan estimasi fair value tiga metode.

### Fase 9 — Intraday
26. Ingest intraday, WebSocket quote, VWAP & volume profile.
27. Aktifkan mode scalping dan day trading.

---

## 18. Instruksi untuk Claude Code

Buat file `CLAUDE.md` di root dengan isi berikut:

```markdown
# Panduan Kerja

Baca `SPEC.md` sebelum menulis kode. Kerjakan per fase sesuai Bagian 17,
satu fase per sesi. Jangan lompat fase.

## Aturan wajib
- Semua harga: `Decimal`, jangan `float`. Kolom DB `NUMERIC(18,4)`.
- Timestamp disimpan UTC, ditampilkan Asia/Jakarta.
- Fungsi indikator harus pure: DataFrame masuk, Series keluar, tanpa I/O.
- Parameter strategi hanya boleh dibaca dari `config/modes.yaml`.
  Dilarang hard-code angka strategi di dalam fungsi.
- Setiap indikator dan setiap fungsi di `services/signals/` dan `services/risk/`
  wajib punya unit test sebelum dianggap selesai.
- Semua harga output dibulatkan lewat `round_to_tick()`.
- Jangan pernah mengembalikan sinyal buy jika R:R < minimum mode.
- Type hint lengkap di Python, strict mode di TypeScript.

## Setelah menyelesaikan sebuah fase
1. Jalankan test suite, pastikan hijau.
2. Update `PROGRESS.md`: apa yang selesai, apa yang ditunda, keputusan teknis
   yang diambil dan alasannya.
3. Berhenti dan laporkan, jangan otomatis lanjut ke fase berikutnya.

## Yang tidak boleh dilakukan
- Menambahkan klaim prediktif atau bahasa yang menjanjikan keuntungan.
- Mem-bypass validator data quality "supaya sinyal keluar".
- Memakai data masa depan dalam backtest.
```

---

## 19. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Data intraday IDX gratis tidak tersedia/tidak akurat | Scalping & day trading tidak berfungsi | Bangun mode degraded; siapkan slot untuk vendor berbayar sejak awal |
| Overfitting parameter ke data historis | Sinyal bagus di backtest, buruk di live | Walk-forward validation; simpan 20% data terakhir sebagai holdout yang tidak pernah dipakai tuning |
| Corporate action merusak data historis | Sinyal salah total | Validator split/dividen + flag manual review |
| User memperlakukan output sebagai jaminan | Kerugian finansial user | Disclaimer berlapis, tampilkan win rate historis apa adanya termasuk yang buruk, tampilkan alasan bearish sejajar dengan bullish |
| Beban komputasi screener seluruh emiten | Timeout | Precompute indikator via job terjadwal, screener hanya query hasil |
| Regulasi terkait rekomendasi investasi | Masalah legal | Posisikan sebagai alat analisis pribadi; hindari kata "rekomendasi" di UI publik, pakai "hasil analisis" |

---

**Akhir dokumen.**
