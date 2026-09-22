"""Onde o app guarda dados: banco, logs e o Chromium do Playwright.

Tudo é calculado na hora da chamada (nada acontece ao importar), para que
testes e instalações portáteis possam apontar a pasta por FAREJADOR_DATA_DIR.
"""

import os
import sys
from pathlib import Path

from farejador.config import APP_NAME

_LEGACY_NAMES = {"darwin": "Aluguel", "win32": "Aluguel", "linux": ".aluguel"}


def data_dir() -> Path:
    """Pasta de dados do usuário, criada se não existir.

    Até a v1.1.0 ela se chamava "Aluguel". Se a pasta antiga existir e a nova
    não, ela é renomeada para preservar o banco e o histórico do usuário.
    FAREJADOR_DATA_DIR sobrepõe tudo isso.
    """
    override = os.environ.get("FAREJADOR_DATA_DIR")
    if override:
        d = Path(override)
        d.mkdir(parents=True, exist_ok=True)
        return d

    if sys.platform == "darwin":
        base, name = Path.home() / "Library" / "Application Support", APP_NAME
    elif sys.platform == "win32":
        base, name = Path(os.environ.get("APPDATA", str(Path.home()))), APP_NAME
    else:
        base, name = Path.home(), f".{APP_NAME.lower()}"
    d = base / name
    legacy = base / _LEGACY_NAMES.get(sys.platform, ".aluguel")
    if legacy.is_dir() and not d.exists():
        try:
            legacy.rename(d)
        except OSError:
            pass  # sem permissão para mover: começa uma pasta nova; a antiga fica intacta
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return data_dir() / "listings.db"


def alerts_log_path() -> Path:
    return data_dir() / "alerts.log"


def app_log_path() -> Path:
    """stdout/stderr do app empacotado, que não tem terminal."""
    return data_dir() / "app.log"


def browsers_path() -> Path:
    """Onde o Playwright instala o Chromium. Dentro do .app o padrão seria uma
    pasta somente leitura do bundle, então o caminho é forçado para a pasta de dados."""
    return data_dir() / "ms-playwright"
