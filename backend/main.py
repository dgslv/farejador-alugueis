import asyncio
import json
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from config import INTERVAL_MINUTES, DB_PATH
from scraper import fetch_listings
from storage import get_all_listings, init_db, is_new, mark_checked, save_listing


def _migrate_from_sqlite():
    """One-time migration: copy rows from bundled SQLite snapshot → Supabase."""
    import sqlite3 as _sqlite3
    import os
    if not os.path.exists(DB_PATH):
        print("[migrate] no SQLite snapshot found, skipping", flush=True)
        return
    sqlite_conn = _sqlite3.connect(DB_PATH)
    sqlite_conn.row_factory = _sqlite3.Row
    rows = sqlite_conn.execute("SELECT * FROM listings").fetchall()
    sqlite_conn.close()
    if not rows:
        print("[migrate] SQLite snapshot is empty, skipping", flush=True)
        return
    import psycopg2
    from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME,
                             user=DB_USER, password=DB_PASSWORD, sslmode="require")
    cur = conn.cursor()
    migrated = 0
    for row in rows:
        r = dict(row)
        cur.execute("""
            INSERT INTO listings
                (id,url,title,street,neighborhood,price,condo,iptu,area,bedrooms,images,seen_at,checked,checked_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO UPDATE SET
                checked    = EXCLUDED.checked,
                checked_at = EXCLUDED.checked_at
            WHERE listings.checked = 0
        """, (
            r["id"], r["url"], r.get("title"), r.get("street"), r.get("neighborhood"),
            r.get("price"), r.get("condo"), r.get("iptu"), r.get("area"), r.get("bedrooms"),
            r.get("images"), r["seen_at"], r.get("checked", 0), r.get("checked_at"),
        ))
        migrated += 1
    conn.commit()
    cur.close()
    conn.close()
    print(f"[migrate] done — {migrated} rows upserted into Supabase", flush=True)


async def _scraper_loop():
    print("[scraper] background loop started", flush=True)
    while True:
        try:
            print("[scraper] running...", flush=True)
            listings = await fetch_listings()
            saved = 0
            for l in listings:
                if is_new(l["id"]):
                    save_listing(l)
                    saved += 1
                else:
                    save_listing(l)  # backfills images for existing rows
            print(f"[scraper] done — {saved} new out of {len(listings)} found", flush=True)
        except Exception as exc:
            print(f"[scraper] error: {exc}", flush=True)
        await asyncio.sleep(INTERVAL_MINUTES * 60)


async def _startup():
    """Run DB init, migration, and scraper — all in background."""
    try:
        init_db()
        print("[startup] DB ready", flush=True)
        _migrate_from_sqlite()
    except Exception as exc:
        print(f"[startup] DB init/migrate error: {exc}", flush=True)
    await _scraper_loop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start everything in background so server accepts requests immediately
    asyncio.create_task(_startup())
    yield


app = FastAPI(lifespan=lifespan)

