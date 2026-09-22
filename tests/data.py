"""Real data used by the tests.

The cards below are the `inner_text` of real VivaReal listings, copied from
the database of an installation in use — not invented examples. This is
exactly how the parser meets the text in production. When capturing a new
card, paste the text untouched (the line breaks are part of the format).
"""

SEARCH_URL = "https://www.vivareal.com.br/aluguel/rj/rio-de-janeiro/zona-sul/botafogo/apartamento_residencial/"

# Complete card: street, condo fee and IPTU present.
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

# Card WITHOUT the street line (the advertiser gave no address).
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

# Already-parsed listing, in the shape db.save_listing receives.
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
