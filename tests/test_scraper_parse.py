"""Parser dos cards do VivaReal — as funções puras de scraper.py.

Nada aqui abre navegador: só texto e URL entram, dicionário sai.
"""

import pytest

from scraper import _extract_card_fields, _parse_brl, _parse_link, _price_from_text
from tests.data import BOTAFOGO_2Q, HUMAITA_SEM_RUA

# ── _parse_link: URL + texto do card → anúncio ───────────────────────────────


def test_parse_link_real_card():
    assert _parse_link(BOTAFOGO_2Q["href"], BOTAFOGO_2Q["text"]) == {
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


def test_parse_link_strips_query_string_from_url():
    lst = _parse_link(BOTAFOGO_2Q["href"] + "?utm_source=teste#topo", BOTAFOGO_2Q["text"])
    assert lst["url"] == BOTAFOGO_2Q["href"]


def test_parse_link_price_falls_back_to_url_when_card_text_has_none():
    text = BOTAFOGO_2Q["text"].replace("R$ 4.500/mês", "")
    assert _parse_link(BOTAFOGO_2Q["href"], text)["price"] == 4500  # "-RS4500-" na URL


def test_parse_link_without_price_anywhere_is_zero():
    href = "https://www.vivareal.com.br/imovel/apartamento-2-quartos-botafogo-70m2-aluguel-id-123/"
    assert _parse_link(href, "card sem preço")["price"] == 0


def test_parse_link_missing_rooms_and_area_default_to_zero():
    href = "https://www.vivareal.com.br/imovel/kitnet-centro-aluguel-RS1200-id-999/"
    lst = _parse_link(href, "")
    assert (lst["bedrooms"], lst["area"], lst["price"]) == (0, 0.0, 1200)


@pytest.mark.parametrize(
    "href",
    [
        "https://www.vivareal.com.br/aluguel/rj/rio-de-janeiro/",  # página de busca, não anúncio
        "https://www.vivareal.com.br/imovel/apartamento-2-quartos/",  # sem "-id-NNN"
        "",
    ],
)
def test_parse_link_rejects_non_listing_urls(href):
    assert _parse_link(href, "qualquer texto") is None


# ── _parse_brl / _price_from_text: dinheiro em texto → int ───────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("4.500", 4500),
        ("1.566", 1566),
        ("340", 340),
        ("12.345.678", 12345678),
        ("4,500", 4500),  # separador de milhar com vírgula
        ("", 0),
        ("abc", 0),
        ("R$", 0),
    ],
)
def test_parse_brl(raw, expected):
    assert _parse_brl(raw) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("R$ 4.500/mês", 4500),
        ("R$4500/mês", 4500),
        ("R$ 4.500 / mes", 4500),  # sem acento
        ("R$ 4.500 /MÊS", 4500),  # caixa alta
        ("Venda R$ 900.000\nR$ 4.500/mês", 4500),  # anúncio de venda + aluguel: pega o aluguel
        ("R$ 900.000", 0),  # só preço de venda (sem "/mês") não conta
        ("", 0),
    ],
)
def test_price_from_text(text, expected):
    assert _price_from_text(text) == expected


# ── _extract_card_fields: bairro, rua, condomínio, IPTU ──────────────────────


def test_extract_card_fields_real_card():
    assert _extract_card_fields(BOTAFOGO_2Q["text"]) == {
        "neighborhood": "Botafogo",
        "street": "Rua Pinheiro Guimarães",
        "condo": 1566,
        "iptu": 340,
    }


def test_extract_card_fields_keeps_accents_in_neighborhood():
    assert _extract_card_fields(HUMAITA_SEM_RUA["text"])["neighborhood"] == "Humaitá"


def test_extract_card_fields_without_condo_or_iptu():
    text = BOTAFOGO_2Q["text"].replace("Cond. R$ 1.566 • IPTU R$ 340", "")
    fields = _extract_card_fields(text)
    assert (fields["condo"], fields["iptu"]) == (0, 0)


def test_extract_card_fields_empty_text():
    assert _extract_card_fields("") == {"neighborhood": "", "street": "", "condo": 0, "iptu": 0}


@pytest.mark.xfail(
    strict=True,
    reason="bug conhecido (#2): card sem rua devolve o rótulo 'Tamanho do imóvel' como rua",
)
def test_extract_card_fields_card_without_street_line():
    assert _extract_card_fields(HUMAITA_SEM_RUA["text"])["street"] == ""
