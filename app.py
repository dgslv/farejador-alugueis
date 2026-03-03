"""
Desktop entry point for Aluguel.
Starts Flask dashboard + scraper scheduler, then opens a native pywebview window.
"""
import sys
import os
import subprocess
import threading
import time
from pathlib import Path

import schedule
import webview

# Force headless scraping when running as desktop app (no browser window pop-ups)
import config as _cfg
_cfg.HEADLESS = True

from config import INTERVAL_MINUTES
from storage import init_db


# ── Helpers ────────────────────────────────────────────────────────────────────

def _playwright_chromium_installed() -> bool:
    """Return True if Playwright Chromium is already installed."""
    home = Path.home()
    if sys.platform == "darwin":
        browsers_path = home / "Library" / "Caches" / "ms-playwright"
    elif sys.platform == "win32":
        local_app = os.environ.get("LOCALAPPDATA", "")
        browsers_path = Path(local_app) / "ms-playwright"
    else:
        browsers_path = home / ".cache" / "ms-playwright"

    if not browsers_path.exists():
        return False
    return any(p.name.startswith("chromium") for p in browsers_path.iterdir())


def _install_chromium(window: webview.Window):
    """Install Playwright Chromium while showing a progress screen."""
    window.load_html("""
    <html><body style="font-family:sans-serif;display:flex;align-items:center;
    justify-content:center;height:100vh;margin:0;background:#f5f5f5;flex-direction:column;gap:12px">
    <h2 style="color:#333;margin:0">Configurando Aluguel…</h2>
    <p style="color:#666;margin:0">Instalando navegador (~300 MB, apenas na primeira vez).</p>
    <p style="color:#999;font-size:13px;margin:0">Aguarde, pode levar alguns minutos.</p>
    </body></html>
    """)
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=False,
    )


# ── Background services ─────────────────────────────────────────────────────────

def _start_flask():
    from dashboard import app as flask_app
    flask_app.run(host="127.0.0.1", port=8080, use_reloader=False, threaded=True)


def _start_scheduler():
    from main import run_once
    run_once()
    schedule.every(INTERVAL_MINUTES).minutes.do(run_once)
    while True:
        schedule.run_pending()
        time.sleep(30)


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    init_db()

    threading.Thread(target=_start_flask, daemon=True).start()
    threading.Thread(target=_start_scheduler, daemon=True).start()

    # Wait briefly for Flask to bind
    time.sleep(1.5)

    window = webview.create_window(
        "Aluguel",
        "http://127.0.0.1:8080",
        width=1280,
        height=820,
        min_size=(800, 600),
    )

    def on_ready():
        if not _playwright_chromium_installed():
            _install_chromium(window)
            window.load_url("http://127.0.0.1:8080")

    webview.start(on_ready)


if __name__ == "__main__":
    main()