# ── Templates ──────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Aluguel Dashboard</title>
<style>
  body {{ font-family: sans-serif; margin: 24px; background: #f5f5f5; }}
  h1 {{ margin-bottom: 4px; }}
  .stats {{ color: #555; margin-bottom: 20px; font-size: 14px; }}
  table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.1); }}
  th {{ background: #222; color: white; padding: 10px 14px; text-align: left; font-size: 13px; }}
  td {{ padding: 8px 14px; font-size: 14px; border-bottom: 1px solid #eee; vertical-align: middle; }}
  tr:last-child td {{ border-bottom: none; }}
  tr.unchecked {{ background: white; cursor: pointer; }}
  tr.checked {{ background: #f0f0f0; color: #999; cursor: pointer; }}
  tr.unchecked:hover {{ background: #f0f7ff; }}
  tr.checked:hover {{ background: #e8e8e8; }}
  tr.checked .price {{ text-decoration: line-through; }}
  .price {{ font-weight: bold; }}
  tr.checked .price {{ font-weight: normal; }}
  .total {{ font-weight: bold; color: #333; }}
  tr.checked .total {{ font-weight: normal; color: #999; }}
  .apt-title {{ max-width: 180px; }}
  button {{ cursor: pointer; background: #4caf50; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-size: 13px; }}
  button:hover {{ background: #388e3c; }}
  tr.checked button {{ background: #bbb; }}
  tr.checked button:hover {{ background: #999; }}
  .thumb-cell {{ width: 90px; padding: 6px 10px; }}
  .thumb {{ width: 80px; height: 56px; object-fit: cover; border-radius: 4px; display: block; cursor: zoom-in; }}
  .no-img {{ width: 80px; height: 56px; background: #e0e0e0; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 11px; color: #999; }}
  #lightbox {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.85); z-index:1000; align-items:center; justify-content:center; flex-direction:column; }}
  #lightbox.open {{ display:flex; }}
  #lightbox img {{ max-width:90vw; max-height:80vh; object-fit:contain; border-radius:6px; box-shadow:0 4px 32px rgba(0,0,0,.5); }}
  #lb-nav {{ margin-top:14px; display:flex; gap:16px; align-items:center; }}
  #lb-nav button {{ background:#fff; color:#222; font-size:18px; padding:6px 18px; border-radius:6px; border:none; cursor:pointer; }}
  #lb-nav button:hover {{ background:#eee; }}
  #lb-counter {{ color:#ccc; font-size:13px; min-width:60px; text-align:center; }}
  #lb-close {{ position:fixed; top:18px; right:24px; color:white; font-size:28px; cursor:pointer; line-height:1; }}
</style>
</head>
<body>
<h1>Apartamentos</h1>
<div class="stats">{new} novos &nbsp;·&nbsp; {checked} vistos &nbsp;·&nbsp; {total} total</div>
<table>
  <thead>
    <tr>
      <th></th>
      <th>Título</th>
      <th>Rua</th>
      <th>Bairro</th>
      <th>Quartos</th>
      <th>Área</th>
      <th>Aluguel</th>
      <th>Total</th>
      <th>Ação</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>
<div id="lightbox">
  <span id="lb-close" onclick="closeLb()">&#x2715;</span>
  <img id="lb-img" src="" alt="">
  <div id="lb-nav">
    <button onclick="lbStep(-1)">&#8592;</button>
    <span id="lb-counter"></span>
    <button onclick="lbStep(1)">&#8594;</button>
  </div>
</div>
<script>
  let lbImgs = [], lbIdx = 0;
  function openLb(imgs, idx) {{ lbImgs = imgs; lbIdx = idx; document.getElementById('lightbox').classList.add('open'); lbShow(); }}
  function lbShow() {{ document.getElementById('lb-img').src = lbImgs[lbIdx]; document.getElementById('lb-counter').textContent = (lbIdx+1)+' / '+lbImgs.length; }}
  function lbStep(d) {{ lbIdx = (lbIdx+d+lbImgs.length)%lbImgs.length; lbShow(); }}
  function closeLb() {{ document.getElementById('lightbox').classList.remove('open'); document.getElementById('lb-img').src=''; }}
  document.getElementById('lightbox').addEventListener('click', function(e) {{ if(e.target===this) closeLb(); }});
  document.addEventListener('keydown', function(e) {{ if(!document.getElementById('lightbox').classList.contains('open')) return; if(e.key==='ArrowLeft') lbStep(-1); if(e.key==='ArrowRight') lbStep(1); if(e.key==='Escape') closeLb(); }});
</script>
</body>
</html>"""

ROW_TEMPLATE = """<tr class="{css_class}" onclick="window.open('{url}','_blank')" title="Abrir anúncio">
  <td class="thumb-cell" onclick="event.stopPropagation()">{thumb_html}</td>
  <td class="apt-title">{title}</td>
  <td>{street}</td>
  <td>{neighborhood}</td>
  <td>{bedrooms}</td>
  <td>{area}</td>
  <td class="price">{price}</td>
  <td class="total">{total}</td>
  <td onclick="event.stopPropagation()">
    <form method="POST" action="/check/{listing_id}">
      <button type="submit">{action_label}</button>
    </form>
  </td>
</tr>"""


def clean_title(raw):
    if not raw:
        return "—"
    for line in raw.split('\n'):
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\+?\d+\s*fotos?$', line, re.IGNORECASE):
            continue
        return line[:100] + ('…' if len(line) > 100 else '')
    return "—"


def build_thumb_html(images_json):
    if not images_json:
        return '<div class="no-img">sem foto</div>'
    try:
        imgs = json.loads(images_json)
    except Exception:
        return '<div class="no-img">sem foto</div>'
    if not imgs:
        return '<div class="no-img">sem foto</div>'
    imgs_js = json.dumps(imgs)
    return (
        f'<img class="thumb" src="{imgs[0]}" loading="lazy" '
        f'onclick="openLb({imgs_js},0)" title="{len(imgs)} foto(s)">'
    )


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    listings = get_all_listings()
    total = len(listings)
    checked_count = sum(1 for l in listings if l.get("checked"))
    new_count = total - checked_count

    rows_html = []
    for l in listings:
        is_checked = bool(l.get("checked"))
        css_class = "checked" if is_checked else "unchecked"
        action_label = "Já visto" if is_checked else "✓ Marcar como visto"
        bedrooms = l.get("bedrooms") or "—"
        area = f"{l['area']} m²" if l.get("area") else "—"
        price_val = l.get("price") or 0
        condo_val = l.get("condo") or 0
        iptu_val = l.get("iptu") or 0
        price = f"R$ {price_val:,}/mês".replace(",", ".") if price_val else "—"
        total_val = price_val + condo_val + iptu_val
        total = f"R$ {total_val:,}/mês".replace(",", ".") if total_val else "—"
        rows_html.append(ROW_TEMPLATE.format(
            css_class=css_class,
            title=clean_title(l.get("title")),
            street=l.get("street") or "—",
            neighborhood=l.get("neighborhood") or "—",
            bedrooms=bedrooms,
            area=area,
            price=price,
            total=total,
            url=l.get("url", "#"),
            listing_id=l["id"],
            action_label=action_label,
            thumb_html=build_thumb_html(l.get("images")),
        ))

    return HTML_TEMPLATE.format(
        new=new_count,
        checked=checked_count,
        total=total,
        rows="\n".join(rows_html),
    )


@app.post("/check/{listing_id}")
def check(listing_id: str):
    mark_checked(listing_id)
    return RedirectResponse("/", status_code=303)


@app.post("/api/check/{listing_id}")
def api_check(listing_id: str):
    try:
        mark_checked(listing_id)
        return {"ok": True, "id": listing_id}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
