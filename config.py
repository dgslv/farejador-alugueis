import os
import sys
from pathlib import Path

APP_NAME = "Farejador"  # binários, pasta de dados, notificações
APP_DISPLAY_NAME = "Farejador de Aluguéis"  # janela e títulos


def _app_data_dir() -> Path:
    """Pasta de dados do usuário (banco, logs, Chromium).

    Até a v1.1.0 ela se chamava "Aluguel". Se a pasta antiga existir e a nova
    não, ela é renomeada para preservar o banco e o histórico do usuário.

    FAREJADOR_DATA_DIR sobrepõe tudo isso (instalações portáteis e testes).
    """
    override = os.environ.get("FAREJADOR_DATA_DIR")
    if override:
        d = Path(override)
        d.mkdir(parents=True, exist_ok=True)
        return d
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
        name, legacy = APP_NAME, "Aluguel"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
        name, legacy = APP_NAME, "Aluguel"
    else:
        base = Path.home()
        name, legacy = ".farejador", ".aluguel"
    d = base / name
    old = base / legacy
    if old.is_dir() and not d.exists():
        try:
            old.rename(d)
        except OSError:
            pass  # sem permissão para mover: começa uma pasta nova; a antiga fica intacta
    d.mkdir(parents=True, exist_ok=True)
    return d


_DATA = _app_data_dir()

# Search URLs are managed via the Fontes tab in the dashboard (stored in DB).
# Add your VivaReal search URLs there after first launch.
SEARCH_URLS = []

EXCLUDED_NEIGHBORHOODS = []

DB_PATH = str(_DATA / "listings.db")
LOG_PATH = str(_DATA / "alerts.log")
APP_LOG_PATH = str(_DATA / "app.log")  # stdout/stderr of the packaged app
# Where the desktop app keeps Playwright's Chromium. Must be set explicitly:
# inside a PyInstaller bundle Playwright defaults to a read-only folder in the .app.
BROWSERS_PATH = str(_DATA / "ms-playwright")
# Defaults only — both are editable in the Fontes tab and stored in the DB.
INTERVAL_SECONDS = 15 * 60
MAX_TOTAL_PRICE = 9000  # aluguel + condomínio + IPTU
PAGE_SIZE = 36
MAX_PAGES = 5

HEADLESS = True
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
