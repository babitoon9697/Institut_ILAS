# -*- coding: utf-8 -*-
"""
Builder for English Certificate B1 Modern Examination PDFs
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
<html lang="en">
<head>
<meta charset="utf-8">
<title>English Certificate B1 – Examination Booklet – ANASS BENYAHIA</title>
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

  /* British / International Stripe Bar */
  .flag-bar {{
    display: flex;
    height: 4px;
    width: 100%;
    margin-bottom: 8px;
    border-radius: 2px;
    overflow: hidden;
  }}
  .flag-bar .bar-navy {{ background: #0f2b48; flex: 2; }}
  .flag-bar .bar-red {{ background: #c8102e; flex: 1; }}
  .flag-bar .bar-blue {{ background: #1d4ed8; flex: 2; }}

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
    color: #c8102e;
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

  /* Opinion Cards (Task 2) */
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

  /* Course matching (Task 3) */
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

  <!-- ==================== PAGE 1: COVER PAGE ==================== -->
  <div class="exam-page">
    <div>
      <div class="cover-header">
        <div class="cover-inst-info">
          <div class="cover-inst-title">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</div>
          <div class="cover-inst-sub">ILAS LANGUAGE INSTITUTE &bull; ACCREDITED TRAINING CENTER</div>
          <div class="cover-inst-contact">Ministerial Authorization N° 22-200/2020 &bull; Deroua | Phone: 06 70 38 48 73 / 06 60 29 11 55</div>
        </div>
        <div>
          <img src="data:image/png;base64,{logo_b64}" class="cover-logo-img" alt="ILAS Logo">
        </div>
      </div>

      <div class="flag-bar" style="margin-top: 6px;">
        <div class="bar-navy"></div>
        <div class="bar-red"></div>
        <div class="bar-blue"></div>
      </div>

      <div class="cover-hero">
        <div class="cover-level-badge">COMMON EUROPEAN FRAMEWORK OF REFERENCE FOR LANGUAGES (CEFR) &bull; LEVEL B1</div>
        <h1>ENGLISH B1 CERTIFICATE</h1>
        <h2>OFFICIAL CANDIDATE EXAMINATION BOOKLET</h2>
        <p>Standardized Examination Papers for International B1 English Language Competency</p>
      </div>

      <!-- Candidate Profile -->
      <div class="candidate-card">
        <div class="candidate-card-header">
          <span>Candidate Information / Données du Candidat</span>
          <span style="color:#2563eb; font-weight:700;">Examination Center: ILAS Deroua</span>
        </div>
        <div class="candidate-grid">
          <div class="candidate-field">
            <span class="cand-label">Full Name (Nom &amp; Prénom):</span>
            <span class="cand-value cand-value-highlight">BENYAHIA, Anass</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Date of Birth (Date de Naissance):</span>
            <span class="cand-value">26.01.2007</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">National ID / CIN:</span>
            <span class="cand-value cand-value-highlight">WB226817</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Candidate ID (N° Candidat):</span>
            <span class="cand-value">ILAS-ENG-B1-2026-WB226817</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Exam Date (Date d'Examen):</span>
            <span class="cand-value">16 October 2026</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Examination Type:</span>
            <span class="cand-value">Full B1 Certificate (All Modules)</span>
          </div>
        </div>
      </div>

      <!-- Exam Modules Overview -->
      <table class="score-table">
        <thead>
          <tr>
            <th style="width: 32%;">Examination Module</th>
            <th class="center" style="width: 20%;">Duration</th>
            <th class="center" style="width: 22%;">Max. Points</th>
            <th class="center" style="width: 26%;">Score Achieved</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Part 1: Reading</strong> (Reading Comprehension)</td>
            <td class="center">45 Min.</td>
            <td class="center">25 Points</td>
            <td class="center">_____ / 25</td>
          </tr>
          <tr>
            <td><strong>Part 2: Listening</strong> (Listening Comprehension)</td>
            <td class="center">30 Min.</td>
            <td class="center">25 Points</td>
            <td class="center">_____ / 25</td>
          </tr>
          <tr>
            <td><strong>Part 3: Language in Use</strong> (Grammar &amp; Vocabulary)</td>
            <td class="center">25 Min.</td>
            <td class="center">15 Points</td>
            <td class="center">_____ / 15</td>
          </tr>
          <tr>
            <td><strong>Part 4: Writing</strong> (Written Expression)</td>
            <td class="center">50 Min.</td>
            <td class="center">20 Points</td>
            <td class="center">_____ / 20</td>
          </tr>
          <tr>
            <td><strong>Part 5: Speaking</strong> (Oral Expression &amp; Interaction)</td>
            <td class="center">15 Min.</td>
            <td class="center">15 Points</td>
            <td class="center">_____ / 15</td>
          </tr>
          <tr class="total-row">
            <td><strong>OVERALL RESULT (Total)</strong></td>
            <td class="center"><strong>165 Min.</strong></td>
            <td class="center"><strong>100 Points</strong></td>
            <td class="center"><strong>_____ / 100</strong></td>
          </tr>
        </tbody>
      </table>

      <!-- Exam Rules & Signature -->
      <div class="rules-grid">
        <div class="rules-box">
          <strong>Important Instructions for Examination Candidates:</strong>
          <ul>
            <li><strong>Prohibited Items:</strong> Dictionaries, mobile phones, and smart devices are strictly forbidden.</li>
            <li><strong>Writing Pen:</strong> Use only ballpoint pens with blue or black ink. Pencil is not permitted.</li>
            <li><strong>Responses:</strong> Record your answers clearly in the designated check boxes and lines.</li>
            <li><strong>Passing Grade:</strong> A minimum of <strong>60 points (60 %)</strong> is required to pass B1.</li>
          </ul>
        </div>
        <div class="sign-box">
          <div class="sign-box-label">Candidate Signature</div>
          <div class="sign-area"></div>
          <div style="font-size:7.5px; color:#64748b;">I hereby certify the accuracy of my details and work.</div>
        </div>
      </div>
    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (CIN: WB226817)</span>
      <span class="footer-page">Page 1 of 8</span>
    </div>
  </div>


  <!-- ==================== PAGE 2: PART 1 – READING (TASK 1) ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">English Certificate B1 &bull; Final Examination</span>
        <span class="cand-tag">Candidate: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>PART 1: READING COMPREHENSION</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Duration: 45 Min. (Part 1 total)</span>
          <span class="module-badge">Max. 25 Points</span>
        </div>
      </div>

      <div class="task-box">
        <div class="task-box-title">
          <span>TASK 1: READING AN IN-DEPTH BUSINESS ARTICLE</span>
          <span style="color:#2563eb;">10 Points (2 points per question)</span>
        </div>
        <div class="task-box-desc">
          Read the following article from a business journal and answer questions 1 to 5. Mark the correct answer (a, b, or c).
        </div>
      </div>

      <!-- Business Article -->
      <div class="article-card">
        <div class="article-headline">The Four-Day Work Week: Future Workplace Model or Economic Risk?</div>
        <p>
          Across the world, an increasing number of companies are exploring a radical transformation of the workplace: introducing a four-day work week with full wage compensation. This arrangement means that employees work 32 or 35 hours over four days instead of the traditional 40 hours across five days, while receiving the exact same monthly salary into their bank accounts. What once sounded like an unrealistic demand from labor unions is now being tested by numerous craft businesses, manufacturing facilities, and tech companies in real workplace conditions.
        </p>
        <p>
          One prominent example is Markus Weber’s plumbing and heating company in Cologne. Two years ago, Weber found it nearly impossible to recruit qualified technicians. Young candidates openly stated during job interviews that personal time, health, and family were far more important to them than earning extra pay through overtime. In response, Weber completely restructured his operations: his 18 staff members now work nine hours a day from Monday to Thursday, while the headquarters remains closed on Fridays – with the exception of an emergency on-call service organized on weekly rotation.
        </p>
        <p>
          The outcome astonished even the business owner himself. “In the beginning, I was deeply worried that we wouldn't finish client orders on time and would lose our customer base,” admits Weber. Yet the exact opposite occurred: the number of sick days dropped by almost 40 percent in the first year. Moreover, internal workflows were digitized and unnecessary meetings were eliminated, leading to a substantial increase in productivity per working hour. The recruitment crisis was resolved as well: since the change, Weber has received more than 50 unsolicited applications from highly skilled workers.
        </p>
        <p>
          Despite these inspiring success stories, economic experts caution against imposing a mandatory four-day week across all sectors by law. In public hospitals, emergency transit systems, and the hospitality sector, tasks cannot simply be carried out faster. If a bus driver works 20 percent fewer hours, buses inevitably run 20 percent less frequently – unless additional drivers are hired, who are already in severe shortage in the labor market. A four-day work week is therefore a powerful strategy for individual enterprises, but by no means a one-size-fits-all solution for the entire economy.
        </p>
      </div>

      <!-- Questions 1 to 5 -->
      <div class="question-item">
        <div class="question-text">1. What is meant by a four-day work week “with full wage compensation”?</div>
        <div class="options-group">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Employees work ten hours every day for four days to earn the same salary.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Employees work fewer total hours per week while receiving the same salary.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Employees accept a 20 percent pay reduction in order to take Fridays off.</div>
        </div>
      </div>

      <div class="question-item">
        <div class="question-text">2. Why did Markus Weber decide to introduce the four-day week in his company?</div>
        <div class="options-group">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Because his staff members were constantly taking sick leave and making errors.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Because labor authorities and unions legally compelled his business to do so.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Because he faced severe difficulties in attracting qualified, skilled workers.</div>
        </div>
      </div>

      <div class="question-item">
        <div class="question-text">3. How is working time organized in Weber's company today?</div>
        <div class="options-group">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Every single employee has Friday off without any exception whatsoever.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Staff work longer shifts over four days, with only an emergency team on Friday.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Individual workers choose flexibly on their own which four days to attend.</div>
        </div>
      </div>

      <div class="question-item">
        <div class="question-text">4. What was the direct result of this reorganization for Weber's business?</div>
        <div class="options-group">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Employees took significantly fewer sick days and demonstrated greater focus.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Several loyal clients transferred to competitors because of Friday closure.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Staff spent excessive hours in prolonged discussions about software upgrades.</div>
        </div>
      </div>

      <div class="question-item" style="margin-bottom:0;">
        <div class="question-text">5. Why are economic experts skeptical about enforcing a four-day week across all sectors?</div>
        <div class="options-group">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Because the majority of workers in modern industry prefer working five days.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Because in essential service professions, reduced hours cannot be compensated by faster work.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Because implementing technology in municipal buses and clinics is too expensive.</div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Part 1: Reading</span>
      <span class="footer-page">Page 2 of 8</span>
    </div>
  </div>


  <!-- ==================== PAGE 3: PART 1 – READING (TASKS 2 & 3) ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">English Certificate B1 &bull; Final Examination</span>
        <span class="cand-tag">Candidate: ANASS BENYAHIA (WB226817)</span>
      </div>

      <!-- Task 2 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>TASK 2: READERS' OPINIONS &amp; LETTERS TO THE EDITOR</span>
          <span style="color:#2563eb;">10 Points (2 points per question)</span>
        </div>
        <div class="task-box-desc">
          Read the three opinion pieces on the topic <strong>“Should city centers become completely car-free?”</strong> and evaluate statements 6–10: <strong>True [ T ]</strong> or <strong>False [ F ]</strong>.
        </div>
      </div>

      <div class="opinions-container">
        <div class="opinion-card">
          <div class="opinion-card-header">Post 1 – Sabine K. (44, Shop Owner)</div>
          “Banning cars entirely from city centers would mean financial ruin for many independent retailers. My customers frequently travel from suburban areas specifically to make substantial purchases. Nobody wants to haul heavy shopping bags on crowded trams for miles. Before banning cars, municipal authorities must first build free park-and-ride facilities on the outskirts and cut public transit fares in half.”
        </div>
        <div class="opinion-card">
          <div class="opinion-card-header">Post 2 – Lukas M. (29, Architect)</div>
          “I live right downtown and can hardly tolerate the noise, fumes, and traffic congestion anymore. Forward-thinking cities like Copenhagen and Amsterdam have shown that pedestrian zones dramatically enhance quality of life! People relax at open-air cafés where bumper-to-bumper traffic once crawled, and store revenues have actually climbed because pedestrians and cyclists stop to browse far more spontaneously than drivers.”
        </div>
        <div class="opinion-card">
          <div class="opinion-card-header">Post 3 – Herbert W. (68, Retiree)</div>
          “This discussion is far too polarized. Naturally, we should reduce urban traffic, but an outright ban completely marginalizes elderly or mobility-impaired individuals who depend on vehicles. An urban congestion toll for non-essential drivers would be much more sensible than a total prohibition. Craftsmen, delivery vehicles, and local residents should, of course, continue to enter free of charge.”
        </div>
      </div>

      <table class="rf-table">
        <thead>
          <tr>
            <th>Statement regarding the texts</th>
            <th class="rf-check-cell">True</th>
            <th class="rf-check-cell">False</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>6.</strong> Sabine K. is concerned that suburban customers will stop shopping at her store if cars are banned.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>7.</strong> Sabine K. believes that public transportation fares are already sufficiently inexpensive.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>8.</strong> Lukas M. believes that shops in car-free urban areas experience lower retail turnover than before.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>9.</strong> Herbert W. supports allowing disabled and elderly citizens to continue accessing the city center by car.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>10.</strong> Herbert W. recommends that local residents and repair contractors should also be required to pay the congestion charge.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
        </tbody>
      </table>

      <!-- Task 3 -->
      <div class="task-box" style="margin-top: 6px;">
        <div class="task-box-title">
          <span>TASK 3: MATCHING PROFILES &amp; COURSE ADVERTISEMENTS</span>
          <span style="color:#2563eb;">5 Points (1 point per question)</span>
        </div>
        <div class="task-box-desc">
          Which training course (A–G) matches which person's requirements (11–15)? For one person, there is <strong>NO</strong> suitable course (write “<strong>0</strong>”).
        </div>
      </div>

      <div class="matching-container">
        <!-- Situations 11-15 -->
        <div>
          <div style="font-size:9.5px; font-weight:800; color:#0f2b48; margin-bottom:3px;">People &amp; Situations:</div>
          
          <div class="situation-item">
            <div class="situation-text"><strong>11. Mrs. Yilmaz (Accountant):</strong> Wants to master complex spreadsheets and automated calculations on PC. Only free on weekends.</div>
            <div class="match-box">[ &nbsp; ]</div>
          </div>

          <div class="situation-item">
            <div class="situation-text"><strong>12. Mr. Bergmann:</strong> Newly promoted department head. Anxious about public speaking and seeks vocal and confidence training.</div>
            <div class="match-box">[ &nbsp; ]</div>
          </div>

          <div class="situation-item">
            <div class="situation-text"><strong>13. Leonie (19):</strong> Looking for a 4-week morning intensive Business English course to prepare for university degree.</div>
            <div class="match-box">[ &nbsp; ]</div>
          </div>

          <div class="situation-item">
            <div class="situation-text"><strong>14. Mr. Kovac:</strong> Manages a team troubled by frequent workplace disputes. Wants to acquire professional mediation techniques.</div>
            <div class="match-box">[ &nbsp; ]</div>
          </div>

          <div class="situation-item" style="margin-bottom:0;">
            <div class="situation-text"><strong>15. Mrs. Lindner:</strong> Works remotely from home, suffers chronic back pain, and seeks a relaxing evening wellness class on Tuesdays or Thursdays.</div>
            <div class="match-box">[ &nbsp; ]</div>
          </div>
        </div>

        <!-- Course Offers A-G -->
        <div class="course-list">
          <div style="font-size:9.5px; font-weight:800; color:#0f2b48; margin-bottom:1px;">Course Offerings:</div>
          <div class="course-item"><span class="course-letter">A</span> <span class="course-title">Confident Public Speaking – Rhetoric &amp; Presentation:</span> Voice coaching, stage fright reduction. Wednesdays, 18:00–21:00 (3 sessions).</div>
          <div class="course-item"><span class="course-letter">B</span> <span class="course-title">Business English – Evening Masterclass (B2):</span> Professional fluency. Mondays &amp; Wednesdays, 19:00–20:30 over 12 weeks.</div>
          <div class="course-item"><span class="course-letter">C</span> <span class="course-title">Advanced MS Excel for Financial Data:</span> Formulas, pivot tables &amp; analysis. Weekend Intensive: Sat &amp; Sun, 09:00–16:30.</div>
          <div class="course-item"><span class="course-letter">D</span> <span class="course-title">Workplace Conflict Management:</span> Mediate disputes constructively and reach fair solutions as a leader. Friday, 09:00–17:00.</div>
          <div class="course-item"><span class="course-letter">E</span> <span class="course-title">Fit &amp; Pain-Free at Your Desk:</span> Targeted back exercises &amp; relaxation for office workers. Tuesdays, 18:30–20:00.</div>
          <div class="course-item"><span class="course-letter">F</span> <span class="course-title">Remote IT Security &amp; Data Privacy:</span> Technical hands-on workshop for network admins. Thursday, 14:00–18:00.</div>
          <div class="course-item"><span class="course-letter">G</span> <span class="course-title">Accounting for Startups &amp; Entrepreneurs:</span> Invoicing, taxes, and bookkeeping rules. Saturday, 10:00–15:00.</div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Part 1: Reading</span>
      <span class="footer-page">Page 3 of 8</span>
    </div>
  </div>


  <!-- ==================== PAGE 4: PART 2 – LISTENING ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">English Certificate B1 &bull; Final Examination</span>
        <span class="cand-tag">Candidate: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>PART 2: LISTENING COMPREHENSION</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Duration: 30 Min.</span>
          <span class="module-badge">Max. 25 Points</span>
        </div>
      </div>

      <div class="audio-notice">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
        </svg>
        <span>Note: Audio passages will be read aloud or played by examiners. Mark your answers directly while listening.</span>
      </div>

      <!-- Task 1 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>TASK 1: SHORT ANNOUNCEMENTS &amp; MESSAGES (Listen ONCE)</span>
          <span style="color:#2563eb;">10 Points (2 points per question)</span>
        </div>
        <div class="task-box-desc">
          You will hear five short announcements on the telephone or radio. You will hear each text <strong>ONCE</strong>. Choose the correct answer (a, b, or c).
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 6px;">
        <div class="question-item">
          <div class="question-text">16. What must Mrs. Schneider do before coming to the clinic tomorrow?</div>
          <div class="options-group">
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Call to reschedule her appointment because the doctor is ill.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Bring her new health insurance card and current medication list.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Arrive thirty minutes later than originally scheduled.</div>
          </div>
        </div>

        <div class="question-item">
          <div class="question-text">17. Why is the regional train RB 42 not reaching Central Station?</div>
          <div class="options-group">
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Urgent repair works on a railway bridge following storm damage.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> A city-wide strike by regional railway personnel.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> A defective locomotive blocking the approach platform.</div>
          </div>
        </div>

        <div class="question-item">
          <div class="question-text">18. What weather is forecast for the southern region this weekend?</div>
          <div class="options-group">
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Continuous sunny weather throughout with highs above 25°C.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Heavy unexpected snowfall down to valley levels.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Warm on Saturday, followed by storms and cooler air Sunday.</div>
          </div>
        </div>

        <div class="question-item">
          <div class="question-text">19. Why is the furniture store representative calling Mr. Albers?</div>
          <div class="options-group">
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> The dining table and chairs can be delivered early this Friday.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> The chairs were damaged during transit and must be re-ordered.</div>
            <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> Mr. Albers needs to transfer the remaining invoice balance first.</div>
          </div>
        </div>
      </div>

      <div class="question-item" style="margin-bottom: 6px;">
        <div class="question-text">20. What must visitors remember if visiting the City Museum this Sunday?</div>
        <div class="options-group-horizontal">
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">a)</span> Museum admission is completely free for all visitors on Sunday.</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">b)</span> Due to the City Marathon, cars cannot access the museum (use Subway Line 4).</div>
          <div class="option-label"><span class="checkbox-box"></span><span class="option-code">c)</span> The second-floor special exhibition closes early at 14:00.</div>
        </div>
      </div>

      <!-- Task 2 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>TASK 2: RADIO INTERVIEW (Apprenticeship or University? – Listen TWICE)</span>
          <span style="color:#2563eb;">10 Points (2 points per question)</span>
        </div>
        <div class="task-box-desc">
          Interview with career consultant Thomas Richter. You will hear the dialogue <strong>TWICE</strong>. Mark: <strong>True [ T ]</strong> or <strong>False [ F ]</strong>.
        </div>
      </div>

      <table class="rf-table" style="margin-bottom: 6px;">
        <thead>
          <tr>
            <th>Statement regarding the radio interview</th>
            <th class="rf-check-cell">True</th>
            <th class="rf-check-cell">False</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>21.</strong> Mr. Richter says that nearly 80 percent of school leavers today choose to pursue a university degree.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>22.</strong> Many university students drop out because they had inaccurate expectations regarding academic theory and self-discipline.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>23.</strong> According to Mr. Richter, skilled tradespeople always earn substantially less than university graduates.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>24.</strong> A “dual study programme” combines practical employment in a company with university lectures.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>25.</strong> Mr. Richter urges parents to push their children toward whatever career offers the greatest social prestige.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
        </tbody>
      </table>

      <!-- Task 3 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>TASK 3: WORKPLACE CONVERSATION (Annual Company Outing – Listen ONCE)</span>
          <span style="color:#2563eb;">5 Points (1 point per question)</span>
        </div>
        <div class="task-box-desc">
          Conversation between colleagues Anna and David. You will hear the conversation <strong>ONCE</strong>. Who says what? Mark: <strong>Anna [ A ]</strong>, <strong>David [ D ]</strong>, or <strong>Both [ B ]</strong>.
        </div>
      </div>

      <table class="rf-table">
        <thead>
          <tr>
            <th>Statement in the conversation</th>
            <th class="rf-check-cell">Anna [A]</th>
            <th class="rf-check-cell">David [D]</th>
            <th class="rf-check-cell">Both [B]</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>26.</strong> Last year’s mountain hike was an unpleasant experience because of bad weather and heavy rain.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>27.</strong> A cooking masterclass for the whole team fosters closer collaboration than simply having dinner in a restaurant.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>28.</strong> The company budget of 50 Euros per person is not enough to cover an evening boat cruise with a full buffet.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>29.</strong> The outing should take place on a working Friday rather than asking employees to give up their Saturday.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
          <tr>
            <td><strong>30.</strong> They should submit two different proposals to the boss so the entire department can vote via email.</td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
            <td class="rf-check-cell"><span class="rf-box"></span></td>
          </tr>
        </tbody>
      </table>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Part 2: Listening</span>
      <span class="footer-page">Page 4 of 8</span>
    </div>
  </div>


  <!-- ==================== PAGE 5: PART 3 – LANGUAGE IN USE ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">English Certificate B1 &bull; Final Examination</span>
        <span class="cand-tag">Candidate: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>PART 3: LANGUAGE IN USE (GRAMMAR &amp; VOCABULARY)</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Duration: 25 Min.</span>
          <span class="module-badge">Max. 15 Points</span>
        </div>
      </div>

      <!-- Task 1 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>TASK 1: FORMAL CLOZE TEXT (INSURANCE CLAIM)</span>
          <span style="color:#2563eb;">7.5 Points (0.75 points per gap)</span>
        </div>
        <div class="task-box-desc">
          Read the following formal notification letter and select the grammatically appropriate word for each gap (31–40).
        </div>
      </div>

      <div class="article-card" style="margin-bottom: 6px; padding: 7px 10px;">
        <p style="font-size:9.3px; line-height: 1.4;">
          <strong>Dear Sir or Madam,</strong><br>
          I am writing to formally report an incident of water damage, <strong>(31)</strong> occurred last Tuesday in my rented apartment. When I returned home from work at approximately 6:00 p.m., I discovered <strong>(32)</strong> water had overflowed from the kitchen dishwasher. <strong>(33)</strong> I turned off the main shut-off valve immediately, water had already penetrated under <strong>(34)</strong> newly installed parquet floor in the corridor. The flooring, which <strong>(35)</strong> fitted just two years ago, has warped <strong>(36)</strong> and must now be replaced by a licensed contractor. I notified my landlord that very evening <strong>(37)</strong> inspect the extent of the damage. He advised me to get in touch with <strong>(38)</strong> insurance provider without delay. <strong>(39)</strong> it be possible for you to dispatch an insurance assessor this week? I will forward the contractor’s formal quote <strong>(40)</strong> I receive it.<br>
          <strong>Yours faithfully, Martin Brenner</strong>
        </p>
      </div>

      <!-- Multiple-Choice Grid for 31-40 -->
      <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; margin-bottom: 8px;">
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Gap 31:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) whom</div>
            <div>[ ] b) which</div>
            <div>[ ] c) whose</div>
            <div>[ ] d) what</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Gap 32:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) whether</div>
            <div>[ ] b) because</div>
            <div>[ ] c) that</div>
            <div>[ ] d) when</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Gap 33:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) Despite</div>
            <div>[ ] b) Although</div>
            <div>[ ] c) Because of</div>
            <div>[ ] d) During</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Gap 34:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) an</div>
            <div>[ ] b) a</div>
            <div>[ ] c) the</div>
            <div>[ ] d) these</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Gap 35:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) was</div>
            <div>[ ] b) has</div>
            <div>[ ] c) is</div>
            <div>[ ] d) been</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Gap 36:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) severely</div>
            <div>[ ] b) severe</div>
            <div>[ ] c) more severe</div>
            <div>[ ] d) severity</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Gap 37:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) so that</div>
            <div>[ ] b) in order to</div>
            <div>[ ] c) for</div>
            <div>[ ] d) unless</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Gap 38:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) my</div>
            <div>[ ] b) mine</div>
            <div>[ ] c) me</div>
            <div>[ ] d) myself</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Gap 39:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) Would</div>
            <div>[ ] b) Should</div>
            <div>[ ] c) Were</div>
            <div>[ ] d) Could</div>
          </div>
        </div>
        <div class="question-item" style="padding:4px 6px;">
          <div style="font-weight:800; color:#0f2b48; font-size:9px;">Gap 40:</div>
          <div class="options-group" style="font-size:8.5px;">
            <div>[ ] a) as soon as</div>
            <div>[ ] b) since</div>
            <div>[ ] c) before</div>
            <div>[ ] d) until</div>
          </div>
        </div>
      </div>

      <!-- Task 2 -->
      <div class="task-box">
        <div class="task-box-title">
          <span>TASK 2: COMPLEX B1 GRAMMATICAL STRUCTURES</span>
          <span style="color:#2563eb;">7.5 Points (0.75 points per question)</span>
        </div>
        <div class="task-box-desc">
          Choose the grammatically and semantically correct option (a, b, c, or d) to complete sentences 41 to 50.
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>41.</strong> The woman _______ handbag was stolen at the sidewalk café notified the police immediately.<br>
          <span style="color:#475569;">[ ] a) who &nbsp; [ ] b) which &nbsp; [ ] c) whose &nbsp; [ ] d) whom</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>42.</strong> _______ asking a local resident for directions, my brother drove around lost for nearly two hours.<br>
          <span style="color:#475569;">[ ] a) Without &nbsp; [ ] b) Instead of &nbsp; [ ] c) In order to &nbsp; [ ] d) Despite of</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>43.</strong> In our corporate department, all supplier invoices _______ verified electronically before payment.<br>
          <span style="color:#475569;">[ ] a) must be &nbsp; [ ] b) are been &nbsp; [ ] c) have to &nbsp; [ ] d) should be to</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>44.</strong> Have you already introduced yourself to the new _______ from the international marketing team?<br>
          <span style="color:#475569;">[ ] a) colleague &nbsp; [ ] b) colleague's &nbsp; [ ] c) colleagues &nbsp; [ ] d) collegial</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>45.</strong> _______ more frequently you practice speaking, _______ quicker you overcome linguistic hesitation.<br>
          <span style="color:#475569;">[ ] a) Both / and &nbsp; [ ] b) Either / or &nbsp; [ ] c) The / the &nbsp; [ ] d) Not only / but</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>46.</strong> If I _______ in your position, I _______ accept such unfavorable contract conditions without negotiation.<br>
          <span style="color:#475569;">[ ] a) am / will not &nbsp; [ ] b) were / would not &nbsp; [ ] c) had been / will not &nbsp; [ ] d) would be / do not</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>47.</strong> We were delighted _______ your recent inquiry and look forward _______ developing a productive partnership.<br>
          <span style="color:#475569;">[ ] a) for / on &nbsp; [ ] b) about / in &nbsp; [ ] c) with / to &nbsp; [ ] d) by / toward</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>48.</strong> After the bilateral agreement _______ by both executives, the project officially commenced.<br>
          <span style="color:#475569;">[ ] a) had been signed &nbsp; [ ] b) was signing &nbsp; [ ] c) has been signed &nbsp; [ ] d) would be signed</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>49.</strong> Passengers were instructed to keep their seatbelts fastened throughout _______ entire transatlantic flight.<br>
          <span style="color:#475569;">[ ] a) a &nbsp; [ ] b) an &nbsp; [ ] c) the &nbsp; [ ] d) of</span>
        </div>

        <div class="question-item" style="padding:3px 6px; font-size:8.7px;">
          <strong>50.</strong> It is no longer mandatory _______ the application in person; candidates can submit documentation online.<br>
          <span style="color:#475569;">[ ] a) submit &nbsp; [ ] b) for submit &nbsp; [ ] c) to submit &nbsp; [ ] d) submitting</span>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Part 3: Language in Use</span>
      <span class="footer-page">Page 5 of 8</span>
    </div>
  </div>


  <!-- ==================== PAGE 6: PART 4 – WRITING (TASK 1) ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">English Certificate B1 &bull; Final Examination</span>
        <span class="cand-tag">Candidate: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>PART 4: WRITING (WRITTEN EXPRESSION)</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Total Duration: 50 Min.</span>
          <span class="module-badge">Max. 20 Points (2 x 10 Pts.)</span>
        </div>
      </div>

      <!-- Task 1 Box -->
      <div class="writing-meta-card">
        <div class="task-box-title" style="margin-bottom: 4px;">
          <span>TASK 1: FORMAL COMPLAINT EMAIL / LETTER</span>
          <span style="color:#2563eb;">10 Points &bull; Recommended Time: ~25 Min. &bull; Word Count: ~80–100 words</span>
        </div>
        <div class="writing-meta-grid">
          <div style="font-size:9.2px; line-height: 1.35; color:#1e293b;">
            <strong>Situation:</strong> Two weeks ago, you purchased a premium espresso machine (Model: <em>“Barista Pro”</em>, Order Reference: <strong>TW-9941</strong>) for <strong>£249 / 249€</strong> from the online retailer <em>“TechWorld Ltd”</em>. After three days of normal use, the appliance malfunctioned (it no longer heats water). Your initial complaint email sent last week received no response.<br>
            Write a formal, assertive complaint email addressing all four guiding points.
          </div>
          <div class="points-checklist">
            <div class="points-checklist-title">Required Content Points:</div>
            <ul>
              <li><strong>1. Purpose of writing</strong> (purchase date, model, order ref.)</li>
              <li><strong>2. Problem description</strong> &amp; mention of unanswered first email</li>
              <li><strong>3. Clear remedy demanded:</strong> free replacement or full refund</li>
              <li><strong>4. Set a firm deadline</strong> (e.g., 7 days) &amp; mention legal/consumer steps</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Ruled Response Sheet (13 lines) -->
      <div class="ruled-sheet">
        <div style="font-size:8.5px; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:2px;">
          Answer Sheet Task 1 (Formal Complaint Email):
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

      <!-- Examiner Evaluation Box -->
      <div class="examiner-eval-box">
        <div class="examiner-eval-title">FOR EXAMINERS ONLY (TASK 1 EVALUATION):</div>
        <div class="eval-cells">
          <div class="eval-cell">
            <div class="eval-cell-label">Content Points (4P)</div>
            <div class="eval-cell-val">___ / 4</div>
          </div>
          <div class="eval-cell">
            <div class="eval-cell-label">Coherence &amp; Style (3P)</div>
            <div class="eval-cell-val">___ / 3</div>
          </div>
          <div class="eval-cell">
            <div class="eval-cell-label">Grammar &amp; Vocab (3P)</div>
            <div class="eval-cell-val">___ / 3</div>
          </div>
          <div class="eval-cell" style="background:#eff6ff; border-color:#2563eb;">
            <div class="eval-cell-label" style="color:#1e3a8a;">Total Task 1</div>
            <div class="eval-cell-val" style="color:#1e3a8a;">___ / 10</div>
          </div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Part 4: Writing (Task 1)</span>
      <span class="footer-page">Page 6 of 8</span>
    </div>
  </div>


  <!-- ==================== PAGE 7: PART 4 – WRITING (TASK 2) ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">English Certificate B1 &bull; Final Examination</span>
        <span class="cand-tag">Candidate: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>PART 4: WRITING &bull; TASK 2</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Recommended Time: ~25 Min.</span>
          <span class="module-badge">Max. 10 Points</span>
        </div>
      </div>

      <!-- Task 2 Box -->
      <div class="writing-meta-card">
        <div class="task-box-title" style="margin-bottom: 4px;">
          <span>TASK 2: OPINION ESSAY / DISCUSSION FORUM CONTRIBUTION</span>
          <span style="color:#2563eb;">10 Points &bull; Word Count: ~100–120 words</span>
        </div>
        <div class="writing-meta-grid">
          <div style="font-size:9.2px; line-height: 1.35; color:#1e293b;">
            <strong>Situation:</strong> You read an online article debating <em>“Working from Home or Returning to the Office?”</em>. The author claims provocatively that remote employees work less diligently, become lazy, and that team spirit is completely lost when people do not share a physical office.<br>
            Write a balanced, structured contribution expressing your perspective in the readers' forum.
          </div>
          <div class="points-checklist">
            <div class="points-checklist-title">Required Content Points:</div>
            <ul>
              <li><strong>Personal Opinion:</strong> State your position on the author's claim.</li>
              <li><strong>Balanced Arguments:</strong> Present at least <strong>two advantages</strong> and <strong>two disadvantages</strong> of remote work.</li>
              <li><strong>Constructive Compromise:</strong> Propose a <strong>practical compromise</strong> fair to both employers and staff.</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Ruled Response Sheet (13 lines) -->
      <div class="ruled-sheet">
        <div style="font-size:8.5px; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:2px;">
          Answer Sheet Task 2 (Discussion Forum / Opinion Essay):
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

      <!-- Examiner Evaluation Box -->
      <div class="examiner-eval-box">
        <div class="examiner-eval-title">FOR EXAMINERS ONLY (TASK 2 EVALUATION):</div>
        <div class="eval-cells">
          <div class="eval-cell">
            <div class="eval-cell-label">Opinion &amp; Arguments (4P)</div>
            <div class="eval-cell-val">___ / 4</div>
          </div>
          <div class="eval-cell">
            <div class="eval-cell-label">Connectors / Style (3P)</div>
            <div class="eval-cell-val">___ / 3</div>
          </div>
          <div class="eval-cell">
            <div class="eval-cell-label">Vocabulary &amp; Accuracy (3P)</div>
            <div class="eval-cell-val">___ / 3</div>
          </div>
          <div class="eval-cell" style="background:#eff6ff; border-color:#2563eb;">
            <div class="eval-cell-label" style="color:#1e3a8a;">Total Task 2</div>
            <div class="eval-cell-val" style="color:#1e3a8a;">___ / 10</div>
          </div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Part 4: Writing (Task 2)</span>
      <span class="footer-page">Page 7 of 8</span>
    </div>
  </div>


  <!-- ==================== PAGE 8: PART 5 – SPEAKING ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">English Certificate B1 &bull; Final Examination</span>
        <span class="cand-tag">Candidate: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="module-header">
        <div class="module-title">
          <span>PART 5: SPEAKING (ORAL EXPRESSION &amp; INTERACTION)</span>
        </div>
        <div class="module-meta">
          <span class="module-badge">Preparation: 10 Min.</span>
          <span class="module-badge">Exam Duration: ~15 Min.</span>
          <span class="module-badge">Max. 15 Points</span>
        </div>
      </div>

      <div class="task-box">
        <div class="task-box-title">
          <span>ORAL EXAMINATION PROCEDURES &amp; GUIDELINES</span>
          <span style="color:#2563eb;">Paired Examination or Individual Interview with Examiners</span>
        </div>
        <div class="task-box-desc">
          The speaking test comprises two distinct parts. During your 10-minute supervised preparation, you may write brief bullet points on scrap paper. Speak fluently, avoid reading verbatim, and engage actively with questions.
        </div>
      </div>

      <div class="oral-grid">
        <!-- Part 5A -->
        <div class="oral-card">
          <div>
            <div class="oral-card-header">
              <span>PART 5A: INDIVIDUAL PRESENTATION</span>
              <span style="color:#2563eb;">7.5 Points (~4–5 Min.)</span>
            </div>
            <div class="oral-topic">Topic: “Social Media (Instagram, TikTok, LinkedIn): Blessing or Curse?”</div>
            <div style="font-size:9px; font-weight:700; color:#0f2b48; margin-bottom:3px;">Structure your presentation following these steps:</div>
            <ul>
              <li><strong>1. Introduction:</strong> Introduce the topic and describe your personal habits and daily experience with social networks.</li>
              <li><strong>2. Situation in Home Country:</strong> How are social platforms used in Morocco? What role do they play among youth and businesses?</li>
              <li><strong>3. Advantages &amp; Disadvantages:</strong> Discuss at least two specific benefits (e.g. global networking) and two drawbacks (screen addiction, privacy).</li>
              <li><strong>4. Conclusion &amp; Recommendation:</strong> Summarize your final stance and answer follow-up questions from the examiners.</li>
            </ul>
          </div>
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:4px 6px; font-size:8px; color:#64748b;">
            Tip: Use structuring discourse markers (<em>“To begin with...”, “On the one hand..., on the other hand...”, “In my honest opinion...”</em>).
          </div>
        </div>

        <!-- Part 5B -->
        <div class="oral-card">
          <div>
            <div class="oral-card-header">
              <span>PART 5B: COLLABORATIVE PROBLEM-SOLVING</span>
              <span style="color:#2563eb;">7.5 Points (~6 Min.)</span>
            </div>
            <div class="oral-topic">Scenario: Planning a Surprise Graduation Weekend for a Close Friend</div>
            <div style="font-size:9px; font-weight:700; color:#0f2b48; margin-bottom:3px;">Negotiate and plan together with your partner / examiner:</div>
            <ul>
              <li><strong>Destination &amp; Lodging:</strong> Coastal beach camping, a mountain cabin in the Atlas, or a city boutique hotel?</li>
              <li><strong>Transport &amp; Mobility:</strong> Booking train tickets, renting minivans, or organizing carpools among friends?</li>
              <li><strong>Budget &amp; Costs:</strong> What total budget per person is realistic for 15 friends? Who covers the graduate's portion?</li>
              <li><strong>Task Allocation:</strong> Who handles bookings, who buys food and supplies, and who distracts the friend until the surprise?</li>
            </ul>
          </div>
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:4px 6px; font-size:8px; color:#64748b;">
            Tip: Make constructive suggestions, listen to your partner's counterarguments, and negotiate an agreeable compromise.
          </div>
        </div>
      </div>

      <!-- Official Examiner Oral Assessment Protocol -->
      <div style="background:#ffffff; border:1.5px solid #0f2b48; border-radius:6px; padding:8px 12px; margin-top:2px;">
        <div style="font-size:10px; font-weight:800; color:#0f2b48; text-transform:uppercase; margin-bottom:5px; border-bottom:1px solid #e2e8f0; padding-bottom:3px; display:flex; justify-content:space-between;">
          <span>OFFICIAL EXAMINER PROTOCOL &ndash; ORAL SPEAKING MODULE</span>
          <span style="color:#2563eb;">Candidate: ANASS BENYAHIA</span>
        </div>
        <table class="score-table" style="margin-bottom:6px; font-size:9px;">
          <thead>
            <tr>
              <th>Evaluation Criteria</th>
              <th class="center" style="width:25%;">Part 5A (Presentation)</th>
              <th class="center" style="width:25%;">Part 5B (Negotiation)</th>
              <th class="center" style="width:20%;">Overall Impression</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>1. Task Fulfillment, Discourse &amp; Coherence</td>
              <td class="center">_____ / 2.5 P.</td>
              <td class="center">_____ / 2.5 P.</td>
              <td class="center">_____ / 5.0 P.</td>
            </tr>
            <tr>
              <td>2. Fluency, Pronunciation &amp; Intonation</td>
              <td class="center">_____ / 2.5 P.</td>
              <td class="center">_____ / 2.5 P.</td>
              <td class="center">_____ / 5.0 P.</td>
            </tr>
            <tr>
              <td>3. Lexical Range &amp; Grammatical Accuracy (B1)</td>
              <td class="center">_____ / 2.5 P.</td>
              <td class="center">_____ / 2.5 P.</td>
              <td class="center">_____ / 5.0 P.</td>
            </tr>
            <tr class="total-row">
              <td><strong>TOTAL PART 5 (ORAL SPEAKING SCORE)</strong></td>
              <td class="center"><strong>_____ / 7.5 P.</strong></td>
              <td class="center"><strong>_____ / 7.5 P.</strong></td>
              <td class="center"><strong>_____ / 15.0 P.</strong></td>
            </tr>
          </tbody>
        </table>

        <div style="display:flex; justify-content:space-between; align-items:center; font-size:8.5px; color:#475569; margin-top:4px;">
          <div>Examiner 1 (Name &amp; Signature): ___________________________</div>
          <div>Examiner 2 (Name &amp; Signature): ___________________________</div>
          <div>Date: 16.10.2026</div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Part 5: Speaking</span>
      <span class="footer-page">Page 8 of 8</span>
    </div>
  </div>

</body>
</html>
"""
    return html

