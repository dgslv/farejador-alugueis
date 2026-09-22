# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows (.exe)

from PyInstaller.utils.hooks import collect_all

playwright_datas, playwright_binaries, playwright_hiddenimports = collect_all("playwright")
webview_datas, webview_binaries, webview_hiddenimports = collect_all("webview")
# playwright-stealth ships a js/ folder with the evasion scripts
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
            "plyer.platforms.win.notification",
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
    a.binaries,
    a.datas,
    [],
    name="Aluguel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # no terminal window
    disable_windowed_traceback=False,
    icon=None,       # replace with "icon.ico" if you have one
)
