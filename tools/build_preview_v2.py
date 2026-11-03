import os

html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Badge ILAS — Live Interactive Preview</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Roboto:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.6/dist/JsBarcode.all.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Roboto', sans-serif;
  background: #f4f7fc;
  color: #0B3D6E;
  padding: 30px 20px;
}
.container {
  max-width: 1060px;
  margin: 0 auto;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e2e8f0;
}
.title {
  font-family: 'Montserrat', sans-serif;
  font-size: 24px;
  font-weight: 800;
  color: #0B3D6E;
}
.subtitle {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}
.toggle-bar {
  display: flex;
  background: #e2e8f0;
  border-radius: 8px;
  padding: 4px;
  gap: 4px;
}
.toggle-btn {
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-family: 'Montserrat', sans-serif;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  background: transparent;
  color: #0B3D6E;
  transition: all 0.2s;
}
.toggle-btn.active {
  background: #C8102E;
  color: #ffffff;
  box-shadow: 0 2px 6px rgba(200, 16, 46, 0.3);
}

.layout {
  display: flex;
  gap: 32px;
  align-items: flex-start;
  flex-wrap: wrap;
}
.card-wrap {
  flex: 1 1 460px;
  max-width: 540px;
}

/* ============================================================
   CR80 BADGE CARD (85.6mm x 54mm | Aspect 1.585)
   Pure Layered CSS Architecture — Zero Background Image Overhead!
   ============================================================ */
.badge-card {
  width: 100%;
  aspect-ratio: 1.585 / 1;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 16px 40px rgba(11, 61, 110, 0.35);
  background: linear-gradient(135deg, #071322 0%, #0B3D6E 55%, #155DA8 100%);
  display: flex;
  flex-direction: column;
  user-select: none;
  container-type: inline-size;
  color: #ffffff;
}

.badge-card::before {
  content: '';
  position: absolute;
  top: -30px;
  right: -30px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(240, 160, 46, 0.3) 0%, transparent 70%);
  pointer-events: none;
}
.badge-card::after {
  content: '';
  position: absolute;
  bottom: -30px;
  left: -30px;
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(200, 16, 46, 0.35) 0%, transparent 70%);
  pointer-events: none;
}

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

.top-ribbon {
  height: 4px;
  width: 100%;
  background: linear-gradient(90deg, #C8102E 0%, #E02038 50%, #F0A02E 100%);
}

.card-header {
  padding: 1.8cqw 3.5cqw 0.8cqw 3.5cqw;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 2;
}
.brand-box {
  display: flex;
  align-items: center;
  gap: 1.8cqw;
}
.brand-logo-text {
  display: flex;
  flex-direction: column;
}
.brand-name {
  font-family: 'Montserrat', sans-serif;
  font-size: 3.2cqw;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 1px;
  line-height: 1;
}
.brand-name span {
  color: #F0A02E;
}
.brand-sub {
  font-size: 1.6cqw;
  color: rgba(255, 255, 255, 0.75);
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-top: 0.4cqw;
}
.year-pill {
  background: rgba(255, 255, 255, 0.12);
  border: 0.5px solid rgba(255, 255, 255, 0.25);
  border-radius: 20px;
  padding: 0.6cqw 2.2cqw;
  font-size: 2cqw;
  font-weight: 700;
  color: #FFD47A;
  letter-spacing: 0.8px;
}

.card-body {
  flex: 1;
  display: flex;
  padding: 1cqw 3.5cqw 1.2cqw 3.5cqw;
  gap: 3cqw;
  z-index: 2;
  align-items: center;
}

.left-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}
.photo-frame {
  width: 14.5cqw;
  height: 18.5cqw;
  border-radius: 1.8cqw;
  overflow: hidden;
  border: 0.5cqw solid #F0A02E;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  background: linear-gradient(145deg, #1e293b, #0f172a);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #F0A02E;
  font-family: 'Montserrat', sans-serif;
  font-weight: 800;
  font-size: 6cqw;
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
  gap: 0.8cqw;
  min-width: 0;
}

