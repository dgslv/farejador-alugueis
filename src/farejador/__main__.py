"""Ponto de entrada único.

farejador               app desktop (painel em janela nativa + robô de busca)
farejador --headless    só o robô, no terminal
farejador --dashboard   só o painel, em http://127.0.0.1:8080 no seu navegador
"""

import argparse
import logging

from farejador import __version__
from farejador.config import APP_DISPLAY_NAME, DASHBOARD_HOST, DASHBOARD_PORT, DASHBOARD_URL


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="farejador", description=APP_DISPLAY_NAME)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--headless", action="store_true", help="só o robô de busca, no terminal")
    mode.add_argument("--dashboard", action="store_true", help=f"só o painel, em {DASHBOARD_URL}")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    if args.headless:
        from farejador.logging_setup import setup_logging
        from farejador.scheduler import main as run_scheduler

        setup_logging()
        run_scheduler()
    elif args.dashboard:
        from farejador.db import init_db
        from farejador.logging_setup import setup_logging
        from farejador.web import create_app

        setup_logging()
        init_db()
        logging.getLogger(__name__).info("painel em %s", DASHBOARD_URL)
        create_app().run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=False)
    else:
        from farejador.desktop import main as run_desktop

        run_desktop()


if __name__ == "__main__":
    main()
