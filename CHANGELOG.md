# Changelog

Todas as mudanças relevantes para quem usa o Farejador ficam registradas aqui.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e as versões seguem o [SemVer](https://semver.org/lang/pt-BR/). Tipos de entrada: **Adicionado**, **Mudado**, **Corrigido**, **Removido**, **Segurança**.

## [Não lançado]

### Mudado

- O app agora se chama **Farejador de Aluguéis**: os instaladores são `Farejador.app` / `Farejador.exe` e a pasta de dados passa de `Aluguel` para `Farejador`. A pasta antiga é migrada automaticamente na primeira abertura — nada se perde.
- O scraper roda em modo *headless* com [playwright-stealth](https://github.com/AtuboDad/playwright_stealth): sem janela de navegador aparecendo e com menos bloqueios do site.
- Preço total máximo e intervalo entre buscas agora são configurados na aba **Fontes**, sem editar arquivo; valem sem reiniciar.
- A primeira busca de uma instalação nova só guarda os anúncios, sem notificar (antes chegavam dezenas de avisos de uma vez).
- A marca **SUMIU** passa a considerar o intervalo configurado (3 buscas sem ver o anúncio, mínimo 5 min) em vez de 35 minutos fixos.

### Adicionado

- Notificações nativas no macOS (o app pede permissão na primeira abertura) e o botão **Testar notificação** na aba Fontes.
- Cada instalador gerado no CI passa por um smoke test antes de ser publicado: o binário sobe, o painel responde e o `app.log` não tem erro.

- Projeto aberto no GitHub: README para quem não programa, guia de contribuição, código de conduta, política de segurança e regras de governança/merge.
- Testes automatizados (parser com cards reais do VivaReal, banco, painel, pasta de dados) e lint, rodando em Linux, macOS e Windows a cada PR.
- Releases automáticos por tag: `.dmg` para Mac Apple Silicon **e** Intel, `.exe` para Windows, com `SHA256SUMS.txt`.
- Variável de ambiente `FAREJADOR_DATA_DIR` para escolher a pasta de dados (instalações portáteis, testes).
- No app empacotado, `stdout`/`stderr` vão para `app.log` na pasta de dados — dá para diagnosticar problemas em outra máquina.

### Corrigido

- O `.app` empacotado não conseguia buscar anúncios num Mac limpo: o Chromium do Playwright agora é instalado na pasta de dados (o bundle é somente leitura) e chamado pelo driver correto (dentro do bundle, `python -m playwright` relançava o próprio app).
- `pip install -r requirements.txt` falhava no Windows e no Linux por causa do `rumps`, que só existe no macOS (hoje é opcional, só para `menubar.py`).
- O instalador do Windows não incluía os scripts do playwright-stealth.

### Removido

- Dependência `schedule`, que não era usada.

## [1.1.0] - 2026-03-03

### Adicionado

- Aba **Fontes**: cadastre, pause e remova várias URLs de busca pelo painel (antes ficavam fixas em `config.py`).

### Corrigido

- Detecção de anúncio que sumiu do site para os monitorados.

## [1.0.0] - 2026-03-03

### Adicionado

- Primeira versão: scraper do VivaReal com Playwright, banco SQLite, painel Flask com fotos e detalhes, notificações do sistema, e empacotamento como app desktop para macOS e Windows.

[Não lançado]: https://github.com/dgslv/farejador-alugueis/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/dgslv/farejador-alugueis/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/dgslv/farejador-alugueis/releases/tag/v1.0.0
