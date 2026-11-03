# -*- coding: utf-8 -*-
"""
Script to generate an interactive HTML preview and high-resolution comparison
for 80mm Thermal Timetable (Emploi du Temps).
"""
import base64
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "static", "uploads", "logo-ilas.png")

with open(LOGO_PATH, "rb") as f:
    LOGO_B64 = base64.b64encode(f.read()).decode("utf-8")

preview_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aperçu & Comparaison : Emploi du Temps Ticket Thermique 80mm</title>
<!-- Google Fonts optimisées pour l'impression thermique -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800;900&family=Inter:wght@500;600;700;800;900&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
<style>
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  body {{
    background: #0f172a;
    color: #e2e8f0;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 30px 20px;
    min-height: 100vh;
  }}

  .dashboard-header {{
    max-width: 1280px;
    margin: 0 auto 30px auto;
    background: #1e293b;
    padding: 24px 30px;
    border-radius: 16px;
    border: 1px solid #334155;
    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
  }}

  .badge-tag {{
    display: inline-block;
    background: #3b82f6;
    color: #fff;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 4px 10px;
    border-radius: 20px;
    margin-bottom: 8px;
  }}

  h1 {{
    font-size: 24px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 8px;
  }}

  p.subtitle {{
    color: #94a3b8;
    font-size: 14px;
    line-height: 1.5;
  }}

  .grid-preview {{
    max-width: 1280px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 1.25fr 1.25fr;
    gap: 28px;
    align-items: start;
  }}

  @media (max-width: 1100px) {{
    .grid-preview {{
      grid-template-columns: 1fr;
    }}
  }}

  .card-col {{
    background: #1e293b;
    border-radius: 16px;
    border: 1px solid #334155;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
  }}

  .card-col-header {{
    padding: 18px 20px;
    border-bottom: 1px solid #334155;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .card-col-header h2 {{
    font-size: 15px;
    font-weight: 800;
    color: #f8fafc;
  }}

  .pill-status {{
    font-size: 11px;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 12px;
  }}
  .pill-bad {{
    background: #ef444422;
    color: #f87171;
    border: 1px solid #ef444455;
  }}
  .pill-good {{
    background: #10b98122;
    color: #34d399;
    border: 1px solid #10b98155;
  }}

  .card-col-notes {{
    padding: 12px 20px;
    font-size: 12px;
    color: #94a3b8;
    background: #0f172a88;
    border-bottom: 1px solid #334155;
    line-height: 1.4;
  }}

  .ticket-viewport {{
    background: #334155;
    padding: 30px 15px;
    display: flex;
    justify-content: center;
    align-items: flex-start;
  }}

  /* ========================================================
     STYLE DU TICKET ACTUEL (ANCIEN / BAD LOOK)
     ======================================================== */
  .ticket-old {{
    width: 72mm;
    background: #ffffff;
    color: #000000;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    padding: 4mm 3mm;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }}
  .ticket-old .header {{
    text-align: center;
    border-bottom: 1.5px dashed #000;
    padding-bottom: 6px;
    margin-bottom: 8px;
  }}
  .ticket-old .title {{
    font-size: 13px;
    font-weight: bold;
    text-transform: uppercase;
  }}
  .ticket-old .day {{
    font-weight: bold;
    background: #eee;
    padding: 2px 4px;
    margin-top: 8px;
    border-left: 3px solid #000;
  }}
  .ticket-old .slot {{
    padding: 4px 0;
    border-bottom: 1px dotted #888;
  }}

  /* ========================================================
     NOUVEAU DESIGN 1 : MODERN EXECUTIVE TICKET (80MM THERMIQUE)
     Optimisé contraste noir 100%, typographie dense ultra-nette,
     séparateurs géométriques, badges horaires inversés.
     ======================================================== */
  .ticket-modern-1 {{
    width: 72mm;
    background: #ffffff;
    color: #000000;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    font-size: 10px;
    line-height: 1.3;
    padding: 4mm 3mm;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }}

  /* Header Thermique Haute Précision */
  .t-header {{
    text-align: center;
    padding-bottom: 6px;
  }}
  .t-logo-img {{
    max-width: 50mm;
    height: auto;
    max-height: 14mm;
    display: block;
    margin: 0 auto 4px auto;
    filter: grayscale(100%) contrast(150%);
  }}
  .t-brand-name {{
    font-family: 'Space Grotesk', 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: #000;
    line-height: 1.15;
  }}
  .t-brand-sub {{
    font-size: 8px;
    font-weight: 700;
    color: #000;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-top: 2px;
  }}
  .t-brand-contact {{
    font-size: 8px;
    font-weight: 600;
    color: #000;
    margin-top: 2px;
  }}

  /* Bloc Titre Inversé (Très net sur imprimante thermique) */
  .t-title-badge {{
    background: #000000;
    color: #ffffff;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    text-align: center;
    padding: 3.5px 0;
    margin: 6px 0;
    border-radius: 3px;
  }}

  /* Meta table (Élève / Prof / Filtre / Date) */
  .t-meta-box {{
    border: 1px solid #000000;
    border-radius: 4px;
    padding: 4px 6px;
    margin-bottom: 8px;
    font-size: 9px;
  }}
  .t-meta-row {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 1.5px 0;
  }}
  .t-meta-row:not(:last-child) {{
    border-bottom: 0.5px dashed #000000;
  }}
  .t-meta-label {{
    font-weight: 700;
    text-transform: uppercase;
    font-size: 8px;
    color: #000;
  }}
  .t-meta-val {{
    font-weight: 900;
    color: #000;
    text-align: right;
  }}

  /* Séparateurs nets sans nuance grise */
  .t-sep-double {{
    border-top: 2px solid #000000;
    margin: 6px 0;
  }}
  .t-sep-dashed {{
    border-top: 1.5px dashed #000000;
    margin: 6px 0;
  }}
  .t-sep-dots {{
    border-top: 1px dotted #000000;
    margin: 4px 0;
  }}

  /* En-tête de Jour (Section Bannière Noire Stylée) */
  .t-day-banner {{
    background: #000000;
    color: #ffffff;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2.5px 6px;
    margin-top: 8px;
    margin-bottom: 5px;
    border-radius: 2px;
  }}
  .t-day-name {{
    font-size: 10px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .t-day-count {{
    font-size: 8px;
    font-weight: 800;
    background: #ffffff;
    color: #000000;
    padding: 0 4px;
    border-radius: 2px;
  }}

  /* Carte Séance Moderne 80mm */
  .t-slot-card {{
    border-left: 3px solid #000000;
    padding: 3px 0 3px 6px;
    margin-bottom: 5px;
    position: relative;
  }}
  .t-slot-card:not(:last-child) {{
    border-bottom: 0.5px dashed #000000;
    padding-bottom: 5px;
  }}

  .t-slot-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2px;
  }}
  .t-time-pill {{
    font-size: 9.5px;
    font-weight: 900;
    color: #000000;
    letter-spacing: 0.2px;
  }}
  .t-room-pill {{
    font-size: 8.5px;
    font-weight: 900;
    border: 1px solid #000000;
    padding: 0 4px;
    border-radius: 2px;
    text-transform: uppercase;
  }}
  .t-course-title {{
    font-size: 10.5px;
    font-weight: 800;
    color: #000000;
    line-height: 1.25;
    margin-bottom: 1.5px;
  }}
  .t-slot-bottom {{
    display: flex;
    justify-content: space-between;
    font-size: 8.5px;
    font-weight: 700;
    color: #000000;
  }}

  /* Footer & QR Code */
  .t-footer {{
    text-align: center;
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1.5px dashed #000000;
    font-size: 8px;
    font-weight: 700;
    line-height: 1.35;
  }}
  .t-footer-brand {{
    font-weight: 900;
    font-size: 9px;
    text-transform: uppercase;
    margin-bottom: 2px;
  }}

  /* ========================================================
     NOUVEAU DESIGN 2 : MINIMAL GRID CARDS (STYLE COMPACT)
     ======================================================== */
  .ticket-modern-2 {{
    width: 72mm;
    background: #ffffff;
    color: #000000;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    font-size: 9.5px;
    line-height: 1.25;
    padding: 4mm 3mm;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }}

  .t2-box-border {{
    border: 1.5px solid #000;
    border-radius: 4px;
    padding: 5px;
    margin-bottom: 6px;
  }}

  .t2-slot-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 3px;
  }}
  .t2-slot-table tr {{
    border-bottom: 1px dashed #000;
  }}
  .t2-slot-table td {{
    padding: 3.5px 1px;
    vertical-align: top;
    font-size: 9px;
  }}
  .t2-time-col {{
    width: 25mm;
    font-weight: 900;
    font-size: 9px;
    white-space: nowrap;
  }}
  .t2-info-col {{
    padding-left: 4px;
  }}
