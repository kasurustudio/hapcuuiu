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
cp dist/stockapp-backend/stockapp-backend ../desktop/src-tauri/binaries/stockapp-backend-$TRIPLE

cd ../desktop
npm install
npm run build
```

Otomatis: lihat `.github/workflows/build-macos.yml` — langkah yang sama
dijalankan CI di runner `macos-latest`, hasil `.dmg` diunggah sebagai
artifact, tidak perlu setup manual di atas kalau cukup pakai itu.
