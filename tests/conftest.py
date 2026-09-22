"""Fixtures compartilhadas.

Todo teste roda numa pasta de dados temporária (FAREJADOR_DATA_DIR), então a
suíte nunca toca o banco, os logs ou o Chromium de uma instalação real.
"""

import pytest

from farejador import db as db_module


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    """Pasta de dados isolada para TODO teste (banco, alerts.log, app.log)."""
    d = tmp_path / "data"
    monkeypatch.setenv("FAREJADOR_DATA_DIR", str(d))
    return d


@pytest.fixture
def db(data_dir):
    """Banco vazio com as tabelas criadas. Devolve o caminho do arquivo."""
    db_module.init_db()
    return data_dir / "listings.db"
