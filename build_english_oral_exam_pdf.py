# -*- coding: utf-8 -*-
"""
Builder for English B1 Oral Examination (Speaking Exam / Examen Oral)
Personalized for Candidate ANASS BENYAHIA (DOB: 26.01.2007, CIN: WB226817)
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

def build_oral_candidate_html():
    logo_b64 = get_logo_b64()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>English B1 Oral Examination – Candidate Pack – ANASS BENYAHIA</title>
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

  /* Top Bar & Footer */
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
    padding-bottom: 8px;
    border-bottom: 2px solid #0f2b48;
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
    padding: 10px 0 8px 0;
  }}
  .cover-level-badge {{
    display: inline-block;
    background: #0f2b48;
    color: #ffffff;
    font-size: 10.5px;
    font-weight: 800;
    padding: 3px 14px;
    border-radius: 20px;
    letter-spacing: 1px;
    margin-bottom: 5px;
  }}
  .cover-hero h1 {{
    font-size: 22px;
    font-weight: 900;
    color: #0f2b48;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
  }}
  .cover-hero h2 {{
    font-size: 12.5px;
    font-weight: 700;
    color: #2563eb;
    margin-bottom: 3px;
  }}
  .cover-hero p {{
    font-size: 9px;
    color: #64748b;
  }}

  /* Candidate Profile Card */
  .candidate-card {{
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 9px 12px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .candidate-card-header {{
    font-size: 10.5px;
    font-weight: 800;
    text-transform: uppercase;
    color: #0f2b48;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .candidate-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 14px;
  }}
  .candidate-field {{
    display: flex;
    flex-direction: column;
  }}
  .cand-label {{
    font-size: 7.5px;
    text-transform: uppercase;
    font-weight: 700;
    color: #64748b;
    margin-bottom: 1px;
  }}
  .cand-value {{
    font-size: 11px;
    font-weight: 700;
    color: #0f172a;
    background: #ffffff;
    padding: 3px 8px;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
  }}
  .cand-value-highlight {{
    color: #1e3a8a;
    background: #eff6ff;
    border-color: #bfdbfe;
  }}

  /* Structure Table */
  .struct-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5px;
    margin-bottom: 10px;
  }}
  .struct-table th {{
    background: #0f2b48;
    color: #ffffff;
    font-weight: 700;
    padding: 5px 8px;
    text-align: left;
    border: 1px solid #0f2b48;
  }}
  .struct-table th.center, .struct-table td.center {{
    text-align: center;
  }}
  .struct-table td {{
    padding: 5px 8px;
    border: 1px solid #cbd5e1;
  }}
  .struct-table tr:nth-child(even) {{
    background: #f8fafc;
  }}

  /* Module Head Banner */
  .part-header {{
    background: linear-gradient(135deg, #0f2b48 0%, #1e3a8a 100%);
    color: #ffffff;
    padding: 6px 12px;
    border-radius: 5px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }}
  .part-header .part-title {{
    font-size: 12.5px;
    font-weight: 800;
    letter-spacing: 0.5px;
  }}
  .part-badge {{
    background: rgba(255, 255, 255, 0.2);
    padding: 2px 8px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.3);
    font-size: 9.5px;
    font-weight: 600;
  }}

  /* Card Styles */
  .content-card {{
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 9px 12px;
    margin-bottom: 8px;
  }}
  .content-card-title {{
    font-size: 11px;
    font-weight: 800;
    color: #0f2b48;
    margin-bottom: 4px;
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 3px;
  }}

  /* Visual Prompt Box (Part 2) */
  .visual-prompt-box {{
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 8px;
  }}
  .visual-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin: 6px 0;
  }}
  .visual-card {{
    background: #ffffff;
    border: 1px solid #bfdbfe;
    border-radius: 5px;
    padding: 8px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .visual-card-title {{
    font-size: 10px;
    font-weight: 800;
    color: #1e3a8a;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 5px;
  }}
  .visual-points {{
    font-size: 8.8px;
    color: #334155;
    line-height: 1.35;
    margin-left: 14px;
  }}

  /* Collaborative Mindmap (Part 3) */
  .mindmap-container {{
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 8px;
  }}
  .mindmap-core {{
    background: #0f2b48;
    color: #ffffff;
    text-align: center;
    padding: 6px 12px;
    border-radius: 20px;
    font-weight: 800;
    font-size: 11px;
    margin: 0 auto 8px auto;
    width: fit-content;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }}
  .ideas-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
  }}
  .idea-card {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-left: 3.5px solid #2563eb;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 8.8px;
    line-height: 1.3;
  }}
  .idea-title {{
    font-size: 9.5px;
    font-weight: 800;
    color: #0f2b48;
    margin-bottom: 2px;
    display: flex;
    align-items: center;
    gap: 4px;
  }}

  /* Useful Language Bank */
  .phrase-bank-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }}
  .phrase-box {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 6px 8px;
  }}
  .phrase-box-title {{
    font-size: 9px;
    font-weight: 800;
    color: #1e3a8a;
    text-transform: uppercase;
    margin-bottom: 3px;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 2px;
  }}
  .phrase-box ul {{
    margin-left: 14px;
    font-size: 8.5px;
    color: #334155;
    line-height: 1.35;
  }}

  /* Questions list */
  .prompt-list {{
    margin-left: 14px;
    font-size: 9.3px;
    color: #334155;
    line-height: 1.4;
  }}
  .prompt-list li {{
    margin-bottom: 3px;
  }}
</style>
</head>
<body>

  <!-- ==================== CANDIDATE PAGE 1: COVER & PROFILE ==================== -->
  <div class="exam-page">
    <div>
      <div class="cover-header">
        <div>
          <div class="cover-inst-title">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</div>
          <div class="cover-inst-sub">ILAS LANGUAGE INSTITUTE &bull; ORAL EXAMINATION BOARD</div>
          <div class="cover-inst-contact">Ministerial Authorization N° 22-200/2020 &bull; Deroua | Phone: 06 70 38 48 73 / 06 60 29 11 55</div>
        </div>
        <img src="data:image/png;base64,{logo_b64}" class="cover-logo-img" alt="ILAS Logo">
      </div>

      <div class="flag-bar" style="margin-top: 6px;">
        <div class="bar-navy"></div>
        <div class="bar-red"></div>
        <div class="bar-blue"></div>
      </div>

      <div class="cover-hero">
        <div class="cover-level-badge">COMMON EUROPEAN FRAMEWORK (CEFR) &bull; LEVEL B1 SPEAKING</div>
        <h1>ENGLISH B1 ORAL EXAMINATION</h1>
        <h2>OFFICIAL CANDIDATE SPEAKING PACK (EXAMEN ORAL)</h2>
        <p>Interactive Spoken Production, Collaborative Negotiation &amp; Thematic Monologue</p>
      </div>

      <!-- Candidate Profile -->
      <div class="candidate-card">
        <div class="candidate-card-header">
          <span>Candidate Information / Données du Candidat</span>
          <span style="color:#2563eb; font-weight:700;">Examination Center: ILAS Deroua</span>
        </div>
        <div class="candidate-grid">
          <div class="candidate-field">
            <span class="cand-label">Candidate Name (Nom &amp; Prénom):</span>
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
            <span class="cand-value">ILAS-ENG-ORAL-2026-WB226817</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Examination Date (Date d'Examen):</span>
            <span class="cand-value">16 October 2026</span>
          </div>
          <div class="candidate-field">
            <span class="cand-label">Module Status:</span>
            <span class="cand-value" style="color:#059669; font-weight:800;">Oral Speaking Only (Written Passed)</span>
          </div>
        </div>
      </div>

      <!-- Oral Test Structure -->
      <table class="struct-table">
        <thead>
          <tr>
            <th style="width: 25%;">Oral Test Part</th>
            <th style="width: 35%;">Task Type &amp; Focus</th>
            <th class="center" style="width: 20%;">Timing</th>
            <th class="center" style="width: 20%;">Max. Marks</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Part 1: Interview</strong></td>
            <td>General conversation, personal background, studies &amp; interests</td>
            <td class="center">2–3 Minutes</td>
            <td class="center">5.0 Points</td>
          </tr>
          <tr>
            <td><strong>Part 2: Long Turn</strong></td>
            <td>Individual monologue, visual prompt description &amp; comparison</td>
            <td class="center">3–4 Minutes</td>
            <td class="center">7.5 Points</td>
          </tr>
          <tr>
            <td><strong>Part 3: Collaborative Task</strong></td>
            <td>Interactive problem-solving, exchange of opinions &amp; consensus</td>
            <td class="center">3–4 Minutes</td>
            <td class="center">7.5 Points</td>
          </tr>
          <tr>
            <td><strong>Part 4: Extended Discussion</strong></td>
            <td>In-depth thematic discussion linking Part 3 to wider issues</td>
            <td class="center">3–4 Minutes</td>
            <td class="center">5.0 Points</td>
          </tr>
          <tr style="background:#eff6ff; font-weight:800; color:#0f2b48;">
            <td><strong>TOTAL ORAL EXAMINATION</strong></td>
            <td><strong>Comprehensive Spoken Performance Assessment</strong></td>
            <td class="center"><strong>12–15 Minutes</strong></td>
            <td class="center"><strong>25.0 Points</strong></td>
          </tr>
        </tbody>
      </table>

      <!-- Instructions & Signature -->
      <div style="display:grid; grid-template-columns: 2fr 1.2fr; gap:10px;">
        <div style="background:#fffbeb; border:1px solid #fef3c7; border-left:3px solid #f59e0b; padding:7px 9px; border-radius:4px; font-size:8.5px; color:#92400e;">
          <strong>Candidate Instructions:</strong>
          <ul style="margin-left:14px; margin-top:2px; line-height:1.35;">
            <li>Speak loudly, clearly, and naturally to ensure both examiners can hear you.</li>
            <li>Do not simply answer with “Yes” or “No”; elaborate and support your answers with reasons.</li>
            <li>In the collaborative task, actively invite your partner to speak and reach an agreement.</li>
          </ul>
        </div>
        <div style="border:1.5px dashed #94a3b8; border-radius:5px; padding:6px; text-align:center; display:flex; flex-direction:column; justify-content:space-between; background:#ffffff;">
          <div style="font-size:8px; font-weight:700; color:#475569; text-transform:uppercase;">Candidate Signature</div>
          <div style="height:36px; border-bottom:1px solid #cbd5e1;"></div>
          <div style="font-size:7px; color:#64748b;">ANASS BENYAHIA &bull; WB226817</div>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Oral Examination</span>
      <span class="footer-page">Page 1 of 4</span>
    </div>
  </div>


  <!-- ==================== CANDIDATE PAGE 2: PART 1 & PART 2 ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">English B1 Oral Exam &bull; Candidate Prompt Sheet</span>
        <span class="cand-tag">Candidate: ANASS BENYAHIA (WB226817)</span>
      </div>

      <!-- Part 1 -->
      <div class="part-header">
        <span class="part-title">PART 1: INTERVIEW &amp; PERSONAL PROFILE</span>
        <span class="part-badge">Timing: 2–3 Min. &bull; Warm-Up</span>
      </div>

      <div class="content-card">
        <div class="content-card-title">
          <span>General Conversation &amp; Personal Background</span>
          <span style="color:#2563eb;">Individual Interview</span>
        </div>
        <div style="font-size:9.2px; color:#334155; margin-bottom:5px;">
          The examiner will ask you general questions about yourself, your studies, your hometown, and your interests.
        </div>
        <ul class="prompt-list">
          <li><strong>Hometown &amp; Living:</strong> Can you describe the town or area where you live? What do you like best about it?</li>
          <li><strong>Studies &amp; Daily Routine:</strong> What subjects or fields of study are you most passionate about? How do you organize your typical weekday?</li>
          <li><strong>Free Time &amp; Activities:</strong> What hobbies or sports do you enjoy when you are not studying?</li>
          <li><strong>English Language Goals:</strong> Why is learning English important for your future education and career plans?</li>
        </ul>
      </div>

      <!-- Part 2 -->
      <div class="part-header" style="margin-top:6px;">
        <span class="part-title">PART 2: INDIVIDUAL LONG TURN (VISUAL PROMPT &amp; MONOLOGUE)</span>
        <span class="part-badge">Timing: 3–4 Min. &bull; Monologue (~1.5 min speaking)</span>
      </div>

      <div class="visual-prompt-box">
        <div class="content-card-title" style="margin-bottom:6px;">
          <span>Thematic Comparison: “Modern Learning Environments &ndash; Technology vs. Traditional Classrooms”</span>
          <span style="color:#2563eb;">Candidate Task Card</span>
        </div>
        <div style="font-size:9.2px; color:#334155; margin-bottom:6px;">
          Look at the two learning situations below. Describe what you see, compare how students learn in each environment, and explain which method suits you best.
        </div>

        <div class="visual-grid">
          <!-- Situation A -->
          <div class="visual-card">
            <div>
              <div class="visual-card-title">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
                <span>Situation A: Digital &amp; Online Learning</span>
              </div>
              <ul class="visual-points">
                <li>Students working collaboratively with laptops and smart tablets.</li>
                <li>Flexible self-paced research, interactive simulations, and digital resources.</li>
                <li>Distance learning from home or modern tech-equipped study hubs.</li>
                <li>Instant connectivity with teachers and peers globally.</li>
              </ul>
            </div>
            <div style="background:#eff6ff; padding:3px 6px; border-radius:3px; font-size:8px; color:#1e40af; margin-top:5px; font-weight:600;">
              Key themes: Independence, flexibility, digital literacy, self-motivation.
            </div>
          </div>

          <!-- Situation B -->
          <div class="visual-card">
            <div>
              <div class="visual-card-title">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0f2b48" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                <span>Situation B: Traditional Face-to-Face Classroom</span>
              </div>
              <ul class="visual-points">
                <li>Students seated together in a physical classroom with books and teacher at board.</li>
                <li>Direct face-to-face interaction, immediate verbal feedback, structured timetable.</li>
                <li>Quiet study atmosphere in libraries without screen distractions.</li>
                <li>Developing social relationships and active group discussions in person.</li>
              </ul>
            </div>
            <div style="background:#f1f5f9; padding:3px 6px; border-radius:3px; font-size:8px; color:#334155; margin-top:5px; font-weight:600;">
              Key themes: Focus, direct human contact, discipline, immediate guidance.
            </div>
          </div>
        </div>

        <div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:4px; padding:6px 10px; margin-top:4px;">
          <div style="font-size:9px; font-weight:800; color:#0f2b48; margin-bottom:2px;">Points to address during your talk:</div>
          <ul class="prompt-list">
            <li><strong>Describe &amp; Compare:</strong> What are the main similarities and differences between the two study styles?</li>
            <li><strong>Pros &amp; Cons:</strong> What are the advantages and drawbacks of studying with screens versus studying in person?</li>
            <li><strong>Personal Preference:</strong> Which style do you personally find more effective for learning languages and school subjects? Why?</li>
          </ul>
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Parts 1 &amp; 2</span>
      <span class="footer-page">Page 2 of 4</span>
    </div>
  </div>


  <!-- ==================== CANDIDATE PAGE 3: PART 3 & PART 4 ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">English B1 Oral Exam &bull; Candidate Prompt Sheet</span>
        <span class="cand-tag">Candidate: ANASS BENYAHIA (WB226817)</span>
      </div>

      <!-- Part 3 -->
      <div class="part-header">
        <span class="part-title">PART 3: COLLABORATIVE TASK (SIMULATION &amp; NEGOTIATION)</span>
        <span class="part-badge">Timing: 3–4 Min. &bull; Paired Discussion</span>
      </div>

      <div class="mindmap-container">
        <div class="content-card-title">
          <span>Scenario: Organizing an International Youth &amp; Culture Festival at ILAS</span>
          <span style="color:#2563eb;">Interactive Task</span>
        </div>
        <div style="font-size:9.2px; color:#334155; line-height:1.35; margin-bottom:8px;">
          Your institute is planning a special <strong>“International Youth &amp; Culture Festival”</strong> to encourage students to practice English and bring the local community together. Here are some activities that have been suggested.<br>
          <strong>Your task:</strong> Talk together with your partner about how interesting and useful each activity would be for students. Then, decide which <strong>TWO</strong> activities would be the most successful to include in the festival programme.
        </div>

        <div class="mindmap-core">
          INTERNATIONAL YOUTH &amp; CULTURE FESTIVAL
        </div>

        <div class="ideas-grid">
          <!-- Idea 1 -->
          <div class="idea-card">
            <div class="idea-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
              <span>Live Music &amp; Talent Concert</span>
            </div>
            Students perform acoustic songs in English, rap, or play traditional instruments. Fun atmosphere.
          </div>

          <!-- Idea 2 -->
          <div class="idea-card">
            <div class="idea-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
              <span>Global Street Food Fair</span>
            </div>
            Food stalls with dishes from Morocco, the UK, the USA, and other cultures. Highly popular.
          </div>

          <!-- Idea 3 -->
          <div class="idea-card">
            <div class="idea-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
              <span>English Trivia &amp; Escape Game</span>
            </div>
            Teams solve language puzzles, trivia questions, and riddles to win prizes. Educational &amp; engaging.
          </div>

          <!-- Idea 4 -->
          <div class="idea-card">
            <div class="idea-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
              <span>Virtual Reality (VR) Zone</span>
            </div>
            VR headsets showcasing digital tours of London, New York, and interactive language games.
          </div>

          <!-- Idea 5 -->
          <div class="idea-card">
            <div class="idea-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
              <span>Guest Speaker &amp; Debate</span>
            </div>
            An inspiring guest speaker shares their international career journey followed by a student Q&amp;A.
          </div>

          <!-- Idea 6 -->
          <div class="idea-card">
            <div class="idea-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#0891b2" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              <span>Photography &amp; Art Gallery</span>
            </div>
            Displaying student creative photos and artwork with bilingual English/Arabic descriptions.
          </div>
        </div>
      </div>

      <!-- Part 4 -->
      <div class="part-header" style="margin-top:6px;">
        <span class="part-title">PART 4: EXTENDED DISCUSSION &amp; CRITICAL THINKING</span>
        <span class="part-badge">Timing: 3–4 Min. &bull; Interactive Q&amp;A</span>
      </div>

      <div class="content-card">
        <div class="content-card-title">
          <span>Follow-up Discussion on Cultural Exchange &amp; Youth Opportunities</span>
          <span style="color:#2563eb;">Discussion with Examiners</span>
        </div>
        <ul class="prompt-list">
          <li><strong>Cultural Exchange:</strong> Why is it important for young people today to learn about other cultures and world traditions?</li>
          <li><strong>Community Events:</strong> What kinds of public events or festivals are most popular among teenagers in Morocco?</li>
          <li><strong>Career Readiness:</strong> In your opinion, how does speaking fluent English open doors for international university scholarships and jobs?</li>
          <li><strong>Organizing Challenges:</strong> What difficulties can arise when organizing a large public event, and how can a team solve them?</li>
        </ul>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Parts 3 &amp; 4</span>
      <span class="footer-page">Page 3 of 4</span>
    </div>
  </div>


  <!-- ==================== CANDIDATE PAGE 4: STRATEGY & PHRASE BANK ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">English B1 Oral Exam &bull; Candidate Preparation Guide</span>
        <span class="cand-tag">Candidate: ANASS BENYAHIA (WB226817)</span>
      </div>

      <div class="part-header">
        <span class="part-title">CANDIDATE SPEAKING STRATEGIES &amp; ESSENTIAL B1 PHRASE BANK</span>
        <span class="part-badge">Reference Sheet</span>
      </div>

      <div style="font-size:9.5px; color:#334155; margin-bottom:8px; line-height:1.35;">
        Use these professional phrases and transition words to demonstrate a wide linguistic range, interact smoothly with your partner, and keep the conversation flowing naturally.
      </div>

      <div class="phrase-bank-grid">
        <!-- Box 1 -->
        <div class="phrase-box">
          <div class="phrase-box-title">1. Giving Opinions &amp; Justifying</div>
          <ul>
            <li><em>“In my opinion, ... because ...”</em></li>
            <li><em>“From my perspective, this would be very effective because ...”</em></li>
            <li><em>“I feel that young people would really appreciate ...”</em></li>
            <li><em>“The main advantage of this idea is that ...”</em></li>
            <li><em>“On the other hand, a potential drawback might be ...”</em></li>
          </ul>
        </div>

        <!-- Box 2 -->
        <div class="phrase-box">
          <div class="phrase-box-title">2. Agreeing &amp; Disagreeing Politely</div>
          <ul>
            <li><em>“I completely agree with you on that point.”</em></li>
            <li><em>“That’s an excellent point, but have you considered ...?”</em></li>
            <li><em>“I see what you mean, although I’m not entirely sure that ...”</em></li>
            <li><em>“I’m afraid I have a slightly different view because ...”</em></li>
            <li><em>“You’re absolutely right; in addition, we could also ...”</em></li>
          </ul>
        </div>

        <!-- Box 3 -->
        <div class="phrase-box">
          <div class="phrase-box-title">3. Asking for Opinions &amp; Involving Partner</div>
          <ul>
            <li><em>“What are your thoughts on this idea?”</em></li>
            <li><em>“Do you think this activity would attract more students?”</em></li>
            <li><em>“How do you feel about combining these two options?”</em></li>
            <li><em>“Would you prefer the music concert or the food fair?”</em></li>
            <li><em>“Shall we move on to the next suggestion?”</em></li>
          </ul>
        </div>

        <!-- Box 4 -->
        <div class="phrase-box">
          <div class="phrase-box-title">4. Comparing &amp; Contrasting (Part 2)</div>
          <ul>
            <li><em>“Both pictures illustrate learning, but in very different ways.”</em></li>
            <li><em>“While the first situation focuses on ..., the second highlights ...”</em></li>
            <li><em>“Unlike traditional classrooms, digital learning allows ...”</em></li>
            <li><em>“In contrast to studying alone with a laptop, the classroom offers ...”</em></li>
            <li><em>“Overall, I find the first option much more engaging because ...”</em></li>
          </ul>
        </div>

        <!-- Box 5 -->
        <div class="phrase-box">
          <div class="phrase-box-title">5. Reaching a Decision / Consensus (Part 3)</div>
          <ul>
            <li><em>“So, which two activities shall we select for the festival?”</em></li>
            <li><em>“It seems we both agree that the concert and food fair are best.”</em></li>
            <li><em>“Shall we settle on these two options as our final choice?”</em></li>
            <li><em>“To sum up our discussion, our top recommendations are ...”</em></li>
          </ul>
        </div>

        <!-- Box 6 -->
        <div class="phrase-box">
          <div class="phrase-box-title">6. Buying Time &amp; Clarification</div>
          <ul>
            <li><em>“That’s an interesting question. Let me think for a second...”</em></li>
            <li><em>“Could you please repeat that question, if you don't mind?”</em></li>
            <li><em>“What I mean to say is that ...”</em></li>
            <li><em>“In other words, it creates a much better learning experience.”</em></li>
          </ul>
        </div>
      </div>

      <!-- Success Tips Box -->
      <div style="background:#eff6ff; border:1px solid #bfdbfe; border-left:3.5px solid #2563eb; border-radius:4px; padding:8px 10px; margin-top:8px;">
        <div style="font-size:9.5px; font-weight:800; color:#1e3a8a; margin-bottom:2px;">Top Examiner Tips for ANASS BENYAHIA:</div>
        <div style="font-size:8.8px; color:#334155; line-height:1.35;">
          &bull; <strong>Fluency over perfection:</strong> Don't freeze if you make a small grammar mistake; simply rephrase and keep talking.<br>
          &bull; <strong>Show your vocabulary:</strong> Use specific adjectives (e.g., <em>rewarding, interactive, demanding, essential</em>) instead of just <em>good</em> or <em>nice</em>.<br>
          &bull; <strong>Listen actively:</strong> Respond directly to what the examiner or partner says before moving to your own thoughts.
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span class="footer-inst">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</span>
      <span>Candidate: <strong>ANASS BENYAHIA</strong> (WB226817) &bull; Strategy Guide</span>
      <span class="footer-page">Page 4 of 4</span>
    </div>
  </div>

</body>
</html>
"""
    return html

