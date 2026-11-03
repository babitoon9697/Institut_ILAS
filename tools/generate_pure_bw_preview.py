# -*- coding: utf-8 -*-
"""
Generate 100% Pure Black and White (0% color, 0% gray) preview for 80mm thermal receipt.
Shows exact simulated thermal output without any color tint.
"""
import base64
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "preview_output", "logo_clean_bw.png")

with open(LOGO_PATH, "rb") as f:
    b64_logo = base64.b64encode(f.read()).decode("utf-8")

html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Simulation Réelle : 100% Noir & Blanc Pur (Thermal 80mm)</title>
<!-- Polices optimisées pour têtes d'impression thermique -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800;900&family=Inter:wght@700;800;900&family=Space+Grotesk:wght@700;800&display=swap" rel="stylesheet">
<style>
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  body {{
    background: #18181b;
    color: #ffffff;
    font-family: 'Plus Jakarta Sans', Arial, sans-serif;
    padding: 30px 15px;
  }}

  .header-banner {{
    max-width: 1100px;
    margin: 0 auto 25px auto;
    background: #27272a;
    border: 1px solid #3f3f46;
    padding: 20px 24px;
    border-radius: 12px;
  }}
  .header-banner h1 {{
    font-size: 20px;
    font-weight: 900;
    letter-spacing: 0.5px;
  }}
  .header-banner p {{
    font-size: 13px;
    color: #a1a1aa;
    margin-top: 6px;
    line-height: 1.4;
  }}

  .compare-grid {{
    max-width: 1100px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    align-items: start;
  }}

  .card-wrap {{
    background: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 12px;
    overflow: hidden;
  }}
  .card-top {{
    padding: 14px 18px;
    border-bottom: 1px solid #3f3f46;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .card-title {{
    font-size: 14px;
    font-weight: 800;
  }}
  .pill {{
    font-size: 10px;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 10px;
  }}
  .pill-bad {{ background: #7f1d1d; color: #fca5a5; }}
  .pill-pure {{ background: #14532d; color: #86efac; }}

  .stage {{
    background: #52525b;
    padding: 35px 20px;
    display: flex;
    justify-content: center;
  }}

  /* =========================================================
     1. TICKET ACTUEL (AVANT) — Flou, Courier fin, Gris qui bave
     ========================================================= */
  .ticket-old {{
    width: 72mm;
    background: #ffffff;
    color: #000000;
    font-family: 'Courier New', monospace;
    font-size: 10.5px;
    padding: 4mm 3mm;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
  }}
  .ticket-old .hd {{
    text-align: center;
    border-bottom: 1.5px dashed #000;
    padding-bottom: 5px;
    margin-bottom: 6px;
  }}
  .ticket-old .day {{
    font-weight: bold;
    background: #eee;
    padding: 2px 4px;
    margin-top: 6px;
    border-left: 3px solid #000;
  }}
  .ticket-old .slot {{
    padding: 4px 0;
    border-bottom: 1px dotted #888;
  }}

  /* =========================================================
     2. NOUVEAU TICKET 100% PURE THERMAL MONOCHROME
     Strictement: #000000 (Noir) ou #ffffff (Blanc).
     Typographie: Plus Jakarta Sans / Space Grotesk (800-900 Ultra-Bold)
     ========================================================= */
  .ticket-pure-bw {{
    width: 72mm;
    background: #ffffff;
    color: #000000;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    font-size: 10px;
    line-height: 1.25;
    padding: 5mm 3.5mm;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
  }}

  /* Logo monochrome pur (1-bit style) */
  .bw-logo {{
    max-width: 44mm;
    height: auto;
    display: block;
    margin: 0 auto 3px auto;
  }}

  .bw-header {{
    text-align: center;
  }}
  .bw-brand-name {{
    font-family: 'Space Grotesk', 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: #000000;
    line-height: 1.1;
  }}
  .bw-brand-sub {{
    font-size: 8px;
    font-weight: 800;
    text-transform: uppercase;
    color: #000000;
    letter-spacing: 0.3px;
    margin-top: 2px;
  }}
  .bw-brand-contact {{
    font-size: 8px;
    font-weight: 700;
    color: #000000;
    margin-top: 1.5px;
  }}

  /* Cartouche inversé (Noir plein, texte blanc - rendu 100% parfait sur thermique) */
  .bw-title-badge {{
    background: #000000;
    color: #ffffff;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    text-align: center;
    padding: 4px 0;
    margin: 7px 0 5px 0;
    border-radius: 2px;
  }}

  /* Boîte info meta */
  .bw-meta-box {{
    border: 1.5px solid #000000;
    border-radius: 3px;
    padding: 4px 6px;
    margin-bottom: 7px;
    font-size: 9px;
  }}
  .bw-meta-row {{
    display: flex;
    justify-content: space-between;
    padding: 1.5px 0;
  }}
  .bw-meta-row:not(:last-child) {{
    border-bottom: 1px dashed #000000;
  }}
  .bw-meta-lbl {{
    font-size: 8px;
    font-weight: 800;
    text-transform: uppercase;
  }}
  .bw-meta-val {{
    font-weight: 900;
    text-align: right;
  }}

  /* Bandeau de jour */
  .bw-day-banner {{
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
  .bw-day-title {{
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.5px;
  }}
  .bw-day-cnt {{
    font-size: 8px;
    font-weight: 900;
    background: #ffffff;
    color: #000000;
    padding: 0 4px;
    border-radius: 2px;
  }}

  /* Créneau thermique avec trait épais à gauche */
  .bw-slot {{
    border-left: 3.5px solid #000000;
    padding: 3px 0 4px 6px;
    margin-bottom: 5px;
    border-bottom: 1px dashed #000000;
  }}
  .bw-slot:last-child {{
    border-bottom: none;
  }}

  .bw-slot-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2px;
  }}
  .bw-time {{
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.2px;
  }}
  .bw-room {{
    font-size: 8.5px;
    font-weight: 900;
    border: 1.2px solid #000000;
    padding: 0 4px;
    border-radius: 2px;
    text-transform: uppercase;
  }}
  .bw-course {{
    font-size: 11px;
    font-weight: 900;
    line-height: 1.25;
    margin-bottom: 2px;
  }}
  .bw-slot-bot {{
    display: flex;
    justify-content: space-between;
    font-size: 8.5px;
    font-weight: 800;
  }}

  /* Pied de ticket */
  .bw-footer {{
    text-align: center;
    margin-top: 10px;
    padding-top: 6px;
    border-top: 1.5px dashed #000000;
    font-size: 8px;
    font-weight: 800;
    line-height: 1.35;
  }}
</style>
</head>
<body>

<div class="header-banner">
  <h1>🖨️ Simulation Thermique 100% Noir & Blanc Pur (Zéro Couleur, Zéro Gris)</h1>
  <p>
    Tout élément graphique (logo, textes, encadrements, séparateurs) a été converti en <strong>vrai monochrome binaire (#000000 ou #ffffff)</strong> pour correspondre exactement à ce que la tête thermique 80mm imprime sans aucun tramage de points.
  </p>
</div>

<div class="compare-grid">

  <!-- AVANT -->
  <div class="card-wrap">
    <div class="card-top">
      <span class="card-title">1. Actuel (Courier New)</span>
      <span class="pill pill-bad">Fin & Dithering Gris</span>
    </div>
    <div class="stage">
      <div class="ticket-old">
        <div class="hd">
          <div style="font-size:13px; font-weight:bold;">INSTITUT ILAS</div>
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

  <!-- NOUVEAU PURE B&W -->
  <div class="card-wrap">
    <div class="card-top">
      <span class="card-title">2. Nouveau Pro (100% Noir Pur & Police Grasse)</span>
      <span class="pill pill-pure">Épais & Ultra-Lisible</span>
    </div>
    <div class="stage">
      <div class="ticket-pure-bw">
        
        <!-- Header avec Logo ILAS Pur Noir et Blanc -->
        <div class="bw-header">
          <img src="data:image/png;base64,{b64_logo}" class="bw-logo" alt="ILAS">
          <div class="bw-brand-name">INSTITUT LES SAGES</div>
          <div class="bw-brand-sub">Excellence Pédagogique & Langues</div>
          <div class="bw-brand-contact">Tel: 06 60 29 11 55 · Lot Nora N°10, Deroua</div>
        </div>

        <!-- Titre Inversé -->
        <div class="bw-title-badge">
          [ EMPLOI DU TEMPS OFFICIEL ]
        </div>

        <!-- Informations Récapitulatives -->
        <div class="bw-meta-box">
          <div class="bw-meta-row">
            <span class="bw-meta-lbl">ANNEE SCOLAIRE</span>
            <span class="bw-meta-val">2025 / 2026</span>
          </div>
          <div class="bw-meta-row">
            <span class="bw-meta-lbl">DATE D'EMISSION</span>
            <span class="bw-meta-val">10/10/2026 a 16:00</span>
          </div>
          <div class="bw-meta-row">
            <span class="bw-meta-lbl">TOTAL SEANCES</span>
            <span class="bw-meta-val">4 Cours Hebdo</span>
          </div>
        </div>

        <!-- LUNDI -->
        <div class="bw-day-banner">
          <span class="bw-day-title">>> LUNDI</span>
          <span class="bw-day-cnt">2 COURS</span>
        </div>

        <div class="bw-slot">
          <div class="bw-slot-top">
            <span class="bw-time">[17:30 - 19:00]</span>
            <span class="bw-room">SALLE 2</span>
          </div>
          <div class="bw-course">Soutien 3AC - Mathematiques</div>
          <div class="bw-slot-bot">
            <span>Prof: M. BENALI</span>
            <span>GROUPE A</span>
          </div>
        </div>

        <div class="bw-slot">
          <div class="bw-slot-top">
            <span class="bw-time">[19:00 - 20:30]</span>
            <span class="bw-room">SALLE 5</span>
          </div>
          <div class="bw-course">Anglais Communication - Ados</div>
          <div class="bw-slot-bot">
            <span>Prof: Mme MARYA ANG</span>
            <span>GROUPE 1</span>
          </div>
        </div>

        <!-- MARDI -->
        <div class="bw-day-banner">
          <span class="bw-day-title">>> MARDI</span>
          <span class="bw-day-cnt">1 COURS</span>
        </div>

        <div class="bw-slot">
          <div class="bw-slot-top">
            <span class="bw-time">[18:00 - 19:30]</span>
            <span class="bw-room">SALLE 1</span>
          </div>
          <div class="bw-course">Soutien 2BAC - Physique Chimie</div>
          <div class="bw-slot-bot">
            <span>Prof: M. NACHAT</span>
            <span>PC BIOF</span>
          </div>
        </div>

        <!-- SAMEDI -->
        <div class="bw-day-banner">
          <span class="bw-day-title">>> SAMEDI</span>
          <span class="bw-day-cnt">1 COURS</span>
        </div>

        <div class="bw-slot">
          <div class="bw-slot-top">
            <span class="bw-time">[10:00 - 12:00]</span>
            <span class="bw-room">SALLE 8</span>
          </div>
          <div class="bw-course">Allemand Debutant - Niveau A1</div>
          <div class="bw-slot-bot">
            <span>Prof: M. SAKAM</span>
            <span>GROUPE 1</span>
          </div>
        </div>

        <!-- PIED DE TICKET -->
        <div class="bw-footer">
          <div style="font-weight:900; font-size:9px;">INSTITUT PRIVE LES SAGES</div>
          <div>* Priere d'arriver 5 minutes avant le cours.</div>
          <div style="margin-top:2px; font-size:7.5px;">Autorisation Ministerielle N° 22-200/2020</div>
        </div>

      </div>
    </div>
  </div>

</div>

</body>
</html>
"""

out_file = os.path.join(BASE_DIR, "preview_output", "pure_bw_comparison.html")
with open(out_file, "w", encoding="utf-8") as f:
    f.write(html)

print("Pure B&W comparison HTML written to:", out_file)
