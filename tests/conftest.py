"""Fixtures compartilhadas.

A suíte nunca toca a pasta de dados real do usuário: FAREJADOR_DATA_DIR é
apontada para uma pasta temporária ANTES de qualquer módulo do app ser
importado (config.py cria a pasta no import), e cada teste recebe um banco
SQLite vazio e isolado.
"""

import os
import tempfile

os.environ.setdefault("FAREJADOR_DATA_DIR", tempfile.mkdtemp(prefix="farejador-tests-"))

import pytest  # noqa: E402

import storage  # noqa: E402


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Banco vazio: storage.DB_PATH aponta para um arquivo temporário do teste."""
    path = tmp_path / "listings.db"
    monkeypatch.setattr(storage, "DB_PATH", str(path))
    storage.init_db()
    return path
