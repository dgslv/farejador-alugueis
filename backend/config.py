import os

_BASE = os.path.dirname(os.path.abspath(__file__))

# SQLite snapshot (used only for one-time migration on first deploy)
DB_PATH = os.path.join(_BASE, "listings.db")
LOG_PATH = os.path.join(_BASE, "alerts.log")

# Supabase (PostgreSQL)
DB_HOST = "db.fxfuoqrjsemydqeqygxj.supabase.co"
DB_USER = "postgres"
DB_PASSWORD = "fcE&Zg1U&d!7XCa6"
DB_NAME = "postgres"

INTERVAL_MINUTES = 15
MAX_PAGES = 5
HEADLESS = True

SEARCH_URL = (
    "https://www.vivareal.com.br/aluguel/rj/rio-de-janeiro/zona-sul/botafogo/apartamento_residencial/"
    "?transacao=aluguel"
    "&onde=,Rio+de+Janeiro,Rio+de+Janeiro,Zona+Sul,Botafogo,,,neighborhood,"
    "BR%3ERio+de+Janeiro%3ENULL%3ERio+de+Janeiro%3EZona+Sul%3EBotafogo,-22.951098,-43.180746,"
    "&tipos=apartamento_residencial"
    "&quartos=2,3,4"
    "&precoTotal=true"
    "&precoMaximo=8500"
    "&areaMinima=70"
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
