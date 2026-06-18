# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


ROOT = Path(SPECPATH)
APP_NAME = "HeartRateBandLogger"

hiddenimports = []
hiddenimports += collect_submodules("bleak")
hiddenimports += collect_submodules("PySide6")

block_cipher = None

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="com.example.heart-rate-band-logger",
        info_plist={
            "CFBundleName": "心率助手",
            "CFBundleDisplayName": "心率助手",
            "NSBluetoothAlwaysUsageDescription": "用于搜索并连接智能手环，读取标准蓝牙心率广播。",
            "NSBluetoothPeripheralUsageDescription": "用于搜索并连接智能手环，读取标准蓝牙心率广播。",
        },
    )
