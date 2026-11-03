# -*- coding: utf-8 -*-
"""
Generate a side-by-side comparison of 80mm Thermal Tariffs (Catalogue des tarifs).
100% Pure Black and White (0% color, 0% gray/dithering).
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
<title>Simulation Catalogue des Tarifs — 80mm Thermique (100% Noir & Blanc)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800;900&family=Space+Grotesk:wght@700;800&family=Tajawal:wght@700;800;900&display=swap" rel="stylesheet">
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
     1. ACTUEL (AVANT) — Consolas monospace, gris #eee/#333
     ========================================================= */
  .ticket-old {{
    width: 68mm;
    background: #ffffff;
    color: #000000;
    font-family: 'Consolas', monospace;
    font-size: 10.5px;
    font-weight: 700;
    padding: 4mm 2mm;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
  }}

  /* =========================================================
     2. NOUVEAU PRO : 100% NOIR & BLANC THERMIQUE
     Plus Jakarta Sans + Tajawal, Logo net, badges inversés,
     prix mis en valeur avec bordure nette, zéro tramage gris.
     ========================================================= */
  .ticket-pure-tariffs {{
    width: 72mm;
    background: #ffffff;
    color: #000000;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    font-size: 10px;
    line-height: 1.25;
    padding: 5mm 3mm;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
  }}

  .t-logo {{
    max-width: 44mm;
    height: auto;
    display: block;
    margin: 0 auto 3px auto;
  }}
  .t-header {{
    text-align: center;
  }}
  .t-brand-name {{
    font-family: 'Space Grotesk', 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: #000000;
    line-height: 1.1;
  }}
  .t-brand-sub {{
    font-size: 8px;
    font-weight: 800;
    text-transform: uppercase;
    color: #000000;
    letter-spacing: 0.3px;
    margin-top: 2px;
  }}
  .t-brand-contact {{
    font-size: 8px;
    font-weight: 700;
    color: #000000;
    margin-top: 1.5px;
  }}

  .t-title-badge {{
    background: #000000;
    color: #ffffff;
    font-size: 10.5px;
    font-weight: 900;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    text-align: center;
    padding: 4px 2px;
    margin: 7px 0 3px 0;
    border-radius: 2px;
  }}
  .t-subtitle-ar {{
    text-align: center;
    font-family: 'Tajawal', sans-serif;
    font-size: 10px;
    font-weight: 800;
    direction: rtl;
    color: #000000;
    margin-bottom: 5px;
  }}

  .t-meta-box {{
    border: 1.5px solid #000000;
    border-radius: 3px;
    padding: 3.5px 6px;
    margin-bottom: 7px;
    font-size: 8.5px;
  }}
  .t-meta-row {{
    display: flex;
    justify-content: space-between;
    padding: 1px 0;
  }}
  .t-meta-lbl {{
    font-size: 7.5px;
    font-weight: 800;
    text-transform: uppercase;
  }}
  .t-meta-val {{
    font-weight: 900;
    text-align: right;
  }}

  /* Bannière Catégorie / Niveau */
  .t-cat-banner {{
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
  .t-cat-title {{
    font-size: 9.5px;
    font-weight: 900;
    letter-spacing: 0.4px;
    text-transform: uppercase;
  }}
  .t-cat-badge {{
    font-size: 7.5px;
    font-weight: 900;
    background: #ffffff;
    color: #000000;
    padding: 0 4px;
    border-radius: 2px;
  }}

  /* Ligne de tarif nette */
  .t-tariff-card {{
    border-left: 3.5px solid #000000;
    padding: 3.5px 0 4px 6px;
    margin-bottom: 4.5px;
    border-bottom: 1px dashed #000000;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 6px;
  }}
  .t-tariff-card:last-child {{
    border-bottom: none;
  }}

  .t-tariff-left {{
    flex: 1;
  }}
  .t-subject-fr {{
    font-size: 10.5px;
    font-weight: 900;
    color: #000000;
    line-height: 1.2;
  }}
  .t-subject-ar {{
    font-family: 'Tajawal', sans-serif;
    font-size: 9px;
    font-weight: 800;
    direction: rtl;
    color: #000000;
    margin-top: 1px;
  }}
  .t-schedule-pill {{
    display: inline-block;
    font-size: 7.5px;
    font-weight: 800;
    margin-top: 2px;
  }}

  .t-tariff-right {{
    text-align: right;
    white-space: nowrap;
  }}
  .t-price-box {{
    background: #000000;
    color: #ffffff;
    font-size: 11px;
    font-weight: 900;
    padding: 1.5px 5px;
    border-radius: 2px;
    display: inline-block;
    letter-spacing: 0.2px;
  }}
  .t-cycle-lbl {{
    font-size: 7.5px;
    font-weight: 800;
    text-transform: uppercase;
    margin-top: 1.5px;
  }}

  /* Boîte Frais d'inscription */
  .t-reg-box {{
    border: 2px solid #000000;
    border-radius: 4px;
    padding: 5px 6px;
    margin-top: 8px;
    text-align: center;
    background: #ffffff;
  }}
  .t-reg-title {{
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.3px;
    text-transform: uppercase;
  }}
  .t-reg-sub {{
    font-family: 'Tajawal', sans-serif;
    font-size: 9.5px;
    font-weight: 800;
    direction: rtl;
    margin-top: 1px;
  }}

  /* Footer */
  .t-footer {{
    text-align: center;
    margin-top: 9px;
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
  <h1>🖨️ Catalogue des Tarifs — Optimisation Thermique 80mm</h1>
  <p>
    Comparaison : <strong>Ancien Design (Consolas, gris, sans logo)</strong> vs <strong>Nouveau Design 100% Noir & Blanc Pur</strong> avec logo officiel, bannières inversées, prix bien contrastés et typographie bilingue nette.
  </p>
</div>

<div class="compare-grid">

  <!-- ================= COL 1: ACTUEL (AVANT) ================= -->
  <div class="card-wrap">
    <div class="card-top">
      <span class="card-title">1. Actuel (Avant)</span>
      <span class="pill pill-bad">Consolas & Gris #eee</span>
    </div>
    <div class="stage">
      <div class="ticket-old">
        <div style="text-align:center;">
          <div style="font-size:13px; font-weight:900;">INSTITUT ILAS</div>
          <div style="font-size:8.5px;">المعهد الخاص للغات والدروس التوجيهية</div>
          <div style="font-size:8px;">Aut. 22-200/2020 · Deroua الدروة</div>
          <div style="font-size:8.5px; font-weight:900;">06 60 29 11 55 / 06 70 38 48 73</div>
        </div>
        <div style="border-top:1.5px solid #000; margin:4px 0;"></div>
        <div style="text-align:center; font-weight:900; font-size:10px;">CYCLE COLLÈGE & LYCÉE</div>
        <div style="text-align:center; font-size:9.5px; direction:rtl;">سلك الإعدادي والثانوي التوجيهي</div>
        <div style="border-top:1px dashed #000; margin:4px 0;"></div>

        <table style="width:100%; border-collapse:collapse; font-size:9.5px;">
          <tr>
            <td colspan="2" style="font-weight:900; background:#eee; padding:2px; font-size:9px;">
              3ÈME ANNÉE COLLÈGE (3AC)
            </td>
          </tr>
          <tr>
            <td style="padding:2.5px 0; border-bottom:1px dashed #000;">
              <div><strong>Mathématiques (3AC)</strong></div>
              <div style="font-size:8px; color:#333;">الرياضيات</div>
              <div style="font-size:7.5px;">2 séances / semaine (3h)</div>
            </td>
            <td style="text-align:right; font-weight:900; font-size:11px; padding:2.5px 0; border-bottom:1px dashed #000; vertical-align:top;">
              250 DH
              <div style="font-size:7.5px; font-weight:normal;">/ mois</div>
            </td>
          </tr>
          <tr>
            <td style="padding:2.5px 0; border-bottom:1px dashed #000;">
              <div><strong>Physique Chimie (3AC)</strong></div>
              <div style="font-size:8px; color:#333;">الفيزياء والكيمياء</div>
              <div style="font-size:7.5px;">2 séances / semaine (3h)</div>
            </td>
            <td style="text-align:right; font-weight:900; font-size:11px; padding:2.5px 0; border-bottom:1px dashed #000; vertical-align:top;">
              250 DH
              <div style="font-size:7.5px; font-weight:normal;">/ mois</div>
            </td>
          </tr>

          <tr>
            <td colspan="2" style="font-weight:900; background:#eee; padding:2px; font-size:9px;">
              LANGUES VIVANTES (TOUS NIVEAUX)
            </td>
          </tr>
          <tr>
            <td style="padding:2.5px 0; border-bottom:1px dashed #000;">
              <div><strong>Anglais Général (Ados/Adultes)</strong></div>
              <div style="font-size:8px; color:#333;">اللغة الإنجليزية</div>
              <div style="font-size:7.5px;">3 séances / semaine (4h30)</div>
            </td>
            <td style="text-align:right; font-weight:900; font-size:11px; padding:2.5px 0; border-bottom:1px dashed #000; vertical-align:top;">
              1300 DH
              <div style="font-size:7.5px; font-weight:normal;">/ trimestre</div>
            </td>
          </tr>
        </table>

        <div style="border:1.5px dashed #000; padding:3px; margin-top:5px; text-align:center; font-size:10px; font-weight:900;">
          واجب التسجيل: 200 DH / Frais Inscr.
        </div>
        <div style="border-top:1px dashed #000; margin:5px 0;"></div>
        <div style="text-align:center; font-size:8px;">شكراً لثقتكم · Merci de votre confiance · ILAS</div>
      </div>
    </div>
  </div>

  <!-- ================= COL 2: NOUVEAU PRO (100% PURE B&W) ================= -->
  <div class="card-wrap">
    <div class="card-top">
      <span class="card-title">2. Nouveau Pro (100% Noir Pur & Moderne)</span>
      <span class="pill pill-pure">Épais, Net & Attractif</span>
    </div>
    <div class="stage">
      <div class="ticket-pure-tariffs">
        
        <!-- En-tête officiel avec Logo ILAS Pur Noir et Blanc -->
        <div class="t-header">
          <img src="data:image/png;base64,{b64_logo}" class="t-logo" alt="ILAS">
          <div class="t-brand-name">INSTITUT LES SAGES</div>
          <div class="t-brand-sub">Excellence Pédagogique & Langues</div>
          <div class="t-brand-contact">Tél: 06 60 29 11 55 · Lot Nora N°10, Deroua</div>
        </div>

        <!-- Titre Inversé Bilingue -->
        <div class="t-title-badge">
          [ CATALOGUE DES TARIFS OFFICIELS ]
        </div>
        <div class="t-subtitle-ar">
          دليل الأسعار والتعريفات المعتمدة
        </div>

        <!-- Meta Fiche Info -->
        <div class="t-meta-box">
          <div class="t-meta-row">
            <span class="t-meta-lbl">Année Scolaire</span>
            <span class="t-meta-val">2025 / 2026</span>
          </div>
          <div class="t-meta-row">
            <span class="t-meta-lbl">Date d'Émission</span>
            <span class="t-meta-val">10/10/2026</span>
          </div>
          <div class="t-meta-row">
            <span class="t-meta-lbl">Validité</span>
            <span class="t-meta-val">Tarifs en vigueur</span>
          </div>
        </div>

        <!-- GROUPE 1: 3AC -->
        <div class="t-cat-banner">
          <span class="t-cat-title">&gt;&gt; 3ÈME ANNÉE COLLÈGE (3AC)</span>
          <span class="t-cat-badge">SOUTIEN</span>
        </div>

        <div class="t-tariff-card">
          <div class="t-tariff-left">
            <div class="t-subject-fr">Mathématiques (3AC)</div>
            <div class="t-subject-ar">الرياضيات — الثالثة إعدادي</div>
            <div class="t-schedule-pill">⏱️ 2 séances / sem. (3h00)</div>
          </div>
          <div class="t-tariff-right">
            <span class="t-price-box">250 DH</span>
            <div class="t-cycle-lbl">/ Mois</div>
          </div>
        </div>

        <div class="t-tariff-card">
          <div class="t-tariff-left">
            <div class="t-subject-fr">Physique Chimie (3AC)</div>
            <div class="t-subject-ar">الفيزياء والكيمياء</div>
            <div class="t-schedule-pill">⏱️ 2 séances / sem. (3h00)</div>
          </div>
          <div class="t-tariff-right">
            <span class="t-price-box">250 DH</span>
            <div class="t-cycle-lbl">/ Mois</div>
          </div>
        </div>

        <!-- GROUPE 2: LANGUES -->
        <div class="t-cat-banner">
          <span class="t-cat-title">&gt;&gt; LANGUES VIVANTES</span>
          <span class="t-cat-badge">FORMATION</span>
        </div>

        <div class="t-tariff-card">
          <div class="t-tariff-left">
            <div class="t-subject-fr">Anglais Général — Ados/Adultes</div>
            <div class="t-subject-ar">اللغة الإنجليزية التواصلية</div>
            <div class="t-schedule-pill">⏱️ 3 séances / sem. (4h30)</div>
          </div>
          <div class="t-tariff-right">
            <span class="t-price-box">1300 DH</span>
            <div class="t-cycle-lbl">/ Trimestre</div>
          </div>
        </div>

        <div class="t-tariff-card">
          <div class="t-tariff-left">
            <div class="t-subject-fr">Allemand Débutant — A1</div>
            <div class="t-subject-ar">اللغة الألمانية للمبتدئين</div>
            <div class="t-schedule-pill">⏱️ 2 séances / sem. (4h00)</div>
          </div>
          <div class="t-tariff-right">
            <span class="t-price-box">1200 DH</span>
            <div class="t-cycle-lbl">/ Trimestre</div>
          </div>
        </div>

        <!-- FRAIS D'INSCRIPTION CARTOUCHE NOIR -->
        <div class="t-reg-box">
          <div class="t-reg-title">Frais d'Inscription : 200 DH</div>
          <div class="t-reg-sub">واجب التسجيل السنوي للتأمين والملف</div>
        </div>

        <!-- FOOTER TICKET -->
        <div class="t-footer">
          <div style="font-weight:900; font-size:9px;">INSTITUT PRIVÉ LES SAGES</div>
          <div>شكراً لثقتكم · Merci de votre confiance</div>
          <div style="margin-top:2px; font-size:7.5px;">Autorisation Ministérielle N° 22-200/2020</div>
        </div>

      </div>
    </div>
  </div>

</div>

</body>
</html>
"""

out_file = os.path.join(BASE_DIR, "preview_output", "tariffs_80mm_comparison.html")
with open(out_file, "w", encoding="utf-8") as f:
    f.write(html)

print("Tariffs 80mm preview HTML generated:", out_file)
