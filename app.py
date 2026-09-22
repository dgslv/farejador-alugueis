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

import webview

# Force headless scraping when running as desktop app (no browser window pop-ups)
import config as _cfg
_cfg.HEADLESS = True

# Both the installer subprocess and the scraper read this env var, so they agree
# on where Chromium lives. Must happen before playwright is imported anywhere.
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _cfg.BROWSERS_PATH

from storage import init_db

_browsers_ready = threading.Event()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _playwright_chromium_installed() -> bool:
    """Return True if Playwright Chromium is already installed in BROWSERS_PATH."""
    browsers_path = Path(_cfg.BROWSERS_PATH)
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
    # In the frozen .app, sys.executable is Aluguel itself — running
    # "sys.executable -m playwright" would relaunch the app in a loop.
    # Call the bundled Playwright driver (node + cli.js) directly instead.
    from playwright._impl._driver import compute_driver_executable
    node, cli = compute_driver_executable()
    subprocess.run([node, cli, "install", "chromium"], check=False)


# ── Background services ─────────────────────────────────────────────────────────

def _start_flask():
    from dashboard import app as flask_app
    flask_app.run(host="127.0.0.1", port=8080, use_reloader=False, threaded=True)


def _start_scheduler():
    _browsers_ready.wait()  # first scrape only after Chromium is installed
    from main import run_once, run_forever
    run_once()
    run_forever()


# ── Main ────────────────────────────────────────────────────────────────────────

def _log_to_file():
    """The .app has no terminal: send stdout/stderr to app.log so problems on
    another machine can be diagnosed from the file."""
    if not getattr(sys, "frozen", False):
        return
    from config import APP_LOG_PATH
    f = open(APP_LOG_PATH, "a", buffering=1, encoding="utf-8")
    sys.stdout = sys.stderr = f
    print(f"\n===== Aluguel started {time.strftime('%Y-%m-%d %H:%M:%S')} =====")


def main():
    _log_to_file()
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
        _browsers_ready.set()

    webview.start(on_ready)


if __name__ == "__main__":
    main()
