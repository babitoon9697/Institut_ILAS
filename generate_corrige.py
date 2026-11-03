# -*- coding: utf-8 -*-
"""
Generate the Teacher's Correction Key & Marking Scheme (Corrigé & Barème)
for the B1 English Exam at Institut ILAS.
"""

import os
import base64
import subprocess
import pymupdf

def get_logo_base64():
    logo_path = os.path.abspath('static/uploads/logo-ilas.png')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode('utf-8')
    return ""

def create_answer_key():
    logo_b64 = get_logo_base64()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Institut ILAS - Corrigé &amp; Barème - Examen Anglais B1</title>
<style>
    @page {{
        size: A4 portrait;
        margin: 10mm 14mm 10mm 14mm;
    }}
    * {{
        box-sizing: border-box;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}
    body {{
        font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
        color: #1a202c;
        margin: 0;
        padding: 0;
        font-size: 11px;
        line-height: 1.4;
        background: #fff;
    }}
    .header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 2px solid #0d5c75;
        padding-bottom: 6px;
        margin-bottom: 12px;
    }}
    .header-left {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .header-logo {{
        height: 48px;
        width: auto;
    }}
    .header-inst-text h1 {{
        margin: 0;
        font-size: 16px;
        color: #0d5c75;
        font-weight: 800;
        text-transform: uppercase;
    }}
    .header-inst-text p {{
        margin: 2px 0 0 0;
        font-size: 10px;
        color: #64748b;
    }}
    .badge {{
        background: #0d5c75;
        color: #ffffff;
        font-weight: 700;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 4px;
        display: inline-block;
    }}
    .badge-corr {{
        background: #047857;
        color: #ffffff;
        font-weight: 700;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 4px;
        display: inline-block;
        margin-left: 6px;
    }}
    .section-title {{
        background: #0d5c75;
        color: #ffffff;
        padding: 4px 10px;
        font-weight: 700;
        font-size: 12px;
        margin: 12px 0 6px 0;
        border-radius: 3px;
        display: flex;
        justify-content: space-between;
    }}
    .ans-box {{
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 8px 12px;
        margin-bottom: 8px;
    }}
    .ans-box h4 {{
        margin: 0 0 4px 0;
        color: #0f172a;
        font-size: 11.5px;
    }}
    .ans-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
    }}
    .ans-table th, .ans-table td {{
        border: 1px solid #cbd5e1;
        padding: 4px 8px;
        text-align: left;
    }}
    .ans-table th {{
        background: #e2e8f0;
    }}
    .correct {{
        font-weight: 700;
        color: #047857;
    }}
    .pts {{
        font-weight: 700;
        color: #0d5c75;
        text-align: center;
        width: 65px;
    }}
    .model-email {{
        background: #f0fdf4;
        border-left: 3px solid #10b981;
        padding: 8px 12px;
        font-style: italic;
        margin-top: 6px;
        line-height: 1.45;
    }}
</style>
</head>
<body>

<div class="header">
    <div class="header-left">
        <img src="{logo_b64}" alt="Institut ILAS" class="header-logo" />
        <div class="header-inst-text">
            <h1>INSTITUT ILAS</h1>
            <p>Centre de Langues &bull; Guide de Correction &amp; Barème Officiel</p>
        </div>
    </div>
    <div>
        <span class="badge">ENGLISH B1</span>
        <span class="badge-corr">TEACHER'S ANSWER KEY</span>
    </div>
</div>

<div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 4px; padding: 6px 10px; margin-bottom: 10px; font-size: 10.5px;">
    <strong>Profil de l'examen :</strong> Niveau B1 (CECRL) &bull; Durée : 1h00 &bull; Indice de difficulté : 50% (accessible, compétences pivots) &bull; Total : 40 points divisé par 2 = Note finale sur 20.
</div>

<!-- SECTION 1 -->
<div class="section-title">
    <span>SECTION 1: READING COMPREHENSION</span>
    <span>TOTAL : 14 POINTS</span>
</div>

