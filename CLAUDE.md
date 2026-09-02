# Panduan Kerja

Baca `SPEC.md` sebelum menulis kode. Kerjakan per fase sesuai Bagian 17,
satu fase per sesi. Jangan lompat fase.

## Konteks penting

Ini adalah **decision support tool untuk analisis saham**, BUKAN trading
platform. Tidak ada eksekusi order ke broker (lihat SPEC.md Bagian 3.2 —
"Eksekusi order langsung ke broker" secara eksplisit Out of Scope). Output
aplikasi adalah rekomendasi rule-based (entry zone, stop loss, take profit,
position sizing) yang harus selalu disertai disclaimer bahwa ini bukan
nasihat investasi (SPEC.md Bagian 0).

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
- Menambahkan fitur eksekusi order ke broker (di luar scope produk ini).
