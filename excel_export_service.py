# -*- coding: utf-8 -*-
"""
excel_export_service.py
Service complet d'exportation de toutes les données de l'Institut ILAS au format Excel (.xlsx):
1. Classeur dédié « Classes & Élèves » (Groupé par classe, en-tête classe sur 2 lignes, sous-titre prof, et paiements mensuels)
2. Classeur « Export Global » (Classement de toutes les 19 tables de la base de données)
"""

import os
import re
import sqlite3
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'institut.db')
BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')

MONTH_DEFS = [
    (7, "Mois 07 (Juil)"),
    (8, "Mois 08 (Août)"),
    (9, "Mois 09 (Sept)"),
    (10, "Mois 10 (Oct)"),
    (11, "Mois 11 (Nov)"),
    (12, "Mois 12 (Déc)"),
    (1, "Mois 01 (Janv)"),
    (2, "Mois 02 (Févr)"),
    (3, "Mois 03 (Mars)"),
    (4, "Mois 04 (Avr)"),
    (5, "Mois 05 (Mai)"),
    (6, "Mois 06 (Juin)"),
]

BASE_HEADERS = [
    "N°", "N° C (Code)", "Nom et Prénom", "Téléphone", "Tél. Parent",
    "Niveau Scolaire", "Date Inscript.", "Tarif / M (DH)", "Frais Ins. (DH)",
    "Total Payé (DH)", "Reste (DH)", "Statut"
]


def _format_cell_value(val):
    if val is None:
        return ""
    if isinstance(val, (int, float)):
        return val
    return str(val)


