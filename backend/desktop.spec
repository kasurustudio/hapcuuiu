# PyInstaller spec untuk sidecar backend desktop.
#
# Build: pyinstaller desktop.spec --noconfirm
# Hasil: dist/stockapp-backend (satu file executable, ONEFILE mode)
#
# PENTING — kenapa onefile, bukan onedir: Tauri `externalBin` (sidecar)
# mengharapkan SATU file executable yang berdiri sendiri, dipindah/di-rename
# bebas ke `desktop/src-tauri/binaries/`. Versi awal spec ini pakai onedir
# (EXE exclude_binaries=True + COLLECT) yang menghasilkan direktori berisi
# executable PLUS banyak file pendamping wajib (shared library Python,
# dst). CI/README sebelumnya cuma meng-copy file executable-nya saja keluar
# dari direktori itu — di macOS ini menyebabkan crash saat dijalankan
# ("Failed to load Python shared library ... Contents/Frameworks/Python")
# karena file pendamping yang dibutuhkan tertinggal. Onefile membungkus
# semuanya jadi satu file (unpack ke direktori temp saat runtime), jadi
# aman dipindah sebagai satu file tunggal.
#
# PENTING (Tauri sidecar naming): binary hasil build ini harus di-rename
# menambahkan target triple sebelum dipakai Tauri, mis. di macOS Apple
# Silicon jadi `stockapp-backend-aarch64-apple-darwin`. Ini dilakukan oleh
# script CI (.github/workflows/build-macos.yml), bukan di spec ini, supaya
# spec tetap portable lintas OS.

import sys

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden_imports = (
    collect_submodules("uvicorn")
    + collect_submodules("apscheduler")
    + collect_submodules("app")
    + [
        "passlib.handlers.argon2",
        "argon2",
        "email_validator",
        "sqlalchemy.dialects.sqlite",
        "sqlalchemy.dialects.postgresql",
    ]
)

a = Analysis(
    ["desktop_entrypoint.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest"],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="stockapp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
