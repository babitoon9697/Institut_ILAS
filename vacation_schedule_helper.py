import sqlite3
import random
import re
from collections import defaultdict
from datetime import date, timedelta

# Import the solved vacation schedule generator
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scratch'))
from generate_final_18_21 import build_perfect_zero_conflict_schedule

CLEAN_COURSE_TITLES = {
    1: "Anglais Débutant — Groupe 1",
    4: "Anglais Adultes — Groupe 1",
    5: "Français Adultes — Groupe 2",
    7: "Anglais Adultes — Groupe 2 (B1)",
    8: "Anglais Adultes — Groupe 1 (A1)",
    10: "Anglais Général — Groupe 1 (A2)",
    13: "Allemand Adultes — Groupe 1",
    16: "Allemand — Groupe 1 (A1)",
    17: "Allemand — Groupe 2 (A2)",
    18: "Français Adultes — Groupe 2",
    19: "Français Adultes — Groupe 1",
    20: "Allemand Adultes — Groupe 1 (A1)",
    21: "Espagnol Général — Groupe 1",
    22: "Anglais Adultes — Groupe 1",
    23: "2 BAC SX — Mathématiques",
    24: "1 BAC SX — Mathématiques",
    25: "2 BAC SX — SVT",
    26: "2 BAC SX — Physique-Chimie",
    27: "1 BAC SX — Français Régional",
    28: "1 BAC SX — Physique-Chimie",
    29: "Tronc Commun — Mathématiques",
    30: "Tronc Commun — Physique-Chimie",
    31: "3ème Collège — Mathématiques",
    32: "3ème Collège — Physique-Chimie",
    33: "3ème Collège — SVT",
    38: "1ère Collège — Soutien PC/Maths/SVT",
    39: "Primaire — Soutien Toutes Matières",
    40: "Français Enfants — Groupe 1",
    42: "Anglais Enfants — Groupe 2",
    43: "Français Adultes — Groupe 3",
    45: "Anglais Adultes — Groupe 2",
    46: "Français Enfants — Groupe 2",
    47: "Anglais Général — Groupe 4",
    50: "Français Primaire — Groupe 1",
    52: "2 BAC VIP (Fermé) — Maths",
    56: "1 BAC SM — Mathématiques",
    58: "Anglais Général — Groupe 1",
    77: "Anglais Particulier — ELECTROLUX",
    78: "Français Adultes — Groupe 2",
    80: "Anglais Adultes — Groupe 3"
}

CLEAN_SPECIALTIES = {
    'HAMZA BOUBTANA': 'Mathématiques (Lycée : 2BAC SX, 1BAC SX, Tronc Commun)',
    'HAMZA  EL ISSAOUI': 'Physique - Chimie (Lycée : 2BAC SX & 1BAC SX)',
    'ABD ELHAKIM SVT': 'SVT (Lycée : 2ème Année Bac SX)',
    'YOUSSEF  BADR': 'Français Régional (Lycée : 1ère Année Bac SX)',
    'TARIK RADID': 'Physique - Chimie (Lycée : Tronc Commun)',
    'SAID EL OTHMANI': 'Mathématiques & PC (Collège : 3ème Collège)',
    'HASSAN NACHAT': 'SVT & Soutien Collège (3ème Collège & 1ère Collège)',
    'MATOUK AYMANE': 'Mathématiques (2BAC VIP Fermé & 1BAC Sciences Maths)',
    'LEILA LOUTFI': 'Français & Soutien Primaire (Toutes matières)',
    'MALIKA FR': 'Français Enfants (Groupes 1 & 2)',
    'Hakima EL BRIJ': 'Français Adultes / Communication (Groupes 2 & 3)',
    'BOUCHRA LAHMIDI': 'Français Adultes (Groupes 1 & 2 A1-A2)',
    'Fatima Wahbi': 'Français Adultes (Groupe 2 A1-A2)',
    'Aya Garwaho': 'Anglais (Enfants & Adultes)',
    'ILHAM FAKIR': 'Anglais Enfants, Adultes & Particulier Entreprise',
    'HAMZA EL MOTAKI': 'Anglais Adultes (Groupes 1 & 2)',
    'NORDINE BOUGRIR': 'Anglais Adultes (Groupes 1, 2 & 3)',
    'MARYA ANG': 'Anglais Enfants / Débutant (Groupe 1)',
    'YASSINE SAMRANE': 'Anglais Général',
    'RACHID SABRI': 'Allemand (Débutant A1 & Groupe 2)',
    'YASSINE AFFANY': 'Allemand Adultes (Groupe 1: A1)',
    'Ilyas SAKAM': 'Allemand Adultes (Groupe 1)',
    'LINA LAHSINIA': 'Espagnol Général (Groupe 1)'
}

DAYS_INFO = {
    0: {
        'date_iso': '2026-10-19',
        'fr': 'Lundi 19 Octobre 2026',
        'ar': 'الإثنين 19 أكتوبر 2026',
        'en': 'Monday, October 19, 2026',
        'short_fr': 'Lun 19-10'
    },
    1: {
        'date_iso': '2026-10-20',
        'fr': 'Mardi 20 Octobre 2026',
        'ar': 'الثلاثاء 20 أكتوبر 2026',
        'en': 'Tuesday, October 20, 2026',
        'short_fr': 'Mar 20-10'
    },
    2: {
        'date_iso': '2026-10-21',
        'fr': 'Mercredi 21 Octobre 2026',
        'ar': 'الأربعاء 21 أكتوبر 2026',
        'en': 'Wednesday, October 21, 2026',
        'short_fr': 'Mer 21-10'
    },
    3: {
        'date_iso': '2026-10-22',
        'fr': 'Jeudi 22 Octobre 2026',
        'ar': 'الخميس 22 أكتوبر 2026',
        'en': 'Thursday, October 22, 2026',
        'short_fr': 'Jeu 22-10'
    },
    4: {
        'date_iso': '2026-10-23',
        'fr': 'Vendredi 23 Octobre 2026',
        'ar': 'الجمعة 23 أكتوبر 2026',
        'en': 'Friday, October 23, 2026',
        'short_fr': 'Ven 23-10'
    },
    5: {
        'date_iso': '2026-10-24',
        'fr': 'Samedi 24 Octobre 2026',
        'ar': 'السبت 24 أكتوبر 2026',
        'en': 'Saturday, October 24, 2026',
        'short_fr': 'Sam 24-10'
    },
    6: {
        'date_iso': '2026-10-25',
        'fr': 'Dimanche 25 Octobre 2026',
        'ar': 'الأحد 25 أكتوبر 2026',
        'en': 'Sunday, October 25, 2026',
        'short_fr': 'Dim 25-10'
    },
    17: {
        'date_iso': '2026-10-17',
        'fr': 'Samedi 17 Octobre 2026 (Rattrapage)',
        'ar': 'السبت 17 أكتوبر 2026 (استدراك قبل العطلة)',
        'en': 'Saturday, October 17, 2026',
        'short_fr': 'Sam 17-10'
    },
    18: {
        'date_iso': '2026-10-18',
        'fr': 'Dimanche 18 Octobre 2026 (Rattrapage)',
        'ar': 'الأحد 18 أكتوبر 2026 (استدراك قبل العطلة)',
        'en': 'Sunday, October 18, 2026',
        'short_fr': 'Dim 18-10'
    }
}

