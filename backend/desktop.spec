# PyInstaller spec untuk sidecar backend desktop.
#
# Build: pyinstaller desktop.spec --noconfirm
# Hasil: dist/stockapp-backend/stockapp-backend(.exe)
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
    [],
    exclude_binaries=True,
    name="stockapp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="stockapp-backend",
)