def build_oral_examiner_html():
    logo_b64 = get_logo_b64()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>English B1 Oral Examination – Examiner's Pack &amp; Grading Protocol</title>
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

  /* Top Bar & Footer */
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

  /* Flag Bar */
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

  .section-title {{
    font-size: 11px;
    font-weight: 800;
    color: #0f2b48;
    background: #f1f5f9;
    padding: 4px 8px;
    border-left: 4px solid #0f2b48;
    margin-bottom: 6px;
    border-radius: 0 4px 4px 0;
  }}

  /* Script Box */
  .script-box {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 7px 10px;
    margin-bottom: 7px;
  }}
  .script-box-header {{
    font-size: 10px;
    font-weight: 800;
    color: #1e3a8a;
    margin-bottom: 3px;
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 2px;
  }}
  .spoken-prompt {{
    font-style: italic;
    color: #0f172a;
    font-size: 9.3px;
    line-height: 1.35;
    background: #f8fafc;
    padding: 5px 8px;
    border-left: 3px solid #2563eb;
    margin: 4px 0;
    border-radius: 0 4px 4px 0;
  }}
  .examiner-note {{
    font-size: 8.5px;
    color: #64748b;
    margin-top: 3px;
  }}

  /* Grading Rubric Table */
  .rubric-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9px;
    margin-bottom: 6px;
  }}
  .rubric-table th {{
    background: #0f2b48;
    color: #ffffff;
    font-weight: 700;
    padding: 5px 6px;
    text-align: left;
    border: 1px solid #0f2b48;
  }}
  .rubric-table td {{
    padding: 4px 6px;
    border: 1px solid #cbd5e1;
    vertical-align: top;
  }}
  .rubric-table tr:nth-child(even) {{
    background: #f8fafc;
  }}

  /* Scorecard Table */
  .scorecard-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5px;
    margin-bottom: 8px;
  }}
  .scorecard-table th {{
    background: #0f2b48;
    color: #ffffff;
    font-weight: 700;
    padding: 5px 8px;
    text-align: left;
    border: 1px solid #0f2b48;
  }}
  .scorecard-table td {{
    padding: 5px 8px;
    border: 1px solid #cbd5e1;
  }}
  .scorecard-table tr.total-row {{
    background: #eff6ff;
    font-weight: 800;
    color: #0f2b48;
  }}
