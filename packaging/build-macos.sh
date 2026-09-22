#!/usr/bin/env bash
# Builds Farejador.app and the .dmg into dist/ (at the repo root). Used locally and
# by the Release workflow. Requires Python 3.11+ and the Xcode Command Line Tools (hdiutil).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Installing the package and the packaging dependencies..."
python3 -m pip install -e ".[desktop]"

VERSION="$(python3 -c 'from farejador import __version__; print(__version__)')"
ARCH="$(uname -m)"   # arm64 (Apple Silicon) or x86_64 (Intel)
DMG="dist/Farejador-${VERSION}-macOS-${ARCH}.dmg"

echo "==> Building Farejador.app (v${VERSION}, ${ARCH})..."
pyinstaller packaging/farejador-macos.spec --clean --noconfirm

# Stable signature: macOS ties the notification permission to the signing identity.
# PyInstaller's ad-hoc signature changes on every build, and recent macOS then
# refuses UNUserNotificationCenter outright. Sign with a fixed (self-signed is
# fine) identity when one is available; fall back to ad-hoc otherwise.
SIGN_IDENTITY="${SIGN_IDENTITY:-Farejador Dev}"
if security find-identity -v -p codesigning | grep -q "$SIGN_IDENTITY"; then
  echo "==> Signing with '$SIGN_IDENTITY'..."
  codesign --deep --force --sign "$SIGN_IDENTITY" "dist/Farejador.app"
else
  echo "==> No '$SIGN_IDENTITY' identity found; keeping the ad-hoc signature (native notifications will not work)."
fi

echo "==> Creating ${DMG}..."
# "hdiutil: create failed - Resource busy" happens now and then (Spotlight or another
# process touching the folder), mostly on GitHub runners. Retrying fixes it: three
# attempts with a pause.
for attempt in 1 2 3; do
  if hdiutil create \
       -volname "Farejador" \
       -srcfolder "dist/Farejador.app" \
       -ov -format UDZO \
       "$DMG"; then
    break
  fi
  if [ "$attempt" -eq 3 ]; then
    echo "hdiutil failed 3 times" >&2
    exit 1
  fi
  echo "==> hdiutil failed (attempt $attempt); waiting 10 s and retrying..."
  sleep 10
done

echo
echo "Done: $DMG"
echo "Users: open the .dmg and drag Farejador.app to Applications."
