import html as _html
import json
import re
from datetime import datetime, timedelta

from flask import Flask, redirect, request, url_for

from storage import (
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

app = Flask(__name__)

NEW_THRESHOLD_HOURS = 24

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="referrer" content="no-referrer">
<title>Farejador de Aluguéis</title>
<style>
  body {{ font-family: sans-serif; margin: 24px; background: #f5f5f5; }}
  h1 {{ margin-bottom: 4px; }}
  .stats {{ color: #555; margin-bottom: 20px; font-size: 14px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
  #toggle-checked-btn {{ background: #999; color: white; border: none; padding: 3px 10px; border-radius: 4px; font-size: 12px; cursor: pointer; }}
  #toggle-checked-btn:hover {{ background: #777; }}
  table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.1); }}
  th {{ background: #222; color: white; padding: 10px 14px; text-align: left; font-size: 13px; }}
  td {{ padding: 8px 14px; font-size: 14px; border-bottom: 1px solid #eee; vertical-align: middle; }}
  tr:last-child td {{ border-bottom: none; }}
  tr.unchecked {{ background: white; cursor: pointer; }}
  tr.checked {{ background: #f0f0f0; color: #999; cursor: pointer; }}
  tr.unchecked:hover {{ background: #f0f7ff; }}
  tr.checked:hover {{ background: #e8e8e8; }}
  tr.fresh {{ background: #f0fff4 !important; cursor: pointer; }}
  tr.fresh:hover {{ background: #dcf5e4 !important; }}
  tr.fresh td:first-child {{ box-shadow: inset 4px 0 0 #2e7d32; }}
  .fresh-badge {{ display:inline-block; background:#2e7d32; color:white; font-size:10px; font-weight:600; padding:1px 7px; border-radius:10px; margin-left:6px; vertical-align:middle; letter-spacing:.3px; }}
  tr.tracked td:first-child {{ box-shadow: inset 4px 0 0 #1565c0; }}
  tr.gone {{ background: #fff3e0 !important; }}
  tr.gone:hover {{ background: #ffe0b2 !important; }}
  tr.gone td:first-child {{ box-shadow: inset 4px 0 0 #e65100; }}
  .gone-badge {{ display:inline-block; background:#e65100; color:white; font-size:10px; font-weight:600; padding:1px 7px; border-radius:10px; margin-left:6px; vertical-align:middle; letter-spacing:.3px; }}
  .track-btn {{ background: #1565c0; font-size:12px; padding:4px 8px; margin-top:4px; }}
  .track-btn:hover {{ background: #0d47a1; }}
  .track-btn.tracking {{ background: #5c6bc0; }}
  .track-btn.tracking:hover {{ background: #3949ab; }}
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

  /* Thumbnail */
  .thumb-cell {{ width: 90px; padding: 6px 10px; }}
  .thumb {{ width: 80px; height: 56px; object-fit: cover; border-radius: 4px; display: block; cursor: zoom-in; }}
  .no-img {{ width: 80px; height: 56px; background: #e0e0e0; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 11px; color: #999; }}

  /* Lightbox */
  #lightbox {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.85); z-index:2000; align-items:center; justify-content:center; flex-direction:column; }}
  #lightbox.open {{ display:flex; }}
  #lightbox img {{ max-width:90vw; max-height:80vh; object-fit:contain; border-radius:6px; box-shadow:0 4px 32px rgba(0,0,0,.5); }}
  #lb-nav {{ margin-top:14px; display:flex; gap:16px; align-items:center; }}
  #lb-nav button {{ background:#fff; color:#222; font-size:18px; padding:6px 18px; border-radius:6px; border:none; cursor:pointer; }}
  #lb-nav button:hover {{ background:#eee; }}
  #lb-counter {{ color:#ccc; font-size:13px; min-width:60px; text-align:center; }}
  #lb-close {{ position:fixed; top:18px; right:24px; color:white; font-size:28px; cursor:pointer; line-height:1; }}

  /* Detail modal */
  #detail-modal {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.6); z-index:1000; align-items:center; justify-content:center; }}
  #detail-modal.open {{ display:flex; }}
  .dm-box {{ background:#fff; border-radius:12px; max-width:680px; width:95vw; max-height:90vh; overflow-y:auto; padding:28px 28px 20px; box-shadow:0 8px 40px rgba(0,0,0,.3); position:relative; }}
  .dm-close {{ position:absolute; top:14px; right:18px; font-size:24px; cursor:pointer; color:#666; line-height:1; }}
  .dm-close:hover {{ color:#222; }}
  .dm-title {{ font-size:17px; font-weight:bold; margin:0 0 4px; padding-right:28px; }}
  .dm-addr {{ color:#666; font-size:13px; margin-bottom:14px; }}
  .dm-gallery {{ display:flex; gap:8px; overflow-x:auto; margin-bottom:16px; padding-bottom:4px; }}
  .dm-gallery img {{ height:140px; border-radius:6px; cursor:zoom-in; flex-shrink:0; object-fit:cover; }}
  .dm-gallery .no-gallery {{ color:#aaa; font-size:13px; padding:20px; }}
  .dm-prices {{ display:grid; grid-template-columns:1fr 1fr; gap:8px 20px; margin-bottom:14px; }}
  .dm-prices .item {{ font-size:13px; }}
  .dm-prices .item .label {{ color:#888; font-size:11px; text-transform:uppercase; letter-spacing:.5px; }}
  .dm-prices .item .value {{ font-weight:600; color:#222; font-size:15px; }}
  .dm-prices .item.total .value {{ color:#1a6b1a; font-size:17px; }}
  .dm-meta {{ display:flex; gap:20px; font-size:13px; color:#555; margin-bottom:16px; flex-wrap:wrap; }}
  .dm-meta span {{ background:#f0f0f0; padding:3px 10px; border-radius:20px; }}
  .dm-open-btn {{ display:inline-block; background:#1976d2; color:white; border:none; padding:10px 22px; border-radius:6px; font-size:14px; cursor:pointer; text-decoration:none; }}
  .dm-open-btn:hover {{ background:#1256a3; }}

  /* Nav */
  nav {{ display:flex; gap:4px; margin-bottom:16px; border-bottom:2px solid #ddd; padding-bottom:0; }}
  .nav-link {{ padding:7px 18px; border-radius:6px 6px 0 0; font-size:14px; font-weight:500; text-decoration:none; color:#555; background:#e8e8e8; border:1px solid #ddd; border-bottom:none; margin-bottom:-2px; }}
  .nav-link:hover {{ background:#d5d5d5; color:#222; }}
  .nav-link.active {{ background:white; color:#222; border-color:#ddd; font-weight:600; }}

  /* Sources table */
  .src-url {{ max-width:420px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:12px; color:#555; }}
  .src-label {{ font-weight:500; }}
  .badge-active {{ background:#2e7d32; color:white; font-size:11px; padding:2px 8px; border-radius:10px; }}
  .badge-paused {{ background:#999; color:white; font-size:11px; padding:2px 8px; border-radius:10px; }}
  .add-form {{ margin-top:24px; background:white; border-radius:8px; padding:20px 24px; box-shadow:0 1px 4px rgba(0,0,0,.1); display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end; }}
  .add-form label {{ font-size:13px; color:#555; display:block; margin-bottom:4px; }}
  .add-form input {{ border:1px solid #ccc; border-radius:4px; padding:6px 10px; font-size:13px; }}
  .add-form input[name="url"] {{ width:420px; }}
  .add-form input[name="label"] {{ width:160px; }}
  .btn-danger {{ background:#c62828; }}
  .btn-danger:hover {{ background:#b71c1c; }}
  .btn-secondary {{ background:#546e7a; }}
  .btn-secondary:hover {{ background:#37474f; }}

  /* Toast */
  #toast {{ display:none; position:fixed; top:16px; left:50%; transform:translateX(-50%); background:#2e7d32; color:white; padding:10px 22px; border-radius:8px; font-size:14px; font-weight:600; box-shadow:0 4px 16px rgba(0,0,0,.25); z-index:3000; cursor:pointer; }}
  #toast.show {{ display:block; animation:fadeout 0.4s ease 4.6s forwards; }}
  @keyframes fadeout {{ to {{ opacity:0; pointer-events:none; }} }}
</style>
</head>
<body>
<div id="toast" onclick="this.classList.remove('show')"></div>
<h1>Farejador de Aluguéis</h1>
<nav>
  <a href="/" class="nav-link active">Apartamentos</a>
  <a href="/sources" class="nav-link">Fontes</a>
</nav>
<div class="stats"><span>{new} novos &nbsp;·&nbsp; {checked} vistos &nbsp;·&nbsp; {total} total{fresh_badge}</span><button id="toggle-checked-btn" onclick="toggleChecked()">Ocultar vistos</button><button id="enable-notif-btn" onclick="enableNotifications()" style="display:none;background:#e65100;font-size:12px;padding:3px 10px;">🔔 Ativar notificações</button></div>
<table>
  <thead>
    <tr>
      <th></th>
      <th>Título</th>
      <th>Rua</th>
      <th>Bairro</th>
      <th>Encontrado</th>
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

<!-- Detail modal -->
<div id="detail-modal">
  <div class="dm-box">
    <span class="dm-close" onclick="closeDetail()">&#x2715;</span>
    <p class="dm-title" id="dm-title"></p>
    <p class="dm-addr" id="dm-addr"></p>
    <div class="dm-gallery" id="dm-gallery"></div>
    <div class="dm-prices" id="dm-prices"></div>
    <div class="dm-meta" id="dm-meta"></div>
    <a id="dm-open-btn" class="dm-open-btn" href="#" target="_blank">Abrir anúncio</a>
  </div>
</div>

<!-- Lightbox -->
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
  // ---- Lightbox ----
  let lbImgs = [], lbIdx = 0;

  function openLb(imgs, idx) {{
    lbImgs = imgs; lbIdx = idx;
    document.getElementById('lightbox').classList.add('open');
    lbShow();
  }}

  function lbShow() {{
    document.getElementById('lb-img').src = lbImgs[lbIdx];
    document.getElementById('lb-counter').textContent = (lbIdx + 1) + ' / ' + lbImgs.length;
  }}

  function lbStep(d) {{
    lbIdx = (lbIdx + d + lbImgs.length) % lbImgs.length;
    lbShow();
  }}

  function closeLb() {{
    document.getElementById('lightbox').classList.remove('open');
    document.getElementById('lb-img').src = '';
  }}

  document.getElementById('lightbox').addEventListener('click', function(e) {{
    if (e.target === this) closeLb();
  }});

  // ---- Detail modal ----
  function openDetail(d) {{
    document.getElementById('dm-title').textContent = d.title || '—';
    var addr = [d.street, d.neighborhood].filter(Boolean).join(', ') || '—';
    document.getElementById('dm-addr').textContent = addr;

    // Gallery
    var gallery = document.getElementById('dm-gallery');
    gallery.innerHTML = '';
    var imgs = d.images || [];
    if (imgs.length) {{
      imgs.forEach(function(src, i) {{
        var img = document.createElement('img');
        img.src = src;
        img.loading = 'lazy';
        img.onclick = function(e) {{ e.stopPropagation(); openLb(imgs, i); }};
        gallery.appendChild(img);
      }});
    }} else {{
      gallery.innerHTML = '<span class="no-gallery">Sem fotos disponíveis</span>';
    }}

    // Prices
    var price = d.price ? 'R$ ' + d.price.toLocaleString('pt-BR') + '/mês' : '—';
    var condo = d.condo ? 'R$ ' + d.condo.toLocaleString('pt-BR') + '/mês' : '—';
    var iptu  = d.iptu  ? 'R$ ' + d.iptu.toLocaleString('pt-BR') + '/mês'  : '—';
    var totalVal = (d.price || 0) + (d.condo || 0) + (d.iptu || 0);
    var total = totalVal ? 'R$ ' + totalVal.toLocaleString('pt-BR') + '/mês' : '—';
    document.getElementById('dm-prices').innerHTML =
      '<div class="item"><div class="label">Aluguel</div><div class="value">' + price + '</div></div>' +
      '<div class="item"><div class="label">Condomínio</div><div class="value">' + condo + '</div></div>' +
      '<div class="item"><div class="label">IPTU</div><div class="value">' + iptu + '</div></div>' +
      '<div class="item total"><div class="label">Total</div><div class="value">' + total + '</div></div>';

    // Meta
    var meta = [];
    if (d.area)     meta.push(d.area + ' m²');
    if (d.bedrooms) meta.push(d.bedrooms + ' quarto' + (d.bedrooms > 1 ? 's' : ''));
    if (d.posted_at) {{
      var parts = d.posted_at.split('-');
      meta.push('Publicado ' + parts[2] + '/' + parts[1] + (parts[0] ? '/' + parts[0].slice(2) : ''));
    }}
    document.getElementById('dm-meta').innerHTML = meta.map(function(s) {{ return '<span>' + s + '</span>'; }}).join('');

    document.getElementById('dm-open-btn').href = d.url || '#';
    document.getElementById('detail-modal').classList.add('open');
  }}

  function closeDetail() {{
    document.getElementById('detail-modal').classList.remove('open');
  }}

  document.getElementById('detail-modal').addEventListener('click', function(e) {{
    if (e.target === this) closeDetail();
  }});

  document.addEventListener('keydown', function(e) {{
    if (document.getElementById('lightbox').classList.contains('open')) {{
      if (e.key === 'ArrowLeft')  lbStep(-1);
      if (e.key === 'ArrowRight') lbStep(1);
      if (e.key === 'Escape') closeLb();
      return;
    }}
    if (document.getElementById('detail-modal').classList.contains('open')) {{
      if (e.key === 'Escape') closeDetail();
    }}
  }});

  // ---- Hide-viewed toggle ----
  var checkedHidden = false;
  function toggleChecked() {{
    checkedHidden = !checkedHidden;
    document.querySelectorAll('tr.checked').forEach(function(r) {{
      r.style.display = checkedHidden ? 'none' : '';
    }});
    document.getElementById('toggle-checked-btn').textContent =
      checkedHidden ? 'Mostrar vistos' : 'Ocultar vistos';
  }}

  // ---- Fresh-listing browser notifications ----
  var freshListings = {fresh_listings_json};

  function showToast(msg) {{
    var t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.remove('show');
    void t.offsetWidth; // restart animation
    t.classList.add('show');
    setTimeout(function() {{ t.classList.remove('show'); }}, 5000);
  }}

  function sendFreshNotifications(toNotify) {{
    if (!toNotify.length) return;
    var tag = 'fresh-' + Date.now();
    if (toNotify.length === 1) {{
      var l = toNotify[0];
      showToast('Novo apartamento: ' + l.title + ' · R$ ' + (l.price || 0).toLocaleString('pt-BR') + '/mês');
      if ('Notification' in window && Notification.permission === 'granted') {{
        new Notification('Novo apartamento!', {{
          body: l.title + ' · R$ ' + (l.price || 0).toLocaleString('pt-BR') + '/mês · ' + l.neighborhood,
          tag: tag
        }});
      }}
    }} else {{
      showToast(toNotify.length + ' novos apartamentos encontrados!');
      if ('Notification' in window && Notification.permission === 'granted') {{
        new Notification(toNotify.length + ' novos apartamentos!', {{
          body: toNotify.slice(0, 3).map(function(l) {{ return l.title; }}).join(' | ') + (toNotify.length > 3 ? ' …' : ''),
          tag: tag
        }});
      }}
    }}
  }}

  function fireNotifications() {{
    var stored = localStorage.getItem('notified_ids');
    var notifiedIds = new Set(stored ? JSON.parse(stored) : []);
    var toNotify = freshListings.filter(function(l) {{ return !notifiedIds.has(l.id); }});
    if (toNotify.length) {{
      sendFreshNotifications(toNotify);
      toNotify.forEach(function(l) {{ notifiedIds.add(l.id); }});
      localStorage.setItem('notified_ids', JSON.stringify(Array.from(notifiedIds)));
    }}
  }}

  function enableNotifications() {{
    Notification.requestPermission().then(function(perm) {{
      var btn = document.getElementById('enable-notif-btn');
      if (perm === 'granted') {{
        btn.style.display = 'none';
        fireNotifications();
      }} else {{
        btn.textContent = '🔕 Notificações bloqueadas';
        btn.style.background = '#999';
      }}
    }});
  }}

  if ('Notification' in window) {{
    if (Notification.permission === 'granted') {{
      fireNotifications();
    }} else if (Notification.permission !== 'denied') {{
      document.getElementById('enable-notif-btn').style.display = '';
    }}
  }}

  // ---- Auto-refresh (polls /fragment every 30 s) ----
  setInterval(function() {{
    fetch('/fragment')
      .then(function(r) {{ return r.json(); }})
      .then(function(data) {{
        document.querySelector('tbody').innerHTML = data.rows;
        document.querySelector('.stats span').innerHTML = data.stats;

        // Re-apply hide-viewed state
        if (checkedHidden) {{
          document.querySelectorAll('tr.checked').forEach(function(r) {{
            r.style.display = 'none';
          }});
        }}

        // Check for new unchecked listings and notify
        if (data.fresh.length && 'Notification' in window && Notification.permission === 'granted') {{
          var stored = localStorage.getItem('notified_ids');
          var notifiedIds = new Set(stored ? JSON.parse(stored) : []);
          var toNotify = data.fresh.filter(function(l) {{ return !notifiedIds.has(l.id); }});
          if (toNotify.length) {{
            sendFreshNotifications(toNotify);
            toNotify.forEach(function(l) {{ notifiedIds.add(l.id); }});
            localStorage.setItem('notified_ids', JSON.stringify(Array.from(notifiedIds)));
          }}
        }}
      }});
  }}, 30000);
</script>
</body>
</html>"""

ROW_TEMPLATE = """<tr class="{css_class}" onclick="openDetail({listing_data})" title="Ver detalhes">
  <td class="thumb-cell" onclick="event.stopPropagation()">{thumb_html}</td>
  <td class="apt-title">{title}</td>
  <td>{street}</td>
  <td>{neighborhood}</td>
  <td>{seen_at}</td>
  <td>{bedrooms}</td>
  <td>{area}</td>
  <td class="price">{price}</td>
  <td class="total">{total}</td>
  <td onclick="event.stopPropagation()">
    <form method="POST" action="/check/{listing_id}">
      <button type="submit">{action_label}</button>
    </form>
    <form method="POST" action="/toggle-track/{listing_id}">
      <button type="submit" class="track-btn {track_btn_class}">{track_label}</button>
    </form>
  </td>
</tr>"""


def clean_title(raw):
    """Extract the first descriptive line from VivaReal card text."""
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


def format_seen_at(s):
    if not s:
        return "—"
    try:
        dt = datetime.fromisoformat(s)
        return dt.strftime("%d/%m %H:%M")
    except Exception:
        return s[:16]


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



def _build_content():
    """Return (rows_html, fresh_listings_data, stats_dict) from current DB state."""
    listings = get_all_listings()
    total = len(listings)
    checked_count = sum(1 for lst in listings if lst.get("checked"))
    new_count = total - checked_count

    cutoff_dt = datetime.now() - timedelta(hours=NEW_THRESHOLD_HOURS)
    cutoff_iso = cutoff_dt.isoformat()
    # A tracked listing is "gone" after missing ~3 consecutive scrapes (floor 5 min,
    # so a single failed page at a short interval doesn't flag it).
    gone_after = max(3 * get_setting("interval_seconds"), 5 * 60)
    gone_cutoff_iso = (datetime.now() - timedelta(seconds=gone_after)).isoformat()

    fresh_listings_data = []
    rows_html = []
    for lst in listings:
        is_checked = bool(lst.get("checked"))
        is_tracked = bool(lst.get("tracked"))
        seen_at_str = lst.get("seen_at") or ""
        last_seen_at = lst.get("last_seen_at")
        is_gone = is_tracked and bool(last_seen_at) and last_seen_at < gone_cutoff_iso
        is_fresh = not is_checked and seen_at_str >= cutoff_iso

        classes = []
        if is_gone:
            classes.append("gone")
        if is_tracked:
            classes.append("tracked")
        if is_fresh and not is_gone:
            classes.append("fresh")
        classes.append("checked" if is_checked else "unchecked")
        css_class = " ".join(classes)

        action_label = "Já visto" if is_checked else "✓ Marcar como visto"
        track_label = "★ Monitorando" if is_tracked else "⭐ Monitorar"
        track_btn_class = "tracking" if is_tracked else ""
        bedrooms = lst.get("bedrooms") or "—"
        area = f"{lst['area']} m²" if lst.get("area") else "—"
        price_val = lst.get("price") or 0
        condo_val = lst.get("condo") or 0
        iptu_val = lst.get("iptu") or 0
        price = f"R$ {price_val:,}/mês".replace(",", ".") if price_val else "—"
        total_val = price_val + condo_val + iptu_val
        total_str = f"R$ {total_val:,}/mês".replace(",", ".") if total_val else "—"

        try:
            images_list = json.loads(lst.get("images") or "[]") or []
        except Exception:
            images_list = []
        modal_data = {
            "id":           lst["id"],
            "url":          lst.get("url", "#"),
            "title":        clean_title(lst.get("title")),
            "street":       lst.get("street") or "",
            "neighborhood": lst.get("neighborhood") or "",
            "price":        price_val,
            "condo":        condo_val,
            "iptu":         iptu_val,
            "area":         lst.get("area") or 0,
            "bedrooms":     lst.get("bedrooms") or 0,
            "posted_at":    lst.get("posted_at") or "",
            "images":       images_list,
        }
        if not is_checked:
            fresh_listings_data.append({
                "id":           lst["id"],
                "title":        modal_data["title"],
                "neighborhood": modal_data["neighborhood"],
                "price":        price_val,
            })
        listing_data = _html.escape(json.dumps(modal_data, ensure_ascii=False), quote=True)

        title_cell = clean_title(lst.get("title"))
        if is_fresh and not is_gone:
            title_cell += ' <span class="fresh-badge">novo</span>'
        if is_gone:
            title_cell += ' <span class="gone-badge">SUMIU</span>'

        rows_html.append(ROW_TEMPLATE.format(
            css_class=css_class,
            title=title_cell,
            street=lst.get("street") or "—",
            neighborhood=lst.get("neighborhood") or "—",
            seen_at=format_seen_at(lst.get("seen_at")),
            bedrooms=bedrooms,
            area=area,
            price=price,
            total=total_str,
            url=lst.get("url", "#"),
            listing_id=lst["id"],
            action_label=action_label,
            track_label=track_label,
            track_btn_class=track_btn_class,
            thumb_html=build_thumb_html(lst.get("images")),
            listing_data=listing_data,
        ))

    fresh_count = len(fresh_listings_data)
    fresh_badge = (
        f' &nbsp;·&nbsp; <strong style="color:#2e7d32">{fresh_count} recentes</strong>'
        if fresh_count else ""
    )
    stats = {
        "new": new_count, "checked": checked_count, "total": total,
        "fresh_badge": fresh_badge,
    }
    return rows_html, fresh_listings_data, stats


@app.route("/")
def index():
    init_db()
    rows_html, fresh_listings_data, stats = _build_content()
    html = HTML_TEMPLATE.format(
        new=stats["new"],
        checked=stats["checked"],
        total=stats["total"],
        fresh_badge=stats["fresh_badge"],
        fresh_listings_json=json.dumps(fresh_listings_data, ensure_ascii=False),
        rows="\n".join(rows_html),
    )
    return html


@app.route("/fragment")
def fragment():
    rows_html, fresh_listings_data, stats = _build_content()
    stats_html = (
        f'{stats["new"]} novos &nbsp;·&nbsp; {stats["checked"]} vistos'
        f' &nbsp;·&nbsp; {stats["total"]} total{stats["fresh_badge"]}'
    )
    return {"rows": "\n".join(rows_html), "stats": stats_html, "fresh": fresh_listings_data}


@app.route("/check/<listing_id>", methods=["POST"])
def check(listing_id):
    mark_checked(listing_id)
    return redirect(url_for("index"))


@app.route("/toggle-track/<listing_id>", methods=["POST"])
def toggle_track(listing_id):
    toggle_tracked(listing_id)
    return redirect(url_for("index"))


SOURCES_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="referrer" content="no-referrer">
<title>Fontes — Farejador de Aluguéis</title>
<style>
  body {{ font-family: sans-serif; margin: 24px; background: #f5f5f5; }}
  h1 {{ margin-bottom: 4px; }}
  nav {{ display:flex; gap:4px; margin-bottom:16px; border-bottom:2px solid #ddd; padding-bottom:0; }}
  .nav-link {{ padding:7px 18px; border-radius:6px 6px 0 0; font-size:14px; font-weight:500; text-decoration:none; color:#555; background:#e8e8e8; border:1px solid #ddd; border-bottom:none; margin-bottom:-2px; }}
  .nav-link:hover {{ background:#d5d5d5; color:#222; }}
  .nav-link.active {{ background:white; color:#222; border-color:#ddd; font-weight:600; }}
  table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.1); }}
  th {{ background: #222; color: white; padding: 10px 14px; text-align: left; font-size: 13px; }}
  td {{ padding: 10px 14px; font-size: 14px; border-bottom: 1px solid #eee; vertical-align: middle; }}
  tr:last-child td {{ border-bottom: none; }}
  .src-url {{ max-width:480px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:12px; color:#555; display:block; }}
  .src-label {{ font-weight:500; margin-bottom:2px; }}
  .badge-active {{ background:#2e7d32; color:white; font-size:11px; padding:2px 8px; border-radius:10px; }}
  .badge-paused {{ background:#999; color:white; font-size:11px; padding:2px 8px; border-radius:10px; }}
  button {{ cursor:pointer; border:none; padding:5px 12px; border-radius:4px; font-size:12px; color:white; }}
  .btn-toggle {{ background:#546e7a; }}
  .btn-toggle:hover {{ background:#37474f; }}
  .btn-danger {{ background:#c62828; }}
  .btn-danger:hover {{ background:#b71c1c; }}
  .add-form {{ margin-top:24px; background:white; border-radius:8px; padding:20px 24px; box-shadow:0 1px 4px rgba(0,0,0,.1); }}
  .add-form h3 {{ margin:0 0 14px; font-size:15px; }}
  .add-form .row {{ display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end; }}
  .add-form label {{ font-size:12px; color:#666; display:block; margin-bottom:3px; }}
  .add-form input {{ border:1px solid #ccc; border-radius:4px; padding:7px 10px; font-size:13px; }}
  .add-form input[name="url"] {{ width:460px; }}
  .add-form input[name="label"] {{ width:160px; }}
  .btn-add {{ background:#1565c0; color:white; border:none; padding:7px 18px; border-radius:4px; font-size:13px; cursor:pointer; }}
  .btn-add:hover {{ background:#0d47a1; }}
  .empty {{ color:#999; padding:24px; text-align:center; }}
</style>
</head>
<body>
<h1>Farejador de Aluguéis</h1>
<nav>
  <a href="/" class="nav-link">Apartamentos</a>
  <a href="/sources" class="nav-link active">Fontes</a>
</nav>

<table>
  <thead>
    <tr>
      <th>Fonte</th>
      <th>Status</th>
      <th>Adicionada</th>
      <th>Ações</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>

<div class="add-form">
  <h3>Adicionar nova fonte</h3>
  <form method="POST" action="/sources/add">
    <div class="row">
      <div>
        <label>Nome (opcional)</label>
        <input name="label" placeholder="Ex: Botafogo 2q" autocomplete="off">
      </div>
      <div>
        <label>URL do VivaReal</label>
        <input name="url" placeholder="https://www.vivareal.com.br/aluguel/..." required autocomplete="off">
      </div>
      <button type="submit" class="btn-add">+ Adicionar</button>
    </div>
  </form>
</div>

<div class="add-form">
  <h3>Configurações</h3>
  <form method="POST" action="/settings">
    <div class="row">
      <div>
        <label>Preço total máximo (aluguel + condomínio + IPTU)</label>
        <input name="max_total_price" type="number" min="1" value="{max_total_price}" required>
      </div>
      <div>
        <label>Intervalo entre buscas (segundos)</label>
        <input name="interval_seconds" type="number" min="5" max="86400" value="{interval_seconds}" required>
      </div>
      <button type="submit" class="btn-add">Salvar</button>
    </div>
  </form>
  <form method="POST" action="/notify-test" style="margin-top:12px">
    <button type="submit" class="btn-add btn-toggle">🔔 Testar notificação</button>
  </form>
</div>
</body>
</html>"""

SOURCE_ROW = """<tr>
  <td>
    <div class="src-label">{label}</div>
    <span class="src-url" title="{url}">{url}</span>
  </td>
  <td><span class="{badge_class}">{badge_label}</span></td>
  <td style="font-size:12px;color:#999">{added_at}</td>
  <td style="display:flex;gap:6px">
    <form method="POST" action="/sources/toggle/{sid}">
      <button type="submit" class="btn-toggle">{toggle_label}</button>
    </form>
    <form method="POST" action="/sources/delete/{sid}" onsubmit="return confirm('Remover esta fonte?')">
      <button type="submit" class="btn-danger">Remover</button>
    </form>
  </td>
</tr>"""


@app.route("/sources")
def sources():
    init_db()
    rows = []
    for s in get_sources():
        is_active = bool(s["active"])
        added = s["added_at"][:16].replace("T", " ") if s["added_at"] else "—"
        rows.append(SOURCE_ROW.format(
            sid=s["id"],
            label=s["label"] or "—",
            url=s["url"],
            badge_class="badge-active" if is_active else "badge-paused",
            badge_label="Ativa" if is_active else "Pausada",
            toggle_label="Pausar" if is_active else "Ativar",
            added_at=added,
        ))
    body = "\n".join(rows) if rows else '<tr><td colspan="4" class="empty">Nenhuma fonte cadastrada.</td></tr>'
    return SOURCES_TEMPLATE.format(rows=body, **get_settings())


@app.route("/notify-test", methods=["POST"])
def notify_test():
    from notifier import notify
    notify("Farejador", "Notificações funcionando! Você será avisado de novos apartamentos.")
    return redirect(url_for("sources"))


@app.route("/settings", methods=["POST"])
def settings_save():
    for key, lo, hi in (("max_total_price", 1, 10_000_000), ("interval_seconds", 5, 86400)):
        raw = request.form.get(key, "").strip()
        try:
            value = int(raw)
        except ValueError:
            continue  # ignore garbage, keep the stored value
        set_setting(key, max(lo, min(hi, value)))
    return redirect(url_for("sources"))


@app.route("/sources/add", methods=["POST"])
def source_add():
    url = request.form.get("url", "").strip()
    label = request.form.get("label", "").strip()
    if url:
        add_source(url, label)
    return redirect(url_for("sources"))


@app.route("/sources/delete/<int:sid>", methods=["POST"])
def source_delete(sid):
    delete_source(sid)
    return redirect(url_for("sources"))


@app.route("/sources/toggle/<int:sid>", methods=["POST"])
def source_toggle(sid):
    toggle_source(sid)
    return redirect(url_for("sources"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8080)
