# Como funciona

Um app desktop em Python, sem servidor: um agendador dispara o scraper, que lê o VivaReal com um navegador headless e grava num SQLite; um painel Flask mostra o banco dentro de uma janela nativa. Tudo cabe num único processo.

```
app.py ─┬─ thread: dashboard.py (Flask em 127.0.0.1:8080)
        ├─ thread: main.py     (agendador → scraper.py → storage.py → notifier.py)
        └─ janela pywebview apontando para o Flask
```

## As peças

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Ponto de entrada do app desktop. Sobe o Flask e o agendador em threads, abre a janela (pywebview). Na primeira execução instala o Chromium do Playwright na pasta de dados, mostrando uma tela de progresso. No app empacotado, redireciona stdout/stderr para `app.log`. |
| `main.py` | O agendador. `run_once()` faz uma rodada completa; `run_forever()` repete a cada `interval_seconds` (lido do banco a cada tique, então mudar no painel vale sem reiniciar). Pode rodar sozinho no terminal. |
| `scraper.py` | Abre cada fonte no Chromium (headless, com [playwright-stealth](https://github.com/AtuboDad/playwright_stealth)), rola a página para carregar os cards, segue a paginação até `MAX_PAGES` e converte cada card em um dicionário de anúncio. Só ele fala com a rede. |
| `storage.py` | Tudo que toca o SQLite: anúncios, fontes (URLs de busca) e configurações. Migrações são `ALTER TABLE` tolerantes — rodar de novo não quebra. |
| `dashboard.py` | O painel: Flask com o HTML dentro de strings Python (sem build de frontend). Abas Apartamentos e Fontes, modal de detalhes, lightbox de fotos, atualização automática via `/fragment`. |
| `notifier.py` | Notificação do sistema (plyer; no macOS cai para `osascript` se o plyer falhar) e o `alerts.log`. |
| `config.py` | Pasta de dados por sistema (com migração da pasta antiga "Aluguel" e a variável `FAREJADOR_DATA_DIR`), caminhos, valores padrão e o nome do app. |
| `version.py` | `__version__`, lido pelos specs do PyInstaller e pelo workflow de release. |
| `menubar.py` | Extra opcional para macOS: ícone na barra de menus com o status do scraper. Precisa de `pip install rumps` e lê um `scraper.log` na pasta do projeto (`python main.py | tee scraper.log`). Não vai no instalador. |

## Uma rodada, passo a passo

1. `main.run_once()` lê as fontes ativas e o teto de preço no banco.
2. `scraper.fetch_listings(urls)` abre um Chromium, e para cada fonte:
   - carrega a página (`domcontentloaded` — o VivaReal nunca chega a *networkidle* por causa dos rastreadores) e espera o primeiro card `li[data-cy="rp-property-cd"]`;
   - rola em passos de 400 px até a contagem de cards estabilizar (lazy-load);
   - para cada card, lê o `href` e o `inner_text` e extrai id, quartos, área e preço do slug da URL; preço mensal, condomínio, IPTU, bairro e rua do texto (regex em `scraper.py`); e as URLs das fotos;
   - cards de "várias unidades" não têm link direto: o scraper clica, lê o link de aluguel no modal e fecha com Esc;
   - segue o link "próxima página" enquanto existir, até `MAX_PAGES` (5). Uma página que falha encerra a paginação daquela fonte sem perder o que já veio.
3. De volta em `main`, cada anúncio com `preço + condomínio + IPTU ≤ teto` é salvo. Se é novo, dispara notificação e vai para `alerts.log`; se já existia, só atualiza `last_seen_at`.
4. Anúncios **monitorados** (botão *Monitorar* no painel) que não apareceram nesta rodada são registrados no log; o painel os marca como **SUMIU** quando `last_seen_at` passa de 35 minutos.

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
| `last_seen_at` | Última rodada em que apareceu — define **SUMIU** para monitorados |
| `checked`, `checked_at` | Marcado como visto no painel |
| `tracked` | Monitorado (favorito) |

**`sources`** — `url` (única), `label`, `active`, `added_at`.

**`settings`** — chave/valor: `max_total_price`, `interval_seconds`. Os padrões estão em `config.py` e valem quando a chave não existe ou está corrompida.

## Empacotamento

- PyInstaller, um spec por sistema (`farejador-macos.spec` → `Farejador.app` dentro de um `.dmg`; `farejador-windows.spec` → `Farejador.exe` de arquivo único). Ambos leem a versão de `version.py`.
- O **Chromium não vai no instalador** (seriam +150 MB e a pasta do bundle é somente leitura). `app.py` aponta `PLAYWRIGHT_BROWSERS_PATH` para a pasta de dados e instala na primeira execução chamando o driver do Playwright direto (`node cli.js install chromium`) — chamar `sys.executable -m playwright` dentro do bundle relançaria o próprio app.
- Os instaladores são gerados pelo GitHub Actions ([release.yml](../.github/workflows/release.yml)) a partir dos mesmos scripts que rodam localmente (`scripts/build-*`). Não são assinados — daí os avisos do Gatekeeper e do SmartScreen documentados no README.

## Decisões de projeto

- **SQLite + Flask + pywebview, sem servidor.** O usuário instala um arquivo e pronto; não existe conta, custo de hospedagem nem dado saindo da máquina. O preço é que o app precisa ficar aberto para vigiar.
- **HTML em strings Python.** Evita toolchain de frontend (Node, bundler) num projeto que uma pessoa mantém. Fica feio de ler em `dashboard.py`; se o painel crescer, o caminho natural é mover para templates Jinja em `templates/`.
- **Parser por regex sobre o texto do card**, não sobre a estrutura do HTML: a estrutura muda com mais frequência do que o texto que o usuário vê. Quando mudar, os testes em `tests/test_scraper_parse.py` (com cards reais) mostram exatamente o que quebrou.
- **Módulos soltos na raiz.** Herança de quando era um script. Uma migração para `src/farejador/` está planejada; até lá, os imports são simples e o PyInstaller feliz.
