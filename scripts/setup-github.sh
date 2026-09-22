#!/usr/bin/env bash
# Applies the GitHub settings described in GOVERNANCE.md. Idempotent: run it as
# often as you like. Requires `gh` authenticated as the maintainer.
#
# Usage: scripts/setup-github.sh [owner/repo]
set -euo pipefail
cd "$(dirname "$0")/.."

REPO="${1:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
echo "==> Repository: $REPO"

echo "==> Description, topics and merge method (squash only, delete the branch after merge)"
gh repo edit "$REPO" \
  --description "Monitora anúncios de aluguel no VivaReal e avisa quando aparece apartamento novo dentro do seu orçamento. App para macOS e Windows." \
  --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false \
  --delete-branch-on-merge --enable-issues --enable-discussions --enable-wiki=false \
  --add-topic apartamentos --add-topic aluguel --add-topic vivareal --add-topic scraper \
  --add-topic playwright --add-topic desktop-app --add-topic python --add-topic brasil >/dev/null

echo "==> Labels (the ones .github/release.yml groups release notes by)"
while IFS='|' read -r name color desc; do
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" --force >/dev/null
  echo "    $name"
done <<'EOF'
bug|d73a4a|Algo não funciona como deveria
enhancement|a2eeef|Funcionalidade ou melhoria nova
documentation|0075ca|Só documentação
good first issue|7057ff|Boa para quem está começando no projeto
help wanted|008672|O mantenedor gostaria de ajuda aqui
dependencies|0366d6|Atualização de dependência (Dependabot)
ci|e4e669|Build, release e automações
security|b60205|Vulnerabilidade ou endurecimento
breaking|d93f0b|Muda comportamento de forma incompatível
skip-changelog|cccccc|Não aparece nas notas de release
EOF

echo "==> Private vulnerability reporting (SECURITY.md)"
gh api -X PUT "repos/$REPO/private-vulnerability-reporting" --silent \
  || echo "    not available through the API; enable it in Settings → Code security → Private vulnerability reporting"

echo "==> Ruleset for the main branch (.github/rulesets/main.json)"
existing="$(gh api "repos/$REPO/rulesets" --jq '.[] | select(.name=="main") | .id' 2>/dev/null || true)"
if [ -n "$existing" ]; then
  gh api -X PUT "repos/$REPO/rulesets/$existing" --input .github/rulesets/main.json --silent \
    && echo "    updated (id $existing)"
else
  gh api -X POST "repos/$REPO/rulesets" --input .github/rulesets/main.json --silent \
    && echo "    created" \
    || echo "    FAILED: rulesets require a public repository or GitHub Pro. Make the repo public and run again."
fi

echo "==> Done. Check https://github.com/$REPO/settings/rules"
