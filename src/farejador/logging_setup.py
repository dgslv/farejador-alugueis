"""Configuração única de logging: terminal no modo de desenvolvimento, app.log no app empacotado."""

import logging
import sys
from pathlib import Path
from typing import Optional

FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """Chame uma vez no ponto de entrada. Com `log_file`, tudo (inclusive
    stdout/stderr de bibliotecas que só fazem print) vai para o arquivo."""
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    if log_file is None:
        handler: logging.Handler = logging.StreamHandler(sys.stderr)
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file, encoding="utf-8")
        stream = open(log_file, "a", buffering=1, encoding="utf-8")  # noqa: SIM115 (vive até o processo acabar)
        sys.stdout = sys.stderr = stream
    handler.setFormatter(logging.Formatter(FORMAT, DATEFMT))
    root.addHandler(handler)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # o Flask loga cada request em INFO