</style>
</head>
<body>

  <!-- ==================== EXAMINER PAGE 1: SCRIPT (PARTS 1 & 2) ==================== -->
  <div class="exam-page">
    <div>
      <div class="cover-header">
        <div>
          <div class="cover-inst-title">INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS)</div>
          <div class="cover-inst-sub">SPEAKING EXAMINATION COMMISSION &bull; ENGLISH B1</div>
          <div class="cover-inst-contact">Authorization N° 22-200/2020 &bull; Deroua | Interlocutor Framework &amp; Evaluation Guide</div>
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
          <div style="font-size:13px; font-weight:900;">ORAL EXAMINER'S HANDBOOK (EXAMINATEUR)</div>
          <div style="font-size:9.5px; opacity:0.9;">Interlocutor Script, CEFR B1 Band Descriptors &amp; Official Grading Sheet</div>
        </div>
        <span class="examiner-badge">CONFIDENTIAL</span>
      </div>

      <div class="candidate-ref-bar">
        <span>Candidate: <strong>ANASS BENYAHIA</strong></span>
        <span>Date of Birth: <strong>26.01.2007</strong></span>
        <span>CIN: <strong>WB226817</strong></span>
        <span>Date: <strong>16.10.2026</strong></span>
      </div>

      <div class="section-title">INTERLOCUTOR FRAMEWORK &amp; VERBATIM SCRIPT &bull; PARTS 1 &amp; 2</div>

      <!-- Part 1 Script -->
      <div class="script-box">
        <div class="script-box-header">
          <span>PART 1: INTERVIEW &amp; WARM-UP (2–3 MINUTES)</span>
          <span style="color:#2563eb;">General Interaction</span>
        </div>
        <div class="spoken-prompt">
          “Good morning / afternoon. My name is [Examiner Name], and this is my colleague [Assessor Name].<br>
          Can you tell me your full name, please? ... And what is your date of birth? ... Thank you.<br>
          First of all, Anass, can you tell us where you come from and describe your hometown? ...<br>
          What do you enjoy doing most in your free time when you are not studying? ...<br>
          Why are you studying English at this time, and how do you plan to use it in your future?”
        </div>
        <div class="examiner-note">
          <strong>Examiner Guidance:</strong> Ask 2 to 3 follow-up questions to help the candidate relax. Ensure the candidate produces full sentences rather than isolated single-word answers. Do not over-correct errors at this stage.
        </div>
      </div>

      <!-- Part 2 Script -->
      <div class="script-box" style="margin-bottom:0;">
        <div class="script-box-header">
          <span>PART 2: INDIVIDUAL LONG TURN (3–4 MINUTES)</span>
          <span style="color:#2563eb;">Thematic Comparison (~1.5 min candidate speech)</span>
        </div>
        <div class="spoken-prompt">
          “Thank you, Anass. Now, in this part of the test, I am going to give you a task card with two different situations.<br>
          Here is your card. The theme is: <strong>‘Modern Learning Environments &ndash; Technology vs. Traditional Classrooms’</strong>.<br>
          I would like you to describe what you see, compare how students learn in these two situations, and tell me which method you personally find more effective.<br>
          You have about one minute to look at the card, and then please talk for about one and a half to two minutes. All right? Please begin.”
        </div>
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:6px 8px; margin:4px 0; font-size:8.8px;">
          <strong>Follow-up Questions (if candidate stops early):</strong><br>
          &bull; <em>“How do you think digital tools like artificial intelligence and online apps are changing how students study?”</em><br>
          &bull; <em>“Do you ever feel that having screens in class causes distractions, or does it help you focus better?”</em>
        </div>
        <div class="examiner-note">
          <strong>Assessment Focus:</strong> Assess candidate's ability to produce sustained monologue, organize ideas with cohesive devices (<em>while, whereas, in contrast</em>), and use comparative structures correctly.
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Examiner's Guide: Script (Parts 1 &amp; 2)</span>
      <span>Page 1 of 4</span>
    </div>
  </div>


  <!-- ==================== EXAMINER PAGE 2: SCRIPT (PARTS 3 & 4) ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">CONFIDENTIAL &bull; EXAMINER'S HANDBOOK B1</span>
        <span>Interlocutor Script &bull; Parts 3 &amp; 4</span>
      </div>

      <div class="section-title">INTERLOCUTOR FRAMEWORK &amp; VERBATIM SCRIPT &bull; PARTS 3 &amp; 4</div>

      <!-- Part 3 Script -->
      <div class="script-box">
        <div class="script-box-header">
          <span>PART 3: COLLABORATIVE TASK &amp; NEGOTIATION (3–4 MINUTES)</span>
          <span style="color:#2563eb;">Interactive Simulation</span>
        </div>
        <div class="spoken-prompt">
          “Now, in this part of the test, you are going to talk together with your partner [or the examiner].<br>
          Imagine our language institute, ILAS, is organizing an <strong>‘International Youth &amp; Culture Festival’</strong> to celebrate language learning and bring the student community together.<br>
          Here is a sheet showing different activity ideas: live music, international food stalls, English trivia games, a VR experience zone, a guest speaker session, and an art exhibition.<br>
          Talk together about how engaging and beneficial each activity would be for students. Then, decide which <strong>TWO</strong> activities would be the most popular to include in the festival.<br>
          You have about three to four minutes for your discussion. Please start now.”
        </div>
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:6px 8px; margin:4px 0; font-size:8.8px;">
          <strong>Prompts to support interaction (if candidate pauses):</strong><br>
          &bull; <em>“What do you think about the food fair? Would young people like that?”</em><br>
          &bull; <em>“Do you agree with that suggestion, or would another idea be more practical?”</em><br>
          &bull; <em>“We need to make our final decision now. Which two do we select?”</em>
        </div>
        <div class="examiner-note">
          <strong>Assessment Focus:</strong> Active turn-taking, inviting the other speaker, negotiating pros and cons, using polite disagreement, and reaching a collaborative consensus.
        </div>
      </div>

      <!-- Part 4 Script -->
      <div class="script-box" style="margin-bottom:0;">
        <div class="script-box-header">
          <span>PART 4: EXTENDED DISCUSSION &amp; SOCIETAL THEMES (3–4 MINUTES)</span>
          <span style="color:#2563eb;">Critical Thinking</span>
        </div>
        <div class="spoken-prompt">
          “Thank you. Now, let’s talk a little more about international culture and youth events.<br>
          &bull; Anass, why do you think it is so crucial for today's youth to understand different global cultures?<br>
          &bull; What kinds of community festivals or social events are most successful in Morocco?<br>
          &bull; Some people say that learning English online is enough and schools are no longer needed. What is your view on that?<br>
          &bull; How does being able to speak English confidently help someone get better career opportunities in Morocco and abroad?”
        </div>
        <div class="examiner-note">
          <strong>Assessment Focus:</strong> Candidate's ability to express personal beliefs, substantiate opinions with examples, use conditional sentences and abstract vocabulary appropriate for CEFR B1.
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Examiner's Guide: Script (Parts 3 &amp; 4)</span>
      <span>Page 2 of 4</span>
    </div>
  </div>


  <!-- ==================== EXAMINER PAGE 3: CEFR B1 ASSESSMENT CRITERIA ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">CONFIDENTIAL &bull; EXAMINER'S HANDBOOK B1</span>
        <span>Standardized CEFR B1 Speaking Descriptors</span>
      </div>

      <div class="section-title">STANDARDIZED CEFR B1 SPEAKING ASSESSMENT RUBRIC</div>

      <table class="rubric-table">
        <thead>
          <tr>
            <th style="width:18%;">Criterion</th>
            <th style="width:20%;">Band 5 (Excellent &bull; 90–100%)</th>
            <th style="width:21%;">Band 4 (Good &bull; 80–89%)</th>
            <th style="width:21%;">Band 3 (Pass / B1 &bull; 60–79%)</th>
            <th style="width:20%;">Band 1–2 (Below B1 &bull; &lt;60%)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>1. Grammatical Accuracy &amp; Range</strong></td>
            <td>Uses a good range of B1 structures (conditionals, modals, passives, relative clauses) with high accuracy. Minor slips do not impede communication.</td>
            <td>Shows good control of simple and some complex structures. Errors occur when attempting ambitious language but meaning is clear.</td>
            <td>Demonstrates sufficient control of simple grammar and basic B1 forms. Tense errors occur but communication is consistently maintained.</td>
            <td>Frequent basic grammatical errors (verb forms, word order) that frequently confuse meaning. Very limited sentence variety.</td>
          </tr>
          <tr>
            <td><strong>2. Lexical Range &amp; Resource</strong></td>
            <td>Uses varied, precise vocabulary suited to personal and abstract topics. Effectively paraphrases when searching for words.</td>
            <td>Good vocabulary range for everyday and thematic topics. Uses appropriate collocations and descriptive adjectives.</td>
            <td>Sufficient vocabulary to discuss familiar topics and express personal opinions. Occasionally repeats basic words.</td>
            <td>Narrow vocabulary; struggles to find words even for basic ideas. Frequent hesitation caused by vocabulary search.</td>
          </tr>
          <tr>
            <td><strong>3. Fluency &amp; Discourse Management</strong></td>
            <td>Produces extended, coherent stretches of language with natural rhythm. Connects ideas smoothly using a variety of cohesive devices.</td>
            <td>Speaks fluently with few noticeable pauses. Links thoughts logically (<em>because, however, although, on the other hand</em>).</td>
            <td>Able to sustain a monologue and answer questions without excessive pauses. Uses basic linking words (<em>and, but, so, because</em>).</td>
            <td>Very disjointed speech with frequent, unnatural pauses. Struggles to produce complete utterances without prompting.</td>
          </tr>
          <tr>
            <td><strong>4. Pronunciation &amp; Intonation</strong></td>
            <td>Pronunciation is clear and effortless to understand. Appropriate sentence stress, rhythm, and expressive intonation.</td>
            <td>Consistently intelligible with good control of word stress and sounds. Accent does not hinder comprehension.</td>
            <td>Generally intelligible pronunciation. Occasional phonological errors, but examiners rarely need to ask for repetition.</td>
            <td>Heavy mispronunciation causes frequent misunderstanding. Word stress and rhythm are severely compromised.</td>
          </tr>
          <tr>
            <td><strong>5. Interactive Communication</strong></td>
            <td>Initiates, responds, and actively develops the conversation. Demonstrates excellent turn-taking and negotiates consensus smoothly.</td>
            <td>Interacts effectively, responds readily to prompts, and actively supports the partner with questions and suggestions.</td>
            <td>Maintains interaction reasonably well. Responds to examiner prompts and contributes to decision-making with some support.</td>
            <td>Minimal interaction; relies heavily on examiner assistance to participate. Rarely reacts to what the other speaker says.</td>
          </tr>
        </tbody>
      </table>

      <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:4px; padding:6px 10px; font-size:8.5px; line-height:1.4;">
        <strong>Scoring Weighting:</strong> Each of the 5 criteria carries a maximum of <strong>5.0 Points</strong>, yielding an overall Speaking score out of <strong>25.0 Points</strong>.<br>
        <strong>Passing Benchmark:</strong> Minimum <strong>15.0 / 25.0 Points (60%)</strong> required for B1 certification.
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Examiner's Guide: Rubrics &amp; Descriptors</span>
      <span>Page 3 of 4</span>
    </div>
  </div>


  <!-- ==================== EXAMINER PAGE 4: OFFICIAL GRADING PROTOCOL ==================== -->
  <div class="exam-page">
    <div>
      <div class="page-top-bar">
        <span class="inst-tag">OFFICIAL &bull; ORAL ASSESSMENT PROTOCOL</span>
        <span>Procès-Verbal d'Évaluation &ndash; Épreuve Orale B1</span>
      </div>

      <div class="section-title">OFFICIAL CANDIDATE ORAL ASSESSMENT RECORD (PROCÈS-VERBAL)</div>

      <div class="candidate-card" style="margin-bottom:8px;">
        <div class="candidate-grid">
          <div><strong>Candidate Name:</strong> BENYAHIA, Anass</div>
          <div><strong>Date of Birth:</strong> 26.01.2007</div>
          <div><strong>National ID / CIN:</strong> WB226817</div>
          <div><strong>Examination Reference:</strong> ILAS-ENG-ORAL-2026-WB226817</div>
          <div><strong>Date of Examination:</strong> 16 October 2026</div>
          <div><strong>Center:</strong> Institut Privé de Langues Les Sages (Deroua)</div>
        </div>
      </div>

      <table class="scorecard-table">
        <thead>
          <tr>
            <th style="width:38%;">Assessment Criterion</th>
            <th class="center" style="width:18%;">Max. Points</th>
            <th class="center" style="width:20%;">Awarded Score</th>
            <th style="width:24%;">Examiner Comments</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>1. Grammatical Accuracy &amp; Range</strong><br><span style="font-size:7.5px; color:#64748b;">Control of B1 structures, verb tenses, word order</span></td>
            <td class="center">5.0 Pts</td>
            <td class="center"><strong>_____ / 5.0</strong></td>
            <td></td>
          </tr>
          <tr>
            <td><strong>2. Lexical Resource &amp; Vocabulary</strong><br><span style="font-size:7.5px; color:#64748b;">Variety of words, collocations, idiomatic phrasing</span></td>
            <td class="center">5.0 Pts</td>
            <td class="center"><strong>_____ / 5.0</strong></td>
            <td></td>
          </tr>
          <tr>
            <td><strong>3. Fluency &amp; Discourse Management</strong><br><span style="font-size:7.5px; color:#64748b;">Pacing, coherence, use of connectors, monologue length</span></td>
            <td class="center">5.0 Pts</td>
            <td class="center"><strong>_____ / 5.0</strong></td>
            <td></td>
          </tr>
          <tr>
            <td><strong>4. Pronunciation &amp; Intonation</strong><br><span style="font-size:7.5px; color:#64748b;">Clarity, stress patterns, rhythm, natural flow</span></td>
            <td class="center">5.0 Pts</td>
            <td class="center"><strong>_____ / 5.0</strong></td>
            <td></td>
          </tr>
          <tr>
            <td><strong>5. Interactive Communication</strong><br><span style="font-size:7.5px; color:#64748b;">Turn-taking, collaborative negotiation, initiative</span></td>
            <td class="center">5.0 Pts</td>
            <td class="center"><strong>_____ / 5.0</strong></td>
            <td></td>
          </tr>
          <tr class="total-row">
            <td><strong>TOTAL ORAL SPEAKING SCORE</strong></td>
            <td class="center"><strong>25.0 Pts</strong></td>
            <td class="center"><strong>_____ / 25.0</strong></td>
            <td><strong>Percentage: _____ %</strong></td>
          </tr>
        </tbody>
      </table>

      <!-- Result Decision Box -->
      <div style="background:#ffffff; border:1.5px solid #0f2b48; border-radius:5px; padding:7px 10px; margin-bottom:8px;">
        <div style="font-size:9.5px; font-weight:800; color:#0f2b48; text-transform:uppercase; margin-bottom:4px; display:flex; justify-content:space-between;">
          <span>Official Examination Board Verdict:</span>
          <span>Pass Mark: 15.0 / 25.0 (60%)</span>
        </div>
        <div style="display:flex; gap:16px; font-size:9px;">
          <div>[ &nbsp; ] <strong>Grade A &ndash; Distinction</strong> (22.5–25.0 Pts)</div>
          <div>[ &nbsp; ] <strong>Grade B &ndash; Merit</strong> (20.0–22.0 Pts)</div>
          <div>[ &nbsp; ] <strong>Grade C &ndash; Pass</strong> (15.0–19.5 Pts)</div>
          <div>[ &nbsp; ] <strong>Fail</strong> (&lt; 15.0 Pts)</div>
        </div>
      </div>

      <!-- Signatures & Stamp -->
      <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; font-size:8.5px; color:#334155; border-top:1px solid #cbd5e1; padding-top:6px;">
        <div>
          <strong>Interlocutor (Examiner 1):</strong><br>
          Name: ______________________<br>
          Signature: ___________________
        </div>
        <div>
          <strong>Assessor (Examiner 2):</strong><br>
          Name: ______________________<br>
          Signature: ___________________
        </div>
        <div style="text-align:center;">
          <strong>Director / Head of Center:</strong><br>
          Mr. Aziz Marsoul<br>
          [ &nbsp; Official Stamp &nbsp; ]
        </div>
      </div>

    </div>

    <div class="page-footer-bar">
      <span>INSTITUT PRIVÉ DE LANGUES LES SAGES (ILAS) &bull; DEROUA</span>
      <span>Official Oral Protocol &bull; ANASS BENYAHIA</span>
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

