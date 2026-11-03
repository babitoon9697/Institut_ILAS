# -*- coding: utf-8 -*-
"""
Builder for Deutsch Zertifikat B1 Modern Examination PDFs
for Student ANASS BENYAHIA (DOB: 26.01.2007, CIN: WB226817)
Institut Privé de Langues Les Sages (ILAS)
"""

import os
import subprocess
import pymupdf

def get_logo_b64():
    logo_path = "logo_b64.txt"
    if os.path.exists(logo_path):
        with open(logo_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def build_student_exam_html():
    logo_b64 = get_logo_b64()
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Deutsch Zertifikat B1 – Prüfungsheft – ANASS BENYAHIA</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 0;
  }}
  *, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #0f172a;
    background: #ffffff;
    font-size: 11px;
    line-height: 1.35;
  }}
  .exam-page {{
    width: 210mm;
    height: 297mm;
    padding: 12mm 15mm 10mm 15mm;
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    background: #ffffff;
  }}
  .exam-page:last-child {{
    page-break-after: auto;
  }}

  /* Header & Footer */
  .page-top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1.5px solid #0f2b48;
    padding-bottom: 5px;
    margin-bottom: 8px;
    font-size: 8.5px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #475569;
  }}
  .page-top-bar .inst-tag {{
    font-weight: 700;
    color: #0f2b48;
  }}
  .page-top-bar .cand-tag {{
    font-weight: 600;
    color: #1e3a8a;
  }}
  .page-footer-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #cbd5e1;
    padding-top: 5px;
    margin-top: 6px;
    font-size: 8px;
    color: #64748b;
  }}
  .page-footer-bar .footer-inst {{
    font-weight: 600;
  }}
  .page-footer-bar .footer-page {{
    font-weight: 700;
    color: #0f2b48;
  }}

  /* Module Head Banners */
  .module-header {{
    background: linear-gradient(135deg, #0f2b48 0%, #1e3a8a 100%);
    color: #ffffff;
    padding: 6px 12px;
    border-radius: 5px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }}
  .module-header .module-title {{
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .module-header .module-meta {{
    display: flex;
    gap: 12px;
    font-size: 10px;
    font-weight: 600;
  }}
  .module-badge {{
    background: rgba(255, 255, 255, 0.2);
    padding: 2px 8px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.3);
  }}

  /* Section Task Box */
  .task-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #2563eb;
    padding: 6px 10px;
    border-radius: 4px;
    margin-bottom: 8px;
  }}
  .task-box-title {{
    font-size: 11px;
    font-weight: 700;
    color: #0f2b48;
    display: flex;
    justify-content: space-between;
    margin-bottom: 2px;
  }}
  .task-box-desc {{
    font-size: 9.5px;
    color: #334155;
    line-height: 1.3;
  }}

  /* German Tri-color Bar */
  .ger-bar {{
    display: flex;
    height: 4px;
    width: 100%;
    margin-bottom: 8px;
    border-radius: 2px;
    overflow: hidden;
  }}
  .ger-bar .bar-black {{ background: #111827; flex: 1; }}
  .ger-bar .bar-red {{ background: #dc2626; flex: 1; }}
  .ger-bar .bar-gold {{ background: #f59e0b; flex: 1; }}

  /* Cover Styles */
  .cover-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 8px;
    border-bottom: 2px solid #0f2b48;
  }}
  .cover-inst-info {{
    line-height: 1.25;
  }}
  .cover-inst-title {{
    font-size: 13px;
    font-weight: 900;
    color: #0f2b48;
    letter-spacing: 0.3px;
  }}
  .cover-inst-sub {{
    font-size: 9.5px;
    font-weight: 700;
    color: #b91c1c;
  }}
  .cover-inst-contact {{
    font-size: 8px;
    color: #64748b;
  }}
  .cover-logo-img {{
    height: 48px;
    width: auto;
    object-fit: contain;
  }}
  .cover-hero {{
    text-align: center;
    padding: 12px 0 10px 0;
  }}
  .cover-level-badge {{
    display: inline-block;
    background: #0f2b48;
    color: #ffffff;
    font-size: 11px;
    font-weight: 800;
    padding: 3px 14px;
    border-radius: 20px;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }}
  .cover-hero h1 {{
    font-size: 23px;
    font-weight: 900;
    color: #0f2b48;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
  }}
  .cover-hero h2 {{
    font-size: 13px;
    font-weight: 700;
    color: #2563eb;
    margin-bottom: 4px;
  }}
  .cover-hero p {{
    font-size: 9.5px;
    color: #64748b;
    font-weight: 500;
  }}

  /* Candidate Profile Card */
  .candidate-card {{
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  .candidate-card-header {{
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    color: #0f2b48;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
    padding-bottom: 4px;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .candidate-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 16px;
  }}
  .candidate-field {{
    display: flex;
    flex-direction: column;
  }}
  .cand-label {{
    font-size: 8px;
    text-transform: uppercase;
    font-weight: 700;
    color: #64748b;
    margin-bottom: 1px;
  }}
  .cand-value {{
    font-size: 11.5px;
    font-weight: 700;
    color: #0f172a;
    background: #ffffff;
    padding: 4px 8px;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
  }}
  .cand-value-highlight {{
    color: #1e3a8a;
    background: #eff6ff;
    border-color: #bfdbfe;
  }}

  /* Module Score Table */
  .score-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 12px;
    font-size: 10px;
  }}
  .score-table th {{
    background: #0f2b48;
    color: #ffffff;
    font-weight: 700;
    padding: 6px 8px;
    text-align: left;
    border: 1px solid #0f2b48;
  }}
  .score-table th.center, .score-table td.center {{
    text-align: center;
  }}
  .score-table td {{
    padding: 5px 8px;
    border: 1px solid #cbd5e1;
    color: #1e293b;
  }}
  .score-table tr:nth-child(even) {{
    background: #f8fafc;
  }}
  .score-table tr.total-row {{
    background: #eff6ff;
    font-weight: 800;
    color: #0f2b48;
  }}
  .score-table tr.total-row td {{
    border-top: 2px solid #2563eb;
  }}

  /* Rules & Sign Box */
  .rules-grid {{
    display: grid;
    grid-template-columns: 2fr 1.2fr;
    gap: 12px;
    margin-top: 4px;
  }}
  .rules-box {{
    background: #fffbeb;
    border: 1px solid #fef3c7;
    border-left: 3px solid #f59e0b;
    padding: 8px 10px;
    border-radius: 4px;
    font-size: 9px;
    color: #92400e;
  }}
  .rules-box ul {{
    margin-left: 14px;
    margin-top: 4px;
  }}
  .rules-box li {{
    margin-bottom: 2px;
  }}
  .sign-box {{
    border: 1.5px dashed #94a3b8;
    border-radius: 6px;
    padding: 8px;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: #ffffff;
  }}
  .sign-box-label {{
    font-size: 8.5px;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
  }}
  .sign-area {{
    height: 44px;
    border-bottom: 1px solid #cbd5e1;
    margin-bottom: 4px;
  }}

  /* Content Cards & Articles */
  .article-card {{
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 9px 12px;
    margin-bottom: 9px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }}
  .article-headline {{
    font-size: 12.5px;
    font-weight: 800;
    color: #0f2b48;
    margin-bottom: 5px;
    padding-bottom: 3px;
    border-bottom: 1px solid #e2e8f0;
  }}
  .article-card p {{
    font-size: 9.6px;
    line-height: 1.38;
    color: #1e293b;
    margin-bottom: 5px;
    text-align: justify;
  }}
  .article-card p:last-child {{
    margin-bottom: 0;
  }}

  /* Question Items */
  .question-item {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 6px 9px;
    margin-bottom: 6px;
  }}
  .question-text {{
    font-size: 10px;
    font-weight: 700;
    color: #0f2b48;
    margin-bottom: 4px;
  }}
  .options-group {{
    display: flex;
    flex-direction: column;
    gap: 3px;
  }}
  .options-group-horizontal {{
    display: flex;
    flex-direction: row;
    gap: 12px;
    margin-top: 3px;
  }}
  .option-label {{
    display: flex;
    align-items: flex-start;
    gap: 6px;
    font-size: 9.2px;
    color: #334155;
    line-height: 1.25;
  }}
  .checkbox-box {{
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 1.5px solid #64748b;
    border-radius: 2px;
    margin-top: 1px;
    flex-shrink: 0;
    background: #ffffff;
  }}
  .option-code {{
    font-weight: 700;
    color: #0f2b48;
    min-width: 14px;
  }}

  /* True / False Matrix Table */
  .rf-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5px;
    margin-bottom: 6px;
  }}
  .rf-table th {{
    background: #f1f5f9;
    color: #0f2b48;
    font-weight: 700;
    padding: 5px 6px;
    border: 1px solid #cbd5e1;
    text-align: left;
  }}
  .rf-table td {{
    padding: 5px 6px;
    border: 1px solid #cbd5e1;
    vertical-align: middle;
  }}
  .rf-check-cell {{
    width: 44px;
    text-align: center;
    background: #ffffff;
  }}
  .rf-box {{
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 1.5px solid #475569;
    border-radius: 3px;
  }}

  /* Opinion Cards (Aufgabe 2) */
  .opinions-container {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 6px;
    margin-bottom: 8px;
  }}
  .opinion-card {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 9px;
    line-height: 1.3;
  }}
  .opinion-card-header {{
    font-size: 9.5px;
    font-weight: 800;
    color: #1e3a8a;
    margin-bottom: 3px;
    padding-bottom: 2px;
    border-bottom: 1px solid #e2e8f0;
  }}

  /* Course matching (Aufgabe 3) */
  .matching-container {{
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 8px;
    margin-top: 4px;
  }}
  .course-list {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .course-item {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 3px;
    padding: 4px 6px;
    font-size: 8.8px;
    line-height: 1.25;
  }}
  .course-letter {{
    display: inline-block;
    background: #0f2b48;
    color: #ffffff;
    font-weight: 800;
    font-size: 8px;
    padding: 1px 4px;
    border-radius: 2px;
    margin-right: 3px;
  }}
  .course-title {{
    font-weight: 700;
    color: #0f2b48;
  }}
  .situation-item {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    padding: 5px 6px;
    margin-bottom: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 9px;
  }}
  .situation-text {{
    flex: 1;
    padding-right: 8px;
    line-height: 1.25;
  }}
  .match-box {{
    width: 28px;
    height: 22px;
    border: 1.5px solid #0f2b48;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    background: #f8fafc;
  }}

  /* Listening Page Specifics */
  .audio-notice {{
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    padding: 5px 10px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 9.5px;
    color: #1e40af;
    margin-bottom: 8px;
    font-weight: 600;
  }}
  .audio-notice svg {{
    flex-shrink: 0;
  }}

  /* Writing Answer Sheet Styles */
  .writing-meta-card {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 7px 10px;
    margin-bottom: 8px;
  }}
  .writing-meta-grid {{
    display: grid;
    grid-template-columns: 1.3fr 1fr;
    gap: 8px;
  }}
  .points-checklist {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 5px 8px;
  }}
  .points-checklist-title {{
    font-size: 9px;
    font-weight: 800;
    color: #0f2b48;
    text-transform: uppercase;
    margin-bottom: 3px;
  }}
  .points-checklist ul {{
    margin-left: 14px;
    font-size: 9px;
    color: #334155;
    line-height: 1.3;
  }}

  .ruled-sheet {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 4px 10px;
    margin-bottom: 6px;
    position: relative;
  }}
  .ruled-line {{
    height: 26px;
    border-bottom: 1px solid #94a3b8;
    display: flex;
    align-items: flex-end;
    justify-content: flex-end;
    padding-bottom: 2px;
  }}
  .ruled-line-num {{
    font-size: 7.5px;
    color: #94a3b8;
    font-weight: 600;
    margin-right: -4px;
  }}

  /* Examiner Score Box on Writing / Speaking pages */
  .examiner-eval-box {{
    background: #f8fafc;
    border: 1.5px solid #0f2b48;
    border-radius: 4px;
    padding: 5px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 9.5px;
  }}
  .examiner-eval-title {{
    font-weight: 800;
    color: #0f2b48;
    text-transform: uppercase;
    font-size: 9px;
  }}
  .eval-cells {{
    display: flex;
    gap: 6px;
  }}
  .eval-cell {{
    border: 1px solid #cbd5e1;
    background: #ffffff;
    padding: 3px 8px;
    border-radius: 3px;
    text-align: center;
    min-width: 58px;
  }}
  .eval-cell-label {{
    font-size: 7.5px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
  }}
  .eval-cell-val {{
    font-size: 10px;
    font-weight: 800;
    color: #0f2b48;
    white-space: nowrap;
    margin-top: 1px;
  }}

  /* Oral Speaking Page */
  .oral-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 10px;
  }}
  .oral-card {{
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .oral-card-header {{
    font-size: 11.5px;
    font-weight: 800;
    color: #0f2b48;
    margin-bottom: 4px;
    padding-bottom: 3px;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
  }}
  .oral-topic {{
    font-size: 11px;
    font-weight: 800;
    color: #1e3a8a;
    background: #eff6ff;
    padding: 4px 6px;
    border-radius: 4px;
    margin-bottom: 6px;
    border-left: 3px solid #2563eb;
  }}
  .oral-card ul {{
    margin-left: 14px;
    font-size: 9.5px;
    color: #334155;
    line-height: 1.35;
  }}
  .oral-card li {{
    margin-bottom: 4px;
  }}
</style>
</head>
<body>

  <!-- ==================== SEITE 1: DECKBLATT ==================== -->
  <div class="exam-page">
    <div>
      <div class="cover-header">
        <div class="cover-inst-info">
          <div class="cover-inst-title">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</div>
          <div class="cover-inst-sub">GROUPE SCOLAIRE ILAS &bull; CENTRE OFFICIEL DE LANGUES</div>
          <div class="cover-inst-contact">Autorisation Ministérielle N° 22-200/2020 &bull; Deroua | Tél : 06 70 38 48 73 / 06 60 29 11 55</div>
        </div>
        <div>
          <img src="data:image/png;base64,{logo_b64}" class="cover-logo-img" alt="Logo ILAS">
        </div>
      </div>

      <div class="ger-bar" style="margin-top: 6px;">
        <div class="bar-black"></div>
        <div class="bar-red"></div>
        <div class="bar-gold"></div>
      </div>

      <div class="cover-hero">
        <div class="cover-level-badge">GEMEINSAMER EUROPÄISCHER REFERENZRAHMEN (GER / CEFR) &bull; NIVEAU B1</div>
        <h1>ZERTIFIKAT DEUTSCH B1</h1>
        <h2>OFFIZIELLES PRÜFUNGSHEFT FÜR TEILNEHMENDE</h2>
        <p>Kandidatenblätter zur standardisierten B1-Abschlussprüfung in der deutschen Sprache</p>
      </div>

      <!-- Kandidatenprofil -->
      <div class="candidate-card">
        <div class="candidate-card-header">
          <span>Kandidatendaten / Données du Candidat</span>
          <span style="color:#2563eb; font-weight:700;">Prüfungszentrum: ILAS Deroua</span>
        </div>
        <div class="candidate-grid">
          <div class="candidate-field">
            <span class="cand-label">Name, Vorname (Nom & Prénom):</span>
            <span class="cand-value cand-value-highlight">BENYAHIA, Anass</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Geburtsdatum (Date de Naissance):</span>
            <span class="cand-value">26.01.2007</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Personalausweis / CIN:</span>
            <span class="cand-value cand-value-highlight">WB226817</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Kandidatennummer (N° Candidat):</span>
            <span class="cand-value">ILAS-B1-2026-WB226817</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Prüfungsdatum (Date d'Examen):</span>
            <span class="cand-value">15. Oktober 2026</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Prüfungsart:</span>
            <span class="cand-value">Gesamtprüfung (B1 Komplett)</span>
          </div>
        </div>
      </div>

      <!-- Prüfungsübersicht & Punkteverteilung -->
      <table class="score-table">
        <thead>
          <tr>
            <th style="width: 32%;">Prüfungsmodul (Module)</th>
            <th class="center" style="width: 20%;">Dauer (Durée)</th>
            <th class="center" style="width: 22%;">Max. Punkte</th>
            <th class="center" style="width: 26%;">Erreichte Punkte</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Teil 1: Lesen</strong> (Compréhension écrite)</td>
            <td class="center">45 Min.</td>
            <td class="center">25 Punkte</td>
            <td class="center">_____ / 25</td>
          </tr>
          <tr>
            <td><strong>Teil 2: Hören</strong> (Compréhension orale)</td>
            <td class="center">30 Min.</td>
            <td class="center">25 Punkte</td>
            <td class="center">_____ / 25</td>
          </tr>
          <tr>
            <td><strong>Teil 3: Sprachbausteine</strong> (Grammatik & Wortschatz)</td>
            <td class="center">25 Min.</td>
            <td class="center">15 Punkte</td>
            <td class="center">_____ / 15</td>
          </tr>
          <tr>
            <td><strong>Teil 4: Schreiben</strong> (Schriftlicher Ausdruck)</td>
            <td class="center">50 Min.</td>
            <td class="center">20 Punkte</td>
            <td class="center">_____ / 20</td>
          </tr>
          <tr>
            <td><strong>Teil 5: Mündlicher Ausdruck</strong> (Sprechen)</td>
            <td class="center">15 Min.</td>
            <td class="center">15 Punkte</td>
            <td class="center">_____ / 15</td>
          </tr>
          <tr class="total-row">
            <td><strong>GESAMTERGEBNIS (Total)</strong></td>
            <td class="center"><strong>165 Min.</strong></td>
            <td class="center"><strong>100 Punkte</strong></td>
            <td class="center"><strong>_____ / 100</strong></td>
          </tr>
        </tbody>
      </table>

      <!-- Wichtige Hinweise & Unterschrift -->
      <div class="rules-grid">
        <div class="rules-box">
          <strong>Wichtige Hinweise für die Prüfungsteilnehmenden:</strong>
          <ul>
            <li><strong>Hilfsmittel:</strong> Wörterbücher, Mobiltelefone und Smartwatches sind strengstens verboten.</li>
            <li><strong>Schreibgerät:</strong> Bitte ausschließlich mit Kugelschreiber (blau oder schwarz) schreiben.</li>
            <li><strong>Lösungen:</strong> Markieren Sie Ihre Antworten sorgfältig und leserlich in den Feldern.</li>
            <li><strong>Bestehensgrenze:</strong> Mindestens <strong>60 Punkte (60 %)</strong> zum Bestehen der B1-Prüfung.</li>
          </ul>
        </div>
        <div class="sign-box">
          <div class="sign-box-label">Unterschrift des Teilnehmenden</div>
          <div class="sign-area"></div>
          <div style="font-size:7.5px; color:#64748b;">Hiermit bestätige ich die Richtigkeit der Angaben.</div>
        </div>
      </div>
    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Kandidat: <strong>ANASS BENYAHIA</strong> (CIN: WB226817)</span>
      <span class="footer-page">Seite 1 von 8</span>
    </div>
  </div>


  <!-- ==================== SEITE 2: TEIL 1 – LESEN (AUFGABE 1) ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">Zertifikat Deutsch B1 &bull; Abschlussprüfung</span>
        <span class="cand-tag">Kandidat: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>TEIL 1: LESEN</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Dauer: 45 Min. (für Teil 1 gesamt)</span>
          <span class="module-badge">Max. 25 Punkte</span>
        </div>
      </div>

      <div class="task-box">
        <div class="task-box-title">
          <span>AUFGABE 1: ZEITUNGSARTIKEL VERSTEHEN</span>
          <span style="color:#2563eb;">10 Punkte (je 2 Punkte pro Frage)</span>
        </div>
        <div class="task-box-desc">
          Lesen Sie den folgenden Artikel aus einer deutschen Wirtschaftszeitung und lösen Sie die Aufgaben 1 bis 5. Kreuzen Sie die richtige Lösung (a, b oder c) an.
        </div>
      </div>

      <!-- Zeitungsartikel -->
      <div class="article-card">
        <div class="article-headline">Die Vier-Tage-Woche: Zukunftsmodell oder Risiko für die Wirtschaft?</div>
        <p>
          In Deutschland diskutieren immer mehr Unternehmen über eine radikale Veränderung der Arbeitswelt: die Einführung der Vier-Tage-Woche bei vollem Lohnausgleich. Das bedeutet, dass Arbeitnehmer statt 40 Stunden an fünf Tagen nur noch 32 oder 35 Stunden an vier Tagen arbeiten, aber am Monatsende genau dasselbe Gehalt auf ihrem Konto haben. Was vor einigen Jahren noch wie eine unrealistische Forderung von Gewerkschaften klang, wird inzwischen von zahlreichen Handwerksbetrieben und IT-Firmen in der Praxis getestet.
        </p>
        <p>
          Ein Beispiel dafür ist der Sanitärbetrieb von Markus Weber in Köln. Vor zwei Jahren fand Weber kaum noch qualifizierte Fachkräfte. Junge Bewerber sagten ihm im Vorstellungsgespräch offen, dass ihnen Freizeit und Familie wichtiger seien als Überstunden. Daraufhin stellte Weber seinen Betrieb komplett um: Von Montag bis Donnerstag arbeiten seine 18 Angestellten jeweils neun Stunden, am Freitag bleibt die Firma geschlossen – außer für einen kleinen Notdienst, der im Wechsel organisiert wird.
        </p>
        <p>
          Das Ergebnis überraschte selbst den Chef. „Am Anfang hatte ich große Sorgen, dass wir unsere Aufträge nicht mehr rechtzeitig schaffen und Kunden verlieren“, gibt Weber zu. Doch das Gegenteil trat ein: Die Zahl der Krankheitstage sank im ersten Jahr um fast 40 Prozent. Zudem wurden interne Abläufe digitalisiert und unnötige Besprechungen gestrichen, sodass die Produktivität pro Stunde deutlich stieg. Auch das Personalproblem ist gelöst: Seit der Umstellung hat Weber über 50 Initiativbewerbungen erhalten.
        </p>
        <p>
          Trotz solcher Erfolgsgeschichten warnen Wirtschaftsexperten vor einer gesetzlichen Pflicht für alle Branchen. In Krankenhäusern, im öffentlichen Nahverkehr oder in der Gastronomie lasse sich die Arbeit an vier Tagen nicht einfach schneller erledigen. Wenn ein Busfahrer 20 Prozent weniger arbeite, fahre eben auch der Bus 20 Prozent seltener – es sei denn, man stelle neues Personal ein, das auf dem Arbeitsmarkt jedoch ohnehin fehle. Die Vier-Tage-Woche sei daher ein hervorragendes Instrument für einzelne Betriebe, aber keine Universallösung für das gesamte Land.
        </p>
      </div>

      <!-- Fragen 1 bis 5 -->
      <div class="question-item">
        <div class="question-text">1. Was versteht man unter der Vier-Tage-Woche „bei vollem Lohnausgleich“?</div>
        <div class="options-group">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Man arbeitet vier Tage lang jeweils zehn Stunden für dasselbe Gehalt.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Man arbeitet insgesamt weniger Stunden pro Woche bei gleichem Gehalt.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Man verzichtet auf 20 Prozent seines Gehalts, um am Freitag frei zu haben.</div>
        </div>
      </div>

      <div class="question-item">
        <div class="question-text">2. Warum hat Markus Weber die Vier-Tage-Woche in seiner Firma eingeführt?</div>
        <div class="options-group">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Weil seine Mitarbeiter ständig krank waren und zu viele Fehler machten.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Weil die Gewerkschaft seinen Betrieb zu diesem Schritt gezwungen hat.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Weil er große Schwierigkeiten hatte, gutes Personal zu finden.</div>
        </div>
      </div>

      <div class="question-item">
        <div class="question-text">3. Wie sieht die Arbeitszeit in Webers Betrieb heute aus?</div>
        <div class="options-group">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Alle Mitarbeiter haben jeden Freitag ohne Ausnahme frei.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Man arbeitet an vier Tagen länger, freitags gibt es nur einen Notdienst.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Die Mitarbeiter entscheiden selbst, an welchen vier Tagen sie arbeiten.</div>
        </div>
      </div>

      <div class="question-item">
        <div class="question-text">4. Welche Folge hatte die Umstellung für Webers Unternehmen?</div>
        <div class="options-group">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Die Mitarbeiter waren seltener krank und arbeiteten konzentrierter.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Einige Kunden wechselten zu anderen Firmen, weil freitags zu war.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Es gab plötzlich zu viele lange Besprechungen über die Digitalisierung.</div>
        </div>
      </div>

      <div class="question-item" style="margin-bottom:0;">
        <div class="question-text">5. Warum sind Experten gegen eine Vier-Tage-Woche in allen Berufen?</div>
        <div class="options-group">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Weil die meisten Arbeitnehmer in Deutschland lieber fünf Tage arbeiten.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Weil man in bestimmten Dienstleistungsberufen die Arbeitszeit nicht einfach durch schnellere Arbeit ausgleichen kann.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Weil die Digitalisierung in Krankenhäusern und Bussen zu teuer wäre.</div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Kandidat: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Teil 1: Lesen</span>
      <span class="footer-page">Seite 2 von 8</span>
    </div>
  </div>


  <!-- ==================== SEITE 3: TEIL 1 – LESEN (AUFGABE 2 & 3) ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">Zertifikat Deutsch B1 &bull; Abschlussprüfung</span>
        <span class="cand-tag">Kandidat: ANASS BENYAHIA (WB226817)</span>
      </div>

      <!-- Aufgabe 2 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>AUFGABE 2: LESERBRIEFE UND MEINUNGEN</span>
          <span style="color:#2563eb;">10 Punkte (je 2 Punkte pro Frage)</span>
        </div>
        <div class="task-box-desc">
          Lesen Sie die drei Meinungen zum Thema <strong>„Sollte das Zentrum von Großstädten komplett autofrei werden?“</strong> und beurteilen Sie die Aussagen 6–10: <strong>Richtig [ R ]</strong> oder <strong>Falsch [ F ]</strong>.
        </div>
      </div>

      <div class="opinions-container">
        <div class="opinion-card">
          <div class="opinion-card-header">Beitrag 1 – Sabine K. (44, Ladenbesitzerin)</div>
          „Wenn keine Autos mehr in die Innenstadt dürfen, bedeutet das das Ende für viele kleine Geschäfte. Meine Kunden kommen oft aus den Vororten, um größere Einkäufe zu machen. Niemand möchte schwere Taschen kilometerweit mit der Straßenbahn transportieren. Bevor man Autos verbietet, müsste der Staat erst einmal kostenlose Parkhäuser am Stadtrand bauen und die Ticketpreise für Busse halbieren.“
        </div>
        <div class="opinion-card">
          <div class="opinion-card-header">Beitrag 2 – Lukas M. (29, Architekt)</div>
          „Ich lebe mitten im Zentrum und halte den Lärm und die Abgase kaum noch aus. In Städten wie Kopenhagen oder Amsterdam sieht man doch, dass autofreie Zonen die Lebensqualität enorm steigern! Dort sitzen die Menschen in Straßencafés, wo früher Blechlawinen rollten, und die Umsätze der Geschäfte sind sogar gestiegen, weil Fußgänger und Radfahrer viel öfter spontan stehen bleiben als Autofahrer.“
        </div>
        <div class="opinion-card">
          <div class="opinion-card-header">Beitrag 3 – Herbert W. (68, Rentner)</div>
          „Die Diskussion ist mir zu extrem. Natürlich brauchen wir weniger Verkehr im Zentrum, aber ein komplettes Verbot schließt ältere oder gehbehinderte Menschen aus, die auf ihr Fahrzeug angewiesen sind. Eine City-Maut, also eine Gebühr für alle, die ohne wichtigen Grund in die Stadt fahren, wäre viel vernünftiger als ein generelles Verbot. Handwerker, Lieferanten und Anwohner sollten natürlich weiterhin kostenlos einfahren dürfen.“
        </div>
      </div>

      <table class="rf-table">
        <thead>
          <tr>
            <th>Aussage zum Text</th>
            <th class="rf-check-cell">Richtig</th>
            <th class="rf-check-cell">Falsch</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>6.</strong> Sabine K. befürchtet, dass Kunden aus der Umgebung ohne Auto nicht mehr bei ihr einkaufen werden.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>7.</strong> Sabine K. ist der Meinung, dass die öffentlichen Verkehrsmittel heute schon günstig genug sind.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>8.</strong> Lukas M. glaubt, dass Geschäfte in autofreien Innenstädten weniger Geld verdienen als vorher.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>9.</strong> Herbert W. setzt sich dafür ein, dass kranke und ältere Menschen weiterhin mit dem Auto ins Zentrum fahren können.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>10.</strong> Herbert W. schlägt vor, dass auch Handwerker und Anwohner eine Gebühr (City-Maut) bezahlen müssen.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
        </tbody>
      </table>

      <!-- Aufgabe 3 -->
      <div class="task-box" style="margin-top: 6px;">
        <div class="task-box-title">
          <span>AUFGABE 3: BEDINGUNGEN UND ANZEIGEN ZUORDNEN</span>
          <span style="color:#2563eb;">5 Punkte (je 1 Punkt pro Frage)</span>
        </div>
        <div class="task-box-desc">
          Welches Kursangebot (A–G) passt zu welcher Person (11–15)? Für eine Person gibt es <strong>KEIN</strong> passendes Angebot (schreiben Sie dann „<strong>0</strong>“).
        </div>
      </div>

      <div class="matching-container">
        <!-- Situationen 11-15 -->
        <div>
          <div style="font-size:9.5px; font-weight:800; color:#0f2b48; margin-bottom:3px;">Personen & Situationen:</div>
          
          <div class="situation-item">
            <div class="situation-text"><strong>11. Frau Yilmaz (Buchhalterin):</strong> Möchte lernen, wie man komplizierte Tabellen und Berechnungen am PC erstellt. Kann nur am Wochenende.</div>
            <div class="match-box">[ &nbsp; ]</div>
          </div>

          <div class="situation-item">
            <div class="situation-text"><strong>12. Herr Bergmann:</strong> Wird Abteilungsleiter. Hat Angst davor, vor vielen Menschen frei zu sprechen, und möchte seine Stimme trainieren.</div>
            <div class="match-box">[ &nbsp; ]</div>
          </div>

          <div class="situation-item">
            <div class="situation-text"><strong>13. Leonie (19):</strong> Sucht einen vierwöchigen Intensivkurs in Wirtschaftsenglisch am Vormittag, um sich auf ihr Studium vorzubereiten.</div>
            <div class="match-box">[ &nbsp; ]</div>
          </div>

          <div class="situation-item">
            <div class="situation-text"><strong>14. Herr Kovac:</strong> Leitet ein Team, in dem es oft Streit gibt. Möchte lernen, wie man Probleme zwischen Mitarbeitern professionell löst.</div>
            <div class="match-box">[ &nbsp; ]</div>
          </div>

          <div class="situation-item" style="margin-bottom:0;">
            <div class="situation-text"><strong>15. Frau Lindner:</strong> Arbeitet im Homeoffice, hat Rückenschmerzen und sucht einen Kurs am Dienstag- oder Donnerstagabend zum Entspannen.</div>
            <div class="match-box">[ &nbsp; ]</div>
          </div>
        </div>

        <!-- Kursangebote A-G -->
        <div class="course-list">
          <div style="font-size:9.5px; font-weight:800; color:#0f2b48; margin-bottom:1px;">Kursangebote:</div>
          <div class="course-item"><span class="course-letter">A</span> <span class="course-title">Souverän auftreten – Rhetorik & Präsentation:</span> Stimmtraining, Abbau von Lampenfieber. 3x mittwochs, 18:00–21:00 Uhr.</div>
          <div class="course-item"><span class="course-letter">B</span> <span class="course-title">Business English – Evening Class (B2):</span> Verhandlungssicheres Englisch. Mo & Mi von 19:00 bis 20:30 Uhr über 12 Wochen.</div>
          <div class="course-item"><span class="course-letter">C</span> <span class="course-title">MS Excel für Fortgeschrittene:</span> Formeln, Pivot-Tabellen & Analyse. Intensiv-Wochenende: Sa & So, 09:00–16:30 Uhr.</div>
          <div class="course-item"><span class="course-letter">D</span> <span class="course-title">Konfliktmanagement im Berufsalltag:</span> Konstruktiv vermitteln bei Streit im Team. Freitag, 09:00–17:00 Uhr.</div>
          <div class="course-item"><span class="course-letter">E</span> <span class="course-title">Fit & Schmerzfrei am Schreibtisch:</span> Rückenübungen & Entspannung. Jeden Dienstag, 18:30–20:00 Uhr.</div>
          <div class="course-item"><span class="course-letter">F</span> <span class="course-title">IT-Sicherheit & Datenschutz im Homeoffice:</span> Technischer Workshop für Admins. Donnerstag, 14:00–18:00 Uhr.</div>
          <div class="course-item"><span class="course-letter">G</span> <span class="course-title">Buchhaltung für Existenzgründer:</span> Steuern und Rechnungen. Samstag, 10:00–15:00 Uhr.</div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Kandidat: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Teil 1: Lesen</span>
      <span class="footer-page">Seite 3 von 8</span>
    </div>
  </div>


  <!-- ==================== SEITE 4: TEIL 2 – HÖREN ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">Zertifikat Deutsch B1 &bull; Abschlussprüfung</span>
        <span class="cand-tag">Kandidat: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>TEIL 2: HÖREN (LISTENING COMPREHENSION)</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Dauer: 30 Min.</span>
          <span class="module-badge">Max. 25 Punkte</span>
        </div>
      </div>

      <div class="audio-notice">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
        </svg>
        <span>Hinweis: Die Audio-Texte werden von den Prüfenden vorgelesen oder abgespielt. Markieren Sie Ihre Antworten direkt während des Hörens.</span>
      </div>

      <!-- Aufgabe 1 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>AUFGABE 1: KURZE ANSAGEN UND NACHRICHTEN (1x Hören)</span>
          <span style="color:#2563eb;">10 Punkte (je 2 Punkte)</span>
        </div>
        <div class="task-box-desc">
          Sie hören fünf kurze Ansagen am Telefon oder im Radio. Sie hören jeden Text <strong>EINMAL</strong>. Wählen Sie die richtige Lösung (a, b oder c).
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 6px;">
        <div class="question-item">
          <div class="question-text">16. Was soll Frau Schneider tun, bevor sie morgen kommt?</div>
          <div class="options-group">
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Den Termin telefonisch verschieben.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Neue Gesundheitskarte & Medikamentenplan mitbringen.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Eine halbe Stunde später kommen als geplant.</div>
          </div>
        </div>

        <div class="question-item">
          <div class="question-text">17. Warum fährt die RB 42 nicht bis zum Hauptbahnhof?</div>
          <div class="options-group">
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Reparaturarbeiten an einer Brücke nach Unwetter.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Wegen eines Streiks des Bahnpersonals in der Stadt.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Wegen eines defekten Zuges vor dem Bahnhof.</div>
          </div>
        </div>

        <div class="question-item">
          <div class="question-text">18. Was wird für das Wochenende im Süden vorhergesagt?</div>
          <div class="options-group">
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Durchgehend sonniges Wetter mit über 25 Grad.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Starker Schneefall bis in tiefe Lagen.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Samstag warm, ab Sonntagnachmittag Gewitter/Kälte.</div>
          </div>
        </div>

        <div class="question-item">
          <div class="question-text">19. Warum ruft der Mitarbeiter bei Herrn Albers an?</div>
          <div class="options-group">
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Tisch/Stühle können schon diesen Freitag geliefert werden.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Die Stühle haben einen Transportschaden.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Herr Albers muss noch die Restsumme überweisen.</div>
          </div>
        </div>
      </div>

      <div class="question-item" style="margin-bottom: 6px;">
        <div class="question-text">20. Was müssen Besucher beachten, die am Sonntag das Stadtmuseum besuchen wollen?</div>
        <div class="options-group-horizontal">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Freier Eintritt für alle Besucher.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Wegen des Marathons kein Zugang per Auto (nur U-Bahn).</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Sonderausstellung schließt um 14:00 Uhr.</div>
        </div>
      </div>

      <!-- Aufgabe 2 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>AUFGABE 2: RADIO-INTERVIEW (Ausbildung oder Studium? – 2x Hören)</span>
          <span style="color:#2563eb;">10 Punkte (je 2 Punkte)</span>
        </div>
        <div class="task-box-desc">
          Interview mit Berufsberater Thomas Richter. Sie hören das Gespräch <strong>ZWEIMAL</strong>. Markieren Sie: <strong>Richtig [ R ]</strong> oder <strong>Falsch [ F ]</strong>.
        </div>
      </div>

      <table class="rf-table" style="margin-bottom: 6px;">
        <thead>
          <tr>
            <th>Aussage zum Radio-Interview</th>
            <th class="rf-check-cell">Richtig</th>
            <th class="rf-check-cell">Falsch</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>21.</strong> Herr Richter sagt, dass heute fast 80 Prozent aller Jugendlichen nach der Schule studieren wollen.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>22.</strong> Viele Studenten brechen ihr Studium ab, weil sie falsche Vorstellungen von den theoretischen Anforderungen hatten.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>23.</strong> Nach einer Berufsausbildung im Handwerk verdient man laut Herrn Richter immer deutlich weniger als Akademiker.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>24.</strong> Ein „duales Studium“ verbindet die praktische Arbeit in einem Betrieb mit dem Studium an einer Hochschule.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>25.</strong> Herr Richter rät Eltern dazu, ihre Kinder unbedingt in die Richtung zu drängen, die das meiste Prestige bringt.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
        </tbody>
      </table>

      <!-- Aufgabe 3 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>AUFGABE 3: ALLTAGSGESPRÄCH (Planung des Betriebsausflugs – 1x Hören)</span>
          <span style="color:#2563eb;">5 Punkte (je 1 Punkt)</span>
        </div>
        <div class="task-box-desc">
          Gespräch zwischen Anna und David. Sie hören das Gespräch <strong>EINMAL</strong>. Wer sagt was? Kreuzen Sie an: <strong>Anna [ A ]</strong>, <strong>David [ D ]</strong> oder <strong>Beide [ B ]</strong>.
        </div>
      </div>

      <table class="rf-table">
        <thead>
          <tr>
            <th>Aussage im Gespräch</th>
            <th class="rf-check-cell">Anna [A]</th>
            <th class="rf-check-cell">David [D]</th>
            <th class="rf-check-cell">Beide [B]</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>26.</strong> Die Wanderung im letzten Jahr war wegen des schlechten Wetters keine gute Erfahrung.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>27.</strong> Ein Kochkurs für das ganze Team fördert die Zusammenarbeit besser als ein einfacher Restaurantbesuch.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>28.</strong> Das Budget von 50 Euro pro Person reicht für eine Schifffahrt inklusive Abendessen nicht aus.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>29.</strong> Der Ausflug sollte lieber an einem Freitag während der Arbeitszeit stattfinden und nicht am Samstag.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>30.</strong> Man sollte der Chefin zwei verschiedene Vorschläge machen, damit die Mitarbeiter abstimmen können.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
        </tbody>
      </table>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Kandidat: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Teil 2: Hören</span>
      <span class="footer-page">Seite 4 von 8</span>
    </div>
  </div>


  <!-- ==================== SEITE 5: TEIL 3 – SPRACHBAUSTEINE ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">Zertifikat Deutsch B1 &bull; Abschlussprüfung</span>
        <span class="cand-tag">Kandidat: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>TEIL 3: SPRACHBAUSTEINE (GRAMMATIK & WORTSCHATZ)</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Dauer: 25 Min.</span>
          <span class="module-badge">Max. 15 Punkte</span>
        </div>
      </div>

      <!-- Aufgabe 1 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>AUFGABE 1: LÜCKENTEXT IM FORMELLEN KONTEXT</span>
          <span style="color:#2563eb;">7,5 Punkte (je 0,75 Punkte pro Lücke)</span>
        </div>
        <div class="task-box-desc">
          Lesen Sie das folgende Schreiben und wählen Sie für jede Lücke (31–40) das grammatikalisch passende Wort.
        </div>
      </div>

      <div class="article-card" style="margin-bottom: 6px; padding: 7px 10px;">
        <p style="font-size:9.3px; line-height: 1.4;">
          <strong>Sehr geehrte Damen und Herren,</strong><br>
          hiermit möchte ich Ihnen einen Schadensfall melden, <strong>(31)</strong> sich am vergangenen Dienstag in meiner Mietwohnung ereignet hat. Als ich gegen 18:00 Uhr von der Arbeit nach Hause kam, musste ich feststellen, <strong>(32)</strong> in der Küche Wasser aus dem Geschirrspüler ausgelaufen war. <strong>(33)</strong> ich den Haupthahn sofort zugedreht habe, war das Wasser bereits unter <strong>(34)</strong> neuen Parkettboden im Flur geflossen. Das Parkett, <strong>(35)</strong> erst vor zwei Jahren verlegt <strong>(36)</strong>, hat sich durch die Feuchtigkeit stark verzogen und muss nun von einer Fachfirma ausgetauscht werden. Ich habe noch am selben Abend meinen Vermieter informiert, <strong>(37)</strong> sich den Schaden anzusehen. Er riet mir, mich umgehend mit <strong>(38)</strong> Versicherung in Verbindung zu setzen. <strong>(39)</strong> es Ihnen möglich, noch in dieser Woche einen Gutachter vorbeizuschicken? Den Kostenvoranschlag des Handwerkers sende ich Ihnen zu, <strong>(40)</strong> ich ihn erhalten habe.<br>
          <strong>Mit freundlichen Grüßen, Martin Brenner</strong>
        </p>
      </div>

      <!-- Multiple-Choice Grid für 31-40 -->
      <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; margin-bottom: 8px;">
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Lücke 31:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) den</div>
            <div>[ ] b) der</div>
            <div>[ ] c) dem</div>
            <div>[ ] d) dessen</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Lücke 32:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) ob</div>
            <div>[ ] b) weil</div>
            <div>[ ] c) dass</div>
            <div>[ ] d) wenn</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Lücke 33:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) Trotzdem</div>
            <div>[ ] b) Obwohl</div>
            <div>[ ] c) Wegen</div>
            <div>[ ] d) Während</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Lücke 34:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) dem</div>
            <div>[ ] b) der</div>
            <div>[ ] c) den</div>
            <div>[ ] d) des</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Lücke 35:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) das</div>
            <div>[ ] b) was</div>
            <div>[ ] c) dem</div>
            <div>[ ] d) welches</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Lücke 36:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) wurde</div>
            <div>[ ] b) hat</div>
            <div>[ ] c) ist</div>
            <div>[ ] d) geworden</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Lücke 37:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) damit</div>
            <div>[ ] b) um</div>
            <div>[ ] c) für</div>
            <div>[ ] d) ohne</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Lücke 38:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) meine</div>
            <div>[ ] b) meiner</div>
            <div>[ ] c) meinen</div>
            <div>[ ] d) meines</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Lücke 39:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) Würde</div>
            <div>[ ] b) Hätte</div>
            <div>[ ] c) Wäre</div>
            <div>[ ] d) Könnte</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Lücke 40:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) sobald</div>
            <div>[ ] b) seitdem</div>
            <div>[ ] c) bevor</div>
            <div>[ ] d) bis</div>
          </div>
        </div>
      </div>

      <!-- Aufgabe 2 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>AUFGABE 2: KOMPLEXE B1-STRUKTUREN</span>
          <span style="color:#2563eb;">7,5 Punkte (je 0,75 Punkte pro Frage)</span>
        </div>
        <div class="task-box-desc">
          Wählen Sie bei den Sätzen 41 bis 50 die jeweils grammatikalisch und semantisch richtige Ergänzung (a, b, c oder d).
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>41.</strong> Die Frau, _______ Tasche gestern im Café gestohlen wurde, rief die Polizei.<br>
          <span style="color:#475569;">[ ] a) die &nbsp; [ ] b) der &nbsp; [ ] c) deren &nbsp; [ ] d) dessen</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>42.</strong> _______ nach dem Weg zu fragen, ist mein Bruder stundenlang falsch gefahren.<br>
          <span style="color:#475569;">[ ] a) Ohne &nbsp; [ ] b) Anstatt &nbsp; [ ] c) Um &nbsp; [ ] d) Trotz</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>43.</strong> In unserer Firma _______ alle Rechnungen digital geprüft werden.<br>
          <span style="color:#475569;">[ ] a) werden &nbsp; [ ] b) sind &nbsp; [ ] c) müssen &nbsp; [ ] d) haben</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>44.</strong> Hast du schon mit dem neuen _______ aus der Marketingabteilung gesprochen?<br>
          <span style="color:#475569;">[ ] a) Kollege &nbsp; [ ] b) Kollegen &nbsp; [ ] c) Kollegens &nbsp; [ ] d) Kollegem</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>45.</strong> _______ mehr man eine Sprache spricht, _______ schneller verliert man die Angst.<br>
          <span style="color:#475569;">[ ] a) Sowohl/als &nbsp; [ ] b) Entweder/oder &nbsp; [ ] c) Je/desto &nbsp; [ ] d) Nicht nur/sondern</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>46.</strong> Wenn ich an deiner Stelle _______, _______ ich dieses Angebot nicht annehmen.<br>
          <span style="color:#475569;">[ ] a) bin/werde &nbsp; [ ] b) wäre/würde &nbsp; [ ] c) hätte/könnte &nbsp; [ ] d) wäre/hätte</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>47.</strong> Wir haben uns sehr _______ Ihr Schreiben gefreut und hoffen _______ eine gute Zusammenarbeit.<br>
          <span style="color:#475569;">[ ] a) auf/über &nbsp; [ ] b) für/an &nbsp; [ ] c) über/auf &nbsp; [ ] d) mit/für</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>48.</strong> Nachdem der Vertrag von beiden Seiten unterschrieben _______, begann das Projekt.<br>
          <span style="color:#475569;">[ ] a) worden war &nbsp; [ ] b) wurde &nbsp; [ ] c) geworden ist &nbsp; [ ] d) sein würde</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>49.</strong> Während _______ gesamten Fluges nach Tokio mussten alle angeschnallt bleiben.<br>
          <span style="color:#475569;">[ ] a) dem &nbsp; [ ] b) den &nbsp; [ ] c) des &nbsp; [ ] d) der</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>50.</strong> Es ist nicht mehr nötig, das Formular persönlich _______; es geht auch online.<br>
          <span style="color:#475569;">[ ] a) abgeben &nbsp; [ ] b) zu abgeben &nbsp; [ ] c) abzugeben &nbsp; [ ] d) abgegeben</span>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Kandidat: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Teil 3: Sprachbausteine</span>
      <span class="footer-page">Seite 5 von 8</span>
    </div>
  </div>


  <!-- ==================== SEITE 6: TEIL 4 – SCHREIBEN (AUFGABE 1) ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">Zertifikat Deutsch B1 &bull; Abschlussprüfung</span>
        <span class="cand-tag">Kandidat: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>TEIL 4: SCHREIBEN (SCHRIFTLICHER AUSDRUCK)</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Gesamtdauer: 50 Min.</span>
          <span class="module-badge">Max. 20 Punkte (2 x 10 Pkt.)</span>
        </div>
      </div>

      <!-- Aufgabe 1 Box -->
      <div class="writing-meta-card">
        <div class="task-box-title" style="margin-bottom: 4px;">
          <span>AUFGABE 1: FORMELLE BESCHWERDE-E-MAIL</span>
          <span style="color:#2563eb;">10 Punkte &bull; Richtzeit: ca. 25 Min. &bull; Umfang: ca. 80–100 Wörter</span>
        </div>
        <div class="writing-meta-grid">
          <div style="font-size:9.2px; line-height: 1.35; color:#1e293b;">
            <strong>Situation:</strong> Sie haben vor zwei Wochen bei dem Online-Händler <em>„Technik-Welt GmbH“</em> eine Kaffeemaschine (Modell <em>„Barista Pro“</em>, Bestellnummer: <strong>TW-9941</strong>) für <strong>249 Euro</strong> gekauft. Nach drei Tagen ist das Gerät kaputtgegangen (es heizt das Wasser nicht mehr auf). Auf Ihre erste E-Mail von letzter Woche haben Sie keine Antwort erhalten.<br>
            Schreiben Sie eine sachliche, formelle Beschwerde-E-Mail unter Berücksichtigung aller 4 Leitpunkte.
          </div>
          <div class="points-checklist">
            <div class="points-checklist-title">Zu behandelnde Leitpunkte:</div>
            <ul>
              <li><strong>1. Grund des Schreibens</strong> (Kaufdatum, Modell, Best.-Nr.)</li>
              <li><strong>2. Mängelbeschreibung</strong> & unbeantwortete erste Mail</li>
              <li><strong>3. Forderung:</strong> Ersatzgerät oder Kaufpreiserstattung</li>
              <li><strong>4. Fristsetzung</strong> (z.B. 7 Tage) & rechtliche Schritte</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Liniertes Antwortblatt (13 Zeilen) -->
      <div class="ruled-sheet">
        <div style="font-size:8.5px; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:2px;">
          Antwortbogen Aufgabe 1 (Formelle Beschwerde-E-Mail):
        </div>
        <div class="ruled-line"><span class="ruled-line-num">1</span></div>
        <div class="ruled-line"><span class="ruled-line-num">2</span></div>
        <div class="ruled-line"><span class="ruled-line-num">3</span></div>
        <div class="ruled-line"><span class="ruled-line-num">4</span></div>
        <div class="ruled-line"><span class="ruled-line-num">5</span></div>
        <div class="ruled-line"><span class="ruled-line-num">6</span></div>
        <div class="ruled-line"><span class="ruled-line-num">7</span></div>
        <div class="ruled-line"><span class="ruled-line-num">8</span></div>
        <div class="ruled-line"><span class="ruled-line-num">9</span></div>
        <div class="ruled-line"><span class="ruled-line-num">10</span></div>
        <div class="ruled-line"><span class="ruled-line-num">11</span></div>
        <div class="ruled-line"><span class="ruled-line-num">12</span></div>
        <div class="ruled-line"><span class="ruled-line-num">13</span></div>
      </div>

      <!-- Bewertungsraster für Prüfende -->
      <div class="examiner-eval-box">
        <div class="examiner-eval-title">NUR FÜR DIE PRÜFENDEN (BEWERTUNG AUFGABE 1):</div>
        <div class="eval-cells">
          <div class="eval-cell">
            <div class="eval-cell-label">Leitpunkte (4P)</div>
            <div class="eval-cell-val">___ / 4</div>
          </div>
          <div class="eval-cell">
            <div class="eval-cell-label">Kohärenz & Stil (3P)</div>
            <div class="eval-cell-val">___ / 3</div>
          </div>
          <div class="eval-cell">
            <div class="eval-cell-label">Grammatik & Wortschatz (3P)</div>
            <div class="eval-cell-val">___ / 3</div>
          </div>
          <div class="eval-cell" style="background:#eff6ff; border-color:#2563eb;">
            <div class="eval-cell-label" style="color:#1e3a8a;">Gesamt A1</div>
            <div class="eval-cell-val" style="color:#1e3a8a;">___ / 10</div>
          </div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Kandidat: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Teil 4: Schreiben (Aufgabe 1)</span>
      <span class="footer-page">Seite 6 von 8</span>
    </div>
  </div>


  <!-- ==================== SEITE 7: TEIL 4 – SCHREIBEN (AUFGABE 2) ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">Zertifikat Deutsch B1 &bull; Abschlussprüfung</span>
        <span class="cand-tag">Kandidat: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>TEIL 4: SCHREIBEN &bull; AUFGABE 2</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Richtzeit: ca. 25 Min.</span>
          <span class="module-badge">Max. 10 Punkte</span>
        </div>
      </div>

      <!-- Aufgabe 2 Box -->
      <div class="writing-meta-card">
        <div class="task-box-title" style="margin-bottom: 4px;">
          <span>AUFGABE 2: STELLUNGNAHME / DISKUSSIONSBEITRAG IM FORUM</span>
          <span style="color:#2563eb;">10 Punkte &bull; Umfang: ca. 100–120 Wörter</span>
        </div>
        <div class="writing-meta-grid">
          <div style="font-size:9.2px; line-height: 1.35; color:#1e293b;">
            <strong>Situation:</strong> Sie lesen in einer Zeitschrift einen Artikel zum Thema <em>„Homeoffice oder Präsenzarbeit im Büro?“</em>. Der Autor behauptet provokant, dass Mitarbeiter im Homeoffice weniger leisten, fauler seien und der Teamgeist dadurch vollständig verloren gehe.<br>
            Schreiben Sie einen sachlichen, strukturierten Diskussionsbeitrag für das Leserforum.
          </div>
          <div class="points-checklist">
            <div class="points-checklist-title">Zu behandelnde Leitpunkte:</div>
            <ul>
              <li><strong>Eigene Meinung:</strong> Nehmen Sie Stellung zur Aussage des Autors.</li>
              <li><strong>Argumentation:</strong> Nennen Sie mindestens <strong>zwei Vorteile</strong> und <strong>zwei Nachteile</strong> von Homeoffice.</li>
              <li><strong>Lösungsansatz:</strong> Schlagen Sie einen <strong>fairen Kompromiss</strong> für Firmen und Angestellte vor.</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Liniertes Antwortblatt (13 Zeilen) -->
      <div class="ruled-sheet">
        <div style="font-size:8.5px; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:2px;">
          Antwortbogen Aufgabe 2 (Forumsbeitrag / Stellungnahme):
        </div>
        <div class="ruled-line"><span class="ruled-line-num">1</span></div>
        <div class="ruled-line"><span class="ruled-line-num">2</span></div>
        <div class="ruled-line"><span class="ruled-line-num">3</span></div>
        <div class="ruled-line"><span class="ruled-line-num">4</span></div>
        <div class="ruled-line"><span class="ruled-line-num">5</span></div>
        <div class="ruled-line"><span class="ruled-line-num">6</span></div>
        <div class="ruled-line"><span class="ruled-line-num">7</span></div>
        <div class="ruled-line"><span class="ruled-line-num">8</span></div>
        <div class="ruled-line"><span class="ruled-line-num">9</span></div>
        <div class="ruled-line"><span class="ruled-line-num">10</span></div>
        <div class="ruled-line"><span class="ruled-line-num">11</span></div>
        <div class="ruled-line"><span class="ruled-line-num">12</span></div>
        <div class="ruled-line"><span class="ruled-line-num">13</span></div>
      </div>

      <!-- Bewertungsraster für Prüfende -->
      <div class="examiner-eval-box">
        <div class="examiner-eval-title">NUR FÜR DIE PRÜFENDEN (BEWERTUNG AUFGABE 2):</div>
        <div class="eval-cells">
          <div class="eval-cell">
            <div class="eval-cell-label">Meinung & Argumente (4P)</div>
            <div class="eval-cell-val">___ / 4</div>
          </div>
          <div class="eval-cell">
            <div class="eval-cell-label">Diskursmittel / Konnektoren (3P)</div>
            <div class="eval-cell-val">___ / 3</div>
          </div>
          <div class="eval-cell">
            <div class="eval-cell-label">Wortschatz & Richtigkeit (3P)</div>
            <div class="eval-cell-val">___ / 3</div>
          </div>
          <div class="eval-cell" style="background:#eff6ff; border-color:#2563eb;">
            <div class="eval-cell-label" style="color:#1e3a8a;">Gesamt A2</div>
            <div class="eval-cell-val" style="color:#1e3a8a;">___ / 10</div>
          </div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Kandidat: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Teil 4: Schreiben (Aufgabe 2)</span>
      <span class="footer-page">Seite 7 von 8</span>
    </div>
  </div>


  <!-- ==================== SEITE 8: TEIL 5 – MÜNDLICHER AUSDRUCK ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">Zertifikat Deutsch B1 &bull; Abschlussprüfung</span>
        <span class="cand-tag">Kandidat: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>TEIL 5: MÜNDLICHER AUSDRUCK (SPRECHEN)</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Vorbereitung: 10 Min.</span>
          <span class="module-badge">Prüfungsdauer: ca. 15 Min.</span>
          <span class="module-badge">Max. 15 Punkte</span>
        </div>
      </div>

      <div class="task-box">
        <div class="task-box-title">
          <span>HINWEISE ZUR MÜNDLICHEN PRÜFUNG</span>
          <span style="color:#2563eb;">Paarprüfung oder Einzelprüfung mit Prüfenden</span>
        </div>
        <div class="task-box-desc">
          Die Prüfung besteht aus zwei Teilen. Während der 10-minütigen Vorbereitungszeit dürfen Sie sich kurze Notizen auf einem separaten Blatt machen. Sprechen Sie während der Prüfung möglichst frei und reagieren Sie auf Fragen.
        </div>
      </div>

      <div class="oral-grid">
        <!-- Teil 5A -->
        <div class="oral-card">
          <div>
            <div class="oral-card-header">
              <span>TEIL 5A: PRÄSENTATION</span>
              <span style="color:#2563eb;">7,5 Punkte (ca. 4–5 Min.)</span>
            </div>
            <div class="oral-topic">Thema: „Soziale Netzwerke (Instagram, TikTok, LinkedIn): Fluch oder Segen?“</div>
            <div style="font-size:9px; font-weight:700; color:#0f2b48; margin-bottom:3px;">Strukturieren Sie Ihre Präsentation nach folgenden Schritten:</div>
            <ul>
              <li><strong>1. Einleitung:</strong> Stellen Sie das Thema vor und berichten Sie über Ihre persönlichen Erfahrungen mit Social Media.</li>
              <li><strong>2. Situation im Heimatland:</strong> Welche Rolle spielen soziale Netzwerke in Marokko? Wie nutzen Jugendliche und Betriebe sie?</li>
              <li><strong>3. Vor- und Nachteile:</strong> Nennen Sie jeweils 2 konkrete Vor- und Nachteile (z.B. Vernetzung vs. Zeitverschwendung/Datenschutz).</li>
              <li><strong>4. Fazit & eigene Meinung:</strong> Fassen Sie Ihren Standpunkt zusammen und beantworten Sie Fragen der Prüfenden.</li>
            </ul>
          </div>
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:4px 6px; font-size:8px; color:#64748b;">
            Tipp: Benutzen Sie Rede- und Strukturierungsmittel (<em>„Einleitend möchte ich...“, „Einerseits..., andererseits...“, „Meiner Ansicht nach...“</em>).
          </div>
        </div>

        <!-- Teil 5B -->
        <div class="oral-card">
          <div>
            <div class="oral-card-header">
              <span>TEIL 5B: GEMEINSAM EIN PROBLEM LÖSEN</span>
              <span style="color:#2563eb;">7,5 Punkte (ca. 6 Min.)</span>
            </div>
            <div class="oral-topic">Situation: Überraschungs-Wochenende für eine Freundin zum Studienabschluss</div>
            <div style="font-size:9px; font-weight:700; color:#0f2b48; margin-bottom:3px;">Planen Sie zusammen mit Ihrer Partnerin / Ihrem Partner (Prüferin):</div>
            <ul>
              <li><strong>Reiseziel & Unterkunft:</strong> Camping am Meer, Berghütte im Atlas oder Städtetrip ins Hotel?</li>
              <li><strong>Anreise & Mobilität:</strong> Zugfahrt, Mietwagen buchen oder private Fahrgemeinschaften bilden?</li>
              <li><strong>Finanzierung:</strong> Welches Budget pro Person ist für 15 Freunde realistisch? Wer übernimmt die Kosten der Absolventin?</li>
              <li><strong>Aufgabenverteilung:</strong> Wer bucht die Tickets, wer kauft Verpflegung ein und wer lenkt die Freundin bis zur Überraschung ab?</li>
            </ul>
          </div>
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:4px 6px; font-size:8px; color:#64748b;">
            Tipp: Machen Sie Vorschläge, gehen Sie auf Gegenargumente ein und finden Sie einen überzeugenden Kompromiss.
          </div>
        </div>
      </div>

      <!-- Offizielles Prüferprotokoll für Mündlich -->
      <div style="background:#ffffff; border:1.5px solid #0f2b48; border-radius:6px; padding:8px 12px; margin-top:2px;">
        <div style="font-size:10px; font-weight:800; color:#0f2b48; text-transform:uppercase; margin-bottom:5px; border-bottom:1px solid #e2e8f0; padding-bottom:3px; display:flex; justify-content:space-between;">
          <span>OFFIZIELLES PRÜFUNGSPROTOKOLL &ndash; MÜNDLICHER AUSDRUCK</span>
          <span style="color:#2563eb;">Kandidat: ANASS BENYAHIA</span>
        </div>
        <table class="score-table" style="margin-bottom:6px; font-size:9px;">
          <thead>
            <tr>
              <th>Bewertungskriterium</th>
              <th class="center" style="width:25%;">Teil 5A (Präsentation)</th>
              <th class="center" style="width:25%;">Teil 5B (Gespräch)</th>
              <th class="center" style="width:20%;">Gesamteindruck</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>1. Erfüllung der Aufgabenstellung & Kohärenz</td>
              <td class="center">_____ / 2,5 P.</td>
              <td class="center">_____ / 2,5 P.</td>
              <td class="center">_____ / 5,0 P.</td>
            </tr>
            <tr>
              <td>2. Flüssigkeit, Aussprache & Intonation</td>
              <td class="center">_____ / 2,5 P.</td>
              <td class="center">_____ / 2,5 P.</td>
              <td class="center">_____ / 5,0 P.</td>
            </tr>
            <tr>
              <td>3. Wortschatz & grammatische Richtigkeit (B1)</td>
              <td class="center">_____ / 2,5 P.</td>
              <td class="center">_____ / 2,5 P.</td>
              <td class="center">_____ / 5,0 P.</td>
            </tr>
            <tr class="total-row">
              <td><strong>ERGEBNIS TEIL 5 (MÜNDLICH GESAMT)</strong></td>
              <td class="center"><strong>_____ / 7,5 P.</strong></td>
              <td class="center"><strong>_____ / 7,5 P.</strong></td>
              <td class="center"><strong>_____ / 15,0 P.</strong></td>
            </tr>
          </tbody>
        </table>

        <div style="display:flex; justify-content:space-between; align-items:center; font-size:8.5px; color:#475569; margin-top:4px;">
          <div>Prüfer/in 1 (Name & Unterschrift): ___________________________</div>
          <div>Prüfer/in 2 (Name & Unterschrift): ___________________________</div>
          <div>Datum: 15.10.2026</div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Kandidat: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Teil 5: Mündlicher Ausdruck</span>
      <span class="footer-page">Seite 8 von 8</span>
    </div>
  </div>

