# Política de segurança

## Versões com suporte

Só a versão mais recente publicada em [Releases](https://github.com/dgslv/farejador-alugueis/releases) recebe correções. Se você está numa versão antiga, atualize antes de reportar.

## Como reportar uma vulnerabilidade

**Não abra uma issue pública.** Use o canal privado do GitHub:

1. Vá em **Security → Report a vulnerability** ([link direto](https://github.com/dgslv/farejador-alugueis/security/advisories/new)).
2. Descreva o problema, como reproduzir e o impacto que você enxerga. Se tiver, anexe uma prova de conceito.

O que esperar:

- **Confirmação de recebimento em até 7 dias.**
- Um diagnóstico inicial e a previsão de correção em até 14 dias.
- Crédito no changelog e nas notas de release, se você quiser.

Enquanto a correção não sai, pedimos que você não divulgue o problema publicamente.

## O que conta como vulnerabilidade aqui

O Farejador roda inteiro no computador de quem usa: não há servidor, conta nem transmissão de dados. Mesmo assim, há superfície de ataque:

- O painel local (Flask em `127.0.0.1:8080`) renderiza conteúdo vindo do site coletado — títulos, endereços, URLs de fotos. Injeção de HTML/JS a partir de um anúncio malicioso é vulnerabilidade.
- O app abre páginas externas num Chromium controlado por Playwright. Escapar desse contexto para o sistema é vulnerabilidade.
- Os instaladores são gerados pelo GitHub Actions a partir deste repositório. Qualquer forma de adulterar esse pipeline (dependências, workflow, artefatos) é vulnerabilidade.

Coisas que **não** são vulnerabilidades: o site coletado bloquear o robô; o app ler o banco `listings.db` da própria pasta de dados; o macOS/Windows avisarem que o app não é assinado (é esperado — veja o README).

## Para quem usa

- Baixe o Farejador **só** da página de Releases deste repositório. Cada release traz um `SHA256SUMS.txt`; confira o arquivo baixado com `shasum -a 256 <arquivo>` (macOS) ou `certutil -hashfile <arquivo> SHA256` (Windows).
- O app não pede senha, cartão nem login em lugar nenhum. Se alguma versão pedir, não é desta origem.
