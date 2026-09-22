"""Constants and defaults. Nothing here does I/O; paths live in paths.py."""

import os

APP_NAME = "Farejador"  # binaries, data dir, notifications
APP_DISPLAY_NAME = "Farejador de Aluguéis"  # window title and headings

# Local dashboard. FAREJADOR_PORT works around another program holding 8080.
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = int(os.environ.get("FAREJADOR_PORT", "8080"))
DASHBOARD_URL = f"http://{DASHBOARD_HOST}:{DASHBOARD_PORT}"

# Defaults only — both are editable in the Fontes tab and stored in the database.
INTERVAL_SECONDS = 15 * 60
MAX_TOTAL_PRICE = 9000  # rent + condo fee + IPTU

# Scraper
MAX_PAGES = 5  # result pages per source
EXCLUDED_NEIGHBORHOODS: list = []  # lowercase fragments of URL or neighborhood to skip
HEADLESS = True
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
