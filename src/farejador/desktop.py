"""App desktop: painel Flask e robô de busca em threads, janela nativa (pywebview)."""

import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import webview

from farejador import paths
from farejador.config import APP_DISPLAY_NAME, APP_NAME, DASHBOARD_HOST, DASHBOARD_PORT, DASHBOARD_URL
from farejador.logging_setup import setup_logging

log = logging.getLogger(__name__)
_browsers_ready = threading.Event()


def _chromium_installed(browsers_path: Path) -> bool:
    return browsers_path.exists() and any(p.name.startswith("chromium") for p in browsers_path.iterdir())


def _install_chromium(window: "webview.Window") -> None:
    """Install Playwright Chromium while showing a progress screen."""
    window.load_html(f"""
    <html><body style="font-family:sans-serif;display:flex;align-items:center;
    justify-content:center;height:100vh;margin:0;background:#f5f5f5;flex-direction:column;gap:12px">
    <img src="{DASHBOARD_URL}/static/logo.png" width="96" height="96" style="border-radius:22px" alt="">
    <h2 style="color:#333;margin:0">Configurando o Farejador…</h2>
    <p style="color:#666;margin:0">Instalando navegador (~300 MB, apenas na primeira vez).</p>
    <p style="color:#999;font-size:13px;margin:0">Aguarde, pode levar alguns minutos.</p>
    </body></html>
    """)
    # In the frozen .app, sys.executable is the app itself — running
    # "sys.executable -m playwright" would relaunch the app in a loop.
    # Call the bundled Playwright driver (node + cli.js) directly instead.
    from playwright._impl._driver import compute_driver_executable

    node, cli = compute_driver_executable()
    subprocess.run([node, cli, "install", "chromium"], check=False)


def _start_flask() -> None:
    from farejador.web import create_app

    create_app().run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, use_reloader=False, threaded=True)


def _start_scheduler() -> None:
    _browsers_ready.wait()  # first scrape only after Chromium is installed
    from farejador.scheduler import run_forever, run_once

    run_once()
    run_forever()


def main() -> None:
    frozen = bool(getattr(sys, "frozen", False))
    # The .app has no terminal: everything goes to app.log so problems on
    # another machine can be diagnosed from the file.
    setup_logging(paths.app_log_path() if frozen else None)
    log.info("===== %s started =====", APP_NAME)

    # Both the installer subprocess and the scraper read this env var, so they
    # agree on where Chromium lives. Set before playwright is imported anywhere.
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(paths.browsers_path())

    from farejador.db import init_db

    init_db()
    threading.Thread(target=_start_flask, daemon=True).start()
    threading.Thread(target=_start_scheduler, daemon=True).start()
    time.sleep(1.5)  # wait briefly for Flask to bind

    window = webview.create_window(APP_DISPLAY_NAME, DASHBOARD_URL, width=1280, height=820, min_size=(800, 600))

    def on_ready() -> None:
        from farejador.notify import request_permission

        request_permission()
        if not _chromium_installed(paths.browsers_path()):
            _install_chromium(window)
            window.load_url(DASHBOARD_URL)
        _browsers_ready.set()

    webview.start(on_ready)


if __name__ == "__main__":
    main()
