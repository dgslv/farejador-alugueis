import os
import sys
from pathlib import Path


def _app_data_dir() -> Path:
    if sys.platform == "darwin":
        d = Path.home() / "Library" / "Application Support" / "Aluguel"
    elif sys.platform == "win32":
        d = Path(os.environ.get("APPDATA", str(Path.home()))) / "Aluguel"
    else:
        d = Path.home() / ".aluguel"
    d.mkdir(parents=True, exist_ok=True)
    return d


_DATA = _app_data_dir()

SEARCH_URLS = [
    # Botafogo — existing search
    (
        "https://www.vivareal.com.br/aluguel/rj/rio-de-janeiro/zona-sul/botafogo/apartamento_residencial/"
        "?transacao=aluguel"
        "&onde=,Rio+de+Janeiro,Rio+de+Janeiro,Zona+Sul,Botafogo,,,neighborhood,"
        "BR%3ERio+de+Janeiro%3ENULL%3ERio+de+Janeiro%3EZona+Sul%3EBotafogo,-22.951098,-43.180746,"
        "&tipos=apartamento_residencial"
        "&quartos=2,3,4"
        "&precoTotal=true"
        "&precoMaximo=8500"
        "&areaMinima=70"
    ),
    # Humaitá
    (
        "https://www.vivareal.com.br/aluguel/rj/rio-de-janeiro/zona-sul/humaita/apartamento_residencial/"
        "?transacao=aluguel"
        "&onde=,Rio+de+Janeiro,Rio+de+Janeiro,Zona+Sul,Humait%C3%A1,,,neighborhood,"
        "BR%3ERio+de+Janeiro%3ENULL%3ERio+de+Janeiro%3EZona+Sul%3EHumaita,-22.956627,-43.198584,"
        "&tipos=apartamento_residencial"
        "&quartos=2,3,4"
        "&precoTotal=true"
        "&precoMaximo=8500"
    ),
]

EXCLUDED_NEIGHBORHOODS = ["copacabana", "laranjeiras", "cosme velho"]

DB_PATH = str(_DATA / "listings.db")
LOG_PATH = str(_DATA / "alerts.log")
INTERVAL_MINUTES = 15
PAGE_SIZE = 36
MAX_PAGES = 5

HEADLESS = False
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
