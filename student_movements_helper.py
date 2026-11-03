# -*- coding: utf-8 -*-
"""
Helper module for Student Movements (Mouvements des Élèves / حركة التلاميذ)
Tracks entries (Dkhul), exits (Quitta), renewals, and net variation globally and per subject (matière).
"""

import re
import calendar
import io
from datetime import date, datetime, timedelta
from collections import defaultdict
from models import db, Student, Enrollment, Course, Tariff, MATIERE_CONFIG, get_course_matiere

MONTHS_FR = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}

MONTHS_AR = {
    1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
    5: 'مايو', 6: 'يونيو', 7: 'يوليوز', 8: 'غشت',
    9: 'شتنبر', 10: 'أكتوبر', 11: 'نونبر', 12: 'دجنبر'
}


def get_student_avatar_url(stu):
    if not stu:
        return ""
    if getattr(stu, 'photo', None):
        return f"/static/uploads/{stu.photo}"
    fn = getattr(stu, 'first_name', '') or ''
    ln = getattr(stu, 'last_name', '') or ''
    return f"https://ui-avatars.com/api/?name={fn}+{ln}&background=0B3D6E&color=fff&size=64"


def normalize_matiere_name(m_str):

    if not m_str:
        return 'Autre'
    m_clean = str(m_str).strip()
    low = m_clean.lower()
    if any(k in low for k in ['soutien', 'primaire', '2 bac', '1 bac', 'tronc commun', 'collège', 'college', 'lycée', 'lycee']):
        return 'Soutien Scolaire'
    if 'fran' in low:
        return 'Français'
    if 'angl' in low or 'eng' in low:
        return 'Anglais'
    if 'math' in low:
        return 'Mathématiques'
    if 'phys' in low or 'chim' in low or 'pc' in low:
        return 'Physique-Chimie'
    if 'svt' in low:
        return 'SVT'
    if 'allem' in low or 'germ' in low or 'deutsch' in low:
        return 'Allemand'
    if 'espagn' in low or 'span' in low:
        return 'Espagnol'
    if 'arab' in low:
        return 'Arabe'
    for k in MATIERE_CONFIG:
        if k.lower() in low or low in k.lower():
            return k
    return 'Autre'


def get_enrollment_matiere(e):
    if not e:
        return 'Autre'
    if e.course:
        return normalize_matiere_name(e.course.matiere)
    if e.tariff:
        t_mat = get_course_matiere(e.tariff.language or e.tariff.name)
        return normalize_matiere_name(t_mat)
    if e.notes:
        for k in ['Français', 'Anglais', 'Mathématiques', 'Physique-Chimie', 'SVT', 'Allemand', 'Espagnol', 'Arabe']:
            if k.lower() in e.notes.lower():
                return k
    return 'Autre'


