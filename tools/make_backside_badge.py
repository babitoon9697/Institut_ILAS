import os

# Complete, perfected Dual-Tone Front (Recto) + Back (Verso) HTML template for Flask print page:
print_html_content = """<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
<meta charset="utf-8">
<title>Impression Badges (Recto / Verso) — {{ settings.inst_name }}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Roboto:wght@500;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.6/dist/JsBarcode.all.min.js"></script>

<style>
/* ============================================================
   FORCE EXACT COLOR PRINTING IN ALL BROWSERS (CHROME/EDGE/FIREFOX)
   ============================================================ */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
  color-adjust: exact !important;
}

body {
  font-family: 'Roboto', sans-serif;
  background: #eef1f6;
  padding: 24px;
  color: #0B3D6E;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

.toolbar { max-width: 880px; margin: 0 auto 16px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.toolbar button, .toolbar a { padding: 9px 16px; border: none; border-radius: 8px; font-size: 13px; font-weight: 700; cursor: pointer; text-decoration: none; }
.btn-print { background: #C8102E !important; color: #fff !important; box-shadow: 0 3px 10px rgba(200,16,46,0.35); }
.btn-back { background: #fff; color: #0B3D6E; border: 1px solid #d5dbe4; }
.btn-toggle { background: #0B3D6E; color: #fff; }

.page { max-width: 880px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; align-items: center; }

.card-pair {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  justify-content: center;
  page-break-after: always;
  break-after: page;
}

/* ============================================================
   CR80 BADGE CARD CONTAINER (85.6mm x 54mm)
   ============================================================ */
.badge-card {
  width: 85.6mm;
  height: 54mm;
  border-radius: 3.5mm;
  overflow: hidden;
  position: relative;
  box-shadow: 0 14px 36px rgba(11, 61, 110, 0.28), 0 0 0 1px rgba(11, 61, 110, 0.2);
  background: #ffffff !important;
  display: flex;
  flex-direction: column;
  user-select: none;
  container-type: inline-size;
  page-break-inside: avoid;
  break-inside: avoid;
  color: #0B3D6E;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

/* Header Luxury Navy Gradient Block (14.5mm) */
.card-header-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 14.5mm;
  background: linear-gradient(135deg, #06101E 0%, #0B3D6E 60%, #155DA8 100%) !important;
  z-index: 1;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

/* Curved Red Accent Ribbon */
.accent-wave {
  position: absolute;
  top: 12.8mm;
  left: -2mm;
  width: 105%;
  height: 3.2mm;
  background: linear-gradient(90deg, #C8102E 0%, #E02038 60%, #F0A02E 100%) !important;
  transform: rotate(-1.5deg);
  z-index: 2;
  box-shadow: 0 2px 5px rgba(0,0,0,0.25);
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

/* Header Content */
.card-header {
  height: 13.5mm;
  padding: 1.8mm 3.5mm 0 3.5mm;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 3;
  color: #ffffff !important;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.brand-box {
  display: flex;
  align-items: center;
  gap: 2mm;
}
.logo-img {
  height: 6mm;
  object-fit: contain;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.4));
}
.brand-logo-text {
  display: flex;
  flex-direction: column;
}
.brand-name {
  font-family: 'Montserrat', sans-serif;
  font-size: 11px;
  font-weight: 900;
  color: #ffffff !important;
  letter-spacing: 0.8px;
  line-height: 1;
}
.brand-name span {
  color: #FFD47A !important;
}
.brand-sub {
  font-size: 5.2px;
  color: rgba(255, 255, 255, 0.85) !important;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  font-weight: 700;
  margin-top: 1px;
}
.year-pill {
  background: rgba(255, 255, 255, 0.18) !important;
  border: 0.5px solid rgba(255, 255, 255, 0.35) !important;
  border-radius: 10px;
  padding: 1px 6px;
  font-size: 7px;
  font-weight: 800;
  color: #FFD47A !important;
  letter-spacing: 0.8px;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

/* ============================================================
   FRONT SIDE (RECTO) CONTENT
   ============================================================ */
.card-body {
  flex: 1;
  display: flex;
  padding: 3mm 3.5mm 1mm 3.5mm;
  gap: 3.5mm;
  z-index: 3;
  align-items: center;
}
.left-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  z-index: 4;
}
.photo-frame {
  width: 15mm;
  height: 19.5mm;
  border-radius: 2.2mm;
  overflow: hidden;
  border: 0.8mm solid #C8102E !important;
  box-shadow: 0 4px 10px rgba(11, 61, 110, 0.3);
  background: linear-gradient(145deg, #0B3D6E, #071322) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFD47A !important;
  font-family: 'Montserrat', sans-serif;
  font-weight: 900;
  font-size: 22px;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.photo-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.right-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.person-name {
  font-family: 'Montserrat', sans-serif;
  font-size: 15.5px;
  font-weight: 900;
  color: #0B3D6E !important;
  letter-spacing: 0.3px;
  line-height: 1.1;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.role-tag-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 1px;
}
.role-badge {
  background: linear-gradient(90deg, #C8102E 0%, #E02038 100%) !important;
  color: #ffffff !important;
  font-family: 'Montserrat', sans-serif;
  font-size: 8.5px;
  font-weight: 800;
  letter-spacing: 0.6px;
  padding: 2.5px 10px;
  border-radius: 10px;
  text-transform: uppercase;
  box-shadow: 0 2px 5px rgba(200, 16, 46, 0.35);
  white-space: nowrap;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.id-code-text {
  font-family: 'Roboto', sans-serif;
  font-size: 10px;
  font-weight: 800;
  color: #F0A02E !important;
  letter-spacing: 0.5px;
}
.contact-group {
  display: flex;
  flex-direction: column;
  gap: 1.8px;
  margin-top: 2px;
}
.contact-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 8.8px;
  color: #1e293b !important;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.contact-item svg {
  flex-shrink: 0;
  color: #C8102E !important;
}
.flags-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}
.flag-sphere {
  width: 15.5px;
  height: 15.5px;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.25);
  background: #fff !important;
  border: 0.5px solid #cbd5e1;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.flag-sphere svg {
  width: 100%;
  height: 100%;
}
.card-footer {
  height: 10.5mm;
  padding: 0 3.5mm;
  background: #f8fafc !important;
  border-top: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 3;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.footer-left {
  display: flex;
  align-items: center;
  gap: 6px;
}
.qr-box {
  width: 8.5mm;
  height: 8.5mm;
  background: #ffffff !important;
  border-radius: 1mm;
  border: 1px solid #cbd5e1;
  padding: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.qr-box img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.footer-text {
  display: flex;
  flex-direction: column;
}
.footer-id {
  font-size: 8.5px;
  font-weight: 800;
  color: #0B3D6E !important;
  letter-spacing: 0.5px;
}
.footer-sub {
  font-size: 6px;
  color: #64748b !important;
  font-weight: 700;
}
.barcode-box {
  background: #ffffff !important;
  border-radius: 1mm;
  border: 1px solid #cbd5e1;
  padding: 1px 4px;
  height: 7mm;
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.barcode-box svg {
  height: 6mm;
  width: 90px;
}

/* ============================================================
   BACK SIDE (VERSO) CONTENT
   ============================================================ */
.back-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 3mm 4mm 2mm 4mm;
  z-index: 3;
  justify-content: space-between;
}

.conditions-box {
  display: flex;
  flex-direction: column;
  gap: 1.5px;
  margin-top: 1mm;
}
.cond-title {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px;
  font-weight: 900;
  color: #0B3D6E !important;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-bottom: 1px;
}
.cond-list {
  display: flex;
  flex-direction: column;
  gap: 1.8px;
  font-size: 6.8px;
  line-height: 1.25;
  color: #1e293b !important;
  font-weight: 700;
}
.cond-item {
  display: flex;
  gap: 3px;
  align-items: flex-start;
}
.cond-item span.num {
  color: #C8102E !important;
  font-weight: 900;
  flex-shrink: 0;
}

.back-bottom {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 4mm;
  margin-top: 1.5mm;
  padding-top: 1.5mm;
  border-top: 0.8px dashed #cbd5e1;
}

.stamp-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
}
.stamp-title {
  font-size: 5.5px;
  font-weight: 800;
  color: #64748b !important;
  text-transform: uppercase;
}
.stamp-area {
  width: 22mm;
  height: 9mm;
  border: 0.8px dashed #0B3D6E;
  border-radius: 1mm;
  background: rgba(11, 61, 110, 0.03) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 5px;
  color: #94a3b8 !important;
  font-weight: 700;
}

.notice-pill {
  flex: 1;
  background: #f1f5f9 !important;
  border-left: 2px solid #C8102E !important;
  border-radius: 1mm;
  padding: 1.5px 4px;
  font-size: 6px;
  line-height: 1.2;
  color: #334155 !important;
  font-weight: 700;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

.back-footer {
  height: 7mm;
  padding: 0 4mm;
  background: #0B3D6E !important;
  color: #ffffff !important;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 6px;
  font-weight: 800;
  z-index: 3;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.back-footer span {
  color: #FFD47A !important;
}

@media print {
  *, *::before, *::after {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
  }
  .toolbar { display: none !important; }
  body { background: #fff !important; padding: 0 !important; }
  .page { gap: 0 !important; }
  .card-pair { page-break-after: always; break-after: page; margin-bottom: 5mm; }
}
</style>
</head>
<body>

<div class="toolbar">
  <button class="btn-print" onclick="window.print()">🖨️ Imprimer les Badges (Recto + Verso)</button>
  <button class="btn-toggle" onclick="toggleView('both')">📄 View Both</button>
  <button class="btn-toggle" onclick="toggleView('recto')">🔴 Recto Only</button>
  <button class="btn-toggle" onclick="toggleView('verso')">🔵 Verso Only</button>
  <a class="btn-back" href="javascript:history.back()">← Retour</a>
  <span style="color:#5b6472;font-size:12px">{{ cards|length }} badge(s) · CR80 (85.6 × 54 mm)</span>
</div>

<div class="page">
{% for c in cards %}
{% set s = c.student %}
{% set role_label = (c.record.badge_type|upper if c.record and c.record.badge_type else 'STUDENT') %}
{% set code_val = (s.code if s and s.code else (s.id|string if s else '1234567890')) %}
{% set phone_val = (s.phone if s and s.phone else (settings.inst_phone or '+33 6 12 34 56 78')) %}
{% set email_val = (s.email if s and s.email else (settings.inst_email or 'info@ilas-ecole.com')) %}
{% set full_name = ((s.first_name|upper ~ ' ' ~ s.last_name|upper) if s else 'SARA ALAOUI') %}

<div class="card-pair">
  <!-- RECTO (FRONT SIDE) -->
  <div class="badge-card card-recto">
    <div class="card-header-bg"></div>
    <div class="accent-wave"></div>

    <div class="card-header">
      <div class="brand-box">
        <img class="logo-img" src="{{ url_for('static', filename='uploads/logo-ilas.png') }}" onerror="this.style.display='none'">
        <div class="brand-logo-text">
          <div class="brand-name">INSTITUT <span>ILAS</span></div>
          <div class="brand-sub">LANGUES & FORMATION CONTINUE</div>
        </div>
      </div>
      <div class="year-pill">{{ settings.school_year or '2025/2026' }}</div>
    </div>

    <div class="card-body">
      <div class="left-col">
        <div class="photo-frame">
          {% if s and s.photo %}
            <img src="{{ url_for('static', filename='uploads/' ~ s.photo) }}" alt="{{ full_name }}">
          {% else %}
            <span>{{ full_name[0] if full_name else 'S' }}</span>
          {% endif %}
        </div>
      </div>

      <div class="right-col">
        <div class="person-name" title="{{ full_name }}">{{ full_name }}</div>

        <div class="role-tag-row">
          <div class="role-badge">{{ role_label }}</div>
          <div class="id-code-text">ID: #{{ code_val }}</div>
        </div>

        <div class="contact-group">
          <div class="contact-item" title="{{ phone_val }}">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            {{ phone_val }}
          </div>
          <div class="contact-item" title="{{ email_val }}">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
            {{ email_val }}
          </div>
        </div>

        <div class="flags-bar">
          <div class="flag-sphere"><svg viewBox="0 0 60 60"><clipPath id="u{{ loop.index }}"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#u{{ loop.index }})"><rect width="60" height="60" fill="#00247D"/><path d="M0,0 L60,60 M60,0 L0,60" stroke="#FFF" stroke-width="10"/><path d="M0,0 L60,60 M60,0 L0,60" stroke="#CF142B" stroke-width="6"/><path d="M30,0 V60 M0,30 H60" stroke="#FFF" stroke-width="14"/><path d="M30,0 V60 M0,30 H60" stroke="#CF142B" stroke-width="8"/></g></svg></div>
          <div class="flag-sphere"><svg viewBox="0 0 60 60"><clipPath id="b{{ loop.index }}"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#b{{ loop.index }})"><rect x="0" y="0" width="20" height="60" fill="#000"/><rect x="20" y="0" width="20" height="60" fill="#FDDA24"/><rect x="40" y="0" width="20" height="60" fill="#EF3340"/></g></svg></div>
          <div class="flag-sphere"><svg viewBox="0 0 60 60"><clipPath id="f{{ loop.index }}"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#f{{ loop.index }})"><rect x="0" y="0" width="20" height="60" fill="#002654"/><rect x="20" y="0" width="20" height="60" fill="#FFF"/><rect x="40" y="0" width="20" height="60" fill="#CE1126"/></g></svg></div>
          <div class="flag-sphere"><svg viewBox="0 0 60 60"><clipPath id="e{{ loop.index }}"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#e{{ loop.index }})"><rect x="0" y="0" width="60" height="15" fill="#AA1529"/><rect x="0" y="15" width="60" height="30" fill="#F1BF00"/><rect x="0" y="45" width="60" height="15" fill="#AA1529"/></g></svg></div>
        </div>
      </div>
    </div>

    <div class="card-footer">
      <div class="footer-left">
        <div class="qr-box">
          {% if c.qr %}
            <img src="{{ c.qr }}" alt="QR Code">
          {% endif %}
        </div>
        <div class="footer-text">
          <div class="footer-id">ID: {{ code_val }}</div>
          <div class="footer-sub">ILAS CARTE OFFICIELLE</div>
        </div>
      </div>
      <div class="barcode-box">
        <svg class="barcode-svg" data-code="{{ code_val }}"></svg>
      </div>
    </div>
  </div>

  <!-- VERSO (BACK SIDE) -->
  <div class="badge-card card-verso">
    <div class="card-header-bg"></div>
    <div class="accent-wave"></div>

    <div class="card-header">
      <div class="brand-box">
        <img class="logo-img" src="{{ url_for('static', filename='uploads/logo-ilas.png') }}" onerror="this.style.display='none'">
        <div class="brand-logo-text">
          <div class="brand-name">INSTITUT <span>ILAS</span></div>
          <div class="brand-sub">RÈGLEMENT INTÉRIEUR & CONDITIONS</div>
        </div>
      </div>
      <div class="year-pill">VERSO</div>
    </div>

    <div class="back-body">
      <div class="conditions-box">
        <div class="cond-title">Conditions Générales d'Utilisation :</div>
        <div class="cond-list">
          {% if conditions %}
            {% for line in conditions.splitlines() %}
              {% if line.strip() %}
                <div class="cond-item"><span class="num">•</span> <div>{{ line.strip() }}</div></div>
              {% endif %}
            {% endfor %}
          {% else %}
            <div class="cond-item"><span class="num">1.</span> <div>Cette carte est strictement personnelle, nominative et incessible.</div></div>
            <div class="cond-item"><span class="num">2.</span> <div>Obligatoire pour accéder aux salles de cours et événements de l'institut.</div></div>
            <div class="cond-item"><span class="num">3.</span> <div>En cas de perte ou vol, signaler immédiatement à l'administration.</div></div>
            <div class="cond-item"><span class="num">4.</span> <div>Demeure la propriété exclusive de l'INSTITUT ILAS.</div></div>
          {% endif %}
        </div>
      </div>

      <div class="back-bottom">
        <div class="stamp-box">
          <div class="stamp-title">Cachet & Signature</div>
          <div class="stamp-area">Direction ILAS</div>
        </div>
        <div class="notice-pill">
          ⚠️ Si vous trouvez cette carte, merci de bien vouloir la retourner à l'accueil de l'INSTITUT ILAS.
        </div>
      </div>
    </div>

    <div class="back-footer">
      <div>📞 {{ settings.inst_phone or '+33 6 12 34 56 78' }}</div>
      <div>🌐 <span>www.ilas-ecole.com</span></div>
    </div>
  </div>
</div>
{% else %}
  <div style="text-align:center;padding:60px;color:#8a93a3">Aucun badge sélectionné.</div>
{% endfor %}
</div>

<script>
  document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.barcode-svg').forEach(function(el) {
      var code = el.getAttribute('data-code');
      if (code) {
        try {
          JsBarcode(el, code, {
            format: "CODE128",
            displayValue: false,
            margin: 0,
            lineColor: "#0B3D6E",
            background: "#ffffff",
            height: 18
          });
        } catch(e) { console.warn(e); }
      }
    });
  });

  function toggleView(mode) {
    var rectos = document.querySelectorAll('.card-recto');
    var versos = document.querySelectorAll('.card-verso');
    if (mode === 'recto') {
      rectos.forEach(r => r.style.display = 'flex');
      versos.forEach(v => v.style.display = 'none');
    } else if (mode === 'verso') {
      rectos.forEach(r => r.style.display = 'none');
      versos.forEach(v => v.style.display = 'flex');
    } else {
      rectos.forEach(r => r.style.display = 'flex');
      versos.forEach(v => v.style.display = 'flex');
    }
  }
</script>
</body>
</html>
"""

# Write updated Flask print template
print_template_path = r'c:\Users\Meriem\Downloads\workspace-019fe29e-8f2a-76f2-84d0-8810f12b929a\institut\templates\badges\print.html'
with open(print_template_path, 'w', encoding='utf-8') as f:
    f.write(print_html_content)

print("Updated print.html with Recto & Verso cards successfully.")
