"""__main__.py — the single entry point (`farejador`, `python -m farejador`)."""

import pytest

from farejador import __version__
from farejador.__main__ import main


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"farejador {__version__}"


def test_headless_and_dashboard_are_mutually_exclusive(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--headless", "--dashboard"])
    assert exc.value.code == 2
    assert "not allowed with" in capsys.readouterr().err


def test_default_mode_is_the_desktop_app(monkeypatch):
    launched = []
    import farejador.desktop

    monkeypatch.setattr(farejador.desktop, "main", lambda: launched.append("desktop"))
    main([])
    assert launched == ["desktop"]


def test_headless_mode_runs_the_scheduler(monkeypatch):
    launched = []
    import farejador.scheduler

    monkeypatch.setattr(farejador.scheduler, "main", lambda: launched.append("scheduler"))
    main(["--headless"])
    assert launched == ["scheduler"]
