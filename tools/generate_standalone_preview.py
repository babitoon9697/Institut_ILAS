# -*- coding: utf-8 -*-
import base64
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "static", "uploads", "logo-ilas.png")

with open(LOGO_PATH, "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800;900&family=Space+Grotesk:wght@700;800&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin:0; padding:0; -webkit-print-color-adjust: exact !important; }}
  body {{ background: #0f172a; display:flex; justify-content:center; padding: 25px 0; font-family: 'Plus Jakarta Sans', Arial, sans-serif; }}
  .ticket {{
    width: 72mm;
    background: #ffffff;
    color: #000000;
    padding: 5mm 3.5mm;
    border-radius: 4px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  }}
  .header {{ text-align: center; }}
  .logo {{ max-width: 46mm; height: auto; display: block; margin: 0 auto 3px auto; filter: contrast(160%); }}
  .brand {{ font-family: 'Space Grotesk', sans-serif; font-size: 13px; font-weight: 900; letter-spacing: 0.6px; }}
  .sub {{ font-size: 8px; font-weight: 700; margin-top: 1px; }}
  .contact {{ font-size: 8px; font-weight: 600; margin-top: 2px; }}
  
  .badge-title {{
    background: #000000;
    color: #ffffff;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.8px;
    text-align: center;
    padding: 4px 0;
    margin: 7px 0 5px 0;
    border-radius: 3px;
  }}
  
  .meta-box {{
    border: 1.2px solid #000000;
    border-radius: 4px;
    padding: 4px 6px;
    margin-bottom: 7px;
    font-size: 9px;
  }}
  .meta-row {{ display: flex; justify-content: space-between; padding: 1.5px 0; }}
  .meta-row:not(:last-child) {{ border-bottom: 0.8px dashed #000000; }}
  .meta-lbl {{ font-size: 8px; font-weight: 700; }}
  .meta-val {{ font-weight: 900; }}

  .day-banner {{
    background: #000000;
    color: #ffffff;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 3px 6px;
    margin-top: 8px;
    margin-bottom: 5px;
    border-radius: 2px;
  }}
  .day-title {{ font-size: 10px; font-weight: 900; letter-spacing: 0.5px; }}
  .day-cnt {{ font-size: 8px; font-weight: 900; background: #ffffff; color: #000000; padding: 0 4px; border-radius: 2px; }}

  .slot {{
    border-left: 3.5px solid #000000;
    padding: 3px 0 4px 6px;
    margin-bottom: 5px;
    border-bottom: 0.8px dashed #000000;
  }}
  .slot:last-child {{ border-bottom: none; }}
  .slot-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }}
  .time {{ font-size: 10px; font-weight: 900; }}
  .room {{ font-size: 8.5px; font-weight: 900; border: 1.2px solid #000000; padding: 0 4px; border-radius: 2px; }}
  .course {{ font-size: 11px; font-weight: 800; line-height: 1.25; margin-bottom: 1.5px; }}
  .meta {{ display: flex; justify-content: space-between; font-size: 8.5px; font-weight: 700; }}

  .footer {{
    text-align: center;
    margin-top: 10px;
    padding-top: 6px;
    border-top: 1.5px dashed #000000;
    font-size: 8px;
    font-weight: 700;
    line-height: 1.35;
  }}
</style>
</head>
<body>
  <div class="ticket">
    <div class="header">
      <img src="data:image/png;base64,{b64}" class="logo">
      <div class="brand">INSTITUT LES SAGES</div>
      <div class="sub">EXCELLENCE PÉDAGOGIQUE & LANGUES</div>
      <div class="contact">📞 06 60 29 11 55 · Lot Nora N°10, Deroua</div>
    </div>

    <div class="badge-title">🗓️ EMPLOI DU TEMPS OFFICIEL</div>

    <div class="meta-box">
      <div class="meta-row">
        <span class="meta-lbl">ANNÉE SCOLAIRE</span>
        <span class="meta-val">2025 / 2026</span>
      </div>
      <div class="meta-row">
        <span class="meta-lbl">DATE D'ÉMISSION</span>
        <span class="meta-val">10/10/2026 à 16:00</span>
      </div>
      <div class="meta-row">
        <span class="meta-lbl">TOTAL DES COURS</span>
        <span class="meta-val">4 Séances Hebdo</span>
      </div>
    </div>

    <div class="day-banner">
      <span class="day-title">📅 LUNDI</span>
      <span class="day-cnt">2 COURS</span>
    </div>
    <div class="slot">
      <div class="slot-top">
        <span class="time">⏰ 17:30 – 19:00</span>
        <span class="room">SALLE 2</span>
      </div>
      <div class="course">Soutien 3AC — Mathématiques</div>
      <div class="meta">
        <span>👨‍🏫 M. BENALI</span>
        <span>GROUPE A</span>
      </div>
    </div>
    <div class="slot">
      <div class="slot-top">
        <span class="time">⏰ 19:00 – 20:30</span>
        <span class="room">SALLE 5</span>
      </div>
      <div class="course">Anglais Communication — Ados</div>
      <div class="meta">
        <span>👩‍🏫 Mme MARYA ANG</span>
        <span>GROUPE 1</span>
      </div>
    </div>

    <div class="day-banner">
      <span class="day-title">📅 MARDI</span>
      <span class="day-cnt">1 COURS</span>
    </div>
    <div class="slot">
      <div class="slot-top">
        <span class="time">⏰ 18:00 – 19:30</span>
        <span class="room">SALLE 1</span>
      </div>
      <div class="course">Soutien 2BAC — Physique Chimie</div>
      <div class="meta">
        <span>👨‍🏫 M. NACHAT</span>
        <span>PC BIOF</span>
      </div>
    </div>

    <div class="day-banner">
      <span class="day-title">📅 SAMEDI</span>
      <span class="day-cnt">1 COURS</span>
    </div>
    <div class="slot">
      <div class="slot-top">
        <span class="time">⏰ 10:00 – 12:00</span>
        <span class="room">SALLE 8</span>
      </div>
      <div class="course">Allemand Débutant — Niveau A1</div>
      <div class="meta">
        <span>👨‍🏫 M. SAKAM</span>
        <span>GROUPE 1</span>
      </div>
    </div>

    <div class="footer">
      <div style="font-weight:900; font-size:9px;">INSTITUT PRIVÉ LES SAGES</div>
      <div>⚠️ Prière de respecter les horaires & d'arriver 5 min avant.</div>
      <div style="margin-top:2px; font-size:7.5px;">Autorisation Ministérielle N° 22-200/2020</div>
    </div>
  </div>
</body>
</html>
"""

out_html = os.path.join(BASE_DIR, "preview_output", "standalone_recommended.html")
with open(out_html, "w", encoding="utf-8") as f:
    f.write(html)

print("Generated standalone HTML:", out_html)
