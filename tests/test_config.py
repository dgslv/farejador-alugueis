"""config.py — pasta de dados por sistema, migração da pasta antiga e override."""

import pytest

import config


@pytest.fixture
def mac_home(tmp_path, monkeypatch):
    """Finge um macOS cuja home é tmp_path. Devolve a pasta Application Support."""
    monkeypatch.delenv("FAREJADOR_DATA_DIR", raising=False)
    monkeypatch.setattr(config.sys, "platform", "darwin")
    monkeypatch.setattr(config.Path, "home", lambda: tmp_path)
    return tmp_path / "Library" / "Application Support"


def test_creates_new_data_dir(mac_home):
    assert config._app_data_dir() == mac_home / "Farejador"
    assert (mac_home / "Farejador").is_dir()


def test_migrates_legacy_aluguel_dir_keeping_its_files(mac_home):
    legacy = mac_home / "Aluguel"
    legacy.mkdir(parents=True)
    (legacy / "listings.db").write_bytes(b"dados do usuario")
    new = config._app_data_dir()
    assert new == mac_home / "Farejador"
    assert (new / "listings.db").read_bytes() == b"dados do usuario"
    assert not legacy.exists()


def test_leaves_legacy_dir_alone_when_new_one_already_exists(mac_home):
    (mac_home / "Aluguel").mkdir(parents=True)
    (mac_home / "Farejador").mkdir(parents=True)
    config._app_data_dir()
    assert (mac_home / "Aluguel").is_dir()


def test_falls_back_to_fresh_dir_when_rename_fails(mac_home, monkeypatch):
    (mac_home / "Aluguel").mkdir(parents=True)

    def refuse(self, target):
        raise OSError("sem permissão")

    monkeypatch.setattr(config.Path, "rename", refuse)
    assert config._app_data_dir().is_dir()
    assert (mac_home / "Aluguel").is_dir()  # a pasta antiga fica intacta


def test_windows_uses_appdata(tmp_path, monkeypatch):
    monkeypatch.delenv("FAREJADOR_DATA_DIR", raising=False)
    monkeypatch.setattr(config.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert config._app_data_dir() == tmp_path / "Farejador"


def test_linux_uses_hidden_dir_in_home(tmp_path, monkeypatch):
    monkeypatch.delenv("FAREJADOR_DATA_DIR", raising=False)
    monkeypatch.setattr(config.sys, "platform", "linux")
    monkeypatch.setattr(config.Path, "home", lambda: tmp_path)
    assert config._app_data_dir() == tmp_path / ".farejador"


def test_env_override_wins_on_any_platform(tmp_path, monkeypatch):
    target = tmp_path / "portatil" / "dados"
    monkeypatch.setenv("FAREJADOR_DATA_DIR", str(target))
    assert config._app_data_dir() == target
    assert target.is_dir()