</body>
</html>
"""
    return html

def build_examiner_guide_html():
    logo_b64 = get_logo_b64()
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Deutsch Zertifikat B1 – Prüferheft & Lösungsschlüssel</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 0;
  }}
  *, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #0f172a;
    background: #ffffff;
    font-size: 10.5px;
    line-height: 1.35;
  }}
  .exam-page {{
    width: 210mm;
    height: 297mm;
    padding: 12mm 15mm 10mm 15mm;
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    background: #ffffff;
  }}
  .exam-page:last-child {{
    page-break-after: auto;
  }}

  /* Header & Footer */
  .page-top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1.5px solid #0f2b48;
    padding-bottom: 5px;
    margin-bottom: 8px;
    font-size: 8.5px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #475569;
  }}
  .page-top-bar .inst-tag {{
    font-weight: 700;
    color: #b91c1c;
  }}
  .page-footer-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #cbd5e1;
    padding-top: 5px;
    margin-top: 6px;
    font-size: 8px;
    color: #64748b;
  }}

  /* German Tri-color Bar */
  .ger-bar {{
    display: flex;
    height: 4px;
    width: 100%;
    margin-bottom: 8px;
    border-radius: 2px;
    overflow: hidden;
  }}
  .ger-bar .bar-black {{ background: #111827; flex: 1; }}
  .ger-bar .bar-red {{ background: #dc2626; flex: 1; }}
  .ger-bar .bar-gold {{ background: #f59e0b; flex: 1; }}

  /* Cover Top */
  .cover-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 6px;
    border-bottom: 2px solid #0f2b48;
  }}
  .cover-inst-title {{
    font-size: 13px;
    font-weight: 900;
    color: #0f2b48;
  }}
  .cover-inst-sub {{
    font-size: 9.5px;
    font-weight: 700;
    color: #b91c1c;
  }}
  .cover-inst-contact {{
    font-size: 8px;
    color: #64748b;
  }}
  .cover-logo-img {{
    height: 44px;
    width: auto;
    object-fit: contain;
  }}

  .examiner-banner {{
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    color: #ffffff;
    padding: 8px 12px;
    border-radius: 5px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .examiner-badge {{
    background: #dc2626;
    color: #ffffff;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 8px;
    border-radius: 10px;
    letter-spacing: 0.5px;
  }}

  .section-title {{
    font-size: 11.5px;
    font-weight: 800;
    color: #0f2b48;
    background: #f1f5f9;
    padding: 4px 8px;
    border-left: 4px solid #0f2b48;
    margin-bottom: 6px;
    border-radius: 0 4px 4px 0;
  }}

  .audio-item {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 6px 8px;
    margin-bottom: 6px;
  }}
  .audio-num {{
    font-size: 10px;
    font-weight: 800;
    color: #1e3a8a;
    margin-bottom: 2px;
  }}
  .audio-text {{
    font-size: 9.2px;
    line-height: 1.35;
    color: #1e293b;
    font-style: italic;
  }}

  /* Dialogue Box */
  .dialogue-box {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 6px 8px;
    margin-bottom: 6px;
  }}
  .speaker-line {{
    margin-bottom: 4px;
    font-size: 9.1px;
    line-height: 1.32;
  }}
  .speaker-name {{
    font-weight: 800;
    color: #0f2b48;
    display: inline-block;
    min-width: 90px;
  }}

  /* Answer Key Table */
  .key-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5px;
    margin-bottom: 8px;
  }}
  .key-table th {{
    background: #0f2b48;
    color: #ffffff;
    font-weight: 700;
    padding: 5px 6px;
    text-align: left;
    border: 1px solid #0f2b48;
  }}
  .key-table td {{
    padding: 4px 6px;
    border: 1px solid #cbd5e1;
  }}
  .key-table tr:nth-child(even) {{
    background: #f8fafc;
  }}
  .key-ans {{
    font-weight: 800;
    color: #1e3a8a;
  }}

  /* Candidate Badge */
  .candidate-ref-bar {{
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    padding: 5px 10px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    font-size: 9px;
  }}
</style>
</head>
<body>

  <!-- ==================== PRÜFERHEFT SEITE 1: AUDIO-SKRIPTE TEIL A ==================== -->
  <div class="exam-page">
    <div>
      <div class="cover-header">
        <div>
          <div class="cover-inst-title">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</div>
          <div class="cover-inst-sub">PRÜFUNGSKOMMISSION &bull; DEUTSCHE ZERTIFIKATSPRÜFUNG B1</div>
          <div class="cover-inst-contact">Autorisation N° 22-200/2020 &bull; Deroua | Offizielles Prüferheft &amp; Lösungsschlüssel</div>
        </div>
        <img src="data:image/png;base64,{logo_b64}" class="cover-logo-img" alt="Logo ILAS">
      </div>

      <div class="ger-bar" style="margin-top: 6px;">
        <div class="bar-black"></div>
        <div class="bar-red"></div>
        <div class="bar-gold"></div>
      </div>

      <div class="examiner-banner">
        <div>
          <div style="font-size:13px; font-weight:900;">PRÜFERHEFT (EXAMINATEUR) &bull; B1</div>
          <div style="font-size:9.5px; opacity:0.9;">Hörtexte (Transkriptionen), Lösungsschlüssel &amp; Bewertungsrichtlinien</div>
        </div>
        <span class="examiner-badge">STRENG VERTRAULICH</span>
      </div>

      <div class="candidate-ref-bar">
        <span>Prüfungsbogen für Kandidat: <strong>ANASS BENYAHIA</strong></span>
        <span>Geburtsdatum: <strong>26.01.2007</strong></span>
        <span>CIN: <strong>WB226817</strong></span>
        <span>Datum: <strong>15.10.2026</strong></span>
      </div>

      <div class="section-title">1. HÖRTEXTE / AUDIO-TRANSKRIPTIONEN (Für Teil 2: Hören)</div>
      <div style="font-size:8.8px; color:#475569; margin-bottom:6px; font-style:italic;">
        Hinweis für die Prüfenden: Lesen Sie die Texte im natürlichen, deutlichen Sprechtempo vor oder spielen Sie die Audio-Aufnahme ab. Beachten Sie die Lesehäufigkeit (1x oder 2x).
      </div>

      <div style="font-size:10px; font-weight:800; color:#0f2b48; margin-bottom:4px;">
        AUFGABE 1: KURZE ANSAGEN (Jeden Text 1x vorlesen &bull; Aufgaben 16 bis 20)
      </div>

      <div class="audio-item">
        <div class="audio-num">Nummer 16 (Zahnarztpraxis Dr. Keller):</div>
        <div class="audio-text">
          „Guten Tag, Frau Schneider, hier spricht Sabine Neumann aus der Zahnarztpraxis Dr. Keller. Ich rufe wegen Ihres Kontrolltermins morgen früh um 9 Uhr an. Der Termin findet wie geplant statt, aber da wir seit diesem Quartal ein neues Computersystem haben, bitten wir Sie dringend, Ihre neue elektronische Gesundheitskarte mitzubringen. Außerdem bat mich Dr. Keller, Sie an die Liste der Medikamente zu erinnern, die Sie aktuell einnehmen. Vielen Dank und bis morgen!“
        </div>
      </div>

      <div class="audio-item">
        <div class="audio-num">Nummer 17 (Bahnhofsdurchsage Regionalbahn RB 42):</div>
        <div class="audio-text">
          „Achtung, eine wichtige Durchsage für die Fahrgäste der Regionalbahn RB 42 in Richtung Neustadt Hauptbahnhof: Wegen schwerer Sturmschäden aus der vergangenen Nacht muss die Eisenbahnbrücke zwischen den Stationen Südplatz und Ostbahnhof dringend überprüft und repariert werden. Aus diesem Grund endet dieser Zug heute außerplanmäßig am Ostbahnhof. Bitte nutzen Sie für die Weiterfahrt zum Hauptbahnhof die bereitstehenden Ersatzbusse auf dem Vorplatz.“
        </div>
      </div>

      <div class="audio-item">
        <div class="audio-num">Nummer 18 (Wettervorhersage Süddeutschland):</div>
        <div class="audio-text">
          „Und hier noch die Wetteraussichten für Süddeutschland für das kommende Wochenende: Nutzen Sie unbedingt den Samstag für Ihre Ausflüge ins Grüne! Bei viel Sonnenschein erreichen die Temperaturen noch einmal angenehme 24 Grad. Am Sonntagvormittag bleibt es zunächst trocken, doch ab dem frühen Nachmittag ziehen von Westen her dichte Wolken auf. Es muss mit kräftigen Gewittern, Starkregen und stürmischem Wind gerechnet werden. Dabei kühlt es deutlich auf nur noch 13 Grad ab.“
        </div>
      </div>

      <div class="audio-item">
        <div class="audio-num">Nummer 19 (Möbelhaus Wohn-Traum &bull; Herr Berger):</div>
        <div class="audio-text">
          „Hallo Herr Albers, hier ist das Möbelhaus Wohn-Traum, mein Name ist Berger. Es geht um Ihre Bestellung vom letzten Monat: den großen Eichenholztisch und die sechs Lederstühle. Eigentlich war die Lieferung ja erst für nächsten Mittwoch geplant. Da aber ein anderer Kunde auf unserer Freitags-Tour kurzfristig abgesagt hat, könnten unsere Fahrer Ihnen die kompletten Möbel schon diesen Freitag zwischen 10 und 13 Uhr vorbeibringen. Bitte rufen Sie uns kurz zurück, ob jemand zu Hause ist.“
        </div>
      </div>

      <div class="audio-item" style="margin-bottom:0;">
        <div class="audio-num">Nummer 20 (Telefonischer Ansagedienst des Stadtmuseums):</div>
        <div class="audio-text">
          „Herzlich willkommen beim telefonischen Infodienst des Stadtmuseums. Unsere Ausstellungen sind von Dienstag bis Sonntag jeweils von 10 bis 18 Uhr geöffnet. Ein wichtiger Hinweis für diesen Sonntag: Aufgrund des jährlichen Stadtmarathons sind sämtliche Zufahrtsstraßen rund um das Museum sowie unser Besucherparkplatz von 8 bis 17 Uhr komplett für den Autoverkehr gesperrt. Bitte reisen Sie unbedingt mit der U-Bahn-Linie 4 an. Das Museum hat regulär geöffnet.“
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Prüferheft: Hörtexte (Aufgabe 1)</span>
      <span>Seite 1 von 4</span>
    </div>
  </div>


  <!-- ==================== PRÜFERHEFT SEITE 2: AUDIO-SKRIPTE TEIL B ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">VERTRAULICH &bull; PRÜFERHEFT B1</span>
        <span>Hörtexte Teil 2 (Aufgabe 2 &amp; Aufgabe 3)</span>
      </div>

      <div style="font-size:10px; font-weight:800; color:#0f2b48; margin-bottom:4px;">
        AUFGABE 2: RADIO-INTERVIEW (Gespräch 2x vorlesen &bull; Aufgaben 21 bis 25)
      </div>

      <div class="dialogue-box">
        <div class="speaker-line">
          <span class="speaker-name">Moderatorin:</span>
          „Schönen guten Morgen bei Radio Aktuell! Bald gibt es wieder Abschlusszeugnisse, und Hunderttausende Jugendliche stehen vor der Frage: Soll ich an die Universität gehen oder lieber eine praktische Ausbildung im Betrieb machen? Darüber spreche ich heute mit dem Berufsberater Thomas Richter. Herr Richter, geht der Trend immer noch dahin, dass fast jeder studieren will?“
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Thomas Richter:</span>
          „Guten Morgen! Ja, der gesellschaftliche Druck in Richtung Universität ist nach wie vor enorm hoch, auch wenn es nicht ganz 80 Prozent sind, sondern aktuell etwas mehr als die Hälfte eines Jahrgangs, die ein Studium beginnt. Das Problem dabei ist aber: Fast 30 Prozent der Studierenden in Bachelor-Studiengängen brechen ihr Studium vorzeitig ab.“
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Moderatorin:</span>
          „Woran liegt das? Sind die jungen Leute heute weniger belastbar?“
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Thomas Richter:</span>
          „Nein, überhaupt nicht. Aber viele schreiben sich nach dem Abitur an der Uni ein, weil sie denken, das sei einfach eine Verlängerung der Schulzeit. Sie sind dann völlig überrascht, wie theoretisch und abstrakt ein Universitätsstudium ist und wie viel Selbstorganisation man braucht. Viele merken erst nach zwei Semestern, dass sie eigentlich viel lieber praktisch arbeiten und am Abend ein konkretes Ergebnis ihrer Arbeit sehen möchten.“
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Moderatorin:</span>
          „Trotzdem haben viele Eltern Angst, dass ihr Kind mit einer Berufsausbildung später zu wenig verdient.“
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Thomas Richter:</span>
          „Das ist ein völlig veraltetes Vorurteil! Schauen Sie sich heute das Handwerk oder die technischen Berufe an: Wer eine Ausbildung zum Elektriker, Heizungsbauer oder Mechatroniker macht und danach seinen Meisterbrief erwirbt, verdient heute oft genauso gut oder sogar besser als viele Akademiker – und hat vor allem null Risiko, arbeitslos zu werden. Außerdem verdient man schon ab dem ersten Tag der Ausbildung eigenes Geld, während Studenten oft mit Schulden ins Berufsleben starten.“
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Moderatorin:</span>
          „Und was raten Sie Jugendlichen, die sich zwischen Theorie und Praxis einfach nicht entscheiden können?“
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Thomas Richter:</span>
          „Für diese Gruppe ist das duale Studium ideal. Dabei schließt man einen Vertrag mit einem Unternehmen ab und wechselt alle drei Monate zwischen der praktischen Arbeit im Betrieb und den Vorlesungen an einer Hochschule. Das ist zwar zeitlich sehr intensiv, bietet aber hervorragende Karrierechancen. Mein wichtigster Rat an die Eltern lautet deshalb: Drängen Sie Ihr Kind niemals in ein Studium, nur weil der Nachbarsjunge auch Jura studiert oder weil es besser klingt. Entscheidend ist allein, wo die echten Talente und Interessen des Jugendlichen liegen.“
        </div>
      </div>

      <div style="font-size:10px; font-weight:800; color:#0f2b48; margin-top:8px; margin-bottom:4px;">
        AUFGABE 3: ALLTAGSGESPRÄCH IN DER PAUSE (Gespräch 1x vorlesen &bull; Aufgaben 26 bis 30)
      </div>

      <div class="dialogue-box">
        <div class="speaker-line"><span class="speaker-name">Anna:</span> „Sag mal, David, die Chefin hat uns doch gebeten, bis Freitag Ideen für unseren jährlichen Betriebsausflug im Juni zu sammeln. Hast du dir schon Gedanken gemacht?“</div>
        <div class="speaker-line"><span class="speaker-name">David:</span> „Ja, ein bisschen. Auf jeden Fall sollten wir nicht wieder so eine lange Bergwanderung machen wie letztes Jahr! Als es nachmittags angefangen hat zu regnen, waren alle völlig durchnässt und hatten schlechte Laune.“</div>
        <div class="speaker-line"><span class="speaker-name">Anna:</span> „Da hast du absolut recht, diese Wanderung im Regen war wirklich eine Katastrophe, das fand ich auch schrecklich! Ich dachte deshalb dieses Mal an etwas, das drinnen stattfindet. Wie wäre es mit einem professionellen Kochkurs in einer Kochschule? Wenn man in kleinen Gruppen ein Drei-Gänge-Menü kocht, lernt man auch die neuen Kollegen aus der Buchhaltung richtig kennen – viel besser, als wenn man im Restaurant nur nebeneinander am Tisch sitzt.“</div>
        <div class="speaker-line"><span class="speaker-name">David:</span> „Hm, ich weiß nicht. Manche kochen ja gar nicht gern. Ich fände eine gemütliche Schifffahrt auf dem Fluss mit einem großen Abendbuffet an Bord viel entspannter.“</div>
        <div class="speaker-line"><span class="speaker-name">Anna:</span> „Die Idee mit dem Schiff hatte ich auch schon und habe gestern im Internet nach den Preisen geschaut. Das Problem ist unser Budget: Die Firma zahlt maximal 50 Euro pro Person. Eine Abendfahrt mit Buffet kostet aber schon 68 Euro ohne Getränke, das können wir also leider vergessen.“</div>
        <div class="speaker-line"><span class="speaker-name">David:</span> „Ach schade, ja, wenn es über 50 Euro kostet, genehmigt die Buchhaltung das sicher nicht. Aber noch etwas anderes: Findest du auch, dass der Ausflug dieses Jahr wieder an einem Freitag stattfinden sollte? Wenn wir das auf den Samstag legen, sagen wieder die halben Kollegen ab, weil sie Familie haben.“</div>
        <div class="speaker-line"><span class="speaker-name">Anna:</span> „Nein, ehrlich gesagt fände ich den Samstag gar nicht schlecht, dann hat man keinen Zeitdruck. Aber weißt du was? Lass uns doch einfach deinen Vorschlag mit einer kürzeren Nachmittagsschifffahrt ohne Buffet und meinen Vorschlag mit dem Kochkurs aufschreiben. Dann geben wir der Chefin beide Optionen und das Team kann per E-Mail abstimmen.“</div>
        <div class="speaker-line"><span class="speaker-name">David:</span> „Perfekt, so machen wir das! Eine Abstimmung unter den Kollegen ist die fairste Lösung.“</div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Prüferheft: Hörtexte (Aufgabe 2 &amp; 3)</span>
      <span>Seite 2 von 4</span>
    </div>
  </div>


  <!-- ==================== PRÜFERHEFT SEITE 3: LÖSUNGSSCHLÜSSEL ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">VERTRAULICH &bull; PRÜFERHEFT B1</span>
        <span>Offizieller Master-Lösungsschlüssel (Teil 1 bis Teil 3)</span>
      </div>

      <div class="section-title">2. LÖSUNGSSCHLÜSSEL &amp; BEWERTUNGSTABELLEN</div>

      <!-- Teil 1: Lesen -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-bottom:3px;">
        TEIL 1: LESEN (Gesamt: 25 Punkte)
      </div>
      <table class="key-table">
        <thead>
          <tr>
            <th style="width:25%;">Aufgabe</th>
            <th style="width:20%;">Punkte</th>
            <th>Musterlösungen &amp; Erläuterung</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Aufgabe 1:</strong> Zeitungsartikel</td>
            <td>10 P. (5 x 2 P.)</td>
            <td>
              <strong>1. b</strong> (weniger Stunden bei gleichem Gehalt) &bull; 
              <strong>2. c</strong> (Personalmangel/Fachkräfte) &bull; 
              <strong>3. b</strong> (4 Tage länger, Fr Notdienst) &bull; 
              <strong>4. a</strong> (weniger Krankheit, mehr Produktivität) &bull; 
              <strong>5. b</strong> (Dienstleistung nicht beliebig komprimierbar)
            </td>
          </tr>
          <tr>
            <td><strong>Aufgabe 2:</strong> Leserbriefe</td>
            <td>10 P. (5 x 2 P.)</td>
            <td>
              <strong>6. Richtig [R]</strong> &bull; 
              <strong>7. Falsch [F]</strong> &bull; 
              <strong>8. Falsch [F]</strong> &bull; 
              <strong>9. Richtig [R]</strong> &bull; 
              <strong>10. Falsch [F]</strong> (Anwohner/Handwerker frei)
            </td>
          </tr>
          <tr>
            <td><strong>Aufgabe 3:</strong> Kurszuordnung</td>
            <td>5 P. (5 x 1 P.)</td>
            <td>
              <strong>11. C</strong> (MS Excel Wochenende) &bull; 
              <strong>12. A</strong> (Rhetorik &amp; Stimme) &bull; 
              <strong>13. 0</strong> (Kein 4-wöchiger Vormittagskurs B2) &bull; 
              <strong>14. D</strong> (Konfliktmanagement) &bull; 
              <strong>15. E</strong> (Rücken &amp; Büro Di-Abend)
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Teil 2: Hören -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-top:8px; margin-bottom:3px;">
        TEIL 2: HÖREN (Gesamt: 25 Punkte)
      </div>
      <table class="key-table">
        <thead>
          <tr>
            <th style="width:25%;">Aufgabe</th>
            <th style="width:20%;">Punkte</th>
            <th>Musterlösungen &amp; Erläuterung</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Aufgabe 1:</strong> Ansagen</td>
            <td>10 P. (5 x 2 P.)</td>
            <td>
              <strong>16. b</strong> (Karte &amp; Medikamentenplan) &bull; 
              <strong>17. a</strong> (Brückenreparatur nach Sturm) &bull; 
              <strong>18. c</strong> (Sa warm, So Gewitter &amp; Kälte) &bull; 
              <strong>19. a</strong> (Frühzeitige Lieferung Fr) &bull; 
              <strong>20. b</strong> (Museumszufahrt wegen Marathon gesperrt)
            </td>
          </tr>
          <tr>
            <td><strong>Aufgabe 2:</strong> Interview</td>
            <td>10 P. (5 x 2 P.)</td>
            <td>
              <strong>21. Falsch [F]</strong> (nur etwas über die Hälfte, nicht 80%) &bull; 
              <strong>22. Richtig [R]</strong> &bull; 
              <strong>23. Falsch [F]</strong> (Handwerksmeister verdienen oft besser) &bull; 
              <strong>24. Richtig [R]</strong> &bull; 
              <strong>25. Falsch [F]</strong> (nicht auf Prestige drängen, sondern Interessen fördern)
            </td>
          </tr>
          <tr>
            <td><strong>Aufgabe 3:</strong> Alltagsgespräch</td>
            <td>5 P. (5 x 1 P.)</td>
            <td>
              <strong>26. Beide [B]</strong> (beide fanden Regenwanderung schrecklich) &bull; 
              <strong>27. Anna [A]</strong> (Kochkurs schweißt zusammen) &bull; 
              <strong>28. Beide [B]</strong> (50€ Budget vs. 68€ Buffet) &bull; 
              <strong>29. David [D]</strong> (präferiert Freitag wegen Familie) &bull; 
              <strong>30. Beide [B]</strong> (einigen sich auf Doppel-Vorschlag zur Abstimmung)
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Teil 3: Sprachbausteine -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-top:8px; margin-bottom:3px;">
        TEIL 3: SPRACHBAUSTEINE (Gesamt: 15 Punkte &bull; 20 Fragen x 0,75 Punkte)
      </div>
      <table class="key-table">
        <thead>
          <tr>
            <th style="width:25%;">Aufgabe</th>
            <th style="width:20%;">Punkte</th>
            <th>Lösungen (Schlüssel 31 bis 50)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Aufgabe 1:</strong> Lückentext (31–40)</td>
            <td>7,5 P. (10 x 0,75 P.)</td>
            <td>
              <strong>31. b</strong> (der) &bull; <strong>32. c</strong> (dass) &bull; <strong>33. b</strong> (Obwohl) &bull; <strong>34. c</strong> (den) &bull; <strong>35. a</strong> (das)<br>
              <strong>36. a</strong> (wurde) &bull; <strong>37. b</strong> (um) &bull; <strong>38. b</strong> (meiner) &bull; <strong>39. c</strong> (Wäre) &bull; <strong>40. a</strong> (sobald)
            </td>
          </tr>
          <tr>
            <td><strong>Aufgabe 2:</strong> B1-Grammatik (41–50)</td>
            <td>7,5 P. (10 x 0,75 P.)</td>
            <td>
              <strong>41. c</strong> (deren) &bull; <strong>42. b</strong> (Anstatt) &bull; <strong>43. c</strong> (müssen) &bull; <strong>44. b</strong> (Kollegen - N-Deklination)<br>
              <strong>45. c</strong> (Je/desto) &bull; <strong>46. b</strong> (wäre/würde) &bull; <strong>47. c</strong> (über/auf) &bull; <strong>48. a</strong> (worden war - Plusquamperfekt Passiv)<br>
              <strong>49. c</strong> (des - Genitiv) &bull; <strong>50. c</strong> (abzugeben - Infinitiv mit zu)
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Schnellübersicht Klickmatrix -->
      <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:4px; padding:6px 10px; font-size:8.5px; line-height:1.4;">
        <strong>Kompakte Prüfer-Schnellübersicht (1–50):</strong><br>
        1.b | 2.c | 3.b | 4.a | 5.b | 6.R | 7.F | 8.F | 9.R | 10.F | 11.C | 12.A | 13.0 | 14.D | 15.E | 16.b | 17.a | 18.c | 19.a | 20.b | 21.F | 22.R | 23.F | 24.R | 25.F | 26.B | 27.A | 28.B | 29.D | 30.B | 31.b | 32.c | 33.b | 34.c | 35.a | 36.a | 37.b | 38.b | 39.c | 40.a | 41.c | 42.b | 43.c | 44.b | 45.c | 46.b | 47.c | 48.a | 49.c | 50.c
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Prüferheft: Lösungsschlüssel (Teil 1 bis 3)</span>
      <span>Seite 3 von 4</span>
    </div>
  </div>


  <!-- ==================== PRÜFERHEFT SEITE 4: BEWERTUNGSKRITERIEN ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">VERTRAULICH &bull; PRÜFERHEFT B1</span>
        <span>Bewertungsrichtlinien &amp; Notenskala</span>
      </div>

      <div class="section-title">3. BEWERTUNGSKRITERIEN FÜR SCHREIBEN &amp; SPRECHEN</div>

      <!-- Schreiben Kriterien -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-bottom:3px;">
        TEIL 4: SCHREIBEN (20 PUNKTE &bull; AUFGABE 1: 10 P. / AUFGABE 2: 10 P.)
      </div>
      <table class="key-table" style="font-size:9px;">
        <thead>
          <tr>
            <th style="width:28%;">Kriterium</th>
            <th style="width:22%;">Punkteverteilung</th>
            <th>Deskriptoren für B1-Niveau</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Aufgabe 1:</strong> Formelle Beschwerde-E-Mail (10 P.)</td>
            <td>
              &bull; Leitpunkte: 4 P.<br>
              &bull; Kohärenz/Stil: 3 P.<br>
              &bull; Korrektheit: 3 P.
            </td>
            <td>
              Alle 4 Leitpunkte (Kaufdaten, Defekt, Frist, Forderung) angemessen behandelt. Formelle Anrede (<em>„Sehr geehrte Damen und Herren“</em>) und Grußformel. Sinnvolle Verknüpfung der Sätze mit B1-Konnektoren (<em>„daher“, „obwohl“, „falls“</em>). Grammatisch weitgehend korrekt.
            </td>
          </tr>
          <tr>
            <td><strong>Aufgabe 2:</strong> Forumsbeitrag / Meinung (10 P.)</td>
            <td>
              &bull; Inhalt/Argumente: 4 P.<br>
              &bull; Konnektoren/Stil: 3 P.<br>
              &bull; Wortschatz/Form: 3 P.
            </td>
            <td>
              Stellungnahme zur These des Autors. Mindestens zwei Vor- und zwei Nachteile von Homeoffice explizit genannt und begründet. Ein schlüssiger, realistischer Kompromiss formuliert. Reicher B1-Wortschatz, Textgliederung mit Einleitung, Hauptteil und Schlusssatz.
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Mündlich Kriterien -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-top:8px; margin-bottom:3px;">
        TEIL 5: MÜNDLICHER AUSDRUCK (15 PUNKTE &bull; 5A: 7,5 P. / 5B: 7,5 P.)
      </div>
      <table class="key-table" style="font-size:9px;">
        <thead>
          <tr>
            <th style="width:28%;">Prüfungsbereich</th>
            <th style="width:22%;">Punkteverteilung</th>
            <th>Bewertungskriterien</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Teil 5A:</strong> Präsentation (Soziale Netzwerke)</td>
            <td>7,5 Punkte (ca. 4–5 Min.)</td>
            <td>
              Klare thematische Gliederung (Erfahrung &rarr; Heimatland &rarr; Vor-/Nachteile &rarr; Fazit). Flüssiges Sprechen ohne übermäßige Pausen, verständliche Aussprache und Intonation, sichere Beantwortung von 1–2 Prüfernachfragen.
            </td>
          </tr>
          <tr>
            <td><strong>Teil 5B:</strong> Problemlösung (Überraschungstrip)</td>
            <td>7,5 Punkte (ca. 6 Min.)</td>
            <td>
              Aktive Interaktion und partnerschaftliche Gesprächsführung. Eigene Ideen einbringen, auf Argumente des Partners eingehen, Kompromiss bei Budget/Unterkunft/Fahrt aushandeln.
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Notenskala -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-top:8px; margin-bottom:3px;">
        OFFIZIELLE NOTENSKALA (GER B1 &bull; 100 PUNKTE GESAMT)
      </div>
      <table class="key-table" style="text-align:center; font-size:9px;">
        <thead>
          <tr>
            <th style="text-align:center;">Punkte</th>
            <th style="text-align:center;">Prozentwert</th>
            <th style="text-align:center;">Prädikat (Note)</th>
            <th style="text-align:center;">B1-Status</th>
          </tr>
        </thead>
        <tbody>
          <tr style="background:#ecfdf5;">
            <td><strong>90,0 – 100,0</strong></td>
            <td>90 % – 100 %</td>
            <td><strong>Sehr gut (1)</strong></td>
            <td><strong style="color:#059669;">Bestanden mit Auszeichnung</strong></td>
          </tr>
          <tr style="background:#f0fdf4;">
            <td><strong>80,0 – 89,5</strong></td>
            <td>80 % – 89 %</td>
            <td><strong>Gut (2)</strong></td>
            <td><strong style="color:#16a34a;">Bestanden</strong></td>
          </tr>
          <tr>
            <td><strong>70,0 – 79,5</strong></td>
            <td>70 % – 79 %</td>
            <td><strong>Befriedigend (3)</strong></td>
            <td><strong style="color:#2563eb;">Bestanden</strong></td>
          </tr>
          <tr style="background:#fffbeb;">
            <td><strong>60,0 – 69,5</strong></td>
            <td>60 % – 69 %</td>
            <td><strong>Ausreichend (4)</strong></td>
            <td><strong style="color:#d97706;">Bestanden (Mindestgrenze)</strong></td>
          </tr>
          <tr style="background:#fef2f2;">
            <td><strong>0,0 – 59,5</strong></td>
            <td>&lt; 60 %</td>
            <td><strong>Nicht bestanden (5)</strong></td>
            <td><strong style="color:#dc2626;">Nicht bestanden</strong></td>
          </tr>
        </tbody>
      </table>

      <div style="border-top:1.5px solid #cbd5e1; padding-top:6px; margin-top:8px; display:flex; justify-content:space-between; align-items:center; font-size:8.5px; color:#475569;">
        <div>Prüfungsleitung ILAS: <strong>M. Aziz Marsoul</strong></div>
        <div>Zertifikatsreferenz: <strong>GER-B1-2026-ILAS</strong></div>
        <div>Siegel &amp; Unterschrift: [ ___________________________ ]</div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Prüferheft: Bewertungsrichtlinien &amp; Notenskala</span>
      <span>Seite 4 von 4</span>
    </div>
  </div>

</body>
</html>
"""
    return html

