#!/usr/bin/env bash
# End-to-end local validation on macOS, the way a release should be checked before it
# is trusted: fresh venv → install → lint + tests → build the .app → launch it with an
# isolated data dir → real first scrape. Nothing touches your real data folder.
#
# Usage: scripts/validate-local.sh [search-url]      (~10 min; needs internet and the Xcode CLT)
# Env:   PYTHON=python3.12   interpreter for the venv (default: python3.11, then python3)
set -euo pipefail
cd "$(dirname "$0")/.."

SEARCH_URL="${1:-https://www.vivareal.com.br/aluguel/rj/rio-de-janeiro/zona-sul/botafogo/apartamento_residencial/}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/farejador-validate.XXXXXX")"
PY="${PYTHON:-python3.11}"
command -v "$PY" >/dev/null 2>&1 || PY=python3
step() { printf '\n==> %s\n' "$*"; }

step "1/7 fresh venv ($PY)"
"$PY" -m venv "$WORK/venv"
# shellcheck disable=SC1091
source "$WORK/venv/bin/activate"
python --version

step "2/7 install: pip install -e \".[dev,desktop]\""
pip install -q -e ".[dev,desktop]"

step "3/7 lint, format and tests"
ruff check .
ruff format --check .
pytest -q

step "4/7 CLI"
farejador --version

step "5/7 build Farejador.app and the .dmg (packaging/build-macos.sh)"
packaging/build-macos.sh
DMG="$(ls dist/Farejador-*-macOS-*.dmg | head -1)"
plutil -p dist/Farejador.app/Contents/Info.plist | grep -E "CFBundleShortVersionString|CFBundleIdentifier"

step "6/7 launch the built app with an isolated data dir"
if curl -sf -m 2 http://127.0.0.1:8080/ >/dev/null 2>&1; then
  echo "ABORT: something already answers on 127.0.0.1:8080 (is the Farejador open?)"
  exit 2
fi
export FAREJADOR_DATA_DIR="$WORK/data"
dist/Farejador.app/Contents/MacOS/Farejador &
APP_PID=$!
trap 'kill $APP_PID 2>/dev/null || true' EXIT
for _ in $(seq 1 60); do curl -sf http://127.0.0.1:8080/sources >/dev/null && break; sleep 2; done
curl -sf http://127.0.0.1:8080/sources | grep -q 'name="interval_seconds"' && echo "dashboard up"
curl -s -o /dev/null -w "add source -> HTTP %{http_code}\n" -X POST \
  --data-urlencode "url=$SEARCH_URL" --data-urlencode "label=validacao" http://127.0.0.1:8080/sources/add

step "7/7 first scrape (downloads Chromium on first run; up to 10 min)"
for _ in $(seq 1 120); do
  grep -qE "Checked [0-9]+ listings|ERROR fetching" "$WORK/data/app.log" 2>/dev/null && break
  sleep 5
done
grep -E "Checked [0-9]+ listings|ERROR fetching|Traceback" "$WORK/data/app.log" | tail -3 \
  || { echo "FAIL: no scrape result in app.log"; exit 1; }
grep -qE "Checked [1-9][0-9]* listings" "$WORK/data/app.log" || { echo "FAIL: the scrape found no listings"; exit 1; }
grep -q "Traceback" "$WORK/data/app.log" && { echo "FAIL: traceback in app.log"; exit 1; }

echo
echo "ALL GOOD"
echo "  installer: $DMG"
echo "  data dir (temporary, delete when done): $WORK/data"
