# -*- coding: utf-8 -*-
"""
Generate a professional, ready-to-print 2-page B1 English Exam for Institut ILAS.
Strict 2-page layout, duration 60 minutes, CEFR B1 level (50% difficulty index: accessible intermediate).
Includes:
- Reading Comprehension (14 pts)
- Use of English / Grammar (14 pts)
- Guided Written Expression (12 pts)
Total = 40 pts (Scale to 20/20).
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

def create_exam_html():
    logo_b64 = get_logo_base64()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Institut ILAS - B1 English Examination</title>
<style>
    @page {{
        size: A4 portrait;
        margin: 8mm 12mm 8mm 12mm;
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
        font-size: 11.5px;
        line-height: 1.35;
        background: #fff;
    }}
    .page {{
        width: 100%;
        min-height: 280mm;
        max-height: 280mm;
        position: relative;
        page-break-after: always;
        overflow: hidden;
    }}
    .page:last-child {{
        page-break-after: avoid;
    }}

    /* Header styling */
    .exam-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 2px solid #0d5c75;
        padding-bottom: 6px;
        margin-bottom: 8px;
    }}
    .header-left {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .header-logo {{
        height: 52px;
        width: auto;
        object-fit: contain;
    }}
    .header-inst-text h1 {{
        margin: 0;
        font-size: 16px;
        color: #0d5c75;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .header-inst-text p {{
        margin: 2px 0 0 0;
        font-size: 10px;
        color: #64748b;
        font-weight: 500;
    }}
    .header-right {{
        text-align: right;
    }}
    .badge-b1 {{
        display: inline-block;
        background: #0d5c75;
        color: #ffffff;
        font-weight: 700;
        font-size: 11px;
        padding: 3px 10px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 3px;
    }}
    .header-meta {{
        font-size: 10px;
        color: #334155;
        font-weight: 600;
    }}

    /* Student info box */
    .student-box {{
        border: 1px solid #cbd5e1;
        background: #f8fafc;
        border-radius: 5px;
        padding: 6px 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
    }}
    .student-field {{
        display: inline-block;
    }}
    .field-label {{
        font-weight: 600;
        color: #475569;
    }}
    .dots {{
        display: inline-block;
        border-bottom: 1px dotted #64748b;
        min-width: 140px;
        height: 12px;
        margin-left: 4px;
    }}
    .score-box {{
        border: 2px solid #0d5c75;
        background: #ffffff;
        border-radius: 4px;
        padding: 4px 12px;
        text-align: center;
        font-weight: 700;
        font-size: 12px;
        color: #0d5c75;
        min-width: 100px;
    }}
    .score-box span {{
        font-size: 9.5px;
        display: block;
        color: #64748b;
        font-weight: normal;
    }}

    /* Section Titles */
    .section-title {{
        background: #e2e8f0;
        border-left: 4px solid #0d5c75;
        padding: 4px 8px;
        font-weight: 700;
        font-size: 12px;
        color: #0f172a;
        margin: 6px 0 6px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 0 4px 4px 0;
    }}
    .section-pts {{
        font-size: 10.5px;
        color: #0d5c75;
        font-weight: 700;
    }}

    /* Reading passage box */
    .reading-box {{
        border: 1px solid #e2e8f0;
        background: #ffffff;
        padding: 8px 10px;
        border-radius: 4px;
        margin-bottom: 8px;
        font-size: 11px;
        line-height: 1.4;
        text-align: justify;
    }}
    .reading-title {{
        font-weight: 700;
        color: #0d5c75;
        text-align: center;
        margin-bottom: 4px;
        font-size: 11.5px;
    }}

    /* Questions formatting */
    .question-block {{
        margin-bottom: 6px;
    }}
    .q-title {{
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 3px;
        font-size: 11px;
    }}
    .mcq-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 4px 10px;
        margin-bottom: 6px;
    }}
    .mcq-item {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 10.5px;
    }}
    .mcq-q {{
        font-weight: 600;
        margin-bottom: 2px;
    }}
    .mcq-options {{
        margin-left: 6px;
        line-height: 1.3;
    }}

    .tf-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 10.5px;
        margin-bottom: 6px;
    }}
    .tf-table th, .tf-table td {{
        border: 1px solid #cbd5e1;
        padding: 4px 6px;
    }}
    .tf-table th {{
        background: #f1f5f9;
        font-weight: 600;
        text-align: left;
    }}
    .tf-center {{
        text-align: center;
        width: 45px;
    }}

    .vocab-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 4px 12px;
        font-size: 10.5px;
    }}

    /* Exercise rows */
    .exercise-list {{
        list-style-type: decimal;
        margin: 0;
        padding-left: 18px;
        font-size: 10.5px;
    }}
    .exercise-list li {{
        margin-bottom: 4px;
        line-height: 1.35;
    }}
    .fill-line {{
        display: inline-block;
        border-bottom: 1px solid #334155;
        min-width: 90px;
        height: 12px;
        margin: 0 4px;
    }}

    /* Writing Section */
    .writing-prompt-box {{
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 4px;
        padding: 6px 10px;
        margin-bottom: 6px;
        font-size: 10.5px;
        line-height: 1.35;
    }}
    .writing-lines {{
        width: 100%;
        border: 1px solid #cbd5e1;
        background: repeating-linear-gradient(#ffffff, #ffffff 21px, #e2e8f0 22px);
        height: 200px;
        border-radius: 4px;
        margin-bottom: 6px;
        padding: 4px 8px;
        line-height: 22px;
        font-family: inherit;
        font-size: 11px;
    }}

    /* Rubric footer table */
    .footer-rubric {{
        width: 100%;
        border-collapse: collapse;
        font-size: 9.5px;
        margin-top: 4px;
    }}
    .footer-rubric td {{
        border: 1px solid #cbd5e1;
        padding: 3px 6px;
        text-align: center;
    }}
    .footer-rubric .label-td {{
        background: #f8fafc;
        font-weight: 600;
        text-align: left;
    }}

    .page-footer {{
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid #e2e8f0;
        padding-top: 3px;
        font-size: 9px;
        color: #94a3b8;
    }}
</style>
</head>
<body>

<!-- ================= PAGE 1 ================= -->
<div class="page">
    <!-- Header -->
    <div class="exam-header">
        <div class="header-left">
            <img src="{logo_b64}" alt="Institut ILAS" class="header-logo" />
            <div class="header-inst-text">
                <h1>INSTITUT ILAS</h1>
                <p>Language Learning &amp; Academic Center &bull; Formation Continue &amp; Certifications</p>
            </div>
        </div>
        <div class="header-right">
            <div class="badge-b1">ENGLISH &bull; LEVEL B1</div>
            <div class="header-meta">Session Evaluation &bull; Duration: 1h00 &bull; Total: 40 pts</div>
        </div>
    </div>

    <!-- Student details bar -->
    <div class="student-box">
        <div>
            <span class="field-label">Candidate Name:</span>
            <span class="dots" style="min-width:180px;"></span>
        </div>
        <div>
            <span class="field-label">Group / Class:</span>
            <span class="dots" style="min-width:90px;"></span>
        </div>
        <div>
            <span class="field-label">Date:</span>
            <span class="dots" style="min-width:80px;"></span>
        </div>
        <div class="score-box">
            Score: &nbsp;&nbsp;&nbsp;&nbsp; / 40
            <span>(Final: &nbsp;&nbsp;&nbsp;&nbsp; / 20)</span>
        </div>
    </div>

    <!-- SECTION 1 -->
    <div class="section-title">
        <span>SECTION 1: READING COMPREHENSION &bull; The Life of a Modern Digital Nomad</span>
        <span class="section-pts">14 POINTS</span>
    </div>

    <!-- Text -->
    <div class="reading-box">
        <div class="reading-title">Working from Anywhere: The Rise of Digital Nomads</div>
        <p style="margin: 0 0 4px 0;">
            In recent years, the way professionals work has transformed dramatically. Thanks to reliable high-speed internet and lightweight portable computers, millions of employees and freelancers are abandoning traditional office desks. These workers are known as <strong>digital nomads</strong>. Instead of commuting to a fixed company office every day, they work remotely from coffee shops, shared workspaces, or quiet apartments across different countries.
        </p>
        <p style="margin: 0 0 4px 0;">
            Liam Carter, a 28-year-old graphic designer from the UK, decided to embrace this lifestyle two years ago. <em>"At the beginning, my family was worried that I was putting my career at risk,"</em> Liam explains. <em>"However, I am actually much more productive now. I organize my own weekly schedule and complete projects for international clients while learning about new cultures."</em>
        </p>
        <p style="margin: 0;">
            Nevertheless, this modern lifestyle comes with distinct difficulties. Moving constantly from one city to another can become physically exhausting, and being far away from friends during special events is sometimes lonely. Furthermore, digital nomads must manage their own administrative paperwork and adapt to diverse time zones. Despite these real challenges, Liam has no intention of returning to a traditional 9-to-5 desk job in the near future.
        </p>
    </div>

    <!-- Part A: Multiple Choice -->
    <div class="question-block">
        <div class="q-title">A. Choose the correct answer (A, B, or C): <span style="font-weight:normal; color:#64748b;">(4 &times; 1 pt = 4 pts)</span></div>
        <div class="mcq-grid">
            <div class="mcq-item">
                <div class="mcq-q">1. Digital nomads can work globally mainly because of:</div>
                <div class="mcq-options">
                    [ &nbsp; ] <strong>A.</strong> Free international flights.<br>
                    [ &nbsp; ] <strong>B.</strong> Fast internet and laptops.<br>
                    [ &nbsp; ] <strong>C.</strong> Strict daily office guidelines.
                </div>
            </div>
            <div class="mcq-item">
                <div class="mcq-q">2. When Liam started this lifestyle, his family:</div>
                <div class="mcq-options">
                    [ &nbsp; ] <strong>A.</strong> Felt concerned about his career.<br>
                    [ &nbsp; ] <strong>B.</strong> Decided to travel along with him.<br>
                    [ &nbsp; ] <strong>C.</strong> Encouraged him to buy a house.
                </div>
            </div>
            <div class="mcq-item">
                <div class="mcq-q">3. Liam feels that working remotely has made him:</div>
                <div class="mcq-options">
                    [ &nbsp; ] <strong>A.</strong> Less productive than in an office.<br>
                    [ &nbsp; ] <strong>B.</strong> More productive and independent.<br>
                    [ &nbsp; ] <strong>C.</strong> Reluctant to accept new clients.
                </div>
            </div>
            <div class="mcq-item">
                <div class="mcq-q">4. According to paragraph 3, one main disadvantage is:</div>
                <div class="mcq-options">
                    [ &nbsp; ] <strong>A.</strong> High cost of computers.<br>
                    [ &nbsp; ] <strong>B.</strong> Loneliness and constant traveling.<br>
                    [ &nbsp; ] <strong>C.</strong> Strict vacation rules from bosses.
                </div>
            </div>
        </div>
    </div>

    <!-- Part B: True/False -->
    <div class="question-block">
        <div class="q-title">B. Are these statements True or False? Justify with a short quote from the text: <span style="font-weight:normal; color:#64748b;">(3 &times; 2 pts = 6 pts)</span></div>
        <table class="tf-table">
            <thead>
                <tr>
                    <th style="width: 48%;">Statement</th>
                    <th class="tf-center">T / F</th>
                    <th style="width: 44%;">Justification from text</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>1.</strong> Liam has been living as a digital nomad for over five years.</td>
                    <td class="tf-center">[ &nbsp;&nbsp;&nbsp; ]</td>
                    <td>Quote: &ldquo;.......................................................................................&rdquo;</td>
                </tr>
                <tr>
                    <td><strong>2.</strong> Liam works exclusively for companies based in his hometown.</td>
                    <td class="tf-center">[ &nbsp;&nbsp;&nbsp; ]</td>
                    <td>Quote: &ldquo;.......................................................................................&rdquo;</td>
                </tr>
                <tr>
                    <td><strong>3.</strong> Liam wants to return to an ordinary 9-to-5 desk job very soon.</td>
                    <td class="tf-center">[ &nbsp;&nbsp;&nbsp; ]</td>
                    <td>Quote: &ldquo;.......................................................................................&rdquo;</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Part C: Vocabulary -->
    <div class="question-block">
        <div class="q-title">C. Find words or phrases in the text that mean the same as: <span style="font-weight:normal; color:#64748b;">(4 &times; 1 pt = 4 pts)</span></div>
        <div class="vocab-grid">
            <div>1. Changed substantially <em>(Paragraph 1)</em>: <strong>........................................</strong></div>
            <div>2. Traveling between home and work <em>(Paragraph 1)</em>: <strong>........................................</strong></div>
            <div>3. Hardships / obstacles <em>(Paragraph 3)</em>: <strong>........................................</strong></div>
            <div>4. Traditional / normal <em>(Paragraph 3)</em>: <strong>........................................</strong></div>
        </div>
    </div>

    <!-- Footer -->
    <div class="page-footer">
        <span>Institut ILAS &bull; B1 English Examination &bull; 50% Intermediate Baseline</span>
        <span>Page 1 / 2 &mdash; Turn over &rarr;</span>
    </div>
</div>

<!-- ================= PAGE 2 ================= -->
<div class="page">
    <!-- Header Page 2 -->
    <div class="exam-header" style="margin-bottom: 6px;">
        <div class="header-left">
            <span style="font-weight: 800; font-size: 13px; color: #0d5c75;">INSTITUT ILAS</span>
            <span style="color: #64748b; font-size: 11px;">&bull; Candidate Name: _____________________________________</span>
        </div>
        <div class="header-right">
            <span class="badge-b1" style="font-size: 10px; padding: 2px 8px;">ENGLISH B1 &bull; PAGE 2</span>
        </div>
    </div>

    <!-- SECTION 2 -->
    <div class="section-title">
        <span>SECTION 2: USE OF ENGLISH &amp; GRAMMAR</span>
        <span class="section-pts">14 POINTS</span>
    </div>

    <!-- Task 1: Verb Tenses -->
    <div class="question-block">
        <div class="q-title">A. Put the verbs in brackets into the correct tense or form: <span style="font-weight:normal; color:#64748b;">(6 &times; 1 pt = 6 pts)</span></div>
        <ol class="exercise-list">
            <li>While my classmate <span class="fill-line" style="min-width:130px;"></span> (prepare) her presentation yesterday, her laptop suddenly shut down.</li>
            <li>Mr. Taylor is a passionate instructor; he <span class="fill-line" style="min-width:130px;"></span> (teach) English at Institut ILAS for three years.</li>
            <li>If Sarah finishes her project early tomorrow afternoon, she <span class="fill-line" style="min-width:120px;"></span> (join) us for the speaking workshop.</li>
            <li>If I had enough savings, I <span class="fill-line" style="min-width:130px;"></span> (travel) to Canada to practice my English with native speakers.</li>
            <li>We <span class="fill-line" style="min-width:130px;"></span> (not / receive) any confirmation email since we submitted the registration form.</li>
            <li>When we arrived at the classroom, we found out that the teacher <span class="fill-line" style="min-width:120px;"></span> (already / start) the lecture.</li>
        </ol>
    </div>

    <!-- Task 2: Relative Pronouns & Linking Words -->
    <div class="question-block">
        <div class="q-title">B. Circle or underline the correct word in brackets: <span style="font-weight:normal; color:#64748b;">(4 &times; 1 pt = 4 pts)</span></div>
        <ol class="exercise-list">
            <li>The multimedia laboratory ( <strong>which</strong> / <strong>where</strong> / <strong>who</strong> ) we listen to audio tracks was renovated last month.</li>
            <li>Mrs. Adams is the language supervisor ( <strong>whose</strong> / <strong>which</strong> / <strong>who</strong> ) evaluates the students' final oral exams.</li>
            <li>( <strong>Although</strong> / <strong>Because</strong> / <strong>Despite</strong> ) the exam was comprehensive, Adam managed his time very effectively.</li>
            <li>Nour practiced conversation every single day, ( <strong>so</strong> / <strong>however</strong> / <strong>but</strong> ) she spoke with great confidence during the test.</li>
        </ol>
    </div>

    <!-- Task 3: Modal Verbs -->
    <div class="question-block">
        <div class="q-title">C. Complete each sentence with: <em>must &bull; don't have to &bull; shouldn't &bull; mustn't</em>: <span style="font-weight:normal; color:#64748b;">(4 &times; 1 pt = 4 pts)</span></div>
        <ol class="exercise-list">
            <li>Candidates <span class="fill-line" style="min-width:100px;"></span> look at their neighbor's paper; any attempt of cheating results in disqualification.</li>
            <li>You <span class="fill-line" style="min-width:100px;"></span> buy the textbook immediately; digital copies are available for free in the student portal.</li>
            <li>You look very tired before the exam; you <span class="fill-line" style="min-width:100px;"></span> stay awake all night studying without getting sleep.</li>
            <li>To obtain the B1 certificate, each student <span class="fill-line" style="min-width:100px;"></span> obtain at least 50% of the total score.</li>
        </ol>
    </div>

    <!-- SECTION 3 -->
    <div class="section-title">
        <span>SECTION 3: GUIDED WRITTEN PRODUCTION &bull; Email to a Friend</span>
        <span class="section-pts">12 POINTS</span>
    </div>

    <div class="writing-prompt-box">
        <strong>Prompt:</strong> You have recently joined an English training course at <strong>Institut ILAS</strong>. Write an email <strong>(80 to 100 words)</strong> to your friend, Sam, describing your experience:
        <ul style="margin: 2px 0 0 16px; padding: 0;">
            <li>Explain which course you attend and why you chose it.</li>
            <li>Describe what you like most about the lessons, the teacher, or the institute atmosphere.</li>
            <li>Invite Sam to join the next session and give one piece of practical advice.</li>
        </ul>
    </div>

    <div class="writing-lines">
To: sam.walker@example.com &nbsp;&nbsp;|&nbsp;&nbsp; Subject: My new English classes at Institut ILAS!
Dear Sam,
...................................................................................................................................................................................................................
...................................................................................................................................................................................................................
...................................................................................................................................................................................................................
...................................................................................................................................................................................................................
...................................................................................................................................................................................................................
...................................................................................................................................................................................................................
...................................................................................................................................................................................................................
...................................................................................................................................................................................................................
Best regards, [Your Name]
    </div>

    <!-- Examiner Rubric -->
    <table class="footer-rubric">
        <tr>
            <td class="label-td" style="width: 25%;"><strong>Writing Assessment:</strong></td>
            <td>Task Fulfillment: &nbsp; / 3</td>
            <td>Grammar &amp; Accuracy: &nbsp; / 3</td>
            <td>Vocabulary Range: &nbsp; / 3</td>
            <td>Structure &amp; Cohesion: &nbsp; / 3</td>
            <td style="font-weight: 700; color: #0d5c75; width: 18%;">Writing Total: &nbsp;&nbsp;&nbsp;&nbsp; / 12</td>
        </tr>
    </table>

    <!-- Footer -->
    <div class="page-footer">
        <span>Institut ILAS &bull; Examiner's signature: ______________________ &bull; Final Grade: _______ / 20</span>
        <span>Page 2 / 2 &bull; End of Examination</span>
    </div>
</div>

</body>
</html>
"""
    with open('Examen_Anglais_B1_Institut_ILAS.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Examen_Anglais_B1_Institut_ILAS.html created successfully.")

if __name__ == '__main__':
    create_exam_html()