def convert_html_to_pdf(html_content, html_filename, pdf_filename):
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    full_html_path = os.path.abspath(html_filename)
    full_pdf_path = os.path.abspath(pdf_filename)
    
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={full_pdf_path}",
        full_html_path
    ]
    
    print(f"Converting {html_filename} -> {pdf_filename}...")
    subprocess.run(cmd, check=True)
    
    if os.path.exists(pdf_filename):
        size = os.path.getsize(pdf_filename)
        doc = pymupdf.open(pdf_filename)
        page_count = len(doc)
        print(f"Success! {pdf_filename} created ({size} bytes, {page_count} pages).")
        return page_count
    else:
        raise RuntimeError(f"Failed to generate {pdf_filename}")

def merge_pdfs(pdf_list, output_filename):
    merged_doc = pymupdf.open()
    for pdf in pdf_list:
        doc = pymupdf.open(pdf)
        merged_doc.insert_pdf(doc)
    merged_doc.save(output_filename)
    merged_doc.close()
    print(f"Merged PDF saved to {output_filename} with {len(pymupdf.open(output_filename))} total pages.")

def render_preview_images(pdf_filename, output_prefix, max_pages=3):
    doc = pymupdf.open(pdf_filename)
    image_paths = []
    for i in range(min(len(doc), max_pages)):
        page = doc[i]
        pix = page.get_pixmap(dpi=150)
        img_path = f"{output_prefix}_page_{i+1}.png"
        pix.save(img_path)
        image_paths.append(img_path)
        print(f"Rendered preview image: {img_path}")
    return image_paths

