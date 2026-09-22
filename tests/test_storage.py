"""storage.py — persistência em SQLite (anúncios, fontes e configurações)."""

import sqlite3
from datetime import datetime

import pytest

import storage
from tests.data import LISTING, SEARCH_URL


class FrozenClock:
    """Substitui storage.datetime para controlar seen_at / last_seen_at."""

    def __init__(self, iso):
        self._now = datetime.fromisoformat(iso)

    def now(self):
        return self._now


# ── Anúncios ─────────────────────────────────────────────────────────────────


def test_init_db_is_idempotent(db):
    storage.init_db()  # as migrações "ALTER TABLE" já aplicadas não podem quebrar
    assert storage.get_all_listings() == []


def test_new_listing_is_saved_once(db):
    assert storage.is_new(LISTING["id"])
    storage.save_listing(LISTING)
    assert not storage.is_new(LISTING["id"])
    rows = storage.get_all_listings()
    assert len(rows) == 1
    assert (rows[0]["price"], rows[0]["neighborhood"], rows[0]["street"]) == (
        4500,
        "Botafogo",
        "Rua Pinheiro Guimarães",
    )


def test_saving_again_only_touches_last_seen_at(db, monkeypatch):
    monkeypatch.setattr(storage, "datetime", FrozenClock("2026-09-01T10:00:00"))
    storage.save_listing(LISTING)
    monkeypatch.setattr(storage, "datetime", FrozenClock("2026-09-02T10:00:00"))
    storage.save_listing({**LISTING, "price": 9999})  # preço novo é ignorado de propósito
    row = storage.get_all_listings()[0]
    assert row["seen_at"] == "2026-09-01T10:00:00"
    assert row["last_seen_at"] == "2026-09-02T10:00:00"
    assert row["price"] == 4500


def test_images_are_backfilled_only_when_missing(db):
    storage.save_listing({**LISTING, "images": None})
    storage.save_listing({**LISTING, "images": '["https://img/1.jpg"]'})
    assert storage.get_all_listings()[0]["images"] == '["https://img/1.jpg"]'
    storage.save_listing({**LISTING, "images": '["https://img/2.jpg"]'})
    assert storage.get_all_listings()[0]["images"] == '["https://img/1.jpg"]'


def test_mark_checked_moves_listing_to_the_end(db):
    storage.save_listing(LISTING)
    storage.save_listing({**LISTING, "id": "2", "url": "https://www.vivareal.com.br/imovel/x-id-2/"})
    storage.mark_checked(LISTING["id"])
    rows = storage.get_all_listings()
    assert [r["id"] for r in rows] == ["2", LISTING["id"]]  # não vistos primeiro
    assert rows[1]["checked"] == 1
    assert rows[1]["checked_at"]


def test_count_listings_counts_distinct_ids(db):
    assert storage.count_listings() == 0
    storage.save_listing(LISTING)
    storage.save_listing(LISTING)  # mesma chave: continua 1
    assert storage.count_listings() == 1


def test_toggle_tracked_round_trip(db):
    storage.save_listing(LISTING)
    storage.toggle_tracked(LISTING["id"])
    assert storage.get_tracked_ids() == {LISTING["id"]}
    storage.toggle_tracked(LISTING["id"])
    assert storage.get_tracked_ids() == set()


# ── Fontes (URLs de busca) ───────────────────────────────────────────────────


def test_add_source_ignores_duplicate_url(db):
    storage.add_source(SEARCH_URL, "Botafogo 2q")
    storage.add_source("  " + SEARCH_URL + "  ", "outro nome")  # mesma URL, com espaços
    sources = storage.get_sources()
    assert len(sources) == 1
    assert (sources[0]["label"], sources[0]["active"]) == ("Botafogo 2q", 1)


def test_add_source_empty_label_becomes_null_and_unicode_is_kept(db):
    storage.add_source(SEARCH_URL, "")
    storage.add_source(SEARCH_URL + "?quartos=3", "Zona Sul — Humaitá ✓")
    assert [s["label"] for s in storage.get_sources()] == [None, "Zona Sul — Humaitá ✓"]


def test_toggle_and_delete_source(db):
    storage.add_source(SEARCH_URL, "x")
    sid = storage.get_sources()[0]["id"]
    storage.toggle_source(sid)
    assert storage.get_sources()[0]["active"] == 0
    storage.delete_source(sid)
    assert storage.get_sources() == []


def test_delete_unknown_source_is_a_noop(db):
    storage.delete_source(12345)
    assert storage.get_sources() == []


# ── Configurações ────────────────────────────────────────────────────────────


def test_settings_defaults_come_from_config(db):
    assert storage.get_settings() == {
        "max_total_price": storage.MAX_TOTAL_PRICE,
        "interval_seconds": storage.INTERVAL_SECONDS,
    }


def test_set_setting_round_trip_and_overwrite(db):
    storage.set_setting("max_total_price", 7000)
    storage.set_setting("max_total_price", 6500)
    assert storage.get_setting("max_total_price") == 6500


def test_set_setting_rejects_unknown_key(db):
    with pytest.raises(KeyError):
        storage.set_setting("tema", 1)


def test_corrupted_setting_value_falls_back_to_default(db):
    with sqlite3.connect(str(db)) as conn:
        conn.execute("INSERT INTO settings (key, value) VALUES ('interval_seconds', 'abc')")
    assert storage.get_setting("interval_seconds") == storage.INTERVAL_SECONDS
