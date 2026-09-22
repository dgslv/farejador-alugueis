#!/usr/bin/env python3
"""Imprime a seção de uma versão do CHANGELOG.md (o workflow Release usa como notas).

Uso: python scripts/changelog_section.py 2.0.0   (ou v2.0.0)
"""

import re
import sys
from pathlib import Path


def section(changelog: str, version: str) -> str:
    version = version.lstrip("v")
    m = re.search(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        changelog,
        re.MULTILINE | re.DOTALL,
    )
    return m.group(1).strip() if m else ""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("uso: changelog_section.py <versão>")
    text = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
    body = section(text, sys.argv[1])
    print(body or f"Veja o CHANGELOG.md para a versão {sys.argv[1]}.")
