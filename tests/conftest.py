"""Shared fixtures.

Every test runs in a temporary data dir (FAREJADOR_DATA_DIR), so the suite
never touches the database, logs or Chromium of a real installation.
"""

import pytest

from farejador import db as db_module


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    """Isolated data dir for EVERY test (database, alerts.log, app.log)."""
    d = tmp_path / "data"
    monkeypatch.setenv("FAREJADOR_DATA_DIR", str(d))
    return d


@pytest.fixture
def db(data_dir):
    """Empty database with the tables created. Returns the file path."""
    db_module.init_db()
    return data_dir / "listings.db"