def main():
    print("--- Building Student Examination Booklet ---")
    student_html = build_student_exam_html()
    student_pages = convert_html_to_pdf(student_html, "Deutsch_B1_Pruefungsheft_ANASS_BENYAHIA.html", "Deutsch_B1_Pruefungsheft_ANASS_BENYAHIA.pdf")
    
    print("\n--- Building Examiner Guide & Solution Key ---")
    examiner_html = build_examiner_guide_html()
    examiner_pages = convert_html_to_pdf(examiner_html, "Deutsch_B1_Prueferheft_Loesungsschluessel.html", "Deutsch_B1_Prueferheft_Loesungsschluessel.pdf")
    
    print("\n--- Creating Master Combined Package ---")
    merge_pdfs(["Deutsch_B1_Pruefungsheft_ANASS_BENYAHIA.pdf", "Deutsch_B1_Prueferheft_Loesungsschluessel.pdf"], "Deutsch_B1_Komplettpaket_ANASS_BENYAHIA.pdf")
    
    print("\n--- Generating Visual Previews ---")
    student_previews = render_preview_images("Deutsch_B1_Pruefungsheft_ANASS_BENYAHIA.pdf", "preview_student", max_pages=4)
    examiner_previews = render_preview_images("Deutsch_B1_Prueferheft_Loesungsschluessel.pdf", "preview_examiner", max_pages=2)
    
    print("\nALL BUILDS COMPLETE SUCCESSFULLY!")

if __name__ == "__main__":
    main()
