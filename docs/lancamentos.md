# Como publicar uma versão

Só o mantenedor publica ([GOVERNANCE.md](../GOVERNANCE.md)). Um release leva uns 20 minutos, dos quais 15 são o CI gerando os instaladores.

## Numeração

[SemVer](https://semver.org/lang/pt-BR/) `X.Y.Z`:

- **Z** (patch): correção que não muda como se usa o app.
- **Y** (minor): funcionalidade nova, compatível.
- **X** (major): muda algo que quem usa precisa saber — pasta de dados, formato do banco, nome do app.

## Passo a passo

1. **Abra um PR de release** a partir de `main` (`chore/release-X.Y.Z`) com duas mudanças:
   - `version.py` → `__version__ = "X.Y.Z"`;
   - `CHANGELOG.md` → renomeie `## [Não lançado]` para `## [X.Y.Z] - AAAA-MM-DD`, crie um `## [Não lançado]` vazio acima e atualize os links de comparação no fim do arquivo.
2. **Faça o merge** do PR (CI verde, como sempre).
3. **Crie e envie a tag** apontando para o commit do merge:

   ```bash
   git checkout main && git pull
   git tag -a vX.Y.Z -m "Farejador X.Y.Z"
   git push origin vX.Y.Z
   ```

4. **Acompanhe o workflow [Release](https://github.com/dgslv/farejador-alugueis/actions/workflows/release.yml).** Ele:
   - confere que a tag bate com `version.py` (se não bater, para aqui — apague a tag, corrija e repita);
   - gera `Farejador-X.Y.Z-macOS-arm64.dmg`, `Farejador-X.Y.Z-macOS-x86_64.dmg` e `Farejador-X.Y.Z-Windows-x64.exe`;
   - publica a Release com esses três arquivos, `SHA256SUMS.txt`, a seção do CHANGELOG e a lista de PRs agrupada por label ([`.github/release.yml`](../.github/release.yml)).
5. **Canário — a release só está pronta depois disto:** baixe pelo menos um instalador da página da Release (não o artefato do CI), instale numa máquina limpa ou numa conta nova, cadastre uma fonte e espere a primeira busca terminar com anúncios na tela. Se falhar, marque a Release como *pre-release*, abra uma issue e corrija num patch.
6. Avise onde fizer sentido (issue de acompanhamento, redes) com o link da Release.

## Testar o empacotamento sem lançar

Dois jeitos, ambos rodam os mesmos builds e deixam os instaladores como artefatos do workflow por 90 dias, sem criar Release:

- **Automático**: todo PR que mexe em `*.spec`, `requirements*.txt`, `scripts/build-*`, `app.py` ou `version.py` dispara o workflow *Release* sozinho.
- **Manual**: Actions → **Release** → *Run workflow* → escolha a branch (o GitHub só mostra o botão para workflows que já existem na `main`).

## Se algo deu errado depois de publicar

- **Instalador quebrado**: marque a Release como *pre-release*, publique um patch `X.Y.(Z+1)`. Não apague releases — quem já baixou precisa conseguir achar o que instalou.
- **Tag errada**: `git push --delete origin vX.Y.Z && git tag -d vX.Y.Z`, apague a Release rascunho se o workflow chegou a criar uma, corrija e refaça.
