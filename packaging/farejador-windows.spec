# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows (single-file .exe). Build with packaging\build-windows.bat.
# Every path is derived from SPECPATH (injected by PyInstaller), so the spec works
# from any working directory.

import os
import re

from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # noqa: F821
SRC = os.path.join(ROOT, "src")
PKG = os.path.join(SRC, "farejador")

with open(os.path.join(PKG, "__init__.py"), encoding="utf-8") as _f:
    VERSION = re.search(r'__version__ = "([^"]+)"', _f.read()).group(1)

playwright_datas, playwright_binaries, playwright_hiddenimports = collect_all("playwright")
webview_datas, webview_binaries, webview_hiddenimports = collect_all("webview")
# playwright-stealth ships a js/ folder with the evasion scripts
stealth_datas, stealth_binaries, stealth_hiddenimports = collect_all("playwright_stealth")

a = Analysis(
    [os.path.join(PKG, "__main__.py")],
    pathex=[SRC],
    binaries=playwright_binaries + webview_binaries + stealth_binaries,
    datas=playwright_datas
    + webview_datas
    + stealth_datas
    + [
        # Flask resolves these relative to the farejador.web package inside the bundle.
        (os.path.join(PKG, "web", "templates"), "farejador/web/templates"),
        (os.path.join(PKG, "web", "static"), "farejador/web/static"),
    ],
    hiddenimports=(
        playwright_hiddenimports
        + webview_hiddenimports
        + stealth_hiddenimports
        + ["plyer", "plyer.platforms.win.notification", "flask", "sqlite3", "json"]
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
    name="Farejador",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # no terminal window
    disable_windowed_traceback=False,
    icon=os.path.join(SPECPATH, "icons", "farejador.ico"),  # noqa: F821
)
