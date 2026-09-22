#!/usr/bin/env python3
"""Gera os ícones do app a partir de assets/farejador.svg.

Saídas (todas versionadas, para o build não depender deste script):
  assets/logo.png           512 px — README e painel
  assets/farejador.ico      Windows (16–256 px)
  assets/farejador.icns     macOS (só roda no macOS: usa o iconutil do sistema)

Requer: pip install playwright pillow  +  playwright install chromium
Uso:    python scripts/make-icons.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SVG = ASSETS / "farejador.svg"
ICONSET_SIZES = [16, 32, 64, 128, 256, 512, 1024]


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

    master.resize((512, 512), Image.LANCZOS).save(ASSETS / "logo.png", optimize=True)
    print("assets/logo.png")

    master.save(
        ASSETS / "farejador.ico",
        sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)],
    )
    print("assets/farejador.ico")

    if sys.platform != "darwin" or not shutil.which("iconutil"):
        print("assets/farejador.icns: pulado (precisa do iconutil do macOS)")
        return
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "farejador.iconset"
        iconset.mkdir()
        for size in ICONSET_SIZES[:-1]:
            master.resize((size, size), Image.LANCZOS).save(iconset / f"icon_{size}x{size}.png")
            master.resize((size * 2, size * 2), Image.LANCZOS).save(iconset / f"icon_{size}x{size}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(ASSETS / "farejador.icns")], check=True)
    print("assets/farejador.icns")


if __name__ == "__main__":
    main()
