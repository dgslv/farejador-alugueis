"""scheduler.py — uma rodada do agendador, com o scraper substituído por uma função falsa."""

import pytest

from farejador import db as dbm
from farejador import scheduler
from tests.data import HUMAITA_SEM_RUA, LISTING, SEARCH_URL

LISTING_2 = {
    **LISTING,
    "id": "2873470586",
    "url": HUMAITA_SEM_RUA["href"],
    "title": HUMAITA_SEM_RUA["text"],
    "street": "",
    "neighborhood": "Humaitá",
    "price": 5500,
    "condo": 800,
    "iptu": 174,
    "area": 75.0,
}


@pytest.fixture
def env(db, monkeypatch):
    """Banco criado, uma fonte cadastrada, notificações capturadas, scraper falso."""
    dbm.add_source(SEARCH_URL, "Botafogo")
    notified = []
    monkeypatch.setattr(scheduler, "notify", lambda title, message: notified.append((title, message)))
    monkeypatch.setattr(scheduler, "log_listing", lambda listing: None)

    def returns(listings):
        async def fake_fetch(urls):
            assert urls == [SEARCH_URL]
            return list(listings)

        monkeypatch.setattr(scheduler, "fetch_listings", fake_fetch)

    return {"notified": notified, "returns": returns}


def test_first_run_saves_silently_then_notifies_only_new_listings(env):
    env["returns"]([LISTING])
    scheduler.run_once()
    assert env["notified"] == []  # banco vazio = primeira rodada: sem avisos
    assert not dbm.is_new(LISTING["id"])

    env["returns"]([LISTING, LISTING_2])
    scheduler.run_once()
    assert len(env["notified"]) == 1  # só o anúncio novo
    title, message = env["notified"][0]
    assert "Novo" in title
    assert "5,500" in message


def test_run_once_ignores_listings_over_the_budget(env):
    dbm.set_setting("max_total_price", 6000)  # LISTING custa 4500 + 1566 + 340 = 6406
    env["returns"]([LISTING])
    scheduler.run_once()
    assert dbm.is_new(LISTING["id"])
    assert env["notified"] == []


def test_run_once_survives_a_failing_scrape(env, monkeypatch):
    async def boom(urls):
        raise RuntimeError("site fora do ar")

    monkeypatch.setattr(scheduler, "fetch_listings", boom)
    scheduler.run_once()  # não pode levantar exceção: o agendador continua na próxima rodada
    assert dbm.count_listings() == 0
    assert env["notified"] == []


def test_run_once_with_no_active_source_fetches_nothing(db, monkeypatch):
    dbm.add_source(SEARCH_URL, "pausada")
    dbm.toggle_source(dbm.get_sources()[0]["id"])
    seen_urls = []

    async def fake_fetch(urls):
        seen_urls.append(urls)
        return []

    monkeypatch.setattr(scheduler, "fetch_listings", fake_fetch)
    scheduler.run_once()
    assert seen_urls == [[]]
