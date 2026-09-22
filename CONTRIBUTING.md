# Contribuindo

Obrigado pelo interesse! Este guia mostra como montar o ambiente, rodar os testes e abrir um pull request que passe de primeira. As regras de quem aprova e faz merge estão em [GOVERNANCE.md](GOVERNANCE.md); as de convivência, em [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Formas de contribuir

- **Relatar um problema** → [abrir issue](https://github.com/dgslv/farejador-alugueis/issues/new/choose). O template pede o `app.log`; ele resolve metade dos casos.
- **Sugerir uma funcionalidade** → issue também. Conte o problema que você quer resolver, não só a solução.
- **Revisar pull requests** → qualquer pessoa pode. Testar um PR na sua máquina e contar o resultado é uma contribuição valiosa.
- **Documentação** → README, docs/, textos do app. Erro de digitação conta.
- **Código** → correções, funcionalidades, testes. Para mudanças grandes, abra uma issue antes de codar, para alinhar a abordagem e não perder trabalho.

## Ambiente de desenvolvimento

Requisitos: Python 3.9+ (o CI e os instaladores usam **3.11** — prefira essa), Git.

```bash
git clone https://github.com/<seu-usuario>/farejador-alugueis.git   # seu fork
cd farejador-alugueis
python -m venv .venv && source .venv/bin/activate                   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # o pacote em modo editável + pytest, ruff, pre-commit
playwright install chromium        # navegador usado pelo scraper (~150 MB)
pre-commit install                 # roda lint e formatação em cada commit
```

O código fica em `src/farejador/` (layout `src/`, o recomendado pela PyPA), os testes em `tests/`, o empacotamento em `packaging/` e as ferramentas de mantenedor em `scripts/`.

Rodando (`python -m farejador` é o mesmo que `farejador`):

| Comando | O que faz |
|---|---|
| `farejador` | App completo em janela nativa (o que o instalador entrega) |
| `farejador --headless` | Só o robô de busca, no terminal |
| `farejador --dashboard` | Só o painel, em <http://127.0.0.1:8080> no seu navegador |

Para não misturar com os seus dados de uso real, aponte a pasta de dados para outro lugar (e a porta, se a 8080 estiver ocupada):

```bash
FAREJADOR_DATA_DIR=/tmp/farejador-dev FAREJADOR_PORT=8090 farejador
```

Como cada peça se encaixa: [docs/como-funciona.md](docs/como-funciona.md).

## Testes

```bash
pytest            # a suíte inteira, ~1 s, sem rede e sem navegador
ruff check .      # lint (ruff check --fix corrige o que dá)
ruff format .     # formatação (o CI confere com --check)
```

O que esperamos de um PR com código:

- **Teste para o caminho feliz e para cada forma de falhar.** Entrada vazia, valor fora do limite, arquivo ausente, site que mudou o formato — se a sua mudança pode quebrar de um jeito, tem um teste mostrando o que acontece nesse jeito.
- **Dados reais em vez de inventados** quando o comportamento depende do conteúdo. Os testes do parser usam cards copiados do VivaReal (`tests/data.py`). Capturou um card diferente? Cole o texto sem retocar.
- **Prove que o teste pega o bug.** Ao corrigir algo, escreva o teste antes, veja-o falhar, depois corrija. Diga no PR o que ficou de fora ("não testei X porque…").
- A suíte **nunca toca a pasta de dados real**: `tests/conftest.py` aponta `FAREJADOR_DATA_DIR` para uma pasta temporária. Mantenha assim.

Um teste marcado com `xfail(strict=True)` documenta um bug conhecido: ele *deve* falhar até o bug ser corrigido. Corrigiu? Remova a marca no mesmo PR.

## Estilo

- **Lint e formatação**: `ruff check` e `ruff format`, com as regras em [`pyproject.toml`](pyproject.toml). O CI roda os mesmos comandos; se passa local, passa lá.
- **Sem `print`**: use `logging` (`log = logging.getLogger(__name__)`); no app empacotado tudo vai para o `app.log`.
- **Textos do app e documentação em português**; identificadores, comentários de código e mensagens de commit em inglês (é o que o código já faz).
- **Comentários explicam o porquê**, não o quê. O código já diz o quê.
- **Mudança cirúrgica.** Toque só no que a sua mudança exige; não reformate código vizinho. Achou algo errado por perto? Abra uma issue ou um PR separado.
- Sem dependência nova sem conversa na issue. Cada uma vai parar dentro do instalador.

## Commits e branches

Usamos [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/): `tipo: descrição curta no imperativo`.

| Tipo | Quando |
|---|---|
| `feat` | funcionalidade nova visível para quem usa |
| `fix` | correção de bug |
| `docs` | só documentação |
| `test` | só testes |
| `build` | empacotamento, dependências, specs do PyInstaller |
| `ci` | workflows do GitHub Actions |
| `refactor` | muda a estrutura sem mudar o comportamento |
| `chore` | manutenção que não se encaixa acima |

Branch a partir de `main`, nome `tipo/descricao-curta` (ex. `fix/preco-com-centavos`). Um PR = uma mudança; se são duas coisas, são dois PRs.

## Abrindo o pull request

1. Confira `ruff check .` e `pytest` localmente.
2. Se a mudança afeta quem usa o app, adicione uma linha na seção **Não lançado** do [`CHANGELOG.md`](CHANGELOG.md).
3. Abra o PR contra `main` e preencha o template (o que muda, como testar, checklist). O **título** segue o formato de commit — ele vira a mensagem do commit no squash.
4. O CI roda lint e testes em Linux, macOS e Windows. Vermelho? Clique no check para ver o log.
5. Alguém — talvez o mantenedor, talvez outra pessoa — vai revisar. Responda aos comentários com commits novos (não reescreva o histórico da branch durante a revisão; fica mais fácil acompanhar).
6. Com CI verde e aprovação do mantenedor, ele faz o merge. A branch é apagada automaticamente.

**Mexeu em empacotamento** (`packaging/**`, `pyproject.toml`, `src/farejador/desktop.py`, `__main__.py`)? O workflow *Release* roda automaticamente no seu PR e deixa os instaladores dos três sistemas como artefatos (aba *Actions* → o run do seu PR → *Artifacts*). Baixe o do seu sistema, instale e conte no PR o que aconteceu — isso é o que valida a mudança, não o build ter ficado verde.

## Revisando o PR de outra pessoa

Não precisa de permissão. O que mais ajuda:

- Rodar a branch e dizer o que aconteceu, em qual sistema.
- Apontar cenários que a mudança não cobre ("e se a URL tiver espaço?").
- Sugerir simplificações. O melhor PR é o menor que resolve o problema.

Seja específico e gentil — do outro lado tem uma pessoa que gastou o tempo livre dela nisso.
