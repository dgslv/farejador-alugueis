"""Rotas do painel. HTML fica em templates/, CSS e JS em static/."""

import json
import re
from datetime import datetime, timedelta

from flask import Blueprint, redirect, render_template, request, url_for

from farejador.db import (
    add_source,
    delete_source,
    get_all_listings,
    get_setting,
    get_settings,
    get_sources,
    init_db,
    mark_checked,
    set_setting,
    toggle_source,
    toggle_tracked,
)

bp = Blueprint("dashboard", __name__)

NEW_THRESHOLD_HOURS = 24  # "novo" = encontrado há menos de 24 h e ainda não visto


# ── Helpers puros ────────────────────────────────────────────────────────────


def clean_title(raw):
    """Primeira linha descritiva do texto do card (pula "+16 fotos" e vazios)."""
    if not raw:
        return "—"
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\+?\d+\s*fotos?$", line, re.IGNORECASE):
            continue
        return line[:100] + ("…" if len(line) > 100 else "")
    return "—"


def format_seen_at(s):
    if not s:
        return "—"
    try:
        return datetime.fromisoformat(s).strftime("%d/%m %H:%M")
    except Exception:
        return s[:16]


def _brl(value: int) -> str:
    return f"R$ {value:,}/mês".replace(",", ".") if value else "—"


def _parse_images(images_json) -> list:
    try:
        return json.loads(images_json or "[]") or []
    except Exception:
        return []


# ── Conteúdo da aba Apartamentos ─────────────────────────────────────────────


def _build_content():
    """Return (rows, fresh_listings, stats) from the current DB state.

    Cada row já vem com os campos derivados (classes, rótulos, preços
    formatados); os templates só cuidam da marcação.
    """
    listings = get_all_listings()
    total = len(listings)
    checked_count = sum(1 for lst in listings if lst.get("checked"))
    new_count = total - checked_count

    now = datetime.now()
    cutoff_iso = (now - timedelta(hours=NEW_THRESHOLD_HOURS)).isoformat()
    # A tracked listing is "gone" after missing ~3 consecutive scrapes (floor 5 min,
    # so a single failed page at a short interval doesn't flag it).
    gone_after = max(3 * get_setting("interval_seconds"), 5 * 60)
    gone_cutoff_iso = (now - timedelta(seconds=gone_after)).isoformat()

    rows = []
    fresh = []
    for lst in listings:
        is_checked = bool(lst.get("checked"))
        is_tracked = bool(lst.get("tracked"))
        seen_at = lst.get("seen_at") or ""
        last_seen_at = lst.get("last_seen_at")
        is_gone = is_tracked and bool(last_seen_at) and last_seen_at < gone_cutoff_iso
        is_fresh = not is_checked and seen_at >= cutoff_iso and not is_gone

        classes = []
        if is_gone:
            classes.append("gone")
        if is_tracked:
            classes.append("tracked")
        if is_fresh:
            classes.append("fresh")
        classes.append("checked" if is_checked else "unchecked")

        price = lst.get("price") or 0
        condo = lst.get("condo") or 0
        iptu = lst.get("iptu") or 0
        images = _parse_images(lst.get("images"))
        title = clean_title(lst.get("title"))
        modal = {
            "id": lst["id"],
            "url": lst.get("url", "#"),
            "title": title,
            "street": lst.get("street") or "",
            "neighborhood": lst.get("neighborhood") or "",
            "price": price,
            "condo": condo,
            "iptu": iptu,
            "area": lst.get("area") or 0,
            "bedrooms": lst.get("bedrooms") or 0,
            "posted_at": lst.get("posted_at") or "",
            "images": images,
        }
        if not is_checked:
            fresh.append({"id": lst["id"], "title": title, "neighborhood": modal["neighborhood"], "price": price})

        rows.append(
            {
                "id": lst["id"],
                "css_class": " ".join(classes),
                "fresh": is_fresh,
                "gone": is_gone,
                "title": title,
                "street": lst.get("street") or "",
                "neighborhood": lst.get("neighborhood") or "",
                "seen_at": format_seen_at(lst.get("seen_at")),
                "bedrooms": lst.get("bedrooms") or 0,
                "area_str": f"{lst['area']} m²" if lst.get("area") else "—",
                "price_str": _brl(price),
                "total_str": _brl(price + condo + iptu),
                "images": images,
                "modal_json": json.dumps(modal, ensure_ascii=False),
                "action_label": "Já visto" if is_checked else "✓ Marcar como visto",
                "track_label": "★ Monitorando" if is_tracked else "⭐ Monitorar",
                "track_btn_class": "tracking" if is_tracked else "",
            }
        )

    fresh_badge = f' &nbsp;·&nbsp; <strong style="color:#2e7d32">{len(fresh)} recentes</strong>' if fresh else ""
    stats = {"new": new_count, "checked": checked_count, "total": total, "fresh_badge": fresh_badge}
    return rows, fresh, stats


# ── Rotas ────────────────────────────────────────────────────────────────────


@bp.route("/")
def index():
    init_db()
    rows, fresh, stats = _build_content()
    return render_template("index.html", rows=rows, fresh=fresh, stats=stats)


@bp.route("/fragment")
def fragment():
    """Polled by the page every 30 s: rows + stats re-rendered, fresh listings for notifications."""
    rows, fresh, stats = _build_content()
    stats_html = (
        f"{stats['new']} novos &nbsp;·&nbsp; {stats['checked']} vistos"
        f" &nbsp;·&nbsp; {stats['total']} total{stats['fresh_badge']}"
    )
    return {"rows": render_template("_rows.html", rows=rows), "stats": stats_html, "fresh": fresh}


@bp.route("/check/<listing_id>", methods=["POST"])
def check(listing_id):
    mark_checked(listing_id)
    return redirect(url_for("dashboard.index"))


@bp.route("/toggle-track/<listing_id>", methods=["POST"])
def toggle_track(listing_id):
    toggle_tracked(listing_id)
    return redirect(url_for("dashboard.index"))


@bp.route("/sources")
def sources():
    init_db()
    return render_template("sources.html", sources=get_sources(), settings=get_settings())


@bp.route("/notify-test", methods=["POST"])
def notify_test():
    from farejador.notify import notify

    notify("Farejador", "Notificações funcionando! Você será avisado de novos apartamentos.")
    return redirect(url_for("dashboard.sources"))


@bp.route("/settings", methods=["POST"])
def settings_save():
    for key, lo, hi in (("max_total_price", 1, 10_000_000), ("interval_seconds", 5, 86400)):
        raw = request.form.get(key, "").strip()
        try:
            value = int(raw)
        except ValueError:
            continue  # lixo: mantém o valor guardado
        set_setting(key, max(lo, min(hi, value)))
    return redirect(url_for("dashboard.sources"))


@bp.route("/sources/add", methods=["POST"])
def source_add():
    url = request.form.get("url", "").strip()
    label = request.form.get("label", "").strip()
    if url:
        add_source(url, label)
    return redirect(url_for("dashboard.sources"))


@bp.route("/sources/delete/<int:sid>", methods=["POST"])
def source_delete(sid):
    delete_source(sid)
    return redirect(url_for("dashboard.sources"))


@bp.route("/sources/toggle/<int:sid>", methods=["POST"])
def source_toggle(sid):
    toggle_source(sid)
    return redirect(url_for("dashboard.sources"))