</style>
</head>
<body>

<div class="dashboard-header">
  <div class="badge-tag">⚡ Aperçu Prototype 80mm Thermique</div>
  <h1>Emploi du Temps — Optimisation Imprimante Ticket de Caisse (80mm)</h1>
  <p class="subtitle">
    Comparaison en direct : <strong>Ancien Design (Courier New, flou et fin)</strong> vs <strong>Nouveaux Designs Modernes</strong> conçus sur mesure pour le contraste thermique (0% nuance grise, typographie grasse ultra-lisible, encadrements nets, support logo ILAS net).
  </p>
</div>

<div class="grid-preview">

  <!-- ================= COL 1: ANCIEN DESIGN ACTUEL ================= -->
  <div class="card-col">
    <div class="card-col-header">
      <h2>1. Actuel (Avant)</h2>
      <span class="pill-status pill-bad">⚠️ Trop fin & Démodé</span>
    </div>
    <div class="card-col-notes">
      • Police <code>Courier New</code> : trop fine (rqaqa bzf), lettres étirées.<br>
      • Pas de logo de l'école.<br>
      • Séparateurs grisés <code>#eee</code> ou <code>#888</code> qui bavent ou disparaissent sur le papier thermique.
    </div>
    <div class="ticket-viewport">
      <div class="ticket-old">
        <div class="header">
          <div class="title">INSTITUT ILAS</div>
          <div style="font-size:10px;">Excellence & Réussite · Deroua</div>
          <div style="font-size:9px;">Autorisation N° 22-200/2020</div>
          <div style="margin-top:4px; font-weight:bold; font-size:11px;">
            EMPLOI DU TEMPS HEBDOMADAIRE
          </div>
        </div>

        <div class="day">📅 LUNDI</div>
        <div class="slot">
          <div>⏰ 17:30 - 19:00</div>
          <div style="font-weight:bold;">Soutien 3AC - Mathématiques</div>
          <div>👨‍🏫 Prof: MOHAMMED BENALI</div>
          <div>🚪 Salle: <strong>SALLE 2</strong></div>
        </div>
        <div class="slot">
          <div>⏰ 19:00 - 20:30</div>
          <div style="font-weight:bold;">Anglais Communication - Ados</div>
          <div>👨‍🏫 Prof: MARYA ANG</div>
          <div>🚪 Salle: <strong>SALLE 5</strong></div>
        </div>

        <div class="day">📅 MARDI</div>
        <div class="slot">
          <div>⏰ 18:00 - 19:30</div>
          <div style="font-weight:bold;">Soutien 2BAC - Physique Chimie</div>
          <div>👨‍🏫 Prof: HASSAN NACHAT</div>
          <div>🚪 Salle: <strong>SALLE 1</strong></div>
        </div>

        <div class="day">📅 SAMEDI</div>
        <div class="slot">
          <div>⏰ 10:00 - 12:00</div>
          <div style="font-weight:bold;">Allemand Débutant - A1</div>
          <div>👨‍🏫 Prof: Ilyas SAKAM</div>
          <div>🚪 Salle: <strong>SALLE 8</strong></div>
        </div>

        <div style="text-align:center; margin-top:10px; border-top:1.5px dashed #000; padding-top:6px; font-size:9.5px;">
          Document officiel · Imprimé le 10/10/2026
        </div>
      </div>
    </div>
  </div>

  <!-- ================= COL 2: PROPOSITION MODERNE 1 (EXECUTIVE BADGE) ================= -->
  <div class="card-col">
    <div class="card-col-header">
      <h2>2. Moderne Pro (Option Recommandée)</h2>
      <span class="pill-status pill-good">⭐ Ultra-Net & Frais</span>
    </div>
    <div class="card-col-notes">
      • Police <strong>Plus Jakarta Sans</strong> (épaisse, géométrique, parfaite pour tête thermique).<br>
      • Header officiel avec Logo ILAS en monochrome noir profond.<br>
      • Cartouches noirs inversés (Inverted Badge) : lecture instantanée des jours.<br>
      • Créneaux avec bordure gauche 3px, badge horaire & pillule de salle.
    </div>
    <div class="ticket-viewport">
      <div class="ticket-modern-1">
        
        <!-- Header ILAS -->
        <div class="t-header">
          <img src="data:image/png;base64,{LOGO_B64}" class="t-logo-img" alt="ILAS">
          <div class="t-brand-name">INSTITUT LES SAGES</div>
          <div class="t-brand-sub">Excellence Pédagogique & Langues</div>
          <div class="t-brand-contact">📞 06 60 29 11 55 · Lot Nora N°10, Deroua</div>
        </div>

        <!-- Titre Inversé -->
        <div class="t-title-badge">
          🗓️ EMPLOI DU TEMPS OFFICIEL
        </div>

        <!-- Meta Fiche Info -->
        <div class="t-meta-box">
          <div class="t-meta-row">
            <span class="t-meta-label">Année Scolaire</span>
            <span class="t-meta-val">2025 / 2026</span>
          </div>
          <div class="t-meta-row">
            <span class="t-meta-label">Imprimé le</span>
            <span class="t-meta-val">10/10/2026 à 16:00</span>
          </div>
          <div class="t-meta-row">
            <span class="t-meta-label">Total Séances</span>
            <span class="t-meta-val">4 cours programmés</span>
          </div>
        </div>

        <!-- JOUR 1: LUNDI -->
        <div class="t-day-banner">
          <span class="t-day-name">📅 LUNDI</span>
          <span class="t-day-count">2 COURS</span>
        </div>

        <div class="t-slot-card">
          <div class="t-slot-top">
            <span class="t-time-pill">⏰ 17:30 – 19:00</span>
            <span class="t-room-pill">🚪 SALLE 2</span>
          </div>
          <div class="t-course-title">Soutien 3AC — Mathématiques</div>
          <div class="t-slot-bottom">
            <span>👨‍🏫 M. BENALI</span>
            <span style="font-weight:900;">GROUPE A</span>
          </div>
        </div>

        <div class="t-slot-card">
          <div class="t-slot-top">
            <span class="t-time-pill">⏰ 19:00 – 20:30</span>
            <span class="t-room-pill">🚪 SALLE 5</span>
          </div>
          <div class="t-course-title">Anglais Communication — Ados</div>
          <div class="t-slot-bottom">
            <span>👩‍🏫 Mme MARYA ANG</span>
            <span style="font-weight:900;">GROUPE 1</span>
          </div>
        </div>

        <!-- JOUR 2: MARDI -->
        <div class="t-day-banner">
          <span class="t-day-name">📅 MARDI</span>
          <span class="t-day-count">1 COURS</span>
        </div>

        <div class="t-slot-card">
          <div class="t-slot-top">
            <span class="t-time-pill">⏰ 18:00 – 19:30</span>
            <span class="t-room-pill">🚪 SALLE 1</span>
          </div>
          <div class="t-course-title">Soutien 2BAC — Physique Chimie</div>
          <div class="t-slot-bottom">
            <span>👨‍🏫 M. NACHAT</span>
            <span style="font-weight:900;">PC BIOF</span>
          </div>
        </div>

        <!-- JOUR 3: SAMEDI -->
        <div class="t-day-banner">
          <span class="t-day-name">📅 SAMEDI</span>
          <span class="t-day-count">1 COURS</span>
        </div>

        <div class="t-slot-card">
          <div class="t-slot-top">
            <span class="t-time-pill">⏰ 10:00 – 12:00</span>
            <span class="t-room-pill">🚪 SALLE 8</span>
          </div>
          <div class="t-course-title">Allemand Débutant — Niveau A1</div>
          <div class="t-slot-bottom">
            <span>👨‍🏫 M. SAKAM</span>
            <span style="font-weight:900;">GROUPE 1</span>
          </div>
        </div>

        <!-- FOOTER TICKET -->
        <div class="t-footer">
          <div class="t-footer-brand">INSTITUT PRIVÉ LES SAGES</div>
          <div>⚠️ Prière d'être présent 5 min avant le début du cours.</div>
          <div style="margin-top:2px; font-size:7.5px;">Autorisation Ministérielle N° 22-200/2020</div>
        </div>

      </div>
    </div>
  </div>

  <!-- ================= COL 3: PROPOSITION MODERNE 2 (TABLEAU COMPACT MINIMAL) ================= -->
  <div class="card-col">
    <div class="card-col-header">
      <h2>3. Moderne Compact (Style Tableau)</h2>
      <span class="pill-status pill-good">📊 Structuré & Net</span>
    </div>
    <div class="card-col-notes">
      • Police <strong>Inter</strong> (boldness 800/900, lisibilité maximale en petites tailles).<br>
      • Format tabulaire compact optimisant la hauteur du rouleau thermique.<br>
      • Cadre supérieur net avec coordonnées condensées.
    </div>
    <div class="ticket-viewport">
      <div class="ticket-modern-2">
        
        <div class="t2-box-border" style="text-align:center;">
          <div style="font-size:12px; font-weight:900; letter-spacing:0.5px;">INSTITUT ILAS</div>
          <div style="font-size:8px; font-weight:700;">PLANNING DES SÉANCES (80MM)</div>
          <div style="font-size:7.5px; font-weight:600; margin-top:2px;">Tél: 05 22 53 22 17 · 06 60 29 11 55</div>
        </div>

        <div style="display:flex; justify-content:space-between; font-size:8px; font-weight:800; border-bottom:1px solid #000; padding-bottom:3px; margin-bottom:4px;">
          <span>ÉLÈVE / FILTRE : GÉNÉRAL</span>
          <span>10/10/2026</span>
        </div>

        <!-- LUNDI TABLE -->
        <div style="font-size:9.5px; font-weight:900; background:#000; color:#fff; padding:2px 4px; margin-top:6px;">
          ■ LUNDI
        </div>
        <table class="t2-slot-table">
          <tr>
            <td class="t2-time-col">
              <strong>17:30 - 19:00</strong><br>
              <span style="font-size:7.5px; border:0.5px solid #000; padding:0 2px;">SALLE 2</span>
            </td>
            <td class="t2-info-col">
              <strong style="font-size:10px;">Mathématiques (3AC)</strong><br>
              <span>Prof: M. BENALI</span>
            </td>
          </tr>
          <tr>
            <td class="t2-time-col">
              <strong>19:00 - 20:30</strong><br>
              <span style="font-size:7.5px; border:0.5px solid #000; padding:0 2px;">SALLE 5</span>
            </td>
            <td class="t2-info-col">
              <strong style="font-size:10px;">Anglais Ados (G1)</strong><br>
              <span>Prof: Mme MARYA</span>
            </td>
          </tr>
        </table>

        <!-- MARDI TABLE -->
        <div style="font-size:9.5px; font-weight:900; background:#000; color:#fff; padding:2px 4px; margin-top:6px;">
          ■ MARDI
        </div>
        <table class="t2-slot-table">
          <tr>
            <td class="t2-time-col">
              <strong>18:00 - 19:30</strong><br>
              <span style="font-size:7.5px; border:0.5px solid #000; padding:0 2px;">SALLE 1</span>
            </td>
            <td class="t2-info-col">
              <strong style="font-size:10px;">Physique Chimie (2BAC)</strong><br>
              <span>Prof: M. NACHAT</span>
            </td>
          </tr>
        </table>

        <!-- SAMEDI TABLE -->
        <div style="font-size:9.5px; font-weight:900; background:#000; color:#fff; padding:2px 4px; margin-top:6px;">
          ■ SAMEDI
        </div>
        <table class="t2-slot-table">
          <tr>
            <td class="t2-time-col">
              <strong>10:00 - 12:00</strong><br>
              <span style="font-size:7.5px; border:0.5px solid #000; padding:0 2px;">SALLE 8</span>
            </td>
            <td class="t2-info-col">
              <strong style="font-size:10px;">Allemand A1 (G1)</strong><br>
              <span>Prof: M. SAKAM</span>
            </td>
          </tr>
        </table>

        <div style="border-top:1.5px dashed #000; margin-top:8px; padding-top:4px; text-align:center; font-size:7.5px; font-weight:700;">
          Institut Privé Les Sages · Excellence & Réussite
        </div>

      </div>
    </div>
  </div>

</div>

</body>
</html>
"""

output_path = os.path.join(BASE_DIR, "preview_output", "preview_80mm_timetable.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(preview_html)

print("Preview HTML written to:", output_path)
