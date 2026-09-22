# <img src="assets/logo.png" width="40" alt=""> Farejador de Aluguéis

> *"Rental sniffer"* — a desktop app that watches your [VivaReal](https://www.vivareal.com.br) (Brazil's main rental listings site) searches and notifies you the moment a new apartment shows up within your total budget (rent + condo fee + property tax).

**The full documentation is in Portuguese** — the app targets people renting in Brazil — starting at [README.md](README.md). This page is a short orientation for English-speaking contributors.

## What it does

- Every N minutes (default 15) it opens each saved search in a headless Chromium (Playwright + stealth), parses the listing cards and stores them in a local SQLite database.
- New listings under your budget trigger a system notification and are flagged **NOVO** in the dashboard.
- Mark listings as seen, track favourites, and get told when a tracked listing disappears from the site.
- Everything runs locally. No server, no account, no data leaves the machine.

Installers for macOS (Apple Silicon and Intel) and Windows are on the [Releases](https://github.com/dgslv/farejador-alugueis/releases/latest) page; they are unsigned, so both OSes show a warning on first launch (steps in the Portuguese README).

## Running from source

```bash
git clone https://github.com/dgslv/farejador-alugueis.git
cd farejador-alugueis
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
farejador            # desktop app; `--headless` = scraper only; `--dashboard` = dashboard only
pytest && ruff check . && ruff format --check .
```

Architecture: [docs/how-it-works.md](docs/how-it-works.md) (Portuguese, but the diagram and tables translate easily).

## Contributing and governance

- Issues and pull requests are welcome in English or Portuguese. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow (Conventional Commits, tests with real data, CI on three OSes).
- **Anyone can review; only the maintainer ([@dgslv](https://github.com/dgslv)) merges.** Merges require green CI and the maintainer's approval, enforced by `CODEOWNERS` and a branch ruleset — details in [GOVERNANCE.md](GOVERNANCE.md).
- Security issues: [SECURITY.md](SECURITY.md). Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) (Contributor Covenant 2.1).

## License

[MIT](LICENSE) © Diego Silva.
