#!/bin/bash
set -e

echo "==> Installing desktop dependencies..."
pip install -r requirements-desktop.txt

echo "==> Building Aluguel.app..."
pyinstaller aluguel.spec --clean --noconfirm

echo "==> Creating DMG..."
hdiutil create \
  -volname "Aluguel" \
  -srcfolder "dist/Aluguel.app" \
  -ov -format UDZO \
  "dist/Aluguel.dmg"

echo ""
echo "Done! Distributable: dist/Aluguel.dmg"
echo "Users: open DMG, drag Aluguel.app to Applications."
