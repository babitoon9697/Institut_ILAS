# -*- coding: utf-8 -*-
"""
Script to update programme_journalier_ilas.html and programme_journalier_ilas_arabe.html
with the refined rule:
1. Envoi de la fiche pédagogique par WhatsApp aux profs de langues CHAQUE SAMEDI SOIR pour la remplir.
2. Suivi et vérification rigoureuse du remplissage des fiches chaque matin pour assurer le suivi pédagogique.
3. Publication quotidienne (au moins 1 post/jour) sur Facebook, Instagram... réalisée via Canva.
"""

import os
import subprocess
import pymupdf

def update_french():
    with open('programme_journalier_ilas.html', 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('\r\n', '\n')

    # 1. Update Morning Emploi du Temps (Morning verification & follow-up)
    old_morning = """            <tr>
                <td class="time">08h45 – 08h55</td>
                <td class="domain">Emploi du Temps &amp; Fiches Pédagogiques (Langues)</td>
                <td class="actions">
                    <ul class="task-list">
                        <li>Validation des présences formateurs, affectation des salles et <strong>affichage à l'accueil</strong>.</li>
                        <li><strong>Envoi WhatsApp de la fiche pédagogique le matin aux profs de langues uniquement</strong>.</li>
                        <li><strong>Suivi &amp; vérification rigoureuse du remplissage</strong> effectif et complet des fiches retournées.</li>
                    </ul>
                </td>
            </tr>"""

    new_morning = """            <tr>
                <td class="time">08h45 – 08h55</td>
                <td class="domain">Emploi du Temps &amp; Suivi Fiches Pédagogiques (Langues)</td>
                <td class="actions">
                    <ul class="task-list">
                        <li>Validation des présences formateurs, affectation des salles et <strong>affichage à l'accueil</strong>.</li>
                        <li><strong>Suivi &amp; vérification rigoureuse du remplissage</strong> des fiches pédagogiques (envoyées chaque samedi soir aux profs de langues).</li>
                        <li>Relance WhatsApp immédiate des enseignants dont la fiche n'est pas encore complétée.</li>
                    </ul>
                </td>
            </tr>"""

    assert old_morning in content, "old_morning not found in French file"
    content = content.replace(old_morning, new_morning, 1)

    # 2. Update Handover box
    old_handover = """<span><strong>🔄 14h50 – 15h00 : PASSATION D'ÉQUIPE (10 MIN)</strong> — Transmission de la fiche de bord : passage en revue des inscrits du matin, des paiements reçus, <strong>des fiches pédagogiques langues remplies</strong>, des incidents et des urgences.</span>"""
    new_handover = """<span><strong>🔄 14h50 – 15h00 : PASSATION D'ÉQUIPE (10 MIN)</strong> — Transmission de la fiche de bord : passage en revue des inscrits du matin, des paiements reçus, <strong>du suivi des fiches pédagogiques langues remplies (et envoi samedi soir)</strong>, des incidents et des urgences.</span>"""
    assert old_handover in content, "old_handover not found in French file"
    content = content.replace(old_handover, new_handover, 1)

    # 3. Update Evening Permanence to include Saturday evening dispatch
    old_evening_perm = """            <tr>
                <td class="time">20h30 – 21h30</td>
                <td class="domain">Permanence & Cours du Soir</td>
                <td class="actions">
                    <ul class="task-list">
                        <li>Accueil et encadrement des sessions de cours du soir (professionnels / adultes).</li>
                        <li>Pointage des présences du soir et gestion des demandes administratives tardives.</li>
                    </ul>
                </td>
            </tr>"""

    new_evening_perm = """            <tr>
                <td class="time">20h30 – 21h30</td>
                <td class="domain">Permanence &amp; Cours du Soir</td>
                <td class="actions">
                    <ul class="task-list">
                        <li>Accueil et encadrement des sessions de cours du soir (professionnels / adultes).</li>
                        <li>Pointage des présences du soir et gestion des demandes administratives tardives.</li>
                        <li><strong>Chaque Samedi Soir : Envoi WhatsApp des fiches pédagogiques à remplir</strong> à tous les professeurs de langues pour le suivi de la semaine suivante.</li>
                    </ul>
                </td>
            </tr>"""
    assert old_evening_perm in content, "old_evening_perm not found in French file"
    content = content.replace(old_evening_perm, new_evening_perm, 1)

    # 4. Update Page 2 - Section 2 table rows (Status: Remplie & Suivie)
    old_sec2 = """    <div class="section-title">
        <span>2. SUIVI DES FORMATEURS & EMPLOI DU TEMPS DU JOUR</span>
    </div>
    <table class="log-grid">
        <thead>
            <tr>
                <th style="width:22%;">Formateur / Enseignant</th>
                <th style="width:18%;">Matière / Groupe</th>
                <th style="width:9%; text-align:center;">Salle</th>
                <th style="width:15%; text-align:center;">Statut (Présent / Retard)</th>
                <th style="width:18%; text-align:center;">Fiche Pédag. Langues</th>
                <th style="width:18%;">Observations / Remplacement</th>
            </tr>
        </thead>
        <tbody>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] Envoyée&nbsp;&nbsp;[ ] Remplie</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] Envoyée&nbsp;&nbsp;[ ] Remplie</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] Envoyée&nbsp;&nbsp;[ ] Remplie</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] Envoyée&nbsp;&nbsp;[ ] Remplie</td><td></td></tr>
        </tbody>
    </table>"""

    new_sec2 = """    <div class="section-title">
        <span>2. SUIVI DES FORMATEURS & EMPLOI DU TEMPS DU JOUR</span>
    </div>
    <table class="log-grid">
        <thead>
            <tr>
                <th style="width:22%;">Formateur / Enseignant</th>
                <th style="width:18%;">Matière / Groupe</th>
                <th style="width:9%; text-align:center;">Salle</th>
                <th style="width:15%; text-align:center;">Statut (Présent / Retard)</th>
                <th style="width:18%; text-align:center;">Fiche Pédag. Langues</th>
                <th style="width:18%;">Observations / Remplacement</th>
            </tr>
        </thead>
        <tbody>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] Remplie &amp; Suivie</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] Remplie &amp; Suivie</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] Remplie &amp; Suivie</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] Remplie &amp; Suivie</td><td></td></tr>
        </tbody>
    </table>"""
    assert old_sec2 in content, "old_sec2 not found in French file"
    content = content.replace(old_sec2, new_sec2, 1)

    # 5. Update Page 2 - Section 4
    old_sec4 = """    <div class="section-title">
        <span>4. SUIVI ABSENCES, FICHES PÉDAGOGIQUES, PAIEMENTS & BADGES</span>
    </div>
    <table class="log-grid">
        <tr>
            <td style="width:24%;"><strong>Messages parents envoyés :</strong><br>[ ] Oui&nbsp;&nbsp;&nbsp;&nbsp;[ ] Non<br>Total absents : .......</td>
            <td style="width:29%;"><strong>Fiches Pédagogiques (Langues) :</strong><br>[ ] Envoyées WhatsApp (Matin)<br>[ ] Remplies &amp; Vérifiées (..... / .....)</td>
            <td style="width:24%;"><strong>Relances paiements :</strong><br>[ ] Oui&nbsp;&nbsp;&nbsp;&nbsp;[ ] Non<br>Total relancés : .......</td>
            <td style="width:23%;"><strong>Cartes d'étudiants :</strong><br>Quantité : ....... badges</td>
        </tr>
    </table>"""

    new_sec4 = """    <div class="section-title">
        <span>4. SUIVI ABSENCES, FICHES PÉDAGOGIQUES, PAIEMENTS & BADGES</span>
    </div>
    <table class="log-grid">
        <tr>
            <td style="width:24%;"><strong>Messages parents envoyés :</strong><br>[ ] Oui&nbsp;&nbsp;&nbsp;&nbsp;[ ] Non<br>Total absents : .......</td>
            <td style="width:29%;"><strong>Fiches Pédagogiques (Langues) :</strong><br>[ ] Envoyées WhatsApp (Samedi Soir)<br>[ ] Remplies &amp; Suivies (..... / .....)</td>
            <td style="width:24%;"><strong>Relances paiements :</strong><br>[ ] Oui&nbsp;&nbsp;&nbsp;&nbsp;[ ] Non<br>Total relancés : .......</td>
            <td style="width:23%;"><strong>Cartes d'étudiants :</strong><br>Quantité : ....... badges</td>
        </tr>
    </table>"""
    assert old_sec4 in content, "old_sec4 not found in French file"
    content = content.replace(old_sec4, new_sec4, 1)

    with open('programme_journalier_ilas.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("programme_journalier_ilas.html updated successfully with Saturday Evening dispatch!")


def update_arabic():
    with open('programme_journalier_ilas_arabe.html', 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('\r\n', '\n')

    # 1. Update Morning Emploi du Temps
    old_morning_ar = """            <tr>
                <td class="time">08:45 – 08:55</td>
                <td class="domain">جدول التوقيت والجذاذات البيداغوجية (اللغات)</td>
                <td class="actions">
                    <ul class="task-list">
                        <li>تأكيد حضور الأساتذة، ضبط وتوزيع القاعات، و<strong>تعليق جدول اليوم في الاستقبال</strong> للطلاب.</li>
                        <li><strong>إرسال الجذاذة البيداغوجية عبر واتساب صباحاً لأساتذة اللغات فقط</strong> (حصص اللغات).</li>
                        <li><strong>المتابعة والتحقق الصارم من استيفاء وملء الجذاذات</strong> المستلمة من أساتذة اللغات.</li>
                    </ul>
                </td>
            </tr>"""

    new_morning_ar = """            <tr>
                <td class="time">08:45 – 08:55</td>
                <td class="domain">جدول التوقيت ومتابعة الجذاذات البيداغوجية (اللغات)</td>
                <td class="actions">
                    <ul class="task-list">
                        <li>تأكيد حضور الأساتذة، ضبط وتوزيع القاعات، و<strong>تعليق جدول اليوم في الاستقبال</strong> للطلاب.</li>
                        <li><strong>المتابعة والتحقق الصارم من استيفاء وملء الجذاذات البيداغوجية</strong> لأساتذة اللغات (المرسلة مساء كل سبت).</li>
                        <li>تذكير ومتابعة الأساتذة الذين لم يستكملوا ملء الجذاذة لضمان حسن سير الدروس.</li>
                    </ul>
                </td>
            </tr>"""
    assert old_morning_ar in content, "old_morning_ar not found in Arabic file"
    content = content.replace(old_morning_ar, new_morning_ar, 1)

    # 2. Update Handover box
    old_handover_ar = """<span><strong>🔄 14:50 – 15:00 : جلسة تسليم المهام بين الفترتين (10 دقائق)</strong> — تسليم ورقة المتابعة اليومية: إحاطة فريق المساء بالمستجدات، والمسجلين الجدد، والمبالغ المستلمة، <strong>واستيفاء جذاذات أساتذة اللغات ومراقبة ملئها</strong>، والتعليمات العاجلة.</span>"""
    new_handover_ar = """<span><strong>🔄 14:50 – 15:00 : جلسة تسليم المهام بين الفترتين (10 دقائق)</strong> — تسليم ورقة المتابعة اليومية: إحاطة فريق المساء بالمستجدات، والمسجلين الجدد، والمبالغ المستلمة، <strong>ومتابعة جذاذات أساتذة اللغات المستوفاة (والتأكيد على إرسالها مساء كل سبت)</strong>، والتعليمات العاجلة.</span>"""
    assert old_handover_ar in content, "old_handover_ar not found in Arabic file"
    content = content.replace(old_handover_ar, new_handover_ar, 1)

    # 3. Update Evening Permanence
    old_evening_perm_ar = """            <tr>
                <td class="time">20:30 – 21:30</td>
                <td class="domain">مداومة ومتابعة الدروس الليلية</td>
                <td class="actions">
                    <ul class="task-list">
                        <li>استقبال ومتابعة حصص الدروس المسائية/الليلية (المهنيين والكبار).</li>
                        <li>حصر حضور المساء وتوفير الدعم الإداري والتقني للأساتذة.</li>
                    </ul>
                </td>
            </tr>"""

    new_evening_perm_ar = """            <tr>
                <td class="time">20:30 – 21:30</td>
                <td class="domain">مداومة ومتابعة الدروس الليلية</td>
                <td class="actions">
                    <ul class="task-list">
                        <li>استقبال ومتابعة حصص الدروس المسائية/الليلية (المهنيين والكبار).</li>
                        <li>حصر حضور المساء وتوفير الدعم الإداري والتقني للأساتذة.</li>
                        <li><strong>مساء كل سبت : الإرسال الإلزامي للجذاذة البيداغوجية عبر واتساب</strong> لجميع أساتذة اللغات لتعبئتها ومتابعة الأسبوع القادم.</li>
                    </ul>
                </td>
            </tr>"""
    assert old_evening_perm_ar in content, "old_evening_perm_ar not found in Arabic file"
    content = content.replace(old_evening_perm_ar, new_evening_perm_ar, 1)

    # 4. Update Page 2 - Section 2 table
    old_sec2_ar = """    <div class="section-title">
        <span>2. جدول متابعة الأساتذة وسير الحصص</span>
    </div>
    <table class="log-grid">
        <thead>
            <tr>
                <th style="width:22%;">الأستاذ / المكون</th>
                <th style="width:18%;">المادة / الفوج</th>
                <th style="width:9%; text-align:center;">القاعة</th>
                <th style="width:15%; text-align:center;">الحالة (حاضر / تأخر)</th>
                <th style="width:18%; text-align:center;">الجذاذة البيداغوجية (اللغات)</th>
                <th style="width:18%;">ملاحظات / تعويض</th>
            </tr>
        </thead>
        <tbody>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] أُرسلت&nbsp;&nbsp;[ ] تم الملء</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] أُرسلت&nbsp;&nbsp;[ ] تم الملء</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] أُرسلت&nbsp;&nbsp;[ ] تم الملء</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] أُرسلت&nbsp;&nbsp;[ ] تم الملء</td><td></td></tr>
        </tbody>
    </table>"""

    new_sec2_ar = """    <div class="section-title">
        <span>2. جدول متابعة الأساتذة وسير الحصص</span>
    </div>
    <table class="log-grid">
        <thead>
            <tr>
                <th style="width:22%;">الأستاذ / المكون</th>
                <th style="width:18%;">المادة / الفوج</th>
                <th style="width:9%; text-align:center;">القاعة</th>
                <th style="width:15%; text-align:center;">الحالة (حاضر / تأخر)</th>
                <th style="width:18%; text-align:center;">الجذاذة البيداغوجية (اللغات)</th>
                <th style="width:18%;">ملاحظات / تعويض</th>
            </tr>
        </thead>
        <tbody>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] تم الاستيفاء والمتابعة</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] تم الاستيفاء والمتابعة</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] تم الاستيفاء والمتابعة</td><td></td></tr>
            <tr><td style="height:19px;"></td><td></td><td></td><td></td><td style="text-align:center; font-size:7pt; color:#475569;">[ ] تم الاستيفاء والمتابعة</td><td></td></tr>
        </tbody>
    </table>"""
    assert old_sec2_ar in content, "old_sec2_ar not found in Arabic file"
    content = content.replace(old_sec2_ar, new_sec2_ar, 1)

    # 5. Update Page 2 - Section 4
    old_sec4_ar = """    <div class="section-title">
        <span>4. متابعة الغيابات، الجذاذات البيداغوجية، المدفوعات والبطاقات</span>
    </div>
    <table class="log-grid">
        <tr>
            <td style="width:24%;"><strong>رسائل أولياء الأمور:</strong><br>[ ] تم الإرسال&nbsp;&nbsp;&nbsp;&nbsp;[ ] لم يُرسل<br>العدد: .......</td>
            <td style="width:29%;"><strong>الجذاذة البيداغوجية (اللغات):</strong><br>[ ] أُرسلت واتساب صباحاً<br>[ ] تم التحقق من الملء (..... / .....)</td>
            <td style="width:24%;"><strong>مطالبات الواتساب للمستحقات:</strong><br>[ ] تم الإرسال&nbsp;&nbsp;&nbsp;&nbsp;[ ] لم يُرسل<br>العدد: .......</td>
            <td style="width:23%;"><strong>بطاقات الطلاب المطبوعة:</strong><br>العدد المنجز: ....... بطاقة</td>
        </tr>
    </table>"""

    new_sec4_ar = """    <div class="section-title">
        <span>4. متابعة الغيابات، الجذاذات البيداغوجية، المدفوعات والبطاقات</span>
    </div>
    <table class="log-grid">
        <tr>
            <td style="width:24%;"><strong>رسائل أولياء الأمور:</strong><br>[ ] تم الإرسال&nbsp;&nbsp;&nbsp;&nbsp;[ ] لم يُرسل<br>العدد: .......</td>
            <td style="width:29%;"><strong>الجذاذة البيداغوجية (اللغات):</strong><br>[ ] أُرسلت بالواتساب (مساء كل سبت)<br>[ ] تم التحقق من الملء والمتابعة (..... / .....)</td>
            <td style="width:24%;"><strong>مطالبات الواتساب للمستحقات:</strong><br>[ ] تم الإرسال&nbsp;&nbsp;&nbsp;&nbsp;[ ] لم يُرسل<br>العدد: .......</td>
            <td style="width:23%;"><strong>بطاقات الطلاب المطبوعة:</strong><br>العدد المنجز: ....... بطاقة</td>
        </tr>
    </table>"""
    assert old_sec4_ar in content, "old_sec4_ar not found in Arabic file"
    content = content.replace(old_sec4_ar, new_sec4_ar, 1)

    with open('programme_journalier_ilas_arabe.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("programme_journalier_ilas_arabe.html updated successfully with Saturday Evening dispatch!")


def generate_pdf(html_path, pdf_path):
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    full_html = os.path.abspath(html_path)
    full_pdf = os.path.abspath(pdf_path)

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
    print(f"Generated {pdf_path}: {len(doc)} pages, size: {os.path.getsize(full_pdf)} bytes")
    return len(doc)


if __name__ == '__main__':
    update_french()
    update_arabic()
    p_fr = generate_pdf('programme_journalier_ilas.html', 'Programme_Journalier_Institut_ILAS.pdf')
    p_ar = generate_pdf('programme_journalier_ilas_arabe.html', 'Programme_Journalier_Institut_ILAS_Arabe.pdf')
    print(f"French pages: {p_fr}, Arabic pages: {p_ar}")
