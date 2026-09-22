#!/bin/bash
set -e

echo "==> Installing desktop dependencies..."
pip install -r requirements-desktop.txt

echo "==> Building Aluguel.app..."
pyinstaller aluguel.spec --clean --noconfirm

# Stable signature: macOS ties notification permission to the signing identity.
# PyInstaller's ad-hoc signature changes every build, and recent macOS then
# refuses UNUserNotificationCenter outright. Sign with a fixed (self-signed is
# fine) identity when one is available; fall back to ad-hoc otherwise.
SIGN_IDENTITY="${SIGN_IDENTITY:-Aluguel Dev}"
if security find-identity -v -p codesigning | grep -q "$SIGN_IDENTITY"; then
  echo "==> Signing with '$SIGN_IDENTITY'..."
  codesign --deep --force --sign "$SIGN_IDENTITY" "dist/Aluguel.app"
else
  echo "==> No '$SIGN_IDENTITY' identity found; keeping ad-hoc signature (notifications will not work)."
fi

echo "==> Creating DMG..."
hdiutil create \
  -volname "Aluguel" \
  -srcfolder "dist/Aluguel.app" \
  -ov -format UDZO \
  "dist/Aluguel.dmg"

echo ""
echo "Done! Distributable: dist/Aluguel.dmg"
echo "Users: open DMG, drag Aluguel.app to Applications."
