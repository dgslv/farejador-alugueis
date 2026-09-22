# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for macOS (.app bundle)

import sys
from PyInstaller.utils.hooks import collect_all

# Collect playwright Python package files
playwright_datas, playwright_binaries, playwright_hiddenimports = collect_all("playwright")

# Collect pywebview
webview_datas, webview_binaries, webview_hiddenimports = collect_all("webview")

# Collect playwright-stealth (ships a js/ folder with the evasion scripts)
stealth_datas, stealth_binaries, stealth_hiddenimports = collect_all("playwright_stealth")

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=playwright_binaries + webview_binaries + stealth_binaries,
    datas=playwright_datas + webview_datas + stealth_datas,
    hiddenimports=(
        playwright_hiddenimports
        + webview_hiddenimports
        + stealth_hiddenimports
        + [
            "plyer",
            "plyer.platforms.macosx.notification",
            "flask",
            "schedule",
            "sqlite3",
            "json",
        ]
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Aluguel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # no terminal window
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Aluguel",
)

app = BUNDLE(
    coll,
    name="Aluguel.app",
    icon=None,  # replace with "icon.icns" if you have one
    bundle_identifier="com.aluguel.app",
    info_plist={
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
        "CFBundleShortVersionString": "1.0.0",
    },
)
