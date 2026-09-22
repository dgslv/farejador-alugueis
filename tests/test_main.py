"""main.py — uma rodada do agendador, com o scraper substituído por uma função falsa."""

import pytest

import main
import storage
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
def scheduler(db, monkeypatch):
    """Uma fonte cadastrada, notificações capturadas em vez de exibidas, scraper falso."""
    storage.add_source(SEARCH_URL, "Botafogo")
    notified = []
    monkeypatch.setattr(main, "notify", lambda title, message: notified.append((title, message)))
    monkeypatch.setattr(main, "log_listing", lambda listing: None)

    def returns(listings):
        async def fake_fetch(urls):
            assert urls == [SEARCH_URL]
            return list(listings)

        monkeypatch.setattr(main, "fetch_listings", fake_fetch)

    return {"notified": notified, "returns": returns}


def test_first_run_saves_silently_then_notifies_only_new_listings(scheduler):
    scheduler["returns"]([LISTING])
    main.run_once()
    assert scheduler["notified"] == []  # banco vazio = primeira rodada: sem avisos
    assert not storage.is_new(LISTING["id"])

    scheduler["returns"]([LISTING, LISTING_2])
    main.run_once()
    assert len(scheduler["notified"]) == 1  # só o anúncio novo
    title, message = scheduler["notified"][0]
    assert "Novo" in title
    assert "5,500" in message


def test_run_once_ignores_listings_over_the_budget(scheduler):
    storage.set_setting("max_total_price", 6000)  # LISTING custa 4500 + 1566 + 340 = 6406
    scheduler["returns"]([LISTING])
    main.run_once()
    assert storage.is_new(LISTING["id"])
    assert scheduler["notified"] == []


def test_run_once_survives_a_failing_scrape(scheduler, monkeypatch):
    async def boom(urls):
        raise RuntimeError("site fora do ar")

    monkeypatch.setattr(main, "fetch_listings", boom)
    main.run_once()  # não pode levantar exceção: o agendador continua na próxima rodada
    assert storage.count_listings() == 0
    assert scheduler["notified"] == []


def test_run_once_with_no_active_source_fetches_nothing(db, monkeypatch):
    storage.add_source(SEARCH_URL, "pausada")
    storage.toggle_source(storage.get_sources()[0]["id"])
    seen_urls = []

    async def fake_fetch(urls):
        seen_urls.append(urls)
        return []

    monkeypatch.setattr(main, "fetch_listings", fake_fetch)
    main.run_once()
    assert seen_urls == [[]]
