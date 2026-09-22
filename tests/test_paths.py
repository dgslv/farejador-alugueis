"""paths.py — per-OS data dir, migration of the old "Aluguel" folder and the env override."""

import pytest

from farejador import paths


@pytest.fixture
def mac_home(tmp_path, monkeypatch):
    """Pretend to be macOS with tmp_path as home and no override. Returns the Application Support dir."""
    monkeypatch.delenv("FAREJADOR_DATA_DIR", raising=False)
    monkeypatch.setattr(paths.sys, "platform", "darwin")
    monkeypatch.setattr(paths.Path, "home", lambda: tmp_path)
    return tmp_path / "Library" / "Application Support"


def test_creates_new_data_dir(mac_home):
    assert paths.data_dir() == mac_home / "Farejador"
    assert (mac_home / "Farejador").is_dir()


def test_migrates_legacy_aluguel_dir_keeping_its_files(mac_home):
    legacy = mac_home / "Aluguel"
    legacy.mkdir(parents=True)
    (legacy / "listings.db").write_bytes(b"dados do usuario")
    new = paths.data_dir()
    assert new == mac_home / "Farejador"
    assert (new / "listings.db").read_bytes() == b"dados do usuario"
    assert not legacy.exists()


def test_leaves_legacy_dir_alone_when_new_one_already_exists(mac_home):
    (mac_home / "Aluguel").mkdir(parents=True)
    (mac_home / "Farejador").mkdir(parents=True)
    paths.data_dir()
    assert (mac_home / "Aluguel").is_dir()


def test_falls_back_to_fresh_dir_when_rename_fails(mac_home, monkeypatch):
    (mac_home / "Aluguel").mkdir(parents=True)

    def refuse(self, target):
        raise OSError("sem permissão")

    monkeypatch.setattr(paths.Path, "rename", refuse)
    assert paths.data_dir().is_dir()
    assert (mac_home / "Aluguel").is_dir()  # the old folder is left untouched


def test_windows_uses_appdata(tmp_path, monkeypatch):
    monkeypatch.delenv("FAREJADOR_DATA_DIR", raising=False)
    monkeypatch.setattr(paths.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert paths.data_dir() == tmp_path / "Farejador"


def test_linux_uses_hidden_dir_in_home(tmp_path, monkeypatch):
    monkeypatch.delenv("FAREJADOR_DATA_DIR", raising=False)
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setattr(paths.Path, "home", lambda: tmp_path)
    assert paths.data_dir() == tmp_path / ".farejador"


def test_env_override_wins_on_any_platform(tmp_path, monkeypatch):
    target = tmp_path / "portatil" / "dados"
    monkeypatch.setenv("FAREJADOR_DATA_DIR", str(target))
    assert paths.data_dir() == target
    assert target.is_dir()


def test_all_files_live_inside_the_data_dir(data_dir):
    assert paths.db_path() == data_dir / "listings.db"
    assert paths.alerts_log_path() == data_dir / "alerts.log"
    assert paths.app_log_path() == data_dir / "app.log"
    assert paths.browsers_path() == data_dir / "ms-playwright"


def test_importing_the_package_does_no_io(tmp_path, monkeypatch):
    """Importing config/paths must not create any folder (side effect on import)."""
    import importlib

    monkeypatch.setenv("FAREJADOR_DATA_DIR", str(tmp_path / "nunca-criada"))
    importlib.reload(paths)
    assert not (tmp_path / "nunca-criada").exists()
