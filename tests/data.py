"""Dados reais usados pelos testes.

Os cards abaixo são o `inner_text` de anúncios reais do VivaReal, copiados
do banco de uma instalação em uso — não exemplos inventados. É exatamente
assim que o parser encontra o texto em produção. Ao capturar um card novo,
cole o texto sem retocar (as quebras de linha fazem parte do formato).
"""

SEARCH_URL = "https://www.vivareal.com.br/aluguel/rj/rio-de-janeiro/zona-sul/botafogo/apartamento_residencial/"

# Card completo: rua, condomínio e IPTU presentes.
BOTAFOGO_2Q = {
    "href": (
        "https://www.vivareal.com.br/imovel/"
        "apartamento-2-quartos-botafogo-rio-de-janeiro-com-garagem-70m2-aluguel-RS4500-id-2873504200/"
    ),
    "text": (
        "+16 fotos\n"
        "Apartamento para alugar com 70 m², 2 quartos, 2 banheiros, 1 vaga em\n"
        "Botafogo, Rio de Janeiro\n"
        "\n"
        "Rua Pinheiro Guimarães\n"
        "\n"
        "Tamanho do imóvel\n"
        "70 m²\n"
        "Quantidade de quartos\n"
        "2\n"
        "Quantidade de banheiros\n"
        "2\n"
        "Quantidade de vagas de garagem\n"
        "1\n"
        "\n"
        "R$ 4.500/mês\n"
        "\n"
        "Cond. R$ 1.566 • IPTU R$ 340\n"
        "\n"
        "Contatar"
    ),
}

# Card SEM a linha da rua (o anunciante não informou o endereço).
HUMAITA_SEM_RUA = {
    "href": (
        "https://www.vivareal.com.br/imovel/"
        "apartamento-2-quartos-humaita-rio-de-janeiro-75m2-aluguel-RS5500-id-2873470586/"
    ),
    "text": (
        "Apartamento para alugar com 75 m², 2 quartos, 2 banheiros em\n"
        "Humaitá, Rio de Janeiro\n"
        "\n"
        "Tamanho do imóvel\n"
        "75 m²\n"
        "Quantidade de quartos\n"
        "2\n"
        "Quantidade de banheiros\n"
        "2\n"
        "\n"
        "R$ 5.500/mês\n"
        "\n"
        "Cond. R$ 800 • IPTU R$ 174\n"
        "\n"
        "Contatar"
    ),
}

# Anúncio já parseado, no formato que storage.save_listing recebe.
LISTING = {
    "id": "2873504200",
    "url": BOTAFOGO_2Q["href"],
    "title": BOTAFOGO_2Q["text"],
    "street": "Rua Pinheiro Guimarães",
    "neighborhood": "Botafogo",
    "price": 4500,
    "condo": 1566,
    "iptu": 340,
    "area": 70.0,
    "bedrooms": 2,
}
