"""dashboard.py — helpers puros e rotas Flask (client de teste, sem navegador)."""

import pytest

import dashboard
import storage
from tests.data import LISTING, SEARCH_URL


@pytest.fixture
def client(db):
    dashboard.app.config["TESTING"] = True
    return dashboard.app.test_client()


# ── Helpers puros ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, "—"),
        ("", "—"),
        ("+16 fotos\nApartamento para alugar com 70 m²", "Apartamento para alugar com 70 m²"),
        ("  \n\n3 fotos\n", "—"),  # só linhas vazias e contador de fotos
        ("x" * 150, "x" * 100 + "…"),
    ],
)
def test_clean_title(raw, expected):
    assert dashboard.clean_title(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-09-21T23:34:18", "21/09 23:34"),
        ("", "—"),
        (None, "—"),
        ("não-é-data", "não-é-data"),
    ],
)
def test_format_seen_at(raw, expected):
    assert dashboard.format_seen_at(raw) == expected


@pytest.mark.parametrize("images_json", [None, "", "[]", "não é json"])
def test_build_thumb_html_without_images(images_json):
    assert "sem foto" in dashboard.build_thumb_html(images_json)


def test_build_thumb_html_uses_first_image():
    html = dashboard.build_thumb_html('["https://img/1.jpg", "https://img/2.jpg"]')
    assert 'src="https://img/1.jpg"' in html
    assert "2 foto(s)" in html


# ── Rotas ────────────────────────────────────────────────────────────────────


def test_index_renders_with_empty_db(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Farejador de Aluguéis" in r.get_data(as_text=True)


def test_index_lists_saved_listing_and_check_marks_it(client):
    storage.save_listing(LISTING)
    assert "Rua Pinheiro Guimarães" in client.get("/").get_data(as_text=True)
    r = client.post(f"/check/{LISTING['id']}")
    assert r.status_code == 302
    assert storage.get_all_listings()[0]["checked"] == 1


def test_fragment_returns_rows_and_stats(client):
    storage.save_listing(LISTING)
    data = client.get("/fragment").get_json()
    assert set(data) == {"rows", "stats", "fresh"}
    assert "1 novos" in data["stats"]


def test_sources_page_add_and_delete(client):
    assert "Nenhuma fonte cadastrada" in client.get("/sources").get_data(as_text=True)
    client.post("/sources/add", data={"url": SEARCH_URL, "label": "Botafogo"})
    page = client.get("/sources").get_data(as_text=True)
    assert "Botafogo" in page and SEARCH_URL in page
    client.post(f"/sources/delete/{storage.get_sources()[0]['id']}")
    assert storage.get_sources() == []


def test_sources_add_ignores_empty_url(client):
    client.post("/sources/add", data={"url": "   ", "label": "x"})
    assert storage.get_sources() == []


def test_notify_test_route_sends_one_notification(client, monkeypatch):
    import notifier

    sent = []
    monkeypatch.setattr(notifier, "notify", lambda title, message: sent.append((title, message)))
    r = client.post("/notify-test")
    assert r.status_code == 302
    assert len(sent) == 1
    assert sent[0][0] == "Farejador"


def test_settings_save_persists_values(client):
    client.post("/settings", data={"max_total_price": "7000", "interval_seconds": "600"})
    assert storage.get_settings() == {"max_total_price": 7000, "interval_seconds": 600}


def test_settings_save_clamps_out_of_range(client):
    client.post("/settings", data={"max_total_price": "0", "interval_seconds": "1"})
    assert storage.get_settings() == {"max_total_price": 1, "interval_seconds": 5}


def test_settings_save_ignores_garbage_and_keeps_current(client):
    storage.set_setting("interval_seconds", 600)
    client.post("/settings", data={"max_total_price": "abc", "interval_seconds": ""})
    assert storage.get_settings() == {"max_total_price": storage.MAX_TOTAL_PRICE, "interval_seconds": 600}
