"""assets/ — o logo e os ícones que os specs do PyInstaller e o painel referenciam.

Os arquivos são versionados (gerados por scripts/make-icons.py); se algum sumir
ou for corrompido, é melhor descobrir aqui do que no build de release.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def test_svg_source_exists():
    assert (ASSETS / "farejador.svg").read_text(encoding="utf-8").lstrip().startswith("<svg")


def test_logo_png_is_a_png():
    assert (ASSETS / "logo.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_windows_icon_is_an_ico():
    assert (ASSETS / "farejador.ico").read_bytes()[:4] == b"\x00\x00\x01\x00"


def test_macos_icon_is_an_icns():
    assert (ASSETS / "farejador.icns").read_bytes()[:4] == b"icns"


def test_specs_reference_the_icons_and_bundle_assets():
    mac = (ROOT / "farejador-macos.spec").read_text(encoding="utf-8")
    win = (ROOT / "farejador-windows.spec").read_text(encoding="utf-8")
    assert 'icon="assets/farejador.icns"' in mac
    assert 'icon="assets/farejador.ico"' in win
    assert '("assets", "assets")' in mac
    assert '("assets", "assets")' in win