def build_examiner_guide_html():
    logo_b64 = get_logo_b64()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>English Certificate B1 – Examiner's Guide &amp; Solution Key</title>
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
    color: #c8102e;
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

  /* British / International Stripe Bar */
  .flag-bar {{
    display: flex;
    height: 4px;
    width: 100%;
    margin-bottom: 8px;
    border-radius: 2px;
    overflow: hidden;
  }}
  .flag-bar .bar-navy {{ background: #0f2b48; flex: 2; }}
  .flag-bar .bar-red {{ background: #c8102e; flex: 1; }}
  .flag-bar .bar-blue {{ background: #1d4ed8; flex: 2; }}

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
    color: #c8102e;
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
    background: #c8102e;
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

  <!-- ==================== EXAMINER PAGE 1: AUDIO SCRIPTS (TASK 1) ==================== -->
  <div class="exam-page">
    <div>
      <div class="cover-header">
        <div>
          <div class="cover-inst-title">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</div>
          <div class="cover-inst-sub">EXAMINATION BOARD &bull; ENGLISH B1 CERTIFICATE</div>
          <div class="cover-inst-contact">Authorization N° 22-200/2020 &bull; Deroua | Official Examiner's Handbook &amp; Solution Key</div>
        </div>
        <img src="data:image/png;base64,{logo_b64}" class="cover-logo-img" alt="ILAS Logo">
      </div>

      <div class="flag-bar" style="margin-top: 6px;">
        <div class="bar-navy"></div>
        <div class="bar-red"></div>
        <div class="bar-blue"></div>
      </div>

      <div class="examiner-banner">
        <div>
          <div style="font-size:13px; font-weight:900;">EXAMINER'S HANDBOOK (EXAMINATEUR) &bull; B1</div>
          <div style="font-size:9.5px; opacity:0.9;">Audio Transcripts, Master Answer Keys &amp; Assessment Descriptors</div>
        </div>
        <span class="examiner-badge">STRICTLY CONFIDENTIAL</span>
      </div>

      <div class="candidate-ref-bar">
        <span>Assigned Candidate: <strong>ANASS BENYAHIA</strong></span>
        <span>Date of Birth: <strong>26.01.2007</strong></span>
        <span>National ID / CIN: <strong>WB226817</strong></span>
        <span>Date: <strong>16.10.2026</strong></span>
      </div>

      <div class="section-title">1. AUDIO TRANSCRIPTS (FOR PART 2: LISTENING)</div>
      <div style="font-size:8.8px; color:#475569; margin-bottom:6px; font-style:italic;">
        Instructions for Examiners: Read these transcripts aloud at a natural, steady pace, or play the recorded audio files. Observe the reading frequency indicated (1x or 2x).
      </div>

      <div style="font-size:10px; font-weight:800; color:#0f2b48; margin-bottom:4px;">
        TASK 1: SHORT ANNOUNCEMENTS (Read each text ONCE &bull; Questions 16 to 20)
      </div>

      <div class="audio-item">
        <div class="audio-num">Number 16 (Dr. Keller’s Dental Clinic):</div>
        <div class="audio-text">
          “Good morning, Mrs. Schneider. This is Sabine Neumann calling from Dr. Keller’s dental practice. I am calling to confirm your routine check-up appointment tomorrow morning at 9:00 a.m. The appointment will go ahead as scheduled, but since we recently upgraded to a new digital management system, we kindly request that you bring your new electronic health insurance card. In addition, Dr. Keller asked me to remind you to bring an updated list of any medications you are currently taking. Thank you very much, and we will see you tomorrow!”
        </div>
      </div>

      <div class="audio-item">
        <div class="audio-num">Number 17 (Station Announcement &ndash; Regional Train RB 42):</div>
        <div class="audio-text">
          “Attention, passengers on regional train RB 42 bound for Neustadt Central Station: Due to severe storm damage that occurred overnight, the railway bridge between South Square and East Station must undergo urgent structural inspection and repairs. Consequently, this service will terminate unscheduled at East Station today. For passengers continuing towards Central Station, please transfer to the rail replacement shuttle buses waiting directly outside on the station forecourt.”
        </div>
      </div>

      <div class="audio-item">
        <div class="audio-num">Number 18 (Regional Weekend Weather Forecast):</div>
        <div class="audio-text">
          “And now, here is the weekend weather outlook for the southern region: Be sure to take full advantage of Saturday for any outdoor excursions! With widespread sunshine, afternoon temperatures will comfortably reach a pleasant 24 degrees Celsius. Sunday morning will remain dry at first, but by early afternoon, thick clouds will roll in from the west. Expect heavy thunderstorms, downpours, and gusty winds, accompanied by a sharp drop in temperatures to just 13 degrees.”
        </div>
      </div>

      <div class="audio-item">
        <div class="audio-num">Number 19 (Dream-Home Furniture &ndash; Mr. Berger):</div>
        <div class="audio-text">
          “Hello, Mr. Albers. This is Berger calling from Dream-Home Furnishings regarding your order from last month: the large solid oak dining table and six matching leather chairs. Delivery was originally scheduled for next Wednesday. However, another client on our Friday delivery route had to cancel at short notice, which means our delivery team can now deliver your complete set this Friday between 10:00 a.m. and 1:00 p.m. Please give us a quick call back to confirm whether someone will be home.”
        </div>
      </div>

      <div class="audio-item" style="margin-bottom:0;">
        <div class="audio-num">Number 20 (City Museum Telephone Information Service):</div>
        <div class="audio-text">
          “Welcome to the automated information line of the City Museum. Our exhibitions are open Tuesday through Sunday from 10:00 a.m. to 6:00 p.m. Please take note of an important advisory for this Sunday: Due to the annual City Marathon, all access roads surrounding the museum district, as well as our visitor car park, will be strictly closed to vehicular traffic from 8:00 a.m. to 5:00 p.m. Visitors are strongly advised to travel by public transport via Subway Line 4. The museum galleries will be open as normal.”
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Examiner's Guide: Audio Transcripts (Task 1)</span>
      <span>Page 1 of 4</span>
    </div>
  </div>


  <!-- ==================== EXAMINER PAGE 2: AUDIO SCRIPTS (TASKS 2 & 3) ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">CONFIDENTIAL &bull; EXAMINER'S HANDBOOK B1</span>
        <span>Audio Transcripts Part 2 (Tasks 2 &amp; 3)</span>
      </div>

      <div style="font-size:10px; font-weight:800; color:#0f2b48; margin-bottom:4px;">
        TASK 2: RADIO INTERVIEW (Read dialogue TWICE &bull; Questions 21 to 25)
      </div>

      <div class="dialogue-box">
        <div class="speaker-line">
          <span class="speaker-name">Presenter:</span>
          “A very good morning to all our listeners on Radio Current Affairs! Final school certificates are around the corner, and hundreds of thousands of young people face a vital choice: should I head straight to university, or would I be better off pursuing practical vocational training in a business? Here in the studio to discuss this is professional career consultant Thomas Richter. Mr. Richter, is it still true that nearly everyone wants to study at university?”
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Thomas Richter:</span>
          “Good morning! Yes, societal pressure towards an academic degree remains extraordinarily high, even though it’s not quite 80 percent, but currently just over half of a school-leaving cohort that enrolls in university. The alarming issue, however, is that nearly 30 percent of students in undergraduate bachelor programmes drop out before completing their degrees.”
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Presenter:</span>
          “Why is that? Are young people today simply less resilient?”
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Thomas Richter:</span>
          “Not at all. The problem is that many enroll at university simply assuming it is a natural continuation of secondary school. They are then utterly shocked by how theoretical and abstract university education is, and by the enormous degree of self-organization required. Many discover only after two full semesters that they actually prefer practical, hands-on work where they can see a tangible outcome of their labor at the end of the day.”
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Presenter:</span>
          “Even so, many parents worry that a vocational apprenticeship means lower lifetime earnings.”
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Thomas Richter:</span>
          “That is an outdated prejudice! Look at skilled trades or technical fields today: someone who completes an apprenticeship as an electrician, heating engineer, or mechatronics technician and subsequently qualifies as a master craftsman often earns as much as or more than many university graduates – with virtually zero risk of unemployment. Moreover, apprentices earn an independent income from day one, whereas university graduates frequently enter the workforce carrying heavy student debts.”
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Presenter:</span>
          “And what advice do you offer to young people torn between academic theory and practical training?”
        </div>
        <div class="speaker-line">
          <span class="speaker-name">Thomas Richter:</span>
          “For them, a dual study programme is the ideal pathway. You sign an employment contract with a sponsoring firm and alternate every three months between practical workplace training and academic lectures at a partner college. It demands intense dedication, but offers outstanding career prospects. My foremost advice to parents is this: never pressure your child into university merely because the neighbor’s son is studying law or because it sounds prestigious. What truly matters is where the young person’s genuine talents and passions lie.”
        </div>
      </div>

      <div style="font-size:10px; font-weight:800; color:#0f2b48; margin-top:8px; margin-bottom:4px;">
        TASK 3: WORKPLACE CONVERSATION (Read conversation ONCE &bull; Questions 26 to 30)
      </div>

      <div class="dialogue-box">
        <div class="speaker-line"><span class="speaker-name">Anna:</span> “David, remember our manager asked us to gather ideas by Friday for our annual company outing in June? Have you had a chance to think about it?”</div>
        <div class="speaker-line"><span class="speaker-name">David:</span> “Yes, a bit. One thing is certain: we definitely shouldn't do a long mountain trek like last year! When the rain started in the afternoon, everyone got completely soaked and spirits hit rock bottom.”</div>
        <div class="speaker-line"><span class="speaker-name">Anna:</span> “You’re completely right. That rainy hike was a complete catastrophe; I hated it too! That’s why I was thinking of an indoor activity this time. How about a professional culinary workshop at a cooking school? Preparing a three-course dinner in small teams would allow us to get to know our new colleagues in accounting much better than merely sitting beside each other in a restaurant.”</div>
        <div class="speaker-line"><span class="speaker-name">David:</span> “Hmm, I’m not sure. Some colleagues don't enjoy cooking at all. I thought a relaxed riverboat cruise with an evening buffet on board would be far more laid-back.”</div>
        <div class="speaker-line"><span class="speaker-name">Anna:</span> “I actually looked into that exact boat idea yesterday online. The catch is our budget: the company covers a maximum of 50 Euros per employee. An evening cruise with dinner costs at least 68 Euros without drinks, so that’s unfortunately out of reach.”</div>
        <div class="speaker-line"><span class="speaker-name">David:</span> “What a pity! Yes, if it exceeds 50 Euros, finance definitely won't sign off on it. But on another note: don’t you think the trip should take place on a working Friday again? If we schedule it on a Saturday, half the team will decline because of family commitments.”</div>
        <div class="speaker-line"><span class="speaker-name">Anna:</span> “Actually, I wouldn't mind Saturday since there's no rush. But you know what? Why don't we put down your idea of a shorter afternoon river cruise without dinner alongside my cooking workshop proposal? We can submit both options to management and let the team vote by email.”</div>
        <div class="speaker-line"><span class="speaker-name">David:</span> “Perfect, let’s do that! Having the team vote is by far the fairest solution.”</div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Examiner's Guide: Audio Transcripts (Tasks 2 &amp; 3)</span>
      <span>Page 2 of 4</span>
    </div>
  </div>


  <!-- ==================== EXAMINER PAGE 3: SOLUTION KEY ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">CONFIDENTIAL &bull; EXAMINER'S HANDBOOK B1</span>
        <span>Official Master Solution Key (Parts 1 to 3)</span>
      </div>

      <div class="section-title">2. OFFICIAL MASTER ANSWER KEY &amp; GRADING GRIDS</div>

      <!-- Part 1: Reading -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-bottom:3px;">
        PART 1: READING (Total: 25 Points)
      </div>
      <table class="key-table">
        <thead>
          <tr>
            <th style="width:25%;">Section</th>
            <th style="width:20%;">Points</th>
            <th>Correct Answers &amp; Rationale</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Task 1:</strong> Business Article</td>
            <td>10 P. (5 x 2 P.)</td>
            <td>
              <strong>1. b</strong> (fewer hours with same wage) &bull; 
              <strong>2. c</strong> (severe skilled labor shortage) &bull; 
              <strong>3. b</strong> (longer shifts over 4 days, Friday emergency team) &bull; 
              <strong>4. a</strong> (less absenteeism, higher hourly productivity) &bull; 
              <strong>5. b</strong> (essential public services cannot simply compress time)
            </td>
          </tr>
          <tr>
            <td><strong>Task 2:</strong> Readers' Opinions</td>
            <td>10 P. (5 x 2 P.)</td>
            <td>
              <strong>6. True [T]</strong> &bull; 
              <strong>7. False [F]</strong> &bull; 
              <strong>8. False [F]</strong> &bull; 
              <strong>9. True [T]</strong> &bull; 
              <strong>10. False [F]</strong> (tradespeople and residents free)
            </td>
          </tr>
          <tr>
            <td><strong>Task 3:</strong> Course Matching</td>
            <td>5 P. (5 x 1 P.)</td>
            <td>
              <strong>11. C</strong> (MS Excel Weekend Intensive) &bull; 
              <strong>12. A</strong> (Public Speaking &amp; Rhetoric) &bull; 
              <strong>13. 0</strong> (No 4-week morning intensive Business English fits) &bull; 
              <strong>14. D</strong> (Workplace Conflict Management) &bull; 
              <strong>15. E</strong> (Desk Posture &amp; Pain Relief Tuesday Eve)
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Part 2: Listening -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-top:8px; margin-bottom:3px;">
        PART 2: LISTENING (Total: 25 Points)
      </div>
      <table class="key-table">
        <thead>
          <tr>
            <th style="width:25%;">Section</th>
            <th style="width:20%;">Points</th>
            <th>Correct Answers &amp; Rationale</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Task 1:</strong> Announcements</td>
            <td>10 P. (5 x 2 P.)</td>
            <td>
              <strong>16. b</strong> (insurance card &amp; medication list) &bull; 
              <strong>17. a</strong> (railway bridge storm damage) &bull; 
              <strong>18. c</strong> (sunny Sat 24°C, stormy cooler Sun 13°C) &bull; 
              <strong>19. a</strong> (early delivery on Friday) &bull; 
              <strong>20. b</strong> (car access blocked due to Marathon; use Subway 4)
            </td>
          </tr>
          <tr>
            <td><strong>Task 2:</strong> Radio Interview</td>
            <td>10 P. (5 x 2 P.)</td>
            <td>
              <strong>21. False [F]</strong> (just over half, not 80%) &bull; 
              <strong>22. True [T]</strong> &bull; 
              <strong>23. False [F]</strong> (master craftsmen frequently out-earn academics) &bull; 
              <strong>24. True [T]</strong> &bull; 
              <strong>25. False [F]</strong> (parents should focus on talents, not prestige)
            </td>
          </tr>
          <tr>
            <td><strong>Task 3:</strong> Workplace Dialogue</td>
            <td>5 P. (5 x 1 P.)</td>
            <td>
              <strong>26. Both [B]</strong> (both agree last year's rainy hike was awful) &bull; 
              <strong>27. Anna [A]</strong> (cooking workshop fosters teamwork) &bull; 
              <strong>28. Both [B]</strong> (50€ budget vs 68€ cruise cost) &bull; 
              <strong>29. David [D]</strong> (prefers Friday to avoid Saturday family conflicts) &bull; 
              <strong>30. Both [B]</strong> (both agree to present dual option for team vote)
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Part 3: Language in Use -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-top:8px; margin-bottom:3px;">
        PART 3: LANGUAGE IN USE (Total: 15 Points &bull; 20 Questions x 0.75 Points)
      </div>
      <table class="key-table">
        <thead>
          <tr>
            <th style="width:25%;">Section</th>
            <th style="width:20%;">Points</th>
            <th>Answers (Keys 31 to 50)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Task 1:</strong> Cloze Text (31–40)</td>
            <td>7.5 P. (10 x 0.75 P.)</td>
            <td>
              <strong>31. b</strong> (which) &bull; <strong>32. c</strong> (that) &bull; <strong>33. b</strong> (Although) &bull; <strong>34. c</strong> (the) &bull; <strong>35. a</strong> (was)<br>
              <strong>36. a</strong> (severely) &bull; <strong>37. b</strong> (in order to) &bull; <strong>38. a</strong> (my) &bull; <strong>39. a</strong> (Would) &bull; <strong>40. a</strong> (as soon as)
            </td>
          </tr>
          <tr>
            <td><strong>Task 2:</strong> B1 Structures (41–50)</td>
            <td>7.5 P. (10 x 0.75 P.)</td>
            <td>
              <strong>41. c</strong> (whose - relative possessive) &bull; <strong>42. b</strong> (Instead of - preposition + gerund) &bull; <strong>43. a</strong> (must be - modal passive)<br>
              <strong>44. a</strong> (colleague - noun singular) &bull; <strong>45. c</strong> (The / the - correlative comparative) &bull; <strong>46. b</strong> (were / would not - 2nd conditional)<br>
              <strong>47. c</strong> (with / to - prepositional complements) &bull; <strong>48. a</strong> (had been signed - past perfect passive)<br>
              <strong>49. c</strong> (the - definite article) &bull; <strong>50. c</strong> (to submit - infinitive after necessary)
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Rapid Correction Cheat-sheet -->
      <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:4px; padding:6px 10px; font-size:8.5px; line-height:1.4;">
        <strong>Rapid Examiner Scoring Key (1–50):</strong><br>
        1.b | 2.c | 3.b | 4.a | 5.b | 6.T | 7.F | 8.F | 9.T | 10.F | 11.C | 12.A | 13.0 | 14.D | 15.E | 16.b | 17.a | 18.c | 19.a | 20.b | 21.F | 22.T | 23.F | 24.T | 25.F | 26.B | 27.A | 28.B | 29.D | 30.B | 31.b | 32.c | 33.b | 34.c | 35.a | 36.a | 37.b | 38.a | 39.a | 40.a | 41.c | 42.b | 43.a | 44.a | 45.c | 46.b | 47.c | 48.a | 49.c | 50.c
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Examiner's Guide: Master Key (Parts 1 to 3)</span>
      <span>Page 3 of 4</span>
    </div>
  </div>


  <!-- ==================== EXAMINER PAGE 4: ASSESSMENT DESCRIPTORS ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">CONFIDENTIAL &bull; EXAMINER'S HANDBOOK B1</span>
        <span>Assessment Criteria &amp; Grade Conversion Scale</span>
      </div>

      <div class="section-title">3. ASSESSMENT CRITERIA FOR WRITING &amp; SPEAKING</div>

      <!-- Writing Criteria -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-bottom:3px;">
        PART 4: WRITING (20 POINTS &bull; TASK 1: 10 PTS / TASK 2: 10 PTS)
      </div>
      <table class="key-table" style="font-size:9px;">
        <thead>
          <tr>
            <th style="width:28%;">Task</th>
            <th style="width:22%;">Points Allocation</th>
            <th>CEFR Level B1 Performance Descriptors</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Task 1:</strong> Formal Complaint Email (10 Pts.)</td>
            <td>
              &bull; Content Points: 4 Pts.<br>
              &bull; Coherence &amp; Style: 3 Pts.<br>
              &bull; Accuracy: 3 Pts.
            </td>
            <td>
              All 4 prompts (order details, defect, deadline, remedy demanded) clearly addressed. Formal salutation (<em>“Dear Sir or Madam”</em>) and complimentary close (<em>“Yours faithfully”</em>). Smooth linking with B1 cohesive devices (<em>“therefore”, “although”, “in addition”</em>). Generally accurate grammar.
            </td>
          </tr>
          <tr>
            <td><strong>Task 2:</strong> Opinion Forum Essay (10 Pts.)</td>
            <td>
              &bull; Arguments &amp; Stance: 4 Pts.<br>
              &bull; Connectors &amp; Flow: 3 Pts.<br>
              &bull; Vocabulary Range: 3 Pts.
            </td>
            <td>
              Clear statement of personal viewpoint. At least two advantages and two disadvantages of remote work explicitly articulated and substantiated. Realistic compromise proposed. Good range of everyday B1 vocabulary, logical paragraphing (intro, body, conclusion).
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Speaking Criteria -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-top:8px; margin-bottom:3px;">
        PART 5: SPEAKING (15 POINTS &bull; 5A: 7.5 PTS / 5B: 7.5 PTS)
      </div>
      <table class="key-table" style="font-size:9px;">
        <thead>
          <tr>
            <th style="width:28%;">Examination Area</th>
            <th style="width:22%;">Points Allocation</th>
            <th>Assessment Descriptors</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Part 5A:</strong> Presentation (Social Media)</td>
            <td>7.5 Points (~4–5 Min.)</td>
            <td>
              Clear structure (Introduction &rarr; Home Country Context &rarr; Pros/Cons &rarr; Conclusion). Fluency without unnatural hesitation, intelligible pronunciation, and confident handling of 1–2 follow-up questions from the examiners.
            </td>
          </tr>
          <tr>
            <td><strong>Part 5B:</strong> Negotiation (Graduation Trip)</td>
            <td>7.5 Points (~6 Min.)</td>
            <td>
              Active engagement and communicative collaboration. Contributes relevant ideas, responds appropriately to partner's points, and actively negotiates a workable compromise on destination, transportation, and costs.
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Grade Scale -->
      <div style="font-size:10.5px; font-weight:800; color:#0f2b48; margin-top:8px; margin-bottom:3px;">
        OFFICIAL GRADING CONVERSION SCALE (CEFR B1 &bull; 100 POINTS TOTAL)
      </div>
      <table class="key-table" style="text-align:center; font-size:9px;">
        <thead>
          <tr>
            <th style="text-align:center;">Score Range</th>
            <th style="text-align:center;">Percentage</th>
            <th style="text-align:center;">Grade &amp; Classification</th>
            <th style="text-align:center;">B1 Status</th>
          </tr>
        </thead>
        <tbody>
          <tr style="background:#ecfdf5;">
            <td><strong>90.0 – 100.0</strong></td>
            <td>90 % – 100 %</td>
            <td><strong>Grade A &ndash; Distinction</strong></td>
            <td><strong style="color:#059669;">Passed with Distinction</strong></td>
          </tr>
          <tr style="background:#f0fdf4;">
            <td><strong>80.0 – 89.5</strong></td>
            <td>80 % – 89 %</td>
            <td><strong>Grade B &ndash; Merit</strong></td>
            <td><strong style="color:#16a34a;">Passed with Merit</strong></td>
          </tr>
          <tr>
            <td><strong>70.0 – 79.5</strong></td>
            <td>70 % – 79 %</td>
            <td><strong>Grade C &ndash; Satisfactory</strong></td>
            <td><strong style="color:#2563eb;">Passed</strong></td>
          </tr>
          <tr style="background:#fffbeb;">
            <td><strong>60.0 – 69.5</strong></td>
            <td>60 % – 69 %</td>
            <td><strong>Grade D &ndash; Pass (Threshold)</strong></td>
            <td><strong style="color:#d97706;">Passed (Minimum Pass Mark)</strong></td>
          </tr>
          <tr style="background:#fef2f2;">
            <td><strong>0.0 – 59.5</strong></td>
            <td>&lt; 60 %</td>
            <td><strong>Fail</strong></td>
            <td><strong style="color:#dc2626;">Not Passed</strong></td>
          </tr>
        </tbody>
      </table>

      <div style="border-top:1.5px solid #cbd5e1; padding-top:6px; margin-top:8px; display:flex; justify-content:space-between; align-items:center; font-size:8.5px; color:#475569;">
        <div>Academic Director ILAS: <strong>Mr. Aziz Marsoul</strong></div>
        <div>Certificate Reference: <strong>CEFR-ENG-B1-2026-ILAS</strong></div>
        <div>Official Seal &amp; Signature: [ ___________________________ ]</div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Examiner's Guide: Descriptors &amp; Grade Scale</span>
      <span>Page 4 of 4</span>
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
    print("--- Building English Student Examination Booklet ---")
    student_html = build_student_exam_html()
    student_pages = convert_html_to_pdf(student_html, "English_B1_Examination_Booklet_ANASS_BENYAHIA.html", "English_B1_Examination_Booklet_ANASS_BENYAHIA.pdf")
    
    print("\n--- Building English Examiner Guide & Solution Key ---")
    examiner_html = build_examiner_guide_html()
    examiner_pages = convert_html_to_pdf(examiner_html, "English_B1_Examiners_Guide_Answer_Key.html", "English_B1_Examiners_Guide_Answer_Key.pdf")
    
    print("\n--- Creating English Master Combined Package ---")
    merge_pdfs(["English_B1_Examination_Booklet_ANASS_BENYAHIA.pdf", "English_B1_Examiners_Guide_Answer_Key.pdf"], "English_B1_Complete_Package_ANASS_BENYAHIA.pdf")
    
    print("\n--- Generating Visual Previews for English Version ---")
    student_previews = render_preview_images("English_B1_Examination_Booklet_ANASS_BENYAHIA.pdf", "preview_english_student", max_pages=4)
    examiner_previews = render_preview_images("English_B1_Examiners_Guide_Answer_Key.pdf", "preview_english_examiner", max_pages=2)
    
    print("\nALL ENGLISH BUILDS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