def render_preview_images(pdf_filename, output_prefix, max_pages=4):
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
    print("--- Building English Oral Exam Candidate Pack ---")
    candidate_html = build_oral_candidate_html()
    cand_pages = convert_html_to_pdf(candidate_html, "English_B1_Oral_Exam_Candidate_Pack_ANASS_BENYAHIA.html", "English_B1_Oral_Exam_Candidate_Pack_ANASS_BENYAHIA.pdf")
    
    print("\n--- Building English Oral Exam Examiner Pack ---")
    examiner_html = build_oral_examiner_html()
    exam_pages = convert_html_to_pdf(examiner_html, "English_B1_Oral_Exam_Examiners_Pack_ANASS_BENYAHIA.html", "English_B1_Oral_Exam_Examiners_Pack_ANASS_BENYAHIA.pdf")
    
    print("\n--- Creating Master Combined Oral Package ---")
    merge_pdfs(["English_B1_Oral_Exam_Candidate_Pack_ANASS_BENYAHIA.pdf", "English_B1_Oral_Exam_Examiners_Pack_ANASS_BENYAHIA.pdf"], "English_B1_Oral_Exam_Complete_ANASS_BENYAHIA.pdf")
    
    print("\n--- Generating Visual Previews ---")
    cand_previews = render_preview_images("English_B1_Oral_Exam_Candidate_Pack_ANASS_BENYAHIA.pdf", "preview_oral_candidate", max_pages=4)
    exam_previews = render_preview_images("English_B1_Oral_Exam_Examiners_Pack_ANASS_BENYAHIA.pdf", "preview_oral_examiner", max_pages=4)
    
    print("\n--- Copying to User Desktop ---")
    import shutil
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    files_to_copy = [
        "English_B1_Oral_Exam_Candidate_Pack_ANASS_BENYAHIA.pdf",
        "English_B1_Oral_Exam_Examiners_Pack_ANASS_BENYAHIA.pdf",
        "English_B1_Oral_Exam_Complete_ANASS_BENYAHIA.pdf"
    ]
    for f in files_to_copy:
        dest = os.path.join(desktop, f)
        shutil.copy2(f, dest)
        print(f"Copied to Desktop: {dest}")
        
    print("\nALL ORAL BUILDS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
