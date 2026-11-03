import os

# New Modern Pure-CSS Badge HTML template for Flask print page:
print_html_content = """<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
<meta charset="utf-8">
<title>Impression Badges — {{ settings.inst_name }}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.6/dist/JsBarcode.all.min.js"></script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Roboto', sans-serif; background: #eef1f6; padding: 24px; color: #0B3D6E; }
.toolbar { max-width: 880px; margin: 0 auto 16px; display: flex; gap: 10px; align-items: center; }
.toolbar button, .toolbar a { padding: 9px 16px; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; text-decoration: none; }
.btn-print { background: #C8102E; color: #fff; box-shadow: 0 2px 6px rgba(200,16,46,0.3); }
.btn-back { background: #fff; color: #0B3D6E; border: 1px solid #d5dbe4; }

.page { max-width: 880px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; align-items: center; }

/* ============================================================
   CR80 BADGE CARD (85.6mm x 54mm | Aspect 1.585)
   Pure Layered CSS — Zero Background Image Dependencies!
   ============================================================ */
.badge-card {
  width: 85.6mm;
  height: 54mm;
  border-radius: 3.2mm;
  overflow: hidden;
  position: relative;
  box-shadow: 0 12px 30px rgba(11, 61, 110, 0.35);
  background: linear-gradient(135deg, #071322 0%, #0B3D6E 55%, #155DA8 100%);
  display: flex;
  flex-direction: column;
  user-select: none;
  container-type: inline-size;
  page-break-inside: avoid;
  break-inside: avoid;
  color: #ffffff;
}

/* Ambient Glow Corner Accents */
.badge-card::before {
  content: '';
  position: absolute;
  top: -30px;
  right: -30px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(240, 160, 46, 0.3) 0%, transparent 70%);
  pointer-events: none;
}
.badge-card::after {
  content: '';
  position: absolute;
  bottom: -30px;
  left: -30px;
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(200, 16, 46, 0.35) 0%, transparent 70%);
  pointer-events: none;
}

/* Diagonal Overlay Wave */
.bg-wave {
  position: absolute;
  top: 0;
  right: 0;
  width: 55%;
  height: 100%;
  background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0) 100%);
  clip-path: polygon(25% 0, 100% 0, 100% 100%, 0% 100%);
  pointer-events: none;
}

/* Top Accent Ribbon (Red to Gold) */
.top-ribbon {
  height: 3.5px;
  width: 100%;
  background: linear-gradient(90deg, #C8102E 0%, #E02038 50%, #F0A02E 100%);
}

/* Header Area */
.card-header {
  padding: 6px 12px 2px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 2;
}
.brand-box {
  display: flex;
  align-items: center;
  gap: 6px;
}
.logo-img {
  height: 18px;
  object-fit: contain;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3));
}
.brand-logo-text {
  display: flex;
  flex-direction: column;
}
.brand-name {
  font-family: 'Montserrat', sans-serif;
  font-size: 11px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 1px;
  line-height: 1;
}
.brand-name span {
  color: #F0A02E;
}
.brand-sub {
  font-size: 5.5px;
  color: rgba(255, 255, 255, 0.75);
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-top: 1.5px;
}
.year-pill {
  background: rgba(255, 255, 255, 0.12);
  border: 0.5px solid rgba(255, 255, 255, 0.25);
  border-radius: 8px;
  padding: 2px 7px;
  font-size: 7px;
  font-weight: 700;
  color: #FFD47A;
  letter-spacing: 0.8px;
}

/* Body Content Area */
.card-body {
  flex: 1;
  display: flex;
  padding: 3px 12px 4px 12px;
  gap: 10px;
  z-index: 2;
  align-items: center;
}

/* Left Column: Photo Frame */
.left-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}
.photo-frame {
  width: 50px;
  height: 64px;
  border-radius: 6px;
  overflow: hidden;
  border: 1.8px solid #F0A02E;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
  background: linear-gradient(145deg, #1e293b, #0f172a);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #F0A02E;
  font-family: 'Montserrat', sans-serif;
  font-weight: 800;
  font-size: 22px;
}
.photo-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Right Column: Details */
.right-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2.5px;
  min-width: 0;
}

.person-name {
  font-family: 'Montserrat', sans-serif;
  font-size: 13.5px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 0.4px;
  line-height: 1.1;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 1px 3px rgba(0,0,0,0.4);
}

.role-tag-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.role-badge {
  background: linear-gradient(90deg, #C8102E 0%, #E02038 100%);
  color: #ffffff;
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px;
  font-weight: 700;
  letter-spacing: 0.6px;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: uppercase;
  box-shadow: 0 2px 5px rgba(200, 16, 46, 0.4);
  white-space: nowrap;
}
.id-code-text {
  font-family: 'Montserrat', sans-serif;
  font-size: 8.5px;
  font-weight: 700;
  color: #F0A02E;
  letter-spacing: 0.8px;
}

/* Contact Rows */
.contact-group {
  display: flex;
  flex-direction: column;
  gap: 1.5px;
  margin-top: 1px;
}
.contact-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 7.5px;
  color: rgba(255, 255, 255, 0.92);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.contact-item svg {
  flex-shrink: 0;
  color: #F0A02E;
}

/* Language Flags Spheres */
.flags-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 1.5px;
}
.flag-sphere {
  width: 15px;
  height: 15px;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  background: #fff;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.flag-sphere svg {
  width: 100%;
  height: 100%;
}

/* Footer Section with QR & Barcode */
.card-footer {
  padding: 3px 12px 4px 12px;
  background: rgba(0, 0, 0, 0.28);
  border-top: 0.5px solid rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 2;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 6px;
}
.qr-box {
  width: 24px;
  height: 24px;
  background: #ffffff;
  border-radius: 3px;
  padding: 1.5px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
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
  font-size: 8px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
}
.footer-sub {
  font-size: 6px;
  color: rgba(255, 255, 255, 0.65);
}

.barcode-box {
  background: #ffffff;
  border-radius: 3px;
  padding: 1.5px 4px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.barcode-box svg {
  height: 18px;
  width: 85px;
}

@media print {
  .toolbar { display: none !important; }
  body { background: #fff !important; padding: 0 !important; }
  .page { gap: 0 !important; }
  .badge-card { box-shadow: none !important; margin-bottom: 5mm; }
}
</style>
</head>
<body>

<div class="toolbar">
  <button class="btn-print" onclick="window.print()">🖨️ Imprimer les Badges</button>
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

<div class="badge-card">
  <div class="top-ribbon"></div>
  <div class="bg-wave"></div>

  <!-- Header -->
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

  <!-- Body -->
  <div class="card-body">
    <!-- Left: Photo Frame -->
    <div class="left-col">
      <div class="photo-frame">
        {% if s and s.photo %}
          <img src="{{ url_for('static', filename='uploads/' ~ s.photo) }}" alt="{{ full_name }}">
        {% else %}
          <span>{{ full_name[0] if full_name else 'S' }}</span>
        {% endif %}
      </div>
    </div>

    <!-- Right: Details -->
    <div class="right-col">
      <div class="person-name" title="{{ full_name }}">{{ full_name }}</div>

      <div class="role-tag-row">
        <div class="role-badge">{{ role_label }}</div>
        <div class="id-code-text">#{{ code_val }}</div>
      </div>

      <div class="contact-group">
        <div class="contact-item" title="{{ phone_val }}">
          <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
          {{ phone_val }}
        </div>
        <div class="contact-item" title="{{ email_val }}">
          <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
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

  <!-- Footer -->
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
</script>
</body>
</html>
"""

# Write updated Flask print template
print_template_path = r'c:\Users\Meriem\Downloads\workspace-019fe29e-8f2a-76f2-84d0-8810f12b929a\institut\templates\badges\print.html'
with open(print_template_path, 'w', encoding='utf-8') as f:
    f.write(print_html_content)

print("Updated print.html successfully.")
