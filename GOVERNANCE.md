# Governança

Como as decisões são tomadas e — principalmente — **quem pode fazer merge, e sob quais condições**.

## Papéis

| Papel | Quem | O que faz |
|---|---|---|
| **Mantenedor** | [@dgslv](https://github.com/dgslv) (Diego Silva) | Define o rumo do projeto, revisa, aprova, faz merge e publica releases. É a única pessoa com permissão de escrita no repositório. |
| **Revisor** | Qualquer pessoa | Lê pull requests, testa, comenta, aprova ou pede mudanças. Não precisa de convite. |
| **Contribuidor** | Qualquer pessoa | Abre issues e pull requests a partir de um fork. |

O projeto segue o modelo de **mantenedor único**: a discussão é aberta e acontece nas issues e nos PRs; a palavra final é do mantenedor, que registra o motivo da decisão no próprio PR ou issue. É o modelo da maioria dos projetos de uma pessoa no GitHub e o que o Python usou nos seus primeiros vinte anos (o "BDFL"). Se o projeto crescer a ponto de precisar de mais mantenedores, este documento muda primeiro.

## Regras de merge

1. **Toda mudança em `main` entra por pull request.** Ninguém faz push direto — nem o mantenedor. Não existe força maior: hotfix também é PR.
2. **Qualquer pessoa pode revisar.** Revisões de fora são bem-vindas, contam para a decisão e são a melhor forma de ganhar confiança no projeto. Uma aprovação externa, porém, não destrava o merge sozinha.
3. **Só o mantenedor faz merge.** Nenhuma outra conta tem esse poder, e o botão só aparece quando as condições abaixo forem atendidas.
4. **Condições para o merge de um PR de contribuidor:**
   - CI verde: `lint` e `test` nos três sistemas (Linux, macOS, Windows), rodando sobre a versão mais recente da branch;
   - revisão **aprovada pelo mantenedor** — obrigatória pelo `CODEOWNERS`; aprovações anteriores caem se o autor enviar novos commits;
   - todas as conversas do PR resolvidas;
   - título no formato `tipo: descrição` (ele vira a mensagem do commit) e, quando a mudança afeta quem usa o app, uma linha no `CHANGELOG.md`.
5. **PRs do próprio mantenedor** seguem as mesmas condições, exceto a aprovação de uma segunda pessoa, que não é exigida (o mantenedor usa o *bypass* de administrador, válido apenas para PRs). Em troca: PRs grandes ou que mudam comportamento ficam abertos por pelo menos 24 h para comentários, e revisões externas são encorajadas.
6. **Método: squash merge.** Um PR vira um commit em `main`; o histórico é linear. A branch é apagada após o merge.
7. **`main` não aceita force push nem pode ser apagada.**

## Como as regras são garantidas (não é só combinado)

| Regra | Mecanismo |
|---|---|
| Só o mantenedor faz merge | Só o mantenedor tem acesso de escrita; contribuidores trabalham em forks. |
| Aprovação do mantenedor obrigatória | [`.github/CODEOWNERS`](.github/CODEOWNERS): `* @dgslv` + regra *require code owner review*. |
| PR obrigatório, sem force push, sem apagar `main`, squash apenas, CI obrigatório | Ruleset da branch `main`, versionado em [`.github/rulesets/main.json`](.github/rulesets/main.json) e aplicado por [`scripts/setup-github.sh`](scripts/setup-github.sh). |
| CI verde | Jobs `lint` e `test (…)` de [`.github/workflows/ci.yml`](.github/workflows/ci.yml) são *required status checks*. |

Mudou o ruleset no GitHub sem passar pelo JSON? Rode `scripts/setup-github.sh` — ele reaplica o arquivo e o repositório volta ao que está documentado aqui.

## Releases

Só o mantenedor cria tags e publica releases. O processo — versão, changelog, tag, instaladores gerados pelo CI — está em [docs/releasing.md](docs/releasing.md).

## Mudanças nesta governança

Por pull request neste arquivo, aberto por pelo menos **7 dias** para comentários antes do merge.

## Sucessão

Se o mantenedor ficar sem responder por mais de 6 meses, quem quiser continuar o projeto deve abrir uma issue dizendo isso. O mantenedor pode transferir o repositório ou nomear novos mantenedores; sem resposta, a licença MIT garante que um fork pode seguir em frente com outro nome.
