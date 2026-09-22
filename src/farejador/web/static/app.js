// Farejador de Aluguéis — aba Apartamentos.
// `freshListings` é definido pela página (index.html) antes deste arquivo carregar.

// ---- Lightbox ----
let lbImgs = [], lbIdx = 0;

function openLb(imgs, idx) {
  lbImgs = imgs; lbIdx = idx;
  document.getElementById('lightbox').classList.add('open');
  lbShow();
}

function lbShow() {
  document.getElementById('lb-img').src = lbImgs[lbIdx];
  document.getElementById('lb-counter').textContent = (lbIdx + 1) + ' / ' + lbImgs.length;
}

function lbStep(d) {
  lbIdx = (lbIdx + d + lbImgs.length) % lbImgs.length;
  lbShow();
}

function closeLb() {
  document.getElementById('lightbox').classList.remove('open');
  document.getElementById('lb-img').src = '';
}

document.getElementById('lightbox').addEventListener('click', function(e) {
  if (e.target === this) closeLb();
});

// ---- Detail modal ----
function openDetail(d) {
  document.getElementById('dm-title').textContent = d.title || '—';
  var addr = [d.street, d.neighborhood].filter(Boolean).join(', ') || '—';
  document.getElementById('dm-addr').textContent = addr;

  // Gallery
  var gallery = document.getElementById('dm-gallery');
  gallery.innerHTML = '';
  var imgs = d.images || [];
  if (imgs.length) {
    imgs.forEach(function(src, i) {
      var img = document.createElement('img');
      img.src = src;
      img.loading = 'lazy';
      img.onclick = function(e) { e.stopPropagation(); openLb(imgs, i); };
      gallery.appendChild(img);
    });
  } else {
    gallery.innerHTML = '<span class="no-gallery">Sem fotos disponíveis</span>';
  }

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
  if (d.posted_at) {
    var parts = d.posted_at.split('-');
    meta.push('Publicado ' + parts[2] + '/' + parts[1] + (parts[0] ? '/' + parts[0].slice(2) : ''));
  }
  document.getElementById('dm-meta').innerHTML = meta.map(function(s) { return '<span>' + s + '</span>'; }).join('');

  document.getElementById('dm-open-btn').href = d.url || '#';
  document.getElementById('detail-modal').classList.add('open');
}

function closeDetail() {
  document.getElementById('detail-modal').classList.remove('open');
}

document.getElementById('detail-modal').addEventListener('click', function(e) {
  if (e.target === this) closeDetail();
});

document.addEventListener('keydown', function(e) {
  if (document.getElementById('lightbox').classList.contains('open')) {
    if (e.key === 'ArrowLeft')  lbStep(-1);
    if (e.key === 'ArrowRight') lbStep(1);
    if (e.key === 'Escape') closeLb();
    return;
  }
  if (document.getElementById('detail-modal').classList.contains('open')) {
    if (e.key === 'Escape') closeDetail();
  }
});

// ---- Hide-viewed toggle ----
var checkedHidden = false;
function toggleChecked() {
  checkedHidden = !checkedHidden;
  document.querySelectorAll('tr.checked').forEach(function(r) {
    r.style.display = checkedHidden ? 'none' : '';
  });
  document.getElementById('toggle-checked-btn').textContent =
    checkedHidden ? 'Mostrar vistos' : 'Ocultar vistos';
}

// ---- Fresh-listing browser notifications ----
function showToast(msg) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.remove('show');
  void t.offsetWidth; // restart animation
  t.classList.add('show');
  setTimeout(function() { t.classList.remove('show'); }, 5000);
}

function sendFreshNotifications(toNotify) {
  if (!toNotify.length) return;
  var tag = 'fresh-' + Date.now();
  if (toNotify.length === 1) {
    var l = toNotify[0];
    showToast('Novo apartamento: ' + l.title + ' · R$ ' + (l.price || 0).toLocaleString('pt-BR') + '/mês');
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Novo apartamento!', {
        body: l.title + ' · R$ ' + (l.price || 0).toLocaleString('pt-BR') + '/mês · ' + l.neighborhood,
        tag: tag
      });
    }
  } else {
    showToast(toNotify.length + ' novos apartamentos encontrados!');
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(toNotify.length + ' novos apartamentos!', {
        body: toNotify.slice(0, 3).map(function(l) { return l.title; }).join(' | ') + (toNotify.length > 3 ? ' …' : ''),
        tag: tag
      });
    }
  }
}

function notifyUnseen(fresh) {
  var stored = localStorage.getItem('notified_ids');
  var notifiedIds = new Set(stored ? JSON.parse(stored) : []);
  var toNotify = fresh.filter(function(l) { return !notifiedIds.has(l.id); });
  if (toNotify.length) {
    sendFreshNotifications(toNotify);
    toNotify.forEach(function(l) { notifiedIds.add(l.id); });
    localStorage.setItem('notified_ids', JSON.stringify(Array.from(notifiedIds)));
  }
}

function enableNotifications() {
  Notification.requestPermission().then(function(perm) {
    var btn = document.getElementById('enable-notif-btn');
    if (perm === 'granted') {
      btn.style.display = 'none';
      notifyUnseen(freshListings);
    } else {
      btn.textContent = '🔕 Notificações bloqueadas';
      btn.style.background = '#999';
    }
  });
}

if ('Notification' in window) {
  if (Notification.permission === 'granted') {
    notifyUnseen(freshListings);
  } else if (Notification.permission !== 'denied') {
    document.getElementById('enable-notif-btn').style.display = '';
  }
}

// ---- Auto-refresh (polls /fragment every 30 s) ----
setInterval(function() {
  fetch('/fragment')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      document.querySelector('tbody').innerHTML = data.rows;
      document.querySelector('.stats span').innerHTML = data.stats;
      if (checkedHidden) {
        document.querySelectorAll('tr.checked').forEach(function(r) { r.style.display = 'none'; });
      }
      if (data.fresh.length && 'Notification' in window && Notification.permission === 'granted') {
        notifyUnseen(data.fresh);
      }
    });
}, 30000);