<div class="ans-box">
    <h4>A. Multiple Choice (4 &times; 1 pt = 4 pts)</h4>
    <table class="ans-table">
        <tr><th>Question</th><th>Bonne Réponse</th><th>Justification / Explication</th><th class="pts">Points</th></tr>
        <tr><td>1. Why nomads can work</td><td><span class="correct">B. Fast internet and laptops</span></td><td>Ligne 1: "Thanks to reliable high-speed internet and lightweight portable computers..."</td><td class="pts">1 pt</td></tr>
        <tr><td>2. Family reaction</td><td><span class="correct">A. Felt concerned about his career</span></td><td>Ligne 6: "my family was worried that I was putting my career at risk"</td><td class="pts">1 pt</td></tr>
        <tr><td>3. Liam's productivity</td><td><span class="correct">B. More productive and independent</span></td><td>Ligne 7: "I am actually much more productive now. I organize my own weekly schedule..."</td><td class="pts">1 pt</td></tr>
        <tr><td>4. Main disadvantage</td><td><span class="correct">B. Loneliness and constant traveling</span></td><td>Ligne 10: "Moving constantly... physically exhausting... far away from friends... lonely"</td><td class="pts">1 pt</td></tr>
    </table>
</div>

<div class="ans-box">
    <h4>B. True / False with Quote (3 &times; 2 pts = 6 pts: 1 pt T/F + 1 pt citation exacte)</h4>
    <table class="ans-table">
        <tr><th>Énoncé</th><th>T / F</th><th>Citation textuelle attendue</th><th class="pts">Points</th></tr>
        <tr><td>1. Liam lives as nomad for 5 years</td><td><span class="correct">FALSE</span></td><td><em>"decided to embrace this lifestyle two years ago."</em></td><td class="pts">2 pts</td></tr>
        <tr><td>2. Works exclusively for hometown clients</td><td><span class="correct">FALSE</span></td><td><em>"complete projects for international clients"</em></td><td class="pts">2 pts</td></tr>
        <tr><td>3. Wants to return to desk job soon</td><td><span class="correct">FALSE</span></td><td><em>"Liam has no intention of returning to a traditional 9-to-5 desk job in the near future."</em></td><td class="pts">2 pts</td></tr>
    </table>
</div>

<div class="ans-box">
    <h4>C. Vocabulary in Context (4 &times; 1 pt = 4 pts)</h4>
    <table class="ans-table">
        <tr><th>Mot cherché</th><th>Réponse acceptée</th><th class="pts">Points</th></tr>
        <tr><td>1. Changed substantially (Par. 1)</td><td><span class="correct">transformed</span></td><td class="pts">1 pt</td></tr>
        <tr><td>2. Traveling between home and work (Par. 1)</td><td><span class="correct">commuting</span></td><td class="pts">1 pt</td></tr>
        <tr><td>3. Hardships / obstacles (Par. 3)</td><td><span class="correct">difficulties</span> (ou <em>challenges</em>)</td><td class="pts">1 pt</td></tr>
        <tr><td>4. Traditional / normal (Par. 3)</td><td><span class="correct">ordinary</span></td><td class="pts">1 pt</td></tr>
    </table>
</div>

<!-- SECTION 2 -->
<div class="section-title">
    <span>SECTION 2: USE OF ENGLISH &amp; GRAMMAR</span>
    <span>TOTAL : 14 POINTS</span>
</div>

<div class="ans-box">
    <h4>A. Verb Tenses &amp; Forms (6 &times; 1 pt = 6 pts)</h4>
    <ol style="margin: 0; padding-left: 20px;">
        <li>While my classmate <span class="correct">was preparing</span> her presentation yesterday... <em>(Past Continuous)</em> &mdash; <strong>[1 pt]</strong></li>
        <li>Mr. Taylor is a passionate instructor; he <span class="correct">has taught</span> (ou <span class="correct">has been teaching</span>) English for three years. &mdash; <strong>[1 pt]</strong></li>
        <li>If Sarah finishes her project early tomorrow afternoon, she <span class="correct">will join</span> us... <em>(First Conditional)</em> &mdash; <strong>[1 pt]</strong></li>
        <li>If I had enough savings, I <span class="correct">would travel</span> to Canada... <em>(Second Conditional)</em> &mdash; <strong>[1 pt]</strong></li>
        <li>We <span class="correct">have not received</span> (ou <span class="correct">haven't received</span>) any confirmation email... <em>(Present Perfect)</em> &mdash; <strong>[1 pt]</strong></li>
        <li>When we arrived... the teacher <span class="correct">had already started</span> the lecture. <em>(Past Perfect)</em> &mdash; <strong>[1 pt]</strong></li>
    </ol>
</div>

<div class="ans-box">
    <h4>B. Relative Pronouns &amp; Linking Words (4 &times; 1 pt = 4 pts)</h4>
    <ol style="margin: 0; padding-left: 20px;">
        <li>The multimedia laboratory (<span class="correct">where</span>) we listen to audio tracks... &mdash; <strong>[1 pt]</strong></li>
        <li>Mrs. Adams is the language supervisor (<span class="correct">who</span>) evaluates the students... &mdash; <strong>[1 pt]</strong></li>
        <li>(<span class="correct">Although</span>) the exam was comprehensive, Adam managed his time effectively. &mdash; <strong>[1 pt]</strong></li>
        <li>Nour practiced conversation every single day, (<span class="correct">so</span>) she spoke with great confidence... &mdash; <strong>[1 pt]</strong></li>
    </ol>
</div>

<div class="ans-box">
    <h4>C. Modal Verbs (4 &times; 1 pt = 4 pts)</h4>
    <ol style="margin: 0; padding-left: 20px;">
        <li>Candidates <span class="correct">mustn't</span> look at their neighbor's paper... <em>(Interdiction stricte)</em> &mdash; <strong>[1 pt]</strong></li>
        <li>You <span class="correct">don't have to</span> buy the textbook immediately... <em>(Absence d'obligation)</em> &mdash; <strong>[1 pt]</strong></li>
        <li>You look very tired before the exam; you <span class="correct">shouldn't</span> stay awake all night... <em>(Conseil négatif)</em> &mdash; <strong>[1 pt]</strong></li>
        <li>To obtain the B1 certificate, each student <span class="correct">must</span> obtain at least 50%... <em>(Obligation)</em> &mdash; <strong>[1 pt]</strong></li>
    </ol>
