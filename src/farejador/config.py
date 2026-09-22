"""Constantes e valores padrão. Nada aqui faz I/O; caminhos ficam em paths.py."""

import os

APP_NAME = "Farejador"  # binários, pasta de dados, notificações
APP_DISPLAY_NAME = "Farejador de Aluguéis"  # janela e títulos

# Painel local. FAREJADOR_PORT resolve conflito com outro programa na 8080.
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = int(os.environ.get("FAREJADOR_PORT", "8080"))
DASHBOARD_URL = f"http://{DASHBOARD_HOST}:{DASHBOARD_PORT}"

# Padrões — ambos editáveis na aba Fontes e guardados no banco.
INTERVAL_SECONDS = 15 * 60
MAX_TOTAL_PRICE = 9000  # aluguel + condomínio + IPTU

# Scraper
MAX_PAGES = 5  # páginas de resultado por fonte
EXCLUDED_NEIGHBORHOODS: list = []  # trechos (minúsculos) de URL ou bairro a ignorar
HEADLESS = True
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