def build_classes_and_students_sheet(ws, cur):
    """
    Construit la feuille des classes et étudiants groupés par classe :
    - En-tête du nom de classe fusionné sur 2 lignes avec police grasse
    - Sous-titre avec nom de l'enseignant, salle, horaires et tarif
    - Tableau des élèves avec informations complètes et colonnes de paiements de chaque mois
    - Ligne de total par classe
    """
    ws.views.sheetView[0].showGridLines = True

    cur.execute('''
        SELECT c.id, c.code, c.name, c.category, c.level, c.price_per_month, c.registration_fee,
               c.scheduled_days, c.session_duration,
               t.first_name || ' ' || t.last_name as teacher_name,
               r.name as room_name
        FROM courses c
        LEFT JOIN teachers t ON c.teacher_id = t.id
        LEFT JOIN rooms r ON c.room_id = r.id
        ORDER BY c.category, c.name
    ''')
    courses = cur.fetchall()

    ALL_HEADERS = BASE_HEADERS + [m[1] for m in MONTH_DEFS]
    TOTAL_COLS = len(ALL_HEADERS)

    # Styles
    font_class_title = Font(name="Arial", size=14, bold=True, color="FFFFFF")
    fill_class_title = PatternFill(start_color="00B050", end_color="00B050", fill_type="solid")  # Vert administratif officiel
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    font_sub = Font(name="Calibri", size=11, bold=True, color="1E293B")
    fill_sub = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

    font_th = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    fill_th = PatternFill(start_color="0B3D6E", end_color="0B3D6E", fill_type="solid")

    font_data = Font(name="Calibri", size=10)
    fill_zebra1 = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    fill_zebra2 = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    font_total = Font(name="Calibri", size=10.5, bold=True, color="0F172A")
    fill_total = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

    thin = Side(border_style="thin", color="CBD5E1")
    border_cell = Border(top=thin, left=thin, right=thin, bottom=thin)
    border_total = Border(top=Side(border_style="thin", color="94A3B8"),
                          bottom=Side(border_style="double", color="94A3B8"),
                          left=thin, right=thin)

    current_row = 1

    for c in courses:
        cid = c['id']
        c_code = c['code'] or f"CRS{cid:03d}"
        c_name = c['name'] or 'Classe sans nom'
        t_name = c['teacher_name'] or 'Non assigné'
        r_name = c['room_name'] or '-'
        days = c['scheduled_days'] or '-'
        duration = c['session_duration'] or ''
        price_m = float(c['price_per_month'] or 0.0)
        reg_fee = float(c['registration_fee'] or 0.0)

        # Élèves inscrits
        cur.execute('''
            SELECT e.id as enr_id, e.enroll_date, e.monthly_price, e.calculated_price, e.status as enr_status,
                   s.id as stu_id, s.code as stu_code, s.first_name, s.last_name, s.phone as stu_phone,
                   s.parent_phone, s.school_level
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            WHERE e.course_id = ?
            ORDER BY s.last_name, s.first_name
        ''', (cid,))
        students = cur.fetchall()

        # Si aucun élève inscrit, on passe à la suivante
        if not students:
            continue

        # 1. EN-TÊTE DE LA CLASSE (Fusionné sur 2 lignes et sur toutes les colonnes)
        row_title_start = current_row
        row_title_end = current_row + 1

        ws.merge_cells(start_row=row_title_start, start_column=1, end_row=row_title_end, end_column=TOTAL_COLS)
        ws.row_dimensions[row_title_start].height = 25
        ws.row_dimensions[row_title_end].height = 25

        title_cell = ws.cell(row=row_title_start, column=1)
        title_cell.value = f"📚 {c_name.upper()}  [{c_code}]"
        title_cell.font = font_class_title
        title_cell.alignment = align_center

        for r in range(row_title_start, row_title_end + 1):
            for col in range(1, TOTAL_COLS + 1):
                cell = ws.cell(row=r, column=col)
                cell.fill = fill_class_title
                cell.border = border_cell

        current_row += 2

        # 2. SOUS-TITRE : Enseignant, Salle, Horaires & Effectif
        row_sub = current_row
        ws.merge_cells(start_row=row_sub, start_column=1, end_row=row_sub, end_column=TOTAL_COLS)
        ws.row_dimensions[row_sub].height = 22

        sub_cell = ws.cell(row=row_sub, column=1)
        sub_cell.value = f"👨‍🏫 Professeur : {t_name}   |   📍 Salle : {r_name}   |   ⏰ Horaires : {days} {duration}   |   💰 Tarif Mensuel : {price_m:,.2f} DH   |   👥 Effectif : {len(students)} Élèves inscrits"
        sub_cell.font = font_sub
        sub_cell.alignment = align_center

        for col in range(1, TOTAL_COLS + 1):
            cell = ws.cell(row=row_sub, column=col)
            cell.fill = fill_sub
            cell.border = border_cell

        current_row += 1

        # 3. EN-TÊTES DES COLONNES DU TABLEAU
        row_th = current_row
        ws.row_dimensions[row_th].height = 26
        for c_idx, h in enumerate(ALL_HEADERS, 1):
            cell = ws.cell(row=row_th, column=c_idx, value=h)
            cell.font = font_th
            cell.fill = fill_th
            cell.alignment = align_center
            cell.border = border_cell

        current_row += 1

        # 4. LIGNES DES ÉLÈVES
        data_start_row = current_row
        for s_idx, st in enumerate(students, 1):
            row_data = current_row
            ws.row_dimensions[row_data].height = 20
            zebra = fill_zebra1 if s_idx % 2 != 0 else fill_zebra2

            enr_id = st['enr_id']
            stu_name = f"{st['first_name'] or ''} {st['last_name'] or ''}".strip()
            stu_code = st['stu_code'] or f"ETU{st['stu_id']:03d}"
            stu_phone = st['stu_phone'] or '-'
            parent_phone = st['parent_phone'] or '-'
            school_level = st['school_level'] or '-'
            enroll_date = st['enroll_date'] or '-'
            stu_status = 'Actif' if st['enr_status'] == 'active' else (st['enr_status'] or 'Inactif')
            fee_month = float(st['monthly_price'] or price_m)

            # Paiements de cet élève pour ce cours
            cur.execute('SELECT amount, date, note FROM payments WHERE enrollment_id = ?', (enr_id,))
            payments = cur.fetchall()

            total_paid = sum(float(p['amount'] or 0.0) for p in payments)
            reste = max(0.0, fee_month - total_paid) if fee_month > 0 else 0.0

            # Ventilation des paiements par mois
            monthly_amounts = {m[0]: 0.0 for m in MONTH_DEFS}
            for p in payments:
                note = (p['note'] or '').lower()
                m_match = re.search(r'mois\s*(\d{1,2})', note)
                if m_match:
                    m_num = int(m_match.group(1))
                else:
                    d = str(p['date'] or '')
                    m_num = int(d[5:7]) if len(d) >= 7 and d[5:7].isdigit() else 0
                if m_num in monthly_amounts:
                    monthly_amounts[m_num] += float(p['amount'] or 0.0)

            row_vals = [
                s_idx, stu_code, stu_name, stu_phone, parent_phone,
                school_level, enroll_date, fee_month, reg_fee,
                total_paid, reste, stu_status
            ]
            for m in MONTH_DEFS:
                m_val = monthly_amounts[m[0]]
                row_vals.append(m_val if m_val > 0 else "")

            for c_idx, val in enumerate(row_vals, 1):
                cell = ws.cell(row=row_data, column=c_idx, value=val)
                cell.font = font_data
                cell.fill = zebra
                cell.border = border_cell

                if c_idx in [1, 2, 7, 12]:
                    cell.alignment = align_center
                elif c_idx in [8, 9, 10, 11]:
                    cell.alignment = align_right
                    if isinstance(val, (int, float)):
                        cell.number_format = '#,##0.00'
                elif c_idx > 12:
                    cell.alignment = align_right
                    if isinstance(val, (int, float)) and val > 0:
                        cell.number_format = '#,##0.00'
                        cell.font = Font(name="Calibri", size=10, bold=True, color="047857")
                    else:
                        cell.alignment = align_center
                else:
                    cell.alignment = align_left

            current_row += 1

        data_end_row = current_row - 1

        # 5. LIGNE TOTAL DU GROUPE
        row_total = current_row
        ws.row_dimensions[row_total].height = 24
        ws.merge_cells(start_row=row_total, start_column=1, end_row=row_total, end_column=7)

        tot_label = ws.cell(row=row_total, column=1)
        tot_label.value = f"TOTAL DU GROUPE ({len(students)} Élèves)"
        tot_label.font = font_total
        tot_label.alignment = Alignment(horizontal="right", vertical="center")

        for col in range(1, 8):
            c = ws.cell(row=row_total, column=col)
            c.fill = fill_total
            c.border = border_total

        for c_idx in range(8, TOTAL_COLS + 1):
            col_letter = get_column_letter(c_idx)
            cell = ws.cell(row=row_total, column=c_idx)
            cell.value = f"=SUM({col_letter}{data_start_row}:{col_letter}{data_end_row})"
            cell.font = font_total
            cell.fill = fill_total
            cell.border = border_total
            cell.alignment = align_right
            cell.number_format = '#,##0.00'

        current_row += 3  # 2 lignes vides de séparation

    # Largeurs des colonnes adaptatives
    for col in ws.columns:
        max_len = 0
        for cell in col:
            val_str = str(cell.value or '')
            if cell.row < 4 or val_str.startswith("📚"):
                continue
            if len(val_str) > max_len:
                max_len = len(val_str)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 11), 32)


