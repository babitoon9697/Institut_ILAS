import os

html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Badge ILAS — Live Interactive Preview</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Roboto:wght@500;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.6/dist/JsBarcode.all.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

<style>
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
  background: #f4f7fc;
  color: #0B3D6E;
  padding: 30px 20px;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
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
   EXACT MATCH TO PREVIEW MOCKUP — FULL PRINT COLOR ADJUSTED
   ============================================================ */
.badge-card {
  width: 100%;
  aspect-ratio: 1.585 / 1;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 14px 36px rgba(11, 61, 110, 0.28), 0 0 0 1px rgba(11, 61, 110, 0.15);
  background: #ffffff !important;
  display: flex;
  flex-direction: column;
  user-select: none;
  container-type: inline-size;
  color: #0B3D6E;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

.card-header-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 40.7%;
  background: linear-gradient(135deg, #06101E 0%, #0B3D6E 60%, #155DA8 100%) !important;
  z-index: 1;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

.accent-wave {
  position: absolute;
  top: 36.1%;
  left: -2%;
  width: 104%;
  height: 8.3%;
  background: linear-gradient(90deg, #C8102E 0%, #E02038 60%, #F0A02E 100%) !important;
  transform: rotate(-2deg);
  z-index: 2;
  box-shadow: 0 2px 6px rgba(0,0,0,0.25);
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

.card-header {
  height: 36.1%;
  padding: 1.8cqw 3.5cqw 0 3.5cqw;
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
  gap: 1.8cqw;
}
.brand-logo-text {
  display: flex;
  flex-direction: column;
}
.brand-name {
  font-family: 'Montserrat', sans-serif;
  font-size: 3.4cqw;
  font-weight: 900;
  color: #ffffff !important;
  letter-spacing: 1px;
  line-height: 1;
}
.brand-name span {
  color: #FFD47A !important;
}
.brand-sub {
  font-size: 1.6cqw;
  color: rgba(255, 255, 255, 0.85) !important;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  font-weight: 700;
  margin-top: 0.3cqw;
}
.year-pill {
  background: rgba(255, 255, 255, 0.18) !important;
  border: 0.5px solid rgba(255, 255, 255, 0.35) !important;
  border-radius: 12px;
  padding: 0.5cqw 2.2cqw;
  font-size: 2cqw;
  font-weight: 800;
  color: #FFD47A !important;
  letter-spacing: 0.8px;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

.card-body {
  flex: 1;
  display: flex;
  padding: 2.2cqw 3.5cqw 1cqw 3.5cqw;
  gap: 3cqw;
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
  width: 15cqw;
  height: 19.5cqw;
  border-radius: 2cqw;
  overflow: hidden;
  border: 0.6cqw solid #C8102E !important;
  box-shadow: 0 4px 12px rgba(11, 61, 110, 0.35);
  background: linear-gradient(145deg, #0B3D6E, #071322) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFD47A !important;
  font-family: 'Montserrat', sans-serif;
  font-weight: 900;
  font-size: 6cqw;
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
  gap: 0.8cqw;
  min-width: 0;
}

.person-name {
  font-family: 'Montserrat', sans-serif;
  font-size: 4.4cqw;
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
  gap: 1.8cqw;
  margin-top: 0.2cqw;
}
.role-badge {
  background: linear-gradient(90deg, #C8102E 0%, #E02038 100%) !important;
  color: #ffffff !important;
  font-family: 'Montserrat', sans-serif;
  font-size: 2.4cqw;
  font-weight: 800;
  letter-spacing: 0.6px;
  padding: 0.6cqw 2.4cqw;
  border-radius: 20px;
  text-transform: uppercase;
  box-shadow: 0 2px 5px rgba(200, 16, 46, 0.35);
  white-space: nowrap;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.id-code-text {
  font-family: 'Roboto', sans-serif;
  font-size: 2.7cqw;
  font-weight: 800;
  color: #F0A02E !important;
  letter-spacing: 0.5px;
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
  font-size: 2.4cqw;
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
  gap: 1.2cqw;
  margin-top: 0.4cqw;
}
.flag-sphere {
  width: 4.3cqw;
  height: 4.3cqw;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.25);
  background: #ffffff !important;
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
  height: 19.4%;
  padding: 0 3.5cqw;
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
  gap: 1.8cqw;
}
.qr-box {
  width: 7.2cqw;
  height: 7.2cqw;
  background: #ffffff !important;
  border-radius: 1cqw;
  border: 1px solid #cbd5e1;
  padding: 0.4cqw;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
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
  font-size: 2.4cqw;
  font-weight: 800;
  color: #0B3D6E !important;
  letter-spacing: 0.5px;
}
.footer-sub {
  font-size: 1.7cqw;
  color: #64748b !important;
  font-weight: 700;
}

.barcode-box {
  background: #ffffff !important;
  border-radius: 1cqw;
  border: 1px solid #cbd5e1;
  padding: 0.4cqw 1.2cqw;
  height: 6.2cqw;
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
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
  font-weight: 800;
  font-size: 13px;
  cursor: pointer;
  background: #C8102E !important;
  color: #ffffff !important;
  box-shadow: 0 3px 10px rgba(200, 16, 46, 0.35);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.act-btn:hover {
  background: #a80b23 !important;
  transform: translateY(-1px);
}
.act-btn.sec {
  background: #ffffff !important;
  color: #0B3D6E !important;
  border: 1.5px solid #0B3D6E !important;
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
  font-weight: 700;
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
  *, *::before, *::after {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
  }
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
        <div class="title">🪪 Ultimate Print-Color-Adjusted ILAS Badge</div>
        <div class="subtitle">Forces 100% Background Graphics & Colors in All Printers • CR80 Format</div>
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
          <div class="card-header-bg"></div>
          <div class="accent-wave"></div>

          <!-- Header -->
          <div class="card-header">
            <div class="brand-box">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="#FFD47A"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
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
                <span id="ui-photo-initial">I</span>
              </div>
            </div>

            <!-- Right: Details -->
            <div class="right-col">
              <div class="person-name" id="ui-name">ILIASS NAKKACH</div>

              <div class="role-tag-row">
                <div class="role-badge" id="ui-role">STUDENT</div>
                <div class="id-code-text" id="ui-id-code">ID: #ETU001</div>
              </div>

              <div class="contact-group">
                <div class="contact-item">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#C8102E" stroke-width="2.5"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  <span id="ui-phone">0638683230</span>
                </div>
                <div class="contact-item">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#C8102E" stroke-width="2.5"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                  <span id="ui-email">contact@mrmakkach.pro</span>
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
                <div class="footer-id" id="ui-footer-id">ID: ETU001</div>
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
          <div class="field"><label>Full Name</label><input id="in-name" value="ILIASS NAKKACH" oninput="update()"></div>
          <div class="field"><label>Role / Badge Label</label><input id="in-role" value="STUDENT" oninput="update()"></div>
          <div class="field"><label>ID Number</label><input id="in-id" value="ETU001" oninput="update()"></div>
          <div class="field"><label>Phone</label><input id="in-phone" value="0638683230" oninput="update()"></div>
          <div class="field"><label>Email</label><input id="in-email" value="contact@mrmakkach.pro" oninput="update()"></div>
          <div class="field"><label>Photo URL</label><input id="in-photo" placeholder="https://..." oninput="update()"></div>
          <div class="field"><label>QR Code Data</label><input id="in-qr" value="ETU001" oninput="update()"></div>
          <div class="field"><label>Barcode Data (CODE128)</label><input id="in-bc" value="ETU001" oninput="update()"></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    function update() {
      const name = document.getElementById('in-name').value || 'NAME SURNAME';
      const role = document.getElementById('in-role').value || 'ROLE';
      const id = document.getElementById('in-id').value || 'ETU001';
      const phone = document.getElementById('in-phone').value || '0638683230';
      const email = document.getElementById('in-email').value || 'contact@mrmakkach.pro';
      const photo = document.getElementById('in-photo').value;
      const qrData = document.getElementById('in-qr').value || id;
      const bcData = document.getElementById('in-bc').value || id;

      document.getElementById('ui-name').innerText = name;
      document.getElementById('ui-role').innerText = role;
      document.getElementById('ui-id-code').innerText = 'ID: #' + id;
      document.getElementById('ui-phone').innerText = phone;
      document.getElementById('ui-email').innerText = email;
      document.getElementById('ui-footer-id').innerText = 'ID: ' + id;

      // Photo
      const photoBox = document.getElementById('ui-photo-box');
      if (photo) {
        photoBox.innerHTML = `<img src="${photo}" alt="Photo">`;
      } else {
        photoBox.innerHTML = `<span>${name.trim().charAt(0).toUpperCase() || 'I'}</span>`;
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
          height: 18
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

print("Generated new v5 print-color-adjusted badge_id_preview.html successfully.")
