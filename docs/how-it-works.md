# Como funciona

Um app desktop em Python, sem servidor: um agendador dispara o scraper, que lê o VivaReal com um navegador headless e grava num SQLite; um painel Flask mostra o banco dentro de uma janela nativa. Tudo cabe num único processo.

```
farejador (__main__.py) ─┬─ thread: web/ (Flask em 127.0.0.1:8080)
                         ├─ thread: scheduler.py (→ scrapers/vivareal.py → db.py → notify.py)
                         └─ janela pywebview apontando para o Flask        (desktop.py)
```

## As peças

Tudo vive no pacote `src/farejador/`; `pip install -e .` deixa `farejador` e `python -m farejador` disponíveis.

| Arquivo | Responsabilidade |
|---|---|
| `__main__.py` | A porta de entrada única: `farejador` (desktop), `--headless` (só o robô), `--dashboard` (só o painel), `--version`. |
| `desktop.py` | O app desktop. Sobe o Flask e o agendador em threads, abre a janela (pywebview). Na primeira execução instala o Chromium do Playwright na pasta de dados, mostrando uma tela de progresso. No app empacotado, o log vai para `app.log`. |
| `scheduler.py` | O agendador. `run_once()` faz uma rodada completa; `run_forever()` repete a cada `interval_seconds` (lido do banco a cada tique, então mudar no painel vale sem reiniciar). |
| `scrapers/vivareal.py` | Abre cada fonte no Chromium (headless, com [playwright-stealth](https://github.com/AtuboDad/playwright_stealth)), rola a página para carregar os cards, segue a paginação até `MAX_PAGES` e converte cada card em um dicionário de anúncio. Só ele fala com a rede. Um segundo portal entra como outro módulo em `scrapers/`. |
| `db.py` | Tudo que toca o SQLite: anúncios, fontes (URLs de busca) e configurações. Migrações são `ALTER TABLE` tolerantes — rodar de novo não quebra. |
| `web/` | O painel: `create_app()` (Flask), rotas em `routes.py`, HTML em `templates/` (Jinja), CSS/JS/logo em `static/`. Abas Apartamentos e Fontes, modal de detalhes, lightbox de fotos, atualização automática via `/fragment`. |
| `notify.py` | Notificação do sistema e o `alerts.log`. No `.app` do macOS usa o `UNUserNotificationCenter` nativo (pede permissão na primeira abertura); rodando do código-fonte no macOS cai para `osascript`; no Windows/Linux usa o plyer. O botão *Testar notificação* da aba Fontes chama a mesma função. |
| `paths.py` | Pasta de dados por sistema (com migração da pasta antiga "Aluguel" e a variável `FAREJADOR_DATA_DIR`) e os caminhos de banco, logs e Chromium. Tudo calculado na hora — importar não cria nada. |
| `config.py` | Constantes: nome do app, host/porta do painel (`FAREJADOR_PORT`), padrões de intervalo e preço, user agent. |
| `logging_setup.py` | `logging` para o terminal (código-fonte) ou para o `app.log` (app empacotado). |
| `__init__.py` | `__version__`, lido pelo `pyproject.toml`, pelos specs do PyInstaller e pelo workflow de release. |

## Uma rodada, passo a passo

1. `scheduler.run_once()` lê as fontes ativas e o teto de preço no banco.
2. `scrapers.vivareal.fetch_listings(urls)` abre um Chromium, e para cada fonte:
   - carrega a página (`domcontentloaded` — o VivaReal nunca chega a *networkidle* por causa dos rastreadores) e espera o primeiro card `li[data-cy="rp-property-cd"]`;
   - rola em passos de 400 px até a contagem de cards estabilizar (lazy-load);
   - para cada card, lê o `href` e o `inner_text` e extrai id, quartos, área e preço do slug da URL; preço mensal, condomínio, IPTU, bairro e rua do texto (regex em `scrapers/vivareal.py`); e as URLs das fotos;
   - cards de "várias unidades" não têm link direto: o scraper clica, lê o link de aluguel no modal e fecha com Esc;
   - segue o link "próxima página" enquanto existir, até `MAX_PAGES` (5). Uma página que falha encerra a paginação daquela fonte sem perder o que já veio.
3. De volta no `scheduler`, cada anúncio com `preço + condomínio + IPTU ≤ teto` é salvo. Se é novo, dispara notificação e vai para `alerts.log`; se já existia, só atualiza `last_seen_at`. Com o banco vazio (primeira rodada) tudo é salvo em silêncio — senão seriam dezenas de notificações de uma vez.
4. Anúncios **monitorados** (botão *Monitorar* no painel) que não apareceram nesta rodada são registrados no log; o painel os marca como **SUMIU** quando `last_seen_at` fica mais velho que 3 intervalos de busca (mínimo 5 min), para que uma única página que falhou não dispare o alarme.

Pausas aleatórias de 1,5–3 s entre páginas, user agent de desktop comum e o modo stealth são o que mantém o robô discreto. O intervalo padrão de 15 minutos é deliberadamente conservador — ver "Aviso legal" no README.

## O banco (`listings.db`)

**`listings`** — um registro por anúncio, chave `id` (o número no fim da URL do VivaReal).

| Coluna | Significado |
|---|---|
| `url`, `title` | URL sem query string; texto completo do card (o painel extrai a primeira linha útil) |
| `price`, `condo`, `iptu` | Inteiros em reais. `total` no painel é a soma |
| `area`, `bedrooms` | Do slug da URL; 0 quando ausente |
| `street`, `neighborhood`, `images` (JSON) | Do texto/fotos do card |
| `seen_at` | Primeira vez que apareceu — define a marca **novo** (últimas 24 h e não visto) |
| `last_seen_at` | Última rodada em que apareceu — define **SUMIU** para monitorados (mais velho que 3 intervalos, mínimo 5 min) |
| `checked`, `checked_at` | Marcado como visto no painel |
| `tracked` | Monitorado (favorito) |

**`sources`** — `url` (única), `label`, `active`, `added_at`.

**`settings`** — chave/valor: `max_total_price`, `interval_seconds`. Os padrões estão em `config.py` e valem quando a chave não existe ou está corrompida.

## Empacotamento

- Tudo em `packaging/`: PyInstaller, um spec por sistema (`farejador-macos.spec` → `Farejador.app` dentro de um `.dmg`; `farejador-windows.spec` → `Farejador.exe` de arquivo único), os scripts `build-macos.sh` / `build-windows.bat` e os ícones. Os specs leem a versão de `src/farejador/__init__.py` e levam `web/templates` e `web/static` como dados do pacote.
- **Logo e ícones**: `assets/farejador.svg` é a fonte; `packaging/make-icons.py` gera `assets/logo.png` (README), `src/farejador/web/static/logo.png` (painel e favicon — dado do pacote, funciona igual do código-fonte, via pip ou dentro do instalador), `packaging/icons/farejador.icns` (macOS) e `packaging/icons/farejador.ico` (Windows). Todos versionados, para o build não depender do script.
- O **Chromium não vai no instalador** (seriam +150 MB e a pasta do bundle é somente leitura). `app.py` aponta `PLAYWRIGHT_BROWSERS_PATH` para a pasta de dados e instala na primeira execução chamando o driver do Playwright direto (`node cli.js install chromium`) — chamar `sys.executable -m playwright` dentro do bundle relançaria o próprio app.
- Os instaladores são gerados pelo GitHub Actions ([release.yml](../.github/workflows/release.yml)) a partir dos mesmos scripts que rodam localmente (`packaging/build-*`), e cada build passa por um smoke test: o binário sobe, o painel responde e o `app.log` não tem traceback. Não são assinados com identidade da Apple — daí os avisos do Gatekeeper e do SmartScreen documentados no README.
- O macOS amarra a permissão de notificações à identidade de assinatura, e a assinatura ad-hoc do PyInstaller muda a cada build. `packaging/build-macos.sh` assina com uma identidade fixa (`SIGN_IDENTITY`, padrão `Farejador Dev`, autoassinada serve) quando ela existe na máquina; no CI não existe, então o build fica ad-hoc.

## Decisões de projeto

- **SQLite + Flask + pywebview, sem servidor.** O usuário instala um arquivo e pronto; não existe conta, custo de hospedagem nem dado saindo da máquina. O preço é que o app precisa ficar aberto para vigiar.
- **Jinja + CSS/JS estáticos, sem build de frontend.** O painel é HTML servido pelo Flask com templates em `web/templates/` e arquivos em `web/static/`; nada de Node ou bundler num projeto que uma pessoa mantém. Se o painel crescer muito, o caminho natural é um framework leve no lado do navegador — não antes.
- **Parser por regex sobre o texto do card**, não sobre a estrutura do HTML: a estrutura muda com mais frequência do que o texto que o usuário vê. Quando mudar, os testes em `tests/test_scraper_parse.py` (com cards reais) mostram exatamente o que quebrou.
- **Layout `src/` e uma porta de entrada.** O pacote `farejador` é instalável (`pip install -e .`), os testes rodam contra o pacote instalado e o PyInstaller parte do mesmo `__main__.py` que o comando `farejador` usa — o que o instalador entrega é o que o desenvolvedor roda.