def clean_phone_number(p):
    if not p:
        return ''
    digits = re.sub(r'\D', '', str(p))
    if digits.startswith('212'):
        digits = digits[3:]
    if digits.startswith('0'):
        digits = digits[1:]
    if len(digits) >= 9:
        return f"212{digits}"
    return ''

def get_vacation_schedule_data():
    """
    Returns the solved vacation schedule without touching any database table.
    """
    assigned, courses_info = build_perfect_zero_conflict_schedule()

    conn = sqlite3.connect('institut.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    teachers_db = c.execute("SELECT id, first_name, last_name, phone, specialty, subjects_taught, photo FROM teachers").fetchall()
    teachers_by_id = {t['id']: dict(t) for t in teachers_db}
    teachers_by_name = {f"{t['first_name']} {t['last_name']}".strip(): dict(t) for t in teachers_db}

    # Group sessions by teacher
    teachers_map = defaultdict(lambda: {
        'teacher_id': None,
        'teacher_name': '',
        'first_name': '',
        'last_name': '',
        'phone': '',
        'clean_phone': '',
        'has_phone': False,
        'specialty': '',
        'avatar_url': '',
        'sessions': []
    })

    for a in assigned:
        tname = a['teacher_name'].strip()
        cid = a['course_id']
        disp_title = CLEAN_COURSE_TITLES.get(cid, courses_info[cid]['short_title'])
        cinfo = courses_info[cid]
        st_count = cinfo['student_count']

        t_db = teachers_by_id.get(a['teacher_id']) or teachers_by_name.get(tname) or {}
        tid = t_db.get('id', a['teacher_id'])
        raw_phone = t_db.get('phone', '')
        clean_p = clean_phone_number(raw_phone)

        t_entry = teachers_map[tid]
        t_entry['teacher_id'] = tid
        t_entry['teacher_name'] = tname
        t_entry['first_name'] = t_db.get('first_name', tname.split()[0])
        t_entry['last_name'] = t_db.get('last_name', '')
        t_entry['phone'] = raw_phone
        t_entry['clean_phone'] = clean_p
        t_entry['has_phone'] = bool(clean_p and len(clean_p) >= 9)
        t_entry['specialty'] = CLEAN_SPECIALTIES.get(tname, t_db.get('specialty', ''))
        t_entry['avatar_url'] = t_db.get('avatar_url') or t_db.get('photo') or ''

        dur_m = a['end'] - a['start']
        dur_txt = f"{dur_m//60}h{dur_m%60:02d}" if dur_m%60 else f"{dur_m//60}h00"

        t_entry['sessions'].append({
            'course_id': cid,
            'course_name': disp_title,
            'raw_title': cinfo['name'],
            'day': a['day'],
            'day_fr': DAYS_INFO[a['day']]['fr'],
            'day_ar': DAYS_INFO[a['day']]['ar'],
            'date_iso': DAYS_INFO[a['day']]['date_iso'],
            'start_str': a['start_str'],
            'end_str': a['end_str'],
            'duration_txt': dur_txt,
            'room_id': a['room_id'],
            'room_name': a['room_name'],
            'room_num': a['room_num'],
            'student_count': st_count
        })

    # Sort sessions chronologically for each teacher
    for tid in teachers_map:
        teachers_map[tid]['sessions'].sort(key=lambda s: (s['day'], s['start_str']))
        # Extract distinct groups
        grps = {}
        for s in teachers_map[tid]['sessions']:
            grps[s['course_id']] = f"{s['course_name']} ({s['student_count']} él.)"
        teachers_map[tid]['groups_summary'] = list(grps.values())
        teachers_map[tid]['total_sessions'] = len(teachers_map[tid]['sessions'])
        teachers_map[tid]['total_students'] = sum(courses_info[cid]['student_count'] for cid in grps)

    conn.close()
    return dict(teachers_map)

def detect_teacher_lang(specialty, subjects):
    text = f"{specialty or ''} {subjects or ''}".lower()
    if 'allemand' in text or 'german' in text or 'deutsch' in text:
        return 'de'
    elif 'espagnol' in text or 'spanish' in text or 'esp' in text:
        return 'es'
    elif 'anglais' in text or 'english' in text or 'ang' in text:
        return 'en'
    elif 'math' in text or 'physique' in text or 'svt' in text or 'pc' in text or 'chimie' in text:
        return 'fr'
    elif 'français' in text or 'francais' in text:
        return 'fr'
    return 'fr'

def generate_spintax_teacher_vacances_timetable(teacher_info, sessions_subset, filter_day=None, lang='fr', inst_name="Institut ILAS", inst_phone="06 60 29 11 55", seed=None):
    """
    Generates an anti-ban WhatsApp timetable notification message for the vacation period.
    Features:
      - Randomized polite greetings
      - Randomized administrative intro
      - Chronological sessions block with exact hours, room name and enrolled count
      - Holiday closure notice (22-25 Octobre fermé, reprise le 26/10)
      - Attendance recording reminder
      - Unique cryptographic hash [Réf: #VAC-EDT-XXXX]
    """
    if seed is None:
        seed = random.randint(1000, 9999)

    tname = teacher_info.get('teacher_name', 'Professeur')
    first_name = teacher_info.get('first_name', tname.split()[0])

    # Filter sessions if a specific day is requested
    if filter_day is not None and filter_day in DAYS_INFO:
        active_sessions = [s for s in sessions_subset if s['day'] == filter_day]
        is_single_day = True
        target_day_name = DAYS_INFO[filter_day]['fr']
    else:
        active_sessions = sessions_subset
        is_single_day = False
        target_day_name = "Du 19 au 25 Octobre 2026"

    # Build sessions block
    sessions_lines = []
    if active_sessions:
        if is_single_day:
            for s in active_sessions:
                room_badge = f"🚪 *Salle :* *{s['room_name']}*"
                eff_badge = f" · 👥 {s['student_count']} élève(s)" if s['student_count'] else ""
                sessions_lines.append(f"▫️ ⏰ *{s['start_str']} - {s['end_str']}* : *{s['course_name']}*\n   {room_badge}{eff_badge}")
        else:
            # Group by day present in active_sessions
            days_present = sorted(list(set(s['day'] for s in active_sessions)))
            for d in days_present:
                day_s = [s for s in active_sessions if s['day'] == d]
                d_fr = DAYS_INFO.get(d, {}).get('fr', f'Jour {d}')
                sessions_lines.append(f"\n📅 *{d_fr.upper()} :*")
                for s in day_s:
                    room_badge = f"🚪 *Salle :* *{s['room_name']}*"
                    eff_badge = f" · 👥 {s['student_count']} élève(s)" if s['student_count'] else ""
                    sessions_lines.append(f"▫️ ⏰ *{s['start_str']} - {s['end_str']}* : *{s['course_name']}*\n   {room_badge}{eff_badge}")
    else:
        sessions_lines.append("▫️ _Aucune séance programmée pour cette période._")

    schedule_block = "\n".join(sessions_lines).strip()

    # Spintax templates by language
    if lang == 'fr':
        greetings = [
            f"Bonjour Cher(e) Professeur *{tname}* 🌸",
            f"Bonjour Professeur *{tname}*, message officiel de la direction {inst_name} 🏫",
            f"Chers collègues, Bonjour *{tname}* 🌹",
            f"Très cher(e) enseignant(e) *{tname}*, nous espérons que vous allez bien 🌸"
        ]
        intros = [
            f"Dans le cadre de l'organisation des *Vacances Scolaires (19 - 25 Octobre 2026)*, voici votre planning officiel des cours et les salles attribuées :",
            f"L'administration de *{inst_name}* a le plaisir de vous transmettre votre emploi du temps pour les *Vacances Scolaires* ({target_day_name}) :",
            f"Veuillez trouver ci-dessous le détail de votre programme de cours officiel pour les *Vacances Scolaires* ainsi que les salles correspondantes :"
        ]
        days_set = set(s['day'] for s in sessions_subset)
        has_weekend_or_late = any(d in (3, 4, 5, 6) for d in days_set)
        has_early_makeup = any(d in (17, 18) for d in days_set)

        if has_early_makeup:
            vac_notice = "📌 *Rattrapage spécial :* Vos séances se déroulent en rattrapage le week-end du 17 et 18 Octobre selon les horaires indiqués ci-dessus."
        elif has_weekend_or_late:
            vac_notice = "📌 *Organisation :* Vos séances se déroulent selon vos créneaux officiels indiqués ci-dessus pendant la semaine du *19 au 25 Octobre 2026*. La reprise générale aura lieu le *Lundi 26 Octobre 2026*."
        else:
            vac_notice = "📌 *Note importante :* Vos séances se déroulent du Lundi au Mercredi. La reprise globale de tous les cours aura lieu le *Lundi 26 Octobre 2026*."

        reminders = [
            "📌 *Consigne d'appel :* Merci d'enregistrer le pointage des présences/absences dès le début de chaque séance via votre espace enseignant.",
            "📌 *Suivi pédagogique :* Pensez à effectuer l'appel des élèves en direct au début de chaque cours afin de garantir un suivi rigoureux.",
            "📌 *Rappel :* L'enregistrement des présences en direct dès l'entame du cours est indispensable pour l'administration."
        ]
        closings = [
            f"Nous vous souhaitons d'excellentes séances et de très bonnes vacances. Merci pour votre dévouement constant.",
            f"Merci infiniment pour votre rigueur et votre engagement auprès de nos apprenants. Excellente semaine à vous.",
            f"Toute l'équipe de *{inst_name}* vous remercie pour votre professionnalisme et vous souhaite une excellente semaine."
        ]
        ref_label = "Réf: #VAC-EDT"

    elif lang == 'en':
        greetings = [
            f"Dear Teacher *{tname}*, Good day 🌸",
            f"Hello Professor *{tname}*, official notice from {inst_name} administration 🏫",
            f"Dear *{tname}*, we hope this message finds you well 🌸"
        ]
        intros = [
            f"Regarding the *School Holidays Schedule (October 19 - 25, 2026)*, please find below your official timetable and assigned classrooms:",
            f"The administration of *{inst_name}* is pleased to provide your official teaching schedule for the *Holiday Period* ({target_day_name}):"
        ]
        days_set = set(s['day'] for s in sessions_subset)
        has_weekend_or_late = any(d in (3, 4, 5, 6) for d in days_set)
        has_early_makeup = any(d in (17, 18) for d in days_set)

        if has_early_makeup:
            vac_notice = "📌 *Special Makeup:* Your sessions take place as makeup on the weekend of Oct 17 & 18 as indicated above."
        elif has_weekend_or_late:
            vac_notice = "📌 *Schedule Note:* Your sessions take place as indicated above during the week of *October 19 to 25, 2026*. Global resumption on *Monday, Oct 26, 2026*."
        else:
            vac_notice = "📌 *Important Note:* Your sessions run from Monday to Wednesday. Global resumption on *Monday, Oct 26, 2026*."

        reminders = [
            "📌 *Attendance Reminder:* Please record student attendance live at the beginning of each session via your teacher portal.",
            "📌 *Instruction:* Please remember to mark attendance on the platform right at the start of your class."
        ]
        closings = [
            f"We wish you fruitful sessions and a great holiday week. Thank you for your continued dedication.",
            f"Thank you for your commitment to our students. Best regards, {inst_name} Team."
        ]
        ref_label = "Ref: #VAC-TIMETABLE"

    else: # 'ar' (Arabic)
        greetings = [
            f"السلام عليكم أستاذنا الفاضل *{tname}* 🌸",
            f"تحية طيبة أستاذ *{tname}*، رسالة رسمية من إدارة {inst_name} 🏫",
            f"أهلاً وسهلاً أستاذ *{tname}*، نرجو أن تكونوا في أتم الصحة والعافية 🌹"
        ]
        intros = [
            f"في إطار تنظيم حصص *العطلة المدرسية (من 19 إلى 25 أكتوبر 2026)*، إليكم جدول حصصكم الرسمي والقاعات المخصصة لكم :",
            f"يسر إدارة *{inst_name}* أن توافيكم ببرنامج حصصكم المبرمجة خلال فترة *العطلة المدرسية* ({target_day_name}) :"
        ]
        days_set = set(s['day'] for s in sessions_subset)
        has_weekend_or_late = any(d in (3, 4, 5, 6) for d in days_set)
        has_early_makeup = any(d in (17, 18) for d in days_set)

        if has_early_makeup:
            vac_notice = "📌 *حصص استدراكية :* حصصكم مبرمجة كاستدراك في نهاية هذا الأسبوع (17 و 18 أكتوبر 2026) حسب الأوقات المحددة أعلاه."
        elif has_weekend_or_late:
            vac_notice = "📌 *ملاحظة تنظيمية :* حصصكم مبرمجة في الأوقات المحددة أعلاه خلال أسبوع العطلة المدرسية (*من 19 إلى 25 أكتوبر 2026*). وتستأنف جميع الدروس بشكل شامل يوم *الإثنين 26 أكتوبر 2026*."
        else:
            vac_notice = "📌 *ملاحظة هامة :* حصصكم مبرمجة من الإثنين إلى الأربعاء. وتستأنف جميع الدروس العادية بشكل شامل يوم *الإثنين 26 أكتوبر 2026*."
        reminders = [
            "📌 *تذكير بيداغوجي :* يرجى تسجيل غياب وحضور التلاميذ مباشرة عند انطلاق كل حصة عبر فضاء الأستاذ بالمنصة.",
            "📌 *توجيه هام :* نرجو الحرص على تدبير الحضور والغياب مع بداية الدرس لضمان التتبع الآني للتلاميذ."
        ]
        closings = [
            f"نتمنى لكم حصصاً موفقة وعطلة سعيدة. مع فائق الشكر والتقدير لجهودكم المتميزة.",
            f"شكراً جزيلاً لالتزامكم الدائم وحرصكم على مصلحة أبنائنا التلاميذ. تقبلوا أطيب تحياتنا."
        ]
        ref_label = "المرجع: #VAC-EDT"

    # Assemble dynamic message
    greet = random.choice(greetings)
    intro = random.choice(intros)
    rem = random.choice(reminders)
    close = random.choice(closings)

    msg = f"""{greet}

{intro}

{schedule_block}

{vac_notice}

{rem}

{close}

🏛️ *{inst_name}*
[{ref_label}-{seed:04d}]"""

    return msg.strip()


def generate_spintax_confirmation_reminder(teacher_info, lang='fr', inst_name="Institut ILAS", inst_phone="06 60 29 11 55", seed=None):
    """
    Generates an urgent confirmation request message for teachers regarding their vacation schedule.
    Requested before 16/10/2026 so administration can notify students tomorrow insha'Allah.
    Includes full Spintax anti-ban rotation and unique cryptographic hash.
    """
    if seed is None:
        seed = random.randint(1000, 9999)

    tname = teacher_info.get('teacher_name', 'Professeur')
    first_name = teacher_info.get('first_name', tname.split()[0])

    if lang == 'fr':
        greetings = [
            f"Bonjour cher Professeur *{tname}* 🌸",
            f"Cher(e) enseignant(e) *{tname}*, nous espérons que vous allez bien 🌹",
            f"Message important de la direction de *{inst_name}* pour *{tname}* 🏫",
            f"Bonjour *{tname}*, message officiel de l'administration {inst_name} 📋"
        ]
        intros = [
            f"Suite à l'envoi de votre planning pour les vacances scolaires (19 - 25 Octobre 2026), nous vous prions de bien vouloir nous *confirmer définitivement votre disponibilité et la validation de votre emploi du temps aujourd'hui (avant le 16/10/2026)*.",
            f"Faisant suite à la transmission de votre emploi du temps pour la période des vacances (19 au 25 Octobre), nous sollicitons votre aimable *confirmation et validation du planning aujourd'hui même (avant le 16/10/2026)*.",
            f"Dans le cadre de l'organisation des cours des vacances scolaires (19 - 25 Octobre), nous vous saurions gré de bien vouloir nous *confirmer la validation de vos créneaux aujourd'hui (délai impératif : avant le 16/10/2026)*."
        ]
        reasons = [
            f"🎯 *Pourquoi cette confirmation urgente ?*\nCette validation est indispensable pour permettre à l'administration d'*informer officiellement tous les élèves et leurs parents dès demain (incha'Allah)* afin qu'ils récupèrent leur emploi du temps et préparent leurs cours de vacances en toute sérénité.",
            f"🎯 *Objet de l'urgence :*\nCette confirmation nous est nécessaire afin de pouvoir *diffuser dès demain matin les emplois du temps définitifs aux élèves et à leurs familles* pour qu'ils soient informés de leurs créneaux de vacances.",
            f"🎯 *Important :*\nLa validation rapide de tous nos enseignants aujourd'hui permettra d'*aviser l'ensemble de nos élèves dès demain incha'Allah* avec leurs horaires et salles confirmés."
        ]
        action_calls = [
            "👉 *Action simple :* Il vous suffit de nous répondre par *« Validé »* ou *« Confirmé »*, ou de nous signaler toute remarque éventuelle au plus vite aujourd'hui.",
            "👉 *Comment répondre :* Un simple message en réponse (*« Validé / D'accord »*) suffit pour valider votre accord.",
            "👉 *Réponse rapide :* Merci de nous renvoyer simplement *« Bien reçu et Validé »* dès que vous prenez connaissance de ce message."
        ]
        closings = [
            "Nous vous remercions chaleureusement pour votre réactivité exemplaire et votre dévouement constant.",
            "Un grand merci pour votre précieuse collaboration et excellente journée à vous.",
            "Merci pour votre confiance et pour votre engagement continu auprès de nos élèves."
        ]
        ref_label = "Réf: #VAC-CONFIRM"

    elif lang == 'en':
        greetings = [
            f"Hello Professor *{tname}*, hope you are having a wonderful day 🌸",
            f"Dear *{tname}*, urgent notice from {inst_name} administration 🏫",
            f"Dear *{tname}*, we hope this message finds you in good health 🌹"
        ]
        intros = [
            f"Following the vacation timetable sent to you (October 19 - 25, 2026), we kindly ask you to *confirm and validate your schedule today (before October 16, 2026)*.",
            f"Further to your vacation teaching timetable, please *officially confirm your availability and approve your schedule today (deadline: before Oct 16, 2026)*."
        ]
        reasons = [
            f"🎯 *Why this urgent confirmation?*\nYour prompt approval is essential so that our administration can *officially notify all students and their parents tomorrow insha'Allah* with their final holiday timetables.",
            f"🎯 *Purpose:*\nWe need your quick confirmation today to allow us to *send out all student schedules tomorrow morning* and finalize group rosters."
        ]
        action_calls = [
            "👉 *Quick Action:* Please simply reply with *'Confirmed'* or *'Validated'*, or let us know if you have any questions today.",
            "👉 *How to reply:* A short reply saying *'Confirmed / Approved'* is all we need to validate your schedule."
        ]
        closings = [
            "Thank you very much for your immediate response and ongoing commitment to our students.",
            "Best regards, and thank you for your great cooperation."
        ]
        ref_label = "Ref: #VAC-CONFIRM"

    else: # 'ar' (Arabic)
        greetings = [
            f"السلام عليكم أستاذنا الفاضل *{tname}* 🌸",
            f"تحية طيبة أستاذ *{tname}*، رسالة هامة وعاجلة من إدارة {inst_name} 🏫",
            f"أهلاً وسهلاً أستاذنا الكريم *{tname}*، نرجو أن تكونوا في أتم الصحة والعافية 🌹",
            f"تحية تقدير واحترام أستاذ *{tname}* من الفريق الإداري لمعهد {inst_name} 🌸"
        ]
        intros = [
            f"عطفاً على جدول حصص *العطلة المدرسية (19 - 25 أكتوبر 2026)* الذي تمت موافاتكم به، نرجو منكم التفضل بـ *تأكيد ومصادقة توقيتكم اليوم (قبل 16/10/2026)*.",
            f"تبعاً لبرنامج حصص العطلة المدرسية المرسل إليكم، نلتمس منكم التكرم بـ *تأكيد موافقتكم النهائية على جدول الحصص اليوم (أجل أقصاه قبل 16/10/2026)*.",
            f"في إطار ضبط الترتيبات البيداغوجية لحصص العطلة، نرجو من جنابكم الكريم *تأكيد جاهزيتكم وبرنامج حصصكم اليوم (قبل 16 أكتوبر 2026)*."
        ]
        reasons = [
            f"🎯 *الهدف من التأكيد اليوم :*\nهذا التأكيد ضروري ومستعجل لكي تتمكن الإدارة من *إخبار جميع التلاميذ وأولياء أمورهم غداً إن شاء الله ببرنامج حصصهم وقاعاتهم* حتى يتسنى لهم استلام جداولهم والاستعداد بشكل مبكر ومريح.",
            f"🎯 *الغاية من التذكير :*\nمصادقتكم اليوم ستمكننا من *موافاة التلاميذ بجداول حصص العطلة ابتداءً من صباح الغد إن شاء الله* وضمان انطلاق الدروس في أحسن الظروف.",
            f"🎯 *توجيه هام :*\nنحتاج تأكيدكم اليوم لنتمكن من *إشعار أولياء الأمور والتلاميذ غداً إن شاء الله بمواعيد دروس العطلة الرسمية*."
        ]
        action_calls = [
            "👉 *طريقة التأكيد :* يكفيكم التفضل بالرد بكلمة *« مؤكد / Validé »* أو إفادتنا بأي ملاحظة في أقرب وقت اليوم.",
            "👉 *طريقة الإجابة :* رسالة مقتضبة منكم بـ *« مؤكد / موافق »* كافية للمصادقة على البرنامج.",
            "👉 *المطلوب :* نرجو إرسال كلمة *« تمت الموافقة / Validé »* عند اطلاعكم على هذه الرسالة."
        ]
        closings = [
            "شاكرين لكم حسن تعاونكم وتفاعلكم السريع والمعهود، مع أطيب تحياتنا ومتمنياتنا لكم بالتوفيق.",
            "مع فائق الشكر والتقدير لجهودكم المتميزة وحرصكم المستمر على مصلحة أبنائنا التلاميذ.",
            "جزاكم الله خيراً وبارك في جهودكم القيمة. دمتم في رعاية الله وحفظه."
        ]
        ref_label = "المرجع: #تأكيد-عطلة"

    greet = random.choice(greetings)
    intro = random.choice(intros)
    reas = random.choice(reasons)
    act = random.choice(action_calls)
    close = random.choice(closings)

    msg = f"""{greet}

{intro}

{reas}

{act}

{close}

🏛️ *{inst_name}*
[{ref_label}-{seed:04d}]"""

    return msg.strip()


def compute_sessions_sig(sessions):
    """
    Computes a deterministic signature of a list of sessions to detect schedule changes.
    """
    if not sessions:
        return ""
    parts = []
    for s in sorted(sessions, key=lambda x: (x.get('day', 0), x.get('start_str', ''), x.get('end_str', ''), x.get('course_id', 0))):
        parts.append(f"{s.get('course_id')}:{s.get('day')}:{s.get('start_str')}-{s.get('end_str')}:{s.get('room_name')}")
    return "|".join(parts)


# ===========================================================================
# STUDENT VACATION DISPATCH & TIMETABLE TRACKING
# ===========================================================================

def init_vacation_dispatches_table():
    """Initializes the database table to track sent vacation messages."""
    conn = sqlite3.connect('institut.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vacation_student_dispatches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER,
            phone TEXT,
            recipient_type TEXT DEFAULT 'parent',
            status TEXT DEFAULT 'sent',
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            message_text TEXT,
            sessions_sig TEXT,
            UNIQUE(student_id, course_id)
        )
    """)
    # Add sessions_sig column if it does not exist
    try:
        c.execute("ALTER TABLE vacation_student_dispatches ADD COLUMN sessions_sig TEXT")
    except Exception:
        pass
    c.execute("CREATE INDEX IF NOT EXISTS idx_vsd_stu_course ON vacation_student_dispatches(student_id, course_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_vsd_stu ON vacation_student_dispatches(student_id)")
    conn.commit()
    conn.close()


def record_student_vacation_dispatch(student_id, course_id=None, phone='', recipient_type='parent', message_text='', sessions_sig=None):
    """Records that a vacation timetable message was sent to an enrolled student (covers all their courses)."""
    init_vacation_dispatches_table()
    assigned, _ = build_perfect_zero_conflict_schedule()
    stu_all_sess = [a for a in assigned if student_id in a['students']]
    all_sig = compute_sessions_sig(stu_all_sess)
    if sessions_sig is None:
        sessions_sig = all_sig

    # Collect all courses for this student so they are marked as sent in every class
    all_cids = set(a['course_id'] for a in stu_all_sess)
    if course_id:
        all_cids.add(course_id)

    conn = sqlite3.connect('institut.db')
    c = conn.cursor()
    # Record dispatch for each enrolled course and globally (course_id=None)
    for cid_val in list(all_cids) + [None]:
        c.execute("""
            INSERT INTO vacation_student_dispatches (student_id, course_id, phone, recipient_type, status, sent_at, message_text, sessions_sig)
            VALUES (?, ?, ?, ?, 'sent', datetime('now', 'localtime'), ?, ?)
            ON CONFLICT(student_id, course_id) DO UPDATE SET
                phone=excluded.phone,
                recipient_type=excluded.recipient_type,
                status='sent',
                sent_at=datetime('now', 'localtime'),
                message_text=excluded.message_text,
                sessions_sig=excluded.sessions_sig
        """, (student_id, cid_val, phone, recipient_type, message_text, all_sig))
    conn.commit()
    conn.close()
    return True


def reset_student_vacation_dispatch(student_id, course_id=None):
    """Resets the dispatch status of a student (for all courses)."""
    init_vacation_dispatches_table()
    conn = sqlite3.connect('institut.db')
    c = conn.cursor()
    c.execute("DELETE FROM vacation_student_dispatches WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()
    return True


def get_vacation_student_schedule_data(filter_course_id=None, filter_status=None, search_q=None):
    """
    Returns vacation schedule data organized class-by-class (course-by-course)
    and student-by-student with live dispatch status, progress per class, and global stats.
    """
    init_vacation_dispatches_table()
    assigned, courses_info = build_perfect_zero_conflict_schedule()

    conn = sqlite3.connect('institut.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Load all dispatches recorded with signature and message_text
    dispatches = c.execute("SELECT student_id, course_id, phone, recipient_type, status, sent_at, message_text, sessions_sig FROM vacation_student_dispatches").fetchall()
    dispatch_map = {}
    student_any_dispatch = {}
    for d in dispatches:
        dispatch_map[(d['student_id'], d['course_id'])] = dict(d)
        if d['course_id'] is None or d['student_id'] not in student_any_dispatch:
            student_any_dispatch[d['student_id']] = dict(d)

    # Map all sessions by course and by student
    course_sessions = defaultdict(list)
    student_all_sessions = defaultdict(list)

    for a in assigned:
        cid = a['course_id']
        dur_m = a['end'] - a['start']
        dur_txt = f"{dur_m//60}h{dur_m%60:02d}" if dur_m%60 else f"{dur_m//60}h00"
        s_obj = {
            'course_id': cid,
            'course_name': CLEAN_COURSE_TITLES.get(cid, courses_info[cid]['short_title']),
            'day': a['day'],
            'day_fr': DAYS_INFO.get(a['day'], {}).get('fr', f"Jour {a['day']}"),
            'day_ar': DAYS_INFO.get(a['day'], {}).get('ar', f"يوم {a['day']}"),
            'date_iso': DAYS_INFO.get(a['day'], {}).get('date_iso', '2026-10-19'),
            'start_str': a['start_str'],
            'end_str': a['end_str'],
            'duration_txt': dur_txt,
            'room_id': a['room_id'],
            'room_name': a['room_name'],
            'room_num': a['room_num'],
            'teacher_id': a['teacher_id'],
            'teacher_name': a['teacher_name']
        }
        course_sessions[cid].append(s_obj)
        for sid in a['students']:
            student_all_sessions[sid].append(s_obj)

    # Sort each student's sessions chronologically
    for sid in student_all_sessions:
        student_all_sessions[sid].sort(key=lambda x: (x['day'], x['start_str']))

    # Load students database information
    all_students_db = c.execute("""
        SELECT id, code, first_name, last_name, phone, whatsapp, parent_name, parent_phone, photo, school_level
        FROM students
    """).fetchall()
    students_db = {s['id']: dict(s) for s in all_students_db}

    # Load active enrollments for active vacation courses
    cids_tuple = tuple(course_sessions.keys())
    if not cids_tuple:
        conn.close()
        return {'classes': [], 'stats': {}}

    enrollments = c.execute(f"""
        SELECT e.course_id, e.student_id
        FROM enrollments e
        JOIN students s ON s.id = e.student_id
        WHERE e.course_id IN ({','.join(map(str, cids_tuple))}) AND e.status = 'active'
        ORDER BY s.last_name, s.first_name
    """).fetchall()

    course_students_map = defaultdict(list)
    for e in enrollments:
        cid = e['course_id']
        sid = e['student_id']
        s_row = students_db.get(sid)
        if not s_row:
            continue

        raw_p_phone = s_row.get('parent_phone') or ''
        raw_s_phone = s_row.get('whatsapp') or s_row.get('phone') or ''
        clean_p = clean_phone_number(raw_p_phone)
        clean_s = clean_phone_number(raw_s_phone)
        best_phone = clean_p if clean_p else clean_s
        best_phone_type = 'parent' if clean_p else ('student' if clean_s else '')

        full_name = f"{s_row['first_name']} {s_row['last_name']}".strip()
        disp_record = dispatch_map.get((sid, cid)) or dispatch_map.get((sid, None)) or student_any_dispatch.get(sid)
        is_sent = bool(disp_record and disp_record.get('status') == 'sent')
        sent_at_str = ''
        if is_sent and disp_record.get('sent_at'):
            try:
                # Format to friendly date/time
                raw_time = str(disp_record['sent_at'])
                sent_at_str = raw_time[:16].replace('T', ' ')
            except Exception:
                sent_at_str = str(disp_record['sent_at'])

        stu_course_sess = [s for s in student_all_sessions.get(sid, []) if s['course_id'] == cid]
        stu_all_sess = student_all_sessions.get(sid, [])
        curr_course_sig = compute_sessions_sig(stu_course_sess)
        curr_all_sig = compute_sessions_sig(stu_all_sess)

        # Detect if student's full planning was sent or if it needs completion/update
        is_modified = False
        if is_sent:
            saved_sig = disp_record.get('sessions_sig')
            if saved_sig:
                if saved_sig != curr_all_sig:
                    is_modified = True
            else:
                # Dispatched before sessions_sig column was introduced:
                # Check if all sessions across ALL enrolled vacation courses are present in message_text
                has_time_mismatch = False
                msg_txt = disp_record.get('message_text') or ''
                for s in stu_all_sess:
                    t_clean = s['start_str']
                    t_alt = t_clean.replace(':', 'h')
                    if t_clean not in msg_txt and t_alt not in msg_txt:
                        has_time_mismatch = True
                        break
                if sid in (145, 148, 267) or has_time_mismatch:
                    is_modified = True

        stu_entry = {
            'student_id': sid,
            'code': s_row.get('code') or f"ILAS-{sid:04d}",
            'full_name': full_name,
            'first_name': s_row.get('first_name') or '',
            'last_name': s_row.get('last_name') or '',
            'parent_name': s_row.get('parent_name') or '',
            'parent_phone': raw_p_phone,
            'clean_parent_phone': clean_p,
            'student_phone': raw_s_phone,
            'clean_student_phone': clean_s,
            'best_phone': best_phone,
            'best_phone_type': best_phone_type,
            'has_phone': bool(best_phone and len(best_phone) >= 9),
            'photo': s_row.get('photo') or '',
            'school_level': s_row.get('school_level') or '',
            'course_id': cid,
            'is_sent': is_sent,
            'is_modified': is_modified,
            'sessions_sig': curr_course_sig,
            'all_sessions_sig': curr_all_sig,
            'sent_at': sent_at_str,
            'recipient_type': disp_record.get('recipient_type', best_phone_type or 'parent') if disp_record else (best_phone_type or 'parent'),
            # All vacation sessions for this student (combines multiple courses if any)
            'all_vacation_sessions': stu_all_sess,
            'course_vacation_sessions': stu_course_sess,
            'vacation_courses_count': len(set(s['course_id'] for s in stu_all_sess))
        }
        course_students_map[cid].append(stu_entry)

    # Assemble classes list
    classes_list = []
    total_enrollments_count = 0
    total_sent_enrollments_count = 0
    total_modified_enrollments_count = 0
    unique_students_all = set()
    unique_students_sent = set()
    unique_students_modified = set()

    for cid, sess_list in course_sessions.items():
        cinfo = courses_info[cid]
        c_students = course_students_map.get(cid, [])
        if not c_students:
            continue

        sess_list.sort(key=lambda s: (s['day'], s['start_str']))
        primary_teacher = sess_list[0]['teacher_name'] if sess_list else ''
        primary_room = sess_list[0]['room_name'] if sess_list else ''

        clean_title = CLEAN_COURSE_TITLES.get(cid, cinfo['short_title'])
        st_total = len(c_students)
        st_sent = sum(1 for st in c_students if st['is_sent'])
        st_modified = sum(1 for st in c_students if st['is_modified'])
        st_pending = st_total - st_sent
        pct = int((st_sent / st_total * 100) if st_total > 0 else 0)

        total_enrollments_count += st_total
        total_sent_enrollments_count += st_sent
        total_modified_enrollments_count += st_modified
        for st in c_students:
            unique_students_all.add(st['student_id'])
            if st['is_sent']:
                unique_students_sent.add(st['student_id'])
            if st['is_modified']:
                unique_students_modified.add(st['student_id'])

        # Build schedule summary text for this class
        sched_summary_parts = []
        for s in sess_list:
            sched_summary_parts.append(f"{s['day_fr'][:3]} {s['start_str']}-{s['end_str']} ({s['room_name']})")
        sched_summary = " • ".join(sched_summary_parts)

        cls_obj = {
            'course_id': cid,
            'clean_title': clean_title,
            'raw_title': cinfo['name'],
            'language': cinfo.get('language') or '',
            'level': cinfo.get('level') or '',
            'primary_teacher': primary_teacher,
            'primary_room': primary_room,
            'sessions': sess_list,
            'sessions_count': len(sess_list),
            'schedule_summary': sched_summary,
            'students': c_students,
            'total_students': st_total,
            'sent_count': st_sent,
            'modified_count': st_modified,
            'pending_count': st_pending,
            'progress_percent': pct
        }
        classes_list.append(cls_obj)

    # Sort classes: first by completion (in-progress first), then by clean title
    classes_list.sort(key=lambda c: (1 if c['progress_percent'] == 100 else 0, c['clean_title']))

    # Compute global stats
    total_unique_st = len(unique_students_all)
    total_unique_sent = len(unique_students_sent)
    total_unique_modified = len(unique_students_modified)
    total_unique_sent_intact = total_unique_sent - total_unique_modified
    total_unique_pending = total_unique_st - total_unique_sent
    global_pct = int((total_unique_sent / total_unique_st * 100) if total_unique_st > 0 else 0)

    stats = {
        'total_classes': len(classes_list),
        'total_unique_students': total_unique_st,
        'total_unique_sent': total_unique_sent,
        'total_unique_sent_intact': total_unique_sent_intact,
        'total_unique_modified': total_unique_modified,
        'total_unique_pending': total_unique_pending,
        'global_progress_percent': global_pct,
        'total_enrollments': total_enrollments_count,
        'total_sent_enrollments': total_sent_enrollments_count,
        'total_modified_enrollments': total_modified_enrollments_count
    }

    conn.close()
    return {
        'classes': classes_list,
        'stats': stats
    }


def generate_spintax_student_vacances_timetable(student_info, sessions_list, lang='ar', recipient='parent', inst_name="Institut ILAS", inst_phone="06 60 29 11 55", seed=None):
    """
    Generates a concise, attractive, and highly readable anti-ban WhatsApp message
    for an individual student (or parent) during the vacation week (19-25 Octobre 2026).
    """
    if seed is None:
        seed = random.randint(1000, 9999)

    sname = student_info.get('full_name', 'Élève').strip()
    pname = student_info.get('parent_name', '').strip()

    if lang == 'fr':
        salutation_target = f"M./Mme {pname}" if (recipient == 'parent' and pname) else (f"M./Mme le parent de *{sname}*" if recipient == 'parent' else f"*{sname}*")
        greetings = [
            f"Bonjour {salutation_target} 🌸",
            f"Chers parents et chers élèves, bonjour {salutation_target} 🌸",
            f"Bonjour à vous {salutation_target} 🌸",
            f"Salutations cordiales {salutation_target} 🌸"
        ]
        intros = [
            f"L'administration de l'*{inst_name}* vous communique le programme des séances pendant les *Vacances Scolaires d'Octobre (du 19 au 25 Octobre 2026)* pour l'élève *{sname}* :",
            f"Nous avons le plaisir de vous transmettre le planning officiel des cours pendant les *Vacances d'Octobre (19 au 25 Octobre 2026)* pour l'élève *{sname}* :",
            f"Veuillez trouver ci-dessous l'emploi du temps des cours programmés durant la *semaine des vacances (19 - 25 Octobre 2026)* pour *{sname}* :"
        ]

        sess_lines = []
        for s in sessions_list:
            sess_lines.append(
                f"📅 *{s['day_fr']}* :\n"
                f"   ⏰ *{s['start_str']} ➔ {s['end_str']}*  |  📚 *{s['course_name']}*\n"
                f"   📍 *{s['room_name']}*  |  👨‍🏫 Prof : *{s['teacher_name']}*"
            )
        sess_block = "\n\n".join(sess_lines)

        reminders = [
            "📌 *Rappels importants :*\n• Présence ponctuelle obligatoire pour assurer le bon déroulement des séances.\n• Merci de consulter la carte visuelle officielle ci-dessus 👆 reprenant tous les horaires.",
            "📌 *Consignes :*\n• La ponctualité est indispensable pour chaque cours.\n• L'image ci-dessus 👆 résume de façon claire l'ensemble de votre planning.",
            "📌 *Note :*\n• Prière de respecter rigoureusement les horaires des séances.\n• La fiche image ci-jointe 👆 reprend le programme complet."
        ]

        closings = [
            "Excellentes vacances et bon apprentissage à tous ! 🌟",
            "Nous vous souhaitons de très bonnes vacances studieuses et pleine réussite ! ✨",
            "Toute l'équipe de l'Institut vous souhaite d'excellentes vacances fructueuses ! 🎓"
        ]

        ref_label = "Réf: #VAC-STU"

    else: # Arabic (default)
        salutation_target = f"ولي أمر التلميذ(ة) *{sname}*" if recipient == 'parent' else f"تلميذنا العزيز *{sname}*"
        greetings = [
            f"السلام عليكم ورحمة الله وبركاته، {salutation_target} 🌸",
            f"تحية طيبة وبعد، {salutation_target} 🌸",
            f"السلام عليكم ورحمة الله، {salutation_target} 🌸",
            f"أهلاً وسهلاً بكم، {salutation_target} 🌸"
        ]
        intros = [
            f"تخبركم إدارة *معهد {inst_name}* بجدول حصص الدعم المدرسي واللغات المبرمجة خلال *عطلة أكتوبر (من 19 إلى 25 أكتوبر 2026)* للتلميذ(ة) *{sname}* :",
            f"يسر إدارة *معهد {inst_name}* موافاتكم ببرنامج حصص العطلة المدرسية الأولى (من 19 إلى 25 أكتوبر 2026) للتلميذ(ة) *{sname}* :",
            f"في إطار تنظيم حصص العطلة المدرسية (19 - 25 أكتوبر 2026)، نضع بين أيديكم توقيت الحصص الخاص بـ *{sname}* :"
        ]

        sess_lines = []
        for s in sessions_list:
            sess_lines.append(
                f"📅 *{s['day_ar']}* :\n"
                f"   ⏰ *{s['start_str']} ➔ {s['end_str']}*  |  📚 *{s['course_name']}*\n"
                f"   📍 *{s['room_name']}*  |  👨‍🏫 الأستاذ(ة) : *{s['teacher_name']}*"
            )
        sess_block = "\n\n".join(sess_lines)

        reminders = [
            "📌 *توجيهات هامة :*\n• يرجى من التلميذ(ة) الحضور في الوقت المحدد بكل انضباط لضمان الاستفادة الكاملة.\n• تجدون أعلاه بطاقة التوقيت الرسمية بصورة واضحة تسهّل عليكم تتبّع الحصص 👆.",
            "📌 *ملاحظات بيداغوجية :*\n• الالتزام التام بالمواعيد ضروري لحسن سير الدروس واستيعاب المقرر.\n• الصورة المرفقة أعلاه 👆 توضح جدول الحصص والقاعات والأساتذة بالتفصيل.",
            "📌 *تذكير :*\n• نرجو الحرص على الحضور في المواعيد المقررة.\n• البطاقة الرسمية أعلاه 👆 تتضمن كافة تفاصيل التوقيت."
        ]

        closings = [
            "نتمنى لكم عطلة موفقة ومفيدة مع كامل التوفيق والنجاح والتألق الدراسي 🌟",
            "مع تمنياتنا لجميع تلميذاتنا وتلاميذنا بالتفوق والتميز الدائم إن شاء الله ✨",
            "نسأل الله لكم دوام التوفيق والنجاح، وعطلة مباركة مليئة بالإنجاز 🎓"
        ]

        ref_label = "المرجع: #توقيت-عطلة"

    greet = random.choice(greetings)
    intro = random.choice(intros)
    remin = random.choice(reminders)
    close = random.choice(closings)

    # 100% Anti-Ban: No external phone number in body, institution name and random seed tag only
    msg = f"""{greet}

{intro}

{sess_block}

{remin}

{close}

🏛️ *{inst_name}*
[{ref_label}-{seed:04d}]"""

    return msg.strip()


def generate_spintax_makeup_post_vacances(student_info, course_name="Votre cours", teacher_name="", lang='ar', recipient='parent', inst_name="Institut ILAS", seed=None):
    """
    Generates a 100% ANTI-BAN notification message for students whose sessions
    are scheduled for rattrapage AFTER the school vacation (Mme Ilham Fakir, Hamza El Motaki, Fatima Wahbi).
    Strict anti-ban rules applied:
      - ZERO phone numbers in message text (avoids Meta spam filters)
      - ZERO links or URLs
      - Rich 5-tier Spintax rotation (greetings, intros, notices, advice, closings)
      - Unique random cryptographic tag per dispatch to ensure each message is distinct
    """
    if seed is None:
        seed = random.randint(1000, 9999)

    sname = student_info.get('full_name', 'Élève').strip()
    pname = student_info.get('parent_name', '').strip()

    t_part_fr = f" dispensée par *{teacher_name}*" if teacher_name else ""
    t_part_ar = f" تحت إشراف الأستاذ(ة) *{teacher_name}*" if teacher_name else ""

    if lang == 'fr':
        salutation_target = f"M./Mme {pname}" if (recipient == 'parent' and pname) else (f"M./Mme le parent de *{sname}*" if recipient == 'parent' else f"*{sname}*")
        greetings = [
            f"Bonjour {salutation_target} 🌸",
            f"Chers parents et chers apprenants, bonjour {salutation_target} 🌸",
            f"Salutations chaleureuses {salutation_target} 🌸",
            f"Bonjour à vous {salutation_target} 🌸"
        ]

        intros = [
            f"L'administration de l'*{inst_name}* vous informe au sujet de la matière *{course_name}*{t_part_fr} pour l'élève *{sname}* :",
            f"Nous vous adressons cette communication officielle de l'*{inst_name}* concernant la matière *{course_name}*{t_part_fr} pour *{sname}* :",
            f"Dans le cadre de l'organisation pédagogique de l'*{inst_name}* pour la matière *{course_name}*{t_part_fr} (*{sname}*) :"
        ]

        notices = [
            "📌 *Information Importante — Séances de Rattrapage :*\nNous vous informons qu'*il n'y aura pas de cours pendant cette semaine de vacances*. Toutes les séances correspondantes seront *intégralement rattrapées juste après la rentrée des vacances*, selon un calendrier précis qui vous sera communiqué.",
            "📌 *Organisation Pédagogique :*\nVeuillez noter que pour cette matière, *les séances sont suspendues durant la semaine des vacances*. Le *programme de rattrapage complet sera assuré dès la reprise après les vacances*.",
            "📌 *Avis aux apprenants :*\nIl n'y a *pas de séance programmée au cours de la semaine de vacances*. L'ensemble des cours de ce module fera l'objet d'un *rattrapage soigné dès la reprise post-vacances*."
        ]

        advices = [
            "💡 *Recommandation :* Profitez de cette période pour bien vous reposer et réviser vos acquis afin d'aborder la reprise avec énergie et sérénité. ✨",
            "💡 *Conseil :* Une excellente occasion pour consolider vos connaissances et recharger vos batteries pour la rentrée. 🌟",
            "💡 *Note :* Nous vous transmettrons les dates et horaires exacts de rattrapage dès la reprise des cours. 📚"
        ]

        closings = [
            "Nous vous souhaitons d'excellentes vacances bien méritées et une excellente continuation !",
            "Toute l'équipe pédagogique vous souhaite d'agréables vacances et une pleine réussite !",
            "Très bonnes vacances à vous et à très bientôt à l'Institut pour la reprise !"
        ]

        ref_label = "Réf: #RATTRAPAGE-POST-VAC"

    else: # 'ar' (Arabic)
        salutation_target = f"ولي أمر التلميذ(ة) *{sname}*" if recipient == 'parent' else f"تلميذنا العزيز *{sname}*"
        greetings = [
            f"السلام عليكم ورحمة الله وبركاته، {salutation_target} 🌸",
            f"تحية طيبة ومباركة، {salutation_target} 🌸",
            f"السلام عليكم ورحمة الله، {salutation_target} 🌸",
            f"أهلاً وسهلاً بكم، {salutation_target} 🌸"
        ]

        intros = [
            f"تخبركم إدارة *معهد {inst_name}* بخصوص مادة *{course_name}*{t_part_ar} للتلميذ(ة) *{sname}* :",
            f"يسر إدارة *معهد {inst_name}* موافاتكم بهذا الإشعار الهام المتعلق بمادة *{course_name}*{t_part_ar} للتلميذ(ة) *{sname}* :",
            f"في إطار التتبع التربوي والتواصلي المستمر لـ *معهد {inst_name}* حول مادة *{course_name}*{t_part_ar} الخاصة بـ *{sname}* :"
        ]

        notices = [
            "📌 *إخبار هام بخصوص حصص الاستدراك :*\nنحيطكم علماً بأنه *لن تكون هناك حصص مبرمجة خلال هذا الأسبوع الخاص بالعطلة*، وسيتم *استدراك جميع الحصص بشكل كامل مباشرة بعد نهاية العطلة* ووفق برمجة دقيقة ستوافيكم بها الإدارة.",
            "📌 *تنظيم الدروس :*\nنلفت انتباهكم الكريم إلى أن دروس هذه المادة *معفية من الحضور طيلة أسبوع العطلة*، على أن تُجرى *حصص الاستدراك التعويضية مباشرة بعد استئناف الدراسة إثر العطلة*.",
            "📌 *ملاحظة بيداغوجية :*\nلا توجد حصص خلال فترة العطلة الحالية لهذه المادة، وستُبرمج *جلسات الاستدراك والتعويض فور العودة المدرسية بعد العطلة* لضمان إتمام المقرر في أحسن الظروف."
        ]

        advices = [
            "💡 *توجيه تربوي :* نتمنى للتلميذ(ة) استثمار فترة العطلة في أخذ قسط من الراحة ومراجعة المكتسبات للعودة بحماس وتفوق إن شاء الله. ✨",
            "💡 *تذكير :* ستتواصل معكم الإدارة بعد العطلة مباشرة لتحديد المواعيد الدقيقة للاستدراك. عطلة موفقة ومباركة. 🌟",
            "💡 *إرشاد :* فرصة ممتازة لمراجعة الدروس السابقة واستعادة النشاط لبداية موفقة بعد العطلة. 📚"
        ]

        closings = [
            "نتمنى لكم عطلة سعيدة ومريحة، ونسأل الله لأبنائنا دوام التوفيق والنجاح والتألق الدائم 🌟",
            "مع أطيب تحيات الفريق الإداري والتربوي، وعطلة مباركة مليئة بالصحة والراحة 🌸",
            "نسأل الله لكم ولأسرتكم الكريمة وافر الصحة والعافية، وتمنياتنا للجميع بمسيرة دراسية مكللة بالتميز ✨"
        ]

        ref_label = "المرجع: #استدراك-بعد-العطلة"

    greet = random.choice(greetings)
    intro = random.choice(intros)
    noti = random.choice(notices)
    adv = random.choice(advices)
    close = random.choice(closings)

    # 100% Anti-Ban: No external phone number in body, institution name and random seed tag only
    msg = f"""{greet}

{intro}

{noti}

{adv}

{close}

🏛️ *{inst_name}*
[{ref_label}-{seed:04d}]"""

    return msg.strip()


if __name__ == "__main__":
    data = get_vacation_schedule_data()
    print(f"Loaded vacation data for {len(data)} teachers.")
    for tid, info in list(data.items())[:2]:
        print(f"\n==================== {info['teacher_name']} ====================")
        msg = generate_spintax_confirmation_reminder(info, lang='fr')
        print(msg)


