# Solução de problemas

Antes de tudo: **onde está o `app.log`**. Ele registra tudo o que o app faz e é o primeiro lugar para olhar (e para anexar num relato de problema, depois de apagar qualquer informação pessoal).

| Sistema | Caminho |
|---|---|
| macOS | `~/Library/Application Support/Farejador/app.log` (no Finder: ⌘⇧G e cole o caminho) |
| Windows | `%APPDATA%\Farejador\app.log` (cole no Explorador de Arquivos) |
| Linux (código-fonte) | o app imprime no terminal; não há `app.log` |

---

## macOS: "não foi possível verificar o desenvolvedor" / "está danificado"

O app não é assinado com uma conta de desenvolvedor da Apple, então o Gatekeeper bloqueia a primeira abertura.

1. Feche o aviso.
2. **Ajustes do Sistema → Privacidade e Segurança**, role até o fim: aparece "Farejador foi bloqueado…" → **Abrir Mesmo Assim**. Confirme com a senha do Mac.
3. Abra o app de novo. Só precisa uma vez por versão instalada.

Alternativa no Terminal (remove a marca de "baixado da internet"):

```bash
xattr -cr /Applications/Farejador.app
```

Se aparecer **"está danificado e não pode ser aberto"**, o comando acima resolve — é o mesmo bloqueio com outra mensagem, não um arquivo corrompido. Confira o download com o `SHA256SUMS.txt` da Release se quiser ter certeza.

## Windows: "O Windows protegeu o computador"

SmartScreen, pelo mesmo motivo (app sem certificado de assinatura). Clique em **Mais informações → Executar assim mesmo**. Só na primeira vez.

## A tela "Configurando o Farejador…" não sai do lugar

Na primeira abertura o app baixa o Chromium (~300 MB) para a pasta de dados. Precisa de internet e pode levar alguns minutos numa conexão lenta.

- Passou de 10 minutos: feche o app, apague a pasta `ms-playwright` dentro da pasta de dados (tabela no topo) e abra de novo.
- Continua: abra o `app.log` e procure linhas com `install` ou `Error`. Proxy corporativo e antivírus costumam bloquear esse download.

## A janela abre em branco ou fecha sozinha

O painel roda num servidor local na porta **8080**. Se outro programa (ou outra cópia do Farejador) já usa essa porta, o app não consegue subir.

- Confira se não há outro Farejador aberto (macOS: ⌘Tab; Windows: barra de tarefas / Gerenciador de Tarefas).
- Feche o outro programa que usa a porta 8080 e abra de novo.
- No `app.log`, a mensagem é `Address already in use`.

## "Checked 0 listings" / nenhum anúncio aparece

1. **A URL da fonte é de uma busca de aluguel?** Abra-a no seu navegador: tem que ser uma página de resultados do VivaReal (`vivareal.com.br/aluguel/...`) com anúncios visíveis. Página de um anúncio único, de venda ou de outro site não funciona.
2. **O site bloqueou temporariamente o robô.** No `app.log` aparece `page 1 failed` ou `Timeout`. Aumente o intervalo entre buscas (aba Fontes) e espere uma hora. O app usa um navegador com proteções contra detecção, mas nenhuma é infalível.
3. **O VivaReal mudou o layout.** Se as buscas funcionam no navegador e o log mostra `found 0 listings on page 1` em todas as fontes, o formato dos cards mudou e o parser precisa ser atualizado. [Abra uma issue](https://github.com/dgslv/farejador-alugueis/issues/new/choose) com a URL da fonte.

## Preço, condomínio ou bairro errados num anúncio

O app lê esses valores do texto do card na página de resultados. Se o anunciante preencheu errado, o app mostra errado — confira no anúncio original. Se **vários** anúncios vêm errados do mesmo jeito, é mudança de formato no site: abra uma issue e cole o texto do card (abra o anúncio no VivaReal, selecione o card inteiro e copie).

Caso conhecido: card sem a linha da rua mostra "Tamanho do imóvel" como rua. Está registrado e documentado nos testes.

## As notificações não aparecem

Primeiro: aba **Fontes → Testar notificação**. Se o teste aparece, o app está certo e o que falta é anúncio novo — lembre que a **primeira busca não avisa** de propósito.

- **macOS**: na primeira abertura o sistema pergunta se o Farejador pode enviar notificações; se você negou, vá em Ajustes do Sistema → Notificações → Farejador → permitir. Se o app não estiver na lista, o pedido de permissão falhou: procure `permission granted=False` ou `delivery error` no `app.log` e abra uma issue com essa linha (instaladores gerados no CI têm assinatura ad-hoc, e versões recentes do macOS podem recusar notificações nativas de apps assim).
- **Windows**: Configurações → Sistema → Notificações → ativar, e conferir se o modo *Não perturbe / Assistente de foco* não está ligado.
- Os avisos também ficam gravados em `alerts.log`, na pasta de dados, mesmo quando a notificação não aparece.

## Quero começar do zero

Feche o app e apague a pasta de dados (tabela no topo). Na próxima abertura ele recria tudo — e baixa o Chromium de novo. Para manter o navegador e apagar só os anúncios e fontes, apague apenas o arquivo `listings.db`.

## Nada disso resolveu

[Abra uma issue](https://github.com/dgslv/farejador-alugueis/issues/new/choose) com: versão do app, sistema, o que você fez, o que aconteceu, e as últimas ~50 linhas do `app.log`.
