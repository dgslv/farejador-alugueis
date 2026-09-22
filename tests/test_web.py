"""web/ — helpers puros, templates e rotas Flask (client de teste, sem navegador)."""

import pytest

from farejador import db
from farejador.web import create_app
from farejador.web.routes import clean_title, format_seen_at
from tests.data import LISTING, SEARCH_URL


@pytest.fixture(autouse=True)
def _tables(db):
    """Toda rota assume o banco criado (fixture `db` do conftest)."""


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


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
    assert clean_title(raw) == expected


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
    assert format_seen_at(raw) == expected


# ── Aba Apartamentos ─────────────────────────────────────────────────────────


def test_index_renders_with_empty_db(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "Farejador de Aluguéis" in html
    assert "0 novos" in html


def test_index_lists_saved_listing_with_thumbnail_and_badge(client):
    db.save_listing({**LISTING, "images": '["https://img/1.jpg", "https://img/2.jpg"]'})
    html = client.get("/").get_data(as_text=True)
    assert "Rua Pinheiro Guimarães" in html
    assert 'class="thumb"' in html and "2 foto(s)" in html
    assert 'class="fresh-badge">novo' in html  # acabou de ser encontrado e não foi visto
    assert "R$ 6.406/mês" in html  # 4500 + 1566 + 340


def test_index_without_images_shows_placeholder(client):
    db.save_listing(LISTING)
    assert "sem foto" in client.get("/").get_data(as_text=True)


def test_listing_data_is_html_escaped_in_the_row(client):
    db.save_listing({**LISTING, "title": 'Apto "top" <script>alert(1)</script>'})
    html = client.get("/").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_check_marks_the_listing(client):
    db.save_listing(LISTING)
    r = client.post(f"/check/{LISTING['id']}")
    assert r.status_code == 302
    assert db.get_all_listings()[0]["checked"] == 1


def test_toggle_track_marks_the_listing(client):
    db.save_listing(LISTING)
    client.post(f"/toggle-track/{LISTING['id']}")
    assert db.get_tracked_ids() == {LISTING["id"]}
    assert "Monitorando" in client.get("/").get_data(as_text=True)


def test_fragment_returns_rows_and_stats(client):
    db.save_listing(LISTING)
    data = client.get("/fragment").get_json()
    assert set(data) == {"rows", "stats", "fresh"}
    assert "1 novos" in data["stats"]
    assert "<tr" in data["rows"]
    assert data["fresh"][0]["id"] == LISTING["id"]


# ── Aba Fontes ───────────────────────────────────────────────────────────────


def test_sources_page_add_and_delete(client):
    assert "Nenhuma fonte cadastrada" in client.get("/sources").get_data(as_text=True)
    client.post("/sources/add", data={"url": SEARCH_URL, "label": "Botafogo"})
    page = client.get("/sources").get_data(as_text=True)
    assert "Botafogo" in page and SEARCH_URL in page
    client.post(f"/sources/delete/{db.get_sources()[0]['id']}")
    assert db.get_sources() == []


def test_sources_add_ignores_empty_url(client):
    client.post("/sources/add", data={"url": "   ", "label": "x"})
    assert db.get_sources() == []


def test_notify_test_route_sends_one_notification(client, monkeypatch):
    from farejador import notify as notify_module

    sent = []
    monkeypatch.setattr(notify_module, "notify", lambda title, message: sent.append((title, message)))
    r = client.post("/notify-test")
    assert r.status_code == 302
    assert len(sent) == 1
    assert sent[0][0] == "Farejador"


def test_settings_save_persists_values(client):
    client.post("/settings", data={"max_total_price": "7000", "interval_seconds": "600"})
    assert db.get_settings() == {"max_total_price": 7000, "interval_seconds": 600}


def test_settings_save_clamps_out_of_range(client):
    client.post("/settings", data={"max_total_price": "0", "interval_seconds": "1"})
    assert db.get_settings() == {"max_total_price": 1, "interval_seconds": 5}


def test_settings_save_ignores_garbage_and_keeps_current(client):
    db.set_setting("interval_seconds", 600)
    client.post("/settings", data={"max_total_price": "abc", "interval_seconds": ""})
    assert db.get_settings() == {"max_total_price": db.MAX_TOTAL_PRICE, "interval_seconds": 600}


# ── Arquivos estáticos (dados do pacote) ─────────────────────────────────────


@pytest.mark.parametrize(
    ("path", "mimetypes", "signature"),
    [
        ("/static/logo.png", {"image/png"}, b"\x89PNG\r\n\x1a\n"),
        ("/static/style.css", {"text/css"}, b"/* Farejador"),
        # O tipo vem da tabela MIME do sistema: no Windows .js é application/javascript.
        ("/static/app.js", {"text/javascript", "application/javascript"}, b"// Farejador"),
    ],
)
def test_static_files_are_served(client, path, mimetypes, signature):
    r = client.get(path)
    assert r.status_code == 200
    assert r.mimetype in mimetypes
    assert r.data.startswith(signature)


def test_logo_is_linked_as_favicon_on_both_pages(client):
    for path in ("/", "/sources"):
        assert 'href="/static/logo.png"' in client.get(path).get_data(as_text=True)
