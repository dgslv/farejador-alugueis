#!/usr/bin/env python3
"""Gera o logo e os ícones do app a partir de assets/farejador.svg.

Saídas (todas versionadas, para o build não depender deste script):
  assets/logo.png                         512 px — README
  src/farejador/web/static/logo.png       512 px — painel e favicon (dado do pacote)
  packaging/icons/farejador.ico           Windows (16–256 px)
  packaging/icons/farejador.icns          macOS (só roda no macOS: usa o iconutil do sistema)

Requer: pip install -e ".[desktop]"  +  playwright install chromium
Uso:    python packaging/make-icons.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "assets" / "farejador.svg"
ICONS = ROOT / "packaging" / "icons"
LOGO_TARGETS = [ROOT / "assets" / "logo.png", ROOT / "src" / "farejador" / "web" / "static" / "logo.png"]
ICONSET_SIZES = [16, 32, 64, 128, 256, 512]


def render_png(size: int) -> Image.Image:
    """Renderiza o SVG com o Chromium do Playwright (o mesmo que o app já usa).

    O SVG vai embutido no HTML: um <img src="file://…"> numa página about:blank
    é bloqueado pelo Chromium e renderiza em branco.
    """
    svg = SVG.read_text(encoding="utf-8")
    html = f"<html><body style='margin:0;background:transparent'>{svg}</body></html>"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": size, "height": size})
        page.set_content(html)
        page.wait_for_load_state("networkidle")
        png = page.screenshot(omit_background=True)
        browser.close()
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.write(png)
    tmp.close()
    return Image.open(tmp.name).convert("RGBA")


def main() -> None:
    master = render_png(1024)
    ICONS.mkdir(parents=True, exist_ok=True)

    logo = master.resize((512, 512), Image.LANCZOS)
    for target in LOGO_TARGETS:
        logo.save(target, optimize=True)
        print(target.relative_to(ROOT))

    master.save(ICONS / "farejador.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print("packaging/icons/farejador.ico")

    if sys.platform != "darwin" or not shutil.which("iconutil"):
        print("packaging/icons/farejador.icns: pulado (precisa do iconutil do macOS)")
        return
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "farejador.iconset"
        iconset.mkdir()
        for size in ICONSET_SIZES:
            master.resize((size, size), Image.LANCZOS).save(iconset / f"icon_{size}x{size}.png")
            master.resize((size * 2, size * 2), Image.LANCZOS).save(iconset / f"icon_{size}x{size}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(ICONS / "farejador.icns")], check=True)
    print("packaging/icons/farejador.icns")


if __name__ == "__main__":
    main()
