#!/usr/bin/env bash
# Gera Farejador.app e o .dmg em dist/ (na raiz do repo). Usado localmente e pelo
# workflow Release. Requer Python 3.11+ e Xcode Command Line Tools (hdiutil).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Instalando o pacote e as dependências de empacotamento..."
python3 -m pip install -e ".[desktop]"

VERSION="$(python3 -c 'from farejador import __version__; print(__version__)')"
ARCH="$(uname -m)"   # arm64 (Apple Silicon) ou x86_64 (Intel)
DMG="dist/Farejador-${VERSION}-macOS-${ARCH}.dmg"

echo "==> Gerando Farejador.app (v${VERSION}, ${ARCH})..."
pyinstaller packaging/farejador-macos.spec --clean --noconfirm

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
# "hdiutil: create failed - Resource busy" acontece de vez em quando (Spotlight ou
# outro processo tocando a pasta), principalmente nos runners do GitHub. Tentar de
# novo resolve; três tentativas com pausa.
for attempt in 1 2 3; do
  if hdiutil create \
       -volname "Farejador" \
       -srcfolder "dist/Farejador.app" \
       -ov -format UDZO \
       "$DMG"; then
    break
  fi
  if [ "$attempt" -eq 3 ]; then
    echo "hdiutil falhou 3 vezes" >&2
    exit 1
  fi
  echo "==> hdiutil falhou (tentativa $attempt); esperando 10 s e tentando de novo..."
  sleep 10
done

echo
echo "Pronto: $DMG"
echo "Usuários: abrir o .dmg e arrastar Farejador.app para Aplicativos."