.person-name {
  font-family: 'Montserrat', sans-serif;
  font-size: 4cqw;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 0.5px;
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
  gap: 1.8cqw;
}
.role-badge {
  background: linear-gradient(90deg, #C8102E 0%, #E02038 100%);
  color: #ffffff;
  font-family: 'Montserrat', sans-serif;
  font-size: 2.2cqw;
  font-weight: 700;
  letter-spacing: 0.6px;
  padding: 0.6cqw 2.4cqw;
  border-radius: 20px;
  text-transform: uppercase;
  box-shadow: 0 2px 5px rgba(200, 16, 46, 0.4);
  white-space: nowrap;
}
.id-code-text {
  font-family: 'Montserrat', sans-serif;
  font-size: 2.5cqw;
  font-weight: 700;
  color: #F0A02E;
  letter-spacing: 0.8px;
}

.contact-group {
  display: flex;
  flex-direction: column;
  gap: 0.5cqw;
  margin-top: 0.4cqw;
}
.contact-item {
  display: flex;
  align-items: center;
  gap: 1.2cqw;
  font-size: 2.2cqw;
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

.flags-bar {
  display: flex;
  align-items: center;
  gap: 1.2cqw;
  margin-top: 0.4cqw;
}
.flag-sphere {
  width: 4.2cqw;
  height: 4.2cqw;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  background: #ffffff;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.flag-sphere svg {
  width: 100%;
  height: 100%;
}

.card-footer {
  padding: 1cqw 3.5cqw 1.2cqw 3.5cqw;
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
  gap: 1.8cqw;
}
.qr-box {
  width: 6.8cqw;
  height: 6.8cqw;
  background: #ffffff;
  border-radius: 1cqw;
  padding: 0.4cqw;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.qr-box svg {
  width: 100% !important;
  height: 100% !important;
}
.footer-text {
  display: flex;
  flex-direction: column;
}
.footer-id {
  font-size: 2.3cqw;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
}
.footer-sub {
  font-size: 1.7cqw;
  color: rgba(255, 255, 255, 0.65);
}

.barcode-box {
  background: #ffffff;
  border-radius: 1cqw;
  padding: 0.4cqw 1.2cqw;
  height: 6.2cqw;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.barcode-box svg {
  height: 100%;
  width: 100%;
}

.actions-row {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}
.act-btn {
  padding: 10px 18px;
  border-radius: 8px;
  border: none;
  font-family: 'Montserrat', sans-serif;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  background: #C8102E;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(200, 16, 46, 0.35);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}
.act-btn:hover {
  background: #a80b23;
  transform: translateY(-1px);
}
.act-btn.sec {
  background: #ffffff;
  color: #0B3D6E;
  border: 1.5px solid #0B3D6E;
}

.edit-panel {
  flex: 1 1 360px;
  background: #ffffff;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #cbd5e1;
  box-shadow: 0 10px 25px rgba(11, 61, 110, 0.08);
}
.edit-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field label {
  font-size: 12px;
  font-weight: 600;
  color: #0B3D6E;
}
.field input {
  padding: 9px 12px;
  border-radius: 8px;
  border: 1.5px solid #cbd5e1;
  font-size: 13px;
  outline: none;
}
.field input:focus {
  border-color: #0B3D6E;
}

@media print {
  .header, .toggle-bar, .actions-row, .edit-panel {
    display: none !important;
  }
  body {
    background: none !important;
    padding: 0 !important;
  }
  .badge-card {
    width: 85.6mm !important;
    height: 54mm !important;
    box-shadow: none !important;
  }
}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <div class="title">🪪 Official ILAS Badge Generator</div>
        <div class="subtitle">100% Pure Layered CSS Design • CR80 (85.6mm × 54mm) • Zero Background Image Misalignment</div>
      </div>
      <div class="toggle-bar">
        <button id="btn-prev" class="toggle-btn active" onclick="setMode('preview')">👁️ Preview Mode</button>
        <button id="btn-edit" class="toggle-btn" onclick="setMode('edit')">✏️ Edit Mode</button>
      </div>
    </div>

    <div class="layout">
      <!-- CR80 CARD -->
      <div class="card-wrap">
        <div id="badgeCard" class="badge-card">
          <div class="top-ribbon"></div>
          <div class="bg-wave"></div>

          <!-- Header -->
          <div class="card-header">
            <div class="brand-box">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="#F0A02E"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
              <div class="brand-logo-text">
                <div class="brand-name">INSTITUT <span>ILAS</span></div>
                <div class="brand-sub">LANGUES & FORMATION CONTINUE</div>
              </div>
            </div>
            <div class="year-pill">2025/2026</div>
          </div>

          <!-- Body -->
          <div class="card-body">
            <!-- Left: Photo Frame -->
            <div class="left-col">
              <div class="photo-frame" id="ui-photo-box">
                <span id="ui-photo-initial">S</span>
              </div>
            </div>

            <!-- Right: Details -->
            <div class="right-col">
              <div class="person-name" id="ui-name">SARA ALAOUI</div>

              <div class="role-tag-row">
                <div class="role-badge" id="ui-role">LANGUAGE INSTRUCTOR</div>
                <div class="id-code-text" id="ui-id-code">#1234567890</div>
              </div>

              <div class="contact-group">
                <div class="contact-item">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#F0A02E" stroke-width="2.5"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  <span id="ui-phone">+33 6 12 34 56 78</span>
                </div>
                <div class="contact-item">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#F0A02E" stroke-width="2.5"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                  <span id="ui-email">info@ilas-ecole.com</span>
                </div>
              </div>

              <div class="flags-bar">
                <div class="flag-sphere"><svg viewBox="0 0 60 60"><clipPath id="uk"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#uk)"><rect width="60" height="60" fill="#00247D"/><path d="M0,0 L60,60 M60,0 L0,60" stroke="#FFF" stroke-width="10"/><path d="M0,0 L60,60 M60,0 L0,60" stroke="#CF142B" stroke-width="6"/><path d="M30,0 V60 M0,30 H60" stroke="#FFF" stroke-width="14"/><path d="M30,0 V60 M0,30 H60" stroke="#CF142B" stroke-width="8"/></g></svg></div>
                <div class="flag-sphere"><svg viewBox="0 0 60 60"><clipPath id="be"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#be)"><rect x="0" y="0" width="20" height="60" fill="#000"/><rect x="20" y="0" width="20" height="60" fill="#FDDA24"/><rect x="40" y="0" width="20" height="60" fill="#EF3340"/></g></svg></div>
                <div class="flag-sphere"><svg viewBox="0 0 60 60"><clipPath id="fr"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#fr)"><rect x="0" y="0" width="20" height="60" fill="#002654"/><rect x="20" y="0" width="20" height="60" fill="#FFF"/><rect x="40" y="0" width="20" height="60" fill="#CE1126"/></g></svg></div>
                <div class="flag-sphere"><svg viewBox="0 0 60 60"><clipPath id="es"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#es)"><rect x="0" y="0" width="60" height="15" fill="#AA1529"/><rect x="0" y="15" width="60" height="30" fill="#F1BF00"/><rect x="0" y="45" width="60" height="15" fill="#AA1529"/></g></svg></div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="card-footer">
            <div class="footer-left">
              <div class="qr-box" id="ui-qr"></div>
              <div class="footer-text">
                <div class="footer-id" id="ui-footer-id">ID: 1234567890</div>
                <div class="footer-sub">ILAS CARTE OFFICIELLE</div>
              </div>
            </div>

            <div class="barcode-box">
              <svg id="ui-barcode"></svg>
            </div>
          </div>
        </div>

        <div class="actions-row">
          <button class="act-btn" onclick="downloadPNG()">⬇️ Download PNG</button>
          <button class="act-btn" onclick="downloadPDF()">📄 Download PDF</button>
          <button class="act-btn sec" onclick="window.print()">🖨️ Print</button>
        </div>
      </div>

      <!-- EDIT PANEL -->
      <div id="editPanel" class="edit-panel" style="display: none;">
        <h3 style="color: #0B3D6E; margin-bottom: 16px; font-size: 16px;">Edit Dynamic Fields</h3>
        <div class="edit-grid">
          <div class="field"><label>Full Name</label><input id="in-name" value="SARA ALAOUI" oninput="update()"></div>
          <div class="field"><label>Role / Badge Label</label><input id="in-role" value="LANGUAGE INSTRUCTOR" oninput="update()"></div>
          <div class="field"><label>ID Number</label><input id="in-id" value="1234567890" oninput="update()"></div>
          <div class="field"><label>Phone</label><input id="in-phone" value="+33 6 12 34 56 78" oninput="update()"></div>
          <div class="field"><label>Email</label><input id="in-email" value="info@ilas-ecole.com" oninput="update()"></div>
          <div class="field"><label>Photo URL</label><input id="in-photo" placeholder="https://..." oninput="update()"></div>
          <div class="field"><label>QR Code Data</label><input id="in-qr" value="1234567890" oninput="update()"></div>
          <div class="field"><label>Barcode Data (CODE128)</label><input id="in-bc" value="1234567890" oninput="update()"></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    function update() {
      const name = document.getElementById('in-name').value || 'NAME SURNAME';
      const role = document.getElementById('in-role').value || 'ROLE';
      const id = document.getElementById('in-id').value || '1234567890';
      const phone = document.getElementById('in-phone').value || '+33 6 12 34 56 78';
      const email = document.getElementById('in-email').value || 'info@ilas-ecole.com';
      const photo = document.getElementById('in-photo').value;
      const qrData = document.getElementById('in-qr').value || id;
      const bcData = document.getElementById('in-bc').value || id;

      document.getElementById('ui-name').innerText = name;
      document.getElementById('ui-role').innerText = role;
      document.getElementById('ui-id-code').innerText = '#' + id;
      document.getElementById('ui-phone').innerText = phone;
      document.getElementById('ui-email').innerText = email;
      document.getElementById('ui-footer-id').innerText = 'ID: ' + id;

      // Photo
      const photoBox = document.getElementById('ui-photo-box');
      if (photo) {
        photoBox.innerHTML = `<img src="${photo}" alt="Photo">`;
      } else {
        photoBox.innerHTML = `<span>${name.trim().charAt(0).toUpperCase() || 'U'}</span>`;
      }

      // QR Code
      try {
        const qr = qrcode(0, 'M');
        qr.addData('ILAS|' + role + '|' + id + '|' + name);
        qr.make();
        document.getElementById('ui-qr').innerHTML = qr.createSvgTag({ scalable: true });
      } catch(e) { console.warn(e); }

      // Barcode CODE128
      try {
        JsBarcode('#ui-barcode', bcData, {
          format: 'CODE128',
          displayValue: false,
          margin: 0,
          lineColor: '#0B3D6E',
          background: '#ffffff',
          height: 20
        });
      } catch(e) { console.warn(e); }
    }

    function setMode(mode) {
      const p = document.getElementById('editPanel');
      const btnP = document.getElementById('btn-prev');
      const btnE = document.getElementById('btn-edit');
      if (mode === 'edit') {
        p.style.display = 'block';
        btnE.classList.add('active');
        btnP.classList.remove('active');
      } else {
        p.style.display = 'none';
        btnP.classList.add('active');
        btnE.classList.remove('active');
      }
    }

    async function downloadPNG() {
      const el = document.getElementById('badgeCard');
      const canvas = await html2canvas(el, { scale: 3, useCORS: true });
      const a = document.createElement('a');
      a.download = 'ilas-id-badge.png';
      a.href = canvas.toDataURL('image/png');
      a.click();
    }

    async function downloadPDF() {
      const el = document.getElementById('badgeCard');
      const canvas = await html2canvas(el, { scale: 3, useCORS: true });
      const img = canvas.toDataURL('image/png');
      const { jsPDF } = window.jspdf;
      const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: [85.6, 54] });
      pdf.addImage(img, 'PNG', 0, 0, 85.6, 54);
      pdf.save('ilas-id-badge.pdf');
    }

    // Initial render
    update();
  </script>
</body>
</html>"""

with open(r'c:\Users\Meriem\Downloads\workspace-019fe29e-8f2a-76f2-84d0-8810f12b929a\institut\id_badge\badge_id_preview.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

with open(r'c:\Users\Meriem\Downloads\workspace-019fe29e-8f2a-76f2-84d0-8810f12b929a\institut\badge_id_preview.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Generated new standalone badge_id_preview.html successfully.")
