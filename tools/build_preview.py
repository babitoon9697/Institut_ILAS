import os

bg_file_path = r'c:\Users\Meriem\Downloads\workspace-019fe29e-8f2a-76f2-84d0-8810f12b929a\institut\id_badge\assets\bg_b64.txt'
with open(bg_file_path, 'r') as f:
    bg_b64 = f.read().strip()

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ID Badge Generator — Live Interactive Preview</title>
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&family=Roboto:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <!-- JS Libraries for Standalone Browser Preview -->
  <script src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.6/dist/JsBarcode.all.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Roboto', sans-serif;
      background: #f4f7fc;
      color: #1B3D8F;
      padding: 30px 20px;
    }}
    .container {{
      max-width: 1060px;
      margin: 0 auto;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 2px solid #e2e8f0;
    }}
    .title {{
      font-family: 'Montserrat', sans-serif;
      font-size: 24px;
      font-weight: 700;
      color: #1B3D8F;
    }}
    .subtitle {{
      font-size: 13px;
      color: #64748b;
      margin-top: 4px;
    }}
    .toggle-bar {{
      display: flex;
      background: #e2e8f0;
      border-radius: 8px;
      padding: 4px;
      gap: 4px;
    }}
    .toggle-btn {{
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      font-family: 'Montserrat', sans-serif;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      background: transparent;
      color: #1B3D8F;
      transition: all 0.2s;
    }}
    .toggle-btn.active {{
      background: #1B3D8F;
      color: #ffffff;
      box-shadow: 0 2px 6px rgba(27, 61, 143, 0.3);
    }}
    
    .layout {{
      display: flex;
      gap: 32px;
      align-items: flex-start;
      flex-wrap: wrap;
    }}
    .card-wrap {{
      flex: 1 1 460px;
      max-width: 540px;
    }}

    /* CR80 CARD SPECIFICATIONS */
    .card {{
      position: relative;
      width: 100%;
      aspect-ratio: 1.585 / 1; /* 85.6mm x 54mm */
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 12px 32px rgba(27, 61, 143, 0.22);
      background: #ffffff;
      container-type: inline-size;
      user-select: none;
    }}
    .card-bg {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      z-index: 1;
      pointer-events: none;
    }}

    /* EXACT POSITIONING (% OF CARD) */
    .badge-photo {{
      position: absolute;
      left: 5.8%;
      top: 14.8%;
      width: 25.7%;
      height: 48.1%;
      border-radius: 8px;
      border: 2px solid #ffffff;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      overflow: hidden;
      z-index: 2;
      background: linear-gradient(135deg, #1B3D8F, #0d2359);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-family: 'Montserrat', sans-serif;
      font-weight: 700;
      font-size: clamp(16px, 6cqw, 32px);
    }}
    .badge-photo img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}

    .badge-name {{
      position: absolute;
      left: 39.7%;
      top: 48.1%;
      width: 52.5%;
      height: 9.2%;
      z-index: 2;
      display: flex;
      align-items: center;
      font-family: 'Montserrat', sans-serif;
      font-weight: 700;
      color: #1B3D8F;
      letter-spacing: 1px;
      font-size: clamp(12px, 2.174cqw, 24px);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      text-transform: uppercase;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
    }}

    .badge-role {{
      position: absolute;
      left: 44.4%;
      top: 57.4%;
      width: 44.4%;
      height: 7.4%;
      z-index: 2;
      background: #E30613;
      color: #ffffff;
      font-family: 'Montserrat', sans-serif;
      font-weight: 600;
      font-size: clamp(9px, 1.186cqw, 14px);
      border-radius: 20px;
      padding: 0 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      text-transform: uppercase;
      box-shadow: 0 2px 4px rgba(227, 6, 19, 0.25);
    }}

    .badge-id-main {{
      position: absolute;
      left: 42%;
      top: 66.6%;
      width: 35%;
      height: 6.5%;
      z-index: 2;
      display: flex;
      align-items: center;
      font-family: 'Roboto', sans-serif;
      font-weight: 600;
      color: #1B3D8F;
      font-size: clamp(11px, 1.581cqw, 18px);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .badge-qr {{
      position: absolute;
      left: 5.8%;
      top: 66.6%;
      width: 16.3%;
      height: 25.9%;
      z-index: 2;
      background: #ffffff;
      padding: 4px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 1px 4px rgba(0,0,0,0.12);
      overflow: hidden;
    }}
    .badge-qr svg {{
      width: 100% !important;
      height: 100% !important;
    }}

    .badge-flags {{
      position: absolute;
      left: 37.4%;
      top: 74%;
      width: 21%;
      height: 7.4%;
      z-index: 2;
      display: flex;
      align-items: center;
      gap: 4px;
    }}
    .flag-circle {{
      width: 24px;
      height: 24px;
      max-width: 100%;
      max-height: 100%;
      border-radius: 50%;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
      flex-shrink: 0;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #ffffff;
    }}
    .flag-circle svg {{
      width: 100%;
      height: 100%;
    }}

    .badge-phone {{
      position: absolute;
      left: 64.2%;
      top: 74%;
      width: 32.7%;
      height: 6.5%;
      z-index: 2;
      display: flex;
      align-items: center;
      gap: 6px;
      font-family: 'Roboto', sans-serif;
      font-weight: 500;
      color: #1B3D8F;
      font-size: clamp(9px, 1.087cqw, 13px);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .badge-email {{
      position: absolute;
      left: 64.2%;
      top: 81.5%;
      width: 32.7%;
      height: 6.5%;
      z-index: 2;
      display: flex;
      align-items: center;
      gap: 6px;
      font-family: 'Roboto', sans-serif;
      font-weight: 500;
      color: #1B3D8F;
      font-size: clamp(9px, 1.087cqw, 13px);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .badge-footer-id {{
      position: absolute;
      left: 4.7%;
      top: 88.9%;
      width: 23.4%;
      height: 5.6%;
      z-index: 2;
      display: flex;
      align-items: center;
      font-family: 'Roboto', sans-serif;
      font-weight: 600;
      color: #1B3D8F;
      font-size: clamp(8px, 0.988cqw, 11px);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .badge-footer-phone {{
      position: absolute;
      left: 32.7%;
      top: 88.9%;
      width: 29.2%;
      height: 5.6%;
      z-index: 2;
      display: flex;
      align-items: center;
      font-family: 'Roboto', sans-serif;
      font-weight: 600;
      color: #1B3D8F;
      font-size: clamp(8px, 0.988cqw, 11px);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .badge-barcode {{
      position: absolute;
      left: 67.8%;
      top: 87%;
      width: 29.2%;
      height: 9.2%;
      z-index: 2;
      background: #ffffff;
      border-radius: 4px;
      padding: 2px 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }}
    .badge-barcode svg {{
      width: 100%;
      height: 100%;
    }}

    .actions-row {{
      display: flex;
      gap: 12px;
      margin-top: 16px;
    }}
    .act-btn {{
      padding: 10px 18px;
      border-radius: 8px;
      border: none;
      font-family: 'Montserrat', sans-serif;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      background: #1B3D8F;
      color: #ffffff;
      box-shadow: 0 2px 6px rgba(27, 61, 143, 0.2);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }}
    .act-btn:hover {{
      background: #153275;
      transform: translateY(-1px);
    }}
    .act-btn.sec {{
      background: #ffffff;
      color: #1B3D8F;
      border: 1.5px solid #1B3D8F;
    }}

    .edit-panel {{
      flex: 1 1 360px;
      background: #ffffff;
      padding: 24px;
      border-radius: 16px;
      border: 1px solid #cbd5e1;
      box-shadow: 0 10px 25px rgba(27, 61, 143, 0.08);
    }}
    .edit-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 14px;
    }}
    .field {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .field label {{
      font-size: 12px;
      font-weight: 600;
      color: #1B3D8F;
    }}
    .field input {{
      padding: 9px 12px;
      border-radius: 8px;
      border: 1.5px solid #cbd5e1;
      font-size: 13px;
      outline: none;
    }}
    .field input:focus {{
      border-color: #1B3D8F;
    }}

    @media print {{
      .header, .toggle-bar, .actions-row, .edit-panel {{
        display: none !important;
      }}
      body {{
        background: none !important;
        padding: 0 !important;
      }}
      .card {{
        width: 85.6mm !important;
        height: 54mm !important;
        box-shadow: none !important;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <div class="title">🪪 ID Badge Generator</div>
        <div class="subtitle">Student & Instructor Badge Template • CR80 (85.6mm × 54mm) • Exact % Positioning</div>
      </div>
      <div class="toggle-bar">
        <button id="btn-prev" class="toggle-btn active" onclick="setMode('preview')">👁️ Preview Mode</button>
        <button id="btn-edit" class="toggle-btn" onclick="setMode('edit')">✏️ Edit Mode</button>
      </div>
    </div>

    <div class="layout">
      <!-- CR80 CARD -->
      <div class="card-wrap">
        <div id="badgeCard" class="card">
          <img class="card-bg" src="data:image/png;base64,{bg_b64}" alt="Background Template">

          <div class="badge-photo" id="ui-photo-box">
            <span id="ui-photo-initial">S</span>
          </div>
          <div class="badge-name" id="ui-name">SARA ALAOUI</div>
          <div class="badge-role" id="ui-role">LANGUAGE INSTRUCTOR</div>
          <div class="badge-id-main" id="ui-id-main">1234567890</div>

          <div class="badge-qr" id="ui-qr"></div>

          <div class="badge-flags">
            <div class="flag-circle"><svg viewBox="0 0 60 60"><clipPath id="u1"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#u1)"><rect width="60" height="60" fill="#00247D"/><path d="M0,0 L60,60 M60,0 L0,60" stroke="#FFF" stroke-width="10"/><path d="M0,0 L60,60 M60,0 L0,60" stroke="#CF142B" stroke-width="6"/><path d="M30,0 V60 M0,30 H60" stroke="#FFF" stroke-width="14"/><path d="M30,0 V60 M0,30 H60" stroke="#CF142B" stroke-width="8"/></g></svg></div>
            <div class="flag-circle"><svg viewBox="0 0 60 60"><clipPath id="b1"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#b1)"><rect x="0" y="0" width="20" height="60" fill="#000"/><rect x="20" y="0" width="20" height="60" fill="#FDDA24"/><rect x="40" y="0" width="20" height="60" fill="#EF3340"/></g></svg></div>
            <div class="flag-circle"><svg viewBox="0 0 60 60"><clipPath id="f1"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#f1)"><rect x="0" y="0" width="20" height="60" fill="#002654"/><rect x="20" y="0" width="20" height="60" fill="#FFF"/><rect x="40" y="0" width="20" height="60" fill="#CE1126"/></g></svg></div>
            <div class="flag-circle"><svg viewBox="0 0 60 60"><clipPath id="e1"><circle cx="30" cy="30" r="30"/></clipPath><g clip-path="url(#e1)"><rect x="0" y="0" width="60" height="15" fill="#AA1529"/><rect x="0" y="15" width="60" height="30" fill="#F1BF00"/><rect x="0" y="45" width="60" height="15" fill="#AA1529"/></g></svg></div>
          </div>

          <div class="badge-phone">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1B3D8F" stroke-width="2.5"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            <span id="ui-phone">+33 6 12 34 56 78</span>
          </div>

          <div class="badge-email">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1B3D8F" stroke-width="2.5"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
            <span id="ui-email">info@ilas-ecole.com</span>
          </div>

          <div class="badge-footer-id" id="ui-footer-id">1234567890</div>
          <div class="badge-footer-phone" id="ui-footer-phone">+33 6 12 34 56 78</div>

          <div class="badge-barcode">
            <svg id="ui-barcode"></svg>
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
        <h3 style="color: #1B3D8F; margin-bottom: 16px; font-size: 16px;">Edit Dynamic Fields</h3>
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
    function update() {{
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
      document.getElementById('ui-id-main').innerText = id;
      document.getElementById('ui-phone').innerText = phone;
      document.getElementById('ui-email').innerText = email;
      document.getElementById('ui-footer-id').innerText = id;
      document.getElementById('ui-footer-phone').innerText = phone;

      // Photo
      const photoBox = document.getElementById('ui-photo-box');
      if (photo) {{
        photoBox.innerHTML = `<img src="${{photo}}" alt="Photo">`;
      }} else {{
        photoBox.innerHTML = `<span>${{name.trim().charAt(0).toUpperCase() || 'U'}}</span>`;
      }}

      // QR Code
      try {{
        const typeNumber = 0;
        const errorCorrectionLevel = 'M';
        const qr = qrcode(typeNumber, errorCorrectionLevel);
        qr.addData(qrData);
        qr.make();
        document.getElementById('ui-qr').innerHTML = qr.createSvgTag({{ scalable: true }});
      }} catch(e) {{
        console.warn(e);
      }}

      // Barcode CODE128
      try {{
        JsBarcode('#ui-barcode', bcData, {{
          format: 'CODE128',
          displayValue: false,
          margin: 0,
          lineColor: '#1B3D8F',
          background: '#ffffff',
          height: 40
        }});
      }} catch(e) {{
        console.warn(e);
      }}
    }}

    function setMode(mode) {{
      const p = document.getElementById('editPanel');
      const btnP = document.getElementById('btn-prev');
      const btnE = document.getElementById('btn-edit');
      if (mode === 'edit') {{
        p.style.display = 'block';
        btnE.classList.add('active');
        btnP.classList.remove('active');
      }} else {{
        p.style.display = 'none';
        btnP.classList.add('active');
        btnE.classList.remove('active');
      }}
    }}

    async function downloadPNG() {{
      const el = document.getElementById('badgeCard');
      const canvas = await html2canvas(el, {{ scale: 3, useCORS: true }});
      const a = document.createElement('a');
      a.download = 'id-badge.png';
      a.href = canvas.toDataURL('image/png');
      a.click();
    }}

    async function downloadPDF() {{
      const el = document.getElementById('badgeCard');
      const canvas = await html2canvas(el, {{ scale: 3, useCORS: true }});
      const img = canvas.toDataURL('image/png');
      const {{ jsPDF }} = window.jspdf;
      const pdf = new jsPDF({{ orientation: 'landscape', unit: 'mm', format: [85.6, 54] }});
      pdf.addImage(img, 'PNG', 0, 0, 85.6, 54);
      pdf.save('id-badge.pdf');
    }}

    // Initial render
    update();
  </script>
</body>
</html>"""

with open(r'c:\Users\Meriem\Downloads\workspace-019fe29e-8f2a-76f2-84d0-8810f12b929a\institut\id_badge\badge_id_preview.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

with open(r'c:\Users\Meriem\Downloads\workspace-019fe29e-8f2a-76f2-84d0-8810f12b929a\institut\badge_id_preview.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Generated preview HTML files successfully.")