def create_classes_students_excel(db_path=None, output_path=None):
    """
    Génère un classeur Excel dédié spécifiquement aux Classes et leurs Élèves :
    groupé par classe avec en-têtes classe 2 lignes, sous-titres enseignant et paiements mensuels.
    """
    if db_path is None:
        db_path = DB_PATH
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    if output_path is None:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ILAS_Classes_et_Eleves_{ts}.xlsx"
        output_path = os.path.join(BACKUPS_DIR, filename)

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Base de données introuvable : {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Classes_et_Eleves"
    build_classes_and_students_sheet(ws, conn.cursor())

    conn.close()
    wb.save(output_path)
    return output_path


def create_master_excel_export(db_path=None, output_path=None):
    """
    Exporte toutes les tables de la base de données SQLite dans un fichier Excel multi-feuilles,
    avec la feuille « Classes_et_Eleves » en première position !
    """
    if db_path is None:
        db_path = DB_PATH
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    if output_path is None:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ILAS_Export_Global_{ts}.xlsx"
        output_path = os.path.join(BACKUPS_DIR, filename)

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Base de données introuvable : {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    wb = openpyxl.Workbook()
    # 1. PREMIÈRE FEUILLE : Classes et leurs Élèves groupés par classe
    ws_classes = wb.active
    ws_classes.title = "Classes_et_Eleves"
    build_classes_and_students_sheet(ws_classes, cur)

    # Styles pour les autres feuilles
    navy_fill = PatternFill(start_color="0B3D6E", end_color="0B3D6E", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    thin = Side(border_style="thin", color="CBD5E1")
    border = Border(top=thin, left=thin, right=thin, bottom=thin)
    font_body = Font(name="Calibri", size=10)

    def write_sheet(title, headers, rows, col_types=None):
        ws = wb.create_sheet(title=title[:31])
        ws.views.sheetView[0].showGridLines = True
        ws.row_dimensions[1].height = 28

        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.fill = navy_fill
            cell.font = header_font
            cell.alignment = align_center
            cell.border = border

        for row_idx, r in enumerate(rows, 2):
            ws.row_dimensions[row_idx].height = 20
            for col_idx, val in enumerate(r, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=_format_cell_value(val))
                cell.font = font_body
                cell.border = border
                ctype = col_types.get(col_idx, 'text') if col_types else 'text'
                if ctype == 'number':
                    cell.alignment = align_right
                    if isinstance(val, (int, float)):
                        cell.number_format = '#,##0.00'
                elif ctype == 'center':
                    cell.alignment = align_center
                else:
                    cell.alignment = align_left

        for col in ws.columns:
            max_len = 0
            for cell in col:
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 45)

    # 2. ÉLÈVES
    cur.execute("""
        SELECT id, code, first_name, last_name, gender, birth_date, phone, whatsapp, email,
               parent_name, parent_phone, school_level, school_name, city, address, cin,
               credit_balance, status, created_at, notes
        FROM students ORDER BY id ASC
    """)
    stu_headers = [
        "ID", "Code Élève", "Prénom", "Nom", "Genre", "Date de Naissance", "Téléphone",
        "WhatsApp", "Email", "Nom Parent / Tuteur", "Tél Parent", "Niveau Scolaire",
        "Établissement", "Ville", "Adresse", "CIN", "Solde Crédit (DH)", "Statut",
        "Date Inscription", "Remarques"
    ]
    write_sheet("Élèves", stu_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 5: 'center', 17: 'number'})

    # 3. ENSEIGNANTS
    cur.execute("""
        SELECT id, code, title, first_name, last_name, specialty, phone, email, cin,
               salary_type, salary_amount, hire_date, diploma, bank_name, bank_rib,
               CASE WHEN active = 1 THEN 'Actif' ELSE 'Inactif' END, notes
        FROM teachers ORDER BY id ASC
    """)
    tea_headers = [
        "ID", "Code", "Civilité", "Prénom", "Nom", "Spécialité", "Téléphone", "Email", "CIN",
        "Type Salaire", "Montant / Taux Salaire", "Date Embauche", "Diplôme", "Banque", "RIB",
        "Statut", "Remarques"
    ]
    write_sheet("Enseignants", tea_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 11: 'number', 16: 'center'})

    # 4. CLASSES & COURS (Table brute)
    cur.execute("""
        SELECT c.id, c.code, c.name, c.category, c.level, c.group_name,
               t.first_name || ' ' || t.last_name as teacher_name,
               r.name as room_name, c.price_per_month, c.registration_fee,
               c.sessions_per_week, c.session_duration, c.max_students,
               CASE WHEN c.active = 1 THEN 'Actif' ELSE 'Inactif' END, c.notes
        FROM courses c
        LEFT JOIN teachers t ON c.teacher_id = t.id
        LEFT JOIN rooms r ON c.room_id = r.id
        ORDER BY c.id ASC
    """)
    cou_headers = [
        "ID", "Code Cours", "Nom de la Classe", "Catégorie", "Niveau", "Groupe",
        "Enseignant", "Salle", "Prix Mensuel (DH)", "Frais Inscription (DH)",
        "Séances / Semaine", "Durée Séance", "Capacité Max", "Statut", "Notes"
    ]
    write_sheet("Classes_Cours", cou_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 9: 'number', 10: 'number', 14: 'center'})

    # 5. INSCRIPTIONS
    cur.execute("""
        SELECT e.id, s.code, s.first_name || ' ' || s.last_name as student_name,
               c.code as course_code, c.name as course_name,
               e.enroll_date, e.payment_plan, e.monthly_price, e.calculated_price,
               e.status, e.total_sessions_month, e.attended_sessions_month, e.notes
        FROM enrollments e
        JOIN students s ON e.student_id = s.id
        JOIN courses c ON e.course_id = c.id
        ORDER BY e.id ASC
    """)
    enr_headers = [
        "ID", "Code Élève", "Nom de l'Élève", "Code Cours", "Nom du Cours",
        "Date Inscription", "Plan Paiement", "Prix Mensuel (DH)", "Prix Net Calculé (DH)",
        "Statut", "Séances Prévues / Mois", "Séances Assistées", "Remarques"
    ]
    write_sheet("Inscriptions", enr_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 4: 'center', 8: 'number', 9: 'number', 10: 'center'})

    # 6. PAIEMENTS
    cur.execute("""
        SELECT p.id, p.receipt, p.date, s.code as student_code,
               s.first_name || ' ' || s.last_name as student_name,
               c.name as course_name, p.amount, p.method, p.note, p.recorded_by, p.created_at
        FROM payments p
        LEFT JOIN students s ON p.student_id = s.id
        LEFT JOIN enrollments e ON p.enrollment_id = e.id
        LEFT JOIN courses c ON e.course_id = c.id
        ORDER BY p.id ASC
    """)
    pay_headers = [
        "ID", "N° Reçu", "Date Paiement", "Code Élève", "Nom de l'Élève",
        "Classe / Cours", "Montant Payé (DH)", "Mode de Règlement",
        "Note / Mois", "Enregistré Par", "Date Création"
    ]
    write_sheet("Paiements", pay_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 4: 'center', 7: 'number', 8: 'center'})

    # 7. FACTURES
    cur.execute("""
        SELECT i.id, i.number, i.type, i.issue_date, i.due_date,
               s.code as student_code, s.first_name || ' ' || s.last_name as student_name,
               i.subtotal, i.tva_rate, i.tva_amount, i.total, i.status, i.notes
        FROM invoices i
        LEFT JOIN students s ON i.student_id = s.id
        ORDER BY i.id ASC
    """)
    inv_headers = [
        "ID", "N° Facture", "Type", "Date Émission", "Date Échéance",
        "Code Élève", "Nom Élève", "Sous-total HT (DH)", "Taux TVA (%)",
        "Montant TVA (DH)", "Total TTC (DH)", "Statut", "Notes"
    ]
    write_sheet("Factures", inv_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 8: 'number', 9: 'number', 10: 'number', 11: 'number', 12: 'center'})

    # 8. DÉTAIL DES FACTURES
    cur.execute("""
        SELECT ii.id, i.number as invoice_number, ii.description, ii.amount
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.id
        ORDER BY ii.id ASC
    """)
    write_sheet("Lignes_Factures", ["ID", "N° Facture", "Désignation", "Montant (DH)"], [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 4: 'number'})

    # 9. PRÉSENCES & ABSENCES
    cur.execute("""
        SELECT a.id, a.date, c.name as course_name, s.code as student_code,
               s.first_name || ' ' || s.last_name as student_name,
               a.status
        FROM attendances a
        JOIN courses c ON a.course_id = c.id
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC, a.id DESC
    """)
    write_sheet("Présences", ["ID", "Date de la Séance", "Classe / Cours", "Code Élève", "Nom de l'Élève", "Statut de Présence"], [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 4: 'center', 6: 'center'})

    # 10. DÉPENSES
    cur.execute("""
        SELECT e.id, e.date, e.category, e.description, e.amount,
               e.payment_method, e.reference_no, e.supplier_name, e.status, e.notes
        FROM expenses e
        ORDER BY e.date DESC, e.id DESC
    """)
    exp_headers = [
        "ID", "Date Dépense", "Catégorie", "Description / Libellé", "Montant (DH)",
        "Mode Paiement", "Réf Pièce / Chèque", "Fournisseur / Bénéficiaire", "Statut", "Remarques"
    ]
    write_sheet("Dépenses", exp_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 5: 'number', 9: 'center'})

    # 11. SALAIRES ENSEIGNANTS
    cur.execute("""
        SELECT p.id, p.receipt_no, p.period_month, t.first_name || ' ' || t.last_name as teacher_name,
               p.gross_amount, p.advances_deducted, p.net_amount, p.payment_date,
               p.payment_method, p.status, p.notes
        FROM teacher_salary_payouts p
        JOIN teachers t ON p.teacher_id = t.id
        ORDER BY p.id ASC
    """)
    tsp_headers = [
        "ID", "N° Reçu", "Mois / Période", "Enseignant", "Montant Brut (DH)",
        "Avances Déduites (DH)", "Net Versé (DH)", "Date Paiement",
        "Mode de Paiement", "Statut", "Remarques"
    ]
    write_sheet("Salaires_Enseignants", tsp_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 3: 'center', 5: 'number', 6: 'number', 7: 'number', 10: 'center'})

    # 12. AVANCES ENSEIGNANTS
    cur.execute("""
        SELECT a.id, a.receipt_no, a.date, a.period_month,
               t.first_name || ' ' || t.last_name as teacher_name,
               a.amount, a.payment_method, a.status, a.notes
        FROM teacher_advances a
        JOIN teachers t ON a.teacher_id = t.id
        ORDER BY a.id ASC
    """)
    tadv_headers = [
        "ID", "N° Reçu", "Date Avance", "Mois Concerné", "Enseignant",
        "Montant Avancé (DH)", "Mode de Versement", "Statut", "Remarques"
    ]
    write_sheet("Avances_Enseignants", tadv_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 6: 'number', 8: 'center'})

    # 13. EMPLOYÉS
    cur.execute("""
        SELECT id, code, first_name, last_name, cin, phone, email, job_title,
               department, base_salary, hire_date, bank_name, rib,
               CASE WHEN active = 1 THEN 'Actif' ELSE 'Inactif' END, notes
        FROM employees ORDER BY id ASC
    """)
    emp_headers = [
        "ID", "Code", "Prénom", "Nom", "CIN", "Téléphone", "Email", "Poste",
        "Département", "Salaire Base (DH)", "Date Embauche", "Banque", "RIB", "Statut", "Notes"
    ]
    write_sheet("Employés", emp_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 10: 'number', 14: 'center'})

    # 14. VENTES DE LIVRES / MANUELS
    cur.execute("""
        SELECT bs.id, bs.receipt_no, bs.sale_date, b.title as book_title,
               s.first_name || ' ' || s.last_name as student_name,
               bs.quantity, bs.unit_price, bs.total_amount, bs.payment_method, bs.notes
        FROM book_sales bs
        LEFT JOIN books b ON bs.book_id = b.id
        LEFT JOIN students s ON bs.student_id = s.id
        ORDER BY bs.id ASC
    """)
    bs_headers = [
        "ID", "N° Reçu", "Date Vente", "Titre du Manuel", "Élève Acheteur",
        "Quantité", "Prix Unitaire (DH)", "Montant Total (DH)", "Mode Paiement", "Notes"
    ]
    write_sheet("Ventes_Manuels", bs_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 6: 'number', 7: 'number', 8: 'number'})

    # 15. CATALOGUE MANUELS
    cur.execute("""
        SELECT id, code, title, publisher, category, level, purchase_price, sale_price, stock_quantity,
               CASE WHEN active = 1 THEN 'Disponible' ELSE 'Archivé' END, notes
        FROM books ORDER BY id ASC
    """)
    b_headers = [
        "ID", "Code", "Titre du Manuel", "Éditeur", "Catégorie", "Niveau",
        "Prix d'Achat (DH)", "Prix de Vente (DH)", "Stock Actuel", "Statut", "Notes"
    ]
    write_sheet("Catalogue_Manuels", b_headers, [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 7: 'number', 8: 'number', 9: 'number', 10: 'center'})

    # 16. TESTS DE POSITIONNEMENT
    cur.execute("""
        SELECT id, created_at, first_name, last_name, phone, whatsapp, email,
               language, school_level, score, max_score, percentage, recommended_level, status
        FROM placement_tests ORDER BY id DESC
    """)
    pt_headers = [
        "ID", "Date Test", "Prénom", "Nom", "Téléphone", "WhatsApp", "Email",
        "Langue", "Niveau Scolaire", "Score", "Score Max", "Pourcentage (%)",
        "Niveau Recommandé", "Statut"
    ]
    write_sheet("Tests_Positionnement", pt_headers, [list(r) for r in cur.fetchall()], {1: 'center', 10: 'number', 11: 'number', 12: 'number', 14: 'center'})

    # 17. SALLES
    cur.execute("SELECT id, name, capacity, notes FROM rooms ORDER BY id ASC")
    write_sheet("Salles", ["ID", "Nom de la Salle", "Capacité (places)", "Description / Équipement"], [list(r) for r in cur.fetchall()], {1: 'center', 3: 'number'})

    # 18. FOURNISSEURS
    cur.execute("SELECT id, name, category, contact_person, phone, email, address, city, ice FROM suppliers ORDER BY id ASC")
    write_sheet("Fournisseurs", ["ID", "Raison Sociale", "Catégorie", "Contact", "Téléphone", "Email", "Adresse", "Ville", "ICE"], [list(r) for r in cur.fetchall()], {1: 'center'})

    # 19. TARIFS
    cur.execute("SELECT id, code, name, category, language, billing_cycle, price, registration_fee, sessions_per_week, session_duration FROM tariffs ORDER BY id ASC")
    write_sheet("Grille_Tarifs", ["ID", "Code", "Formule / Tarif", "Catégorie", "Langue", "Périodicité", "Prix Mensuel (DH)", "Frais Inscription (DH)", "Séances / Semaine", "Durée"], [list(r) for r in cur.fetchall()], {1: 'center', 2: 'center', 7: 'number', 8: 'number'})

    conn.close()

    wb.save(output_path)
    return output_path