def parse_drop_date_and_reason(enrollment):
    """
    Extracts the precise exit date and specific reason from notes, custom_end_date, or creation date.
    """
    drop_dt = None
    reason_fr = "Désistement / Retrait"
    reason_ar = "انسحاب / إلغاء"
    exit_type = "dropped"
    
    notes = enrollment.notes or ""
    notes_low = notes.lower()

    if "séance d'essai annulée" in notes_low or "essai annulé" in notes_low:
        reason_fr = "Séance d'essai non poursuivie"
        reason_ar = "حصة تجريبية غير مؤكدة"
        exit_type = "trial_cancelled"
    elif "retiré manuellement" in notes_low or "retrait de" in notes_low:
        reason_fr = "Retiré de la classe"
        reason_ar = "حذف يدوي من القسم"
        exit_type = "manual_removal"
    elif "transféré" in notes_low or "transfert" in notes_low:
        reason_fr = "Transféré vers une autre classe"
        reason_ar = "تحويل إلى فوج آخر"
        exit_type = "transfer"
    elif "désistement" in notes_low:
        reason_fr = "Désistement d'inscription"
        reason_ar = "انسحاب واسترداد / رصيد"
        exit_type = "withdrawal"
    elif "auto-suppression" in notes_low or "3ème rappel" in notes_low:
        reason_fr = "Délai expiré (3 rappels WhatsApp sans suite)"
        reason_ar = "حذف تلقائي بعد 3 تذكيرات"
        exit_type = "auto_purged"

    # Search for French date DD/MM/YYYY
    m = re.search(r'(?:le|le\s+)(\d{2}/\d{2}/\d{4})', notes)
    if m:
        try:
            drop_dt = datetime.strptime(m.group(1), '%d/%m/%Y').date()
        except Exception:
            pass

    # Search for ISO date YYYY-MM-DD
    if not drop_dt:
        m_iso = re.search(r'(\d{4}-\d{2}-\d{2})', notes)
        if m_iso:
            try:
                drop_dt = datetime.strptime(m_iso.group(1), '%Y-%m-%d').date()
            except Exception:
                pass

    if not drop_dt and enrollment.custom_end_date:
        drop_dt = enrollment.custom_end_date

    if not drop_dt and enrollment.created_at:
        drop_dt = enrollment.created_at.date()

    return drop_dt, reason_fr, reason_ar, exit_type


