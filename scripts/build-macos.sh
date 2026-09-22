#!/usr/bin/env bash
# Gera Farejador.app e o .dmg em dist/. Usado localmente e pelo workflow Release.
# Requer Python 3.11+ e Xcode Command Line Tools (hdiutil).
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="$(python3 -c 'from version import __version__; print(__version__)')"
ARCH="$(uname -m)"   # arm64 (Apple Silicon) ou x86_64 (Intel)
DMG="dist/Farejador-${VERSION}-macOS-${ARCH}.dmg"

echo "==> Instalando dependências de empacotamento..."
python3 -m pip install -r requirements-desktop.txt

echo "==> Gerando Farejador.app (v${VERSION}, ${ARCH})..."
pyinstaller farejador-macos.spec --clean --noconfirm

# Assinatura estável: o macOS amarra a permissão de notificações à identidade de
# assinatura. A assinatura ad-hoc do PyInstaller muda a cada build, e o macOS
# recente então recusa o UNUserNotificationCenter. Assine com uma identidade fixa
# (autoassinada serve) quando existir; senão fica a ad-hoc.
SIGN_IDENTITY="${SIGN_IDENTITY:-Farejador Dev}"
if security find-identity -v -p codesigning | grep -q "$SIGN_IDENTITY"; then
  echo "==> Assinando com '$SIGN_IDENTITY'..."
  codesign --deep --force --sign "$SIGN_IDENTITY" "dist/Farejador.app"
else
  echo "==> Identidade '$SIGN_IDENTITY' não encontrada; mantendo assinatura ad-hoc (notificações nativas não funcionam)."
fi

echo "==> Criando ${DMG}..."
hdiutil create \
  -volname "Farejador" \
  -srcfolder "dist/Farejador.app" \
  -ov -format UDZO \
  "$DMG"

echo
echo "Pronto: $DMG"
echo "Usuários: abrir o .dmg e arrastar Farejador.app para Aplicativos."
