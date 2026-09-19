# binaries/

Sidecar backend (hasil `pyinstaller backend/desktop.spec`) ditaruh di sini
sebelum `tauri build`/`tauri dev`, dengan nama yang menyertakan target
triple platform — **wajib**, ini konvensi Tauri untuk sidecar binary:

```
stockapp-backend-aarch64-apple-darwin      # Mac Apple Silicon
stockapp-backend-x86_64-apple-darwin       # Mac Intel
```

Dapatkan target triple mesin Anda dengan `rustc -Vv | grep host`.

## Build manual di Mac

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-desktop.txt
pyinstaller desktop.spec --noconfirm

TRIPLE=$(rustc -Vv | grep host | cut -d' ' -f2)
cp dist/stockapp-backend ../desktop/src-tauri/binaries/stockapp-backend-$TRIPLE

cd ../desktop
npm install
npm run build
```

Otomatis: lihat `.github/workflows/build-macos.yml` — langkah yang sama
dijalankan CI di runner `macos-latest`, hasil `.dmg` diunggah sebagai
artifact, tidak perlu setup manual di atas kalau cukup pakai itu.

## Setelah install: WAJIB hapus quarantine flag

`.app` di dalam `.dmg` ditandatangani **ad-hoc** (`signingIdentity: "-"`
di `tauri.conf.json`), bukan pakai sertifikat Apple Developer ID resmi
($99/tahun, belum dibeli — tidak diperlukan untuk pemakaian sendiri).
Konsekuensinya: **Gatekeeper macOS SELALU menolak signature ad-hoc** untuk
file yang kena quarantine flag (ditambahkan otomatis oleh browser saat
download) — muncul sebagai dialog **"is damaged and can't be opened"**,
bukan prompt "unidentified developer" yang bisa di-bypass klik-kanan-buka.

Setiap kali install `.dmg` baru (termasuk update), setelah drag `.app` ke
Applications, jalankan di Terminal:

```bash
sudo xattr -dr com.apple.quarantine "/Applications/Stock Analysis Platform.app"
```

Verifikasi berhasil (baris `com.apple.quarantine` sudah tidak muncul):

```bash
xattr -l "/Applications/Stock Analysis Platform.app"
```

`xattr -cr` (hapus semua attribute) atau klik-kanan-buka biasa **tidak
cukup** — harus `-dr com.apple.quarantine` spesifik dengan `sudo`, target
langsung ke `.app` yang sudah di-copy ke Applications (bukan yang masih
di dalam `.dmg` mounted, itu read-only).
