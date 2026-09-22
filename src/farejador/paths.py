"""Where the app keeps its data: database, logs and Playwright's Chromium.

Everything is computed at call time (nothing happens on import), so tests and
portable installs can point the folder elsewhere with FAREJADOR_DATA_DIR.
"""

import os
import sys
from pathlib import Path

from farejador.config import APP_NAME

_LEGACY_NAMES = {"darwin": "Aluguel", "win32": "Aluguel", "linux": ".aluguel"}


def data_dir() -> Path:
    """The user's data folder, created if missing.

    Up to v1.1.0 it was called "Aluguel". If the old folder exists and the new
    one does not, it is renamed so the database and history survive.
    FAREJADOR_DATA_DIR overrides all of this.
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
            pass  # no permission to move: start a fresh folder, leave the old one untouched
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return data_dir() / "listings.db"


def alerts_log_path() -> Path:
    return data_dir() / "alerts.log"


def app_log_path() -> Path:
    """stdout/stderr of the packaged app, which has no terminal."""
    return data_dir() / "app.log"


def browsers_path() -> Path:
    """Where Playwright installs Chromium. Inside the .app the default would be a
    read-only folder in the bundle, so the path is forced into the data dir."""
    return data_dir() / "ms-playwright"