def get_student_movements_data(year=None, month=None, selected_matiere=None, search_q=None, entry_type_filter=None, exit_type_filter=None):
    today = date.today()
    if not year or not month:
        year = today.year
        month = today.month

    year = int(year)
    month = int(month)

    # Date bounds
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    # Navigation dates
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    period_label_fr = f"{MONTHS_FR.get(month, '')} {year}"
    period_label_ar = f"{MONTHS_AR.get(month, '')} {year}"

    # Fetch all enrollments
    all_enrollments = Enrollment.query.order_by(Enrollment.id.asc()).all()

    # Pre-organize enrollments by student
    student_all_ens = defaultdict(list)
    for e in all_enrollments:
        if e.student_id:
            student_all_ens[e.student_id].append(e)

    for sid in student_all_ens:
        student_all_ens[sid].sort(key=lambda x: (x.enroll_date or date(2000, 1, 1), x.id))

    # 1. ENTRÉES (DKHUL)
    raw_entries = []
    for e in all_enrollments:
        entry_dt = e.enroll_date or (e.created_at.date() if e.created_at else None)
        if not entry_dt or not (start_date <= entry_dt <= end_date):
            continue

        mat = get_enrollment_matiere(e)
        stu = e.student
        stu_ens = student_all_ens.get(e.student_id, [])

        # Check if first student appearance ever
        is_first_stu = False
        if stu_ens:
            earliest_dt = stu_ens[0].enroll_date or (stu_ens[0].created_at.date() if stu_ens[0].created_at else None)
            if stu_ens[0].id == e.id or (earliest_dt and earliest_dt >= start_date):
                is_first_stu = True

        # Check if renewed in this matiere
        earlier_same_mat = [
            x for x in stu_ens
            if get_enrollment_matiere(x) == mat and x.id < e.id and (x.enroll_date or date(2000, 1, 1)) < entry_dt
        ]
        is_renewal = len(earlier_same_mat) > 0

        if is_first_stu:
            etype = 'new_student'
            etype_label_fr = "Nouveau à l'Institut"
            etype_label_ar = "تلميذ جديد بالمعهد"
            etype_badge = "chip-green"
        elif is_renewal:
            etype = 'renewal'
            etype_label_fr = "Renouvellement"
            etype_label_ar = "تجديد اشتراك"
            etype_badge = "chip-blue"
        else:
            etype = 'new_matiere'
            etype_label_fr = "Nouvelle Matière"
            etype_label_ar = "مادة جديدة (تلميذ حالي)"
            etype_badge = "chip-purple"

        raw_entries.append({
            'enrollment_id': e.id,
            'student_id': e.student_id,
            'student_name': stu.full_name if stu else f"Élève #{e.student_id}",
            'student_code': stu.code if stu else '',
            'student_phone': stu.phone or (stu.parent_phone if stu else ''),
            'student_whatsapp': stu.whatsapp or stu.phone or (stu.parent_phone if stu else ''),
            'student_avatar': get_student_avatar_url(stu),
            'student_level': stu.school_level if stu else '',
            'matiere': mat,
            'course_id': e.course_id,
            'course_name': e.course.receipt_name if (e.course and hasattr(e.course, 'receipt_name')) else (e.course.display_name if e.course else (e.tariff.name if e.tariff else 'Classe en attente')),
            'entry_date': entry_dt,
            'entry_type': etype,
            'entry_type_label_fr': etype_label_fr,
            'entry_type_label_ar': etype_label_ar,
            'entry_type_badge': etype_badge,
            'paid_amount': float(e.total_paid or 0.0),
            'due_amount': float(e.due_amount or 0.0),
            'balance': float(e.balance or 0.0),
            'status': e.status,
            'notes': e.notes or ''
        })

    # 2. SORTIES (QUITTA)
    raw_exits = []

    # A. Dropped enrollments
    dropped_enrolls = Enrollment.query.filter_by(status='dropped').all()
    for e in dropped_enrolls:
        drop_dt, r_fr, r_ar, etype = parse_drop_date_and_reason(e)
        if drop_dt and (start_date <= drop_dt <= end_date):
            mat = get_enrollment_matiere(e)
            stu = e.student
            raw_exits.append({
                'enrollment_id': e.id,
                'student_id': e.student_id,
                'student_name': stu.full_name if stu else f"Élève #{e.student_id}",
                'student_code': stu.code if stu else '',
                'student_phone': stu.phone or (stu.parent_phone if stu else ''),
                'student_whatsapp': stu.whatsapp or stu.phone or (stu.parent_phone if stu else ''),
                'student_avatar': get_student_avatar_url(stu),
                'student_level': stu.school_level if stu else '',
                'matiere': mat,
                'course_id': e.course_id,
                'course_name': e.course.receipt_name if (e.course and hasattr(e.course, 'receipt_name')) else (e.course.display_name if e.course else 'Classe'),
                'exit_date': drop_dt,
                'exit_type': etype,
                'reason_fr': r_fr,
                'reason_ar': r_ar,
                'notes': e.notes or '',
                'paid_amount': float(e.total_paid or 0.0)
            })

    # B. Completed or Expired in this month without renewal
    student_matiere_enrolls = defaultdict(lambda: defaultdict(list))
    for e in all_enrollments:
        if not e.student_id or e.status == 'dropped':
            continue
        student_matiere_enrolls[e.student_id][get_enrollment_matiere(e)].append(e)

    for sid, mat_dict in student_matiere_enrolls.items():
        for mat, ens in mat_dict.items():
            ens.sort(key=lambda x: (x.enroll_date or date(2000, 1, 1), x.id))
            last_e = ens[-1]
            ed = last_e.end_date
            if ed and (start_date <= ed <= end_date):
                # If completed OR (active and end_date has passed)
                if last_e.status == 'completed' or (last_e.status == 'active' and ed < today):
                    # Check if student renewed in this matiere with another enrollment
                    has_other_active = any(
                        x.status == 'active' and (x.end_date is None or x.end_date >= today)
                        for x in ens if x.id != last_e.id
                    )
                    if not has_other_active:
                        stu = last_e.student
                        raw_exits.append({
                            'enrollment_id': last_e.id,
                            'student_id': last_e.student_id,
                            'student_name': stu.full_name if stu else f"Élève #{last_e.student_id}",
                            'student_code': stu.code if stu else '',
                            'student_phone': stu.phone or (stu.parent_phone if stu else ''),
                            'student_whatsapp': stu.whatsapp or stu.phone or (stu.parent_phone if stu else ''),
                            'student_avatar': get_student_avatar_url(stu),
                            'student_level': stu.school_level if stu else '',
                            'matiere': mat,
                            'course_id': last_e.course_id,
                            'course_name': last_e.course.receipt_name if (last_e.course and hasattr(last_e.course, 'receipt_name')) else (last_e.course.display_name if last_e.course else 'Classe'),
                            'exit_date': ed,
                            'exit_type': 'non_renewed',
                            'reason_fr': "Abonnement expiré sans renouvellement",
                            'reason_ar': "نهاية اشتراك دون تجديد",
                            'notes': last_e.notes or '',
                            'paid_amount': float(last_e.total_paid or 0.0)
                        })

    # Sort lists chronologically
    raw_entries.sort(key=lambda x: (x['entry_date'], x['enrollment_id']), reverse=True)
    raw_exits.sort(key=lambda x: (x['exit_date'], x['enrollment_id']), reverse=True)

    # Calculate active students currently per matiere
    active_enrolls = Enrollment.query.filter(Enrollment.status.in_(['active', 'trial'])).all()
    active_by_mat = defaultdict(int)
    for ae in active_enrolls:
        active_by_mat[get_enrollment_matiere(ae)] += 1

    # Aggregate by Matière
    mat_summary = {}
    known_matieres = [
        'Français', 'Anglais', 'Mathématiques', 'Physique-Chimie',
        'Allemand', 'Espagnol', 'SVT', 'Soutien Scolaire', 'Arabe', 'Autre'
    ]

    all_seen_matieres = set(known_matieres)
    for x in raw_entries:
        all_seen_matieres.add(x['matiere'])
    for x in raw_exits:
        all_seen_matieres.add(x['matiere'])

    for m in all_seen_matieres:
        cfg = MATIERE_CONFIG.get(m, {
            'icon': '📚',
            'color': '#0284c7',
            'bg': '#f0f9ff',
            'border': '#bae6fd',
            'priority': 90,
            'name_ar': m
        })

        m_entries = [x for x in raw_entries if x['matiere'] == m]
        m_exits = [x for x in raw_exits if x['matiere'] == m]

        # Ignore if zero movements and zero active students (unless it's a main core subject)
        act_cnt = active_by_mat.get(m, 0)
        if len(m_entries) == 0 and len(m_exits) == 0 and act_cnt == 0 and m not in ['Français', 'Anglais', 'Mathématiques', 'Physique-Chimie']:
            continue

        net = len(m_entries) - len(m_exits)

        mat_summary[m] = {
            'name': m,
            'name_ar': cfg.get('name_ar', m),
            'icon': cfg.get('icon', '📚'),
            'color': cfg.get('color', '#0284c7'),
            'bg': cfg.get('bg', '#f0f9ff'),
            'border': cfg.get('border', '#bae6fd'),
            'priority': cfg.get('priority', 90),
            'entries_count': len(m_entries),
            'entries_new_stu': sum(1 for x in m_entries if x['entry_type'] == 'new_student'),
            'entries_renewal': sum(1 for x in m_entries if x['entry_type'] == 'renewal'),
            'entries_new_mat': sum(1 for x in m_entries if x['entry_type'] == 'new_matiere'),
            'exits_count': len(m_exits),
            'exits_dropped': sum(1 for x in m_exits if x['exit_type'] != 'non_renewed'),
            'exits_non_renewed': sum(1 for x in m_exits if x['exit_type'] == 'non_renewed'),
            'net_variation': net,
            'active_now': act_cnt,
            'entries': m_entries,
            'exits': m_exits
        }

    # Sort mat_summary by priority
    sorted_matieres = sorted(mat_summary.values(), key=lambda x: (x['priority'], -x['entries_count']))

    # Filtered lists for table views if query or matiere selected
    filtered_entries = raw_entries
    filtered_exits = raw_exits

    if selected_matiere and selected_matiere != 'all':
        filtered_entries = [x for x in filtered_entries if x['matiere'] == selected_matiere]
        filtered_exits = [x for x in filtered_exits if x['matiere'] == selected_matiere]

    if entry_type_filter and entry_type_filter != 'all':
        filtered_entries = [x for x in filtered_entries if x['entry_type'] == entry_type_filter]

    if exit_type_filter and exit_type_filter != 'all':
        if exit_type_filter == 'non_renewed':
            filtered_exits = [x for x in filtered_exits if x['exit_type'] == 'non_renewed']
        elif exit_type_filter == 'dropped':
            filtered_exits = [x for x in filtered_exits if x['exit_type'] != 'non_renewed']
        else:
            filtered_exits = [x for x in filtered_exits if x['exit_type'] == exit_type_filter]

    if search_q:
        q_low = search_q.strip().lower()
        filtered_entries = [
            x for x in filtered_entries
            if q_low in x['student_name'].lower() or q_low in (x['student_code'] or '').lower() or q_low in (x['student_phone'] or '') or q_low in (x['course_name'] or '').lower()
        ]
        filtered_exits = [
            x for x in filtered_exits
            if q_low in x['student_name'].lower() or q_low in (x['student_code'] or '').lower() or q_low in (x['student_phone'] or '') or q_low in (x['course_name'] or '').lower()
        ]

    # Global totals
    total_entries = len(raw_entries)
    total_exits = len(raw_exits)
    total_net = total_entries - total_exits

    total_new_students = sum(1 for x in raw_entries if x['entry_type'] == 'new_student')
    total_renewals = sum(1 for x in raw_entries if x['entry_type'] == 'renewal')
    total_new_matieres = sum(1 for x in raw_entries if x['entry_type'] == 'new_matiere')

    total_dropped = sum(1 for x in raw_exits if x['exit_type'] != 'non_renewed')
    total_non_renewed = sum(1 for x in raw_exits if x['exit_type'] == 'non_renewed')

    # Total active enrolled students in the institute right now
    total_active_students = Student.query.filter_by(status='active').count()

    # Retention rate (% renewed vs non_renewed)
    if (total_renewals + total_non_renewed) > 0:
        retention_rate = round((total_renewals / (total_renewals + total_non_renewed)) * 100, 1)
    else:
        retention_rate = 100.0 if total_entries > 0 else 0.0

    return {
        'year': year,
        'month': month,
        'month_str': f"{year}-{month:02d}",
        'period_label_fr': period_label_fr,
        'period_label_ar': period_label_ar,
        'start_date': start_date,
        'end_date': end_date,
        'prev_month_str': f"{prev_year}-{prev_month:02d}",
        'next_month_str': f"{next_year}-{next_month:02d}",
        'is_current_month': (year == today.year and month == today.month),
        'today': today,

        # Global KPIs
        'total_entries': total_entries,
        'total_exits': total_exits,
        'total_net': total_net,
        'total_new_students': total_new_students,
        'total_renewals': total_renewals,
        'total_new_matieres': total_new_matieres,
        'total_dropped': total_dropped,
        'total_non_renewed': total_non_renewed,
        'total_active_students': total_active_students,
        'retention_rate': retention_rate,

        # Matières breakdown
        'matieres_summary': sorted_matieres,
        'active_by_mat': dict(active_by_mat),

        # Detail lists
        'entries': filtered_entries,
        'exits': filtered_exits,
        'all_entries_count': len(raw_entries),
        'all_exits_count': len(raw_exits),

        # Filters
        'selected_matiere': selected_matiere or 'all',
        'search_q': search_q or '',
        'entry_type_filter': entry_type_filter or 'all',
        'exit_type_filter': exit_type_filter or 'all'
    }


