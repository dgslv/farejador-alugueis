#!/usr/bin/env bash
# Aplica no GitHub as configurações descritas em GOVERNANCE.md. Idempotente:
# pode rodar quantas vezes quiser. Requer `gh` autenticado como o mantenedor.
#
# Uso: scripts/setup-github.sh [dono/repo]
set -euo pipefail
cd "$(dirname "$0")/.."

REPO="${1:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
echo "==> Repositório: $REPO"

echo "==> Descrição, tópicos e método de merge (só squash, apaga a branch após o merge)"
gh repo edit "$REPO" \
  --description "Monitora anúncios de aluguel no VivaReal e avisa quando aparece apartamento novo dentro do seu orçamento. App para macOS e Windows." \
  --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false \
  --delete-branch-on-merge --enable-issues --enable-discussions --enable-wiki=false \
  --add-topic apartamentos --add-topic aluguel --add-topic vivareal --add-topic scraper \
  --add-topic playwright --add-topic desktop-app --add-topic python --add-topic brasil >/dev/null

echo "==> Labels (as usadas em .github/release.yml)"
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

echo "==> Relato privado de vulnerabilidades (SECURITY.md)"
gh api -X PUT "repos/$REPO/private-vulnerability-reporting" --silent \
  || echo "    indisponível pela API; ative em Settings → Code security → Private vulnerability reporting"

echo "==> Ruleset da branch main (.github/rulesets/main.json)"
existing="$(gh api "repos/$REPO/rulesets" --jq '.[] | select(.name=="main") | .id' 2>/dev/null || true)"
if [ -n "$existing" ]; then
  gh api -X PUT "repos/$REPO/rulesets/$existing" --input .github/rulesets/main.json --silent \
    && echo "    atualizado (id $existing)"
else
  gh api -X POST "repos/$REPO/rulesets" --input .github/rulesets/main.json --silent \
    && echo "    criado" \
    || echo "    FALHOU: rulesets exigem repositório público ou GitHub Pro. Torne o repo público e rode de novo."
fi

echo "==> Pronto. Confira em https://github.com/$REPO/settings/rules"