</div>

<!-- SECTION 3 -->
<div class="section-title">
    <span>SECTION 3: GUIDED WRITTEN PRODUCTION</span>
    <span>TOTAL : 12 POINTS</span>
</div>

<div class="ans-box">
    <h4>Grille d'évaluation B1 (12 points)</h4>
    <table class="ans-table">
        <tr><th>Critère</th><th>Description B1</th><th class="pts">Points</th></tr>
        <tr><td><strong>1. Respect de la consigne (Task Fulfillment)</strong></td><td>Traite les 3 points du prompt (cours choisi, aspects appréciés, invitation &amp; conseil). Longueur respectée (80–100 mots).</td><td class="pts">/ 3 pts</td></tr>
        <tr><td><strong>2. Correction grammaticale</strong></td><td>Structures simples et courantes bien maîtrisées (présent, passé composé/prétérit, connecteurs). Quelques erreurs non bloquantes acceptées.</td><td class="pts">/ 3 pts</td></tr>
        <tr><td><strong>3. Lexique &amp; Orthographe</strong></td><td>Vocabulaire adapté au thème (études, centre de formation, cours, ambiance, professeur). Orthographe usuelle correcte.</td><td class="pts">/ 3 pts</td></tr>
        <tr><td><strong>4. Cohérence &amp; Organisation</strong></td><td>Format d'email respecté (formule de politesse début/fin, paragraphes, connecteurs logiques : <em>and, but, because, also</em>).</td><td class="pts">/ 3 pts</td></tr>
    </table>

    <div class="model-email">
        <strong>Exemple de production modèle (92 mots) :</strong><br>
        &ldquo;Dear Sam,<br>
        I hope you are doing well! I am writing to tell you about my new English course at Institut ILAS. I joined the B1 conversational class last week because I really need to speak more fluently for my future job.<br>
        I absolutely love this course! The lessons are lively, and our teacher explains grammar very clearly with fun speaking games. The atmosphere is friendly and encouraging.<br>
        Next Thursday, we have a speaking debate session. You should definitely come with me! Don't forget to register online beforehand.<br>
        Best regards,<br>
        Alex&rdquo;
    </div>
</div>

<div style="text-align: right; font-size: 10px; color: #64748b; margin-top: 10px; border-top: 1px solid #cbd5e1; padding-top: 4px;">
    Institut ILAS &bull; Document Pédagogique Interne &bull; Évaluation B1 (60 min)
</div>

</body>
</html>
"""
    with open('Corrige_Examen_Anglais_B1_Institut_ILAS.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Corrige_Examen_Anglais_B1_Institut_ILAS.html created successfully.")

    # Generate PDF
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    full_html = os.path.abspath('Corrige_Examen_Anglais_B1_Institut_ILAS.html')
    full_pdf = os.path.abspath('Corrige_Examen_Anglais_B1_Institut_ILAS.pdf')

    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={full_pdf}",
        full_html
    ]
    subprocess.run(cmd, check=True)
    doc = pymupdf.open(full_pdf)
    print(f"Corrige PDF generated: {len(doc)} pages, size: {os.path.getsize(full_pdf)} bytes")

if __name__ == '__main__':
    create_answer_key()