def generate_movements_excel(data):
    """
    Build an elegant multi-sheet Excel file with openpyxl.
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()

    # Style definitions
    header_fill = PatternFill(start_color="0B3D6E", end_color="0B3D6E", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Segoe UI", size=15, bold=True, color="0B3D6E")
    subtitle_font = Font(name="Segoe UI", size=10, italic=True, color="475569")
    bold_font = Font(name="Segoe UI", size=10, bold=True)
    regular_font = Font(name="Segoe UI", size=10)
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    total_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    # ==========================================
    # SHEET 1: SYNTHÈSE PAR MATIÈRE
    # ==========================================
    ws1 = wb.active
    ws1.title = "Synthèse par Matière"

    # Title
    ws1.merge_cells("A1:G1")
    ws1["A1"] = f"INSTITUT ILAS — RAPPORT DES MOUVEMENTS D'ÉLÈVES ({data['period_label_fr'].upper()})"
    ws1["A1"].font = title_font
    ws1["A1"].alignment = left_align

    ws1.merge_cells("A2:G2")
    ws1["A2"] = f"Généré le {date.today().strftime('%d/%m/%Y')} | Période du {data['start_date'].strftime('%d/%m/%Y')} au {data['end_date'].strftime('%d/%m/%Y')}"
    ws1["A2"].font = subtitle_font
    ws1["A2"].alignment = left_align

    # Overall KPIs Row
    ws1["A4"] = "Total Entrées"
    ws1["B4"] = data['total_entries']
    ws1["C4"] = "Total Sorties"
    ws1["D4"] = data['total_exits']
    ws1["E4"] = "Bilan Net"
    ws1["F4"] = data['total_net']
    ws1["G4"] = f"Rétention: {data['retention_rate']}%"
    for col in ["A", "B", "C", "D", "E", "F", "G"]:
        ws1[f"{col}4"].font = bold_font
        ws1[f"{col}4"].fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        ws1[f"{col}4"].border = thin_border
        ws1[f"{col}4"].alignment = center_align

    # Table Headers
    headers1 = [
        "Matière / Discipline",
        "Entrées (Dkhul)",
        "Dont Nouveaux",
        "Dont Renouvelés",
        "Sorties (Quitta)",
        "Variation Nette",
        "Actifs en Classe"
    ]
    for col_idx, h in enumerate(headers1, 1):
        cell = ws1.cell(row=6, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = thin_border

    row_num = 7
    for m in data['matieres_summary']:
        ws1.cell(row=row_num, column=1, value=f"{m['icon']} {m['name']}").alignment = left_align
        ws1.cell(row=row_num, column=2, value=m['entries_count']).alignment = center_align
        ws1.cell(row=row_num, column=3, value=m['entries_new_stu']).alignment = center_align
        ws1.cell(row=row_num, column=4, value=m['entries_renewal']).alignment = center_align
        ws1.cell(row=row_num, column=5, value=m['exits_count']).alignment = center_align
        net_cell = ws1.cell(row=row_num, column=6, value=m['net_variation'])
        net_cell.alignment = center_align
        if m['net_variation'] > 0:
            net_cell.font = Font(name="Segoe UI", size=10, bold=True, color="16A34A")
        elif m['net_variation'] < 0:
            net_cell.font = Font(name="Segoe UI", size=10, bold=True, color="DC2626")
        else:
            net_cell.font = bold_font

        ws1.cell(row=row_num, column=7, value=m['active_now']).alignment = center_align

        for c in range(1, 8):
            cell = ws1.cell(row=row_num, column=c)
            if c != 6:
                cell.font = regular_font
            cell.border = thin_border
        row_num += 1

    # Totals Row
    ws1.cell(row=row_num, column=1, value="TOTAL GÉNÉRAL").alignment = left_align
    ws1.cell(row=row_num, column=2, value=data['total_entries']).alignment = center_align
    ws1.cell(row=row_num, column=3, value=data['total_new_students']).alignment = center_align
    ws1.cell(row=row_num, column=4, value=data['total_renewals']).alignment = center_align
    ws1.cell(row=row_num, column=5, value=data['total_exits']).alignment = center_align
    ws1.cell(row=row_num, column=6, value=data['total_net']).alignment = center_align
    ws1.cell(row=row_num, column=7, value=sum(m['active_now'] for m in data['matieres_summary'])).alignment = center_align

    for c in range(1, 8):
        cell = ws1.cell(row=row_num, column=c)
        cell.font = bold_font
        cell.fill = total_fill
        cell.border = thin_border

    # ==========================================
    # SHEET 2: LISTE DES ENTRÉES (DKHUL)
    # ==========================================
    ws2 = wb.create_sheet(title="Liste Entrées (Dkhul)")

    headers2 = [
        "Date Entrée", "Code", "Nom & Prénom", "Téléphone", "Matière",
        "Classe / Groupe", "Type d'Entrée", "Montant Payé (DH)", "Statut"
    ]
    for col_idx, h in enumerate(headers2, 1):
        cell = ws2.cell(row=1, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = thin_border

    r2 = 2
    for item in data['entries']:
        ws2.cell(row=r2, column=1, value=item['entry_date'].strftime('%d/%m/%Y')).alignment = center_align
        ws2.cell(row=r2, column=2, value=item['student_code']).alignment = center_align
        ws2.cell(row=r2, column=3, value=item['student_name']).alignment = left_align
        ws2.cell(row=r2, column=4, value=item['student_phone']).alignment = center_align
        ws2.cell(row=r2, column=5, value=item['matiere']).alignment = center_align
        ws2.cell(row=r2, column=6, value=item['course_name']).alignment = left_align
        ws2.cell(row=r2, column=7, value=item['entry_type_label_fr']).alignment = center_align
        ws2.cell(row=r2, column=8, value=item['paid_amount']).alignment = right_align
        ws2.cell(row=r2, column=9, value=item['status'].upper()).alignment = center_align

        for c in range(1, 10):
            cell = ws2.cell(row=r2, column=c)
            cell.font = regular_font
            cell.border = thin_border
        r2 += 1

    # ==========================================
    # SHEET 3: LISTE DES SORTIES (QUITTA)
    # ==========================================
    ws3 = wb.create_sheet(title="Liste Sorties (Quitta)")

    headers3 = [
        "Date Sortie", "Code", "Nom & Prénom", "Téléphone", "Matière",
        "Classe / Groupe", "Motif de Sortie", "Détail / Notes"
    ]
    for col_idx, h in enumerate(headers3, 1):
        cell = ws3.cell(row=1, column=col_idx, value=h)
        cell.fill = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid")
        cell.font = header_font
        cell.alignment = center_align
        cell.border = thin_border

    r3 = 2
    for item in data['exits']:
        ws3.cell(row=r3, column=1, value=item['exit_date'].strftime('%d/%m/%Y')).alignment = center_align
        ws3.cell(row=r3, column=2, value=item['student_code']).alignment = center_align
        ws3.cell(row=r3, column=3, value=item['student_name']).alignment = left_align
        ws3.cell(row=r3, column=4, value=item['student_phone']).alignment = center_align
        ws3.cell(row=r3, column=5, value=item['matiere']).alignment = center_align
        ws3.cell(row=r3, column=6, value=item['course_name']).alignment = left_align
        ws3.cell(row=r3, column=7, value=item['reason_fr']).alignment = center_align
        ws3.cell(row=r3, column=8, value=item['notes'][:120] if item['notes'] else '').alignment = left_align

        for c in range(1, 9):
            cell = ws3.cell(row=r3, column=c)
            cell.font = regular_font
            cell.border = thin_border
        r3 += 1

    # Auto-fit columns for all sheets
    for ws in [ws1, ws2, ws3]:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or '')
                if '\n' in val:
                    val = val.split('\n')[0]
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
