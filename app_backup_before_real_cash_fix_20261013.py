# -*- coding: utf-8 -*-
import os
import sys
import threading
import webbrowser
import calendar
import io
import csv
import zipfile
import shutil
import re
import base64
import json
import uuid
import gzip
import qrcode
from datetime import date, datetime, timedelta
from functools import wraps
from sqlalchemy.orm import joinedload
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, send_file, send_from_directory, Response, jsonify, abort, has_request_context)
from werkzeug.utils import secure_filename
from urllib.parse import quote

from models import (db, User, Setting, Teacher, Room, Student, Course, Tariff,
                    Enrollment, Payment, Invoice, Attendance, Grade,
                    ScheduleSlot, LogEntry, BadgeRecord, CourseTeacher, InvoiceItem,
                    StudentCredit, SubstituteLog, SystemNotification, Certificate,
                    BlockedIP, LoginAttempt, Expense, RecurringCharge, Supplier, Book, BookSale,
                    TeacherAdvance, TeacherExpense, TeacherSalaryPayout, TeacherChargeItem,
                    TeacherPaymentVisibility, TeacherCandidate, TeacherStudentRequest,
                    Employee, EmployeeSalaryPayout, EmployeeAdvance,
                    PlacementTest, PlacementQuestion, StaffNote,
                    calculate_last_session_date, smart_shorten_course_name,
                    MATIERE_CONFIG, get_course_matiere, get_teacher_primary_matiere, get_matiere_priority)
import settings_helper as SH
from i18n import translate

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

BACKUPS_DIR = os.path.join(BASE, 'backups')
os.makedirs(BACKUPS_DIR, exist_ok=True)

app = Flask(__name__,
            template_folder=os.path.join(BASE, 'templates'),
            static_folder=os.path.join(BASE, 'static'))
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.jinja_env.globals['hasattr'] = hasattr
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ILAS_INSTITUT_SECURE_KEY_88997766554433221100_PROD')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=60)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE, 'institut.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'timeout': 30}
}
app.config['UPLOAD_FOLDER'] = os.path.join(BASE, 'static', 'uploads')
db.init_app(app)

from sqlalchemy.engine import Engine
from sqlalchemy import event
import sqlite3

@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers / context
# ---------------------------------------------------------------------------
def current_user():
    if not has_request_context():
        return None
    uid = session.get('uid')
    if uid:
        return db.session.get(User, uid)
    return None


def lang():
    return session.get('lang') or SH.get_setting('default_lang', 'fr')



def get_current_teacher():
    """Identifie le profil Enseignant associé à l'utilisateur connecté."""
    u = current_user()
    if not u or u.role != 'teacher':
        return None
    if u.teacher_id:
        t = db.session.get(Teacher, u.teacher_id)
        if t:
            return t
    # Repli intelligent par recherche de nom
    name_clean = (u.full_name or u.username or '').strip().lower()
    for prefix in ['prof.', 'prof ']:
        if name_clean.startswith(prefix):
            name_clean = name_clean[len(prefix):].strip()
    for t in Teacher.query.filter_by(active=True).all():
        t_name = t.full_name.strip().lower()
        if t_name == name_clean or name_clean in t_name or t_name in name_clean:
            return t
        if t.last_name and t.last_name.strip().lower() in name_clean:
            return t
    return None


def get_teacher_course_ids(teacher_id):
    """Retourne la liste des IDs de cours assignés à cet enseignant."""
    if not teacher_id:
        return []
    direct = [c.id for c in Course.query.filter_by(teacher_id=teacher_id, active=True).all()]
    via_ct = [ct.course_id for ct in CourseTeacher.query.filter_by(teacher_id=teacher_id, is_active=True).all()]
    return sorted(list(set(direct + via_ct)))


def get_teacher_courses(teacher_id):
    """Retourne les objets Course assignés à cet enseignant."""
    cids = get_teacher_course_ids(teacher_id)
    if not cids:
        return []
    return Course.query.filter(Course.id.in_(cids), Course.active == True).order_by(Course.name).all()


def get_teacher_student_ids(teacher_id):
    """Retourne la liste des IDs d'élèves inscrits dans les cours de cet enseignant."""
    cids = get_teacher_course_ids(teacher_id)
    if not cids:
        return []
    ens = Enrollment.query.filter(Enrollment.course_id.in_(cids), Enrollment.status != 'dropped').all()
    return sorted(list(set([e.student_id for e in ens if e.student_id])))


def build_student_search_filter(q, student_model=Student):
    """
    Construit un filtre SQLAlchemy pour la recherche d'élèves par prénom, nom,
    nom complet (dans n'importe quel ordre), code, téléphone, téléphone parent, cin.
    """
    if not q:
        return None
    q_clean = " ".join(q.split())
    tokens = q_clean.split()
    if not tokens:
        return None

    full_name_1 = db.func.coalesce(student_model.first_name, '') + ' ' + db.func.coalesce(student_model.last_name, '')
    full_name_2 = db.func.coalesce(student_model.last_name, '') + ' ' + db.func.coalesce(student_model.first_name, '')

    token_match = db.and_(*[full_name_1.ilike(f"%{t}%") for t in tokens])

    conds = [
        token_match,
        full_name_1.ilike(f"%{q_clean}%"),
        full_name_2.ilike(f"%{q_clean}%"),
        student_model.first_name.ilike(f"%{q_clean}%"),
        student_model.last_name.ilike(f"%{q_clean}%"),
        student_model.code.ilike(f"%{q_clean}%")
    ]
    if hasattr(student_model, 'phone'):
        conds.append(student_model.phone.ilike(f"%{q_clean}%"))
    if hasattr(student_model, 'parent_phone'):
        conds.append(student_model.parent_phone.ilike(f"%{q_clean}%"))
    if hasattr(student_model, 'cin'):
        conds.append(student_model.cin.ilike(f"%{q_clean}%"))

    return db.or_(*conds)


def build_teacher_search_filter(q, teacher_model=Teacher):
    """
    Construit un filtre SQLAlchemy pour la recherche d'enseignants par prénom, nom,
    nom complet (dans n'importe quel ordre), code, spécialité, téléphone, cin.
    """
    if not q:
        return None
    q_clean = " ".join(q.split())
    tokens = q_clean.split()
    if not tokens:
        return None

    full_name_1 = db.func.coalesce(teacher_model.first_name, '') + ' ' + db.func.coalesce(teacher_model.last_name, '')
    full_name_2 = db.func.coalesce(teacher_model.last_name, '') + ' ' + db.func.coalesce(teacher_model.first_name, '')

    token_match = db.and_(*[full_name_1.ilike(f"%{t}%") for t in tokens])

    conds = [
        token_match,
        full_name_1.ilike(f"%{q_clean}%"),
        full_name_2.ilike(f"%{q_clean}%"),
        teacher_model.first_name.ilike(f"%{q_clean}%"),
        teacher_model.last_name.ilike(f"%{q_clean}%"),
        teacher_model.code.ilike(f"%{q_clean}%")
    ]
    if hasattr(teacher_model, 'specialty'):
        conds.append(teacher_model.specialty.ilike(f"%{q_clean}%"))
    if hasattr(teacher_model, 'phone'):
        conds.append(teacher_model.phone.ilike(f"%{q_clean}%"))
    if hasattr(teacher_model, 'cin'):
        conds.append(teacher_model.cin.ilike(f"%{q_clean}%"))

    return db.or_(*conds)


def build_enrollment_search_filter(q):
    """
    Construit un filtre SQLAlchemy complet pour la Liste des Inscrits (Enrollment) :
    Recherche par élève (prénom, nom, nom complet dans n'importe quel ordre, code),
    cours (nom du cours, langue) ou combinaison (ex: 'NIHAD Anglais').
    """
    if not q:
        return None
    q_clean = " ".join(q.split())
    tokens = q_clean.split()
    if not tokens:
        return None

    student_full_1 = db.func.coalesce(Student.first_name, '') + ' ' + db.func.coalesce(Student.last_name, '')
    student_full_2 = db.func.coalesce(Student.last_name, '') + ' ' + db.func.coalesce(Student.first_name, '')
    combined_search_target = (
        student_full_1 + ' ' + 
        student_full_2 + ' ' + 
        db.func.coalesce(Student.code, '') + ' ' + 
        db.func.coalesce(Course.name, '') + ' ' + 
        db.func.coalesce(Course.language, '')
    )

    all_tokens_match = db.and_(*[combined_search_target.ilike(f"%{t}%") for t in tokens])

    conds = [
        all_tokens_match,
        student_full_1.ilike(f"%{q_clean}%"),
        student_full_2.ilike(f"%{q_clean}%"),
        Student.first_name.ilike(f"%{q_clean}%"),
        Student.last_name.ilike(f"%{q_clean}%"),
        Student.code.ilike(f"%{q_clean}%"),
        Course.name.ilike(f"%{q_clean}%"),
        Course.language.ilike(f"%{q_clean}%")
    ]
    return db.or_(*conds)


@app.context_processor
def inject_globals():
    unreads = SystemNotification.query.filter_by(is_read=False).order_by(SystemNotification.created_at.desc()).limit(10).all() if session.get('uid') else []
    unread_cnt = SystemNotification.query.filter_by(is_read=False).count() if session.get('uid') else 0
    
    active_staff_notes_cnt = 0
    if session.get('uid'):
        try:
            u = current_user()
            if u:
                if u.role == 'admin':
                    active_staff_notes_cnt = StaffNote.query.filter_by(status='pending').count()
                else:
                    all_p = StaffNote.query.filter_by(status='pending').all()
                    active_staff_notes_cnt = sum(1 for n in all_p if n.is_visible_to(u))
        except Exception:
            pass

    pending_teacher_requests_cnt = 0
    if session.get('uid'):
        try:
            pending_teacher_requests_cnt = TeacherStudentRequest.query.filter_by(status='pending').count()
        except Exception:
            pass

    return dict(
        settings=SH.all_settings_dict(),
        lang=lang(),
        t=lambda k: translate(k, lang()),
        cur_user=current_user(),
        today=date.today(),
        yesterday=date.today() - timedelta(days=1),
        timedelta=timedelta,
        date=date,
        unread_notifications=unreads,
        unread_notifications_count=unread_cnt,
        active_staff_notes_count=active_staff_notes_cnt,
        pending_teacher_requests_count=pending_teacher_requests_cnt,
        max=max,
        min=min,
        round=round,
        smart_shorten_course_name=smart_shorten_course_name,
    )


@app.template_filter('smart_short_course')
def smart_short_course_filter(val, course=None):
    if hasattr(val, 'receipt_name'):
        return val.receipt_name
    return smart_shorten_course_name(val, course=course)


@app.after_request
def compress_response(response):
    accept_encoding = request.headers.get('Accept-Encoding', '')
    if ('gzip' in accept_encoding and
            response.status_code == 200 and
            not response.direct_passthrough and
            'Content-Encoding' not in response.headers and
            response.mimetype in ['text/html', 'text/css', 'application/javascript', 'application/json', 'text/plain']):
        response_data = response.get_data()
        if len(response_data) > 1024:
            compressed = gzip.compress(response_data, compresslevel=6)
            response.set_data(compressed)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(compressed)
    return response


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        uid = session.get('uid')
        if not uid:
            return redirect(url_for('login'))
        u = db.session.get(User, uid)
        if not u or not u.active:
            session.clear()
            flash('Votre compte a été désactivé ou n\'existe plus. Accès refusé.', 'danger')
            return redirect(url_for('login'))
        return f(*a, **kw)
    return wrapper


def role_required(*roles):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **kw):
            u = current_user()
            if not u:
                return redirect(url_for('login'))
            if u.role not in roles:
                flash('Accès refusé', 'danger')
                if u.role == 'teacher':
                    return redirect(url_for('attendance'))
                return redirect(url_for('dashboard'))
            return f(*a, **kw)
        return wrapper
    return deco


def log_action(action, detail=''):
    u = current_user()
    db.session.add(LogEntry(user_id=u.id if u else None, action=action, detail=detail))
    db.session.commit()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.svg', mimetype='image/svg+xml')


def parse_date(v):
    if not v:
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, datetime):
        return v.date()
    v_str = str(v).strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(v_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def fmt_amount(v):
    cur = SH.get_setting('currency', 'MAD')
    try:
        return f"{float(v):,.2f} {cur}".replace(',', ' ')
    except (TypeError, ValueError):
        return f"0.00 {cur}"


def create_auto_backup(reason='auto'):
    """Crée une archive ZIP compressée et horodatée de la base SQLite dans backups/"""
    db_path = os.path.join(BASE, 'institut.db')
    if not os.path.exists(db_path):
        return None
    try:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"backup_{reason}_{ts}.zip"
        zip_filepath = os.path.join(BACKUPS_DIR, zip_filename)
        
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_path, arcname='institut.db')
            
        # Rotation : conserver les 15 dernières sauvegardes les plus récentes par date de modification
        all_backups = [f for f in os.listdir(BACKUPS_DIR) if f.startswith('backup_') and (f.endswith('.zip') or f.endswith('.db'))]
        all_backups.sort(key=lambda x: os.path.getmtime(os.path.join(BACKUPS_DIR, x)), reverse=True)
        for old in all_backups[15:]:
            try:
                os.remove(os.path.join(BACKUPS_DIR, old))
            except Exception:
                pass
                
        return zip_filename
    except Exception as e:
        print(">>> Backup error notice:", e)
        return None


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    client_ip = (request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')).split(',')[0].strip()

    # Check if IP is currently blocked
    blocked = BlockedIP.query.filter_by(ip_address=client_ip, is_blocked=True).first()
    if blocked:
        if blocked.blocked_until and datetime.utcnow() > blocked.blocked_until:
            blocked.is_blocked = False
            db.session.commit()
        else:
            flash(f"🚨 Votre adresse IP ({client_ip}) est temporairement bloquée suite à plusieurs échecs de connexion. Veuillez contacter l'administrateur.", 'danger')
            return render_template('login.html')

    if request.method == 'POST':
        uname = request.form.get('username', '').strip()
        pwd = request.form.get('password', '')
        u = User.query.filter(db.func.lower(User.username) == uname.lower()).first()

        if u and u.check_password(pwd) and u.active:
            session.permanent = True
            session['uid'] = u.id
            session['lang'] = request.form.get('lang') or lang()
            
            attempt = LoginAttempt(ip_address=client_ip, username=u.username, success=True, attempted_at=datetime.utcnow())
            db.session.add(attempt)

            role_fr = {'admin': 'Administrateur', 'secretary': 'Secrétaire', 'teacher': 'Enseignant'}.get(u.role, u.role.capitalize())
            notif = SystemNotification(
                title=f"👤 Connexion réussie : {u.full_name or u.username}",
                message=f"Compte @{u.username} ({role_fr}) connecté depuis l’adresse IP {client_ip}.",
                link="/settings/security"
            )
            db.session.add(notif)
            db.session.commit()

            log_action('login', u.username)
            if u.role == 'teacher':
                return redirect(url_for('attendance'))
            return redirect(url_for('dashboard'))

        try:
            attempt = LoginAttempt(ip_address=client_ip, username=uname, success=False, attempted_at=datetime.utcnow())
            db.session.add(attempt)

            notif_fail = SystemNotification(
                title=f"🚨 Mot de passe incorrect : @{uname or 'inconnu'}",
                message=f"Tentative échouée de connexion avec mot de passe erroné pour le compte '{uname}' depuis l'adresse IP {client_ip}.",
                link="/settings/security"
            )
            db.session.add(notif_fail)
            db.session.commit()

            ten_mins_ago = datetime.utcnow() - timedelta(minutes=15)
            failed_count = LoginAttempt.query.filter(
                LoginAttempt.ip_address == client_ip,
                LoginAttempt.success == False,
                LoginAttempt.attempted_at >= ten_mins_ago
            ).count()

            if failed_count >= 5:
                blocked_until = datetime.utcnow() + timedelta(minutes=30)
                blk = BlockedIP.query.filter_by(ip_address=client_ip).first()
                if not blk:
                    blk = BlockedIP(ip_address=client_ip)
                    db.session.add(blk)
                blk.is_blocked = True
                blk.failed_attempts = failed_count
                blk.blocked_until = blocked_until
                db.session.commit()

                notif = SystemNotification(
                    title=f"🚨 Alert Sécurité : IP Bloquée ({client_ip})",
                    message=f"L'adresse IP {client_ip} a été automatiquement bloquée après {failed_count} échecs de connexion sur le compte '{uname}'.",
                    link="/settings/security"
                )
                db.session.add(notif)
                db.session.commit()

                flash(f"🚨 Trop d'échecs de connexion ({failed_count} essais). Votre adresse IP ({client_ip}) a été bloquée par sécurité pendant 30 minutes.", 'danger')
                return render_template('login.html')

            flash(f'Nom d’utilisateur ou mot de passe incorrect (Essai {failed_count}/5)', 'danger')
        except Exception as e:
            db.session.rollback()
            flash('Nom d’utilisateur ou mot de passe incorrect.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/set_lang/<l>')
@login_required
def set_lang(l):
    if l in ('fr', 'ar'):
        session['lang'] = l
    return redirect(request.referrer or url_for('dashboard'))


# ---------------------------------------------------------------------------
# PWA (Progressive Web App) Routes
# ---------------------------------------------------------------------------
@app.route('/manifest.json')
def web_manifest():
    res = send_from_directory(os.path.join(BASE, 'static'), 'manifest.json', mimetype='application/manifest+json')
    res.headers['Cache-Control'] = 'no-cache'
    return res


@app.route('/sw.js')
def service_worker():
    res = send_from_directory(os.path.join(BASE, 'static'), 'sw.js', mimetype='application/javascript')
    res.headers['Service-Worker-Allowed'] = '/'
    res.headers['Cache-Control'] = 'no-cache'
    return res


@app.route('/offline.html')
def offline_page():
    return render_template('offline.html')



# ---------------------------------------------------------------------------
# Secretary Inscription Bonus / Commission Calculator
# ---------------------------------------------------------------------------
def is_new_student_enrollment(enrollment):
    """
    Vérifie si une inscription correspond à un NOUVEL élève (première inscription)
    ou à un RENOUVELLEMENT / TRANSFERT d'un élève existant.
    Règle : Seules les nouvelles inscriptions donnent droit au bonus d'inscription.
    """
    if not enrollment or not enrollment.student_id:
        return True

    # 0. Statuts exclus (abandonné, annulé, transféré)
    if getattr(enrollment, 'status', None) in ['dropped', 'cancelled', 'transferred']:
        return False

    # 1. Vérification par les marqueurs explicites générés par le système
    if enrollment.notes:
        notes_lower = enrollment.notes.lower().strip()
        system_markers = [
            'renouvellement (', 'suite à l\'inscription', 'suite a l\'inscription',
            'transféré depuis', 'transfere depuis', 'transféré vers', 'transfere vers'
        ]
        if any(m in notes_lower for m in system_markers) or notes_lower in ['renouvellement', 'renew', 'renewal', 'transfert', 'transfer']:
            return False

    # 2. Vérification d'inscriptions antérieures
    e_date = enrollment.enroll_date or date.today()
    prior_enrollments = Enrollment.query.filter(
        Enrollment.student_id == enrollment.student_id,
        Enrollment.id != (enrollment.id or 0)
    ).all()

    for pe in prior_enrollments:
        # Ignorer les anciennes tentatives à 0 DH (essai annulé, abandon à 0 DH, attente groupe non payée)
        if float(pe.total_paid or 0.0) <= 0.0 and getattr(pe, 'status', None) in ['dropped', 'cancelled', 'pending_assignment', 'trial']:
            continue

        pe_date = pe.enroll_date or (pe.created_at.date() if pe.created_at else date.today())
        if pe.course_id == enrollment.course_id:
            # Même cours : toute inscription antérieure est un renouvellement
            if pe_date < e_date or (pe_date == e_date and (pe.id or 0) < (enrollment.id or 0)):
                return False
        else:
            # Cours différent : si les inscriptions ont été créées simultanément (pack), ce n'est pas un renouvellement
            is_same_day_pack = False
            if pe.created_at and enrollment.created_at:
                if abs((enrollment.created_at - pe.created_at).total_seconds()) < 86400:
                    is_same_day_pack = True
            if not is_same_day_pack and pe_date < e_date:
                return False

    # 3. Vérification de l'ancienneté du dossier élève (sécurité si d'anciennes inscriptions ont été supprimées)
    student = enrollment.student or (Student.query.get(enrollment.student_id) if enrollment.student_id else None)
    if student and student.created_at:
        stu_created_dt = student.created_at.date()
        # Si la fiche de l'élève a été créée lors d'un mois antérieur (il y a > 10 jours) ET qu'il a déjà des paiements antérieurs
        if (e_date.year > stu_created_dt.year or e_date.month > stu_created_dt.month) and (e_date - stu_created_dt).days > 10:
            has_prior_payments = Payment.query.filter(
                Payment.student_id == student.id,
                Payment.date < e_date,
                Payment.amount > 0
            ).count() > 0
            if has_prior_payments:
                return False

    return True


def calculate_enrollment_secretary_bonus(enrollment, commission_rate=None, user=None):
    """
    Calcule la prime/commission de la secrétaire ou collaborateur pour une inscription donnée.
    
    RÈGLES :
    A. Pour @mriliass :
       - Système FORFAIT FIXE par NOUVELLE inscription :
         * Formation Langue (Anglais, Français, Espagnol...) : 50 DH
         * Soutien scolaire (Tutoring) : 20 DH
         * Multi-cours pour un nouvel élève (Pack) : prime sur chaque cours (ex: 50+20 = 70 DH)
         * Renouvellement / Transfert de classe : 0 DH
       - Condition d'encaissement :
         * L'élève doit avoir payé au moins 100 DH (ou la totalité si le prix < 100 DH).
         * Si payé < 100 DH : prime en attente (0 DH débloqué tant que le seuil n'est pas atteint).
         * Dès que >= 100 DH est encaissé : la prime est débloquée à 100%.
         * Pas de doublon lorsque l'élève complète le reste de la scolarité.

    B. Pour les autres utilisateurs (ex: Secrétaire standard) :
       - Calcul au POURCENTAGE sur la marge nette encaissée (système classique).
    """
    if not enrollment:
        return None

    # Identifier l'utilisateur cible
    target_user = user or (enrollment.creator if enrollment else None)
    is_mriliass = bool(target_user and getattr(target_user, 'username', '') and target_user.username.strip().lower() == 'mriliass')

    # Taux de commission (%) pour le mode standard
    if commission_rate is not None:
        rate = float(commission_rate)
    elif enrollment.creator and enrollment.creator.commission_rate is not None:
        rate = float(enrollment.creator.commission_rate)
    else:
        rate = 0.0

    # 1. Vérification Nouveau Élève vs Renouvellement / Transfert
    is_new_student = is_new_student_enrollment(enrollment)

    # 2. Frais d'inscription (frais de dossier de l'école)
    m_price = float(enrollment.monthly_price or 0.0)
    calc_price = float(enrollment.calculated_price or 0.0)
    reg_fee = 0.0
    if calc_price > m_price and m_price > 0:
        reg_fee = round(calc_price - m_price, 2)
    elif enrollment.course and enrollment.course.registration_fee:
        reg_fee = float(enrollment.course.registration_fee)
    elif enrollment.tariff and enrollment.tariff.registration_fee:
        reg_fee = float(enrollment.tariff.registration_fee)

    # 3. Montant théorique de scolarité
    if m_price > 0:
        tuition_theoretical = m_price
    else:
        due = float(enrollment.due_amount or 0.0)
        tuition_theoretical = max(0.0, due - reg_fee)

    due_total = float(enrollment.due_amount or (tuition_theoretical + reg_fee))
    total_paid = float(enrollment.total_paid or 0.0)

    # 4. Scolarité réellement encaissée (après déduction des frais de dossier)
    if total_paid >= reg_fee:
        paid_tuition = min(tuition_theoretical, round(total_paid - reg_fee, 2))
    else:
        paid_tuition = 0.0

    payment_ratio = (paid_tuition / tuition_theoretical) if tuition_theoretical > 0 else (1.0 if total_paid > 0 else 0.0)
    payment_ratio = min(1.0, max(0.0, payment_ratio))

    # 5. Traitement selon affectation de groupe
    is_pending_group = (enrollment.status == 'pending_assignment' or enrollment.course_id is None)

    notes_lower = (enrollment.notes or '').lower()
    is_transfer = (enrollment.status == 'transferred') or any(w in notes_lower for w in ['transféré', 'transfere', 'transfer'])
    is_dropped = (enrollment.status in ['dropped', 'cancelled'])

    # Part enseignant et marge école standard pour affichage
    if is_pending_group:
        teacher_rate_str = "50% (Estimé en attente)"
        teacher_name = "Non affecté (En attente)"
        teacher_share_full = round(tuition_theoretical * 0.5, 2)
        teacher_share_paid = round(paid_tuition * 0.5, 2)
        school_net_full = max(0.0, round(tuition_theoretical - teacher_share_full, 2))
        school_net_paid = max(0.0, round(paid_tuition - teacher_share_paid, 2))
    else:
        course = enrollment.course
        teacher = course.teacher if course else None
        if teacher:
            teacher_name = teacher.full_name
            ct = CourseTeacher.query.filter_by(course_id=course.id, teacher_id=teacher.id, is_active=True).first()
            if not ct:
                ct = CourseTeacher.query.filter_by(course_id=course.id, teacher_id=teacher.id).first()

            comp_type = ct.compensation_type if ct else (teacher.salary_type or 'percentage')
            comp_val = ct.compensation_value if (ct and ct.compensation_value is not None) else (teacher.salary_amount if (teacher.salary_amount is not None and teacher.salary_amount > 0) else 50.0)

            if comp_type == 'percentage':
                teacher_share_full = round(tuition_theoretical * (comp_val / 100.0), 2)
                teacher_share_paid = round(paid_tuition * (comp_val / 100.0), 2)
                teacher_rate_str = f"{comp_val:.0f}%"
            elif comp_type == 'per_student':
                teacher_share_full = round(min(tuition_theoretical, comp_val), 2)
                teacher_share_paid = round(teacher_share_full * payment_ratio, 2)
                teacher_rate_str = f"{comp_val:.0f} DH/él."
            elif comp_type == 'fixed':
                en_cnt = max(1, course.enrolled_count)
                teacher_share_full = round(comp_val / en_cnt, 2)
                teacher_share_paid = round(teacher_share_full * payment_ratio, 2)
                teacher_rate_str = f"Fixe ({comp_val:.0f} DH)"
            elif comp_type == 'hourly':
                slots_count = ScheduleSlot.query.filter_by(course_id=course.id).count() or 3
                en_cnt = max(1, course.enrolled_count)
                teacher_share_full = round((slots_count * 4 * comp_val) / en_cnt, 2)
                teacher_share_paid = round(teacher_share_full * payment_ratio, 2)
                teacher_rate_str = f"Horaire ({comp_val:.0f} DH/h)"
            else:
                teacher_share_full = round(tuition_theoretical * 0.5, 2)
                teacher_share_paid = round(paid_tuition * 0.5, 2)
                teacher_rate_str = "50%"
        else:
            teacher_name = "Aucun enseignant"
            teacher_share_full = 0.0
            teacher_share_paid = 0.0
            teacher_rate_str = "0%"

        school_net_full = max(0.0, round(tuition_theoretical - teacher_share_full, 2))
        school_net_paid = max(0.0, round(paid_tuition - teacher_share_paid, 2))

    # --- CALCUL DE LA PRIME ---
    if is_mriliass:
        # Déterminer la catégorie du cours (Langue = 50 DH, Soutien = 20 DH)
        course = enrollment.course if enrollment else None
        cat = 'language'
        if course:
            cat = getattr(course, 'category', None) or ('language' if getattr(course, 'language', None) else 'language')
        elif enrollment.tariff:
            cat = getattr(enrollment.tariff, 'category', None) or 'language'

        is_language = (cat == 'language')
        fixed_bonus_target = 50.0 if is_language else 20.0
        cat_str = "Langue 50 DH" if is_language else "Soutien 20 DH"
        rate_str = f"Fixe {cat_str}"

        # Règle d'or @mriliass : MAX 1 SEULE PRIME PAR ÉLÈVE (la plus élevée : 50 DH si Langue, sinon 20 DH si Soutien)
        is_already_covered_by_other = False
        already_covered_bonus = 0.0
        if is_new_student and not is_dropped:
            other_enrolls = Enrollment.query.filter(
                Enrollment.student_id == enrollment.student_id,
                Enrollment.id != (enrollment.id or 0)
            ).all()
            for pe in other_enrolls:
                if getattr(pe, 'status', None) in ['dropped', 'cancelled', 'transferred']:
                    continue
                if pe.course_id is None or getattr(pe, 'status', None) == 'pending_assignment':
                    continue
                if not is_new_student_enrollment(pe):
                    continue
                pe_paid = float(pe.total_paid or 0.0)
                pe_c = pe.course
                pe_cat = getattr(pe_c, 'category', None) or ('language' if getattr(pe_c, 'language', None) else 'language') if pe_c else 'language'
                pe_is_lang = (pe_cat == 'language')
                pe_bonus = 50.0 if pe_is_lang else 20.0

                if pe_paid >= 100.0:
                    # pe est déjà qualifiée (payée >= 100 DH)
                    if pe_bonus > fixed_bonus_target:
                        is_already_covered_by_other = True
                        already_covered_bonus = max(already_covered_bonus, pe_bonus)
                    elif pe_bonus == fixed_bonus_target:
                        if total_paid < 100.0 or (pe.id or 0) < (enrollment.id or 0):
                            is_already_covered_by_other = True
                            already_covered_bonus = max(already_covered_bonus, pe_bonus)
                elif total_paid < 100.0:
                    # Aucune des deux n'est payée : éviter de compter deux fois le reste à débloquer
                    if pe_bonus > fixed_bonus_target or (pe_bonus == fixed_bonus_target and (pe.id or 0) < (enrollment.id or 0)):
                        is_already_covered_by_other = True
                        already_covered_bonus = max(already_covered_bonus, pe_bonus)

        if is_dropped:
            bonus_potential = 0.0
            bonus_earned = 0.0
            bonus_remaining = 0.0
            status_key = 'cancelled'
            status_label = "❌ Abandon / Annulée (Non éligible)"
            status_badge = "chip-gray"
            is_confirmed = False
        elif not is_new_student:
            bonus_potential = 0.0
            bonus_earned = 0.0
            bonus_remaining = 0.0
            if is_transfer:
                status_key = 'transfer'
                status_label = "🔀 Transfert (Non éligible)"
            else:
                status_key = 'renewal'
                status_label = "🔄 Renouvellement (Non éligible)"
            status_badge = "chip-gray"
            is_confirmed = False
        elif is_already_covered_by_other:
            bonus_potential = 0.0
            bonus_earned = 0.0
            bonus_remaining = 0.0
            status_key = 'pack_soutien'
            if total_paid >= 100.0:
                status_label = f"📦 Multi-cours (Prime {already_covered_bonus:.0f} DH déjà comptée)"
            else:
                status_label = "📦 Multi-cours (Inclus dans dossier élève)"
            status_badge = "chip-gray"
            is_confirmed = False
        elif is_pending_group:
            bonus_potential = fixed_bonus_target
            bonus_earned = 0.0
            bonus_remaining = fixed_bonus_target
            status_key = 'pending_group'
            status_label = f"⏳ En attente groupe ({cat_str})"
            status_badge = "chip-amber"
            is_confirmed = False
        else:
            # Nouveau élève avec cours assigné
            # Condition de déblocage : Au moins 100 DH payé réellement
            is_qualified = (total_paid >= 100.0)
            bonus_potential = fixed_bonus_target

            if is_qualified:
                bonus_earned = fixed_bonus_target
                bonus_remaining = 0.0
                status_key = 'full'
                status_label = f"✅ Validée ({fixed_bonus_target:.0f} DH - Payé {total_paid:.0f} DH)"
                status_badge = "chip-green"
                is_confirmed = True
            else:
                bonus_earned = 0.0
                bonus_remaining = fixed_bonus_target
                status_key = 'pending_payment'
                status_label = f"⏳ En attente paiement (Min 100 DH - Payé {total_paid:.0f}/{due_total:.0f} DH)"
                status_badge = "chip-amber"
                is_confirmed = False

    else:
        # MODE STANDARD PAR POURCENTAGE
        rate_str = f"{rate:.1f}%"
        if not is_new_student:
            bonus_potential = 0.0
            bonus_earned = 0.0
            bonus_remaining = 0.0
            if is_transfer:
                status_key = 'transfer'
                status_label = "🔀 Transfert (Non éligible)"
            else:
                status_key = 'renewal'
                status_label = "🔄 Renouvellement (Non éligible)"
            status_badge = "chip-gray"
            is_confirmed = False
        elif is_pending_group:
            bonus_potential = round(school_net_full * (rate / 100.0), 2)
            bonus_earned = round(school_net_paid * (rate / 100.0), 2)
            bonus_remaining = max(0.0, round(bonus_potential - bonus_earned, 2))
            status_key = 'pending_group'
            status_label = "⏳ En attente de confirmation du groupe"
            status_badge = "chip-amber"
            is_confirmed = False
        else:
            bonus_potential = round(school_net_full * (rate / 100.0), 2)
            bonus_earned = round(school_net_paid * (rate / 100.0), 2)
            bonus_remaining = max(0.0, round(bonus_potential - bonus_earned, 2))

            if total_paid >= due_total and due_total > 0:
                status_key = 'full'
                status_label = "✅ Validée (100% Payé)"
                status_badge = "chip-green"
                is_confirmed = True
            elif bonus_earned > 0:
                status_key = 'partial'
                status_label = f"⏳ Acompte ({bonus_earned:.2f}/{bonus_potential:.2f} DH)"
                status_badge = "chip-blue"
                is_confirmed = True
            else:
                status_key = 'pending_payment'
                status_label = "⏳ En attente règlement"
                status_badge = "chip-amber"
                is_confirmed = False

    return {
        'enrollment': enrollment,
        'rate': rate,
        'rate_str': rate_str,
        'is_mriliass': is_mriliass,
        'is_new_student': is_new_student,
        'reg_fee': reg_fee,
        'tuition_theoretical': tuition_theoretical,
        'paid_tuition': paid_tuition,
        'total_paid': total_paid,
        'due_total': due_total,
        'teacher_name': teacher_name,
        'teacher_share_full': teacher_share_full,
        'teacher_share_paid': teacher_share_paid,
        'teacher_rate_str': teacher_rate_str,
        'school_net_full': school_net_full,
        'school_net_paid': school_net_paid,
        'bonus_earned': bonus_earned,
        'bonus_potential': bonus_potential,
        'bonus_remaining': bonus_remaining,
        'bonus_amount': bonus_earned,
        'is_pending_group': is_pending_group,
        'is_confirmed': is_confirmed,
        'status_key': status_key,
        'status_label': status_label,
        'status_badge': status_badge,
        'tuition_amount': tuition_theoretical,
        'teacher_share': teacher_share_paid,
        'school_net': school_net_paid,
    }


# ---------------------------------------------------------------------------
# Payment Aggregation Helper
# ---------------------------------------------------------------------------
class GroupedPaymentView:
    """Wrapper that aggregates split payments sharing the same receipt number into a single receipt view."""
    def __init__(self, primary_payment, all_payments_in_group):
        self._primary = primary_payment
        self.payments = all_payments_in_group
        self.id = primary_payment.id
        self.receipt = primary_payment.receipt or f"REC-{primary_payment.id}"
        self.date = primary_payment.date
        self.method = primary_payment.method
        self.student = primary_payment.student
        self.student_id = primary_payment.student_id
        self.creator = primary_payment.creator
        self.recorded_by = primary_payment.recorded_by
        self.invoice = primary_payment.invoice
        self.invoice_id = primary_payment.invoice_id
        self.amount = sum(pay.amount for pay in all_payments_in_group)

        # Build raw and shortened course items
        raw_items = []
        short_items = []

        if self.invoice and self.invoice.items:
            for item in self.invoice.items:
                raw_desc = (item.description or "").strip()
                if raw_desc and raw_desc not in raw_items:
                    raw_items.append(raw_desc)
                clean_p = raw_desc.replace('(Scolarité)', '').replace('(Scolarité (3 mois))', '').strip()
                s_name = smart_shorten_course_name(clean_p)
                if 'frais d\'inscription' in raw_desc.lower() and not s_name.startswith('Inscription'):
                    s_name = f"Inscription ({s_name})"
                if s_name and s_name not in short_items:
                    short_items.append(s_name)
        else:
            for pay in all_payments_in_group:
                d = pay.courses_description
                if d:
                    for chunk in d.split(','):
                        c_clean = chunk.strip()
                        if c_clean and c_clean not in raw_items:
                            raw_items.append(c_clean)
                        clean_p = c_clean.replace('(Scolarité)', '').replace('(Scolarité (3 mois))', '').strip()
                        s_name = smart_shorten_course_name(clean_p)
                        if 'frais d\'inscription' in c_clean.lower() and not s_name.startswith('Inscription'):
                            s_name = f"Inscription ({s_name})"
                        if s_name and s_name not in short_items:
                            short_items.append(s_name)

        if not short_items and primary_payment.courses_description:
            for chunk in primary_payment.courses_description.split(','):
                c_clean = chunk.strip()
                if c_clean and c_clean not in raw_items:
                    raw_items.append(c_clean)
                clean_p = c_clean.replace('(Scolarité)', '').replace('(Scolarité (3 mois))', '').strip()
                s_name = smart_shorten_course_name(clean_p)
                if 'frais d\'inscription' in c_clean.lower() and not s_name.startswith('Inscription'):
                    s_name = f"Inscription ({s_name})"
                if s_name and s_name not in short_items:
                    short_items.append(s_name)

        self.courses_raw_list = raw_items
        self.courses_list = short_items if short_items else raw_items
        self.courses_description_full = ", ".join(raw_items) if raw_items else (primary_payment.courses_description or "")
        self.courses_description = ", ".join(short_items) if short_items else self.courses_description_full

        # Build note
        notes = []
        for pay in all_payments_in_group:
            if pay.note:
                n_str = pay.note.strip()
                if n_str and n_str not in notes:
                    notes.append(n_str)
        self.note = " | ".join(notes) if notes else (primary_payment.note or "")

        # Clean display note: filter out notes that merely duplicate raw course names
        clean_notes = []
        for n in notes:
            if n != self.courses_description_full and n != self.courses_description:
                if "Paiement renouvellement groupé" in n:
                    clean_notes.append("Renouvellement groupé")
                elif "Renouvellement" in n and len(n) > 40:
                    clean_notes.append("Renouvellement")
                elif len(n) > 100:
                    clean_notes.append(n[:97] + "...")
                else:
                    clean_notes.append(n)
        self.clean_note = " | ".join(clean_notes) if clean_notes else ""

    def __getattr__(self, item):
        return getattr(self._primary, item)


def group_payments_by_receipt(payment_list):
    """Groups payments sharing the same receipt number into a single aggregated item."""
    if not payment_list:
        return []
    order = []
    seen = {}
    for p in payment_list:
        key = p.receipt.strip() if (p.receipt and p.receipt.strip()) else f"__NO_REC_{p.id}"
        if key in seen:
            seen[key].append(p)
        else:
            seen[key] = [p]
            order.append(key)

    return [GroupedPaymentView(seen[k][0], seen[k]) for k in order]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    u = current_user()
    role = u.role if u else 'admin'
    today_dt = date.today()
    month_start = today_dt.replace(day=1)

    # ---------------------------------------------------------
    # 1. TEACHER: Redirect to Attendance (Do not show dashboard)
    # ---------------------------------------------------------
    if role == 'teacher':
        return redirect(url_for('attendance'))

    # ---------------------------------------------------------
    # 2. ADMIN & SECRETARY BASE STATS
    # ---------------------------------------------------------
    stats = {
        'students': Student.query.count(),
        'active_students': Student.query.filter_by(status='active').count(),
        'courses': Course.query.filter_by(active=True).count(),
        'teachers': Teacher.query.filter_by(active=True).count(),
        'enrollments': Enrollment.query.filter_by(status='active').count(),
        'outstanding': 0,
        'today_present': 0,
    }
    stats['active_students_pct'] = round((stats['active_students'] / stats['students'] * 100) if stats['students'] else 0, 1)

    # chiffre à recouvrer (balances d'inscriptions actives)
    bal = 0
    for e in Enrollment.query.filter_by(status='active').all():
        bal += e.balance
    stats['outstanding'] = bal

    lang_courses = Course.query.filter_by(category='language', active=True).count()
    tut_courses = Course.query.filter_by(category='tutoring', active=True).count()

    attend_today = Attendance.query.filter_by(date=today_dt).count()
    absent_today = Attendance.query.filter_by(date=today_dt, status='absent').count()
    low_stock_books = Book.query.filter_by(active=True).filter(Book.stock_quantity <= Book.min_stock_alert).all()

    handover_notes = []
    try:
        all_pending = StaffNote.query.filter_by(status='pending').order_by(StaffNote.is_pinned.desc(), StaffNote.created_at.desc()).all()
        handover_notes = [n for n in all_pending if n.is_visible_to(u)][:4]
    except Exception:
        handover_notes = []

    active_teachers = Teacher.query.filter_by(active=True).order_by(Teacher.first_name, Teacher.last_name).all()

    # Classes sans prof actives ayant au moins 1 élève inscrit
    classes_sans_prof = Course.query.filter(
        Course.active == True,
        (Course.teacher_id == None) | (Course.teacher_id == 0)
    ).all()
    upcoming_classes_alerts = []
    for c in classes_sans_prof:
        cnt = c.enrolled_count
        if cnt >= 1:
            ens = Enrollment.query.filter(
                Enrollment.course_id == c.id,
                Enrollment.status.in_(['active', 'trial'])
            ).all()
            students_list = [e.student for e in ens if e.student and e.is_attendance_eligible()]
            needed = max(0, 4 - cnt)
            upcoming_classes_alerts.append({
                'course': c,
                'enrolled_count': cnt,
                'needed': needed,
                'is_ready': cnt >= 4,
                'students': students_list
            })
    upcoming_classes_alerts.sort(key=lambda x: (not x['is_ready'], -x['enrolled_count'], x['course'].name))
    stats['upcoming_classes_count'] = len(upcoming_classes_alerts)
    stats['urgent_classes_count'] = sum(1 for a in upcoming_classes_alerts if a['is_ready'])

    # ---------------------------------------------------------
    # 3. SECRETARY SPECIFIC STATS (HER CASH TOTALS & HER ACTIONS)
    # ---------------------------------------------------------
    if role == 'secretary':
        sec_cash_today = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).filter(
            Payment.recorded_by == u.id, Payment.date == today_dt, Payment.method == 'cash'
        ).scalar() or 0.0
        sec_bank_today = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).filter(
            Payment.recorded_by == u.id, Payment.date == today_dt, Payment.method.in_(['transfer', 'card', 'online'])
        ).scalar() or 0.0
        sec_books_today = db.session.query(db.func.coalesce(db.func.sum(BookSale.total_amount), 0)).filter(
            BookSale.recorded_by == u.id, BookSale.sale_date == today_dt
        ).scalar() or 0.0

        sec_payments_month = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).filter(
            Payment.recorded_by == u.id, Payment.date >= month_start
        ).scalar() or 0.0
        sec_books_month = db.session.query(db.func.coalesce(db.func.sum(BookSale.total_amount), 0)).filter(
            BookSale.recorded_by == u.id, BookSale.sale_date >= month_start
        ).scalar() or 0.0

        stats['revenue_today'] = sec_cash_today + sec_bank_today + sec_books_today
        stats['revenue_month'] = sec_payments_month + sec_books_month
        stats['sec_cash_today'] = sec_cash_today
        stats['sec_bank_today'] = sec_bank_today
        stats['sec_books_today'] = sec_books_today

        # Inscription Bonuses for the current month
        sec_month_enrolls = Enrollment.query.filter(
            Enrollment.created_by == u.id,
            db.or_(
                Enrollment.enroll_date >= month_start,
                db.func.date(Enrollment.created_at) >= month_start
            )
        ).all()
        sec_bonuses = [calculate_enrollment_secretary_bonus(e, u.commission_rate, user=u) for e in sec_month_enrolls]
        new_st_bonuses = [b for b in sec_bonuses if b['is_new_student']]
        stats['sec_bonus_month'] = round(sum(b['bonus_earned'] for b in new_st_bonuses if b['is_confirmed']), 2)
        stats['sec_bonus_remaining'] = round(sum(b['bonus_remaining'] for b in new_st_bonuses if not b['is_confirmed'] and not b['is_pending_group']), 2)
        stats['sec_bonus_pending'] = round(sum(b['bonus_potential'] for b in new_st_bonuses if b['is_pending_group']), 2)
        stats['sec_bonus_count_confirmed'] = sum(1 for b in new_st_bonuses if b['is_confirmed'])
        stats['sec_bonus_count_pending'] = sum(1 for b in new_st_bonuses if b['is_pending_group'])
        stats['sec_renewals_count'] = sum(1 for b in sec_bonuses if not b['is_new_student'])
        stats['sec_commission_rate'] = u.commission_rate or 0.0
        stats['is_fixed_commission'] = False

        recent_payments_raw = Payment.query.filter_by(recorded_by=u.id).order_by(Payment.date.desc(), Payment.id.desc()).limit(16).all()
        recent_payments = group_payments_by_receipt(recent_payments_raw)[:8]
        recent_enrolls = Enrollment.query.filter_by(status='active', created_by=u.id).order_by(Enrollment.created_at.desc(), Enrollment.id.desc()).limit(8).all()
        pending_enrolls = Enrollment.query.filter_by(status='pending_assignment').order_by(Enrollment.created_at.desc()).all()
        stats['pending_enrollments'] = len(pending_enrolls)
        trial_enrolls = Enrollment.query.filter_by(status='trial').all()
        stats['trial_enrollments'] = len(trial_enrolls)
        stats['trial_decision_needed'] = sum(1 for te in trial_enrolls if te.trial_completed)
        due_invoices = Invoice.query.filter(Invoice.status == 'unpaid').order_by(Invoice.due_date.asc()).limit(6).all()

        return render_template('dashboard.html', stats=stats,
                               lang_courses=lang_courses, tut_courses=tut_courses,
                               months=[], rev=[],
                               recent_payments=recent_payments,
                               recent_enrolls=recent_enrolls,
                               pending_enrolls=pending_enrolls,
                               due_invoices=due_invoices,
                               attend_today=attend_today,
                               absent_today=absent_today,
                               low_stock_books=low_stock_books,
                               handover_notes=handover_notes,
                               last_backup_name=None,
                               active_teachers=active_teachers,
                               upcoming_classes_alerts=upcoming_classes_alerts,
                               today=today_dt)

    # ---------------------------------------------------------
    # 4. ADMIN DASHBOARD (GLOBAL MACRO FINANCIAL METRICS & FIXED CHARGES)
    # ---------------------------------------------------------
    cur_y, cur_m = today_dt.year, today_dt.month
    req_month_cur = f"{cur_y:04d}-{cur_m:02d}"

    rev_tuition_month = (db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))
                         .filter(Payment.date >= month_start).scalar() or 0.0)
    
    # Book sales: separate physical cash collected from institute net revenue (exclude teacher share)
    month_book_sales = BookSale.query.filter(BookSale.sale_date >= month_start).all()
    gross_books_month = round(sum((b.total_amount or 0.0) for b in month_book_sales), 2)
    teacher_books_due_month = round(sum((b.teacher_earned or 0.0) for b in month_book_sales), 2)
    rev_books_month = round(sum(
        ((b.school_earned if b.teacher_id is not None else b.total_amount) or 0.0)
        for b in month_book_sales
    ), 2)
    total_rev_month = round(rev_tuition_month + rev_books_month, 2)

    stats['revenue'] = (db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).scalar() or 0) + (db.session.query(db.func.coalesce(db.func.sum(BookSale.school_earned), 0)).scalar() or 0)
    stats['revenue_month'] = total_rev_month
    stats['rev_tuition_month'] = rev_tuition_month
    stats['rev_books_month'] = rev_books_month
    stats['revenue_today'] = (db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))
                              .filter(Payment.date == today_dt).scalar() or 0)

    actual_expenses_month = (db.session.query(db.func.coalesce(db.func.sum(Expense.amount), 0))
                             .filter(Expense.date >= month_start).scalar() or 0.0)
    stats['expenses_month'] = actual_expenses_month
    stats['net_profit_month'] = round(total_rev_month - actual_expenses_month, 2)

    # Recurring Charges Tracking for Current Month
    all_rcs = RecurringCharge.query.filter_by(active=True).all()
    total_rc_monthly = sum((r.amount or 0.0) for r in all_rcs)

    gen_rc_expenses = Expense.query.filter(
        Expense.recurring_charge_id.isnot(None)
    ).filter(
        db.or_(
            Expense.recurring_month == req_month_cur,
            db.and_(db.extract('year', Expense.date) == cur_y, db.extract('month', Expense.date) == cur_m)
        )
    ).all()
    gen_rc_ids = set(e.recurring_charge_id for e in gen_rc_expenses if e.recurring_charge_id)

    validated_rc_count = len([r for r in all_rcs if r.id in gen_rc_ids])
    validated_rc_amount = sum((e.amount or 0.0) for e in gen_rc_expenses)
    pending_rc_list = [r for r in all_rcs if r.id not in gen_rc_ids]
    pending_rc_count = len(pending_rc_list)
    pending_rc_amount = sum((r.amount or 0.0) for r in pending_rc_list)

    # Teachers payroll for current month
    start_d_cur = date(cur_y, cur_m, 1)
    _, last_day_cur = calendar.monthrange(cur_y, cur_m)
    end_d_cur = date(cur_y, cur_m, last_day_cur)
    _, grand_teacher_payroll_cur = _calculate_period_teacher_payroll(start_d_cur, end_d_cur)
    t_payouts_cur = TeacherSalaryPayout.query.filter_by(period_month=req_month_cur, status='paid').all()
    t_paid_cur = sum((p.net_amount or 0.0) for p in t_payouts_cur)
    pending_teacher_payroll = max(0.0, round(grand_teacher_payroll_cur - t_paid_cur, 2))

    # Pending supplier debts for non-fixed expenses in this month
    cur_month_exps = Expense.query.filter(
        db.extract('year', Expense.date) == cur_y,
        db.extract('month', Expense.date) == cur_m
    ).all()
    pending_supplier_debts = round(sum((e.remaining_balance or 0.0) for e in cur_month_exps if e.status in ['unpaid', 'partial']), 2)

    # Total of all pending charges to be paid (Fixed + Teachers Payroll + Non-fixed debts)
    total_pending_all_charges = round(pending_rc_amount + pending_teacher_payroll + pending_supplier_debts, 2)
    total_month_all_charges = round(actual_expenses_month + total_pending_all_charges, 2)

    # Projected Net Profit after deducting ALL charges (Fixed, Teachers, Non-fixed)
    theoretical_cash = total_rev_month - actual_expenses_month
    real_cash_val = SH.get_setting(f"real_cash_amount_{req_month_cur}", "")
    real_cash_amount = float(real_cash_val) if real_cash_val not in ['', None] else None
    real_cash_note = SH.get_setting(f"real_cash_note_{req_month_cur}", "")
    real_cash_date = SH.get_setting(f"real_cash_date_{req_month_cur}", "")

    if real_cash_amount is not None:
        effective_cash = real_cash_amount
        ecart_caisse = round(theoretical_cash - real_cash_amount, 2)
        projected_net_profit = round(effective_cash - total_pending_all_charges, 2)
        is_real_cash_used = True
    else:
        effective_cash = theoretical_cash
        ecart_caisse = 0.0
        projected_net_profit = round(theoretical_cash - total_pending_all_charges, 2)
        is_real_cash_used = False

    coverage_pct = round((total_rev_month / total_month_all_charges * 100), 1) if total_month_all_charges > 0 else 100.0

    rc_by_cat = {}
    for r in all_rcs:
        rc_by_cat[r.category] = rc_by_cat.get(r.category, 0.0) + (r.amount or 0.0)

    months_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    month_name_fr = f"{months_fr[cur_m]} {cur_y}" if (1 <= cur_m <= 12) else req_month_cur

    financial_overview = {
        'month_name_fr': month_name_fr,
        'req_month': req_month_cur,
        'revenue_month': total_rev_month,
        'rev_tuition_month': rev_tuition_month,
        'rev_books_month': rev_books_month,
        'gross_books_month': gross_books_month,
        'teacher_books_due_month': teacher_books_due_month,
        'actual_expenses_month': actual_expenses_month,
        'current_net_profit': stats['net_profit_month'],
        'theoretical_cash': theoretical_cash,
        'real_cash_amount': real_cash_amount,
        'real_cash_note': real_cash_note,
        'real_cash_date': real_cash_date,
        'effective_cash': effective_cash,
        'ecart_caisse': ecart_caisse,
        'is_real_cash_used': is_real_cash_used,
        'total_rc_monthly': total_rc_monthly,
        'validated_rc_count': validated_rc_count,
        'validated_rc_amount': validated_rc_amount,
        'pending_rc_count': pending_rc_count,
        'pending_rc_amount': pending_rc_amount,
        'pending_rc_list': pending_rc_list,
        'grand_teacher_payroll': grand_teacher_payroll_cur,
        'paid_teacher_payroll': t_paid_cur,
        'pending_teacher_payroll': pending_teacher_payroll,
        'pending_supplier_debts': pending_supplier_debts,
        'total_pending_all_charges': total_pending_all_charges,
        'total_month_all_charges': total_month_all_charges,
        'projected_net_profit': projected_net_profit,
        'coverage_pct': coverage_pct,
        'total_projected_charges': total_month_all_charges,
        'rc_by_cat': sorted(rc_by_cat.items(), key=lambda x: x[1], reverse=True),
        'all_rcs': all_rcs
    }

    months = []
    rev = []
    for i in range(5, -1, -1):
        first = (date.today().replace(day=1) - timedelta(days=i * 31)).replace(day=1)
        last = (first + timedelta(days=32)).replace(day=1)
        total = (db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))
                 .filter(Payment.date >= first, Payment.date < last).scalar() or 0)
        months.append(first.strftime('%b'))
        rev.append(float(total))

    recent_payments_raw = (Payment.query.order_by(Payment.date.desc(), Payment.id.desc()).limit(16).all())
    recent_payments = group_payments_by_receipt(recent_payments_raw)[:8]
    recent_enrolls = (Enrollment.query.filter_by(status='active').order_by(Enrollment.created_at.desc(), Enrollment.id.desc()).limit(8).all())
    pending_enrolls = (Enrollment.query.filter_by(status='pending_assignment').order_by(Enrollment.created_at.desc()).all())
    stats['pending_enrollments'] = len(pending_enrolls)
    trial_enrolls = Enrollment.query.filter_by(status='trial').all()
    stats['trial_enrollments'] = len(trial_enrolls)
    stats['trial_decision_needed'] = sum(1 for te in trial_enrolls if te.trial_completed)
    due_invoices = Invoice.query.filter(Invoice.status == 'unpaid').order_by(Invoice.due_date.asc()).limit(6).all()

    # ---------------------------------------------------------
    # Collaborator Inscription Bonuses for @mriliass (Admin)
    # ---------------------------------------------------------
    if u and u.username and u.username.lower() == 'mriliass':
        sec_month_enrolls = Enrollment.query.filter(
            Enrollment.created_by == u.id,
            db.or_(
                Enrollment.enroll_date >= month_start,
                db.func.date(Enrollment.created_at) >= month_start
            )
        ).all()
        sec_bonuses = [calculate_enrollment_secretary_bonus(e, user=u) for e in sec_month_enrolls]
        new_st_bonuses = [b for b in sec_bonuses if b['is_new_student']]
        stats['sec_bonus_month'] = round(sum(b['bonus_earned'] for b in new_st_bonuses if b['is_confirmed']), 2)
        stats['sec_bonus_remaining'] = round(sum(b['bonus_remaining'] for b in new_st_bonuses if not b['is_confirmed'] and not b['is_pending_group']), 2)
        stats['sec_bonus_pending'] = round(sum(b['bonus_potential'] for b in new_st_bonuses if b['is_pending_group']), 2)
        stats['sec_bonus_count_confirmed'] = sum(1 for b in new_st_bonuses if b['is_confirmed'])
        stats['sec_bonus_count_pending'] = sum(1 for b in new_st_bonuses if b['is_pending_group'])
        stats['sec_renewals_count'] = sum(1 for b in sec_bonuses if not b['is_new_student'])
        stats['sec_commission_rate'] = 0.0
        stats['is_fixed_commission'] = True
    last_backup_name = None
    try:
        if os.path.exists(BACKUPS_DIR):
            bk_list = sorted([f for f in os.listdir(BACKUPS_DIR) if f.endswith('.zip') or f.endswith('.db')], reverse=True)
            if bk_list:
                last_backup_name = bk_list[0]
    except Exception:
        pass

    return render_template('dashboard.html', stats=stats,
                           financial_overview=financial_overview,
                           lang_courses=lang_courses, tut_courses=tut_courses,
                           months=months, rev=rev,
                           recent_payments=recent_payments,
                           recent_enrolls=recent_enrolls,
                           pending_enrolls=pending_enrolls,
                           due_invoices=due_invoices,
                           attend_today=attend_today,
                           absent_today=absent_today,
                           low_stock_books=low_stock_books,
                           handover_notes=handover_notes,
                           last_backup_name=last_backup_name,
                           active_teachers=active_teachers,
                           upcoming_classes_alerts=upcoming_classes_alerts,
                           today=today_dt)


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------
@app.route('/students')
@login_required
@role_required('admin', 'secretary')
def students():
    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    level_filter = request.args.get('level', '').strip()
    exp_filter = request.args.get('expiration', '').strip()
    end_date_filter = request.args.get('end_date', '').strip()

    u = current_user()
    cur_t = None
    teacher_sids = None
    if u and u.role == 'teacher':
        cur_t = get_current_teacher()
        teacher_sids = get_teacher_student_ids(cur_t.id) if cur_t else []

    query = Student.query
    if teacher_sids is not None:
        if teacher_sids:
            query = query.filter(Student.id.in_(teacher_sids))
        else:
            query = query.filter(Student.id == -1)

    if q:
        stu_filter = build_student_search_filter(q, Student)
        if stu_filter is not None:
            query = query.filter(stu_filter)

    if status_filter:
        query = query.filter_by(status=status_filter)

    if level_filter:
        query = query.filter(Student.school_level.ilike(f"%{level_filter}%"))

    all_students = query.order_by(Student.id.desc()).all()

    # High-performance batch pre-loading for students
    pay_sums = dict(db.session.query(Payment.enrollment_id, db.func.sum(Payment.amount))
                    .filter(Payment.enrollment_id.isnot(None))
                    .group_by(Payment.enrollment_id).all())
    student_pay_sums = dict(db.session.query(Payment.student_id, db.func.sum(Payment.amount))
                            .filter(Payment.student_id.isnot(None))
                            .group_by(Payment.student_id).all())
    all_non_dropped = db.session.query(Enrollment.student_id, Enrollment.calculated_price, Enrollment.monthly_price)\
                        .filter(Enrollment.status != 'dropped').all()
    student_dues = {}
    for sid, calc_p, m_p in all_non_dropped:
        student_dues[sid] = student_dues.get(sid, 0.0) + (calc_p or m_p or 0.0)

    active_enrolls = Enrollment.query.filter_by(status='active').options(
        joinedload(Enrollment.course)
    ).all()
    student_active_enrolls = {}
    for ae in active_enrolls:
        ae._total_paid_cache = float(pay_sums.get(ae.id, 0.0))
        student_active_enrolls.setdefault(ae.student_id, []).append(ae)

    today_val = date.today()
    for s in all_students:
        s_pay = float(student_pay_sums.get(s.id, 0.0))
        s_due = float(student_dues.get(s.id, 0.0))
        excess = max(0.0, s_pay - s_due)
        s._credit_balance_cache = round(excess + (s.credit_balance or 0.0), 2)

        s_ens = student_active_enrolls.get(s.id, [])
        dates = [e.end_date for e in s_ens if e.end_date]
        s._end_date_cache = max(dates) if dates else None
        ed = s._end_date_cache
        s._days_remaining_cache = (ed - today_val).days if ed else 0

    # In-memory filter for expiration or specific end date if requested
    if end_date_filter:
        parsed_ed = parse_date(end_date_filter)
        if parsed_ed:
            students_list = [s for s in all_students if s.end_date == parsed_ed]
        else:
            students_list = all_students
    elif exp_filter == 'expiring':
        students_list = [s for s in all_students if s.end_date and s.days_remaining is not None and 0 <= s.days_remaining <= 5]
    elif exp_filter == 'expired':
        students_list = [s for s in all_students if s.end_date and s.days_remaining is not None and s.days_remaining < 0]
    else:
        students_list = all_students

    # KPIs
    if teacher_sids is not None:
        base_teacher_students = Student.query.filter(Student.id.in_(teacher_sids)).all() if teacher_sids else []
        total_count = len(base_teacher_students)
        active_count = sum(1 for s in base_teacher_students if s.status == 'active')
        expiring_count = sum(1 for s in base_teacher_students if s.status == 'active' and s.end_date and s.days_remaining is not None and s.days_remaining <= 5)
        total_credits = 0.0
        levels = sorted(list(set(s.school_level for s in base_teacher_students if s.school_level and s.school_level.strip())))
    else:
        total_count = Student.query.count()
        active_count = Student.query.filter_by(status='active').count()
        all_active_stu = Student.query.filter_by(status='active').all()
        expiring_count = sum(1 for s in all_active_stu if s.end_date and s.days_remaining is not None and s.days_remaining <= 5)
        total_credits = sum(s.dynamic_credit_balance for s in all_active_stu if s.dynamic_credit_balance > 0)
        levels_raw = db.session.query(Student.school_level).distinct().filter(Student.school_level != None).all()
        levels = sorted([l[0] for l in levels_raw if l[0] and l[0].strip()])

    return render_template('students/list.html',
                           students=students_list,
                           q=q,
                           status_filter=status_filter,
                           level_filter=level_filter,
                           exp_filter=exp_filter,
                           end_date_filter=end_date_filter,
                           levels=levels,
                           total_count=total_count,
                           active_count=active_count,
                           expiring_count=expiring_count,
                           total_credits=total_credits,
                           current_teacher=cur_t)


def _get_students_by_date_data():
    sync_student_renewed_enrollments(None)
    today_dt = date.today()
    target_date_str = request.args.get('date', '').strip()
    filter_mode = request.args.get('mode', 'today').strip()  # today, next_1, next_2, next_3, next_4, next_5, under_5, week, expired, all, exact
    reminder_filter = request.args.get('reminder', 'all').strip()  # all, pending, sent
    q = request.args.get('q', '').strip()
    course_id_str = request.args.get('course_id', '').strip()
    course_id = int(course_id_str) if course_id_str.isdigit() else None
    teacher_id_str = request.args.get('teacher_id', '').strip()
    teacher_id = int(teacher_id_str) if teacher_id_str.isdigit() else None

    # Determine target_date based on filter_mode or explicit date
    if filter_mode == 'next_1':
        target_date = today_dt + timedelta(days=1)
    elif filter_mode == 'next_2':
        target_date = today_dt + timedelta(days=2)
    elif filter_mode == 'next_3':
        target_date = today_dt + timedelta(days=3)
    elif filter_mode == 'next_4':
        target_date = today_dt + timedelta(days=4)
    elif filter_mode == 'next_5':
        target_date = today_dt + timedelta(days=5)
    elif filter_mode == 'today':
        target_date = today_dt
    elif filter_mode in ('under_5', 'expiring_soon', 'week', 'expired', 'all'):
        target_date = parse_date(target_date_str) or today_dt
    else:  # exact
        target_date = parse_date(target_date_str) or today_dt

    target_date_str = target_date.strftime('%Y-%m-%d')
    prev_date = target_date - timedelta(days=1)
    next_date = target_date + timedelta(days=1)

    u = current_user()
    cur_t = None
    teacher_course_ids = None
    if u and u.role == 'teacher':
        cur_t = get_current_teacher()
        if cur_t:
            teacher_course_ids = get_teacher_course_ids(cur_t.id)
        else:
            teacher_course_ids = []

    # Query enrollments that are active or paused (not dropped)
    query = Enrollment.query.filter(Enrollment.status != 'dropped')

    if teacher_course_ids is not None:
        if teacher_course_ids:
            query = query.filter(Enrollment.course_id.in_(teacher_course_ids))
        else:
            query = query.filter(Enrollment.id == -1)
    elif teacher_id:
        c_ids = get_teacher_course_ids(teacher_id)
        query = query.filter(Enrollment.course_id.in_(c_ids)) if c_ids else query.filter(Enrollment.id == -1)

    if course_id:
        query = query.filter(Enrollment.course_id == course_id)

    all_enrolls = query.order_by(Enrollment.id.desc()).all()

    # Pre-calculate counts across all enrolls for badges
    mode_counts = {
        'today': 0,
        'next_1': 0,
        'next_2': 0,
        'next_3': 0,
        'next_4': 0,
        'next_5': 0,
        'under_5': 0,
        'week': 0,
        'expired': 0,
        'all': len(all_enrolls),
        'pending': 0,
        'sent': 0
    }
    for e in all_enrolls:
        if not e.end_date:
            continue
        # Do not count completed or already-renewed enrollments in reminders/expiries
        if e.status == 'completed' or e.is_renewed:
            continue
        r = (e.end_date - today_dt).days
        if r == 0:
            mode_counts['today'] += 1
        elif r == 1:
            mode_counts['next_1'] += 1
        elif r == 2:
            mode_counts['next_2'] += 1
        elif r == 3:
            mode_counts['next_3'] += 1
        elif r == 4:
            mode_counts['next_4'] += 1
        elif r == 5:
            mode_counts['next_5'] += 1

        if 0 <= r <= 5:
            mode_counts['under_5'] += 1
        if 0 <= r <= 6:
            mode_counts['week'] += 1
        if r < 0:
            mode_counts['expired'] += 1

        if e.last_reminder_at is not None:
            mode_counts['sent'] += 1
        else:
            mode_counts['pending'] += 1

    # Filter based on end_date and filter_mode
    filtered_items = []
    for e in all_enrolls:
        ed = e.end_date
        if not ed:
            continue

        rem = (ed - today_dt).days
        match = False
        if filter_mode == 'today':
            match = (rem == 0)
        elif filter_mode == 'next_1':
            match = (rem == 1)
        elif filter_mode == 'next_2':
            match = (rem == 2)
        elif filter_mode == 'next_3':
            match = (rem == 3)
        elif filter_mode == 'next_4':
            match = (rem == 4)
        elif filter_mode == 'next_5':
            match = (rem == 5)
        elif filter_mode in ('under_5', 'expiring_soon'):
            match = (0 <= rem <= 5)
        elif filter_mode == 'week':
            match = (0 <= rem <= 6)
        elif filter_mode == 'expired':
            match = (rem < 0)
        elif filter_mode == 'all':
            match = True
        elif filter_mode == 'exact':
            match = (ed == target_date)
        else:
            match = (ed == target_date)

        if match:
            # Check reminder filter
            if reminder_filter == 'pending' and e.last_reminder_at is not None:
                continue
            elif reminder_filter == 'sent' and e.last_reminder_at is None:
                continue

            s = e.student
            if not s:
                continue
            if q:
                q_clean = " ".join(q.split()).lower()
                tokens = q_clean.split()
                full_s1 = f"{s.first_name or ''} {s.last_name or ''}".lower()
                full_s2 = f"{s.last_name or ''} {s.first_name or ''}".lower()
                name_match = (
                    (q_clean in full_s1) or (q_clean in full_s2) or
                    (tokens and all(t in full_s1 for t in tokens))
                )
                code_match = bool(s.code and q_clean in s.code.lower())
                phone_match = bool((s.phone and q_clean in s.phone.lower()) or (s.parent_phone and q_clean in s.parent_phone.lower()))
                course_match = bool(e.course and (q_clean in (e.course.name or '').lower() or q_clean in (e.course.group_name or '').lower()))
                if not (name_match or code_match or phone_match or course_match):
                    continue
            filtered_items.append(e)

    # Sort items: by end_date asc, course name, student name
    filtered_items.sort(key=lambda x: (x.end_date or date.min, x.course.display_name if x.course else '', x.student.full_name if x.student else ''))

    # KPIs
    total_count = len(filtered_items)
    unique_students = len(set(e.student_id for e in filtered_items if e.student_id))
    unique_courses = len(set(e.course_id for e in filtered_items if e.course_id))
    sum_due = sum(e.due_amount for e in filtered_items if not (e.is_renewed or e.status == 'completed'))
    sum_paid = sum(e.total_paid for e in filtered_items if not (e.is_renewed or e.status == 'completed'))
    sum_balance = sum(e.balance for e in filtered_items if not (e.is_renewed or e.status == 'completed'))
    with_phone_count = sum(1 for e in filtered_items if e.student and (e.student.phone or e.student.parent_phone))

    all_courses = Course.query.filter_by(active=True).order_by(Course.name).all()
    all_teachers = Teacher.query.filter_by(active=True).order_by(Teacher.last_name).all()

    day_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    day_names_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    month_names_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    month_names_ar = ['', 'يناير', 'فبراير', 'مارس', 'أبريل', 'ماي', 'يونيو', 'يوليوز', 'غشت', 'شتنبر', 'أكتوبر', 'نونبر', 'دجنبر']

    dow_idx = target_date.weekday()
    formatted_date_fr = f"{day_names_fr[dow_idx]} {target_date.day} {month_names_fr[target_date.month]} {target_date.year}"
    formatted_date_ar = f"{day_names_ar[dow_idx]} {target_date.day} {month_names_ar[target_date.month]} {target_date.year}"

    if filter_mode == 'today':
        target_date_fr = f"Aujourd'hui ({formatted_date_fr})"
        target_date_ar = f"اليوم ({formatted_date_ar})"
    elif filter_mode == 'next_1':
        target_date_fr = f"Demain (+1j) ({formatted_date_fr})"
        target_date_ar = f"غداً (+1 يوم) ({formatted_date_ar})"
    elif filter_mode == 'next_2':
        target_date_fr = f"+2 jours ({formatted_date_fr})"
        target_date_ar = f"بعد يومين ({formatted_date_ar})"
    elif filter_mode == 'next_3':
        target_date_fr = f"+3 jours ({formatted_date_fr})"
        target_date_ar = f"بعد 3 أيام ({formatted_date_ar})"
    elif filter_mode == 'next_4':
        target_date_fr = f"+4 jours ({formatted_date_fr})"
        target_date_ar = f"بعد 4 أيام ({formatted_date_ar})"
    elif filter_mode == 'next_5':
        target_date_fr = f"+5 jours ({formatted_date_fr})"
        target_date_ar = f"بعد 5 أيام ({formatted_date_ar})"
    elif filter_mode in ('under_5', 'expiring_soon'):
        target_date_fr = f"Sous 5 jours (0 à 5j)"
        target_date_ar = f"خلال 5 أيام القادمة (0 إلى 5 أيام)"
    elif filter_mode == 'week':
        target_date_fr = f"7 jours à venir (0 à 6j)"
        target_date_ar = f"خلال 7 أيام القادمة"
    elif filter_mode == 'expired':
        target_date_fr = f"Abonnements Expirés (En retard)"
        target_date_ar = f"الاشتراكات المنتهية (متأخرات)"
    elif filter_mode == 'all':
        target_date_fr = f"Tous les abonnements actifs"
        target_date_ar = f"جميع الاشتراكات النشطة"
    else:
        target_date_fr = formatted_date_fr
        target_date_ar = formatted_date_ar

    return {
        'enrollments': filtered_items,
        'target_date': target_date,
        'target_date_str': target_date_str,
        'prev_date_str': prev_date.strftime('%Y-%m-%d'),
        'next_date_str': next_date.strftime('%Y-%m-%d'),
        'today_date_str': today_dt.strftime('%Y-%m-%d'),
        'target_date_fr': target_date_fr,
        'target_date_ar': target_date_ar,
        'filter_mode': filter_mode,
        'reminder_filter': reminder_filter,
        'mode_counts': mode_counts,
        'q': q,
        'course_id': course_id,
        'teacher_id': teacher_id,
        'all_courses': all_courses,
        'all_teachers': all_teachers,
        'total_count': total_count,
        'unique_students': unique_students,
        'unique_courses': unique_courses,
        'sum_due': sum_due,
        'sum_paid': sum_paid,
        'sum_balance': sum_balance,
        'with_phone_count': with_phone_count,
        'current_teacher': cur_t,
        'today_dt': today_dt
    }



@app.route('/students/by-date')
@login_required
@role_required('admin', 'secretary')
def students_by_date():
    data = _get_students_by_date_data()
    return render_template('students/by_date.html', **data)


@app.route('/students/by-date/print')
@login_required
@role_required('admin', 'secretary')
def students_by_date_print():
    data = _get_students_by_date_data()
    return render_template('students/by_date_print.html', **data)


@app.route('/api/enrollments/<int:eid>/update-end-date', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def api_enrollment_update_end_date(eid):
    e = Enrollment.query.get_or_404(eid)
    new_end_date = parse_date(request.form.get('new_end_date'))
    if not new_end_date:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Date de fin invalide'}), 400
        flash('Date de fin invalide', 'danger')
        return redirect(request.referrer or url_for('students_by_date'))

    note = request.form.get('note', '').strip()
    old_end = e.end_date
    e.custom_end_date = new_end_date
    old_end_str = old_end.strftime('%d/%m/%Y') if old_end else '—'
    new_end_str = new_end_date.strftime('%d/%m/%Y')
    if note:
        e.notes = f"{e.notes or ''}\n[Date fin modifiée le {date.today().strftime('%d/%m/%Y')} : {old_end_str} -> {new_end_str} | {note}]".strip()
    db.session.commit()

    stu_name = e.student.full_name if e.student else 'Élève'
    log_action('enrollment_end_date_update', f"Enrollment {e.id} ({stu_name}): date fin modifiée de {old_end_str} à {new_end_str}. Note: {note}")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'message': f"Date de fin mise à jour avec succès au {new_end_str}",
            'new_end_date': new_end_str,
            'new_end_date_iso': new_end_date.strftime('%Y-%m-%d')
        })

    flash(f"Date de fin pour {stu_name} ajustée avec succès au {new_end_str} !", 'success')
    return redirect(request.referrer or url_for('students_by_date', date=new_end_date.strftime('%Y-%m-%d')))


@app.route('/enrollments/mark_reminded', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def enrollments_mark_reminded():
    data = request.get_json(silent=True) or request.form
    eid = _int(data.get('enrollment_id'))
    eids = data.get('enrollment_ids')
    phone = (data.get('phone') or '').strip()

    now = datetime.utcnow()
    updated_ids = []
    last_label = ""
    lang = session.get('lang', 'fr')

    def _mark(enr):
        nonlocal last_label
        enr.last_reminder_at = now
        if phone:
            enr.last_reminder_phone = phone
        enr.reminder_count = (enr.reminder_count or 0) + 1
        updated_ids.append(enr.id)
        last_label = enr.reminder_status_label(lang)

    if eid:
        e = Enrollment.query.get(eid)
        if e:
            _mark(e)
    elif eids and isinstance(eids, list):
        for single_id in eids:
            e = Enrollment.query.get(_int(single_id))
            if e:
                _mark(e)

    db.session.commit()
    return jsonify({
        'success': True,
        'updated_count': len(updated_ids),
        'updated_ids': updated_ids,
        'last_reminder_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'reminder_status_label': last_label
    })


@app.route('/students/by-date/whatsapp_queue', methods=['GET'])
@login_required
@role_required('admin', 'secretary')
def students_by_date_whatsapp_queue():
    ids_param = request.args.get('ids', '').strip()
    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '')
    lang = session.get('lang', 'fr')

    if ids_param:
        ids_list = [_int(x) for x in ids_param.split(',') if _int(x)]
        enrollments = Enrollment.query.filter(Enrollment.id.in_(ids_list)).all()
    else:
        data = _get_students_by_date_data()
        enrollments = data.get('enrollments', [])

    results = []
    for e in enrollments:
        if e.is_renewed or e.status == 'completed':
            continue
        s = e.student
        c = e.course
        t = c.teacher if (c and c.teacher) else None

        raw_parent_phone = (s.parent_phone or '') if s else ''
        raw_student_phone = (s.phone or '') if s else ''
        clean_parent = _clean_wa_phone(raw_parent_phone)
        clean_student = _clean_wa_phone(raw_student_phone)

        is_adult = bool(s.is_adult) if s else False
        default_template = 'adult' if is_adult else 'parent'

        # Generate both parent and adult variations in Arabic & French
        msg_parent_ar = generate_spintax_payment_reminder(
            stu_name=s.full_name if s else '',
            course_name=c.display_name if c else '',
            end_date=e.end_date,
            days_remaining=e.days_remaining,
            balance=e.balance,
            due_amount=e.due_amount,
            lang='ar',
            recipient_type='parent',
            inst_name=inst_name,
            inst_phone=inst_phone,
            ref_seed=e.id
        )
        msg_parent_fr = generate_spintax_payment_reminder(
            stu_name=s.full_name if s else '',
            course_name=c.display_name if c else '',
            end_date=e.end_date,
            days_remaining=e.days_remaining,
            balance=e.balance,
            due_amount=e.due_amount,
            lang='fr',
            recipient_type='parent',
            inst_name=inst_name,
            inst_phone=inst_phone,
            ref_seed=e.id
        )
        msg_adult_ar = generate_spintax_payment_reminder(
            stu_name=s.full_name if s else '',
            course_name=c.display_name if c else '',
            end_date=e.end_date,
            days_remaining=e.days_remaining,
            balance=e.balance,
            due_amount=e.due_amount,
            lang='ar',
            recipient_type='adult',
            inst_name=inst_name,
            inst_phone=inst_phone,
            ref_seed=e.id
        )
        msg_adult_fr = generate_spintax_payment_reminder(
            stu_name=s.full_name if s else '',
            course_name=c.display_name if c else '',
            end_date=e.end_date,
            days_remaining=e.days_remaining,
            balance=e.balance,
            due_amount=e.due_amount,
            lang='fr',
            recipient_type='adult',
            inst_name=inst_name,
            inst_phone=inst_phone,
            ref_seed=e.id
        )

        # Default phone selection: for adult, student phone takes priority; for minor, parent phone takes priority
        if is_adult:
            def_target_phone = clean_student or clean_parent
        else:
            def_target_phone = clean_parent or clean_student

        results.append({
            'enrollment_id': e.id,
            'student_id': s.id if s else None,
            'student_name': s.full_name if s else 'Élève',
            'student_code': s.code if s else '',
            'student_photo': s.photo if (s and s.photo) else None,
            'course_name': c.display_name if c else 'Cours',
            'group_name': c.group_name if c else '',
            'teacher_name': t.full_name if t else '',
            'end_date': e.end_date.strftime('%d/%m/%Y') if e.end_date else '',
            'days_remaining': e.days_remaining,
            'due_amount': e.due_amount,
            'total_paid': e.total_paid,
            'balance': e.balance,
            'is_adult': is_adult,
            'student_age': s.age if s else None,
            'default_template': default_template,
            'raw_parent_phone': raw_parent_phone,
            'raw_student_phone': raw_student_phone,
            'clean_parent_phone': clean_parent,
            'clean_student_phone': clean_student,
            'target_phone': def_target_phone,
            'last_reminder_at': e.last_reminder_at.strftime('%d/%m/%Y %H:%M') if e.last_reminder_at else None,
            'reminder_status_label': e.reminder_status_label(lang),
            'reminder_count': e.reminder_count or 0,
            'msg_parent_ar': msg_parent_ar,
            'msg_parent_fr': msg_parent_fr,
            'msg_adult_ar': msg_adult_ar,
            'msg_adult_fr': msg_adult_fr,
            'msg_ar': msg_adult_ar if is_adult else msg_parent_ar,
            'msg_fr': msg_adult_fr if is_adult else msg_parent_fr
        })

    return jsonify({
        'success': True,
        'queue': results,
        'count': len(results)
    })



@app.route('/students/new', methods=['GET', 'POST'])

@app.route('/students/<int:sid>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def student_form(sid=None):
    stu = Student.query.get(sid) if sid else None
    if request.method == 'POST':
        data = request.form
        if stu is None:
            stu = Student(code=SH.gen_code('student_prefix', 'next_student_number'),
                          created_by=current_user().id if current_user() else None)
            db.session.add(stu)
        stu.first_name = (data.get('first_name') or '').strip()
        stu.last_name = (data.get('last_name') or '').strip()
        stu.gender = data.get('gender')
        stu.birth_date = parse_date(data.get('birth_date'))
        stu.phone = (data.get('phone') or '').strip() or None
        stu.whatsapp = (data.get('whatsapp') or '').strip() or None
        stu.email = (data.get('email') or '').strip() or None
        stu.address = (data.get('address') or '').strip() or None
        stu.city = (data.get('city') or '').strip() or None
        stu.cin = (data.get('cin') or '').strip().upper() or None
        stu.school_level = data.get('school_level')
        stu.school_name = (data.get('school_name') or '').strip() or None
        stu.parent_name = (data.get('parent_name') or '').strip() or None
        raw_p_phone = (data.get('parent_phone') or '').strip()
        stu.parent_phone = raw_p_phone or None
        stu.status = data.get('status', 'active')
        stu.notes = data.get('notes')

        # Auto-link family code if not set
        if not stu.family_code and (raw_p_phone or stu.phone):
            p_check = raw_p_phone or stu.phone
            if p_check and len(p_check) >= 8:
                clean_p = p_check.replace(' ', '').replace('-', '').replace('.', '')
                sibling = Student.query.filter(
                    Student.id != (stu.id or 0),
                    db.or_(
                        Student.parent_phone.like(f"%{clean_p[-8:]}%"),
                        Student.phone.like(f"%{clean_p[-8:]}%")
                    )
                ).first()
                if sibling:
                    fam_code = sibling.family_code or f"FAM-{clean_p[-6:]}"
                    stu.family_code = fam_code
                    if not sibling.family_code:
                        sibling.family_code = fam_code
        # photo
        f = request.files.get('photo')
        if f and f.filename:
            fn = f"{stu.id or 'tmp'}_{secure_filename(f.filename)}"
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
            stu.photo = fn
        db.session.commit()
        log_action('student_save', stu.full_name)
        flash('Élève enregistré', 'success')
        return redirect(url_for('student_view', sid=stu.id))
    return render_template('students/form.html', stu=stu)


@app.route('/students/<int:sid>')
@login_required
@role_required('admin', 'secretary')
def student_view(sid):
    stu = Student.query.get_or_404(sid)
    sync_student_renewed_enrollments(sid)
    enrolls = Enrollment.query.filter_by(student_id=sid).order_by(Enrollment.id.desc()).all()
    raw_payments = Payment.query.filter_by(student_id=sid).order_by(Payment.date.desc(), Payment.id.desc()).all()
    grades = Grade.query.filter_by(student_id=sid).order_by(Grade.date.desc()).all()
    attendances = Attendance.query.filter_by(student_id=sid).order_by(Attendance.date.desc()).limit(30).all()

    att_present = sum(1 for a in attendances if a.status == 'present')
    att_absent = sum(1 for a in attendances if a.status == 'absent')
    att_late = sum(1 for a in attendances if a.status == 'late')
    att_rate = round((att_present / len(attendances) * 100) if attendances else 100, 1)

    total_spent = sum(p.amount for p in raw_payments)
    payments = group_payments_by_receipt(raw_payments)
    all_courses = Course.query.filter_by(active=True).order_by(Course.name).all()

    return render_template('students/view.html',
                           stu=stu,
                           enrolls=enrolls,
                           payments=payments,
                           grades=grades,
                           attendances=attendances,
                           att_present=att_present,
                           att_absent=att_absent,
                           att_late=att_late,
                            att_rate=att_rate,
                            all_courses=all_courses,
                            total_spent=total_spent)


@app.route('/students/<int:sid>/timetable')
@app.route('/students/<int:sid>/timetable/print')
@app.route('/students/<int:sid>/timetable_print')
@login_required
@role_required('admin', 'secretary', 'teacher')
def student_timetable_print(sid):
    stu = Student.query.get_or_404(sid)
    fmt = request.args.get('fmt', 'a5').lower()  # 'a5', 'a4', '80mm'

    # Récupérer les inscriptions actives ou en cours
    enrollments = Enrollment.query.filter(
        Enrollment.student_id == sid,
        Enrollment.status.in_(['active', 'trial', 'pending_assignment'])
    ).all()

    # Récupérer les cours distincts de l'élève
    courses = []
    course_ids = []
    for e in enrollments:
        if e.course and e.course.id not in course_ids:
            courses.append(e.course)
            course_ids.append(e.course.id)

    # Récupérer les créneaux horaires associés uniquement à ces cours
    slots = []
    if course_ids:
        slots = ScheduleSlot.query.filter(ScheduleSlot.course_id.in_(course_ids)).all()
        slots.sort(key=lambda s: (s.day_of_week, s.start_time or ''))

    grid = {d: [] for d in range(7)}
    for s in slots:
        grid[s.day_of_week].append(s)

    current_lang = session.get('lang', 'fr')
    days_list = DAYS_AR if current_lang == 'ar' else DAYS_FR
    settings_dict = {s.key: s.value for s in Setting.query.all()}

    return render_template(
        'students/timetable_print.html',
        stu=stu,
        enrollments=enrollments,
        courses=courses,
        slots=slots,
        grid=grid,
        days=days_list,
        days_fr=DAYS_FR,
        fmt=fmt,
        settings=settings_dict,
        today=date.today()
    )


def generate_spintax_student_timetable(stu, courses, slots, recipient_type='parent', lang='ar', inst_name=None, inst_phone=None, ref_seed=None):
    """
    Generate an anti-ban WhatsApp timetable notification message using Spintax variations.
    Includes:
      - Student Name & Code
      - Schedule breakdown by days, times, courses, rooms, teachers
      - Randomized greetings, intros, guidance, and closings
      - Unique anti-ban reference hash [Réf: #EDT-XXXX]
    Supports recipient_type='parent' or recipient_type='student'.
    Languages: lang='ar' or lang='fr'.
    """
    import random
    if not inst_name:
        inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    if not inst_phone:
        inst_phone = SH.get_setting('inst_phone', '06 60 29 11 55')

    seed = ref_seed if ref_seed is not None else random.randint(1000, 9999)
    stu_name = stu.full_name or "Élève"
    stu_code = stu.code or f"#{stu.id}"

    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    days_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']

    schedule_lines_fr = []
    schedule_lines_ar = []

    if slots:
        sorted_slots = sorted(slots, key=lambda s: (s.day_of_week or 0, s.start_time or ''))
        for s in sorted_slots:
            d_idx = s.day_of_week if 0 <= (s.day_of_week or 0) <= 6 else 0
            day_f = days_fr[d_idx]
            day_a = days_ar[d_idx]
            time_str = f"{s.start_time or ''} - {s.end_time or ''}"
            c_name = s.course.display_name if s.course else "Séance"
            room_name = s.course.room.name if (s.course and s.course.room) else ""
            t_name = s.course.teacher.full_name if (s.course and s.course.teacher) else ""
            
            room_part_fr = f" (🚪 {room_name})" if room_name else ""
            room_part_ar = f" (🚪 قاعة {room_name})" if room_name else ""
            prof_part_fr = f" · 👨‍🏫 {t_name}" if t_name else ""
            prof_part_ar = f" · 👨‍🏫 {t_name}" if t_name else ""

            schedule_lines_fr.append(f"▫️ *{day_f}* ({time_str}) : *{c_name}*{room_part_fr}{prof_part_fr}")
            schedule_lines_ar.append(f"▫️ *{day_a}* ({time_str}) : *{c_name}*{room_part_ar}{prof_part_ar}")
    elif courses:
        for c in courses:
            t_name = c.teacher.full_name if c.teacher else ""
            schedule_lines_fr.append(f"▫️ *{c.display_name}* (👨‍🏫 {t_name or 'Équipe pédagogique'})")
            schedule_lines_ar.append(f"▫️ *{c.display_name}* (👨‍🏫 {t_name or 'الطاقم التربوي'})")
    else:
        schedule_lines_fr.append("▫️ Aucun créneau programmé pour le moment.")
        schedule_lines_ar.append("▫️ لا توجد حصص مبرمجة حالياً.")

    sched_text_fr = "\n".join(schedule_lines_fr)
    sched_text_ar = "\n".join(schedule_lines_ar)

    if recipient_type == 'parent':
        if lang == 'fr':
            greetings = [
                f"Bonjour chers parents de l'élève *{stu_name}* 🌸,\nL'administration de *{inst_name}* vous adresse ses salutations les plus cordiales.",
                f"Chers parents d'élèves, bonjour 🌸,\nToute l'équipe pédagogique de *{inst_name}* vous remercie pour votre précieuse confiance.",
                f"Bonjour à toute la famille 🌸,\nLa direction de *{inst_name}* a le plaisir de vous transmettre les détails du parcours scolaire de votre enfant.",
                f"Chère famille de *{stu_name}*, salutations distinguées 🌸,\nNous vous transmettons ce message concernant l'organisation des cours de votre enfant."
            ]
            intros = [
                f"Veuillez trouver ci-dessous l'emploi du temps hebdomadaire officiel de votre enfant (*{stu_name}*) :",
                f"Afin de garantir une assiduité et un suivi optimal, voici le planning des séances de cours hebdomadaires pour votre enfant (*{stu_name}*) :",
                f"Nous avons le plaisir de vous communiquer les créneaux et horaires de cours fixés pour votre enfant (*{stu_name}*) :"
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🗓️ *EMPLOI DU TEMPS OFFICIEL*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Élève :* *{stu_name}* ({stu_code})\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{sched_text_fr}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📸 *Image jointe :* L'image haute définition de l'emploi du temps est également transmise ci-joint."
            )
            closings = [
                f"⚠️ *Rappel :* Nous prions nos chers élèves de respecter scrupuleusement les horaires des séances.\nPour tout renseignement : 📞 *{inst_phone}*.\n\nCordialement,\n*Direction Pédagogique — {inst_name}*\n[Réf: #EDT-{seed}]",
                f"⚠️ *Important :* Merci de veiller à la ponctualité de l'élève aux cours.\nAssistance & Contact : 📞 *{inst_phone}*.\n\nBien cordialement,\n*Administration {inst_name}*\n[Réf: #EDT-{seed}]"
            ]
            return f"{random.choice(greetings)}\n\n{random.choice(intros)}\n\n{card}\n\n{random.choice(closings)}"
        else:
            greetings = [
                f"السلام عليكم ورحمة الله وبركاته 🌸\nتحية طيبة لولي أمر التلميذ(ة) *{stu_name}* من إدارة *{inst_name}*.",
                f"تحية طيبة واحتراماً 🌸\nتتقدم إدارة *{inst_name}* بخالص التحيات والتقدير لأسرة التلميذ(ة) *{stu_name}*.",
                f"أهلاً بحضرتكم 🌸\nتتمنى لكم إدارة وأطر *{inst_name}* مسيرة دراسية موفقة ومليئة بالنجاح والتميز."
            ]
            intros = [
                f"يسعدنا أن نوافيكم أسفله بجدول الحصص والتوقيت الأسبوعي الرسمي الخاص بابنكم/ابنتكم (*{stu_name}*) :",
                f"حرصاً منا على حسن المتابعة والانضباط المدرسي، تجدون أسفله برنامج ومواعيد الحصص الأسبوعية الخاصة بـ (*{stu_name}*) :",
                f"نضع رهن إشارتكم البرنامج الزمني والتوقيت الأسبوعي المعتمد للتلميذ(ة) (*{stu_name}*) :"
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🗓️ *جدول الحصص الأسبوعي الرسمي*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *التلميذ(ة) :* *{stu_name}* ({stu_code})\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{sched_text_ar}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📸 *ملاحظة :* تجدون رفقته الصورة الرسمية لجدول الحصص الأسبوعي."
            )
            closings = [
                f"⚠️ *تنبيه :* نهيب بكم حث التلميذ على احترام مواعيد الحصص بدقة والحضور في الوقت المحدد.\nلأي استفسار أو تواصل : 📞 *{inst_phone}*.\n\nمع فائق الاحترام والتقدير،\n*إدارة {inst_name}*\n[المرجع: #EDT-{seed}]",
                f"⚠️ *ملاحظة هامة :* نرجو الحرص على انضباط التلميذ في الحضور.\nللتواصل والاستعلام : 📞 *{inst_phone}*.\n\nوفقكم الله وسدد خطاكم،\n*الإدارة التربوية — {inst_name}*\n[المرجع: #EDT-{seed}]"
            ]
            return f"{random.choice(greetings)}\n\n{random.choice(intros)}\n\n{card}\n\n{random.choice(closings)}"
    else:
        if lang == 'fr':
            greetings = [
                f"Bonjour *{stu_name}* 🌟,\nL'équipe de *{inst_name}* te souhaite plein succès dans tes cours !",
                f"Salut *{stu_name}* 🌟,\nVoici les informations relatives à ton planning hebdomadaire chez *{inst_name}*.",
                f"Bonjour *{stu_name}* 🌟,\nToute l'équipe pédagogique de *{inst_name}* est ravie de t'accompagner vers l'excellence."
            ]
            intros = [
                f"Voici le récapitulatif officiel de ton emploi du temps pour la semaine :",
                f"Retrouve ci-dessous le planning de tes cours et tes créneaux hebdomadaires :",
                f"Voici les horaires et les salles de tes séances chez *{inst_name}* :"
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🗓️ *TON EMPLOI DU TEMPS HEBDOMADAIRE*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Élève :* *{stu_name}* ({stu_code})\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{sched_text_fr}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📸 *Image :* L'image de ton emploi du temps est également jointe."
            )
            closings = [
                f"💡 *Conseil :* Sois toujours ponctuel(le) pour profiter pleinement de chaque cours !\nContact : 📞 *{inst_phone}*.\n\nBon courage !\n*Équipe {inst_name}*\n[Réf: #EDT-{seed}]",
                f"💡 *Rappel :* Merci d'être présent(e) 5 minutes avant le début de la séance.\nDes questions ? 📞 *{inst_phone}*.\n\nÀ très bientôt !\n*Direction {inst_name}*\n[Réf: #EDT-{seed}]"
            ]
            return f"{random.choice(greetings)}\n\n{random.choice(intros)}\n\n{card}\n\n{random.choice(closings)}"
        else:
            greetings = [
                f"أهلاً وسهلاً بك يا *{stu_name}* 🌟\nتتمنى لك أسرة *{inst_name}* مسيرة دراسية مليئة بالنجاح والتفوق !",
                f"مرحباً بك *{stu_name}* 🌟\nإليك تفاصيل جدول حصصك الأسبوعي في *{inst_name}*.",
                f"تحية طيبة لك يا *{stu_name}* 🌟\nيسعدنا تزويدك بمواعيد حصصك الدراسية للموسم الحالي."
            ]
            intros = [
                f"إليك جدول حصصك الأسبوعي الرسمي والمواعيد المحددة :",
                f"تجد أسفله تفاصيل حصصك الأسبوعية والقاعات المخصصة لك :",
                f"برنامجك الدراسي الأسبوعي موزع على النحو التالي :"
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🗓️ *جدول حصصك الأسبوعي*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *التلميذ :* *{stu_name}* ({stu_code})\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{sched_text_ar}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📸 *ملاحظة :* تجد رفقة هذه الرسالة صورة جدول الحصص الأسبوعي."
            )
            closings = [
                f"💡 *نصيحة ذهبية :* احرص دائماً على الحضور في الوقت المحدد والتركيز داخل الحصة لتحقيق أعلى المراتب !\nللتواصل : 📞 *{inst_phone}*.\n\nبالتوفيق والنجاح الدائم،\n*إدارة {inst_name}*\n[المرجع: #EDT-{seed}]",
                f"💡 *تذكير :* الانضباط والالتزام بالوقت أساس التفوق الدراسي.\nلأي استفسار : 📞 *{inst_phone}*.\n\nنراك في الحصة القادمة !\n*إدارة {inst_name}*\n[المرجع: #EDT-{seed}]"
            ]
            return f"{random.choice(greetings)}\n\n{random.choice(intros)}\n\n{card}\n\n{random.choice(closings)}"


@app.route('/api/students/<int:sid>/whatsapp_timetable_data')
@login_required
@role_required('admin', 'secretary', 'teacher')
def api_student_whatsapp_timetable_data(sid):
    stu = Student.query.get_or_404(sid)

    enrollments = Enrollment.query.filter(
        Enrollment.student_id == sid,
        Enrollment.status.in_(['active', 'trial', 'pending_assignment'])
    ).all()

    courses = []
    course_ids = []
    for e in enrollments:
        if e.course and e.course.id not in course_ids:
            courses.append(e.course)
            course_ids.append(e.course.id)

    slots = []
    if course_ids:
        slots = ScheduleSlot.query.filter(ScheduleSlot.course_id.in_(course_ids)).all()
        slots.sort(key=lambda s: (s.day_of_week or 0, s.start_time or ''))

    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '06 60 29 11 55')
    inst_address = SH.get_setting('inst_address', 'Lot Nora, N°10, Makhlouf - Deroua')

    clean_p = _clean_wa_phone(stu.parent_phone)
    clean_s = _clean_wa_phone(stu.phone)

    msg_ar_parent = generate_spintax_student_timetable(stu, courses, slots, recipient_type='parent', lang='ar', inst_name=inst_name, inst_phone=inst_phone)
    msg_fr_parent = generate_spintax_student_timetable(stu, courses, slots, recipient_type='parent', lang='fr', inst_name=inst_name, inst_phone=inst_phone)
    msg_ar_student = generate_spintax_student_timetable(stu, courses, slots, recipient_type='student', lang='ar', inst_name=inst_name, inst_phone=inst_phone)
    msg_fr_student = generate_spintax_student_timetable(stu, courses, slots, recipient_type='student', lang='fr', inst_name=inst_name, inst_phone=inst_phone)

    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    days_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']

    slots_payload = []
    for s in slots:
        d_idx = s.day_of_week if 0 <= (s.day_of_week or 0) <= 6 else 0
        slots_payload.append({
            'day_of_week': d_idx,
            'day_name_fr': days_fr[d_idx],
            'day_name_ar': days_ar[d_idx],
            'start_time': s.start_time or '',
            'end_time': s.end_time or '',
            'course_name': s.course.display_name if s.course else '',
            'teacher_name': s.course.teacher.full_name if (s.course and s.course.teacher) else '',
            'room_name': s.course.room.name if (s.course and s.course.room) else ''
        })

    courses_payload = []
    for c in courses:
        courses_payload.append({
            'id': c.id,
            'name': c.display_name,
            'teacher_name': c.teacher.full_name if c.teacher else '',
            'room_name': c.room.name if c.room else ''
        })

    return jsonify({
        'success': True,
        'student': {
            'id': stu.id,
            'name': stu.full_name,
            'full_name': stu.full_name,
            'code': stu.code or f"#{stu.id}",
            'parent_name': stu.parent_name or '',
            'raw_parent_phone': stu.parent_phone or '',
            'clean_parent_phone': clean_p or '',
            'raw_student_phone': stu.phone or '',
            'clean_student_phone': clean_s or '',
            'default_recipient': 'parent' if (stu.parent_phone and stu.parent_phone.strip()) else 'student'
        },
        'institute': {
            'name': inst_name,
            'phone': inst_phone,
            'address': inst_address
        },
        'courses': courses_payload,
        'slots': slots_payload,
        'messages': {
            'ar_parent': msg_ar_parent,
            'fr_parent': msg_fr_parent,
            'ar_student': msg_ar_student,
            'fr_student': msg_fr_student
        },
        'print_url': url_for('student_timetable_print', sid=stu.id)
    })


@app.route('/students/<int:sid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def student_delete(sid):
    stu = Student.query.get_or_404(sid)
    active_enrolls = Enrollment.query.filter_by(student_id=sid, status='active').count()
    if active_enrolls > 0:
        flash(f"Impossible de supprimer cet élève : il a {active_enrolls} inscription(s) active(s). Veuillez d'abord désinscrire ou archiver l'élève.", 'danger')
        return redirect(url_for('students'))
    
    past_records = Payment.query.filter_by(student_id=sid).count() + Enrollment.query.filter_by(student_id=sid).count()
    if past_records > 0:
        stu.status = 'inactive'
        db.session.commit()
        log_action('student_archive', f"Student {stu.full_name} archived")
        flash(f"L'élève '{stu.full_name}' a été désactivé (archivé) pour préserver l'historique comptable et financier.", 'warning')
    else:
        db.session.delete(stu)
        db.session.commit()
        log_action('student_delete', stu.full_name)
        flash('Élève supprimé', 'success')
    return redirect(url_for('students'))


# ---------------------------------------------------------------------------
# Teachers
# ---------------------------------------------------------------------------
@app.route('/teachers')
@login_required
@role_required('admin', 'secretary')
def teachers():
    status_filter = request.args.get('status', 'active')
    q = request.args.get('q', '').strip()
    selected_subject = request.args.get('subject', '').strip()

    query = Teacher.query

    if status_filter == 'active':
        query = query.filter_by(active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(active=False)

    if q:
        t_filter = build_teacher_search_filter(q, Teacher)
        if t_filter is not None:
            query = query.filter(t_filter)

    teacher_list = query.all()
    if selected_subject:
        teacher_list = [t for t in teacher_list if t.primary_matiere == selected_subject]

    teacher_list.sort(key=lambda t: (
        get_matiere_priority(t.primary_matiere),
        t.primary_matiere,
        (t.last_name or '').upper(),
        (t.first_name or '').upper()
    ))

    # All available matieres with count
    all_matieres_counts = {}
    base_teachers = Teacher.query.filter_by(active=True).all()
    for t_obj in base_teachers:
        m_name = t_obj.primary_matiere
        all_matieres_counts[m_name] = all_matieres_counts.get(m_name, 0) + 1

    all_matieres = []
    for m_name in sorted(all_matieres_counts.keys(), key=lambda x: (get_matiere_priority(x), x)):
        cfg = MATIERE_CONFIG.get(m_name, {})
        all_matieres.append({
            'name': m_name,
            'icon': cfg.get('icon', '📚'),
            'color': cfg.get('color', '#0B3D6E'),
            'count': all_matieres_counts[m_name]
        })

    total_teachers_count = Teacher.query.count()
    active_teachers_count = Teacher.query.filter_by(active=True).count()
    total_assigned_courses = Course.query.filter(Course.teacher_id != None, Course.active == True).count()

    return render_template('teachers/list.html',
                           teachers=teacher_list,
                           status_filter=status_filter,
                           q=q,
                           selected_subject=selected_subject,
                           all_matieres=all_matieres,
                           total_teachers_count=total_teachers_count,
                           active_teachers_count=active_teachers_count,
                           total_assigned_courses=total_assigned_courses)


# ---------------------------------------------------------------------------
# Teachers WhatsApp Accounts & Wi-Fi Anti-Ban Dispatcher
# ---------------------------------------------------------------------------

def detect_teacher_default_language(teacher):
    """
    Detect default message language for a teacher based on their subject:
    - German teacher -> 'de'
    - Spanish teacher -> 'es'
    - French teacher -> 'fr'
    - English teacher -> 'en' (or 'fr')
    - Soutien scolaire (Maths, PC, SVT, TC/PC, etc.) -> 'ar' (default Arabic as requested)
    - Fallback -> 'ar'
    """
    if not teacher:
        return 'ar'
    spec = (teacher.specialty or '').lower()
    subj = (teacher.subjects_taught or '').lower()
    txt = f"{spec} {subj}"

    if any(k in txt for k in ['allemand', 'deutsch', 'german']):
        return 'de'
    if any(k in txt for k in ['esp', 'espagnol', 'spanish']):
        return 'es'
    if any(k in txt for k in ['francais', 'français', 'fr ', 'fr reg', 'fran']):
        return 'fr'
    if any(k in txt for k in ['anglais', 'ang', 'english', 'eng']):
        return 'en'
    return 'ar'


def _suggest_teacher_username(t_id, first_name, last_name, existing_unames=None):
    if existing_unames is None:
        existing_unames = {u.username.upper() for u in User.query.all()}
    clean_fn = re.sub(r'[^a-zA-Z0-9]', '', first_name or '').upper()
    clean_ln = re.sub(r'[^a-zA-Z0-9]', '', last_name or '').upper()
    cand = clean_fn or f'PROF{t_id}'
    if cand not in existing_unames:
        return cand
    cand2 = f'{clean_fn}{clean_ln[:3]}'
    if cand2 not in existing_unames:
        return cand2
    cand3 = f'{clean_fn}_{t_id}'
    return cand3


def generate_spintax_teacher_account(teacher, user=None, password=None, lang='ar', inst_name=None, inst_phone=None, login_url=None, wifi1_ssid=None, wifi1_pass=None, wifi2_ssid=None, wifi2_pass=None, ref_seed=None):
    """
    Generate an anti-ban WhatsApp notification message for teacher credentials and Wi-Fi access.
    Includes:
      - Teacher Name
      - Platform Login URL, Username, and Password
      - Wi-Fi 1er étage (TP-Link-569C / 87646535)
      - Wi-Fi 2ème étage (TP_Link_5758_5G / 30957008)
      - Notice: Wi-Fi installed so all teachers can record attendance & absences
      - Spintax variations + unique reference hash [Réf: #PROF-XXXX]
    Languages: 'ar', 'fr', 'es', 'de', 'en'.
    """
    import random
    if not inst_name:
        inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    if not inst_phone:
        inst_phone = SH.get_setting('inst_phone', '')
    if not login_url:
        pub_url = SH.get_setting('public_app_url', '').rstrip('/')
        login_url = f"{pub_url}/login" if pub_url else "https://app.institutilas.com/login"
    if not wifi1_ssid:
        wifi1_ssid = SH.get_setting('wifi_floor1_ssid', 'TP-Link-569C')
    if not wifi1_pass:
        wifi1_pass = SH.get_setting('wifi_floor1_pass', '87646535')
    if not wifi2_ssid:
        wifi2_ssid = SH.get_setting('wifi_floor2_ssid', 'TP_Link_5758_5G')
    if not wifi2_pass:
        wifi2_pass = SH.get_setting('wifi_floor2_pass', '30957008')

    seed = ref_seed if ref_seed is not None else random.randint(1000, 9999)
    first_name = (teacher.first_name if teacher and teacher.first_name else 'Professeur').strip()
    username = (user.username if user else (first_name.upper().replace(' ', ''))).strip()
    pwd = (password or (user.plain_password if user and user.plain_password else '')).strip()

    if lang == 'fr':
        greetings = [
            f"Bonjour Cher(e) Professeur *{first_name}* 🌸",
            f"Chers collègues, Bonjour Professeur *{first_name}* 🌹",
            f"Bonjour *{first_name}*, message officiel de l'administration {inst_name} 🏫",
            f"Très cher(e) enseignant(e) *{first_name}*, nous espérons que vous allez bien 🌸"
        ]
        intros = [
            f"La direction de *{inst_name}* a le plaisir de vous transmettre vos identifiants d'accès à l'espace enseignant de la plateforme :",
            f"Dans le cadre de l'optimisation et de la numérisation du suivi pédagogique, voici vos accès à la plateforme *{inst_name}* :",
            f"Veuillez trouver ci-dessous vos paramètres de connexion à la plateforme pédagogique de *{inst_name}* :"
        ]
        wifi_notes = [
            f"📶 *Codes Wi-Fi de l'Établissement (Espace Professeurs) :*\n*Note importante :* Nous vous informons que le Wi-Fi a été spécialement installé et mis à votre disposition afin que l'ensemble des professeurs puissent effectuer l'appel et enregistrer l'absence/présence des élèves en direct à chaque séance :\n▫️ *1er étage :* `{wifi1_ssid}` | Clé : `{wifi1_pass}`\n▫️ *2ème étage :* `{wifi2_ssid}` | Clé : `{wifi2_pass}`",
            f"📶 *Connexion Wi-Fi de l'Institut :*\nVeuillez noter que le réseau Wi-Fi a été déployé pour permettre à tous les enseignants de réaliser le pointage des absences et retards directement via l'application au début de chaque cours :\n▫️ *1er étage :* `{wifi1_ssid}` | Mot de passe : `{wifi1_pass}`\n▫️ *2ème étage :* `{wifi2_ssid}` | Mot de passe : `{wifi2_pass}`"
        ]
        closings = [
            f"Nous vous remercions vivement pour votre collaboration et votre engagement constant auprès de nos élèves.",
            f"Merci pour votre rigueur et votre implication exemplaire dans le suivi en temps réel de nos apprenants.",
            f"Toute l'équipe administrative reste à votre écoute pour vous accompagner. Excellente journée à vous."
        ]
        g = random.choice(greetings)
        i = random.choice(intros)
        w = random.choice(wifi_notes)
        c = random.choice(closings)
        creds = f"🌐 *Lien de connexion :* {login_url}\n👤 *Identifiant :* `{username}`\n🔑 *Mot de passe :* `{pwd}`"
        sign = f"🏫 Direction *{inst_name}* | Tél : {inst_phone}\n[Réf: #PROF-{seed}]"
        return f"{g}\n\n{i}\n\n{creds}\n\n{w}\n\n{c}\n\n{sign}"

    elif lang == 'es':
        greetings = [
            f"¡Hola, estimado/a profesor/a *{first_name}*! 🌸",
            f"Saludos cordiales, estimado/a *{first_name}* 🌹",
            f"Estimado/a profesor/a *{first_name}*, le saludamos cordialmente desde {inst_name} 🏫",
            f"¡Buenos días, profesor/a *{first_name}*! Esperamos que se encuentre muy bien 🌸"
        ]
        intros = [
            f"La dirección de *{inst_name}* tiene el placer de facilitarle sus datos de acceso a la plataforma digital docente:",
            f"Para facilitar su labor pedagógica y el seguimiento escolar, aquí tiene sus credenciales de acceso al portal de *{inst_name}*:",
            f"Le transmitimos a continuación sus datos de inicio de sesión para el portal de profesores de *{inst_name}*:"
        ]
        wifi_notes = [
            f"📶 *Conexión Wi-Fi del Instituto (Exclusiva Profesores):*\n*Aviso importante:* Les informamos que se ha instalado la red Wi-Fi para que todos los profesores puedan registrar cómodamente la asistencia y las faltas de los alumnos en el sistema al inicio de cada clase:\n▫️ *1.ª planta (1er étage) :* `{wifi1_ssid}` | Clave: `{wifi1_pass}`\n▫️ *2.ª planta (2ème étage) :* `{wifi2_ssid}` | Clave: `{wifi2_pass}`",
            f"📶 *Redes Wi-Fi del Centro Educativo:*\nLe recordamos que disponemos de Wi-Fi para que todo el equipo docente registre el parte de asistencia de los estudiantes en tiempo real:\n▫️ *1.ª planta (1er étage) :* `{wifi1_ssid}` | Contraseña: `{wifi1_pass}`\n▫️ *2.ª planta (2ème étage) :* `{wifi2_ssid}` | Contraseña: `{wifi2_pass}`"
        ]
        closings = [
            f"Le agradecemos profundamente su profesionalidad y constante dedicación hacia nuestros estudiantes.",
            f"Muchas gracias por su valiosa colaboración en el seguimiento pedagógico. ¡Mucho éxito en sus clases!",
            f"La administración queda a su completa disposición para cualquier consulta o asistencia."
        ]
        g = random.choice(greetings)
        i = random.choice(intros)
        w = random.choice(wifi_notes)
        c = random.choice(closings)
        creds = f"🌐 *Enlace de acceso :* {login_url}\n👤 *Usuario :* `{username}`\n🔑 *Contraseña :* `{pwd}`"
        sign = f"🏫 Dirección *{inst_name}* | Tel: {inst_phone}\n[Réf: #PROF-{seed}]"
        return f"{g}\n\n{i}\n\n{creds}\n\n{w}\n\n{c}\n\n{sign}"

    elif lang == 'de':
        greetings = [
            f"Guten Tag, sehr geehrte/r Frau/Herr *{first_name}* 🌸",
            f"Herzliche Grüße, liebe/r Kollege/in *{first_name}* 🌹",
            f"Liebe/r *{first_name}*, offizielle Mitteilung der Schulleitung {inst_name} 🏫",
            f"Schönen Tag, Herr/Frau *{first_name}*! Wir hoffen, es geht Ihnen hervorragend 🌸"
        ]
        intros = [
            f"Die Schulleitung von *{inst_name}* übermittelt Ihnen hiermit gerne Ihre persönlichen Zugangsdaten zum Lehrerportal:",
            f"Im Rahmen der Optimierung unseres Schulsystems erhalten Sie hiermit Ihre Login-Daten für die Plattform von *{inst_name}*:",
            f"Nachfolgend finden Sie Ihre Zugangsdaten für das digitale Dozentenportal von *{inst_name}*:"
        ]
        wifi_notes = [
            f"📶 *WLAN-Zugangsdaten des Instituts (Für Lehrkräfte):*\n*Wichtiger Hinweis:* Bitte beachten Sie, dass das WLAN eingerichtet wurde, damit alle Lehrkräfte die Anwesenheit und Fehlzeiten der Schüler zu Beginn jeder Unterrichtsstunde direkt im System erfassen können:\n▫️ *1. Etage (1er étage) :* `{wifi1_ssid}` | Passwort: `{wifi1_pass}`\n▫️ *2. Etage (2ème étage) :* `{wifi2_ssid}` | Passwort: `{wifi2_pass}`",
            f"📶 *WLAN-Verbindung für Lehrkräfte:*\nWir haben ein schulinternes WLAN bereitgestellt, damit die Anwesenheitskontrolle der Schüler während des Unterrichts reibungslos durchgeführt werden kann:\n▫️ *1. Etage (1er étage) :* `{wifi1_ssid}` | Kennwort: `{wifi1_pass}`\n▫️ *2. Etage (2ème étage) :* `{wifi2_ssid}` | Kennwort: `{wifi2_pass}`"
        ]
        closings = [
            f"Wir danken Ihnen herzlich für Ihre geschätzte Mitarbeit und Ihr Engagement für unsere Schüler.",
            f"Vielen Dank für Ihre zuverlässige Dokumentation und pädagogische Begleitung. Viel Erfolg bei Ihren Kursen!",
            f"Die Schulleitung steht Ihnen bei Fragen jederzeit gerne zur Verfügung."
        ]
        g = random.choice(greetings)
        i = random.choice(intros)
        w = random.choice(wifi_notes)
        c = random.choice(closings)
        creds = f"🌐 *Login-Link :* {login_url}\n👤 *Benutzername :* `{username}`\n🔑 *Passwort :* `{pwd}`"
        sign = f"🏫 Schulleitung *{inst_name}* | Tel: {inst_phone}\n[Réf: #PROF-{seed}]"
        return f"{g}\n\n{i}\n\n{creds}\n\n{w}\n\n{c}\n\n{sign}"

    elif lang == 'en':
        greetings = [
            f"Hello Dear Teacher *{first_name}* 🌸",
            f"Warm greetings, dear *{first_name}* 🌹",
            f"Dear Teacher *{first_name}*, official notification from {inst_name} administration 🏫",
            f"Greetings *{first_name}*, we hope this message finds you well 🌸"
        ]
        intros = [
            f"The administration of *{inst_name}* is pleased to share your login credentials for the school management platform:",
            f"To support your teaching and student management, here are your access details for *{inst_name}*:",
            f"Please find below your credentials for the teacher portal of *{inst_name}*:"
        ]
        wifi_notes = [
            f"📶 *Institute Wi-Fi Networks (For Teachers):*\n*Important Notice:* Please note that Wi-Fi has been installed so that all teachers can easily and promptly record student attendance and absences directly on the platform in each session:\n▫️ *1st Floor (1er étage) :* `{wifi1_ssid}` | Password: `{wifi1_pass}`\n▫️ *2nd Floor (2ème étage) :* `{wifi2_ssid}` | Password: `{wifi2_pass}`",
            f"📶 *Wi-Fi Access for Attendance Recording:*\nWi-Fi is provided throughout the institute to enable all professors to mark student attendance at the start of every class:\n▫️ *1st Floor (1er étage) :* `{wifi1_ssid}` | Key: `{wifi1_pass}`\n▫️ *2nd Floor (2ème étage) :* `{wifi2_ssid}` | Key: `{wifi2_pass}`"
        ]
        closings = [
            f"Thank you very much for your continuous cooperation and dedication to our students.",
            f"We appreciate your valuable contribution to student attendance tracking and educational excellence.",
            f"The administration remains at your service for any assistance. Have a wonderful day!"
        ]
        g = random.choice(greetings)
        i = random.choice(intros)
        w = random.choice(wifi_notes)
        c = random.choice(closings)
        creds = f"🌐 *Platform Link :* {login_url}\n👤 *Username :* `{username}`\n🔑 *Password :* `{pwd}`"
        sign = f"🏫 Administration *{inst_name}* | Tel: {inst_phone}\n[Réf: #PROF-{seed}]"
        return f"{g}\n\n{i}\n\n{creds}\n\n{w}\n\n{c}\n\n{sign}"

    else:
        # Arabic Spintax (Default for Moroccan Soutien teachers & General)
        greetings = [
            f"السلام عليكم ورحمة الله وبركاته، أستاذ(ة) *{first_name}* المحترم(ة) 🌹",
            f"تحية طيبة أستاذ(ة) *{first_name}*، نتمنى أن تكونوا في تمام الصحة والعافية 🌸",
            f"أهلاً وسهلاً أستاذ(ة) *{first_name}*، رسالة رسمية من إدارة {inst_name} 🏫",
            f"تحية تقدير واحترام للأستاذ(ة) الفاضل(ة) *{first_name}*، نرجو أن يجدكم هذا الإشعار بأفضل حال 🌹"
        ]
        intros = [
            f"يسر إدارة *{inst_name}* أن تضع رهن إشارتكم بيانات الولوج الخاصة بكم إلى المنظومة الرقمية للمعهد:",
            f"في إطار تنظيم وتطوير العمل الإداري والتربوي، إليكم بيانات حسابكم الشخصي على منصة *{inst_name}*:",
            f"نوافيكم ببيانات حسابكم المهني على الفضاء الرقمي لمؤسسة *{inst_name}* لتتبع الحصص والأنشطة:"
        ]
        wifi_notes = [
            f"📶 *شبكة Wi-Fi المعهد (خاصة بالأساتذة):*\n*إشعار هام:* نحيطكم علماً بأنه تم تزويد المعهد بشبكة Wi-Fi خاصة لتسهيل تسجيل غياب وحضور التلاميذ (Pointage d'absence) مباشرة وبانتظام في كل حصة دراسية عبر هواتفكم:\n▫️ *الطابق الأول (1er étage) :* `{wifi1_ssid}` | الرمز: `{wifi1_pass}`\n▫️ *الطابق الثاني (2ème étage) :* `{wifi2_ssid}` | الرمز: `{wifi2_pass}`",
            f"📶 *بيانات الاتصال بشبكة Wi-Fi (للاستعمال التربوي):*\n*ملاحظة:* نلفت انتباهكم الكريمة إلى أن إدارة المعهد وفرت شبكة Wi-Fi لتمكين جميع الأساتذة من توثيق الحضور والغياب للطلبة فور انطلاق كل حصة بكل سهولة:\n▫️ *الطابق الأول (1er étage) :* `{wifi1_ssid}` | كلمة السر: `{wifi1_pass}`\n▫️ *الطابق الثاني (2ème étage) :* `{wifi2_ssid}` | كلمة السر: `{wifi2_pass}`",
            f"📶 *خدمة Wi-Fi للأساتذة لضبط الغياب:*\n*تنبيه هادف:* تم ربط قاعات المعهد بشبكة Wi-Fi ليتسنى لجميع الأساتذة تسجيل الغياب والحضور بصفة مباشرة ودقيقة خلال الحصص الدراسية:\n▫️ *الطابق الأول (1er étage) :* `{wifi1_ssid}` | الرمز: `{wifi1_pass}`\n▫️ *الطابق الثاني (2ème étage) :* `{wifi2_ssid}` | الرمز: `{wifi2_pass}`"
        ]
        closings = [
            f"نشكركم جزيل الشكر على حسن تعاونكم الدائم وحرصكم التربوي المتميز.",
            f"شاكرين لكم مساهمتكم الفعالة في ضبط وتتبع مسار التلاميذ. دمتم في رعاية الله.",
            f"مع متمنياتنا لكم بكامل التوفيق والسداد في مهامكم النبيلة. إدارة المعهد رهن إشارتكم لأي مساعدة."
        ]
        g = random.choice(greetings)
        i = random.choice(intros)
        w = random.choice(wifi_notes)
        c = random.choice(closings)
        creds = f"🌐 *رابط المنصة :* {login_url}\n👤 *اسم المستخدم (Username) :* `{username}`\n🔑 *كلمة المرور (Mot de passe) :* `{pwd}`"
        sign = f"🏫 إدارة *{inst_name}* | هاتف: {inst_phone}\n[Réf: #PROF-{seed}]"
        return f"{g}\n\n{i}\n\n{creds}\n\n{w}\n\n{c}\n\n{sign}"


@app.route('/teachers/whatsapp-accounts', methods=['GET'])
@login_required
@role_required('admin', 'secretary')
def teachers_whatsapp_accounts():
    status_filter = request.args.get('status', 'all')
    q = request.args.get('q', '').strip()
    type_filter = request.args.get('type', 'all')  # 'all', 'lang', 'soutien'

    query = Teacher.query
    if q:
        t_filter = build_teacher_search_filter(q, Teacher)
        if t_filter is not None:
            query = query.filter(t_filter)

    teachers = query.order_by(Teacher.id).all()

    existing_unames = {u.username.upper() for u in User.query.all()}
    teachers_data = []

    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '')
    pub_url = SH.get_setting('public_app_url', '').rstrip('/')
    login_url = f"{pub_url}/login" if pub_url else url_for('login', _external=True)

    wifi1_ssid = SH.get_setting('wifi_floor1_ssid', 'TP-Link-569C')
    wifi1_pass = SH.get_setting('wifi_floor1_pass', '87646535')
    wifi2_ssid = SH.get_setting('wifi_floor2_ssid', 'TP_Link_5758_5G')
    wifi2_pass = SH.get_setting('wifi_floor2_pass', '30957008')

    wifi_info = {
        'wifi1_ssid': wifi1_ssid,
        'wifi1_pass': wifi1_pass,
        'wifi2_ssid': wifi2_ssid,
        'wifi2_pass': wifi2_pass,
    }

    for t in teachers:
        u = User.query.filter_by(teacher_id=t.id).first()
        has_account = (u is not None)
        uname = u.username if u else _suggest_teacher_username(t.id, t.first_name, t.last_name, existing_unames)
        pwd = (u.plain_password if (u and u.plain_password) else '')
        def_lang = detect_teacher_default_language(t)
        is_lang_teacher = (def_lang in ['de', 'es', 'fr', 'en'])

        # Filters
        if status_filter == 'has_account' and not has_account:
            continue
        if status_filter == 'missing_account' and has_account:
            continue
        if type_filter == 'lang' and not is_lang_teacher:
            continue
        if type_filter == 'soutien' and is_lang_teacher:
            continue

        raw_phone = t.phone or ''
        clean_p = _clean_wa_phone(raw_phone)
        has_phone = bool(clean_p and len(clean_p) >= 9)

        # Pre-generate sample message for current default lang
        sample_msg = generate_spintax_teacher_account(
            t, user=u, password=pwd, lang=def_lang,
            inst_name=inst_name, inst_phone=inst_phone, login_url=login_url,
            wifi1_ssid=wifi1_ssid, wifi1_pass=wifi1_pass,
            wifi2_ssid=wifi2_ssid, wifi2_pass=wifi2_pass
        )

        teachers_data.append({
            'teacher': t,
            'user': u,
            'username': uname,
            'password': pwd,
            'has_account': has_account,
            'raw_phone': raw_phone,
            'clean_phone': clean_p,
            'has_phone': has_phone,
            'default_lang': def_lang,
            'is_lang_teacher': is_lang_teacher,
            'sample_msg': sample_msg
        })

    # Total counts for KPI cards
    all_t = Teacher.query.all()
    total_count = len(all_t)
    with_user_count = User.query.filter(User.teacher_id != None).count()
    missing_user_count = total_count - with_user_count
    with_phone_count = sum(1 for t in all_t if _clean_wa_phone(t.phone))
    lang_count = sum(1 for t in all_t if detect_teacher_default_language(t) in ['de', 'es', 'fr', 'en'])
    soutien_count = total_count - lang_count

    stats = {
        'total': total_count,
        'with_user': with_user_count,
        'missing_user': missing_user_count,
        'with_phone': with_phone_count,
        'lang_teachers': lang_count,
        'soutien_teachers': soutien_count
    }

    return render_template('teachers/whatsapp_accounts.html',
                           teachers_data=teachers_data,
                           stats=stats,
                           status_filter=status_filter,
                           type_filter=type_filter,
                           q=q,
                           wifi_info=wifi_info,
                           inst_name=inst_name,
                           inst_phone=inst_phone,
                           login_url=login_url)


@app.route('/api/teachers/<int:tid>/whatsapp_account_data', methods=['GET'])
@login_required
@role_required('admin', 'secretary')
def api_teacher_whatsapp_account_data(tid):
    t = Teacher.query.get_or_404(tid)
    u = User.query.filter_by(teacher_id=t.id).first()
    uname = u.username if u else _suggest_teacher_username(t.id, t.first_name, t.last_name)
    pwd = request.args.get('password') or (u.plain_password if (u and u.plain_password) else '')
    lang_req = request.args.get('lang') or detect_teacher_default_language(t)

    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '')
    pub_url = SH.get_setting('public_app_url', '').rstrip('/')
    login_url = f"{pub_url}/login" if pub_url else url_for('login', _external=True)

    wifi1_ssid = SH.get_setting('wifi_floor1_ssid', 'TP-Link-569C')
    wifi1_pass = SH.get_setting('wifi_floor1_pass', '87646535')
    wifi2_ssid = SH.get_setting('wifi_floor2_ssid', 'TP_Link_5758_5G')
    wifi2_pass = SH.get_setting('wifi_floor2_pass', '30957008')

    msg = generate_spintax_teacher_account(
        t, user=u, password=pwd, lang=lang_req,
        inst_name=inst_name, inst_phone=inst_phone, login_url=login_url,
        wifi1_ssid=wifi1_ssid, wifi1_pass=wifi1_pass,
        wifi2_ssid=wifi2_ssid, wifi2_pass=wifi2_pass
    )

    clean_p = _clean_wa_phone(t.phone)

    return jsonify({
        'teacher_id': t.id,
        'teacher_name': t.full_name,
        'username': uname,
        'password': pwd,
        'phone': clean_p,
        'lang': lang_req,
        'message': msg,
        'wifi1_ssid': wifi1_ssid,
        'wifi1_pass': wifi1_pass,
        'wifi2_ssid': wifi2_ssid,
        'wifi2_pass': wifi2_pass
    })


@app.route('/api/teachers/whatsapp-accounts/update-password', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def api_teacher_update_password():
    data = request.get_json() or request.form
    tid = _int(data.get('teacher_id'))
    pwd = (data.get('password') or '').strip()
    if not tid or not pwd:
        return jsonify({'success': False, 'message': 'teacher_id et password requis.'}), 400

    t = Teacher.query.get_or_404(tid)
    u = User.query.filter_by(teacher_id=t.id).first()
    if not u:
        uname = _suggest_teacher_username(t.id, t.first_name, t.last_name)
        u = User(username=uname, full_name=t.full_name, role='teacher', teacher_id=t.id, active=True)
        u.set_password(pwd, save_plain=True)
        db.session.add(u)
    else:
        u.set_password(pwd, save_plain=True)

    db.session.commit()
    return jsonify({'success': True, 'teacher_id': t.id, 'username': u.username, 'password': pwd})


@app.route('/api/teachers/whatsapp-accounts/create-account', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def api_teacher_create_account():
    data = request.get_json() or request.form
    tid = _int(data.get('teacher_id'))
    t = Teacher.query.get_or_404(tid)

    existing_u = User.query.filter_by(teacher_id=t.id).first()
    if existing_u:
        return jsonify({'success': True, 'already_exists': True, 'username': existing_u.username, 'password': existing_u.plain_password or ''})

    pwd = (data.get('password') or '').strip()
    if not pwd:
        return jsonify({'success': False, 'message': 'Veuillez renseigner un mot de passe pour cet enseignant.'}), 400

    requested_uname = (data.get('username') or '').strip().upper()
    if not requested_uname:
        requested_uname = _suggest_teacher_username(t.id, t.first_name, t.last_name)

    # Ensure uniqueness
    if User.query.filter(db.func.lower(User.username) == requested_uname.lower()).first():
        requested_uname = _suggest_teacher_username(t.id, t.first_name, t.last_name)

    u = User(username=requested_uname, full_name=t.full_name, role='teacher', teacher_id=t.id, active=True)
    u.set_password(pwd, save_plain=True)
    db.session.add(u)
    db.session.commit()

    return jsonify({'success': True, 'teacher_id': t.id, 'username': u.username, 'password': pwd})


@app.route('/api/teachers/whatsapp-accounts/create-all-missing', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def api_teacher_create_all_missing():
    data = request.get_json() or request.form or {}
    default_pwd = (data.get('password') or '').strip()
    if not default_pwd:
        return jsonify({'success': False, 'message': 'Veuillez spécifier le mot de passe initial à attribuer.'}), 400

    all_teachers = Teacher.query.order_by(Teacher.id).all()
    created_count = 0

    for t in all_teachers:
        existing = User.query.filter_by(teacher_id=t.id).first()
        if not existing:
            uname = _suggest_teacher_username(t.id, t.first_name, t.last_name)
            u = User(username=uname, full_name=t.full_name, role='teacher', teacher_id=t.id, active=True)
            u.set_password(default_pwd, save_plain=True)
            db.session.add(u)
            created_count += 1

    db.session.commit()
    return jsonify({'success': True, 'created_count': created_count})


@app.route('/api/teachers/whatsapp-accounts/bulk-set-password', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def api_teacher_bulk_set_password():
    data = request.get_json() or request.form
    pwd = (data.get('password') or '').strip()
    if not pwd:
        return jsonify({'success': False, 'message': 'Veuillez saisir un mot de passe.'}), 400
    raw_tids = data.get('teacher_ids') or []
    
    if isinstance(raw_tids, str):
        raw_tids = [int(x.strip()) for x in raw_tids.split(',') if x.strip().isdigit()]
    elif isinstance(raw_tids, list):
        raw_tids = [int(x) for x in raw_tids if str(x).isdigit()]

    if not raw_tids:
        raw_tids = [t.id for t in Teacher.query.all()]

    updated_count = 0
    for tid in raw_tids:
        t = Teacher.query.get(tid)
        if not t:
            continue
        u = User.query.filter_by(teacher_id=t.id).first()
        if not u:
            uname = _suggest_teacher_username(t.id, t.first_name, t.last_name)
            u = User(username=uname, full_name=t.full_name, role='teacher', teacher_id=t.id, active=True)
            db.session.add(u)
        u.set_password(pwd, save_plain=True)
        updated_count += 1

    db.session.commit()
    return jsonify({'success': True, 'updated_count': updated_count, 'password': pwd})


# ---------------------------------------------------------------------------
# Teachers Daily Timetable & Rooms WhatsApp Anti-Ban Dispatcher
# ---------------------------------------------------------------------------

def format_localized_date(d, lang='ar'):
    days_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    months_ar = ['', 'يناير', 'فبراير', 'مارس', 'أبريل', 'ماي', 'يونيو', 'يوليوز', 'غشت', 'شتنبر', 'أكتوبر', 'نونبر', 'دجنبر']
    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    months_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    days_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    months_en = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    days_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    months_es = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    days_de = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    months_de = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

    w = d.weekday() if hasattr(d, 'weekday') else 0
    m = d.month if hasattr(d, 'month') else 1
    day_num = d.day if hasattr(d, 'day') else 1
    year_num = d.year if hasattr(d, 'year') else 2026

    if lang == 'ar':
        return f"{days_ar[w]} {day_num} {months_ar[m]} {year_num}"
    elif lang == 'en':
        return f"{days_en[w]}, {months_en[m]} {day_num}, {year_num}"
    elif lang == 'es':
        return f"{days_es[w]} {day_num} de {months_es[m]} de {year_num}"
    elif lang == 'de':
        return f"{days_de[w]}, {day_num}. {months_de[m]} {year_num}"
    else:
        return f"{days_fr[w]} {day_num} {months_fr[m]} {year_num}"


def generate_spintax_teacher_daily_timetable(teacher, sessions, target_date, day_idx=None, lang='ar', inst_name=None, inst_phone=None, ref_seed=None):
    """
    Generate an anti-ban WhatsApp notification message containing a teacher's daily timetable
    and assigned classroom(s) for the selected day.
    Includes:
      - Teacher Name
      - Specific Date and Day of Week
      - Chronological list of sessions with course name, time, and room allocation (salle)
      - Friendly reminder to record student attendance/absences
      - Spintax variations + unique anti-ban reference hash [Réf: #EDT-PROF-XXXX]
    Languages: 'ar', 'fr', 'en', 'es', 'de'.
    """
    import random
    if not inst_name:
        inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    if not inst_phone:
        inst_phone = SH.get_setting('inst_phone', '06 60 29 11 55')

    wifi1_ssid = SH.get_setting('wifi_floor1_ssid', 'TP-Link-569C')
    wifi1_pass = SH.get_setting('wifi_floor1_pass', '87646535')
    wifi2_ssid = SH.get_setting('wifi_floor2_ssid', 'TP_Link_5758_5G')
    wifi2_pass = SH.get_setting('wifi_floor2_pass', '30957008')

    seed = ref_seed if ref_seed is not None else random.randint(1000, 9999)
    first_name = (teacher.first_name if teacher and teacher.first_name else 'Professeur').strip()
    full_name = (teacher.full_name if teacher and teacher.full_name else first_name).strip()

    date_str = format_localized_date(target_date, lang=lang)

    # Build sessions block
    sessions_lines = []
    if sessions:
        for s in sorted(sessions, key=lambda x: x.get('start_time') or ''):
            st = s.get('start_time', '')
            et = s.get('end_time', '')
            c_name = s.get('course_name', 'Séance')
            room = (s.get('room_name') or 'Non assignée').strip()
            enrolled = s.get('enrolled_count', 0)
            
            if lang == 'fr':
                room_txt = f"🚪 *Salle :* *{room}*" if room and room != 'Non assignée' else "🚪 *Salle :* ⚠️ Non assignée (voir administration)"
                eff_txt = f" · 👥 {enrolled} élève(s)" if enrolled else ""
                sessions_lines.append(f"▫️ ⏰ *{st} - {et}* : *{c_name}*\n   {room_txt}{eff_txt}")
            elif lang == 'en':
                room_txt = f"🚪 *Classroom :* *{room}*" if room and room != 'Non assignée' else "🚪 *Classroom :* ⚠️ Unassigned (see admin)"
                eff_txt = f" · 👥 {enrolled} student(s)" if enrolled else ""
                sessions_lines.append(f"▫️ ⏰ *{st} - {et}* : *{c_name}*\n   {room_txt}{eff_txt}")
            elif lang == 'es':
                room_txt = f"🚪 *Aula :* *{room}*" if room and room != 'Non assignée' else "🚪 *Aula :* ⚠️ No asignada"
                eff_txt = f" · 👥 {enrolled} alumno(s)" if enrolled else ""
                sessions_lines.append(f"▫️ ⏰ *{st} - {et}* : *{c_name}*\n   {room_txt}{eff_txt}")
            elif lang == 'de':
                room_txt = f"🚪 *Raum :* *{room}*" if room and room != 'Non assignée' else "🚪 *Raum :* ⚠️ Nicht zugewiesen"
                eff_txt = f" · 👥 {enrolled} Schüler" if enrolled else ""
                sessions_lines.append(f"▫️ ⏰ *{st} - {et}* : *{c_name}*\n   {room_txt}{eff_txt}")
            else: # 'ar'
                room_txt = f"🚪 *القاعة :* *{room}*" if room and room != 'Non assignée' else "🚪 *القاعة :* ⚠️ غير محددة (يرجى مراجعة الإدارة)"
                eff_txt = f" · 👥 {enrolled} تلميذ(ة)" if enrolled else ""
                sessions_lines.append(f"▫️ ⏰ *{st} - {et}* : *{c_name}*\n   {room_txt}{eff_txt}")
    else:
        if lang == 'fr':
            sessions_lines.append("▫️ Aucune séance programmée pour cette journée.")
        elif lang == 'en':
            sessions_lines.append("▫️ No classes scheduled for this day.")
        elif lang == 'es':
            sessions_lines.append("▫️ No hay clases programadas para este día.")
        elif lang == 'de':
            sessions_lines.append("▫️ Für diesen Tag sind keine Kurse geplant.")
        else:
            sessions_lines.append("▫️ لا توجد حصص مبرمجة لهذا اليوم.")

    schedule_block = "\n".join(sessions_lines)

    if lang == 'fr':
        greetings = [
            f"Bonjour Cher(e) Professeur *{full_name}* 🌸",
            f"Chers collègues, Bonjour Professeur *{full_name}* 🌹",
            f"Bonjour *{full_name}*, message officiel de l'administration {inst_name} 🏫",
            f"Très cher(e) enseignant(e) *{full_name}*, nous espérons que vous allez bien 🌸"
        ]
        intros = [
            f"L'administration de *{inst_name}* a le plaisir de vous transmettre votre planning de cours et les salles attribuées pour aujourd'hui (*{date_str}*) :",
            f"Dans le cadre de l'organisation pédagogique quotidienne, voici le programme de vos séances de cours et vos salles pour la journée du (*{date_str}*) :",
            f"Veuillez trouver ci-dessous le détail de vos cours programmés aujourd'hui (*{date_str}*) ainsi que les salles correspondantes :"
        ]
        reminders = [
            f"📌 *Rappel important :* Merci d'enregistrer l'appel et les présences/absences dès le début de chaque séance via votre espace enseignant sur la plateforme.",
            f"📌 *Consigne pédagogique :* Pensez à effectuer le pointage des élèves en direct au début du cours afin de garantir le suivi en temps réel.",
            f"📌 *Note de suivi :* L'enregistrement des présences en direct dès l'entame de la séance est indispensable pour le suivi régulier des élèves."
        ]
        closings = [
            f"Nous vous souhaitons d'excellentes séances et vous remercions vivement pour votre engagement constant.",
            f"Merci pour votre rigueur et votre dévouement auprès de nos apprenants. Excellente journée à vous.",
            f"Toute l'équipe administrative reste à votre écoute pour vous accompagner. Bon cours !"
        ]
        g = random.choice(greetings)
        i = random.choice(intros)
        r = random.choice(reminders)
        c = random.choice(closings)
        wifi_note = f"📶 *Wi-Fi Enseignants :* 1er étage : `{wifi1_ssid}` | 2ème étage : `{wifi2_ssid}`"
        card = (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🗓️ *PLANNING DU JOUR* ({date_str})\n"
            f"👨‍🏫 *Enseignant :* *{full_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{schedule_block}\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        sign = f"🏫 Direction *{inst_name}* | Tél : {inst_phone}\n[Réf: #EDT-PROF-{seed}]"
        return f"{g}\n\n{i}\n\n{card}\n\n{r}\n\n{wifi_note}\n\n{c}\n\n{sign}"

    elif lang == 'en':
        greetings = [
            f"Hello Dear Teacher *{full_name}* 🌸",
            f"Warm greetings, Dear Teacher *{full_name}* 🌹",
            f"Good day *{full_name}*, official notice from {inst_name} 🏫",
            f"Dear Teacher *{full_name}*, hope this message finds you well 🌸"
        ]
        intros = [
            f"The administration of *{inst_name}* is pleased to share your teaching schedule and room allocations for today (*{date_str}*) :",
            f"Here is your daily course schedule along with the assigned classrooms for (*{date_str}*) :",
            f"Please find below your teaching schedule and room assignments for today (*{date_str}*) :"
        ]
        reminders = [
            f"📌 *Reminder :* Please remember to record student attendance and absences at the start of each session on the teacher platform.",
            f"📌 *Notice :* Timely attendance marking at the beginning of each class is required for real-time tracking."
        ]
        closings = [
            f"Wishing you a productive and successful teaching session today.",
            f"Thank you for your continuous dedication and support for our students."
        ]
        g = random.choice(greetings)
        i = random.choice(intros)
        r = random.choice(reminders)
        c = random.choice(closings)
        wifi_note = f"📶 *Teacher Wi-Fi :* 1st Floor : `{wifi1_ssid}` | 2nd Floor : `{wifi2_ssid}`"
        card = (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🗓️ *TODAY'S SCHEDULE* ({date_str})\n"
            f"👨‍🏫 *Teacher :* *{full_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{schedule_block}\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        sign = f"🏫 Administration *{inst_name}* | Tel: {inst_phone}\n[Réf: #EDT-PROF-{seed}]"
        return f"{g}\n\n{i}\n\n{card}\n\n{r}\n\n{wifi_note}\n\n{c}\n\n{sign}"

    elif lang == 'es':
        greetings = [
            f"¡Hola, estimado/a profesor/a *{full_name}*! 🌸",
            f"Saludos cordiales, estimado/a profesor/a *{full_name}* 🌹",
            f"Estimado/a profesor/a *{full_name}*, le saludamos cordialmente desde {inst_name} 🏫"
        ]
        intros = [
            f"La dirección de *{inst_name}* tiene el placer de comunicarle su horario de clases y las aulas asignadas para hoy (*{date_str}*) :",
            f"A continuación le facilitamos su horario de cursos y aulas programadas para la jornada de hoy (*{date_str}*) :"
        ]
        reminders = [
            f"📌 *Recordatorio:* Por favor, registre la asistencia y las faltas de los alumnos al inicio de cada clase en la plataforma."
        ]
        closings = [
            f"¡Le deseamos unas clases excelentes y mucho éxito con los estudiantes!",
            f"Muchas gracias por su profesionalidad y constante dedicación hacia nuestros alumnos."
        ]
        g = random.choice(greetings)
        i = random.choice(intros)
        r = random.choice(reminders)
        c = random.choice(closings)
        wifi_note = f"📶 *Wi-Fi Profesores :* 1.ª planta : `{wifi1_ssid}` | 2.ª planta : `{wifi2_ssid}`"
        card = (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🗓️ *HORARIO DEL DÍA* ({date_str})\n"
            f"👨‍🏫 *Profesor/a :* *{full_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{schedule_block}\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        sign = f"🏫 Dirección *{inst_name}* | Tel: {inst_phone}\n[Réf: #EDT-PROF-{seed}]"
        return f"{g}\n\n{i}\n\n{card}\n\n{r}\n\n{wifi_note}\n\n{c}\n\n{sign}"

    elif lang == 'de':
        greetings = [
            f"Guten Tag, sehr geehrte/r Frau/Herr *{full_name}* 🌸",
            f"Herzliche Grüße, liebe/r Kollege/in *{full_name}* 🌹"
        ]
        intros = [
            f"Die Schulleitung von *{inst_name}* übermittelt Ihnen hiermit Ihren Unterrichtsplan und die Raumzuteilungen für heute (*{date_str}*) :"
        ]
        reminders = [
            f"📌 *Wichtiger Hinweis:* Bitte erfassen Sie die Anwesenheit und Fehlzeiten der Schüler zu Beginn jeder Stunde direkt im Portal."
        ]
        closings = [
            f"Wir wünschen Ihnen einen erfolgreichen Unterrichtstag!"
        ]
        g = random.choice(greetings)
        i = random.choice(intros)
        r = random.choice(reminders)
        c = random.choice(closings)
        wifi_note = f"📶 *Lehrer-WLAN :* 1. Etage : `{wifi1_ssid}` | 2. Etage : `{wifi2_ssid}`"
        card = (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🗓️ *UNTERRICHTSPLAN* ({date_str})\n"
            f"👨‍🏫 *Lehrkraft :* *{full_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{schedule_block}\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        sign = f"🏫 Schulleitung *{inst_name}* | Tel: {inst_phone}\n[Réf: #EDT-PROF-{seed}]"
        return f"{g}\n\n{i}\n\n{card}\n\n{r}\n\n{wifi_note}\n\n{c}\n\n{sign}"

    else:
        # Arabic (Default)
        greetings = [
            f"السلام عليكم ورحمة الله وبركاته، أستاذ(ة) *{full_name}* المحترم(ة) 🌹",
            f"تحية طيبة أستاذ(ة) *{full_name}*، نتمنى أن تكونوا في تمام الصحة والعافية 🌸",
            f"تحية تقدير واحترام للأستاذ(ة) الفاضل(ة) *{full_name}*، نرجو أن يجدكم هذا الإشعار بأفضل حال 🌹",
            f"أستاذ(ة) *{full_name}* الكريم(ة)، أسعد الله أوقاتكم بكل خير 🌸"
        ]
        intros = [
            f"يسر إدارة *{inst_name}* أن توافيكم ببرنامج حصصكم والقاعات المخصصة لكم لليوم (*{date_str}*) :",
            f"في إطار التنظيم اليومي للعمل التربوي، إليكم جدول حصصكم وتوزيع القاعات المبرمجة لكم اليوم (*{date_str}*) :",
            f"نضع بين أيديكم تفاصيل الحصص والقاعات الدراسية الخاصة بكم ليوم (*{date_str}*) بمعهد *{inst_name}* :"
        ]
        reminders = [
            f"📌 *تذكير هام :* نرجو التفضل بتسجيل الحضور والغياب (Pointage d'absence) في مستهل كل حصة عبر فضاء الأستاذ على المنصة.",
            f"📌 *إشعار تربوي :* يرجى تسجيل غياب وحضور التلاميذ فور انطلاق الحصة لضمان التتبع الآني والمستمر.",
            f"📌 *تذكير :* نحثكم على التحقق من قائمة التلاميذ وتسجيل الحضور بانتظام عبر النظام الرقمي لضبط السجلات."
        ]
        closings = [
            f"نتمنى لكم حصصاً موفقة وتأطيراً متميزاً لأبنائنا التلاميذ. دمتم في رعاية الله.",
            f"شاكرين لكم حسن تعاونكم الدائم وعطاءكم التربوي القيم. بالتوفيق والسداد.",
            f"إدارة المعهد رهن إشارتكم لأي مساعدة أو استفسار. عمل موفق ومبارك بإذن الله."
        ]
        g = random.choice(greetings)
        i = random.choice(intros)
        r = random.choice(reminders)
        c = random.choice(closings)
        wifi_note = f"📶 *شبكة Wi-Fi الأساتذة :* الطابق 1: `{wifi1_ssid}` | الطابق 2: `{wifi2_ssid}`"
        card = (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🗓️ *برنامج حصص اليوم* ({date_str})\n"
            f"👨‍🏫 *الأستاذ(ة) :* *{full_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{schedule_block}\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        sign = f"🏫 إدارة *{inst_name}* | هاتف: {inst_phone}\n[Réf: #EDT-PROF-{seed}]"
        return f"{g}\n\n{i}\n\n{card}\n\n{r}\n\n{wifi_note}\n\n{c}\n\n{sign}"


@app.route('/teachers/whatsapp-daily-timetable', methods=['GET'])
@login_required
@role_required('admin', 'secretary')
def teachers_whatsapp_daily_timetable():
    req_date = request.args.get('date', '').strip()
    req_day = request.args.get('day', '').strip()
    q = request.args.get('q', '').strip()
    room_raw = request.args.get('room_id', '').strip()
    room_filter = int(room_raw) if room_raw and room_raw.isdigit() else None

    today = date.today()
    target_date = today

    if req_date:
        try:
            target_date = date.fromisoformat(req_date)
        except Exception:
            target_date = today
    elif req_day != '' and req_day.isdigit():
        day_int = int(req_day)
        if 0 <= day_int <= 6:
            curr_w = today.weekday()
            target_date = today + timedelta(days=(day_int - curr_w))

    day_idx = target_date.weekday()

    # 1. Fetch slots for this weekday
    slots = ScheduleSlot.query.filter_by(day_of_week=day_idx).order_by(ScheduleSlot.start_time).all()
    teachers_map = {}
    seen_course_ids = set()

    for s in slots:
        t = s.effective_teacher
        if not t and s.course:
            ct = CourseTeacher.query.filter_by(course_id=s.course_id, is_active=True).first()
            if ct:
                t = ct.teacher
        if not t:
            continue
        if t.id not in teachers_map:
            teachers_map[t.id] = {'teacher': t, 'sessions': []}

        c = s.course
        room_name = (c.room.name if (c and c.room) else 'Non assignée').strip()
        c_name = c.display_name if c else 'Séance'
        group_name = c.group_name if c else ''
        enrolled = c.enrolled_count if c else 0
        cid = c.id if c else None

        teachers_map[t.id]['sessions'].append({
            'slot_id': s.id,
            'course_id': cid,
            'start_time': s.start_time or '',
            'end_time': s.end_time or '',
            'course_name': c_name,
            'group_name': group_name,
            'room_name': room_name,
            'room_id': c.room_id if c else None,
            'enrolled_count': enrolled
        })
        if cid:
            seen_course_ids.add(cid)

    # 2. Check active courses that have day_idx in scheduled_days but lack slot record
    active_courses = Course.query.filter_by(active=True).all()
    for c in active_courses:
        if c.id in seen_course_ids:
            continue
        if c.scheduled_days:
            days = [int(x.strip()) for x in c.scheduled_days.split(',') if x.strip().isdigit()]
            if day_idx in days:
                t = c.teacher
                if not t:
                    ct = CourseTeacher.query.filter_by(course_id=c.id, is_active=True).first()
                    if ct:
                        t = ct.teacher
                if not t:
                    continue
                if t.id not in teachers_map:
                    teachers_map[t.id] = {'teacher': t, 'sessions': []}

                room_name = (c.room.name if c.room else 'Non assignée').strip()
                teachers_map[t.id]['sessions'].append({
                    'slot_id': None,
                    'course_id': c.id,
                    'start_time': '19:00',
                    'end_time': '20:30',
                    'course_name': c.display_name,
                    'group_name': c.group_name or '',
                    'room_name': room_name,
                    'room_id': c.room_id,
                    'enrolled_count': c.enrolled_count
                })

    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '06 60 29 11 55')

    teachers_data = []
    distinct_rooms_in_use = set()

    for tid, info in teachers_map.items():
        t = info['teacher']
        sessions = info['sessions']
        sessions.sort(key=lambda x: x.get('start_time') or '')

        if room_filter:
            if not any(s.get('room_id') == room_filter for s in sessions):
                continue

        if q:
            q_lower = q.lower()
            name_match = q_lower in (t.full_name or '').lower()
            spec_match = q_lower in (t.specialty or '').lower()
            subj_match = q_lower in (t.subjects_taught or '').lower()
            course_match = any(q_lower in s.get('course_name', '').lower() for s in sessions)
            if not (name_match or spec_match or subj_match or course_match):
                continue

        raw_phone = t.phone or ''
        clean_p = _clean_wa_phone(raw_phone)
        has_phone = bool(clean_p and len(clean_p) >= 9)
        def_lang = detect_teacher_default_language(t)
        is_lang_teacher = (def_lang in ['de', 'es', 'fr', 'en'])

        for s in sessions:
            if s.get('room_name') and s.get('room_name') != 'Non assignée':
                distinct_rooms_in_use.add(s.get('room_name'))

        sample_msg = generate_spintax_teacher_daily_timetable(
            t, sessions, target_date, day_idx=day_idx, lang=def_lang,
            inst_name=inst_name, inst_phone=inst_phone
        )

        teachers_data.append({
            'teacher': t,
            'id': t.id,
            'name': t.full_name,
            'first_name': t.first_name,
            'matiere': t.primary_matiere,
            'avatar_url': t.avatar_url,
            'raw_phone': raw_phone,
            'clean_phone': clean_p,
            'has_phone': has_phone,
            'default_lang': def_lang,
            'is_lang_teacher': is_lang_teacher,
            'sessions': sessions,
            'sessions_count': len(sessions),
            'sample_msg': sample_msg,
            'rooms_list': list(set(s['room_name'] for s in sessions if s['room_name'] != 'Non assignée')),
            'has_unassigned_room': any(s['room_name'] in ['Non assignée', '', None] for s in sessions)
        })

    teachers_data.sort(key=lambda x: (
        x['sessions'][0]['start_time'] if x['sessions'] else '99:99',
        x['name'].upper()
    ))

    all_rooms = Room.query.order_by(Room.name).all()

    days_summary = []
    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    days_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    curr_w = today.weekday()
    for d_i in range(7):
        d_date = today + timedelta(days=(d_i - curr_w))
        d_slots = ScheduleSlot.query.filter_by(day_of_week=d_i).all()
        d_teacher_ids = {s.effective_teacher.id for s in d_slots if s.effective_teacher}
        days_summary.append({
            'day_idx': d_i,
            'date': d_date,
            'date_str': d_date.isoformat(),
            'name_fr': days_fr[d_i],
            'name_ar': days_ar[d_i],
            'sessions_count': len(d_slots),
            'teachers_count': len(d_teacher_ids),
            'is_today': (d_date == today),
            'is_target': (d_date == target_date)
        })

    stats = {
        'total_teachers': len(teachers_data),
        'total_sessions': sum(t['sessions_count'] for t in teachers_data),
        'with_phone': sum(1 for t in teachers_data if t['has_phone']),
        'missing_phone': sum(1 for t in teachers_data if not t['has_phone']),
        'total_rooms': len(distinct_rooms_in_use),
        'has_unassigned_rooms': any(t['has_unassigned_room'] for t in teachers_data)
    }

    date_str_fr = format_localized_date(target_date, lang='fr')
    date_str_ar = format_localized_date(target_date, lang='ar')

    return render_template('teachers/whatsapp_daily_timetable.html',
                           teachers_data=teachers_data,
                           stats=stats,
                           target_date=target_date,
                           target_date_str=target_date.isoformat(),
                           day_idx=day_idx,
                           date_str_fr=date_str_fr,
                           date_str_ar=date_str_ar,
                           days_summary=days_summary,
                           all_rooms=all_rooms,
                           room_filter=room_filter,
                           q=q,
                           is_today=(target_date == today),
                           inst_name=inst_name,
                           inst_phone=inst_phone)


@app.route('/api/teachers/<int:tid>/whatsapp_daily_timetable_data', methods=['GET'])
@login_required
@role_required('admin', 'secretary')
def api_teacher_whatsapp_daily_timetable_data(tid):
    t = Teacher.query.get_or_404(tid)
    req_date = request.args.get('date', '').strip()
    lang_req = request.args.get('lang') or detect_teacher_default_language(t)

    today = date.today()
    target_date = today
    if req_date:
        try:
            target_date = date.fromisoformat(req_date)
        except Exception:
            target_date = today

    day_idx = target_date.weekday()

    slots = ScheduleSlot.query.filter_by(day_of_week=day_idx).order_by(ScheduleSlot.start_time).all()
    teacher_slots = [s for s in slots if (s.effective_teacher and s.effective_teacher.id == tid)]

    sessions = []
    seen_cids = set()
    for s in teacher_slots:
        c = s.course
        room_name = (c.room.name if (c and c.room) else 'Non assignée').strip()
        c_name = c.display_name if c else 'Séance'
        enrolled = c.enrolled_count if c else 0
        cid = c.id if c else None
        sessions.append({
            'slot_id': s.id,
            'course_id': cid,
            'start_time': s.start_time or '',
            'end_time': s.end_time or '',
            'course_name': c_name,
            'room_name': room_name,
            'enrolled_count': enrolled
        })
        if cid:
            seen_cids.add(cid)

    active_courses = Course.query.filter(Course.active == True, (Course.teacher_id == tid)).all()
    for c in active_courses:
        if c.id in seen_cids:
            continue
        if c.scheduled_days:
            days = [int(x.strip()) for x in c.scheduled_days.split(',') if x.strip().isdigit()]
            if day_idx in days:
                room_name = (c.room.name if c.room else 'Non assignée').strip()
                sessions.append({
                    'slot_id': None,
                    'course_id': c.id,
                    'start_time': '19:00',
                    'end_time': '20:30',
                    'course_name': c.display_name,
                    'room_name': room_name,
                    'enrolled_count': c.enrolled_count
                })

    sessions.sort(key=lambda x: x.get('start_time') or '')

    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '06 60 29 11 55')
    clean_p = _clean_wa_phone(t.phone)

    msg = generate_spintax_teacher_daily_timetable(
        t, sessions, target_date, day_idx=day_idx, lang=lang_req,
        inst_name=inst_name, inst_phone=inst_phone
    )

    return jsonify({
        'teacher_id': t.id,
        'teacher_name': t.full_name,
        'phone': clean_p,
        'raw_phone': t.phone or '',
        'has_phone': bool(clean_p and len(clean_p) >= 9),
        'lang': lang_req,
        'target_date': target_date.isoformat(),
        'date_str_fr': format_localized_date(target_date, lang='fr'),
        'date_str_ar': format_localized_date(target_date, lang='ar'),
        'sessions': sessions,
        'message': msg
    })


@app.route('/teachers/new', methods=['GET', 'POST'])
@app.route('/teachers/<int:tid>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def teacher_form(tid=None):
    t = Teacher.query.get(tid) if tid else None
    if request.method == 'POST':
        d = request.form
        if t is None:
            next_num = (db.session.query(db.func.max(Teacher.id)).scalar() or 0) + 1
            t = Teacher(code=f"ENS-{next_num:03d}")
            db.session.add(t)

        t.title = d.get('title') or 'M.'
        t.first_name = (d.get('first_name') or '').strip()
        t.last_name = (d.get('last_name') or '').strip()
        t.gender = d.get('gender') or 'M'
        t.birth_date = parse_date(d.get('birth_date'))
        t.city = (d.get('city') or '').strip()
        t.address = (d.get('address') or '').strip()
        t.phone = (d.get('phone') or '').strip()
        t.email = (d.get('email') or '').strip()
        t.cin = (d.get('cin') or '').strip().upper()
        t.diploma = (d.get('diploma') or '').strip()
        t.years_experience = _int(d.get('years_experience'))
        t.contract_type = d.get('contract_type') or 'vacation'
        t.specialty = (d.get('specialty') or '').strip()
        t.subjects_taught = (d.get('subjects_taught') or '').strip()
        t.availability = (d.get('availability') or '').strip()
        t.bank_name = (d.get('bank_name') or '').strip()
        t.bank_rib = (d.get('bank_rib') or '').strip()
        t.bank_account_holder = (d.get('bank_account_holder') or '').strip()
        t.bank_agency = (d.get('bank_agency') or '').strip()
        t.emergency_contact = (d.get('emergency_contact') or '').strip()

        if current_user() and current_user().role == 'admin':
            t.salary_type = d.get('salary_type') or 'percentage'
            if d.get('salary_amount') is not None and str(d.get('salary_amount')).strip() != '':
                t.salary_amount = _f(d.get('salary_amount'))
            elif t.salary_amount is None:
                t.salary_amount = 50.0
        elif t.salary_amount is None:
            t.salary_amount = 50.0
            t.salary_type = 'percentage'

        t.hire_date = parse_date(d.get('hire_date'))
        t.active = d.get('active') == 'on'
        t.notes = d.get('notes')

        # Handle photo upload
        if 'photo' in request.files:
            pf = request.files['photo']
            if pf and pf.filename:
                fn = f"prof_{int(datetime.utcnow().timestamp())}_{secure_filename(pf.filename)}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                pf.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                t.photo = fn

        db.session.commit()
        log_action('teacher_save', t.full_name)
        flash(f"Enseignant '{t.full_name}' enregistré avec succès.", 'success')
        return redirect(url_for('teachers'))

    return render_template('teachers/form.html', teacher=t)


@app.route('/teachers/<int:tid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def teacher_delete(tid):
    t = Teacher.query.get_or_404(tid)
    active_courses = Course.query.filter_by(teacher_id=tid, active=True).count()
    if active_courses > 0:
        flash(f"Impossible de supprimer cet enseignant : il est assigné à {active_courses} classe(s) active(s). Veuillez d'abord réassigner ses classes.", 'danger')
        return redirect(url_for('teachers'))
    
    past_courses = Course.query.filter_by(teacher_id=tid).count()
    if past_courses > 0:
        t.active = False
        db.session.commit()
        log_action('teacher_archive', f"Teacher {t.full_name} archived")
        flash(f"L'enseignant '{t.full_name}' a été désactivé (archivé) pour préserver l'historique des cours et de paie.", 'warning')
    else:
        db.session.delete(t)
        db.session.commit()
        log_action('teacher_delete', t.full_name)
        flash('Enseignant supprimé', 'success')
    return redirect(url_for('teachers'))


def _parse_teacher_ids(req):
    raw_list = req.args.getlist('teacher_ids') + req.args.getlist('teacher_id')
    res = set()
    for item in raw_list:
        if not item:
            continue
        if isinstance(item, str) and ',' in item:
            for x in item.split(','):
                if x.strip().isdigit():
                    res.add(int(x.strip()))
        elif str(item).isdigit():
            res.add(int(item))
    return res


@app.route('/teachers/student-lists')
@login_required
@role_required('admin', 'secretary')
def teacher_student_lists():
    u = current_user()
    if u and u.role == 'teacher':
        t_id = u.teacher_id
        if not t_id:
            t_obj = Teacher.query.filter_by(full_name=u.full_name).first()
            t_id = t_obj.id if t_obj else None
        selected_teacher_ids = {t_id} if t_id else set()
    else:
        selected_teacher_ids = _parse_teacher_ids(request)
    search_q = request.args.get('q', '').strip()
    selected_subject = request.args.get('subject', '').strip()
    today_month = date.today().strftime('%Y-%m')
    req_month = request.args.get('month') or today_month

    try:
        y, m = map(int, req_month.split('-'))
    except Exception:
        y, m = date.today().year, date.today().month
        req_month = today_month

    all_teachers = Teacher.query.filter_by(active=True).all()
    all_teachers.sort(key=lambda t: (get_matiere_priority(t.primary_matiere), t.primary_matiere, (t.last_name or '').upper(), (t.first_name or '').upper()))
    teacher_data = []

    for t in all_teachers:
        if selected_teacher_ids and t.id not in selected_teacher_ids:
            continue

        courses = Course.query.filter_by(teacher_id=t.id, active=True).all()
        assigned_cts = CourseTeacher.query.filter_by(teacher_id=t.id, is_active=True).all()
        for ct in assigned_cts:
            if ct.course and ct.course.active and ct.course not in courses:
                courses.append(ct.course)
        c_list = []
        t_total_st = 0
        t_total_tuition = 0.0

        t_total_payout = 0.0
        t_total_net = 0.0

        for c in courses:
            c_mat = c.matiere
            if selected_subject and c_mat != selected_subject:
                continue
            all_c_enrolls = Enrollment.query.options(db.joinedload(Enrollment.student))\
                .filter_by(course_id=c.id)\
                .filter(Enrollment.status != 'dropped')\
                .order_by(Enrollment.id.desc()).all()
            
            student_enrolls_map = {}
            for en in all_c_enrolls:
                st = en.student
                if not st or st.status != 'active':
                    continue
                if search_q:
                    q_clean = " ".join(search_q.split()).upper()
                    tokens = q_clean.split()
                    target_str = f"{st.first_name or ''} {st.last_name or ''} {st.first_name or ''} {st.code or ''} {st.phone or ''} {st.parent_phone or ''}".upper()
                    if not (q_clean in target_str or (tokens and all(t in target_str for t in tokens))):
                        continue

                rev = calculate_enrollment_revenue_for_month(en, y, m)
                if en.status == 'transferred':
                    if rev <= 0:
                        continue
                    has_active = Enrollment.query.filter_by(student_id=en.student_id, status='active').first()
                    if not has_active:
                        continue
                else:
                    if not (rev > 0 or (en.enroll_date and en.enroll_date.year == y and en.enroll_date.month == m) or (en.end_date and en.end_date.year == y and en.end_date.month == m)):
                        continue

                if st.id not in student_enrolls_map:
                    student_enrolls_map[st.id] = {
                        'primary_enrollment': en,
                        'total_month_rev': 0.0,
                        'enrollments': []
                    }
                student_enrolls_map[st.id]['total_month_rev'] += rev
                student_enrolls_map[st.id]['enrollments'].append(en)
                if en.status == 'active' or student_enrolls_map[st.id]['primary_enrollment'].status != 'active':
                    student_enrolls_map[st.id]['primary_enrollment'] = en

            filtered_enrolls = []
            grp_tuition = 0.0

            for s_id, s_info in student_enrolls_map.items():
                primary_en = s_info['primary_enrollment']
                std_price = getattr(primary_en, 'unit_monthly_price', None) or primary_en.monthly_price or (c.unit_monthly_price if hasattr(c, 'unit_monthly_price') else (c.price_per_month or c.price or 300.0))
                month_rev = s_info['total_month_rev']

                if month_rev > std_price:
                    month_rev = std_price
                elif month_rev < 0:
                    month_rev = 0.0

                primary_en.month_rev = round(month_rev, 2)
                grp_tuition += primary_en.month_rev
                filtered_enrolls.append(primary_en)

            filtered_enrolls.sort(key=lambda en: (
                (en.student.last_name or '').upper() if en.student else '',
                (en.student.first_name or '').upper() if en.student else ''
            ))

            ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=t.id, is_active=True).first()
            if not ct:
                ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=t.id).first()

            comp_type = ct.compensation_type if ct else (t.salary_type or 'percentage')
            comp_val = ct.compensation_value if (ct and ct.compensation_value is not None) else (t.salary_amount if (t.salary_amount is not None and t.salary_amount > 0) else 50.0)

            grp_payout = 0.0
            if comp_type == 'percentage':
                grp_payout = round(grp_tuition * (comp_val / 100.0), 2)
            elif comp_type == 'per_student':
                grp_payout = round(len(filtered_enrolls) * comp_val, 2)
            elif comp_type == 'fixed':
                grp_payout = round(comp_val, 2) if grp_tuition > 0 else 0.0
            elif comp_type == 'hourly':
                slots_count = ScheduleSlot.query.filter_by(course_id=c.id).count()
                grp_payout = round(slots_count * 4 * comp_val, 2) if grp_tuition > 0 else 0.0

            grp_net = max(0.0, round(grp_tuition - grp_payout, 2))

            t_total_st += len(filtered_enrolls)
            t_total_tuition += grp_tuition
            t_total_payout += grp_payout
            t_total_net += grp_net

            c_list.append({
                'course': c,
                'matiere': c.matiere,
                'enrollments': filtered_enrolls,
                'count': len(filtered_enrolls),
                'grp_tuition': grp_tuition,
                'grp_payout': grp_payout,
                'grp_net': grp_net,
                'comp_type': comp_type,
                'comp_val': comp_val
            })

        t_total_payout = round(t_total_payout, 2)
        t_total_net = round(t_total_net, 2)

        # Skip expensive deductions and prior credit checks if teacher has no courses or no matching students in search
        if not c_list or (search_q and t_total_st == 0):
            continue

        # Advances & Expenses deduction (retenues sur salaire du mois)
        advances = TeacherAdvance.query.filter_by(teacher_id=t.id, period_month=req_month)\
            .filter(TeacherAdvance.status != 'cancelled')\
            .order_by(TeacherAdvance.date.asc(), TeacherAdvance.id.asc()).all()
        t_total_advances = round(sum(a.amount for a in advances), 2)

        teacher_expenses = TeacherExpense.query.filter_by(teacher_id=t.id, period_month=req_month)\
            .filter(TeacherExpense.status != 'cancelled')\
            .order_by(TeacherExpense.date.asc(), TeacherExpense.id.asc()).all()
        t_total_expenses = round(sum(e.amount for e in teacher_expenses), 2)
        t_total_deductions = round(t_total_advances + t_total_expenses, 2)

        # Prior credit/debt carried over from previous months
        prior_credit_deducted, prior_credit_reason = calculate_prior_teacher_credit(t, y, m)
        total_all_deductions = round(t_total_deductions + prior_credit_deducted, 2)

        balance = round(t_total_payout - total_all_deductions, 2)
        if balance >= 0:
            t_net_payout = balance
            t_credit_carryover = 0.0
        else:
            t_net_payout = 0.0
            t_credit_carryover = abs(balance)

        # Check if already paid for req_month (Anti-Doublon check)
        salary_payout = TeacherSalaryPayout.query.filter_by(teacher_id=t.id, period_month=req_month)\
            .filter(TeacherSalaryPayout.status != 'cancelled')\
            .order_by(TeacherSalaryPayout.id.desc()).first()
        is_paid = (salary_payout is not None)
        net_paid = salary_payout.net_amount if is_paid else 0.0
        reste_a_payer = max(0.0, round(t_net_payout - net_paid, 2)) if is_paid else t_net_payout

        if c_list and (not search_q or t_total_st > 0):
            c_list.sort(key=lambda ci: (get_matiere_priority(ci['matiere']), ci['course'].name or ''))
            teacher_data.append({
                'teacher': t,
                'primary_matiere': t.primary_matiere,
                'courses': c_list,
                'total_students': t_total_st,
                'total_tuition': t_total_tuition,
                'total_payout': t_total_payout,
                'total_advances': t_total_advances,
                'advances': advances,
                'total_expenses': t_total_expenses,
                'teacher_expenses': teacher_expenses,
                'total_deductions': t_total_deductions,
                'prior_credit_deducted': prior_credit_deducted,
                'prior_credit_reason': prior_credit_reason,
                'total_all_deductions': total_all_deductions,
                'credit_carryover': t_credit_carryover,
                'net_payout': t_net_payout,
                'total_net': t_total_net,
                'is_paid': is_paid,
                'salary_payout': salary_payout,
                'net_paid': net_paid,
                'reste_a_payer': reste_a_payer
            })

    # Sort teacher_data by Matière priority, then teacher last_name
    teacher_data.sort(key=lambda td: (
        get_matiere_priority(td['primary_matiere']),
        td['primary_matiere'],
        (td['teacher'].last_name or '').upper(),
        (td['teacher'].first_name or '').upper()
    ))

    # All available matieres with count for filter pills
    all_matieres_counts = {}
    for c_obj in Course.query.filter_by(active=True).all():
        m_name = c_obj.matiere
        all_matieres_counts[m_name] = all_matieres_counts.get(m_name, 0) + 1

    all_matieres = []
    for m_name in sorted(all_matieres_counts.keys(), key=lambda x: (get_matiere_priority(x), x)):
        cfg = MATIERE_CONFIG.get(m_name, {})
        all_matieres.append({
            'name': m_name,
            'icon': cfg.get('icon', '📚'),
            'color': cfg.get('color', '#0B3D6E'),
            'count': all_matieres_counts[m_name]
        })

    return render_template('teachers/student_lists.html',
                           teachers=all_teachers,
                           all_teachers=all_teachers,
                           selected_teacher_ids=list(selected_teacher_ids),
                           selected_teacher_id=list(selected_teacher_ids)[0] if len(selected_teacher_ids) == 1 else None,
                           search_q=search_q,
                           selected_subject=selected_subject,
                           all_matieres=all_matieres,
                           req_month=req_month,
                           current_month=today_month,
                           teacher_data=teacher_data)


@app.route('/teachers/student-lists/print')
@login_required
@role_required('admin', 'secretary')
def teacher_student_lists_print():
    u = current_user()
    if u and u.role == 'teacher':
        t_id = u.teacher_id
        if not t_id:
            t_obj = Teacher.query.filter_by(full_name=u.full_name).first()
            t_id = t_obj.id if t_obj else None
        selected_teacher_ids = {t_id} if t_id else set()
    else:
        selected_teacher_ids = _parse_teacher_ids(request)
    search_q = request.args.get('q', '').strip()
    selected_subject = request.args.get('subject', '').strip()
    today_month = date.today().strftime('%Y-%m')
    req_month = request.args.get('month') or today_month
    fmt = request.args.get('format', 'a4_landscape')

    try:
        y, m = map(int, req_month.split('-'))
    except Exception:
        y, m = date.today().year, date.today().month
        req_month = today_month

    months_fr = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
        7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }
    month_name_fr = f"{months_fr.get(m, 'Mois')} {y}"

    all_teachers = Teacher.query.filter_by(active=True).all()
    all_teachers.sort(key=lambda t: (get_matiere_priority(t.primary_matiere), t.primary_matiere, (t.last_name or '').upper(), (t.first_name or '').upper()))
    teacher_data = []

    for t in all_teachers:
        if selected_teacher_ids and t.id not in selected_teacher_ids:
            continue

        courses = Course.query.filter_by(teacher_id=t.id, active=True).all()
        assigned_cts = CourseTeacher.query.filter_by(teacher_id=t.id, is_active=True).all()
        for ct in assigned_cts:
            if ct.course and ct.course.active and ct.course not in courses:
                courses.append(ct.course)
        c_list = []
        t_total_st = 0
        t_total_tuition = 0.0

        t_total_payout = 0.0
        t_total_net = 0.0

        for c in courses:
            c_mat = c.matiere
            if selected_subject and c_mat != selected_subject:
                continue
            all_c_enrolls = Enrollment.query.filter_by(course_id=c.id).filter(Enrollment.status != 'dropped').order_by(Enrollment.id.desc()).all()
            
            student_enrolls_map = {}
            for en in all_c_enrolls:
                st = en.student
                if not st or st.status != 'active':
                    continue
                if search_q:
                    q_clean = " ".join(search_q.split()).upper()
                    tokens = q_clean.split()
                    target_str = f"{st.first_name or ''} {st.last_name or ''} {st.first_name or ''} {st.code or ''} {st.phone or ''} {st.parent_phone or ''}".upper()
                    if not (q_clean in target_str or (tokens and all(tok in target_str for tok in tokens))):
                        continue

                rev = calculate_enrollment_revenue_for_month(en, y, m)
                if en.status == 'transferred':
                    if rev <= 0:
                        continue
                    has_active = Enrollment.query.filter_by(student_id=en.student_id, status='active').first()
                    if not has_active:
                        continue
                else:
                    if not (rev > 0 or (en.enroll_date and en.enroll_date.year == y and en.enroll_date.month == m) or (en.end_date and en.end_date.year == y and en.end_date.month == m)):
                        continue

                if st.id not in student_enrolls_map:
                    student_enrolls_map[st.id] = {
                        'primary_enrollment': en,
                        'total_month_rev': 0.0,
                        'enrollments': []
                    }
                student_enrolls_map[st.id]['total_month_rev'] += rev
                student_enrolls_map[st.id]['enrollments'].append(en)
                if en.status == 'active' or student_enrolls_map[st.id]['primary_enrollment'].status != 'active':
                    student_enrolls_map[st.id]['primary_enrollment'] = en

            filtered_enrolls = []
            grp_tuition = 0.0

            for s_id, s_info in student_enrolls_map.items():
                primary_en = s_info['primary_enrollment']
                std_price = getattr(primary_en, 'unit_monthly_price', None) or primary_en.monthly_price or (c.unit_monthly_price if hasattr(c, 'unit_monthly_price') else (c.price_per_month or c.price or 300.0))
                month_rev = s_info['total_month_rev']

                if month_rev > std_price:
                    month_rev = std_price
                elif month_rev < 0:
                    month_rev = 0.0

                primary_en.month_rev = round(month_rev, 2)
                grp_tuition += primary_en.month_rev
                filtered_enrolls.append(primary_en)

            filtered_enrolls.sort(key=lambda en: (
                (en.student.last_name or '').upper() if en.student else '',
                (en.student.first_name or '').upper() if en.student else ''
            ))

            ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=t.id, is_active=True).first()
            if not ct:
                ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=t.id).first()

            comp_type = ct.compensation_type if ct else (t.salary_type or 'percentage')
            comp_val = ct.compensation_value if (ct and ct.compensation_value is not None) else (t.salary_amount if (t.salary_amount is not None and t.salary_amount > 0) else 50.0)

            grp_payout = 0.0
            if comp_type == 'percentage':
                grp_payout = round(grp_tuition * (comp_val / 100.0), 2)
            elif comp_type == 'per_student':
                grp_payout = round(len(filtered_enrolls) * comp_val, 2)
            elif comp_type == 'fixed':
                grp_payout = round(comp_val, 2) if grp_tuition > 0 else 0.0
            elif comp_type == 'hourly':
                slots_count = ScheduleSlot.query.filter_by(course_id=c.id).count()
                grp_payout = round(slots_count * 4 * comp_val, 2) if grp_tuition > 0 else 0.0

            grp_net = max(0.0, round(grp_tuition - grp_payout, 2))

            t_total_st += len(filtered_enrolls)
            t_total_tuition += grp_tuition
            t_total_payout += grp_payout
            t_total_net += grp_net

            c_list.append({
                'course': c,
                'matiere': c.matiere,
                'enrollments': filtered_enrolls,
                'count': len(filtered_enrolls),
                'grp_tuition': grp_tuition,
                'grp_payout': grp_payout,
                'grp_net': grp_net,
                'comp_type': comp_type,
                'comp_val': comp_val
            })

        t_total_payout = round(t_total_payout, 2)
        t_total_net = round(t_total_net, 2)

        # Advances & Expenses deduction (retenues sur salaire du mois)
        advances = TeacherAdvance.query.filter_by(teacher_id=t.id, period_month=req_month)\
            .filter(TeacherAdvance.status != 'cancelled')\
            .order_by(TeacherAdvance.date.asc(), TeacherAdvance.id.asc()).all()
        t_total_advances = round(sum(a.amount for a in advances), 2)

        teacher_expenses = TeacherExpense.query.filter_by(teacher_id=t.id, period_month=req_month)\
            .filter(TeacherExpense.status != 'cancelled')\
            .order_by(TeacherExpense.date.asc(), TeacherExpense.id.asc()).all()
        t_total_expenses = round(sum(e.amount for e in teacher_expenses), 2)
        t_total_deductions = round(t_total_advances + t_total_expenses, 2)

        # Prior credit/debt carried over from previous months
        prior_credit_deducted, prior_credit_reason = calculate_prior_teacher_credit(t, y, m)
        total_all_deductions = round(t_total_deductions + prior_credit_deducted, 2)

        balance = round(t_total_payout - total_all_deductions, 2)
        if balance >= 0:
            t_net_payout = balance
            t_credit_carryover = 0.0
        else:
            t_net_payout = 0.0
            t_credit_carryover = abs(balance)

        # Check if already paid for req_month (Anti-Doublon check)
        salary_payout = TeacherSalaryPayout.query.filter_by(teacher_id=t.id, period_month=req_month)\
            .filter(TeacherSalaryPayout.status != 'cancelled')\
            .order_by(TeacherSalaryPayout.id.desc()).first()
        is_paid = (salary_payout is not None)
        net_paid = salary_payout.net_amount if is_paid else 0.0
        reste_a_payer = max(0.0, round(t_net_payout - net_paid, 2)) if is_paid else t_net_payout

        if c_list and (not search_q or t_total_st > 0):
            c_list.sort(key=lambda ci: (get_matiere_priority(ci['matiere']), ci['course'].name or ''))
            teacher_data.append({
                'teacher': t,
                'primary_matiere': t.primary_matiere,
                'courses': c_list,
                'total_students': t_total_st,
                'total_tuition': t_total_tuition,
                'total_payout': t_total_payout,
                'total_advances': t_total_advances,
                'advances': advances,
                'total_expenses': t_total_expenses,
                'teacher_expenses': teacher_expenses,
                'total_deductions': t_total_deductions,
                'prior_credit_deducted': prior_credit_deducted,
                'prior_credit_reason': prior_credit_reason,
                'total_all_deductions': total_all_deductions,
                'credit_carryover': t_credit_carryover,
                'net_payout': t_net_payout,
                'total_net': t_total_net,
                'is_paid': is_paid,
                'salary_payout': salary_payout,
                'net_paid': net_paid,
                'reste_a_payer': reste_a_payer
            })

    # Sort teacher_data by Matière priority, then teacher last_name
    teacher_data.sort(key=lambda td: (
        get_matiere_priority(td['primary_matiere']),
        td['primary_matiere'],
        (td['teacher'].last_name or '').upper(),
        (td['teacher'].first_name or '').upper()
    ))

    all_matieres_counts = {}
    for c_obj in Course.query.filter_by(active=True).all():
        m_name = c_obj.matiere
        all_matieres_counts[m_name] = all_matieres_counts.get(m_name, 0) + 1

    all_matieres = []
    for m_name in sorted(all_matieres_counts.keys(), key=lambda x: (get_matiere_priority(x), x)):
        cfg = MATIERE_CONFIG.get(m_name, {})
        all_matieres.append({
            'name': m_name,
            'icon': cfg.get('icon', '📚'),
            'color': cfg.get('color', '#0B3D6E'),
            'count': all_matieres_counts[m_name]
        })

    return render_template('teachers/student_lists_print.html',
                           fmt=fmt,
                           teachers=all_teachers,
                           selected_subject=selected_subject,
                           all_matieres=all_matieres,
                           selected_teacher_ids=list(selected_teacher_ids),
                           selected_teacher_id=list(selected_teacher_ids)[0] if len(selected_teacher_ids) == 1 else None,
                           req_month=req_month,
                           month_name_fr=month_name_fr,
                           teacher_data=teacher_data,
                           today=date.today())


# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Class Lists & Attendance Sheets by Teacher (Zero Fees / Without Money)
# ---------------------------------------------------------------------------
@app.route('/teachers/class-lists')
@login_required
@role_required('admin', 'secretary')
def teacher_class_lists():
    u = current_user()
    all_teachers = Teacher.query.filter_by(active=True).all()
    all_teachers.sort(key=lambda t: (get_matiere_priority(t.primary_matiere), t.primary_matiere, (t.last_name or '').upper(), (t.first_name or '').upper()))

    # If teacher user, restrict to their own teacher profile
    if u and u.role == 'teacher':
        t_id = u.teacher_id
        if not t_id:
            matched_t = Teacher.query.filter_by(full_name=u.full_name).first()
            t_id = matched_t.id if matched_t else None
        selected_teacher_id = t_id
    else:
        selected_teacher_id = _int(request.args.get('teacher_id'))

    selected_course_id = _int(request.args.get('course_id'))
    selected_subject = request.args.get('subject', '').strip()
    status_filter = request.args.get('status', 'active')
    search_q = request.args.get('q', '').strip()
    sheet_type = request.args.get('sheet_type', 'attendance')
    if sheet_type not in ['attendance', 'weekly', 'monthly', 'simple']:
        sheet_type = 'attendance'

    today_month = date.today().strftime('%Y-%m')
    req_month = request.args.get('month') or today_month
    try:
        y, m = map(int, req_month.split('-'))
    except Exception:
        y, m = date.today().year, date.today().month
        req_month = today_month

    months_fr = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
        7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }
    month_name_fr = f"{months_fr.get(m, 'Mois')} {y}"
    month_start = date(y, m, 1)
    _, last_day = calendar.monthrange(y, m)
    month_end = date(y, m, last_day)

    # Week calculation for attendance sheets (Dates of week: Lundi - Dimanche)
    req_week_date = request.args.get('week_date')
    ref_date = None
    if req_week_date:
        ref_date = parse_date(req_week_date)

    if not ref_date:
        today_dt = date.today()
        if today_dt.year == y and today_dt.month == m:
            ref_date = today_dt
        else:
            ref_date = month_start

    # Monday of that week
    monday = ref_date - timedelta(days=ref_date.weekday())
    sunday = monday + timedelta(days=6)

    day_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    day_names_short_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    day_names_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']

    week_days = []
    for i in range(7):
        cur_d = monday + timedelta(days=i)
        week_days.append({
            'index': i,
            'name': day_names_fr[i],
            'short_name': day_names_short_fr[i],
            'name_ar': day_names_ar[i],
            'date': cur_d,
            'date_str': cur_d.strftime('%d/%m'),
            'full_date_str': cur_d.strftime('%d/%m/%Y'),
            'iso_date': cur_d.strftime('%Y-%m-%d'),
            'in_month': (cur_d.year == y and cur_d.month == m)
        })

    prev_week_date = (monday - timedelta(days=7)).strftime('%Y-%m-%d')
    next_week_date = (monday + timedelta(days=7)).strftime('%Y-%m-%d')
    current_week_date = monday.strftime('%Y-%m-%d')
    week_label_fr = f"Semaine du {monday.strftime('%d/%m/%Y')} au {sunday.strftime('%d/%m/%Y')}"

    # Month days & 2 parts (Part 1: 01 to 15, Part 2: 16 to end of month)
    all_month_days = []
    for d in range(1, last_day + 1):
        cur_d = date(y, m, d)
        w_idx = cur_d.weekday()
        all_month_days.append({
            'day_num': d,
            'weekday_index': w_idx,
            'name': day_names_fr[w_idx],
            'short_name': day_names_short_fr[w_idx],
            'name_ar': day_names_ar[w_idx],
            'date': cur_d,
            'date_str': cur_d.strftime('%d/%m'),
            'day_str': f"{d:02d}",
            'full_date_str': cur_d.strftime('%d/%m/%Y'),
            'iso_date': cur_d.strftime('%Y-%m-%d'),
        })

    part1_days = [d for d in all_month_days if d['day_num'] <= 15]
    part2_days = [d for d in all_month_days if d['day_num'] >= 16]

    monthly_parts = [
        {
            'part_num': 1,
            'part_key': 'part1',
            'title': f"1ère Quinzaine (Du 01 au 15 {month_name_fr})",
            'short_title': "Partie 1 (01 au 15)",
            'days': part1_days,
            'start_day': 1,
            'end_day': 15,
            'range_str': f"Du 01/{m:02d}/{y} au 15/{m:02d}/{y}",
            'days_count': len(part1_days)
        },
        {
            'part_num': 2,
            'part_key': 'part2',
            'title': f"2ème Quinzaine (Du 16 au {last_day:02d} {month_name_fr})",
            'short_title': f"Partie 2 (16 au {last_day:02d})",
            'days': part2_days,
            'start_day': 16,
            'end_day': last_day,
            'range_str': f"Du 16/{m:02d}/{y} au {last_day:02d}/{m:02d}/{y}",
            'days_count': len(part2_days)
        }
    ]

    month_part = request.args.get('month_part', 'part1')
    if month_part not in ['part1', 'part2']:
        month_part = 'part1'
    active_monthly_part = monthly_parts[1] if month_part == 'part2' else monthly_parts[0]

    # Pre-calculate active student counts per course in a single query (replaces 68 individual count queries)
    course_student_counts = dict(
        db.session.query(Enrollment.course_id, db.func.count(Enrollment.id))
        .join(Student, Enrollment.student_id == Student.id)
        .filter(
            Enrollment.status.in_(['active', 'trial']),
            Student.status == 'active',
            Enrollment.enroll_date <= month_end
        )
        .group_by(Enrollment.course_id)
        .all()
    )

    # Build teacher_courses_map for client-side dynamic select
    teacher_courses_map = {}
    for t in all_teachers:
        t_c_ids = [ct.course_id for ct in CourseTeacher.query.filter_by(teacher_id=t.id, is_active=True).all()]
        t_courses = Course.query.filter(
            db.or_(
                Course.teacher_id == t.id,
                Course.id.in_(t_c_ids) if t_c_ids else False
            ),
            Course.active == True
        ).order_by(Course.name).all()
        teacher_courses_map[t.id] = [
            {
                'id': c.id,
                'name': c.display_name,
                'full_name': c.full_display_name,
                'room': c.room.name if c.room else '',
                'count': course_student_counts.get(c.id, 0)
            } for c in t_courses
        ]

    # Target teachers
    if selected_teacher_id:
        target_teachers = [t for t in all_teachers if t.id == selected_teacher_id]
    else:
        target_teachers = all_teachers

    total_students_count = 0
    total_classes_count = 0
    matiere_groups_dict = {}

    for t in target_teachers:
        t_courses_meta = teacher_courses_map.get(t.id, [])
        t_course_ids = [c['id'] for c in t_courses_meta]
        
        if selected_course_id:
            if selected_course_id in t_course_ids:
                course_objs = Course.query.filter_by(id=selected_course_id, active=True).all()
            else:
                course_objs = []
        else:
            course_objs = Course.query.filter(Course.id.in_(t_course_ids)).order_by(Course.name).all() if t_course_ids else []

        for c in course_objs:
            c_mat = c.matiere
            if selected_subject and c_mat != selected_subject:
                continue

            enroll_q = Enrollment.query.options(db.joinedload(Enrollment.student)).filter_by(course_id=c.id)
            if status_filter == 'active':
                enroll_q = enroll_q.filter(Enrollment.status.in_(['active', 'trial']))

            enrolls = enroll_q.order_by(Enrollment.id.asc()).all()

            students = []
            for en in enrolls:
                st = en.student
                # 1. Strictly exclude deleted or inactive students
                if not st or st.status != 'active':
                    continue

                if search_q:
                    q_clean = " ".join(search_q.split()).upper()
                    tokens = q_clean.split()
                    target_str = f"{st.first_name or ''} {st.last_name or ''} {st.first_name or ''} {st.code or ''} {st.phone or ''} {st.parent_phone or ''}".upper()
                    if not (q_clean in target_str or (tokens and all(tok in target_str for tok in tokens))):
                        continue

                # 2. Only students enrolled on or before selected month
                en_start = en.enroll_date or (en.created_at.date() if en.created_at else date.today())
                en_end = en.end_date

                if status_filter == 'active':
                    if en.status not in ['active', 'trial']:
                        continue
                    if en_start > month_end:
                        continue
                    if en.is_renewed:
                        continue
                else:
                    if en_start > month_end:
                        continue
                    if en.is_renewed:
                        continue

                students.append({
                    'enrollment': en,
                    'student': st
                })

            students.sort(key=lambda s: (
                (s['student'].last_name or '').upper() if s.get('student') else '',
                (s['student'].first_name or '').upper() if s.get('student') else ''
            ))

            if not search_q or students:
                total_students_count += len(students)
                total_classes_count += 1

                if c_mat not in matiere_groups_dict:
                    cfg = MATIERE_CONFIG.get(c_mat, {})
                    matiere_groups_dict[c_mat] = {
                        'name': c_mat,
                        'icon': cfg.get('icon', '📚'),
                        'color': cfg.get('color', '#0B3D6E'),
                        'bg': cfg.get('bg', '#f8fafc'),
                        'border': cfg.get('border', '#cbd5e1'),
                        'priority': cfg.get('priority', 50),
                        'name_ar': cfg.get('name_ar', c_mat),
                        'total_classes': 0,
                        'total_students': 0,
                        'teacher_blocks_map': {}
                    }

                mg = matiere_groups_dict[c_mat]
                mg['total_classes'] += 1
                mg['total_students'] += len(students)

                if t.id not in mg['teacher_blocks_map']:
                    mg['teacher_blocks_map'][t.id] = {
                        'teacher': t,
                        'classes': [],
                        'total_students': 0,
                        'matiere': c_mat
                    }

                t_block = mg['teacher_blocks_map'][t.id]
                t_block['classes'].append({
                    'course': c,
                    'students': students,
                    'count': len(students),
                    'matiere': c_mat
                })
                t_block['total_students'] += len(students)

    # Sort matiere_groups by priority then name
    sorted_matiere_keys = sorted(
        matiere_groups_dict.keys(),
        key=lambda k: (matiere_groups_dict[k]['priority'], k)
    )

    matiere_groups = []
    class_lists_data = []

    for k in sorted_matiere_keys:
        mg = matiere_groups_dict[k]
        sorted_teacher_blocks = sorted(
            mg['teacher_blocks_map'].values(),
            key=lambda tb: ((tb['teacher'].last_name or '').upper(), (tb['teacher'].first_name or '').upper())
        )
        for tb in sorted_teacher_blocks:
            tb['classes'].sort(key=lambda citem: (citem['course'].name or '').upper())

        mg['teachers'] = sorted_teacher_blocks
        del mg['teacher_blocks_map']
        matiere_groups.append(mg)

        for tb in sorted_teacher_blocks:
            class_lists_data.append(tb)

    # All available matieres with count for filter pills
    all_matieres_counts = {}
    for c_obj in Course.query.filter_by(active=True).all():
        m_name = c_obj.matiere
        all_matieres_counts[m_name] = all_matieres_counts.get(m_name, 0) + 1

    all_matieres = []
    for m_name in sorted(all_matieres_counts.keys(), key=lambda x: (get_matiere_priority(x), x)):
        cfg = MATIERE_CONFIG.get(m_name, {})
        all_matieres.append({
            'name': m_name,
            'icon': cfg.get('icon', '📚'),
            'color': cfg.get('color', '#0B3D6E'),
            'count': all_matieres_counts[m_name]
        })

    if selected_teacher_id and selected_teacher_id in teacher_courses_map:
        current_teacher_courses = teacher_courses_map[selected_teacher_id]
    else:
        current_teacher_courses = []

    return render_template('teachers/class_lists.html',
                           all_teachers=all_teachers,
                           selected_teacher_id=selected_teacher_id,
                           selected_course_id=selected_course_id,
                           selected_subject=selected_subject,
                           current_teacher_courses=current_teacher_courses,
                           teacher_courses_map=teacher_courses_map,
                           class_lists_data=class_lists_data,
                           matiere_groups=matiere_groups,
                           all_matieres=all_matieres,
                           status_filter=status_filter,
                           search_q=search_q,
                           sheet_type=sheet_type,
                           req_month=req_month,
                           month_name_fr=month_name_fr,
                           today_month=today_month,
                           last_day=last_day,
                           month_part=month_part,
                           monthly_parts=monthly_parts,
                           active_monthly_part=active_monthly_part,
                           week_days=week_days,
                           week_label_fr=week_label_fr,
                           current_week_date=current_week_date,
                           prev_week_date=prev_week_date,
                           next_week_date=next_week_date,
                           monday=monday,
                           sunday=sunday,
                           total_students_count=total_students_count,
                           total_classes_count=total_classes_count,
                           today=date.today())



@app.route('/teachers/class-lists/print')
@login_required
@role_required('admin', 'secretary')
def teacher_class_lists_print():
    u = current_user()
    all_teachers = Teacher.query.filter_by(active=True).all()
    all_teachers.sort(key=lambda t: (get_matiere_priority(t.primary_matiere), t.primary_matiere, (t.last_name or '').upper(), (t.first_name or '').upper()))

    if u and u.role == 'teacher':
        t_id = u.teacher_id
        if not t_id:
            matched_t = Teacher.query.filter_by(full_name=u.full_name).first()
            t_id = matched_t.id if matched_t else None
        selected_teacher_id = t_id
    else:
        selected_teacher_id = _int(request.args.get('teacher_id'))

    selected_course_id = _int(request.args.get('course_id'))
    selected_subject = request.args.get('subject', '').strip()
    status_filter = request.args.get('status', 'active')
    search_q = request.args.get('q', '').strip()
    sheet_type = request.args.get('sheet_type', 'attendance')
    if sheet_type not in ['attendance', 'weekly', 'monthly', 'simple']:
        sheet_type = 'attendance'
    fmt = request.args.get('format', 'a4_portrait' if sheet_type == 'simple' else 'a4_landscape')
    sessions_count = _int(request.args.get('sessions_count', 8)) or 8

    today_month = date.today().strftime('%Y-%m')
    req_month = request.args.get('month') or today_month
    try:
        y, m = map(int, req_month.split('-'))
    except Exception:
        y, m = date.today().year, date.today().month
        req_month = today_month

    months_fr = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
        7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }
    month_name_fr = f"{months_fr.get(m, 'Mois')} {y}"
    month_start = date(y, m, 1)
    _, last_day = calendar.monthrange(y, m)
    month_end = date(y, m, last_day)

    # Week calculation for attendance sheets (Dates of week: Lundi - Dimanche)
    req_week_date = request.args.get('week_date')
    ref_date = None
    if req_week_date:
        ref_date = parse_date(req_week_date)

    if not ref_date:
        today_dt = date.today()
        if today_dt.year == y and today_dt.month == m:
            ref_date = today_dt
        else:
            ref_date = month_start

    # Monday of that week
    monday = ref_date - timedelta(days=ref_date.weekday())
    sunday = monday + timedelta(days=6)

    day_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    day_names_short_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    day_names_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']

    week_days = []
    for i in range(7):
        cur_d = monday + timedelta(days=i)
        week_days.append({
            'index': i,
            'name': day_names_fr[i],
            'short_name': day_names_short_fr[i],
            'name_ar': day_names_ar[i],
            'date': cur_d,
            'date_str': cur_d.strftime('%d/%m'),
            'full_date_str': cur_d.strftime('%d/%m/%Y'),
            'iso_date': cur_d.strftime('%Y-%m-%d'),
            'in_month': (cur_d.year == y and cur_d.month == m)
        })

    prev_week_date = (monday - timedelta(days=7)).strftime('%Y-%m-%d')
    next_week_date = (monday + timedelta(days=7)).strftime('%Y-%m-%d')
    current_week_date = monday.strftime('%Y-%m-%d')
    week_label_fr = f"Semaine du {monday.strftime('%d/%m/%Y')} au {sunday.strftime('%d/%m/%Y')}"

    # Month days & 2 parts (Part 1: 01 to 15, Part 2: 16 to end of month)
    all_month_days = []
    for d in range(1, last_day + 1):
        cur_d = date(y, m, d)
        w_idx = cur_d.weekday()
        all_month_days.append({
            'day_num': d,
            'weekday_index': w_idx,
            'name': day_names_fr[w_idx],
            'short_name': day_names_short_fr[w_idx],
            'name_ar': day_names_ar[w_idx],
            'date': cur_d,
            'date_str': cur_d.strftime('%d/%m'),
            'day_str': f"{d:02d}",
            'full_date_str': cur_d.strftime('%d/%m/%Y'),
            'iso_date': cur_d.strftime('%Y-%m-%d'),
        })

    part1_days = [d for d in all_month_days if d['day_num'] <= 15]
    part2_days = [d for d in all_month_days if d['day_num'] >= 16]

    monthly_parts = [
        {
            'part_num': 1,
            'part_key': 'part1',
            'title': f"1ère Quinzaine (Du 01 au 15 {month_name_fr})",
            'short_title': "Partie 1 (01 au 15)",
            'days': part1_days,
            'start_day': 1,
            'end_day': 15,
            'range_str': f"Du 01/{m:02d}/{y} au 15/{m:02d}/{y}",
            'days_count': len(part1_days)
        },
        {
            'part_num': 2,
            'part_key': 'part2',
            'title': f"2ème Quinzaine (Du 16 au {last_day:02d} {month_name_fr})",
            'short_title': f"Partie 2 (16 au {last_day:02d})",
            'days': part2_days,
            'start_day': 16,
            'end_day': last_day,
            'range_str': f"Du 16/{m:02d}/{y} au {last_day:02d}/{m:02d}/{y}",
            'days_count': len(part2_days)
        }
    ]

    month_part = request.args.get('month_part', 'both')
    if month_part == 'part1':
        monthly_parts_to_render = [monthly_parts[0]]
    elif month_part == 'part2':
        monthly_parts_to_render = [monthly_parts[1]]
    else:
        month_part = 'both'
        monthly_parts_to_render = monthly_parts

    if selected_teacher_id:
        target_teachers = [t for t in all_teachers if t.id == selected_teacher_id]
    else:
        target_teachers = all_teachers

    matiere_groups_dict = {}

    for t in target_teachers:
        t_c_ids = [ct.course_id for ct in CourseTeacher.query.filter_by(teacher_id=t.id, is_active=True).all()]
        t_courses = Course.query.filter(
            db.or_(
                Course.teacher_id == t.id,
                Course.id.in_(t_c_ids) if t_c_ids else False
            ),
            Course.active == True
        ).order_by(Course.name).all()

        if selected_course_id:
            course_objs = [c for c in t_courses if c.id == selected_course_id]
        else:
            course_objs = t_courses

        for c in course_objs:
            c_mat = c.matiere
            if selected_subject and c_mat != selected_subject:
                continue

            enroll_q = Enrollment.query.filter_by(course_id=c.id)
            if status_filter == 'active':
                enroll_q = enroll_q.filter(Enrollment.status.in_(['active', 'trial']))

            enrolls = enroll_q.order_by(Enrollment.id.asc()).all()

            students = []
            for en in enrolls:
                st = en.student
                # 1. Strictly exclude non-existent, inactive or deleted student
                if not st or st.status != 'active':
                    continue

                if search_q:
                    q_clean = " ".join(search_q.split()).upper()
                    tokens = q_clean.split()
                    target_str = f"{st.first_name or ''} {st.last_name or ''} {st.first_name or ''} {st.code or ''} {st.phone or ''} {st.parent_phone or ''}".upper()
                    if not (q_clean in target_str or (tokens and all(tok in target_str for tok in tokens))):
                        continue

                # 2. Only students enrolled on or before selected month
                en_start = en.enroll_date or (en.created_at.date() if en.created_at else date.today())
                en_end = en.end_date

                if status_filter == 'active':
                    if en.status not in ['active', 'trial']:
                        continue
                    if en_start > month_end:
                        continue
                    if en.is_renewed:
                        continue
                else:
                    if en_start > month_end:
                        continue
                    if en.is_renewed:
                        continue

                students.append({
                    'enrollment': en,
                    'student': st
                })

            students.sort(key=lambda s: (
                (s['student'].last_name or '').upper() if s.get('student') else '',
                (s['student'].first_name or '').upper() if s.get('student') else ''
            ))

            if students:
                if c_mat not in matiere_groups_dict:
                    cfg = MATIERE_CONFIG.get(c_mat, {})
                    matiere_groups_dict[c_mat] = {
                        'name': c_mat,
                        'icon': cfg.get('icon', '📚'),
                        'color': cfg.get('color', '#0B3D6E'),
                        'bg': cfg.get('bg', '#f8fafc'),
                        'border': cfg.get('border', '#cbd5e1'),
                        'priority': cfg.get('priority', 50),
                        'name_ar': cfg.get('name_ar', c_mat),
                        'total_classes': 0,
                        'total_students': 0,
                        'teacher_blocks_map': {}
                    }

                mg = matiere_groups_dict[c_mat]
                mg['total_classes'] += 1
                mg['total_students'] += len(students)

                if t.id not in mg['teacher_blocks_map']:
                    mg['teacher_blocks_map'][t.id] = {
                        'teacher': t,
                        'classes': [],
                        'total_students': 0,
                        'matiere': c_mat
                    }

                t_block = mg['teacher_blocks_map'][t.id]
                t_block['classes'].append({
                    'course': c,
                    'students': students,
                    'count': len(students),
                    'matiere': c_mat
                })
                t_block['total_students'] += len(students)

    # Sort matiere_groups by priority then name
    sorted_matiere_keys = sorted(
        matiere_groups_dict.keys(),
        key=lambda k: (matiere_groups_dict[k]['priority'], k)
    )

    matiere_groups = []
    class_lists_data = []

    for k in sorted_matiere_keys:
        mg = matiere_groups_dict[k]
        sorted_teacher_blocks = sorted(
            mg['teacher_blocks_map'].values(),
            key=lambda tb: ((tb['teacher'].last_name or '').upper(), (tb['teacher'].first_name or '').upper())
        )
        for tb in sorted_teacher_blocks:
            tb['classes'].sort(key=lambda citem: (citem['course'].name or '').upper())

        mg['teachers'] = sorted_teacher_blocks
        del mg['teacher_blocks_map']
        matiere_groups.append(mg)

        for tb in sorted_teacher_blocks:
            class_lists_data.append(tb)

    # All available matieres with count for filter pills
    all_matieres_counts = {}
    for c_obj in Course.query.filter_by(active=True).all():
        m_name = c_obj.matiere
        all_matieres_counts[m_name] = all_matieres_counts.get(m_name, 0) + 1

    all_matieres = []
    for m_name in sorted(all_matieres_counts.keys(), key=lambda x: (get_matiere_priority(x), x)):
        cfg = MATIERE_CONFIG.get(m_name, {})
        all_matieres.append({
            'name': m_name,
            'icon': cfg.get('icon', '📚'),
            'color': cfg.get('color', '#0B3D6E'),
            'count': all_matieres_counts[m_name]
        })

    # Build attendance lookup map: (course_id, student_id, date_iso) -> status
    # Collect all dates that need to be checked (week dates for attendance/weekly, month dates for monthly)
    attendance_map = {}
    if class_lists_data:
        # Determine all dates to look up
        check_dates = []
        if sheet_type == 'attendance':
            check_dates = [wd['date'] for wd in week_days]
        else:
            check_dates = [d['date'] for d in all_month_days]

        if check_dates:
            date_start = min(check_dates)
            date_end = max(check_dates)
            # Collect all course_ids and student_ids involved
            all_course_ids = []
            all_student_ids = []
            for tdata in class_lists_data:
                for cdata in tdata['classes']:
                    all_course_ids.append(cdata['course'].id)
                    for sdata in cdata['students']:
                        all_student_ids.append(sdata['student'].id)

            if all_course_ids and all_student_ids:
                att_records = Attendance.query.filter(
                    Attendance.course_id.in_(all_course_ids),
                    Attendance.student_id.in_(all_student_ids),
                    Attendance.date >= date_start,
                    Attendance.date <= date_end
                ).all()
                for att in att_records:
                    key = (att.course_id, att.student_id, att.date.strftime('%Y-%m-%d'))
                    attendance_map[key] = att.status

    return render_template('teachers/class_lists_print.html',
                           class_lists_data=class_lists_data,
                           matiere_groups=matiere_groups,
                           all_matieres=all_matieres,
                           selected_subject=selected_subject,
                           selected_teacher_id=selected_teacher_id,
                           selected_course_id=selected_course_id,
                           status_filter=status_filter,
                           sheet_type=sheet_type,
                           fmt=fmt,
                           sessions_count=sessions_count,
                           req_month=req_month,
                           month_name_fr=month_name_fr,
                           last_day=last_day,
                           month_part=month_part,
                           monthly_parts=monthly_parts,
                           monthly_parts_to_render=monthly_parts_to_render,
                           week_days=week_days,
                           week_label_fr=week_label_fr,
                           current_week_date=current_week_date,
                           prev_week_date=prev_week_date,
                           next_week_date=next_week_date,
                           monday=monday,
                           sunday=sunday,
                           attendance_map=attendance_map,
                           today=date.today())



@app.route('/teachers/class-lists/remove-student/<int:eid>', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def teacher_class_lists_remove_student(eid):
    e = db.session.get(Enrollment, eid)
    if not e:
        flash('Inscription introuvable', 'danger')
        return redirect(url_for('teacher_class_lists'))

    stu = e.student
    course = e.course
    stu_name = stu.full_name if stu else f"Élève #{e.student_id}"
    course_name = course.display_name if course else f"Classe #{e.course_id}"

    e.status = 'dropped'
    u = current_user()
    user_label = u.username if u else 'admin'
    e.notes = (e.notes or '') + f"\nRetiré manuellement de la liste de classe le {date.today().strftime('%d/%m/%Y')} par {user_label}."

    if e.student_id:
        remaining_active = Enrollment.query.filter_by(student_id=e.student_id, status='active').filter(Enrollment.id != e.id).count()
        if remaining_active == 0:
            orphan_transfers = Enrollment.query.filter_by(student_id=e.student_id, status='transferred').all()
            for ot in orphan_transfers:
                ot.status = 'dropped'
                ot.notes = (ot.notes or '') + f"\n[Retiré - L'élève a été retiré de la classe #{e.course_id} le {date.today().strftime('%d/%m/%Y')} par {user_label}]."

    db.session.commit()
    log_action('enrollment_dropped', f"Retrait de {stu_name} de {course_name} depuis la liste de classe")

    flash(f"L'élève {stu_name} a été retiré(e) de la classe {course_name} avec succès.", 'warning')

    redirect_url = request.form.get('redirect_url')
    if redirect_url and redirect_url.startswith('/'):
        return redirect(redirect_url)
    return redirect(request.referrer or url_for('teacher_class_lists'))


@app.route('/teachers/class-lists/restore-student/<int:eid>', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def teacher_class_lists_restore_student(eid):
    e = db.session.get(Enrollment, eid)
    if not e:
        flash('Inscription introuvable', 'danger')
        return redirect(url_for('teacher_class_lists'))

    stu = e.student
    course = e.course
    stu_name = stu.full_name if stu else f"Élève #{e.student_id}"
    course_name = course.display_name if course else f"Classe #{e.course_id}"

    e.status = 'active'
    u = current_user()
    user_label = u.username if u else 'admin'
    e.notes = (e.notes or '') + f"\nRéintégré dans la liste de classe le {date.today().strftime('%d/%m/%Y')} par {user_label}."
    db.session.commit()
    log_action('enrollment_restored', f"Réintégration de {stu_name} dans {course_name}")

    flash(f"L'élève {stu_name} a été réintégré(e) dans la classe {course_name} avec succès.", 'success')

    redirect_url = request.form.get('redirect_url')
    if redirect_url and redirect_url.startswith('/'):
        return redirect(redirect_url)
    return redirect(request.referrer or url_for('teacher_class_lists'))


# ---------------------------------------------------------------------------
# Achats & Charges Management (Purchases & Operating Expenses)
# ---------------------------------------------------------------------------
ACHAT_CATEGORIES = [
    'Fournitures & Papeterie',
    'Manuels & Livres',
    'Matériel Informatique & Multimédia',
    'Mobilier & Aménagement',
    'Produits Hygiène & Entretien',
    'Matériel Pédagogique',
    'Divers Achats'
]

CHARGE_CATEGORIES = [
    'Loyer des locaux',
    'Électricité & Eau',
    'Télécom & Internet',
    'Salaires & Primes',
    'Avances sur salaires',
    'Vacations Enseignants / Formateurs',
    'Honoraires Comptable / Fiduciaire',
    'Maintenance & Réparations',
    'Publicité & Marketing',
    'Assurance & Frais bancaires',
    'Taxes & Impôts',
    'Transport & Déplacements',
    'Diverses Charges'
]

ALL_EXPENSE_CATEGORIES = ACHAT_CATEGORIES + CHARGE_CATEGORIES


@app.route('/expenses')
@login_required
@role_required('admin', 'secretary')
def expenses():
    tab = request.args.get('tab', 'all').strip().lower()
    req_month = request.args.get('month', '').strip()
    selected_category = request.args.get('category', '').strip()
    selected_type = request.args.get('type', '').strip()
    selected_status = request.args.get('status', '').strip()
    selected_supplier = _int(request.args.get('supplier_id'))
    search_q = request.args.get('q', '').strip()

    # Restrict recurring charges and PnL tabs to admin only
    cur_u = current_user()
    if cur_u and cur_u.role != 'admin' and tab in ['recurring', 'pnl']:
        tab = 'all'

    # Default to current month if no month and not on suppliers tab
    if not req_month and tab != 'suppliers':
        req_month = date.today().strftime('%Y-%m')

    query = Expense.query

    # Period filtering
    y, m = date.today().year, date.today().month
    if req_month:
        try:
            y, m = map(int, req_month.split('-'))
            query = query.filter(
                db.extract('year', Expense.date) == y,
                db.extract('month', Expense.date) == m
            )
        except Exception:
            y, m = date.today().year, date.today().month
            req_month = f"{y:04d}-{m:02d}"
            query = query.filter(
                db.extract('year', Expense.date) == y,
                db.extract('month', Expense.date) == m
            )

    # Tab shortcut filtering
    if tab == 'achats':
        query = query.filter(Expense.expense_type == 'achat')
    elif tab == 'charges':
        query = query.filter(Expense.expense_type == 'charge')
    elif tab == 'pending':
        query = query.filter(Expense.status.in_(['unpaid', 'partial']))

    # Direct filters
    if selected_type:
        query = query.filter(Expense.expense_type == selected_type)

    if selected_category:
        query = query.filter(Expense.category == selected_category)

    if selected_status:
        if selected_status == 'overdue':
            query = query.filter(Expense.status != 'paid', Expense.due_date < date.today())
        else:
            query = query.filter(Expense.status == selected_status)

    if selected_supplier:
        query = query.filter(Expense.supplier_id == selected_supplier)

    if search_q:
        search_like = f"%{search_q}%"
        query = query.filter(
            db.or_(
                Expense.description.ilike(search_like),
                Expense.reference_no.ilike(search_like),
                Expense.invoice_no.ilike(search_like),
                Expense.supplier_name.ilike(search_like),
                Expense.category.ilike(search_like)
            )
        )

    expense_list = query.order_by(Expense.date.desc(), Expense.id.desc()).all()

    # Statistics for the selected month (or total if all)
    month_query = Expense.query
    if req_month:
        month_query = month_query.filter(
            db.extract('year', Expense.date) == y,
            db.extract('month', Expense.date) == m
        )
    all_period_expenses = month_query.all()

    total_expenses_month = sum((e.amount or 0.0) for e in all_period_expenses)
    total_achats_month = sum((e.amount or 0.0) for e in all_period_expenses if e.expense_type == 'achat')
    total_charges_month = sum((e.amount or 0.0) for e in all_period_expenses if e.expense_type == 'charge')
    total_pending_month = sum(e.remaining_balance for e in all_period_expenses if e.status in ['unpaid', 'partial'])
    total_paid_month = sum(((e.paid_amount or 0.0) if e.status == 'partial' else ((e.amount or 0.0) if e.status == 'paid' else 0.0)) for e in all_period_expenses)

    # Breakdown by category
    category_totals = {}
    for e in all_period_expenses:
        category_totals[e.category] = category_totals.get(e.category, 0.0) + (e.amount or 0.0)

    sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    top_cat = sorted_cats[0][0] if sorted_cats else None
    top_cat_amount = sorted_cats[0][1] if sorted_cats else 0.0

    # P&L / Bilan calculation for this month
    rev_tuition = (db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))
                   .filter(db.extract('year', Payment.date) == y, db.extract('month', Payment.date) == m).scalar() or 0.0)
    month_book_sales_pnl = BookSale.query.filter(
        db.extract('year', BookSale.sale_date) == y,
        db.extract('month', BookSale.sale_date) == m
    ).all()
    gross_books_pnl = round(sum((b.total_amount or 0.0) for b in month_book_sales_pnl), 2)
    teacher_books_due_pnl = round(sum((b.teacher_earned or 0.0) for b in month_book_sales_pnl), 2)
    rev_books = round(sum(
        ((b.school_earned if b.teacher_id is not None else b.total_amount) or 0.0)
        for b in month_book_sales_pnl
    ), 2)
    total_revenue_month = rev_tuition + rev_books
    net_profit_month = total_revenue_month - total_expenses_month
    profit_margin = round((net_profit_month / total_revenue_month * 100), 1) if total_revenue_month > 0 else 0.0

    pnl_data = {
        'rev_tuition': rev_tuition,
        'rev_books': rev_books,
        'gross_books': gross_books_pnl,
        'teacher_books_due': teacher_books_due_pnl,
        'rev_total': total_revenue_month,
        'total_achats': total_achats_month,
        'total_charges': total_charges_month,
        'total_expenses': total_expenses_month,
        'net_profit': net_profit_month,
        'profit_margin': profit_margin,
        'category_breakdown': sorted_cats
    }

    suppliers = Supplier.query.filter_by(active=True).order_by(Supplier.name.asc()).all()
    employees = Employee.query.filter_by(active=True).order_by(Employee.last_name.asc()).all()

    # Recurring charges metrics & mapping for req_month
    recurring_charges = RecurringCharge.query.order_by(RecurringCharge.active.desc(), RecurringCharge.day_of_month.asc(), RecurringCharge.id.asc()).all()

    period_recurring_expenses = Expense.query.filter(
        Expense.recurring_charge_id.isnot(None)
    ).filter(
        db.or_(
            Expense.recurring_month == req_month,
            db.and_(db.extract('year', Expense.date) == y, db.extract('month', Expense.date) == m)
        )
    ).all()

    generated_rc_map = {e.recurring_charge_id: e for e in period_recurring_expenses if e.recurring_charge_id}

    recurring_items_data = []
    pending_recurring_count = 0
    pending_recurring_amount = 0.0
    validated_recurring_count = 0
    validated_recurring_amount = 0.0
    total_recurring_monthly = 0.0

    for rc in recurring_charges:
        gen_exp = generated_rc_map.get(rc.id)
        is_gen = (gen_exp is not None)
        if rc.active:
            total_recurring_monthly += (rc.amount or 0.0)
            if is_gen:
                validated_recurring_count += 1
                validated_recurring_amount += (gen_exp.amount or 0.0)
            else:
                pending_recurring_count += 1
                pending_recurring_amount += (rc.amount or 0.0)

        recurring_items_data.append({
            'rc': rc,
            'is_validated': is_gen,
            'generated_expense': gen_exp
        })

    months_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    month_name_fr = f"{months_fr[m]} {y}" if (1 <= m <= 12) else req_month

    # Real Cash Count on hand (Pointage Caisse Réelle pour Analytics & Bilan)
    real_cash_val = SH.get_setting(f"real_cash_amount_{req_month}", "")
    real_cash_amount = float(real_cash_val) if real_cash_val not in ['', None] else None
    real_cash_note = SH.get_setting(f"real_cash_note_{req_month}", "")
    real_cash_date = SH.get_setting(f"real_cash_date_{req_month}", "")
    real_cash_by = SH.get_setting(f"real_cash_by_{req_month}", "")

    # Teachers payroll for requested month
    start_d_exp = date(y, m, 1)
    _, last_day_exp = calendar.monthrange(y, m)
    end_d_exp = date(y, m, last_day_exp)
    _, grand_teacher_payroll_exp = _calculate_period_teacher_payroll(start_d_exp, end_d_exp)
    t_payouts_exp = TeacherSalaryPayout.query.filter_by(period_month=req_month, status='paid').all()
    t_paid_exp = sum((p.net_amount or 0.0) for p in t_payouts_exp)
    pending_teacher_payroll = max(0.0, round(grand_teacher_payroll_exp - t_paid_exp, 2))

    # Pending supplier debts for non-fixed expenses in this month
    pending_supplier_debts = round(total_pending_month, 2)

    # Total of all pending charges to be paid (Fixed + Teachers + Non-fixed debts)
    total_pending_all_charges = round(pending_recurring_amount + pending_teacher_payroll + pending_supplier_debts, 2)
    total_month_all_charges = round(total_expenses_month + pending_recurring_amount + pending_teacher_payroll, 2)

    theoretical_cash = net_profit_month
    if real_cash_amount is not None:
        effective_cash = real_cash_amount
        ecart_caisse = round(theoretical_cash - real_cash_amount, 2)
        projected_bilan_net = round(effective_cash - total_pending_all_charges, 2)
        is_real_cash_used = True
    else:
        effective_cash = theoretical_cash
        ecart_caisse = 0.0
        projected_bilan_net = round(theoretical_cash - total_pending_all_charges, 2)
        is_real_cash_used = False

    real_cash_data = {
        'amount': real_cash_amount,
        'note': real_cash_note,
        'date': real_cash_date,
        'by': real_cash_by,
        'theoretical_cash': theoretical_cash,
        'ecart': ecart_caisse,
        'effective_cash': effective_cash,
        'pending_recurring_amount': pending_recurring_amount,
        'grand_teacher_payroll': grand_teacher_payroll_exp,
        'paid_teacher_payroll': t_paid_exp,
        'pending_teacher_payroll': pending_teacher_payroll,
        'pending_supplier_debts': pending_supplier_debts,
        'total_pending_all_charges': total_pending_all_charges,
        'total_month_all_charges': total_month_all_charges,
        'projected_bilan_net': projected_bilan_net,
        'is_used': is_real_cash_used
    }

    # Update pnl_data with real cash fields and comprehensive charges
    pnl_data['theoretical_cash'] = theoretical_cash
    pnl_data['real_cash_amount'] = real_cash_amount
    pnl_data['real_cash_note'] = real_cash_note
    pnl_data['real_cash_date'] = real_cash_date
    pnl_data['ecart_caisse'] = ecart_caisse
    pnl_data['effective_cash'] = effective_cash
    pnl_data['pending_recurring_amount'] = pending_recurring_amount
    pnl_data['grand_teacher_payroll'] = grand_teacher_payroll_exp
    pnl_data['paid_teacher_payroll'] = t_paid_exp
    pnl_data['pending_teacher_payroll'] = pending_teacher_payroll
    pnl_data['pending_supplier_debts'] = pending_supplier_debts
    pnl_data['total_pending_all_charges'] = total_pending_all_charges
    pnl_data['total_month_all_charges'] = total_month_all_charges
    pnl_data['projected_bilan_net'] = projected_bilan_net
    pnl_data['is_real_cash_used'] = is_real_cash_used

    return render_template('expenses.html',
                           expenses=expense_list,
                           suppliers=suppliers,
                           employees=employees,
                           recurring_charges=recurring_charges,
                           recurring_items_data=recurring_items_data,
                           pending_recurring_count=pending_recurring_count,
                           pending_recurring_amount=pending_recurring_amount,
                           validated_recurring_count=validated_recurring_count,
                           validated_recurring_amount=validated_recurring_amount,
                           total_recurring_monthly=total_recurring_monthly,
                           month_name_fr=month_name_fr,
                           tab=tab,
                           req_month=req_month,
                           selected_category=selected_category,
                           selected_type=selected_type,
                           selected_status=selected_status,
                           selected_supplier=selected_supplier,
                           search_q=search_q,
                           achat_categories=ACHAT_CATEGORIES,
                           charge_categories=CHARGE_CATEGORIES,
                           categories=ALL_EXPENSE_CATEGORIES,
                           total_expenses_month=total_expenses_month,
                           total_achats_month=total_achats_month,
                           total_charges_month=total_charges_month,
                           total_pending_month=total_pending_month,
                           total_paid_month=total_paid_month,
                           top_category=top_cat,
                           top_category_amount=top_cat_amount,
                           sorted_categories=sorted_cats,
                           pnl=pnl_data,
                           real_cash_data=real_cash_data)


@app.route('/expenses/real-cash/save', methods=['POST'])
@login_required
@role_required('admin')
def expense_real_cash_save():
    req_month = request.form.get('month', date.today().strftime('%Y-%m')).strip()
    raw_amount = request.form.get('amount', '').strip()
    note = request.form.get('note', '').strip()
    action = request.form.get('action', 'save').strip()
    redirect_tab = request.form.get('tab', 'charges').strip()

    if action == 'clear':
        SH.set_setting(f"real_cash_amount_{req_month}", "")
        SH.set_setting(f"real_cash_note_{req_month}", "")
        SH.set_setting(f"real_cash_date_{req_month}", "")
        SH.set_setting(f"real_cash_by_{req_month}", "")
        db.session.commit()
        SH.invalidate_cache()
        log_action('CASH_REAL_RESET', f"Réinitialisation du cash réel pour {req_month}")
        flash('Le relevé physique de caisse a été réinitialisé. Les calculs se basent désormais sur le théorique système.', 'info')
    else:
        try:
            clean_amt = raw_amount.replace(' ', '').replace(',', '.')
            amt = round(float(clean_amt), 2)
            u = current_user()
            user_label = u.full_name or u.username if u else 'Admin'
            SH.set_setting(f"real_cash_amount_{req_month}", str(amt))
            SH.set_setting(f"real_cash_note_{req_month}", note)
            SH.set_setting(f"real_cash_date_{req_month}", datetime.now().strftime('%d/%m/%Y à %H:%M'))
            SH.set_setting(f"real_cash_by_{req_month}", user_label)
            db.session.commit()
            SH.invalidate_cache()
            log_action('CASH_REAL_UPDATE', f"Mise à jour du cash physique réel pour {req_month} : {amt} DH ({note})")
            flash(f"✅ Montant de caisse physique ({amt:.2f} DH) enregistré pour {req_month}. Le Bilan ('فين واصلين') a été ajusté avec précision.", 'success')
        except (ValueError, TypeError):
            flash('Montant invalide. Veuillez saisir un nombre valide.', 'danger')

    return redirect(url_for('expenses', tab=redirect_tab, month=req_month))


@app.route('/expenses/add', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def expense_add():
    d = request.form
    expense_type = d.get('expense_type', 'charge').strip()
    category = d.get('category', 'Divers').strip()
    description = d.get('description', '').strip()
    amount = _f(d.get('amount'))
    exp_date = parse_date(d.get('date')) or date.today()
    due_date = parse_date(d.get('due_date'))
    payment_method = d.get('payment_method', 'Espèces').strip()
    reference_no = d.get('reference_no', '').strip()
    invoice_no = d.get('invoice_no', '').strip()
    supplier_id = _int(d.get('supplier_id'))
    supplier_name = d.get('supplier_name', '').strip()
    status = d.get('status', 'paid').strip()
    tax_amount = _f(d.get('tax_amount'))
    notes = d.get('notes', '').strip()

    if supplier_id:
        sup = Supplier.query.get(supplier_id)
        if sup:
            supplier_name = sup.name

    if not description or amount <= 0:
        flash('Veuillez remplir correctement la description et le montant (supérieur à 0).', 'danger')
        return redirect(url_for('expenses'))

    if status == 'paid':
        paid_amount = amount
    elif status == 'unpaid':
        paid_amount = 0.0
    else:
        paid_amount = min(amount, _f(d.get('paid_amount')))

    receipt_fn = None
    if 'receipt_file' in request.files:
        f = request.files['receipt_file']
        if f and f.filename:
            ext = os.path.splitext(f.filename)[1].lower()
            if ext in ['.pdf', '.jpg', '.jpeg', '.png', '.webp']:
                receipt_fn = f"exp_{int(datetime.utcnow().timestamp())}_{secure_filename(f.filename)}"
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], receipt_fn))

    u = current_user()
    teacher_id = _int(d.get('teacher_id'))
    deduct_teacher = d.get('deduct_teacher') == '1' or 'deduct_teacher' in d

    exp = Expense(
        expense_type=expense_type,
        category=category,
        description=description,
        amount=amount,
        date=exp_date,
        due_date=due_date,
        payment_method=payment_method,
        reference_no=reference_no,
        invoice_no=invoice_no,
        supplier_id=supplier_id if supplier_id else None,
        supplier_name=supplier_name,
        teacher_id=teacher_id if teacher_id else None,
        status=status,
        paid_amount=paid_amount,
        tax_amount=tax_amount,
        receipt_file=receipt_fn,
        notes=notes,
        user_id=u.id if u else None
    )
    db.session.add(exp)
    db.session.flush()

    # Link to TeacherExpense if deducted on teacher salary
    if teacher_id and deduct_teacher:
        teacher = Teacher.query.get(teacher_id)
        if teacher:
            period_month = d.get('period_month', '').strip() or exp_date.strftime('%Y-%m')
            quantity = _int(d.get('copy_quantity')) or 1
            unit_price = _f(d.get('copy_unit_price')) or (amount / quantity if quantity else amount)
            t_type = 'copies' if ('copie' in description.lower() or 'copie' in category.lower() or 'tirage' in description.lower()) else 'other'
            y, m = exp_date.year, exp_date.month
            prefix = f"EXP-T-{y:04d}{m:02d}-"
            seq = TeacherExpense.query.count() + 1
            rec_no = f"{prefix}{seq:04d}"

            t_exp = TeacherExpense(
                receipt_no=rec_no,
                teacher_id=teacher.id,
                expense_type=t_type,
                title=description,
                unit_price=unit_price,
                quantity=quantity,
                amount=amount,
                date=exp_date,
                period_month=period_month,
                payment_method='Retenue sur salaire',
                status='pending',
                expense_id=exp.id,
                notes=f"Créé depuis Achats & Charges. {notes}".strip(),
                recorded_by=u.id if u else None
            )
            db.session.add(t_exp)
            db.session.flush()
            exp.teacher_expense_id = t_exp.id

    db.session.commit()

    type_label = "Achat" if expense_type == 'achat' else "Charge"
    log_action('expense_add', f"{type_label} [{category}]: {description} - {amount:.2f} DH ({status})")
    flash(f"{type_label} enregistré(e) avec succès ({amount:.2f} DH).", 'success')
    return redirect(url_for('expenses'))


@app.route('/expenses/<int:eid>/edit', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def expense_edit(eid):
    exp = Expense.query.get_or_404(eid)
    d = request.form
    exp.expense_type = d.get('expense_type', exp.expense_type).strip()
    exp.category = d.get('category', exp.category).strip()
    exp.description = d.get('description', exp.description).strip()
    exp.amount = _f(d.get('amount'))
    exp.date = parse_date(d.get('date')) or exp.date
    exp.due_date = parse_date(d.get('due_date'))
    exp.payment_method = d.get('payment_method', exp.payment_method).strip()
    exp.reference_no = d.get('reference_no', '').strip()
    exp.invoice_no = d.get('invoice_no', '').strip()
    supplier_id = _int(d.get('supplier_id'))
    exp.supplier_id = supplier_id if supplier_id else None
    if supplier_id:
        sup = Supplier.query.get(supplier_id)
        if sup:
            exp.supplier_name = sup.name
    else:
        exp.supplier_name = d.get('supplier_name', '').strip()

    status = d.get('status', 'paid').strip()
    exp.status = status
    if status == 'paid':
        exp.paid_amount = exp.amount
    elif status == 'unpaid':
        exp.paid_amount = 0.0
    else:
        exp.paid_amount = min(exp.amount, _f(d.get('paid_amount')))

    exp.tax_amount = _f(d.get('tax_amount'))
    exp.notes = d.get('notes', '').strip()

    if 'receipt_file' in request.files:
        f = request.files['receipt_file']
        if f and f.filename:
            ext = os.path.splitext(f.filename)[1].lower()
            if ext in ['.pdf', '.jpg', '.jpeg', '.png', '.webp']:
                receipt_fn = f"exp_{int(datetime.utcnow().timestamp())}_{secure_filename(f.filename)}"
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], receipt_fn))
                exp.receipt_file = receipt_fn

    db.session.commit()
    log_action('expense_edit', f"Modification dépense #{exp.id}: {exp.description} - {exp.amount:.2f} DH")
    flash('Opération mise à jour avec succès.', 'success')
    return redirect(url_for('expenses'))


@app.route('/expenses/<int:eid>/pay', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def expense_pay(eid):
    exp = Expense.query.get_or_404(eid)
    pay_amt = _f(request.form.get('pay_amount'))
    if pay_amt <= 0:
        flash('Veuillez saisir un montant de règlement valide.', 'danger')
        return redirect(url_for('expenses'))

    current_paid = exp.paid_amount or 0.0
    new_paid = current_paid + pay_amt
    exp.paid_amount = round(new_paid, 2)

    if exp.paid_amount >= exp.amount:
        exp.status = 'paid'
        exp.paid_amount = exp.amount
    else:
        exp.status = 'partial'

    db.session.commit()
    log_action('expense_pay', f"Règlement #{exp.id}: +{pay_amt:.2f} DH pour {exp.description}")
    flash(f"Règlement de {pay_amt:.2f} DH enregistré avec succès.", 'success')
    return redirect(url_for('expenses'))


@app.route('/expenses/<int:eid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def expense_delete(eid):
    exp = Expense.query.get_or_404(eid)
    desc = exp.description
    amt = exp.amount

    # If linked to a teacher expense, delete it as well
    if exp.teacher_expense_id:
        te = TeacherExpense.query.get(exp.teacher_expense_id)
        if te:
            db.session.delete(te)

    db.session.delete(exp)
    db.session.commit()
    log_action('expense_delete', f"Suppression dépense: {desc} - {amt:.2f} DH")

    flash('Opération supprimée avec succès.', 'success')
    return redirect(url_for('expenses'))


@app.route('/suppliers', methods=['GET'])
@login_required
@role_required('admin', 'secretary')
def suppliers_list():
    return redirect(url_for('expenses', tab='suppliers'))


@app.route('/suppliers/add', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def supplier_add():
    d = request.form
    name = d.get('name', '').strip()
    if not name:
        flash('Le nom du fournisseur est obligatoire.', 'danger')
        return redirect(url_for('expenses', tab='suppliers'))

    existing = Supplier.query.filter(Supplier.name.ilike(name)).first()
    if existing:
        flash(f"Le fournisseur '{name}' existe déjà.", 'warning')
        return redirect(url_for('expenses', tab='suppliers'))

    sup = Supplier(
        name=name,
        category=d.get('category', 'Général').strip(),
        contact_person=d.get('contact_person', '').strip(),
        phone=d.get('phone', '').strip(),
        email=d.get('email', '').strip(),
        address=d.get('address', '').strip(),
        city=d.get('city', 'Marrakech').strip(),
        ice=d.get('ice', '').strip(),
        if_code=d.get('if_code', '').strip(),
        notes=d.get('notes', '').strip()
    )
    db.session.add(sup)
    db.session.commit()
    log_action('supplier_add', f"Fournisseur créé: {name}")
    flash(f"Fournisseur '{name}' créé avec succès.", 'success')
    return redirect(url_for('expenses', tab='suppliers'))


@app.route('/suppliers/<int:sid>/edit', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def supplier_edit(sid):
    sup = Supplier.query.get_or_404(sid)
    d = request.form
    name = d.get('name', '').strip()
    if not name:
        flash('Le nom du fournisseur est obligatoire.', 'danger')
        return redirect(url_for('expenses', tab='suppliers'))

    existing = Supplier.query.filter(Supplier.name.ilike(name), Supplier.id != sid).first()
    if existing:
        flash(f"Un autre fournisseur avec le nom '{name}' existe déjà.", 'danger')
        return redirect(url_for('expenses', tab='suppliers'))

    sup.name = name
    sup.category = d.get('category', sup.category).strip()
    sup.contact_person = d.get('contact_person', '').strip()
    sup.phone = d.get('phone', '').strip()
    sup.email = d.get('email', '').strip()
    sup.address = d.get('address', '').strip()
    sup.city = d.get('city', sup.city).strip()
    sup.ice = d.get('ice', '').strip()
    sup.if_code = d.get('if_code', '').strip()
    sup.notes = d.get('notes', '').strip()
    db.session.commit()
    log_action('supplier_edit', f"Fournisseur mis à jour: {name}")
    flash(f"Fiche fournisseur '{name}' mise à jour.", 'success')
    return redirect(url_for('expenses', tab='suppliers'))


@app.route('/suppliers/<int:sid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def supplier_delete(sid):
    sup = Supplier.query.get_or_404(sid)
    name = sup.name
    sup.active = False
    db.session.commit()
    log_action('supplier_delete', f"Fournisseur archivé: {name}")
    flash(f"Fournisseur '{name}' archivé.", 'success')
    return redirect(url_for('expenses', tab='suppliers'))


@app.route('/expenses/export')
@login_required
@role_required('admin', 'secretary')
def expenses_export():
    req_month = request.args.get('month', '').strip()
    query = Expense.query
    if req_month:
        try:
            y, m = map(int, req_month.split('-'))
            query = query.filter(
                db.extract('year', Expense.date) == y,
                db.extract('month', Expense.date) == m
            )
        except Exception:
            pass

    exp_list = query.order_by(Expense.date.desc(), Expense.id.desc()).all()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'ID', 'Type', 'Date', 'Echeance', 'Categorie', 'Libelle_Description',
        'Fournisseur', 'N_Facture_Ref', 'Mode_Paiement', 'Montant_Total_DH',
        'Montant_Paye_DH', 'Reste_A_Payer_DH', 'Statut'
    ])
    for e in exp_list:
        writer.writerow([
            e.id,
            e.type_badge_label_fr,
            e.date.strftime('%d/%m/%Y') if e.date else '',
            e.due_date.strftime('%d/%m/%Y') if e.due_date else '',
            e.category,
            e.description,
            e.effective_supplier,
            f"{e.invoice_no or ''} {e.reference_no or ''}".strip(),
            e.payment_method,
            f"{e.amount:.2f}",
            f"{e.paid_amount:.2f}",
            f"{e.remaining_balance:.2f}",
            e.status
        ])

    csv_data = output.getvalue().encode('utf-8-sig')
    filename = f"achats_charges_{req_month or 'global'}_{date.today().strftime('%Y%m%d')}.csv"
    return Response(
        csv_data,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


# ---------------------------------------------------------------------------
# Charges Fixes & Récurrentes Mensuelles (Recurring Charges Management)
# ---------------------------------------------------------------------------
@app.route('/expenses/recurring/add', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def expense_recurring_add():
    d = request.form
    title = d.get('title', '').strip()
    category = d.get('category', 'Loyer des locaux').strip()
    amount = _f(d.get('amount'))
    day_of_month = _int(d.get('day_of_month')) or 1
    day_of_month = max(1, min(31, day_of_month))
    payment_method = d.get('payment_method', 'Espèces').strip()
    supplier_id = _int(d.get('supplier_id'))
    supplier_name = d.get('supplier_name', '').strip()
    beneficiary = d.get('beneficiary', '').strip()
    notes = d.get('notes', '').strip()
    req_month = d.get('month', '').strip() or date.today().strftime('%Y-%m')

    if not title or amount <= 0:
        flash('Veuillez renseigner un intitulé valide et un montant supérieur à 0.', 'danger')
        return redirect(url_for('expenses', tab='recurring', month=req_month))

    if supplier_id:
        sup = Supplier.query.get(supplier_id)
        if sup:
            supplier_name = sup.name

    rc = RecurringCharge(
        title=title,
        category=category,
        amount=amount,
        day_of_month=day_of_month,
        payment_method=payment_method,
        supplier_id=supplier_id if supplier_id else None,
        supplier_name=supplier_name,
        beneficiary=beneficiary,
        active=True,
        notes=notes
    )
    db.session.add(rc)
    db.session.commit()
    log_action('recurring_charge_add', f"Nouvelle charge fixe définie : {title} ({amount:.2f} DH/mois - {category})")
    flash(f"Charge fixe récurrente '{title}' créée avec succès ({amount:.2f} DH/mois).", 'success')
    return redirect(url_for('expenses', tab='recurring', month=req_month))


@app.route('/expenses/recurring/<int:rc_id>/edit', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def expense_recurring_edit(rc_id):
    rc = RecurringCharge.query.get_or_404(rc_id)
    d = request.form
    title = d.get('title', '').strip()
    if title:
        rc.title = title
    rc.category = d.get('category', rc.category).strip()
    amt = _f(d.get('amount'))
    if amt > 0:
        rc.amount = amt
    day_val = _int(d.get('day_of_month')) or rc.day_of_month
    rc.day_of_month = max(1, min(31, day_val))
    rc.payment_method = d.get('payment_method', rc.payment_method or 'Espèces').strip()
    supplier_id = _int(d.get('supplier_id'))
    rc.supplier_id = supplier_id if supplier_id else None
    if supplier_id:
        sup = Supplier.query.get(supplier_id)
        rc.supplier_name = sup.name if sup else d.get('supplier_name', '').strip()
    else:
        rc.supplier_name = d.get('supplier_name', '').strip()
    rc.beneficiary = d.get('beneficiary', '').strip()
    rc.notes = d.get('notes', '').strip()
    rc.active = (d.get('active') == '1' or 'active' in d)
    req_month = d.get('month', '').strip() or date.today().strftime('%Y-%m')

    db.session.commit()
    log_action('recurring_charge_edit', f"Charge fixe modifiée : {rc.title} ({rc.amount:.2f} DH/mois)")
    flash(f"Charge fixe récurrente '{rc.title}' mise à jour.", 'success')
    return redirect(url_for('expenses', tab='recurring', month=req_month))


@app.route('/expenses/recurring/<int:rc_id>/toggle', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def expense_recurring_toggle(rc_id):
    rc = RecurringCharge.query.get_or_404(rc_id)
    rc.active = not rc.active
    db.session.commit()
    req_month = request.form.get('month', '').strip() or date.today().strftime('%Y-%m')
    status_label = "activée" if rc.active else "mise en pause"
    log_action('recurring_charge_toggle', f"Charge fixe '{rc.title}' {status_label}")
    flash(f"La charge fixe '{rc.title}' a été {status_label}.", 'info')
    return redirect(url_for('expenses', tab='recurring', month=req_month))


@app.route('/expenses/recurring/<int:rc_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def expense_recurring_delete(rc_id):
    rc = RecurringCharge.query.get_or_404(rc_id)
    title = rc.title
    req_month = request.form.get('month', '').strip() or date.today().strftime('%Y-%m')

    # Unlink past generated expenses to preserve history
    Expense.query.filter_by(recurring_charge_id=rc.id).update({'recurring_charge_id': None})
    db.session.delete(rc)
    db.session.commit()
    log_action('recurring_charge_delete', f"Suppression modèle charge fixe : {title}")
    flash(f"Modèle de charge fixe '{title}' supprimé (les écritures passées restent dans le journal).", 'success')
    return redirect(url_for('expenses', tab='recurring', month=req_month))


@app.route('/expenses/recurring/<int:rc_id>/validate', methods=['POST'])
@login_required
@role_required('admin')
def expense_recurring_validate(rc_id):
    rc = RecurringCharge.query.get_or_404(rc_id)
    d = request.form
    req_month = d.get('month', '').strip() or date.today().strftime('%Y-%m')
    try:
        y, m = map(int, req_month.split('-'))
    except Exception:
        y, m = date.today().year, date.today().month
        req_month = f"{y:04d}-{m:02d}"

    # Anti-duplicate check
    existing = Expense.query.filter(
        Expense.recurring_charge_id == rc.id
    ).filter(
        db.or_(
            Expense.recurring_month == req_month,
            db.and_(db.extract('year', Expense.date) == y, db.extract('month', Expense.date) == m)
        )
    ).first()

    if existing:
        flash(f"⚠️ La charge fixe '{rc.title}' est déjà validée pour le mois {req_month} (Dépense #{existing.id} de {existing.amount:.2f} DH le {existing.date.strftime('%d/%m/%Y')}).", 'warning')
        return redirect(url_for('expenses', tab='recurring', month=req_month))

    amount = _f(d.get('amount')) or rc.amount
    if amount <= 0:
        flash('Le montant doit être strictement supérieur à 0.', 'danger')
        return redirect(url_for('expenses', tab='recurring', month=req_month))

    payment_method = d.get('payment_method', rc.payment_method or 'Espèces').strip()
    status = d.get('status', 'paid').strip()
    reference_no = d.get('reference_no', '').strip()
    notes = d.get('notes', '').strip()
    custom_desc = d.get('description', '').strip()

    exp_date = parse_date(d.get('date'))
    if not exp_date:
        import calendar
        _, max_day = calendar.monthrange(y, m)
        chosen_day = min(rc.day_of_month or 1, max_day)
        exp_date = date(y, m, chosen_day)

    paid_amount = amount if status == 'paid' else (0.0 if status == 'unpaid' else min(amount, _f(d.get('paid_amount'))))

    months_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    m_label = f"{months_fr[m]} {y}" if (1 <= m <= 12) else req_month
    description = custom_desc or f"{rc.title} ({m_label})"

    u = current_user()
    exp = Expense(
        expense_type='charge',
        category=rc.category,
        description=description,
        amount=amount,
        date=exp_date,
        payment_method=payment_method,
        reference_no=reference_no,
        supplier_id=rc.supplier_id,
        supplier_name=rc.supplier_name or rc.beneficiary,
        recurring_charge_id=rc.id,
        recurring_month=req_month,
        status=status,
        paid_amount=paid_amount,
        notes=f"Charge fixe mensuelle validée [{rc.title}] pour {m_label}. {notes}".strip(),
        user_id=u.id if u else None
    )
    db.session.add(exp)
    db.session.commit()

    log_action('recurring_charge_validate', f"Charge fixe validée [{rc.title}] pour {req_month}: {amount:.2f} DH ({payment_method})")
    flash(f"✅ Charge fixe '{rc.title}' validée et enregistrée pour {m_label} ({amount:.2f} DH).", 'success')
    return redirect(url_for('expenses', tab='recurring', month=req_month))


@app.route('/expenses/recurring/validate-all', methods=['POST'])
@login_required
@role_required('admin')
def expense_recurring_validate_all():
    d = request.form
    req_month = d.get('month', '').strip() or date.today().strftime('%Y-%m')
    try:
        y, m = map(int, req_month.split('-'))
    except Exception:
        y, m = date.today().year, date.today().month
        req_month = f"{y:04d}-{m:02d}"

    pay_date = parse_date(d.get('date'))
    default_method = d.get('payment_method', '').strip()
    status = d.get('status', 'paid').strip()

    months_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    m_label = f"{months_fr[m]} {y}" if (1 <= m <= 12) else req_month

    active_rcs = RecurringCharge.query.filter_by(active=True).all()
    validated_count = 0
    u = current_user()

    for rc in active_rcs:
        existing = Expense.query.filter(
            Expense.recurring_charge_id == rc.id
        ).filter(
            db.or_(
                Expense.recurring_month == req_month,
                db.and_(db.extract('year', Expense.date) == y, db.extract('month', Expense.date) == m)
            )
        ).first()
        if existing:
            continue

        import calendar
        _, max_day = calendar.monthrange(y, m)
        chosen_day = min(rc.day_of_month or 1, max_day)
        item_date = pay_date or date(y, m, chosen_day)

        item_method = default_method or rc.payment_method or 'Espèces'
        amt = rc.amount or 0.0
        paid_amt = amt if status == 'paid' else 0.0

        exp = Expense(
            expense_type='charge',
            category=rc.category,
            description=f"{rc.title} ({m_label})",
            amount=amt,
            date=item_date,
            payment_method=item_method,
            supplier_id=rc.supplier_id,
            supplier_name=rc.supplier_name or rc.beneficiary,
            recurring_charge_id=rc.id,
            recurring_month=req_month,
            status=status,
            paid_amount=paid_amt,
            notes=f"Validation groupée des charges fixes récurrentes pour {m_label}.",
            user_id=u.id if u else None
        )
        db.session.add(exp)
        validated_count += 1

    db.session.commit()
    if validated_count > 0:
        log_action('recurring_charge_validate_all', f"Validation groupée de {validated_count} charges fixes pour {req_month}")
        flash(f"🎉 {validated_count} charge(s) fixe(s) validée(s) et générée(s) avec succès pour {m_label}.", 'success')
    else:
        flash(f"Toutes les charges fixes actives sont déjà validées pour {m_label}.", 'info')

    return redirect(url_for('expenses', tab='recurring', month=req_month))


@app.route('/expenses/recurring/<int:rc_id>/cancel-month', methods=['POST'])
@login_required
@role_required('admin')
def expense_recurring_cancel_month(rc_id):
    rc = RecurringCharge.query.get_or_404(rc_id)
    req_month = request.form.get('month', '').strip() or date.today().strftime('%Y-%m')
    try:
        y, m = map(int, req_month.split('-'))
    except Exception:
        y, m = date.today().year, date.today().month
        req_month = f"{y:04d}-{m:02d}"

    existing = Expense.query.filter(
        Expense.recurring_charge_id == rc.id
    ).filter(
        db.or_(
            Expense.recurring_month == req_month,
            db.and_(db.extract('year', Expense.date) == y, db.extract('month', Expense.date) == m)
        )
    ).first()

    if existing:
        desc = existing.description
        amt = existing.amount
        db.session.delete(existing)
        db.session.commit()
        log_action('recurring_charge_cancel', f"Annulation validation charge fixe '{rc.title}' ({req_month}) - {amt:.2f} DH")
        flash(f"La validation de '{rc.title}' pour {req_month} a été annulée (dépense de {amt:.2f} DH retirée du journal).", 'success')
    else:
        flash("Aucune écriture trouvée pour cette charge sur ce mois.", 'warning')

    return redirect(url_for('expenses', tab='recurring', month=req_month))



# ---------------------------------------------------------------------------
# Course-Teacher Dynamic Assignments & Compensation
# ---------------------------------------------------------------------------
@app.route('/teachers/assignments', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def teacher_assignments():
    return redirect(url_for('courses'))


def calculate_enrollment_revenue_for_month(enrollment, target_year, target_month):
    if not enrollment:
        return 0.0

    # If enrollment is transferred or dropped, it cannot recognize revenue in months strictly after transfer date
    if enrollment.status in ('transferred', 'dropped') and enrollment.custom_end_date:
        if (target_year, target_month) > (enrollment.custom_end_date.year, enrollment.custom_end_date.month):
            return 0.0

    # 1. Registration fee extraction & full tuition due
    tot_paid_overall = float(enrollment.total_paid or 0.0)
    dur = enrollment.duration_months or 1
    reg_fee = 0.0
    if enrollment.notes and "Frais d'inscription:" in enrollment.notes:
        import re
        m = re.search(r"Frais d'inscription:\s*([\d\.]+)\s*DH", enrollment.notes)
        if m:
            try:
                reg_fee = float(m.group(1))
            except Exception:
                reg_fee = 0.0
    elif enrollment.calculated_price is not None and enrollment.monthly_price is not None:
        diff = float(enrollment.calculated_price) - float(enrollment.monthly_price * dur)
        if 0 < diff <= 300:
            reg_fee = diff
        elif float(enrollment.calculated_price) > float(enrollment.monthly_price) and dur == 1:
            diff1 = float(enrollment.calculated_price) - float(enrollment.monthly_price)
            if 0 < diff1 <= 300:
                reg_fee = diff1
    else:
        reg_fee = float(enrollment.course.registration_fee or 0.0) if enrollment.course else 0.0

    calc_pr = float(enrollment.calculated_price or 0.0)
    if calc_pr > reg_fee:
        total_tuition_due = calc_pr - reg_fee
    else:
        total_tuition_due = float(enrollment.monthly_price or 0.0) * dur

    if total_tuition_due <= 0:
        return 0.0

    # 2. Simulate month capacities across enrollment schedule
    e_start = enrollment.enroll_date or date.today()
    scheduled_days = enrollment.scheduled_weekdays
    if not scheduled_days:
        scheduled_days = {0, 2, 4}

    month_capacities = {}

    dur = enrollment.duration_months or 1
    tot_cycle_sess = enrollment.total_cycle_sessions
    if not tot_cycle_sess or tot_cycle_sess <= 0:
        tot_cycle_sess = 12 * dur

    # A course's session price must be based on the full expected sessions of the cycle.
    # We must NEVER compress total_tuition_due into fewer sessions than tot_cycle_sess,
    # because doing so (e.g. when custom_end_date reflects only partial paid sessions)
    # artificially inflates the per-session price and causes the current month
    # to absorb multi-month payments inappropriately.
    total_expected_sessions = tot_cycle_sess
    if hasattr(enrollment, 'custom_end_date') and enrollment.custom_end_date and enrollment.custom_end_date >= e_start:
        cur_dt = e_start
        cnt = 0
        while cur_dt <= enrollment.custom_end_date:
            if cur_dt.weekday() in scheduled_days:
                cnt += 1
            cur_dt += timedelta(days=1)

        span_days = (enrollment.custom_end_date - e_start).days
        if dur == 1:
            # For 1-month enrollments:
            # If custom_end_date marks the end of the month / cycle (span <= 35 days or same month)
            # then expected sessions of this 1-month period is cnt (e.g. 11 for mid-month, 13 for full month)
            if 0 < cnt <= tot_cycle_sess and (span_days <= 35 or (e_start.year == enrollment.custom_end_date.year and e_start.month == enrollment.custom_end_date.month)):
                total_expected_sessions = cnt
            else:
                total_expected_sessions = tot_cycle_sess
        else:
            # For multi-month enrollments (2 or 3 months):
            if cnt > tot_cycle_sess:
                total_expected_sessions = cnt
            elif cnt > 0 and abs(cnt - tot_cycle_sess) <= 4:
                total_expected_sessions = cnt

    session_price = total_tuition_due / total_expected_sessions
    sessions_counted = 0
    cur_dt = e_start

    while sessions_counted < total_expected_sessions:
        if cur_dt.weekday() in scheduled_days:
            month_key = (cur_dt.year, cur_dt.month)
            month_capacities[month_key] = month_capacities.get(month_key, 0.0) + session_price
            sessions_counted += 1
        cur_dt += timedelta(days=1)
        if (cur_dt - e_start).days > 730:
            break

    if not month_capacities:
        month_capacities[(e_start.year, e_start.month)] = total_tuition_due

    target_key = (target_year, target_month)
    _, num_days_target = calendar.monthrange(target_year, target_month)
    target_month_end = date(target_year, target_month, num_days_target)
    target_month_start = date(target_year, target_month, 1)

    # Payments made up to end of target month
    all_payments = Payment.query.filter_by(enrollment_id=enrollment.id).all()
    paid_to_target = sum(p.amount for p in all_payments if p.date and p.date <= target_month_end)
    tuition_paid_to_target = max(0.0, paid_to_target - reg_fee)

    if tuition_paid_to_target <= 0:
        return 0.0

    # Payments made strictly before target month
    paid_prior = sum(p.amount for p in all_payments if p.date and p.date < target_month_start)
    tuition_paid_prior = max(0.0, paid_prior - reg_fee)

    # Waterfall allocation with catch-up for arrears unlocked during this target month
    rem_to_target = tuition_paid_to_target
    rem_prior = tuition_paid_prior

    recognized_revenue = 0.0

    for mk in sorted(month_capacities.keys()):
        cap = month_capacities[mk]
        alloc_to_target = min(cap, rem_to_target)
        alloc_prior = min(cap, rem_prior)

        rem_to_target -= alloc_to_target
        rem_prior -= alloc_prior

        if mk == target_key:
            recognized_revenue += alloc_to_target
        elif mk < target_key:
            arrears_unlocked = max(0.0, alloc_to_target - alloc_prior)
            recognized_revenue += arrears_unlocked

    # If target month is past all scheduled sessions, any new payments collected in this month
    if target_key not in month_capacities and target_key > max(month_capacities.keys()):
        past_alloc_prior = sum(min(month_capacities[k], max(0.0, tuition_paid_prior)) for k in sorted(month_capacities.keys()))
        past_alloc_target = sum(min(month_capacities[k], max(0.0, tuition_paid_to_target)) for k in sorted(month_capacities.keys()))
        recognized_revenue += max(0.0, past_alloc_target - past_alloc_prior)

    return round(recognized_revenue, 2)



def parse_duration_to_hours(duration_str):
    if not duration_str: return 1.0
    s = str(duration_str).lower().strip().replace(' ', '')
    if 'h' in s:
        parts = s.split('h')
        hrs = float(parts[0]) if parts[0] else 0.0
        mins = float(parts[1]) if len(parts)>1 and parts[1] else 0.0
        return hrs + (mins / 60.0)
    try:
        return float(s)
    except:
        return 1.0


def compute_teacher_gross_for_month(teacher, y, m):
    """Calcule le revenu brut gagné par un enseignant pour un mois spécifique (y, m) basé sur les classes."""
    if not teacher:
        return 0.0
    _, num_days = calendar.monthrange(y, m)
    assigned_cts = CourseTeacher.query.filter_by(teacher_id=teacher.id, is_active=True).all()
    assigned_courses = [ct.course for ct in assigned_cts if ct.course and ct.course.active]
    direct_courses = Course.query.filter_by(teacher_id=teacher.id, active=True).all()
    for c in direct_courses:
        if c not in assigned_courses:
            assigned_courses.append(c)

    t_total_earned = 0.0
    for c in assigned_courses:
        all_c_enrolls = Enrollment.query.filter_by(course_id=c.id).filter(Enrollment.status != 'dropped').order_by(Enrollment.id.desc()).all()
        student_enrolls_map = {}
        for en in all_c_enrolls:
            st = en.student
            if not st:
                continue
            rev = calculate_enrollment_revenue_for_month(en, y, m)
            if en.status == 'transferred':
                if rev <= 0:
                    continue
                has_active = Enrollment.query.filter_by(student_id=en.student_id, status='active').first()
                if not has_active:
                    continue
            else:
                if not (rev > 0 or (en.enroll_date and en.enroll_date.year == y and en.enroll_date.month == m) or (en.end_date and en.end_date.year == y and en.end_date.month == m)):
                    continue
            if st.id not in student_enrolls_map:
                student_enrolls_map[st.id] = {'total_month_rev': 0.0, 'primary_enrollment': en}
            student_enrolls_map[st.id]['total_month_rev'] += rev

        group_tuition_rev = sum(min(s_info['total_month_rev'], getattr(s_info['primary_enrollment'], 'unit_monthly_price', None) or s_info['primary_enrollment'].monthly_price or (c.unit_monthly_price if hasattr(c, 'unit_monthly_price') else (c.price_per_month or c.price or 300.0))) for s_info in student_enrolls_map.values() if s_info['total_month_rev'] > 0)
        month_students_count = len(student_enrolls_map)

        # Rémunération basée strictement sur la classe (CourseTeacher du groupe)
        ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=teacher.id, is_active=True).first()
        if not ct:
            ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=teacher.id).first()
        comp_type = ct.compensation_type if (ct and ct.compensation_type) else 'percentage'
        comp_val = ct.compensation_value if (ct and ct.compensation_value is not None) else 50.0

        teacher_earned = 0.0
        if comp_type == 'percentage':
            teacher_earned = round(group_tuition_rev * (comp_val / 100.0), 2)
        elif comp_type == 'per_student':
            teacher_earned = round(month_students_count * comp_val, 2)
        elif comp_type == 'fixed':
            teacher_earned = round(comp_val, 2) if (group_tuition_rev > 0 or month_students_count > 0) else 0.0
        elif comp_type == 'hourly':
            slots_count = ScheduleSlot.query.filter_by(course_id=c.id).count()
            if slots_count == 0:
                slots_count = c.sessions_per_week or 3
            hrs_per_slot = parse_duration_to_hours(c.session_duration)
            scheduled_days = (c.scheduled_weekdays if hasattr(c, 'scheduled_weekdays') else None) or {0, 2, 4}
            actual_sessions_in_month = sum(1 for d in range(1, num_days + 1) if date(y, m, d).weekday() in (scheduled_days or {0, 2, 4}))
            if actual_sessions_in_month == 0:
                actual_sessions_in_month = slots_count * 4
            teacher_earned = round(actual_sessions_in_month * hrs_per_slot * comp_val, 2) if (group_tuition_rev > 0 or month_students_count > 0) else 0.0

        t_total_earned += teacher_earned

    return round(t_total_earned, 2)


def calculate_prior_teacher_credit(teacher, target_y, target_m):
    """
    Calcule tout reliquat d'avances ou trop-perçu non soldé (crédit) reporté des mois antérieurs.
    Fenêtre dynamique sur les 6 derniers mois (au lieu d'une date figée).
    Renvoie : (prior_credit_deducted, reason_str)
    """
    months_fr = {1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
                 7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'}
    
    # Fenêtre dynamique de 6 mois en arrière
    cur_y = target_y
    cur_m = target_m - 6
    while cur_m <= 0:
        cur_m += 12
        cur_y -= 1

    if teacher.hire_date:
        if (teacher.hire_date.year, teacher.hire_date.month) > (cur_y, cur_m):
            cur_y, cur_m = teacher.hire_date.year, teacher.hire_date.month

    carried_debt = 0.0
    reason_str = ""

    while (cur_y < target_y) or (cur_y == target_y and cur_m < target_m):
        m_str = f"{cur_y:04d}-{cur_m:02d}"
        m_name = f"{months_fr.get(cur_m, '')} {cur_y}"

        advances = TeacherAdvance.query.filter_by(teacher_id=teacher.id, period_month=m_str)\
            .filter(TeacherAdvance.status != 'cancelled').all()
        total_adv = round(sum(a.amount for a in advances), 2)

        expenses = TeacherExpense.query.filter_by(teacher_id=teacher.id, period_month=m_str)\
            .filter(TeacherExpense.status != 'cancelled').all()
        total_exp = round(sum(e.amount for e in expenses), 2)

        payout = TeacherSalaryPayout.query.filter_by(teacher_id=teacher.id, period_month=m_str)\
            .filter(TeacherSalaryPayout.status != 'cancelled').first()

        total_owed = round(total_adv + total_exp + carried_debt, 2)

        # Performance optimization: If there is no payout to reconcile and nothing is owed,
        # the teacher has zero debt carryover. Skip expensive enrollment gross calculations!
        if not payout and total_owed == 0:
            carried_debt = 0.0
            if cur_m == 12:
                cur_y += 1
                cur_m = 1
            else:
                cur_m += 1
            continue

        earned = compute_teacher_gross_for_month(teacher, cur_y, cur_m)

        if payout:
            net_actual = payout.net_amount
            net_obligation = round(earned - total_adv - total_exp - carried_debt, 2)
            if net_obligation < 0:
                carried_debt = round(abs(net_obligation) + net_actual, 2)
                reason_str = f"Avances/frais excédentaires non couverts du mois de {m_name}"
            elif net_actual > net_obligation:
                carried_debt = round(net_actual - net_obligation, 2)
                reason_str = f"Trop-perçu sur le salaire versé en {m_name}"
            else:
                carried_debt = 0.0
                reason_str = ""
        else:
            if total_owed > earned:
                carried_debt = round(total_owed - earned, 2)
                reason_str = f"Reliquat avances & frais non couverts de {m_name} (Brut: {earned:.2f} DH, Avances: {total_adv:.2f} DH, Frais: {total_exp:.2f} DH)"
            else:
                carried_debt = 0.0
                reason_str = ""

        if cur_m == 12:
            cur_y += 1
            cur_m = 1
        else:
            cur_m += 1

    return carried_debt, reason_str


@app.route('/teachers/payroll')
@login_required
@role_required('admin')
def teachers_payroll():
    req_month = request.args.get('month') or date.today().strftime('%Y-%m')
    selected_teacher_ids = _parse_teacher_ids(request)
    try:
        y, m = map(int, req_month.split('-'))
    except Exception:
        y, m = date.today().year, date.today().month
        req_month = f"{y:04d}-{m:02d}"

    m_start = date(y, m, 1)
    _, num_days = calendar.monthrange(y, m)
    m_end = date(y, m, num_days)

    all_teachers = Teacher.query.filter_by(active=True).all()
    teachers = [t for t in all_teachers if (not selected_teacher_ids or t.id in selected_teacher_ids)]
    payroll_data = []

    seen_courses_rev = {}
    grand_total_revenue = 0.0
    grand_teacher_payout = 0.0
    grand_school_net = 0.0

    for t in teachers:
        t_groups = []
        t_total_rev = 0.0
        t_total_earned = 0.0
        t_total_school_net = 0.0
        t_total_tuition_rev = 0.0  # Tuition only (excludes reg fees)

        assigned_cts = CourseTeacher.query.filter_by(teacher_id=t.id, is_active=True).all()
        assigned_courses = [ct.course for ct in assigned_cts if ct.course and ct.course.active]
        direct_courses = Course.query.filter_by(teacher_id=t.id, active=True).all()
        for c in direct_courses:
            if c not in assigned_courses:
                assigned_courses.append(c)

        for c in assigned_courses:
            all_c_enrolls = Enrollment.query.filter_by(course_id=c.id).filter(Enrollment.status != 'dropped').order_by(Enrollment.id.desc()).all()
            
            student_enrolls_map = {}
            for en in all_c_enrolls:
                st = en.student
                if not st:
                    continue

                rev = calculate_enrollment_revenue_for_month(en, y, m)
                if en.status == 'transferred':
                    if rev <= 0:
                        continue
                    has_active = Enrollment.query.filter_by(student_id=en.student_id, status='active').first()
                    if not has_active:
                        continue
                else:
                    if not (rev > 0 or (en.enroll_date and en.enroll_date.year == y and en.enroll_date.month == m) or (en.end_date and en.end_date.year == y and en.end_date.month == m)):
                        continue

                if st.id not in student_enrolls_map:
                    student_enrolls_map[st.id] = {
                        'primary_enrollment': en,
                        'total_month_rev': 0.0,
                        'enrollments': []
                    }
                student_enrolls_map[st.id]['total_month_rev'] += rev
                student_enrolls_map[st.id]['enrollments'].append(en)
                if en.status == 'active' or student_enrolls_map[st.id]['primary_enrollment'].status != 'active':
                    student_enrolls_map[st.id]['primary_enrollment'] = en

            group_tuition_rev = 0.0
            group_reg_fees_school = 0.0
            month_students_count = len(student_enrolls_map)

            for s_id, s_info in student_enrolls_map.items():
                primary_en = s_info['primary_enrollment']
                std_price = primary_en.monthly_price or (c.price_per_month or c.price or 300.0)
                m_rev = min(s_info['total_month_rev'], std_price) if s_info['total_month_rev'] > 0 else 0.0
                group_tuition_rev += m_rev

                for e in s_info['enrollments']:
                    if e.enroll_date and e.enroll_date.year == y and e.enroll_date.month == m:
                        reg_fee_val = max(0.0, (e.calculated_price or 0.0) - (e.monthly_price or 0.0))
                        if e.total_paid and e.total_paid > 0:
                            paid_reg_fee = min(e.total_paid, reg_fee_val)
                            group_reg_fees_school += paid_reg_fee

            # Rémunération basée strictement sur la classe (CourseTeacher du groupe)
            ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=t.id, is_active=True).first()
            if not ct:
                ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=t.id).first()
            comp_type = ct.compensation_type if (ct and ct.compensation_type) else 'percentage'
            comp_val = ct.compensation_value if (ct and ct.compensation_value is not None) else 50.0

            teacher_earned = 0.0
            if comp_type == 'percentage':
                teacher_earned = round(group_tuition_rev * (comp_val / 100.0), 2)
            elif comp_type == 'per_student':
                teacher_earned = round(month_students_count * comp_val, 2)
            elif comp_type == 'fixed':
                teacher_earned = round(comp_val, 2) if (group_tuition_rev > 0 or month_students_count > 0) else 0.0
            elif comp_type == 'hourly':
                t_slots = ScheduleSlot.query.filter_by(course_id=c.id).filter(
                    db.or_(ScheduleSlot.teacher_id == t.id, db.and_(ScheduleSlot.teacher_id.is_(None), c.teacher_id == t.id))
                ).all()
                if t_slots:
                    slots_count = len(t_slots)
                    scheduled_days = set(s.day_of_week for s in t_slots)
                else:
                    slots_count = ScheduleSlot.query.filter_by(course_id=c.id).count() or (c.sessions_per_week or 3)
                    scheduled_days = (c.scheduled_weekdays if hasattr(c, 'scheduled_weekdays') else None) or {0, 2, 4}
                hrs_per_slot = parse_duration_to_hours(c.session_duration)
                actual_sessions_in_month = sum(1 for d in range(1, num_days + 1) if date(y, m, d).weekday() in scheduled_days)
                if actual_sessions_in_month == 0:
                    actual_sessions_in_month = slots_count * 4
                teacher_earned = round(actual_sessions_in_month * hrs_per_slot * comp_val, 2) if (group_tuition_rev > 0 or month_students_count > 0) else 0.0

            total_collected_group = group_tuition_rev + group_reg_fees_school
            seen_courses_rev[c.id] = total_collected_group
            school_net = max(0.0, round(total_collected_group - teacher_earned, 2))
            # Tuition-only school net (excluding registration fees from total)
            school_net_tuition = max(0.0, round(group_tuition_rev - teacher_earned, 2))

            t_total_rev += total_collected_group
            t_total_earned += teacher_earned
            t_total_school_net += school_net
            t_total_tuition_rev += group_tuition_rev

            t_groups.append({
                'course': c,
                'enroll_count': month_students_count,
                'group_rev': total_collected_group,
                'group_tuition_rev': round(group_tuition_rev, 2),
                'group_reg_fees': round(group_reg_fees_school, 2),
                'comp_type': comp_type,
                'comp_val': comp_val,
                'teacher_earned': teacher_earned,
                'school_net': school_net,
                'school_net_tuition': school_net_tuition
            })

        # Fetch advances for this teacher for req_month (khassou itnqas lih man payment of month)
        advances = TeacherAdvance.query.filter_by(teacher_id=t.id, period_month=req_month)\
            .filter(TeacherAdvance.status != 'cancelled')\
            .order_by(TeacherAdvance.date.asc(), TeacherAdvance.id.asc()).all()
        t_total_advances = round(sum(a.amount for a in advances), 2)

        # Fetch expenses & copies for this teacher for req_month (déduction sur la paie du même mois)
        teacher_expenses = TeacherExpense.query.filter_by(teacher_id=t.id, period_month=req_month)\
            .filter(TeacherExpense.status != 'cancelled')\
            .order_by(TeacherExpense.date.asc(), TeacherExpense.id.asc()).all()
        t_total_expenses = round(sum(e.amount for e in teacher_expenses), 2)
        t_total_copies = sum((e.quantity or 0) for e in teacher_expenses if e.expense_type == 'copies')
        # Prior credit/debt carried over from previous months (avance/trop-perçu excédentaire)
        prior_credit_deducted, prior_credit_reason = calculate_prior_teacher_credit(t, y, m)

        # Fetch book / item sales for this teacher for req_month (gains ajoutés au salaire)
        teacher_book_sales = BookSale.query.filter_by(teacher_id=t.id, period_month=req_month)\
            .order_by(BookSale.sale_date.asc(), BookSale.id.asc()).all()
        t_total_book_sales = round(sum((s.teacher_earned or 0.0) for s in teacher_book_sales), 2)

        t_total_deductions = round(t_total_advances + t_total_expenses, 2)
        total_all_deductions = round(t_total_deductions + prior_credit_deducted, 2)
        
        # Gross earnings including teaching + book sales commissions
        t_total_gross = round(t_total_earned + t_total_book_sales, 2)
        balance = round(t_total_gross - total_all_deductions, 2)
        if balance >= 0:
            t_net_payable = balance
            t_credit_carryover = 0.0
        else:
            t_net_payable = 0.0
            t_credit_carryover = abs(balance)

        # Check if already paid for req_month (Anti-Doublon check)
        salary_payout = TeacherSalaryPayout.query.filter_by(teacher_id=t.id, period_month=req_month)\
            .filter(TeacherSalaryPayout.status != 'cancelled')\
            .order_by(TeacherSalaryPayout.id.desc()).first()
        is_paid = (salary_payout is not None)

        grand_teacher_payout += t_total_earned

        payroll_data.append({
            'teacher': t,
            'groups': t_groups,
            'total_rev': t_total_rev,
            'total_tuition_rev': round(t_total_tuition_rev, 2),
            'total_earned': t_total_earned,
            'total_book_sales': t_total_book_sales,
            'book_sales': teacher_book_sales,
            'total_gross': t_total_gross,
            'total_advances': t_total_advances,
            'advances': advances,
            'total_expenses': t_total_expenses,
            'total_copies': t_total_copies,
            'teacher_expenses': teacher_expenses,
            'total_deductions': t_total_deductions,
            'prior_credit_deducted': prior_credit_deducted,
            'prior_credit_reason': prior_credit_reason,
            'total_all_deductions': total_all_deductions,
            'credit_carryover': t_credit_carryover,
            'net_payable': t_net_payable,
            'total_school_net': t_total_school_net,
            'total_school_net_tuition': round(t_total_tuition_rev - t_total_earned, 2),
            'is_paid': is_paid,
            'salary_payout': salary_payout
        })

    # Accurately compute grand total revenue across all distinct courses taught
    grand_total_revenue = sum(seen_courses_rev.values())
    grand_school_net = max(0.0, round(grand_total_revenue - grand_teacher_payout, 2))

    grand_teacher_advances = round(sum(item['total_advances'] for item in payroll_data), 2)
    grand_teacher_expenses = round(sum(item['total_expenses'] for item in payroll_data), 2)
    grand_teacher_prior_credits = round(sum(item['prior_credit_deducted'] for item in payroll_data), 2)
    grand_teacher_book_sales = round(sum(item['total_book_sales'] for item in payroll_data), 2)
    grand_teacher_copies = sum(item['total_copies'] for item in payroll_data)
    grand_teacher_deductions = round(sum(item['total_all_deductions'] for item in payroll_data), 2)
    grand_teacher_net = round(sum(item['net_payable'] for item in payroll_data), 2)
    grand_teacher_credits = round(sum(item['credit_carryover'] for item in payroll_data), 2)
    grand_teachers_paid_count = sum(1 for item in payroll_data if item['is_paid'])

    charge_items = TeacherChargeItem.query.filter_by(active=True).order_by(TeacherChargeItem.id.asc()).all()

    return render_template('teachers/payroll.html',
                           req_month=req_month,
                           teachers=all_teachers,
                           all_teachers=all_teachers,
                           selected_teacher_ids=list(selected_teacher_ids),
                           payroll_data=payroll_data,
                           grand_total_revenue=grand_total_revenue,
                           grand_teacher_payout=grand_teacher_payout,
                           grand_teacher_book_sales=grand_teacher_book_sales,
                           grand_teacher_advances=grand_teacher_advances,
                           grand_teacher_expenses=grand_teacher_expenses,
                           grand_teacher_prior_credits=grand_teacher_prior_credits,
                           grand_teacher_copies=grand_teacher_copies,
                           grand_teacher_deductions=grand_teacher_deductions,
                           grand_teacher_net=grand_teacher_net,
                           grand_teacher_credits=grand_teacher_credits,
                           grand_teachers_paid_count=grand_teachers_paid_count,
                           grand_school_net=grand_school_net,
                           charge_items=charge_items)


def get_single_teacher_payroll_details(teacher, y, m):
    """Calcule le détail complet de la paie pour un enseignant et un mois donné (y, m)."""
    if not teacher:
        return None
    req_month = f"{y:04d}-{m:02d}"
    _, num_days = calendar.monthrange(y, m)

    assigned_cts = CourseTeacher.query.filter_by(teacher_id=teacher.id, is_active=True).all()
    assigned_courses = [ct.course for ct in assigned_cts if ct.course and ct.course.active]
    direct_courses = Course.query.filter_by(teacher_id=teacher.id, active=True).all()
    for c in direct_courses:
        if c not in assigned_courses:
            assigned_courses.append(c)

    t_groups = []
    t_total_rev = 0.0
    t_total_earned = 0.0
    t_total_tuition_rev = 0.0

    for c in assigned_courses:
        all_c_enrolls = Enrollment.query.filter_by(course_id=c.id).filter(Enrollment.status != 'dropped').order_by(Enrollment.id.desc()).all()
        student_enrolls_map = {}
        for en in all_c_enrolls:
            st = en.student
            if not st:
                continue
            rev = calculate_enrollment_revenue_for_month(en, y, m)
            if en.status == 'transferred':
                if rev <= 0:
                    continue
                has_active = Enrollment.query.filter_by(student_id=en.student_id, status='active').first()
                if not has_active:
                    continue
            else:
                if not (rev > 0 or (en.enroll_date and en.enroll_date.year == y and en.enroll_date.month == m) or (en.end_date and en.end_date.year == y and en.end_date.month == m)):
                    continue

            if st.id not in student_enrolls_map:
                student_enrolls_map[st.id] = {
                    'primary_enrollment': en,
                    'total_month_rev': 0.0,
                    'enrollments': []
                }
            student_enrolls_map[st.id]['total_month_rev'] += rev
            student_enrolls_map[st.id]['enrollments'].append(en)
            if en.status == 'active' or student_enrolls_map[st.id]['primary_enrollment'].status != 'active':
                student_enrolls_map[st.id]['primary_enrollment'] = en

        group_tuition_rev = 0.0
        group_reg_fees_school = 0.0
        month_students_count = len(student_enrolls_map)

        for s_id, s_info in student_enrolls_map.items():
            primary_en = s_info['primary_enrollment']
            std_price = primary_en.monthly_price or (c.price_per_month or c.price or 300.0)
            m_rev = min(s_info['total_month_rev'], std_price) if s_info['total_month_rev'] > 0 else 0.0
            group_tuition_rev += m_rev

            for e in s_info['enrollments']:
                if e.enroll_date and e.enroll_date.year == y and e.enroll_date.month == m:
                    reg_fee_val = max(0.0, (e.calculated_price or 0.0) - (e.monthly_price or 0.0))
                    if e.total_paid and e.total_paid > 0:
                        paid_reg_fee = min(e.total_paid, reg_fee_val)
                        group_reg_fees_school += paid_reg_fee

        ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=teacher.id, is_active=True).first()
        if not ct:
            ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=teacher.id).first()
        comp_type = ct.compensation_type if (ct and ct.compensation_type) else 'percentage'
        comp_val = ct.compensation_value if (ct and ct.compensation_value is not None) else 50.0

        teacher_earned = 0.0
        if comp_type == 'percentage':
            teacher_earned = round(group_tuition_rev * (comp_val / 100.0), 2)
        elif comp_type == 'per_student':
            teacher_earned = round(month_students_count * comp_val, 2)
        elif comp_type == 'fixed':
            teacher_earned = round(comp_val, 2) if (group_tuition_rev > 0 or month_students_count > 0) else 0.0
        elif comp_type == 'hourly':
            slots_count = ScheduleSlot.query.filter_by(course_id=c.id).count()
            if slots_count == 0:
                slots_count = c.sessions_per_week or 3
            hrs_per_slot = parse_duration_to_hours(c.session_duration)
            scheduled_days = (c.scheduled_weekdays if hasattr(c, 'scheduled_weekdays') else None) or {0, 2, 4}
            actual_sessions_in_month = sum(1 for d in range(1, num_days + 1) if date(y, m, d).weekday() in (scheduled_days or {0, 2, 4}))
            if actual_sessions_in_month == 0:
                actual_sessions_in_month = slots_count * 4
            teacher_earned = round(actual_sessions_in_month * hrs_per_slot * comp_val, 2) if (group_tuition_rev > 0 or month_students_count > 0) else 0.0

        total_collected_group = group_tuition_rev + group_reg_fees_school
        t_total_rev += total_collected_group
        t_total_earned += teacher_earned
        t_total_tuition_rev += group_tuition_rev

        t_groups.append({
            'course': c,
            'enroll_count': month_students_count,
            'group_rev': total_collected_group,
            'group_tuition_rev': round(group_tuition_rev, 2),
            'comp_type': comp_type,
            'comp_val': comp_val,
            'teacher_earned': teacher_earned,
        })

    advances = TeacherAdvance.query.filter_by(teacher_id=teacher.id, period_month=req_month)\
        .filter(TeacherAdvance.status != 'cancelled')\
        .order_by(TeacherAdvance.date.asc(), TeacherAdvance.id.asc()).all()
    t_total_advances = round(sum(a.amount for a in advances), 2)

    teacher_expenses = TeacherExpense.query.filter_by(teacher_id=teacher.id, period_month=req_month)\
        .filter(TeacherExpense.status != 'cancelled')\
        .order_by(TeacherExpense.date.asc(), TeacherExpense.id.asc()).all()
    t_total_expenses = round(sum(e.amount for e in teacher_expenses), 2)
    t_total_copies = sum((e.quantity or 0) for e in teacher_expenses if e.expense_type == 'copies')

    prior_credit_deducted, prior_credit_reason = calculate_prior_teacher_credit(teacher, y, m)

    teacher_book_sales = BookSale.query.filter_by(teacher_id=teacher.id, period_month=req_month)\
        .order_by(BookSale.sale_date.asc(), BookSale.id.asc()).all()
    t_total_book_sales = round(sum((s.teacher_earned or 0.0) for s in teacher_book_sales), 2)

    t_total_deductions = round(t_total_advances + t_total_expenses, 2)
    total_all_deductions = round(t_total_deductions + prior_credit_deducted, 2)
    t_total_gross = round(t_total_earned + t_total_book_sales, 2)
    balance = round(t_total_gross - total_all_deductions, 2)
    if balance >= 0:
        t_net_payable = balance
        t_credit_carryover = 0.0
    else:
        t_net_payable = 0.0
        t_credit_carryover = abs(balance)

    salary_payout = TeacherSalaryPayout.query.filter_by(teacher_id=teacher.id, period_month=req_month)\
        .filter(TeacherSalaryPayout.status != 'cancelled')\
        .order_by(TeacherSalaryPayout.id.desc()).first()
    is_paid = (salary_payout is not None)

    months_map_fr = {1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
                     7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'}
    months_map_ar = {1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'ماي', 6: 'يونيو',
                     7: 'يوليوز', 8: 'غشت', 9: 'شتنبر', 10: 'أكتوبر', 11: 'نونبر', 12: 'دجنبر'}

    return {
        'teacher': teacher,
        'year': y,
        'month': m,
        'period_month': req_month,
        'month_name_fr': months_map_fr.get(m, ''),
        'month_name_ar': months_map_ar.get(m, ''),
        'groups': t_groups,
        'total_rev': t_total_rev,
        'total_tuition_rev': round(t_total_tuition_rev, 2),
        'total_earned': t_total_earned,
        'total_book_sales': t_total_book_sales,
        'book_sales': teacher_book_sales,
        'total_gross': t_total_gross,
        'advances': advances,
        'total_advances': t_total_advances,
        'teacher_expenses': teacher_expenses,
        'total_expenses': t_total_expenses,
        'total_copies': t_total_copies,
        'prior_credit_deducted': prior_credit_deducted,
        'prior_credit_reason': prior_credit_reason,
        'total_all_deductions': total_all_deductions,
        'credit_carryover': t_credit_carryover,
        'net_payable': t_net_payable,
        'is_paid': is_paid,
        'salary_payout': salary_payout
    }


# ---------------------------------------------------------------------------
# Teacher Payment Visibility Management (Admin)
# ---------------------------------------------------------------------------
@app.route('/teachers/payment-visibility', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def teacher_payment_visibility():
    today = date.today()
    try:
        year = int(request.args.get('year', request.form.get('year', today.year)))
    except Exception:
        year = today.year

    try:
        selected_month = int(request.args.get('month', request.form.get('month', today.month)))
    except Exception:
        selected_month = today.month
    selected_month = max(1, min(12, selected_month))

    active_tab = request.args.get('tab', request.form.get('tab', 'fast'))
    if active_tab not in ['fast', 'matrix']:
        active_tab = 'fast'

    teachers = Teacher.query.filter_by(active=True).order_by(Teacher.first_name.asc(), Teacher.last_name.asc()).all()

    months_list = [
        (1, 'Janvier', 'يناير'),
        (2, 'Février', 'فبراير'),
        (3, 'Mars', 'مارس'),
        (4, 'Avril', 'أبريل'),
        (5, 'Mai', 'ماي'),
        (6, 'Juin', 'يونيو'),
        (7, 'Juillet', 'يوليوز'),
        (8, 'Août', 'غشت'),
        (9, 'Septembre', 'شتنبر'),
        (10, 'Octobre', 'أكتوبر'),
        (11, 'Novembre', 'نونبر'),
        (12, 'Décembre', 'دجنبر'),
    ]
    months_dict = {num: (fr, ar) for num, fr, ar in months_list}

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'batch_visibility':
            action_type = request.form.get('action_type', 'show')  # show, hide, show_all, hide_all
            target_month = _int(request.form.get('target_month', selected_month))
            target_month = max(1, min(12, target_month))

            if action_type in ['show_all', 'hide_all']:
                target_teacher_ids = [t.id for t in teachers]
                make_visible = (action_type == 'show_all')
            else:
                target_teacher_ids = [int(tid) for tid in request.form.getlist('teacher_ids') if tid.isdigit()]
                make_visible = (action_type == 'show')

            if not target_teacher_ids:
                flash("Veuillez sélectionner au moins un enseignant à mettre à jour.", 'warning')
                return redirect(url_for('teacher_payment_visibility', year=year, month=target_month, tab='fast'))

            for tid in target_teacher_ids:
                rec = TeacherPaymentVisibility.query.filter_by(teacher_id=tid, year=year, month=target_month).first()
                if not rec:
                    rec = TeacherPaymentVisibility(teacher_id=tid, year=year, month=target_month, is_visible=make_visible)
                    db.session.add(rec)
                else:
                    rec.is_visible = make_visible
                    rec.updated_at = datetime.utcnow()

            db.session.commit()
            m_name_fr = months_dict.get(target_month, ('', ''))[0]
            status_word = "rendu visible" if make_visible else "masqué"
            flash(f"Mois de {m_name_fr} {year} {status_word} pour {len(target_teacher_ids)} enseignant(s) avec succès.", 'success')
            return redirect(url_for('teacher_payment_visibility', year=year, month=target_month, tab='fast'))

        elif action == 'matrix_save':
            for t in teachers:
                for m_num in range(1, 13):
                    is_chk = f"cell_{t.id}_{m_num}" in request.form
                    rec = TeacherPaymentVisibility.query.filter_by(teacher_id=t.id, year=year, month=m_num).first()
                    if not rec:
                        if is_chk:
                            rec = TeacherPaymentVisibility(teacher_id=t.id, year=year, month=m_num, is_visible=True)
                            db.session.add(rec)
                    else:
                        rec.is_visible = is_chk
                        rec.updated_at = datetime.utcnow()
            db.session.commit()
            flash(f"La matrice annuelle de visibilité {year} a été enregistrée avec succès.", 'success')
            return redirect(url_for('teacher_payment_visibility', year=year, month=selected_month, tab='matrix'))

    # Load existing visibilities for this year
    all_vis = TeacherPaymentVisibility.query.filter_by(year=year).all()
    vis_map = {(v.teacher_id, v.month): v.is_visible for v in all_vis}

    # Counts per month
    month_visible_counts = {}
    for m_num, _, _ in months_list:
        month_visible_counts[m_num] = sum(1 for t in teachers if vis_map.get((t.id, m_num), False))

    # Counts per teacher (how many months visible out of 12)
    teacher_visible_counts = {}
    for t in teachers:
        teacher_visible_counts[t.id] = sum(1 for m_num in range(1, 13) if vis_map.get((t.id, m_num), False))

    available_years = sorted(list(set([today.year - 1, today.year, today.year + 1, year])))

    return render_template('teachers/payment_visibility.html',
                           year=year,
                           selected_month=selected_month,
                           active_tab=active_tab,
                           teachers=teachers,
                           months_list=months_list,
                           vis_map=vis_map,
                           month_visible_counts=month_visible_counts,
                           teacher_visible_counts=teacher_visible_counts,
                           available_years=available_years)


@app.route('/teachers/payment-visibility/toggle', methods=['POST'])
@login_required
@role_required('admin')
def teacher_payment_visibility_toggle():
    data = request.get_json(silent=True) or request.form
    teacher_id = _int(data.get('teacher_id'))
    year = _int(data.get('year'))
    month = _int(data.get('month'))
    visible_val = data.get('visible')

    if visible_val in [True, 1, '1', 'true', 'True']:
        visible = True
    else:
        visible = False

    if not teacher_id or not year or not month or month < 1 or month > 12:
        return jsonify({'success': False, 'error': 'Paramètres invalides'}), 400

    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({'success': False, 'error': 'Enseignant introuvable'}), 404

    rec = TeacherPaymentVisibility.query.filter_by(teacher_id=teacher_id, year=year, month=month).first()
    if not rec:
        rec = TeacherPaymentVisibility(teacher_id=teacher_id, year=year, month=month, is_visible=visible)
        db.session.add(rec)
    else:
        rec.is_visible = visible
        rec.updated_at = datetime.utcnow()

    db.session.commit()

    teacher_count = TeacherPaymentVisibility.query.filter_by(teacher_id=teacher_id, year=year, is_visible=True).count()
    month_count = TeacherPaymentVisibility.query.filter_by(year=year, month=month, is_visible=True).count()

    months_fr = {1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
                 7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'}

    return jsonify({
        'success': True,
        'teacher_id': teacher_id,
        'teacher_name': teacher.full_name,
        'year': year,
        'month': month,
        'month_name': months_fr.get(month, ''),
        'is_visible': rec.is_visible,
        'teacher_count': teacher_count,
        'month_count': month_count
    })


@app.route('/teachers/payment-visibility/batch-ajax', methods=['POST'])
@login_required
@role_required('admin')
def teacher_payment_visibility_batch_ajax():
    data = request.get_json(silent=True) or {}
    year = _int(data.get('year'))
    month = _int(data.get('month'))
    action_type = data.get('action_type', 'show')  # show, hide, show_all, hide_all
    teacher_ids = data.get('teacher_ids', [])

    if not year or not month or month < 1 or month > 12:
        return jsonify({'success': False, 'error': 'Paramètres invalides'}), 400

    all_active_teachers = Teacher.query.filter_by(active=True).all()
    if action_type in ['show_all', 'hide_all']:
        target_ids = [t.id for t in all_active_teachers]
        visible = (action_type == 'show_all')
    else:
        target_ids = [_int(tid) for tid in teacher_ids if tid]
        visible = (action_type == 'show')

    if not target_ids:
        return jsonify({'success': False, 'error': 'Aucun enseignant sélectionné'}), 400

    for tid in target_ids:
        rec = TeacherPaymentVisibility.query.filter_by(teacher_id=tid, year=year, month=month).first()
        if not rec:
            rec = TeacherPaymentVisibility(teacher_id=tid, year=year, month=month, is_visible=visible)
            db.session.add(rec)
        else:
            rec.is_visible = visible
            rec.updated_at = datetime.utcnow()

    db.session.commit()

    month_count = TeacherPaymentVisibility.query.filter_by(year=year, month=month, is_visible=True).count()
    months_fr = {1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
                 7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'}

    return jsonify({
        'success': True,
        'count': len(target_ids),
        'visible': visible,
        'month': month,
        'year': year,
        'month_name': months_fr.get(month, ''),
        'month_count': month_count
    })


@app.route('/teacher/my-payments')
@login_required
@role_required('teacher', 'admin')
def teacher_my_payments():
    u = current_user()
    teacher = None
    all_teachers = []

    if u.role == 'teacher':
        if not u.teacher_id:
            flash("Aucun profil enseignant n'est associé à ce compte d'accès.", 'danger')
            return redirect(url_for('attendance'))
        teacher = db.session.get(Teacher, u.teacher_id)
        if not teacher:
            flash("Profil enseignant introuvable.", 'danger')
            return redirect(url_for('attendance'))
    else:
        # Admin preview mode
        all_teachers = Teacher.query.filter_by(active=True).order_by(Teacher.first_name.asc(), Teacher.last_name.asc()).all()
        selected_tid = request.args.get('teacher_id', type=int)
        if selected_tid:
            teacher = db.session.get(Teacher, selected_tid)
        elif all_teachers:
            teacher = all_teachers[0]

    if not teacher:
        return render_template('teachers/my_payments.html',
                               teacher=None,
                               empty_state=True,
                               visible_entries=[],
                               available_months=[],
                               selected_month=None,
                               payroll=None,
                               all_teachers=all_teachers,
                               is_admin_preview=(u.role == 'admin'))

    # Query all visible months published by admin for this teacher
    visible_records = TeacherPaymentVisibility.query.filter_by(teacher_id=teacher.id, is_visible=True)\
        .order_by(TeacherPaymentVisibility.year.desc(), TeacherPaymentVisibility.month.desc()).all()

    if not visible_records:
        return render_template('teachers/my_payments.html',
                               teacher=teacher,
                               empty_state=True,
                               visible_entries=[],
                               available_months=[],
                               selected_month=None,
                               payroll=None,
                               all_teachers=all_teachers,
                               is_admin_preview=(u.role == 'admin'))

    # Available months as 'YYYY-MM'
    available_months = [f"{v.year:04d}-{v.month:02d}" for v in visible_records]

    requested_month = request.args.get('month', '').strip()
    if requested_month not in available_months:
        requested_month = available_months[0]

    try:
        y, m = map(int, requested_month.split('-'))
    except Exception:
        y, m = visible_records[0].year, visible_records[0].month
        requested_month = f"{y:04d}-{m:02d}"

    payroll = get_single_teacher_payroll_details(teacher, y, m)

    return render_template('teachers/my_payments.html',
                           teacher=teacher,
                           empty_state=False,
                           visible_entries=visible_records,
                           available_months=available_months,
                           selected_month=requested_month,
                           selected_year=y,
                           selected_month_num=m,
                           payroll=payroll,
                           all_teachers=all_teachers,
                           is_admin_preview=(u.role == 'admin'))


# ---------------------------------------------------------------------------
# Teacher Advances (Avances sur Salaires / التسبيقات على الأجور)
# ---------------------------------------------------------------------------
@app.route('/teachers/advances')
@login_required
@role_required('admin')
def teacher_advances():
    req_month = request.args.get('month', '').strip()
    selected_teacher_id = _int(request.args.get('teacher_id'))
    search_q = request.args.get('q', '').strip()

    query = TeacherAdvance.query

    if req_month:
        query = query.filter(TeacherAdvance.period_month == req_month)
    else:
        if not search_q and not selected_teacher_id:
            req_month = date.today().strftime('%Y-%m')
            query = query.filter(TeacherAdvance.period_month == req_month)

    if selected_teacher_id:
        query = query.filter(TeacherAdvance.teacher_id == selected_teacher_id)

    if search_q:
        q_like = f"%{search_q}%"
        query = query.join(Teacher).filter(
            db.or_(
                Teacher.first_name.ilike(q_like),
                Teacher.last_name.ilike(q_like),
                TeacherAdvance.receipt_no.ilike(q_like),
                TeacherAdvance.reference_no.ilike(q_like),
                TeacherAdvance.notes.ilike(q_like)
            )
        )

    advances = query.order_by(TeacherAdvance.date.desc(), TeacherAdvance.id.desc()).all()
    all_teachers = Teacher.query.filter_by(active=True).order_by(Teacher.first_name.asc()).all()

    total_amount = sum(a.amount for a in advances)
    teacher_count = len(set(a.teacher_id for a in advances))

    return render_template('teachers/advances.html',
                           advances=advances,
                           all_teachers=all_teachers,
                           req_month=req_month,
                           selected_teacher_id=selected_teacher_id,
                           search_q=search_q,
                           total_amount=total_amount,
                           teacher_count=teacher_count)


@app.route('/teachers/advances/new', methods=['POST'])
@login_required
@role_required('admin')
def teacher_advance_new():
    d = request.form
    teacher_id = _int(d.get('teacher_id'))
    amount = _f(d.get('amount'))
    adv_date = parse_date(d.get('date')) or date.today()
    period_month = d.get('period_month', '').strip() or adv_date.strftime('%Y-%m')
    payment_method = d.get('payment_method', 'Espèces').strip()
    reference_no = d.get('reference_no', '').strip()
    notes = d.get('notes', '').strip()
    sync_expense = d.get('sync_expense') == '1' or 'sync_expense' in d

    teacher = Teacher.query.get(teacher_id) if teacher_id else None
    if not teacher or amount <= 0:
        flash("Veuillez sélectionner un enseignant valide et un montant supérieur à 0 DH.", 'danger')
        return redirect(request.referrer or url_for('teacher_advances'))

    # Generate sequential receipt_no: ADV-YYYYMM-XXXX
    y, m = adv_date.year, adv_date.month
    prefix = f"ADV-{y:04d}{m:02d}-"
    last_adv = TeacherAdvance.query.filter(TeacherAdvance.receipt_no.like(f"{prefix}%")).order_by(TeacherAdvance.id.desc()).first()
    seq = 1
    if last_adv and last_adv.receipt_no:
        try:
            seq = int(last_adv.receipt_no.split('-')[-1]) + 1
        except Exception:
            seq = TeacherAdvance.query.count() + 1
    receipt_no = f"{prefix}{seq:04d}"

    u = current_user()
    expense_id = None

    # Sync with institute expenses/cash register
    if sync_expense:
        exp = Expense(
            expense_type='charge',
            category='Avances sur salaires',
            description=f"Avance sur salaire - Prof. {teacher.full_name} ({period_month})",
            amount=amount,
            date=adv_date,
            payment_method=payment_method,
            reference_no=receipt_no if not reference_no else f"{receipt_no} / {reference_no}",
            status='paid',
            paid_amount=amount,
            notes=f"Généré automatiquement par le module Avances Enseignants. {notes}".strip(),
            user_id=u.id if u else None
        )
        db.session.add(exp)
        db.session.flush()
        expense_id = exp.id

    adv = TeacherAdvance(
        receipt_no=receipt_no,
        teacher_id=teacher.id,
        amount=amount,
        date=adv_date,
        period_month=period_month,
        payment_method=payment_method,
        reference_no=reference_no,
        status='paid',
        expense_id=expense_id,
        notes=notes,
        recorded_by=u.id if u else None
    )
    db.session.add(adv)
    db.session.commit()

    log_action('teacher_advance_add', f"Avance {receipt_no}: {amount:.2f} DH versée à Prof. {teacher.full_name} (Mois {period_month})")
    flash(f"Avance de {amount:.2f} DH enregistrée avec succès pour Prof. {teacher.full_name} (N° {receipt_no}).", 'success')

    if d.get('print_after') == '1':
        return redirect(url_for('teacher_advance_receipt', aid=adv.id))

    return redirect(request.referrer or url_for('teacher_advances', month=period_month))


@app.route('/teachers/advances/<int:aid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def teacher_advance_delete(aid):
    adv = TeacherAdvance.query.get_or_404(aid)
    rec = adv.receipt_no
    amt = adv.amount
    t_name = adv.teacher.full_name if adv.teacher else 'Inconnu'

    # If linked to an Expense, delete it as well to keep accounts balanced
    if adv.expense_id:
        exp = Expense.query.get(adv.expense_id)
        if exp:
            db.session.delete(exp)

    db.session.delete(adv)
    db.session.commit()

    log_action('teacher_advance_delete', f"Suppression avance {rec}: {amt:.2f} DH de Prof. {t_name}")
    flash(f"L'avance {rec} ({amt:.2f} DH) a été supprimée avec succès.", 'success')
    return redirect(request.referrer or url_for('teacher_advances'))


@app.route('/teachers/advances/<int:aid>/receipt')
@login_required
@role_required('admin', 'secretary', 'teacher')
def teacher_advance_receipt(aid):
    adv = TeacherAdvance.query.get_or_404(aid)
    u = current_user()
    if u and u.role == 'teacher':
        if not u.teacher_id or adv.teacher_id != u.teacher_id:
            abort(403)
        try:
            py, pm = map(int, adv.period_month.split('-'))
            vis = TeacherPaymentVisibility.query.filter_by(teacher_id=u.teacher_id, year=py, month=pm, is_visible=True).first()
            if not vis:
                abort(403)
        except Exception:
            abort(403)

    fmt = request.args.get('format', 'a5')
    lang = request.args.get('lang', 'fr')

    try:
        y, m = map(int, adv.period_month.split('-'))
    except Exception:
        y, m = adv.date.year, adv.date.month
    months_fr = {1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
                 7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'}
    months_ar = {1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'ماي', 6: 'يونيو',
                 7: 'يوليوز', 8: 'غشت', 9: 'شتنبر', 10: 'أكتوبر', 11: 'نونبر', 12: 'دجنبر'}
    month_display = f"{months_fr.get(m, '')} {y}" if lang == 'fr' else f"{months_ar.get(m, '')} {y}"

    return render_template('teachers/advance_receipt.html',
                           adv=adv,
                           teacher=adv.teacher,
                           fmt=fmt,
                           lang=lang,
                           month_display=month_display)


# ---------------------------------------------------------------------------
# Teacher Expenses & Copies (Frais & Tirages Enseignants / مصاريف ونسخ وثائق الأساتذة)
# ---------------------------------------------------------------------------
@app.route('/teachers/expenses')
@login_required
@role_required('admin', 'secretary')
def teacher_expenses():
    req_month = request.args.get('month', '').strip()
    selected_teacher_id = _int(request.args.get('teacher_id'))
    selected_type = request.args.get('expense_type', '').strip()
    search_q = request.args.get('q', '').strip()

    query = TeacherExpense.query

    if req_month:
        query = query.filter(TeacherExpense.period_month == req_month)
    else:
        if not search_q and not selected_teacher_id and not selected_type:
            req_month = date.today().strftime('%Y-%m')
            query = query.filter(TeacherExpense.period_month == req_month)

    if selected_teacher_id:
        query = query.filter(TeacherExpense.teacher_id == selected_teacher_id)

    if selected_type:
        query = query.filter(TeacherExpense.expense_type == selected_type)

    if search_q:
        q_like = f"%{search_q}%"
        query = query.join(Teacher).filter(
            db.or_(
                Teacher.first_name.ilike(q_like),
                Teacher.last_name.ilike(q_like),
                TeacherExpense.receipt_no.ilike(q_like),
                TeacherExpense.title.ilike(q_like),
                TeacherExpense.notes.ilike(q_like)
            )
        )

    expenses = query.order_by(TeacherExpense.date.desc(), TeacherExpense.id.desc()).all()
    all_teachers = Teacher.query.filter_by(active=True).order_by(Teacher.first_name.asc()).all()

    total_amount = sum(e.amount for e in expenses)
    total_copies = sum((e.quantity or 0) for e in expenses if e.expense_type == 'copies')
    teacher_count = len(set(e.teacher_id for e in expenses))

    default_copy_price = SH.get_float('teacher_copy_price_page', 0.50)
    charge_items = TeacherChargeItem.query.filter_by(active=True).order_by(TeacherChargeItem.id.asc()).all()

    return render_template('teachers/expenses.html',
                           expenses=expenses,
                           all_teachers=all_teachers,
                           req_month=req_month,
                           selected_teacher_id=selected_teacher_id,
                           selected_type=selected_type,
                           search_q=search_q,
                           total_amount=total_amount,
                           total_copies=total_copies,
                           teacher_count=teacher_count,
                           default_copy_price=default_copy_price,
                           charge_items=charge_items)


@app.route('/teachers/expenses/new', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def teacher_expense_new():
    d = request.form
    teacher_id = _int(d.get('teacher_id'))
    charge_item_id = _int(d.get('charge_item_id'))
    expense_type = d.get('expense_type', 'copies').strip()
    title = d.get('title', '').strip()
    custom_name = d.get('custom_item_name', '').strip()
    unit_label = d.get('unit_label', 'unité').strip() or 'unité'
    save_to_catalog = d.get('save_to_catalog') == '1' or 'save_to_catalog' in d
    unit_price = _f(d.get('unit_price'))
    quantity = _int(d.get('quantity'))
    if quantity <= 0:
        quantity = 1

    amount = _f(d.get('amount'))
    # If amount not explicitly passed or 0, calculate from quantity * unit_price
    if amount <= 0 and unit_price > 0 and quantity > 0:
        amount = round(quantity * unit_price, 2)

    exp_date = parse_date(d.get('date')) or date.today()
    period_month = d.get('period_month', '').strip() or exp_date.strftime('%Y-%m')
    notes = d.get('notes', '').strip()
    sync_expense = d.get('sync_expense') == '1' or 'sync_expense' in d

    teacher = Teacher.query.get(teacher_id) if teacher_id else None
    if not teacher or amount <= 0:
        flash("Veuillez sélectionner un enseignant valide et un montant supérieur à 0 DH.", 'danger')
        return redirect(request.referrer or url_for('teacher_expenses'))

    # If selected an existing item from catalog
    if charge_item_id:
        c_item = TeacherChargeItem.query.get(charge_item_id)
        if c_item:
            if not title:
                title = f"{c_item.name} ({quantity} {c_item.unit_label})"
            if not expense_type or expense_type == 'copies':
                expense_type = c_item.category

    # If custom item was added and option to save to catalog is checked (or custom_name given)
    if custom_name:
        if not title:
            title = f"{custom_name} ({quantity} {unit_label})"
        if save_to_catalog:
            existing_cat = TeacherChargeItem.query.filter(TeacherChargeItem.name.ilike(custom_name)).first()
            if not existing_cat:
                new_item = TeacherChargeItem(
                    name=custom_name,
                    category=expense_type,
                    unit_price=unit_price,
                    unit_label=unit_label,
                    is_default=False,
                    active=True
                )
                db.session.add(new_item)
                db.session.flush()

    if not title:
        if expense_type == 'copies':
            title = f"Tirage de documents ({quantity} copies @ {unit_price:.2f} DH)"
        elif expense_type == 'book':
            title = "Achat manuel / livre"
        elif expense_type == 'paper':
            title = f"Papier / Ramettes ({quantity} unités)"
        else:
            title = "Charge déductible enseignant"

    # Generate sequential receipt_no: EXP-T-YYYYMM-XXXX
    y, m = exp_date.year, exp_date.month
    prefix = f"EXP-T-{y:04d}{m:02d}-"
    last_exp = TeacherExpense.query.filter(TeacherExpense.receipt_no.like(f"{prefix}%")).order_by(TeacherExpense.id.desc()).first()
    seq = 1
    if last_exp and last_exp.receipt_no:
        try:
            seq = int(last_exp.receipt_no.split('-')[-1]) + 1
        except Exception:
            seq = TeacherExpense.query.count() + 1
    receipt_no = f"{prefix}{seq:04d}"

    u = current_user()
    expense_id = None

    # Sync with institute general expenses / caisse if requested
    if sync_expense:
        caisse_exp = Expense(
            expense_type='charge',
            category='Photocopies & Tirages Enseignants' if expense_type == 'copies' else 'Charges & Fournitures Enseignants',
            description=f"{title} - Prof. {teacher.full_name} ({period_month})",
            amount=amount,
            date=exp_date,
            payment_method='Retenue sur salaire',
            reference_no=receipt_no,
            status='paid',
            paid_amount=amount,
            teacher_id=teacher.id,
            notes=f"Déduit sur salaire de Prof. {teacher.full_name} (Mois {period_month}). {notes}".strip(),
            user_id=u.id if u else None
        )
        db.session.add(caisse_exp)
        db.session.flush()
        expense_id = caisse_exp.id

    t_exp = TeacherExpense(
        receipt_no=receipt_no,
        teacher_id=teacher.id,
        expense_type=expense_type,
        title=title,
        unit_price=unit_price,
        quantity=quantity,
        amount=amount,
        date=exp_date,
        period_month=period_month,
        payment_method='Retenue sur salaire',
        status='pending',
        expense_id=expense_id,
        notes=notes,
        recorded_by=u.id if u else None
    )
    db.session.add(t_exp)
    db.session.flush()

    if expense_id:
        caisse_exp.teacher_expense_id = t_exp.id

    db.session.commit()

    log_action('teacher_expense_add', f"Charge {receipt_no}: {amount:.2f} DH imputée à Prof. {teacher.full_name} (Mois {period_month})")
    flash(f"Frais de {amount:.2f} DH enregistrés avec succès pour Prof. {teacher.full_name} (N° {receipt_no}) et déduits sur la paie de {period_month}.", 'success')

    if d.get('print_after') == '1':
        return redirect(url_for('teacher_expense_receipt', teid=t_exp.id))

    return redirect(request.referrer or url_for('teacher_expenses', month=period_month))


@app.route('/teachers/expenses/<int:teid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def teacher_expense_delete(teid):
    t_exp = TeacherExpense.query.get_or_404(teid)
    rec = t_exp.receipt_no
    amt = t_exp.amount
    t_name = t_exp.teacher.full_name if t_exp.teacher else 'Inconnu'

    # If linked to an Expense, delete it as well
    if t_exp.expense_id:
        exp = Expense.query.get(t_exp.expense_id)
        if exp:
            db.session.delete(exp)

    db.session.delete(t_exp)
    db.session.commit()

    log_action('teacher_expense_delete', f"Suppression charge {rec}: {amt:.2f} DH de Prof. {t_name}")
    flash(f"La charge {rec} ({amt:.2f} DH) a été supprimée avec succès et rétablie dans la paie de l'enseignant.", 'success')
    return redirect(request.referrer or url_for('teacher_expenses'))


@app.route('/teachers/expenses/<int:teid>/receipt')
@login_required
@role_required('admin', 'secretary', 'teacher')
def teacher_expense_receipt(teid):
    t_exp = TeacherExpense.query.get_or_404(teid)
    u = current_user()
    if u and u.role == 'teacher':
        if not u.teacher_id or t_exp.teacher_id != u.teacher_id:
            abort(403)
        try:
            py, pm = map(int, t_exp.period_month.split('-'))
            vis = TeacherPaymentVisibility.query.filter_by(teacher_id=u.teacher_id, year=py, month=pm, is_visible=True).first()
            if not vis:
                abort(403)
        except Exception:
            abort(403)

    fmt = request.args.get('format', 'a5')
    lang = request.args.get('lang', 'fr')

    try:
        y, m = map(int, t_exp.period_month.split('-'))
    except Exception:
        y, m = t_exp.date.year, t_exp.date.month

    months_fr = {1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
                 7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'}
    months_ar = {1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'ماي', 6: 'يونيو',
                 7: 'يوليوز', 8: 'غشت', 9: 'شتنبر', 10: 'أكتوبر', 11: 'نونبر', 12: 'دجنبر'}
    month_display = f"{months_fr.get(m, '')} {y}" if lang == 'fr' else f"{months_ar.get(m, '')} {y}"

    return render_template('teachers/expense_receipt.html',
                           t_exp=t_exp,
                           teacher=t_exp.teacher,
                           fmt=fmt,
                           lang=lang,
                           month_display=month_display)


# ---------------------------------------------------------------------------
# Teacher Salary Payouts & Anti-Duplicate Protection (ركلات الرواتب ومنع التكرار)
# ---------------------------------------------------------------------------
@app.route('/teachers/payroll/pay', methods=['POST'])
@login_required
@role_required('admin')
def teacher_payroll_pay():
    d = request.form
    teacher_id = _int(d.get('teacher_id'))
    period_month = d.get('period_month', '').strip()
    gross_amount = _f(d.get('gross_amount'))
    advances_deducted = _f(d.get('advances_deducted'))
    expenses_deducted = _f(d.get('expenses_deducted'))
    prior_credit_deducted = _f(d.get('prior_credit_deducted'))
    book_sales_added = _f(d.get('book_sales_added'))
    net_amount = _f(d.get('net_amount'))
    pay_date = parse_date(d.get('payment_date')) or date.today()
    payment_method = d.get('payment_method', 'Espèces').strip()
    reference_no = d.get('reference_no', '').strip()
    notes = d.get('notes', '').strip()
    sync_expense = d.get('sync_expense') == '1' or 'sync_expense' in d

    teacher = Teacher.query.get(teacher_id) if teacher_id else None
    if not teacher or not period_month or net_amount < 0:
        flash("Informations de règlement invalides.", 'danger')
        return redirect(request.referrer or url_for('teachers_payroll'))

    # STRICT ANTI-DUPLICATE SALARY CHECK
    existing_payout = TeacherSalaryPayout.query.filter_by(
        teacher_id=teacher.id,
        period_month=period_month
    ).filter(TeacherSalaryPayout.status != 'cancelled').first()

    if existing_payout:
        flash(f"🚨 ALERTE DOUBLON : Le salaire de Prof. {teacher.full_name} pour le mois {period_month} a DÉJÀ ÉTÉ RÉGLÉ le {existing_payout.payment_date.strftime('%d/%m/%Y')} (Montant versé : {existing_payout.net_amount:.2f} DH, Reçu N° {existing_payout.receipt_no}, Mode : {existing_payout.payment_method}). Pour votre sécurité financière, le paiement en double a été automatiquement bloqué !", 'danger')
        return redirect(url_for('teachers_payroll', month=period_month))

    # Sequential receipt_no: SAL-YYYYMM-XXXX
    y, m = pay_date.year, pay_date.month
    prefix = f"SAL-{y:04d}{m:02d}-"
    last_payout = TeacherSalaryPayout.query.filter(TeacherSalaryPayout.receipt_no.like(f"{prefix}%")).order_by(TeacherSalaryPayout.id.desc()).first()
    seq = 1
    if last_payout and last_payout.receipt_no:
        try:
            seq = int(last_payout.receipt_no.split('-')[-1]) + 1
        except Exception:
            seq = TeacherSalaryPayout.query.count() + 1
    receipt_no = f"{prefix}{seq:04d}"

    u = current_user()
    expense_id = None

    # Register in general institute cash ledger / expenses
    if sync_expense and net_amount > 0:
        prior_note = f", Report mois préc. déduit : -{prior_credit_deducted:.2f} DH" if prior_credit_deducted > 0 else ""
        books_note = f", Ventes articles/livres ajoutées : +{book_sales_added:.2f} DH" if book_sales_added > 0 else ""
        caisse_exp = Expense(
            expense_type='charge',
            category='Salaires & Primes',
            description=f"Règlement salaire net - Prof. {teacher.full_name} ({period_month})",
            amount=net_amount,
            date=pay_date,
            payment_method=payment_method,
            reference_no=receipt_no if not reference_no else f"{receipt_no} / {reference_no}",
            status='paid',
            paid_amount=net_amount,
            teacher_id=teacher.id,
            notes=f"Règlement officiel salaire fin de mois. Brut Dû : {gross_amount:.2f} DH{books_note}, Avances déduites : -{advances_deducted:.2f} DH, Frais & Copies déduits : -{expenses_deducted:.2f} DH{prior_note}. {notes}".strip(),
            user_id=u.id if u else None
        )
        db.session.add(caisse_exp)
        db.session.flush()
        expense_id = caisse_exp.id

    payout = TeacherSalaryPayout(
        receipt_no=receipt_no,
        teacher_id=teacher.id,
        period_month=period_month,
        gross_amount=gross_amount,
        advances_deducted=advances_deducted,
        expenses_deducted=expenses_deducted,
        prior_credit_deducted=prior_credit_deducted,
        book_sales_added=book_sales_added,
        net_amount=net_amount,
        payment_date=pay_date,
        payment_method=payment_method,
        reference_no=reference_no,
        status='paid',
        expense_id=expense_id,
        notes=notes,
        recorded_by=u.id if u else None
    )
    db.session.add(payout)

    # Marquer les avances et les charges de ce mois comme déduites
    month_advs = TeacherAdvance.query.filter_by(teacher_id=teacher.id, period_month=period_month)\
        .filter(TeacherAdvance.status != 'cancelled').all()
    for adv in month_advs:
        adv.status = 'deducted'

    month_exps = TeacherExpense.query.filter_by(teacher_id=teacher.id, period_month=period_month)\
        .filter(TeacherExpense.status != 'cancelled').all()
    for exp in month_exps:
        exp.status = 'deducted'

    db.session.commit()

    log_action('teacher_salary_pay', f"Salaire {receipt_no}: {net_amount:.2f} DH versé à Prof. {teacher.full_name} pour le mois {period_month}")
    flash(f"✅ Salaire de {net_amount:.2f} DH réglé avec succès pour Prof. {teacher.full_name} (Mois {period_month}, Reçu N° {receipt_no}). Sortie de caisse enregistrée.", 'success')

    if d.get('print_after') == '1':
        return redirect(url_for('teacher_salary_receipt', pid=payout.id))

    return redirect(url_for('teachers_payroll', month=period_month))


@app.route('/teachers/payroll/payout/<int:pid>/cancel', methods=['POST'])
@login_required
@role_required('admin')
def teacher_payroll_cancel_payout(pid):
    payout = TeacherSalaryPayout.query.get_or_404(pid)
    rec = payout.receipt_no
    amt = payout.net_amount
    t_name = payout.teacher.full_name if payout.teacher else 'Inconnu'
    month = payout.period_month
    t_id = payout.teacher_id

    if payout.expense_id:
        exp = Expense.query.get(payout.expense_id)
        if exp:
            db.session.delete(exp)

    # Rétablir les statuts des avances et charges du mois
    month_advs = TeacherAdvance.query.filter_by(teacher_id=t_id, period_month=month)\
        .filter(TeacherAdvance.status == 'deducted').all()
    for adv in month_advs:
        adv.status = 'paid'

    month_exps = TeacherExpense.query.filter_by(teacher_id=t_id, period_month=month)\
        .filter(TeacherExpense.status == 'deducted').all()
    for exp in month_exps:
        exp.status = 'pending'

    db.session.delete(payout)
    db.session.commit()

    log_action('teacher_salary_cancel', f"Annulation règlement salaire {rec}: {amt:.2f} DH de Prof. {t_name} ({month})")
    flash(f"Le règlement de salaire {rec} ({amt:.2f} DH) a été annulé avec succès. L'état repasse à 'En attente de règlement'.", 'warning')
    return redirect(url_for('teachers_payroll', month=month))


@app.route('/teachers/payroll/payout/<int:pid>/receipt')
@login_required
@role_required('admin', 'secretary', 'teacher')
def teacher_salary_receipt(pid):
    payout = TeacherSalaryPayout.query.get_or_404(pid)
    u = current_user()
    if u and u.role == 'teacher':
        if not u.teacher_id or payout.teacher_id != u.teacher_id:
            abort(403)
        try:
            py, pm = map(int, payout.period_month.split('-'))
            vis = TeacherPaymentVisibility.query.filter_by(teacher_id=u.teacher_id, year=py, month=pm, is_visible=True).first()
            if not vis:
                abort(403)
        except Exception:
            abort(403)

    fmt = request.args.get('format', 'a5')
    lang = request.args.get('lang', 'fr')

    try:
        y, m = map(int, payout.period_month.split('-'))
    except Exception:
        y, m = payout.payment_date.year, payout.payment_date.month

    months_fr = {1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
                 7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'}
    months_ar = {1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'ماي', 6: 'يونيو',
                 7: 'يوليوز', 8: 'غشت', 9: 'شتنبر', 10: 'أكتوبر', 11: 'نونبر', 12: 'دجنبر'}
    month_display = f"{months_fr.get(m, '')} {y}" if lang == 'fr' else f"{months_ar.get(m, '')} {y}"

    return render_template('teachers/salary_receipt.html',
                           payout=payout,
                           teacher=payout.teacher,
                           fmt=fmt,
                           lang=lang,
                           month_display=month_display)


@app.route('/teachers/charges/catalog', methods=['GET'])
@login_required
@role_required('admin', 'secretary')
def teacher_charges_catalog():
    items = TeacherChargeItem.query.filter_by(active=True).order_by(TeacherChargeItem.id.asc()).all()
    return jsonify([
        {
            'id': i.id,
            'name': i.name,
            'category': i.category,
            'unit_price': i.unit_price,
            'unit_label': i.unit_label
        } for i in items
    ])


@app.route('/teachers/charges/catalog/add', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def teacher_charge_catalog_add():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'supplies').strip()
    unit_price = _f(request.form.get('unit_price'))
    unit_label = request.form.get('unit_label', 'unité').strip() or 'unité'

    if not name:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Nom requis'}), 400
        flash("Le nom de l'article est obligatoire.", 'danger')
        return redirect(request.referrer or url_for('teacher_expenses'))

    item = TeacherChargeItem.query.filter(TeacherChargeItem.name.ilike(name)).first()
    if not item:
        item = TeacherChargeItem(
            name=name,
            category=category,
            unit_price=unit_price,
            unit_label=unit_label,
            active=True
        )
        db.session.add(item)
        db.session.commit()
        log_action('charge_item_add', f"Nouvel article catalogue: {name} ({unit_price:.2f} DH)")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'item': {
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'unit_price': item.unit_price,
                'unit_label': item.unit_label
            }
        })

    flash(f"Article '{name}' ({unit_price:.2f} DH) enregistré avec succès dans le catalogue.", 'success')
    return redirect(request.referrer or url_for('teacher_expenses'))





# ---------------------------------------------------------------------------
# Teacher Candidates (Pré-Inscription / Banque CV)
# ---------------------------------------------------------------------------
CANDIDATES_CV_FOLDER = os.path.join(BASE, 'static', 'uploads', 'candidates_cv')
os.makedirs(CANDIDATES_CV_FOLDER, exist_ok=True)

CANDIDATE_STATUSES = ['pending', 'contacted', 'interview', 'hired', 'rejected', 'archived']
CANDIDATE_STATUS_LABELS = {
    'pending': 'En attente',
    'contacted': 'Contacté(e)',
    'interview': 'Entretien',
    'hired': 'Recruté(e)',
    'rejected': 'Rejeté(e)',
    'archived': 'Archivé(e)',
}
CANDIDATE_SOURCES = {
    'walk-in': 'Dépôt en personne',
    'referral': 'Recommandation',
    'online': 'En ligne',
    'other': 'Autre',
}


@app.route('/teachers/candidates')
@login_required
@role_required('admin', 'secretary')
def teacher_candidates():
    q_status = request.args.get('status', '')
    q_specialty = request.args.get('specialty', '')
    q_search = request.args.get('q', '').strip()

    query = TeacherCandidate.query.order_by(TeacherCandidate.created_at.desc())

    if q_status:
        query = query.filter(TeacherCandidate.status == q_status)
    if q_specialty:
        query = query.filter(TeacherCandidate.specialty.ilike(f'%{q_specialty}%'))
    if q_search:
        like = f'%{q_search}%'
        query = query.filter(
            db.or_(
                TeacherCandidate.first_name.ilike(like),
                TeacherCandidate.last_name.ilike(like),
                TeacherCandidate.phone.ilike(like),
                TeacherCandidate.specialty.ilike(like),
                TeacherCandidate.email.ilike(like),
            )
        )

    candidates = query.all()

    # Stats per status
    stats = {}
    for s in CANDIDATE_STATUSES:
        stats[s] = TeacherCandidate.query.filter_by(status=s).count()

    # All distinct specialties for filter dropdown
    specialties = db.session.query(TeacherCandidate.specialty)\
        .filter(TeacherCandidate.specialty.isnot(None))\
        .filter(TeacherCandidate.specialty != '')\
        .distinct().all()
    specialties = sorted(set(s[0].strip() for s in specialties if s[0]))

    return render_template(
        'teachers/candidates.html',
        candidates=candidates,
        stats=stats,
        specialties=specialties,
        status_labels=CANDIDATE_STATUS_LABELS,
        sources=CANDIDATE_SOURCES,
        q_status=q_status,
        q_specialty=q_specialty,
        q_search=q_search,
        statuses=CANDIDATE_STATUSES,
    )


@app.route('/teachers/candidates/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def teacher_candidate_new():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        if not first_name or not last_name:
            flash("Le prénom et le nom sont obligatoires.", 'danger')
            return redirect(url_for('teacher_candidates'))

        # CV file upload
        cv_filename = None
        cv_file = request.files.get('cv_file')
        if cv_file and cv_file.filename:
            ext = os.path.splitext(cv_file.filename)[1].lower()
            if ext in ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']:
                safe_name = f"cv_{last_name.lower()}_{first_name.lower()}_{int(datetime.utcnow().timestamp())}{ext}"
                cv_file.save(os.path.join(CANDIDATES_CV_FOLDER, safe_name))
                cv_filename = safe_name

        dob_str = request.form.get('date_of_birth', '')
        dob = None
        if dob_str:
            try:
                from datetime import date as _date
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except Exception:
                pass

        dep_str = request.form.get('deposit_date', '')
        dep_date = datetime.utcnow().date()
        if dep_str:
            try:
                dep_date = datetime.strptime(dep_str, '%Y-%m-%d').date()
            except Exception:
                pass

        cand = TeacherCandidate(
            first_name=first_name,
            last_name=last_name,
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            cin=request.form.get('cin', '').strip(),
            gender=request.form.get('gender', 'M'),
            date_of_birth=dob,
            city=request.form.get('city', '').strip(),
            specialty=request.form.get('specialty', '').strip(),
            diplomas=request.form.get('diplomas', '').strip(),
            years_experience=int(request.form.get('years_experience') or 0),
            availability=request.form.get('availability', '').strip(),
            expected_salary=_f(request.form.get('expected_salary')),
            source=request.form.get('source', 'walk-in'),
            deposit_date=dep_date,
            cv_filename=cv_filename,
            notes=request.form.get('notes', '').strip(),
            status='pending',
        )
        db.session.add(cand)
        db.session.commit()
        log_action('candidate_add', f"Candidat ajouté: {cand.full_name} ({cand.specialty})")
        flash(f"✅ Candidat {cand.full_name} ajouté avec succès.", 'success')
        return redirect(url_for('teacher_candidates'))

    return redirect(url_for('teacher_candidates'))


@app.route('/teachers/candidates/<int:cid>/edit', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def teacher_candidate_edit(cid):
    cand = TeacherCandidate.query.get_or_404(cid)

    cand.first_name = request.form.get('first_name', cand.first_name).strip()
    cand.last_name = request.form.get('last_name', cand.last_name).strip()
    cand.phone = request.form.get('phone', '').strip()
    cand.email = request.form.get('email', '').strip()
    cand.cin = request.form.get('cin', '').strip()
    cand.gender = request.form.get('gender', 'M')
    cand.city = request.form.get('city', '').strip()
    cand.specialty = request.form.get('specialty', '').strip()
    cand.diplomas = request.form.get('diplomas', '').strip()
    cand.years_experience = int(request.form.get('years_experience') or 0)
    cand.availability = request.form.get('availability', '').strip()
    cand.expected_salary = _f(request.form.get('expected_salary'))
    cand.source = request.form.get('source', cand.source)
    cand.notes = request.form.get('notes', '').strip()
    cand.status = request.form.get('status', cand.status)
    cand.status_note = request.form.get('status_note', '').strip()

    dob_str = request.form.get('date_of_birth', '')
    if dob_str:
        try:
            cand.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except Exception:
            pass

    dep_str = request.form.get('deposit_date', '')
    if dep_str:
        try:
            cand.deposit_date = datetime.strptime(dep_str, '%Y-%m-%d').date()
        except Exception:
            pass

    # New CV upload
    cv_file = request.files.get('cv_file')
    if cv_file and cv_file.filename:
        ext = os.path.splitext(cv_file.filename)[1].lower()
        if ext in ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']:
            safe_name = f"cv_{cand.last_name.lower()}_{cand.first_name.lower()}_{int(datetime.utcnow().timestamp())}{ext}"
            cv_file.save(os.path.join(CANDIDATES_CV_FOLDER, safe_name))
            cand.cv_filename = safe_name

    cand.updated_at = datetime.utcnow()
    db.session.commit()
    log_action('candidate_edit', f"Candidat modifié: {cand.full_name}")
    flash(f"✅ Dossier de {cand.full_name} mis à jour.", 'success')
    return redirect(url_for('teacher_candidates'))


@app.route('/teachers/candidates/<int:cid>/status', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def teacher_candidate_status(cid):
    cand = TeacherCandidate.query.get_or_404(cid)
    new_status = request.form.get('status', cand.status)
    note = request.form.get('status_note', '').strip()
    if new_status in CANDIDATE_STATUSES:
        cand.status = new_status
        cand.status_note = note
        cand.updated_at = datetime.utcnow()
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'status': new_status, 'label': CANDIDATE_STATUS_LABELS.get(new_status, new_status)})
    return redirect(url_for('teacher_candidates'))


@app.route('/teachers/candidates/<int:cid>/hire', methods=['POST'])
@login_required
@role_required('admin')
def teacher_candidate_hire(cid):
    """Convert a candidate to an active Teacher record."""
    cand = TeacherCandidate.query.get_or_404(cid)

    if cand.converted_teacher_id:
        existing = Teacher.query.get(cand.converted_teacher_id)
        if existing:
            flash(f"⚠️ {cand.full_name} a déjà été recruté(e) (Prof #{existing.id}).", 'warning')
            return redirect(url_for('teacher_candidates'))

    # Create Teacher record from candidate data
    teacher = Teacher(
        prenom=cand.first_name,
        nom=cand.last_name,
        telephone=cand.phone or '',
        email=cand.email or '',
        cin=cand.cin or '',
        specialite=cand.specialty or '',
        remarques=f"Candidat converti le {datetime.utcnow().strftime('%d/%m/%Y')}. {cand.notes or ''}".strip(),
        type_salaire='fixed',
        montant_salaire=cand.expected_salary or 0.0,
    )
    db.session.add(teacher)
    db.session.flush()  # get teacher.id

    cand.status = 'hired'
    cand.converted_teacher_id = teacher.id
    cand.converted_at = datetime.utcnow()
    cand.updated_at = datetime.utcnow()

    db.session.commit()
    log_action('candidate_hire', f"Candidat {cand.full_name} converti en enseignant #{teacher.id}")
    flash(f"🎉 {cand.full_name} a été recruté(e) avec succès ! Fiche enseignant créée (#T{teacher.id}).", 'success')
    return redirect(url_for('teacher_candidates'))


@app.route('/teachers/candidates/<int:cid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def teacher_candidate_delete(cid):
    cand = TeacherCandidate.query.get_or_404(cid)
    name = cand.full_name
    # Delete CV file if exists
    if cand.cv_filename:
        try:
            os.remove(os.path.join(CANDIDATES_CV_FOLDER, cand.cv_filename))
        except Exception:
            pass
    db.session.delete(cand)
    db.session.commit()
    log_action('candidate_delete', f"Candidat supprimé: {name}")
    flash(f"🗑️ Dossier de {name} supprimé.", 'info')
    return redirect(url_for('teacher_candidates'))


@app.route('/teachers/candidates/cv/<filename>')
@login_required
def teacher_candidate_cv(filename):
    """Serve candidate CV file."""
    return send_from_directory(CANDIDATES_CV_FOLDER, filename)


# ---------------------------------------------------------------------------
# Employee & Staff Management and Payroll (Personnel & Employés d'Institut)
# ---------------------------------------------------------------------------

EMPLOYEE_JOB_TITLES = [
    'Secrétaire Administrative',
    'Assistante d\'Accueil & Scolarité',
    'Agent d\'Entretien & Ménage',
    'Gardien / Agent de Sécurité',
    'Responsable Pédagogique',
    'Comptable / Gestionnaire',
    'Technicien Informatique',
    'Chauffeur / Transport',
    'Autre Employé(e)'
]

EMPLOYEE_DEPARTMENTS = [
    'Administration',
    'Accueil & Scolarité',
    'Entretien / Ménage',
    'Sécurité',
    'Technique & Logistique',
    'Autre'
]


def _generate_employee_code():
    last = Employee.query.order_by(Employee.id.desc()).first()
    seq = (last.id + 1) if last else 1
    return f"EMP-{seq:03d}"


def _seed_default_employees_if_empty():
    if Employee.query.count() == 0:
        emp1 = Employee(
            code="EMP-001",
            first_name="Hiba",
            last_name="ILAS",
            job_title="Secrétaire Administrative",
            department="Administration",
            salary_type="monthly",
            base_salary=3200.0,
            hire_date=date(2023, 9, 1),
            phone="0661000001",
            active=True,
            notes="Secrétariat général et accueil des parents"
        )
        emp2 = Employee(
            code="EMP-002",
            first_name="Fatima",
            last_name="EL HASSANI",
            job_title="Assistante d'Accueil & Scolarité",
            department="Accueil & Scolarité",
            salary_type="monthly",
            base_salary=2800.0,
            hire_date=date(2024, 1, 15),
            phone="0662000002",
            active=True
        )
        emp3 = Employee(
            code="EMP-003",
            first_name="Khadija",
            last_name="MANSOURI",
            job_title="Agent d'Entretien & Ménage",
            department="Entretien / Ménage",
            salary_type="monthly",
            base_salary=2200.0,
            hire_date=date(2023, 10, 1),
            phone="0663000003",
            active=True
        )
        emp4 = Employee(
            code="EMP-004",
            first_name="Abdelkader",
            last_name="BENNANI",
            job_title="Gardien / Agent de Sécurité",
            department="Sécurité",
            salary_type="monthly",
            base_salary=2500.0,
            hire_date=date(2023, 9, 1),
            phone="0664000004",
            active=True
        )
        db.session.add_all([emp1, emp2, emp3, emp4])
        db.session.commit()


@app.route('/employees')
@login_required
@role_required('admin', 'secretary')
def employees():
    _seed_default_employees_if_empty()
    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'active')
    dept_filter = request.args.get('department', '').strip()

    query = Employee.query

    if status_filter == 'active':
        query = query.filter_by(active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(active=False)

    if dept_filter:
        query = query.filter_by(department=dept_filter)

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Employee.first_name.ilike(like),
                Employee.last_name.ilike(like),
                Employee.code.ilike(like),
                Employee.job_title.ilike(like),
                Employee.phone.ilike(like),
                Employee.cin.ilike(like),
            )
        )

    employee_list = query.order_by(Employee.active.desc(), Employee.id.asc()).all()

    total_count = Employee.query.count()
    active_count = Employee.query.filter_by(active=True).count()
    total_base_payroll = sum((e.base_salary or 0.0) for e in Employee.query.filter_by(active=True).all())

    return render_template('employees/list.html',
                           employees=employee_list,
                           q=q,
                           status_filter=status_filter,
                           dept_filter=dept_filter,
                           departments=EMPLOYEE_DEPARTMENTS,
                           total_count=total_count,
                           active_count=active_count,
                           total_base_payroll=total_base_payroll)


@app.route('/employees/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def employee_new():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        if not first_name or not last_name:
            flash("Le prénom et le nom de l'employé sont obligatoires.", 'danger')
            return redirect(url_for('employee_new'))

        code = request.form.get('code', '').strip() or _generate_employee_code()
        existing = Employee.query.filter_by(code=code).first()
        if existing:
            code = _generate_employee_code()

        base_salary = _f(request.form.get('base_salary'))
        h_date = parse_date(request.form.get('hire_date')) or date.today()

        emp = Employee(
            code=code,
            first_name=first_name,
            last_name=last_name,
            cin=request.form.get('cin', '').strip(),
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            job_title=request.form.get('job_title', '').strip() or 'Employé(e)',
            department=request.form.get('department', '').strip() or 'Administration',
            salary_type=request.form.get('salary_type', 'monthly'),
            base_salary=base_salary,
            hire_date=h_date,
            bank_name=request.form.get('bank_name', '').strip(),
            rib=request.form.get('rib', '').strip(),
            cnss_no=request.form.get('cnss_no', '').strip(),
            notes=request.form.get('notes', '').strip(),
            active=True
        )
        db.session.add(emp)
        db.session.commit()
        log_action('employee_add', f"Employé créé: {emp.full_name} ({emp.code})")
        flash(f"Employé {emp.full_name} ({emp.code}) enregistré avec succès.", 'success')
        return redirect(url_for('employees'))

    next_code = _generate_employee_code()
    return render_template('employees/form.html',
                           employee=None,
                           next_code=next_code,
                           departments=EMPLOYEE_DEPARTMENTS,
                           job_titles=EMPLOYEE_JOB_TITLES)


@app.route('/employees/<int:eid>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def employee_edit(eid):
    emp = Employee.query.get_or_404(eid)
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        if not first_name or not last_name:
            flash("Le prénom et le nom sont obligatoires.", 'danger')
            return redirect(url_for('employee_edit', eid=emp.id))

        emp.first_name = first_name
        emp.last_name = last_name
        emp.cin = request.form.get('cin', '').strip()
        emp.phone = request.form.get('phone', '').strip()
        emp.email = request.form.get('email', '').strip()
        emp.job_title = request.form.get('job_title', '').strip() or emp.job_title
        emp.department = request.form.get('department', '').strip() or emp.department
        emp.salary_type = request.form.get('salary_type', 'monthly')
        emp.base_salary = _f(request.form.get('base_salary'))
        h_date = parse_date(request.form.get('hire_date'))
        if h_date:
            emp.hire_date = h_date
        emp.bank_name = request.form.get('bank_name', '').strip()
        emp.rib = request.form.get('rib', '').strip()
        emp.cnss_no = request.form.get('cnss_no', '').strip()
        emp.notes = request.form.get('notes', '').strip()
        emp.active = (request.form.get('active') == '1')

        db.session.commit()
        log_action('employee_edit', f"Employé modifié: {emp.full_name} ({emp.code})")
        flash(f"Fiche de {emp.full_name} mise à jour.", 'success')
        return redirect(url_for('employees'))

    return render_template('employees/form.html',
                           employee=emp,
                           next_code=emp.code,
                           departments=EMPLOYEE_DEPARTMENTS,
                           job_titles=EMPLOYEE_JOB_TITLES)


@app.route('/employees/<int:eid>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def employee_toggle_status(eid):
    emp = Employee.query.get_or_404(eid)
    emp.active = not emp.active
    db.session.commit()
    state = "activé" if emp.active else "désactivé"
    log_action('employee_toggle', f"Employé {emp.full_name} {state}")
    flash(f"L'employé {emp.full_name} a été {state}.", 'info')
    return redirect(request.referrer or url_for('employees'))


@app.route('/employees/<int:eid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def employee_delete(eid):
    emp = Employee.query.get_or_404(eid)
    name = emp.full_name
    if emp.payouts.count() > 0:
        emp.active = False
        db.session.commit()
        flash(f"L'employé {name} a des règlements de salaire enregistrés dans l'historique comptable. Son compte a été désactivé au lieu d'être supprimé pour préserver l'intégrité financière.", 'warning')
        return redirect(url_for('employees'))

    db.session.delete(emp)
    db.session.commit()
    log_action('employee_delete', f"Employé supprimé: {name}")
    flash(f"L'employé {name} a été supprimé.", 'info')
    return redirect(url_for('employees'))


@app.route('/employees/payroll')
@login_required
@role_required('admin', 'secretary')
def employees_payroll():
    _seed_default_employees_if_empty()
    req_month = request.args.get('month') or date.today().strftime('%Y-%m')
    try:
        y, m = map(int, req_month.split('-'))
    except Exception:
        y, m = date.today().year, date.today().month
        req_month = f"{y:04d}-{m:02d}"

    months_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    month_name_fr = f"{months_fr[m]} {y}"

    all_employees = Employee.query.order_by(Employee.department.asc(), Employee.last_name.asc()).all()
    payroll_rows = []

    total_base_payroll = 0.0
    total_paid_payroll = 0.0
    total_advances_month = 0.0
    total_pending_payroll = 0.0

    for emp in all_employees:
        payout = EmployeeSalaryPayout.query.filter_by(
            employee_id=emp.id,
            period_month=req_month
        ).filter(EmployeeSalaryPayout.status != 'cancelled').first()

        advances = EmployeeAdvance.query.filter_by(
            employee_id=emp.id,
            period_month=req_month
        ).filter(EmployeeAdvance.status != 'cancelled').all()
        emp_advances_sum = sum(a.amount for a in advances)

        base_sal = emp.base_salary or 0.0
        is_paid = (payout is not None)

        if is_paid:
            net_to_pay = payout.net_amount
            total_paid_payroll += payout.net_amount
        else:
            net_to_pay = max(0.0, round(base_sal - emp_advances_sum, 2))
            if emp.active:
                total_pending_payroll += net_to_pay

        if emp.active:
            total_base_payroll += base_sal
            total_advances_month += emp_advances_sum

        if emp.active or is_paid:
            payroll_rows.append({
                'employee': emp,
                'base_salary': base_sal,
                'advances_sum': emp_advances_sum,
                'net_to_pay': net_to_pay,
                'is_paid': is_paid,
                'payout': payout
            })

    return render_template('employees/payroll.html',
                           payroll_rows=payroll_rows,
                           req_month=req_month,
                           month_name_fr=month_name_fr,
                           total_base_payroll=total_base_payroll,
                           total_paid_payroll=total_paid_payroll,
                           total_pending_payroll=total_pending_payroll,
                           total_advances_month=total_advances_month,
                           employees_count=len(payroll_rows))


@app.route('/employees/payroll/payout', methods=['POST'])
@login_required
@role_required('admin')
def employee_payroll_payout():
    d = request.form
    emp_id = _int(d.get('employee_id'))
    period_month = d.get('period_month', '').strip()
    emp = Employee.query.get_or_404(emp_id)

    if not period_month:
        period_month = date.today().strftime('%Y-%m')

    # Anti-duplicate check
    existing = EmployeeSalaryPayout.query.filter_by(
        employee_id=emp.id,
        period_month=period_month
    ).filter(EmployeeSalaryPayout.status != 'cancelled').first()

    if existing:
        flash(f"🚨 ALERTE DOUBLON : Le salaire de {emp.full_name} pour le mois {period_month} a DÉJÀ ÉTÉ RÉGLÉ le {existing.payment_date.strftime('%d/%m/%Y')} (Montant versé : {existing.net_amount:.2f} DH, Reçu N° {existing.receipt_no}). Paiement double bloqué !", 'danger')
        return redirect(url_for('employees_payroll', month=period_month))

    base_salary = _f(d.get('base_salary')) or (emp.base_salary or 0.0)
    bonus_amount = _f(d.get('bonus_amount'))
    bonus_notes = d.get('bonus_notes', '').strip()
    advances_deducted = _f(d.get('advances_deducted'))
    deductions_amount = _f(d.get('deductions_amount'))
    deductions_notes = d.get('deductions_notes', '').strip()
    payment_method = d.get('payment_method', 'Espèces').strip()
    reference_no = d.get('reference_no', '').strip()
    pay_date = parse_date(d.get('payment_date')) or date.today()
    notes = d.get('notes', '').strip()
    sync_expense = (d.get('sync_expense') == '1' or 'sync_expense' in d)

    net_amount = _f(d.get('net_amount'))
    if net_amount <= 0:
        net_amount = max(0.0, round(base_salary + bonus_amount - advances_deducted - deductions_amount, 2))

    y, m = pay_date.year, pay_date.month
    prefix = f"EMP-SAL-{y:04d}{m:02d}-"
    last_payout = EmployeeSalaryPayout.query.filter(EmployeeSalaryPayout.receipt_no.like(f"{prefix}%")).order_by(EmployeeSalaryPayout.id.desc()).first()
    seq = 1
    if last_payout and last_payout.receipt_no:
        try:
            seq = int(last_payout.receipt_no.split('-')[-1]) + 1
        except Exception:
            seq = EmployeeSalaryPayout.query.count() + 1
    receipt_no = f"{prefix}{seq:04d}"

    u = current_user()
    expense_id = None

    if sync_expense and net_amount > 0:
        caisse_exp = Expense(
            expense_type='charge',
            category='Salaires & Primes',
            description=f"Règlement salaire employé(e) - {emp.full_name} ({emp.job_title}) ({period_month})",
            amount=net_amount,
            date=pay_date,
            payment_method=payment_method,
            reference_no=receipt_no if not reference_no else f"{receipt_no} / {reference_no}",
            status='paid',
            paid_amount=net_amount,
            notes=f"Salaire personnel Institut ILAS. Base : {base_salary:.2f} DH, Primes : +{bonus_amount:.2f} DH, Acomptes déduits : -{advances_deducted:.2f} DH, Retenues : -{deductions_amount:.2f} DH. {notes}".strip(),
            user_id=u.id if u else None
        )
        db.session.add(caisse_exp)
        db.session.flush()
        expense_id = caisse_exp.id

    payout = EmployeeSalaryPayout(
        receipt_no=receipt_no,
        employee_id=emp.id,
        period_month=period_month,
        base_salary=base_salary,
        bonus_amount=bonus_amount,
        bonus_notes=bonus_notes,
        advances_deducted=advances_deducted,
        deductions_amount=deductions_amount,
        deductions_notes=deductions_notes,
        net_amount=net_amount,
        payment_date=pay_date,
        payment_method=payment_method,
        reference_no=reference_no,
        status='paid',
        expense_id=expense_id,
        notes=notes,
        recorded_by=u.id if u else None
    )
    db.session.add(payout)
    db.session.commit()

    log_action('employee_salary_pay', f"Salaire {receipt_no}: {net_amount:.2f} DH versé à {emp.full_name} ({emp.job_title}) pour le mois {period_month}")
    flash(f"✅ Salaire de {net_amount:.2f} DH réglé avec succès pour {emp.full_name} (Mois {period_month}, Reçu N° {receipt_no}).", 'success')

    if d.get('print_after') == '1':
        return redirect(url_for('employee_salary_receipt', pid=payout.id))

    return redirect(url_for('employees_payroll', month=period_month))


@app.route('/employees/payroll/payout/<int:pid>/cancel', methods=['POST'])
@login_required
@role_required('admin')
def employee_payroll_cancel_payout(pid):
    payout = EmployeeSalaryPayout.query.get_or_404(pid)
    rec = payout.receipt_no
    amt = payout.net_amount
    name = payout.employee.full_name if payout.employee else 'Inconnu'
    month = payout.period_month

    if payout.expense_id:
        exp = Expense.query.get(payout.expense_id)
        if exp:
            db.session.delete(exp)

    db.session.delete(payout)
    db.session.commit()

    log_action('employee_salary_cancel', f"Annulation règlement salaire {rec}: {amt:.2f} DH de {name} ({month})")
    flash(f"Le règlement de salaire {rec} ({amt:.2f} DH de {name}) a été annulé avec succès.", 'warning')
    return redirect(url_for('employees_payroll', month=month))


@app.route('/employees/payroll/payout/<int:pid>/receipt')
@login_required
@role_required('admin', 'secretary')
def employee_salary_receipt(pid):
    payout = EmployeeSalaryPayout.query.get_or_404(pid)
    emp = payout.employee

    try:
        y, m = map(int, payout.period_month.split('-'))
    except Exception:
        y, m = payout.payment_date.year, payout.payment_date.month

    months_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    month_name_fr = f"{months_fr[m]} {y}"

    fmt = request.args.get('format', 'a5')
    return render_template('employees/receipt.html',
                           payout=payout,
                           employee=emp,
                           month_name_fr=month_name_fr,
                           fmt=fmt,
                           today=date.today())


@app.route('/employees/payroll/print')
@login_required
@role_required('admin', 'secretary')
def employees_payroll_print():
    req_month = request.args.get('month') or date.today().strftime('%Y-%m')
    try:
        y, m = map(int, req_month.split('-'))
    except Exception:
        y, m = date.today().year, date.today().month
        req_month = f"{y:04d}-{m:02d}"

    months_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    month_name_fr = f"{months_fr[m]} {y}"

    all_employees = Employee.query.order_by(Employee.department.asc(), Employee.last_name.asc()).all()
    payroll_rows = []

    total_base = 0.0
    total_net = 0.0

    for emp in all_employees:
        payout = EmployeeSalaryPayout.query.filter_by(
            employee_id=emp.id,
            period_month=req_month
        ).filter(EmployeeSalaryPayout.status != 'cancelled').first()

        advances = EmployeeAdvance.query.filter_by(
            employee_id=emp.id,
            period_month=req_month
        ).filter(EmployeeAdvance.status != 'cancelled').all()
        adv_sum = sum(a.amount for a in advances)

        base_sal = emp.base_salary or 0.0
        is_paid = (payout is not None)
        net_to_pay = payout.net_amount if payout else max(0.0, round(base_sal - adv_sum, 2))

        if emp.active or is_paid:
            total_base += base_sal
            total_net += net_to_pay
            payroll_rows.append({
                'employee': emp,
                'base_salary': base_sal,
                'advances_sum': adv_sum,
                'net_to_pay': net_to_pay,
                'is_paid': is_paid,
                'payout': payout
            })

    return render_template('employees/payroll_print.html',
                           payroll_rows=payroll_rows,
                           req_month=req_month,
                           month_name_fr=month_name_fr,
                           total_base=total_base,
                           total_net=total_net,
                           today=date.today())


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------
@app.route('/rooms', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def rooms():
    if request.method == 'POST':
        rid = request.form.get('id')
        name = request.form.get('name', '').strip()
        if not name:
            flash('Le nom de la salle est obligatoire.', 'danger')
            return redirect(url_for('rooms'))

        existing = Room.query.filter(Room.name.ilike(name)).first()
        if existing and (not rid or existing.id != int(rid)):
            flash(f"Une salle avec le nom '{name}' existe déjà.", 'danger')
            return redirect(url_for('rooms'))

        if rid:
            r = Room.query.get(int(rid))
        else:
            r = Room()
            db.session.add(r)
        r.name = name
        r.capacity = _int(request.form.get('capacity'))
        r.notes = request.form.get('notes')
        try:
            db.session.commit()
            flash('Salle enregistrée avec succès', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'enregistrement de la salle : {e}", 'danger')
        return redirect(url_for('rooms'))
    return render_template('rooms.html', rooms=Room.query.order_by(Room.id).all())


@app.route('/rooms/<int:rid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def room_delete(rid):
    r = Room.query.get_or_404(rid)
    assigned_courses = Course.query.filter_by(room_id=rid, active=True).count()
    if assigned_courses > 0:
        flash(f"Impossible de supprimer cette salle : elle est assignée à {assigned_courses} cours actif(s). Veuillez d'abord modifier la salle des cours concernés.", 'danger')
        return redirect(url_for('rooms'))

    ScheduleSlot.query.filter_by(room_id=rid).delete()
    db.session.delete(r)
    db.session.commit()
    flash('Salle supprimée avec succès', 'success')
    return redirect(url_for('rooms'))


# ---------------------------------------------------------------------------
# Courses (langues + soutien)
# ---------------------------------------------------------------------------
@app.route('/courses')
@login_required
@role_required('admin', 'secretary')
def courses():
    cat = request.args.get('cat', '')
    search_q = request.args.get('q', '').strip()
    selected_subject = request.args.get('subject', '').strip()
    teacher_id = _int(request.args.get('teacher_id'))

    u = current_user()
    cur_t = None
    teacher_cids = None
    if u and u.role == 'teacher':
        cur_t = get_current_teacher()
        teacher_cids = get_teacher_course_ids(cur_t.id) if cur_t else []

    query = Course.query.filter_by(active=True)
    if teacher_cids is not None:
        if teacher_cids:
            query = query.filter(Course.id.in_(teacher_cids))
        else:
            query = query.filter(Course.id == -1)

    if cat in ('language', 'tutoring'):
        query = query.filter_by(category=cat)

    if teacher_id and teacher_cids is None:
        query = query.filter_by(teacher_id=teacher_id)

    if search_q:
        query = query.filter(db.or_(
            Course.name.ilike(f'%{search_q}%'),
            Course.code.ilike(f'%{search_q}%'),
            Course.language.ilike(f'%{search_q}%'),
            Course.level.ilike(f'%{search_q}%')
        ))

    course_list = query.all()
    if selected_subject:
        course_list = [c for c in course_list if c.matiere == selected_subject]

    # Sort courses by Matière priority, then Matière name, then Course name
    course_list.sort(key=lambda c: (
        get_matiere_priority(c.matiere),
        c.matiere,
        (c.name or '').upper()
    ))

    # All available matieres with counts
    all_matieres_counts = {}
    base_courses = Course.query.filter_by(active=True).all()
    for c_obj in base_courses:
        m_name = c_obj.matiere
        all_matieres_counts[m_name] = all_matieres_counts.get(m_name, 0) + 1

    all_matieres = []
    for m_name in sorted(all_matieres_counts.keys(), key=lambda x: (get_matiere_priority(x), x)):
        cfg = MATIERE_CONFIG.get(m_name, {})
        all_matieres.append({
            'name': m_name,
            'icon': cfg.get('icon', '📚'),
            'color': cfg.get('color', '#0B3D6E'),
            'count': all_matieres_counts[m_name]
        })

    # KPIs
    if teacher_cids is not None:
        teacher_courses_base = Course.query.filter(Course.id.in_(teacher_cids), Course.active == True).all() if teacher_cids else []
        total_courses_count = len(teacher_courses_base)
        lang_courses_count = sum(1 for c in teacher_courses_base if c.category == 'language')
        tut_courses_count = sum(1 for c in teacher_courses_base if c.category == 'tutoring')
        total_enrolled_students = Enrollment.query.filter(Enrollment.course_id.in_(teacher_cids), Enrollment.status == 'active').count() if teacher_cids else 0
        all_teachers = [cur_t] if cur_t else []
    else:
        total_courses_count = Course.query.filter_by(active=True).count()
        lang_courses_count = Course.query.filter_by(category='language', active=True).count()
        tut_courses_count = Course.query.filter_by(category='tutoring', active=True).count()
        total_enrolled_students = Enrollment.query.filter_by(status='active').count()
        all_teachers = Teacher.query.filter_by(active=True).all()
        all_teachers.sort(key=lambda t: (get_matiere_priority(t.primary_matiere), t.primary_matiere, (t.last_name or '').upper(), (t.first_name or '').upper()))

    return render_template('courses/list.html',
                           courses=course_list,
                           cat=cat,
                           search_q=search_q,
                           selected_subject=selected_subject,
                           all_matieres=all_matieres,
                           teacher_id=teacher_id,
                           all_teachers=all_teachers,
                           total_courses_count=total_courses_count,
                           lang_courses_count=lang_courses_count,
                           tut_courses_count=tut_courses_count,
                           total_enrolled_students=total_enrolled_students,
                           current_teacher=cur_t)


DAYS_FR = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
DAYS_AR = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
DAYS_NAMES_MAP = [
    ('lundi', 0), ('lun', 0), ('mon', 0), ('monday', 0),
    ('mardi', 1), ('mar', 1), ('tue', 1), ('tuesday', 1),
    ('mercredi', 2), ('mer', 2), ('wed', 2), ('wednesday', 2),
    ('jeudi', 3), ('jeu', 3), ('thu', 3), ('thursday', 3),
    ('vendredi', 4), ('ven', 4), ('fri', 4), ('friday', 4),
    ('samedi', 5), ('sam', 5), ('sat', 5), ('saturday', 5),
    ('dimanche', 6), ('dim', 6), ('sun', 6), ('sunday', 6),
    # Noms arabes
    ('الاثنين', 0), ('الإثنين', 0),
    ('الثلاثاء', 1),
    ('الاربعاء', 2), ('الأربعاء', 2),
    ('الخميس', 3),
    ('الجمعة', 4),
    ('السبت', 5),
    ('الاحد', 6), ('الأحد', 6)
]

TIME_INTERVAL_PATTERN = re.compile(
    r'(?<!\d)'
    r'(?:(\d{1,2})[:hH;](\d{2})|(\d{1,2})\s*[hH])'
    r'\s*(?:[-/–—à:]|\s+to\s+|\s+tal\s+|\s+au\s+|\s+et\s+)\s*'
    r'(?:(\d{1,2})[:hH;](\d{2})|(\d{1,2})\s*[hH])'
    r'(?!\d)'
)

def find_days_in_text(text):
    if not text:
        return []
    text_lower = text.lower()
    found = []
    tokens = re.split(r'[^a-zA-Z\u0600-\u06FF]+', text_lower)
    for tok in tokens:
        if not tok:
            continue
        for dname, dnum in DAYS_NAMES_MAP:
            if tok == dname:
                if dnum not in found:
                    found.append(dnum)
                break
    return found

def extract_times_from_match(match):
    g1, g2, g3, g4, g5, g6 = match.groups()
    sh = g1 if g1 is not None else g3
    sm = g2 if g2 is not None else "00"
    eh = g4 if g4 is not None else g6
    em = g5 if g5 is not None else "00"
    return f"{int(sh):02d}:{sm}", f"{int(eh):02d}:{em}"

def calculate_duration_str(start_time, end_time):
    try:
        sh, sm = map(int, start_time.split(':'))
        eh, em = map(int, end_time.split(':'))
        diff_mins = (eh * 60 + em) - (sh * 60 + sm)
        if diff_mins > 0:
            dh = diff_mins // 60
            dm = diff_mins % 60
            return f"{dh}h{dm:02d}" if dm > 0 else f"{dh}h00"
    except Exception:
        pass
    return '1h30'

def parse_schedule_slots_from_text(course_name):
    if not course_name:
        return []
    matches = list(TIME_INTERVAL_PATTERN.finditer(course_name))
    slots = []
    
    if matches:
        last_idx = 0
        for i, m in enumerate(matches):
            start_time, end_time = extract_times_from_match(m)
            seg = course_name[last_idx:m.start()]
            days = find_days_in_text(seg)
            
            # If no days in preceding segment and only 1 time interval matched, check text after
            if not days and len(matches) == 1:
                after_seg = course_name[m.end():]
                days = find_days_in_text(after_seg)
                
            for d in days:
                slots.append({'day': d, 'start_time': start_time, 'end_time': end_time})
            last_idx = m.end()
            
        if not slots and matches:
            all_days = find_days_in_text(course_name)
            st, et = extract_times_from_match(matches[0])
            for d in all_days:
                slots.append({'day': d, 'start_time': st, 'end_time': et})
    return slots

def sync_schedule_from_course_name(course, force_replace=True):
    """
    Extrait les jours et heures du nom du cours et génère automatiquement
    les créneaux dans ScheduleSlot ainsi que scheduled_days et sessions_per_week.
    """
    if not course or not course.name:
        return False, []
    
    slots = parse_schedule_slots_from_text(course.name)
    if not slots:
        return False, []
    
    # Lock custom_end_date for existing active enrollments before schedule days change
    try:
        active_enrs = Enrollment.query.filter_by(course_id=course.id, status='active').all()
        for ae in active_enrs:
            if not ae.custom_end_date and ae.enroll_date:
                ae.custom_end_date = ae.end_date
    except Exception:
        pass

    # Mise à jour des attributs du cours
    unique_days = sorted(list(set(s['day'] for s in slots)))
    course.scheduled_days = ",".join(str(d) for d in unique_days)
    course.sessions_per_week = len(unique_days)
    
    if slots:
        dur = calculate_duration_str(slots[0]['start_time'], slots[0]['end_time'])
        course.session_duration = dur
    
    # Enregistrement des créneaux dans ScheduleSlot
    if force_replace:
        ScheduleSlot.query.filter_by(course_id=course.id).delete()
    
    for s_info in slots:
        existing = ScheduleSlot.query.filter_by(
            course_id=course.id,
            day_of_week=s_info['day'],
            start_time=s_info['start_time'],
            end_time=s_info['end_time']
        ).first()
        if not existing:
            slot_obj = ScheduleSlot(
                course_id=course.id,
                day_of_week=s_info['day'],
                start_time=s_info['start_time'],
                end_time=s_info['end_time']
            )
            db.session.add(slot_obj)
            
    db.session.commit()
    return True, slots


@app.route('/courses/new', methods=['GET', 'POST'])
@app.route('/courses/<int:cid>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def course_form(cid=None):
    c = Course.query.get(cid) if cid else None
    
    preset_tariff_id = _int(request.args.get('tariff_id'))
    if not c and preset_tariff_id:
        trf = Tariff.query.get(preset_tariff_id)
        if trf:
            c = Course(
                tariff_id=trf.id,
                name=trf.name,
                category=trf.category,
                language=trf.language,
                price=trf.price,
                registration_fee=trf.registration_fee,
                sessions_per_week=trf.sessions_per_week,
                billing_cycle=trf.billing_cycle,
                session_duration=trf.session_duration
            )
    if request.method == 'POST':
        d = request.form
        if c is None:
            c = Course(code=SH.gen_code('course_prefix', 'next_student_number'))
            db.session.add(c)
        c.name = d.get('name')
        c.category = d.get('category', 'language')
        c.tariff_id = _int(d.get('tariff_id')) or None

        if c.category == 'language':
            c.language = d.get('language') or 'Français'
            c.level = d.get('level_lang') or d.get('level') or 'A1 (Débutant)'
        else:
            c.language = d.get('tutoring_subject') or d.get('language') or 'Soutien'
            c.level = d.get('level_tutoring') or d.get('level') or '2ème Année Bac (الثانية باك)'

        c.group_name = d.get('group_name')
        c.billing_cycle = d.get('billing_cycle')
        c.price = _f(d.get('price')); c.price_per_month = _f(d.get('price_per_month'))
        c.registration_fee = _f(d.get('registration_fee')) or (200.0 if c.category == 'language' else 40.0)
        c.session_duration = d.get('session_duration', '1h30')
        
        days_list = request.form.getlist('days')
        if days_list:
            c.scheduled_days = ",".join(days_list)
            c.sessions_per_week = len(days_list)
        else:
            c.sessions_per_week = _int(d.get('sessions_per_week')) or 3

        teacher_id = _int(d.get('teacher_id')) or None
        c.teacher_id = teacher_id
        c.room_id = _int(d.get('room_id')) or None
        c.max_students = _int(d.get('max_students')) or 20
        c.start_date = parse_date(d.get('start_date')); c.end_date = parse_date(d.get('end_date'))
        c.active = d.get('active') == 'on'; c.notes = d.get('notes')
        db.session.commit()

        # Save / update CourseTeacher compensation model for this group
        comp_type = d.get('teacher_compensation_type', 'percentage')
        comp_val = _f(d.get('teacher_compensation_value')) or 50.0

        if teacher_id:
            old_assignments = CourseTeacher.query.filter_by(course_id=c.id, is_active=True).all()
            for old_ct in old_assignments:
                if old_ct.teacher_id != teacher_id:
                    old_ct.is_active = False
                    old_ct.end_date = date.today()

            ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=teacher_id, is_active=True).first()
            if not ct:
                ct = CourseTeacher(course_id=c.id, teacher_id=teacher_id, start_date=date.today(), is_active=True)
                db.session.add(ct)
            ct.compensation_type = comp_type
            ct.compensation_value = comp_val
            db.session.commit()

        log_action('course_save', c.display_name)
        if d.get('force_conflict') == '1':
            flash("⚠️ Cours enregistré avec alerte de conflit d'horaires (accepté par la direction)", 'warning')
        else:
            flash('Cours et modèle de rémunération de l\'enseignant enregistrés', 'success')

        # Génération automatique de l'emploi du temps depuis le nom ou les horaires saisis
        auto_schedule = d.get('auto_schedule', 'on') == 'on'
        sched_msg = None
        if auto_schedule:
            synced, detected_slots = sync_schedule_from_course_name(c, force_replace=True)
            if synced:
                readable_slots = ", ".join(f"{DAYS_FR[s['day']]} {s['start_time']}-{s['end_time']}" for s in detected_slots)
                sched_msg = f"🗓️ Emploi du temps configuré automatiquement ({readable_slots})."
            else:
                def_st = (d.get('default_start_time') or '').strip()
                def_et = (d.get('default_end_time') or '').strip()
                if def_st and def_et and days_list:
                    for ae in Enrollment.query.filter_by(course_id=c.id, status='active').all():
                        if not ae.custom_end_date and ae.enroll_date:
                            ae.custom_end_date = ae.end_date
                    ScheduleSlot.query.filter_by(course_id=c.id).delete()
                    for d_val in days_list:
                        s_obj = ScheduleSlot(course_id=c.id, day_of_week=int(d_val), start_time=def_st, end_time=def_et)
                        db.session.add(s_obj)
                    c.session_duration = calculate_duration_str(def_st, def_et)
                    db.session.commit()
                    readable_slots = ", ".join(f"{DAYS_FR[int(d_val)]} {def_st}-{def_et}" for d_val in days_list)
                    sched_msg = f"🗓️ Emploi du temps enregistré avec succès ({readable_slots})."

        if sched_msg:
            flash(sched_msg, 'info')

        return redirect(url_for('courses'))

    ct = CourseTeacher.query.filter_by(course_id=cid, teacher_id=c.teacher_id).first() if (c and c.teacher_id) else None
    return render_template('courses/form.html', c=c, ct=ct,
                           teachers=Teacher.query.filter_by(active=True).all(),
                           rooms=Room.query.all(),
                           tariffs=Tariff.query.filter_by(active=True).order_by(Tariff.language, Tariff.id).all())


@app.route('/courses/<int:cid>/sync_schedule', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def course_sync_schedule(cid):
    c = Course.query.get_or_404(cid)
    synced, slots = sync_schedule_from_course_name(c, force_replace=True)
    if synced:
        slot_desc = ", ".join(f"{DAYS_FR[s['day']]} {s['start_time']}-{s['end_time']}" for s in slots)
        flash(f"🗓️ Emploi du temps synchronisé avec succès pour '{c.name}' ({slot_desc})", "success")
    else:
        flash(f"⚠️ Aucun horaire détecté dans le nom de la classe '{c.name}'.", "warning")
    return redirect(request.referrer or url_for('course_view', cid=cid))


@app.route('/api/teachers/quick_add', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def api_teachers_quick_add():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    subject = request.form.get('subject', '').strip()
    phone = request.form.get('phone', '').strip()
    salary_amount = _f(request.form.get('salary_amount')) or 50.0

    if not first_name or not last_name:
        return jsonify({'success': False, 'message': 'Le prénom et le nom sont obligatoires.'}), 400

    t = Teacher(first_name=first_name, last_name=last_name, specialty=subject, phone=phone, salary_amount=salary_amount, salary_type='percentage', active=True)
    db.session.add(t)
    db.session.commit()

    return jsonify({
        'success': True,
        'id': t.id,
        'full_name': t.full_name,
        'message': f"L'enseignant {t.full_name} a été ajouté avec succès."
    })


@app.route('/courses/<int:cid>/assign_teacher', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def course_assign_teacher(cid):
    c = Course.query.get_or_404(cid)
    teacher_id = _int(request.form.get('teacher_id'))
    if not teacher_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Veuillez sélectionner un enseignant valide.'}), 400
        flash("Veuillez sélectionner un enseignant valide.", "warning")
        return redirect(request.referrer or url_for('dashboard'))

    t = Teacher.query.get_or_404(teacher_id)
    c.teacher_id = t.id

    comp_type = request.form.get('teacher_compensation_type', 'percentage')
    comp_val = _f(request.form.get('teacher_compensation_value'))
    if comp_val is None:
        comp_val = t.salary_amount if (t.salary_amount and t.salary_amount > 0) else 50.0

    # Manage CourseTeacher assignments
    old_assignments = CourseTeacher.query.filter_by(course_id=c.id, is_active=True).all()
    for old_ct in old_assignments:
        if old_ct.teacher_id != t.id:
            old_ct.is_active = False
            old_ct.end_date = date.today()

    ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=t.id, is_active=True).first()
    if not ct:
        ct = CourseTeacher(course_id=c.id, teacher_id=t.id, start_date=date.today(), is_active=True)
        db.session.add(ct)
    ct.compensation_type = comp_type
    ct.compensation_value = comp_val

    db.session.commit()
    log_action('course_assign_teacher', f"Enseignant {t.full_name} assigné à la classe {c.display_name}")
    flash(f"Professeur {t.full_name} assigné avec succès à la classe '{c.display_name}' !", "success")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'message': f"Professeur {t.full_name} assigné avec succès."})

    return redirect(request.referrer or url_for('dashboard'))


@app.route('/courses/<int:cid>')
@login_required
@role_required('admin', 'secretary')
def course_view(cid):
    c = Course.query.get_or_404(cid)
    enrolls = Enrollment.query.filter_by(course_id=cid).order_by(Enrollment.id.desc()).all()
    schedule = ScheduleSlot.query.filter_by(course_id=cid).all()
    ct = CourseTeacher.query.filter_by(course_id=cid, is_active=True).first()
    
    total_group_revenue = sum((e.calculated_price or e.monthly_price or 0.0) for e in enrolls if e.status == 'active')
    total_paid_revenue = sum(e.total_paid for e in enrolls if e.status == 'active')
    
    active_students_count = sum(1 for e in enrolls if e.status == 'active')

    attendances = Attendance.query.filter_by(course_id=cid).order_by(Attendance.date.desc()).limit(25).all()

    return render_template('courses/view.html',
                           c=c,
                           enrolls=enrolls,
                           schedule=schedule,
                           ct=ct,
                           total_group_revenue=total_group_revenue,
                           total_paid_revenue=total_paid_revenue,
                           active_students_count=active_students_count,
                           attendances=attendances)


@app.route('/courses/<int:cid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def course_delete(cid):
    c = Course.query.get_or_404(cid)
    
    active_enrolls_count = Enrollment.query.filter_by(course_id=cid, status='active').count()
    if active_enrolls_count > 0:
        flash(f"Impossible de supprimer ce cours : {active_enrolls_count} élève(s) y sont actuellement inscrits. Veuillez d'abord transférer ou désinscrire les élèves, ou archiver le cours.", 'danger')
        return redirect(url_for('courses'))

    ScheduleSlot.query.filter_by(course_id=cid).delete()
    CourseTeacher.query.filter_by(course_id=cid).delete()
    
    past_enrolls_count = Enrollment.query.filter_by(course_id=cid).count()
    if past_enrolls_count > 0:
        c.active = False
        db.session.commit()
        log_action('course_archive', f"Course {c.display_name} archived")
        flash(f"Le cours '{c.display_name}' a été archivé avec succès pour préserver l'historique محاسبي للتلاميذ.", 'warning')
    else:
        db.session.delete(c)
        db.session.commit()
        log_action('course_delete', c.display_name)
        flash('Cours supprimé avec succès.', 'success')

    return redirect(url_for('courses'))


TARIFF_LEVEL_META = {
    'Primaire': {'fr': 'Primaire Standard', 'ar': 'السلك الابتدائي (العادي)', 'cycle': 'primaire', 'order': 1},
    'Primaire 3 jours': {'fr': 'Primaire — Formule 3 Jours/sem', 'ar': 'الابتدائي — باقة 3 أيام/أسبوع', 'cycle': 'primaire', 'order': 2},
    'Primaire 4 jours': {'fr': 'Primaire — Formule 4 Jours/sem', 'ar': 'الابتدائي — باقة 4 أيام/أسبوع', 'cycle': 'primaire', 'order': 3},
    'Primaire 5 jours': {'fr': 'Primaire — Formule 5 Jours/sem', 'ar': 'الابتدائي — باقة 5 أيام/أسبوع', 'cycle': 'primaire', 'order': 4},
    '1 Collège': {'fr': '1ère Année Collège (1AC)', 'ar': 'الأولى إعدادي (1AC)', 'cycle': 'college', 'order': 10},
    '2 Collège': {'fr': '2ème Année Collège (2AC)', 'ar': 'الثانية إعدادي (2AC)', 'cycle': 'college', 'order': 11},
    '3 Collège': {'fr': '3ème Année Collège (3AC / Examen)', 'ar': 'الثالثة إعدادي (3AC - إشهادي)', 'cycle': 'college', 'order': 12},
    'Tronc Commun': {'fr': 'Tronc Commun (TC)', 'ar': 'الجذع المشترك العلمي والأدبي', 'cycle': 'lycee', 'order': 20},
    '1 BAC SX': {'fr': '1ère Année BAC — Sciences Expérimentales', 'ar': 'الأولى باك — علوم تجريبية (جهوي)', 'cycle': 'lycee', 'order': 21},
    '1 BAC SM': {'fr': '1ère Année BAC — Sciences Mathématiques', 'ar': 'الأولى باك — علوم رياضية (SM)', 'cycle': 'lycee', 'order': 22},
    '2 BAC SX': {'fr': '2ème Année BAC — Sciences (PC / SVT / Éco)', 'ar': 'الثانية باك — علوم تجريبية وفيزيائية واقتصاد', 'cycle': 'lycee', 'order': 23},
    '2 BAC VIP': {'fr': '2ème Année BAC — Groupes Fermés VIP', 'ar': 'الثانية باك — مجموعات مغلقة VIP', 'cycle': 'lycee', 'order': 24},
    'Calcul Mental': {'fr': 'Calcul Mental & Développement Cognitif', 'ar': 'الحساب الذهني وتطوير الذكاء والتركيز', 'cycle': 'primaire', 'order': 5},
    'Français': {'fr': 'Pôle Langue Française', 'ar': 'شعبة اللغة الفرنسية (تواصل وقواعد)', 'cycle': 'langue', 'order': 30},
    'Anglais': {'fr': 'Pôle Langue Anglaise', 'ar': 'شعبة اللغة الإنجليزية (تواصل ومحادثة)', 'cycle': 'langue', 'order': 31},
    'Anglais/ Cours du jour': {'fr': 'Anglais (Cours du Jour Intensif)', 'ar': 'اللغة الإنجليزية (دروس النهار المكثفة)', 'cycle': 'langue', 'order': 32},
    'Allemand': {'fr': 'Pôle Langue Allemande (A1 — B2)', 'ar': 'شعبة اللغة الألمانية (إعداد امتحانات والفيزا)', 'cycle': 'langue', 'order': 33},
    'Espagnol': {'fr': 'Pôle Langue Espagnole', 'ar': 'شعبة اللغة الإسبانية (تواصل ومستويات)', 'cycle': 'langue', 'order': 34},
}

def get_tariff_bilingual_subject(name, category, language):
    n = (name or '').lower()
    if category == 'language':
        if 'fran' in n: return {'fr': 'Français Général & Communication', 'ar': 'الفرنسية العامة والتواصل', 'ico': '🇫🇷'}
        if 'ang' in n: return {'fr': 'Anglais Général & Conversation', 'ar': 'الإنجليزية العامة والمحادثة', 'ico': '🇬🇧'}
        if 'all' in n: return {'fr': 'Allemand (Certification & Préparation)', 'ar': 'الألمانية (مستويات A1-B2 والفيزا)', 'ico': '🇩🇪'}
        if 'esp' in n: return {'fr': 'Espagnol (Communication & Niveaux)', 'ar': 'الإسبانية (تواصل ومستويات)', 'ico': '🇪🇸'}
        return {'fr': language or name, 'ar': language or name, 'ico': '🌍'}
    
    if 'calcul mental' in n: return {'fr': 'Calcul Mental & Anzan', 'ar': 'الحساب الذهني وتنشيط الذاكرة', 'ico': '🧮'}
    if 'toutes les mati' in n or 'pack' in n:
        if '3 jours' in n: return {'fr': 'Pack Toutes Matières (3 jours/sem)', 'ar': 'باقة شاملة لجميع المواد (3 أيام/أسبوع)', 'ico': '📦'}
        if '4 jours' in n: return {'fr': 'Pack Toutes Matières (4 jours/sem)', 'ar': 'باقة شاملة لجميع المواد (4 أيام/أسبوع)', 'ico': '📦'}
        if '5 jours' in n: return {'fr': 'Pack Toutes Matières (5 jours/sem)', 'ar': 'باقة شاملة لجميع المواد (5 أيام/أسبوع)', 'ico': '📦'}
        if 'pc + maths + svt' in n: return {'fr': 'Pack Trio : PC + Maths + SVT', 'ar': 'باقة ثلاثية: فيزياء + رياضيات + علوم', 'ico': '📦'}
        return {'fr': 'Pack Multi-Matières', 'ar': 'باقة شاملة لجميع المواد', 'ico': '📦'}
    if 'maths-éco' in n or 'maths-eco' in n or 'meco' in n: return {'fr': 'Mathématiques Appliquées (Éco)', 'ar': 'رياضيات الاقتصاد', 'ico': '📐'}
    if 'maths + pc' in n or 'math + pc' in n: return {'fr': 'Maths + Physique-Chimie', 'ar': 'الرياضيات + الفيزياء والكيمياء', 'ico': '📐'}
    if 'math' in n: return {'fr': 'Mathématiques', 'ar': 'الرياضيات', 'ico': '📐'}
    if 'physique' in n or 'pc' in n: return {'fr': 'Physique - Chimie (PC)', 'ar': 'الفيزياء والكيمياء', 'ico': '🔬'}
    if 'svt' in n: return {'fr': 'Sciences de la Vie et de la Terre (SVT)', 'ar': 'علوم الحياة والأرض', 'ico': '🌿'}
    if 'fran' in n: return {'fr': 'Français (Examen Régional / Soutien)', 'ar': 'الفرنسية (امتحان جهوي ودعم)', 'ico': '🇫🇷'}
    if 'anglais' in n or 'ang' in n: return {'fr': 'Anglais (Soutien & Renforcement)', 'ar': 'اللغة الإنجليزية (دعم وتقوية)', 'ico': '🇬🇧'}
    if 'arabe' in n or ' ar' in n: return {'fr': 'Langue Arabe', 'ar': 'اللغة العربية', 'ico': '📖'}
    if 'histoire' in n or 'h-g' in n: return {'fr': 'Histoire - Géographie', 'ar': 'التاريخ والجغرافيا', 'ico': '🌍'}
    if 'islam' in n or 'e-i' in n: return {'fr': 'Éducation Islamique', 'ar': 'التربية الإسلامية', 'ico': '🕌'}
    if 'philo' in n: return {'fr': 'Philosophie', 'ar': 'الفلسفة', 'ico': '💡'}
    if 'compta' in n: return {'fr': 'Comptabilité Générale', 'ar': 'المحاسبة العامة', 'ico': '📊'}
    if 'écono' in n or 'econo' in n or 'eco' in n: return {'fr': 'Économie Générale & Statistiques', 'ar': 'الاقتصاد العام والإحصاء', 'ico': '📈'}
    if 'orga' in n: return {'fr': 'Organisation des Entreprises (EOAE)', 'ar': 'تنظيم المقاولات ومحيطها', 'ico': '🏢'}
    return {'fr': name, 'ar': name, 'ico': '📚'}

def get_tariff_bilingual_schedule(sessions, duration):
    s = int(sessions) if sessions else 1
    d = str(duration or '1h30').strip()
    if s == 1:
        s_fr = f"1 séance / sem ({d})"
        s_ar = f"حصة واحدة في الأسبوع ({d})"
    elif s == 2:
        s_fr = f"2 séances / sem ({d})"
        s_ar = f"حصتان في الأسبوع ({d})"
    else:
        s_fr = f"{s} séances / sem ({d})"
        s_ar = f"{s} حصص في الأسبوع ({d})"
    return {'fr': s_fr, 'ar': s_ar}


@app.route('/tariffs')
@login_required
@role_required('admin', 'secretary')
def tariffs():
    cat = request.args.get('cat', '')
    query = Tariff.query.filter_by(active=True)
    if cat:
        query = query.filter_by(category=cat)
    tariffs = query.order_by(Tariff.category, Tariff.language, Tariff.id).all()

    soutien_levels = db.session.query(Tariff.language).filter(
        Tariff.active == True, Tariff.category == 'tutoring'
    ).distinct().all()
    soutien_levels = [lvl[0] for lvl in soutien_levels if lvl[0]]

    language_names = db.session.query(Tariff.language).filter(
        Tariff.active == True, Tariff.category == 'language'
    ).distinct().all()
    language_names = [l[0] for l in language_names if l[0]]

    # Available classes metadata for multi-choice picker
    available_classes = []
    for k, v in sorted(TARIFF_LEVEL_META.items(), key=lambda x: x[1].get('order', 99)):
        cnt = Tariff.query.filter_by(active=True, language=k).count()
        if cnt > 0:
            available_classes.append({
                'id': k,
                'label_fr': v['fr'],
                'label_ar': v['ar'],
                'cycle': v.get('cycle', 'autre'),
                'count': cnt
            })

    return render_template('tariffs/list.html', tariffs=tariffs, soutien_levels=soutien_levels, language_names=language_names, available_classes=available_classes, cat=cat)


@app.route('/tariffs/print')
@login_required
@role_required('admin', 'secretary')
def tariffs_print():
    cat = request.args.get('cat', '')
    level = request.args.get('level', '')
    lang = request.args.get('lang', '')
    tariff_id = _int(request.args.get('id'))
    print_format = request.args.get('fmt', 'a5_duo').lower() # 'a5_duo', 'a5', 'a4', '80mm'
    orient = request.args.get('orient', '')
    if not orient:
        orient = 'landscape' if print_format in ('a5_duo', 'landscape') else 'portrait'

    # Multi-class parsing
    levels_arg = request.args.getlist('levels')
    if not levels_arg:
        levels_raw = request.args.get('levels', '')
        if levels_raw:
            levels_arg = [x.strip() for x in levels_raw.split(',') if x.strip()]

    # If single level or lang provided, include them
    if level and level not in levels_arg:
        levels_arg.append(level)
    if lang and lang not in levels_arg:
        levels_arg.append(lang)

    ids_arg = request.args.getlist('ids')
    if not ids_arg:
        ids_raw = request.args.get('ids', '')
        if ids_raw:
            ids_arg = [_int(x.strip()) for x in ids_raw.split(',') if _int(x.strip())]
    if tariff_id and tariff_id not in ids_arg:
        ids_arg.append(tariff_id)

    query = Tariff.query.filter_by(active=True)

    if ids_arg:
        query = query.filter(Tariff.id.in_(ids_arg))
        title_suffix_fr = "Sélection Personnalisée de Formules"
        title_suffix_ar = "تشكيلة مختارة من التسعيرات الرسمية"
    elif levels_arg:
        query = query.filter(Tariff.language.in_(levels_arg))
        if len(levels_arg) == 1:
            meta = TARIFF_LEVEL_META.get(levels_arg[0], {})
            title_suffix_fr = meta.get('fr', levels_arg[0])
            title_suffix_ar = meta.get('ar', levels_arg[0])
        else:
            title_suffix_fr = f"Sélection de Classes ({len(levels_arg)} niveaux)"
            title_suffix_ar = f"تشكيلة فصول مختارة ({len(levels_arg)} مستويات)"
    elif cat == 'language':
        query = query.filter_by(category='language')
        title_suffix_fr = "Pôle Langues Vivantes"
        title_suffix_ar = "كتالوج اللغات الحية والتواصل"
    elif cat == 'tutoring':
        query = query.filter_by(category='tutoring')
        title_suffix_fr = "Pôle Soutien Scolaire & Excellence"
        title_suffix_ar = "كتالوج الدعم المدرسي الشامل"
    else:
        title_suffix_fr = "Catalogue Officiel des Tarifs"
        title_suffix_ar = "الكتالوج الرسمي للتسعيرات والرسوم"

    tariffs = query.order_by(Tariff.category, Tariff.language, Tariff.price).all()
    reg_fee = tariffs[0].registration_fee if tariffs else 40.0

    # Group tariffs into structured classes
    from collections import defaultdict
    grouped_dict = defaultdict(list)
    for t in tariffs:
        c_key = t.language or 'Général'
        sub = get_tariff_bilingual_subject(t.name, t.category, t.language)
        sch = get_tariff_bilingual_schedule(t.sessions_per_week, t.session_duration)
        cycle_fr = 'Mensuel' if t.billing_cycle == 'monthly' else ('Trimestriel (3 mois)' if t.billing_cycle == '3months' else t.billing_cycle)
        cycle_ar = 'شهرياً' if t.billing_cycle == 'monthly' else ('كل 3 أشهر (فصل)' if t.billing_cycle == '3months' else t.billing_cycle)
        
        grouped_dict[c_key].append({
            'id': t.id,
            'code': t.code,
            'name': t.name,
            'category': t.category,
            'language': t.language,
            'price': t.price,
            'registration_fee': t.registration_fee,
            'sessions_per_week': t.sessions_per_week,
            'session_duration': t.session_duration,
            'billing_cycle': t.billing_cycle,
            'cycle_fr': cycle_fr,
            'cycle_ar': cycle_ar,
            'subject_fr': sub['fr'],
            'subject_ar': sub['ar'],
            'subject_ico': sub['ico'],
            'schedule_fr': sch['fr'],
            'schedule_ar': sch['ar'],
        })

    # Sort groups in pedagogical order
    grouped_classes = []
    for c_key, items in grouped_dict.items():
        meta = TARIFF_LEVEL_META.get(c_key, {'fr': c_key, 'ar': c_key, 'cycle': 'autre', 'order': 99})
        grouped_classes.append({
            'id': c_key,
            'name_fr': meta.get('fr', c_key),
            'name_ar': meta.get('ar', c_key),
            'cycle': meta.get('cycle', 'autre'),
            'order': meta.get('order', 99),
            'tariffs': items
        })
    grouped_classes.sort(key=lambda x: x['order'])

    # Available classes for live switcher modal
    available_classes = []
    for k, v in sorted(TARIFF_LEVEL_META.items(), key=lambda x: x[1].get('order', 99)):
        cnt = Tariff.query.filter_by(active=True, language=k).count()
        if cnt > 0:
            available_classes.append({
                'id': k,
                'label_fr': v['fr'],
                'label_ar': v['ar'],
                'cycle': v.get('cycle', 'autre'),
                'count': cnt
            })

    is_single_class = (len(grouped_classes) == 1)

    private_packs = [
        {'title_fr': "Standard (À l'heure)", 'title_ar': 'فردي (بالساعة)', 'hours': 1, 'rate': 250, 'total': 250},
        {'title_fr': 'Pack 15h', 'title_ar': 'باقة 15 ساعة', 'hours': 15, 'rate': 175, 'total': 2625},
        {'title_fr': 'Pack 30h', 'title_ar': 'باقة 30 ساعة', 'hours': 30, 'rate': 150, 'total': 4500},
        {'title_fr': 'Pack 60h', 'title_ar': 'باقة 60 ساعة', 'hours': 60, 'rate': 100, 'total': 6000},
    ]

    settings_dict = {s.key: s.value for s in Setting.query.all()}

    return render_template(
        'tariffs/print.html',
        tariffs=tariffs,
        grouped_classes=grouped_classes,
        available_classes=available_classes,
        selected_classes=levels_arg,
        is_single_class=is_single_class,
        title_suffix_fr=title_suffix_fr,
        title_suffix_ar=title_suffix_ar,
        private_packs=private_packs,
        level=level,
        lang=lang,
        cat=cat,
        reg_fee=reg_fee,
        print_format=print_format,
        orient=orient,
        settings=settings_dict,
        today=date.today()
    )


@app.route('/tariffs/<int:id>/edit', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def tariff_edit(id):
    trf = db.session.get(Tariff, id)
    if not trf:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Tarif introuvable'}), 404
        flash('Tarif introuvable', 'danger')
        return redirect(url_for('tariffs'))
    
    name = request.form.get('name', '').strip()
    if not name:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Le nom du tarif est obligatoire'}), 400
        flash('Le nom du tarif est obligatoire', 'danger')
        return redirect(url_for('tariffs'))

    code = request.form.get('code', trf.code).strip()
    category = request.form.get('category', trf.category).strip()
    language = request.form.get('language', trf.language).strip()
    billing_cycle = request.form.get('billing_cycle', trf.billing_cycle).strip()
    
    def _parse_num(val, default=0.0):
        try:
            return float(str(val).replace(',', '.').strip())
        except (ValueError, TypeError):
            return default

    price = _parse_num(request.form.get('price'), trf.price)
    registration_fee = _parse_num(request.form.get('registration_fee'), trf.registration_fee)
    sessions_per_week = _int(request.form.get('sessions_per_week')) or trf.sessions_per_week
    session_duration = request.form.get('session_duration', trf.session_duration).strip()
    active_val = request.form.get('active')
    active = True if active_val in ['1', 'true', 'on', True] else False

    # Check code uniqueness if changed
    if code and code != trf.code:
        exist = Tariff.query.filter(Tariff.code == code, Tariff.id != id).first()
        if exist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'message': f'Le code {code} existe déjà'}), 400
            flash(f'Le code {code} existe déjà pour un autre tarif', 'danger')
            return redirect(url_for('tariffs'))
        trf.code = code

    trf.name = name
    trf.category = category
    trf.language = language
    trf.billing_cycle = billing_cycle
    trf.price = price
    trf.registration_fee = registration_fee
    trf.sessions_per_week = sessions_per_week
    trf.session_duration = session_duration
    trf.active = active

    db.session.commit()
    log_action('edit_tariff', f'Tarif #{trf.id} ({trf.name}) modifié: Prix={price} DH, RegFee={registration_fee} DH')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'message': f'Tarif "{trf.name}" mis à jour avec succès',
            'tariff': {
                'id': trf.id,
                'code': trf.code,
                'name': trf.name,
                'category': trf.category,
                'language': trf.language,
                'billing_cycle': trf.billing_cycle,
                'price': trf.price,
                'registration_fee': trf.registration_fee,
                'sessions_per_week': trf.sessions_per_week,
                'session_duration': trf.session_duration,
                'active': trf.active
            }
        })

    flash(f'Tarif "{trf.name}" mis à jour avec succès !', 'success')
    return redirect(url_for('tariffs'))


@app.route('/tariffs/new', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def tariff_new():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Le nom du tarif est obligatoire', 'danger')
        return redirect(url_for('tariffs'))
    
    code = request.form.get('code', '').strip()
    category = request.form.get('category', 'language').strip()
    language = request.form.get('language', '').strip()
    billing_cycle = request.form.get('billing_cycle', 'monthly').strip()
    
    def _parse_num(val, default=0.0):
        try:
            return float(str(val).replace(',', '.').strip())
        except (ValueError, TypeError):
            return default

    price = _parse_num(request.form.get('price'), 0.0)
    registration_fee = _parse_num(request.form.get('registration_fee'), 200.0 if category == 'language' else 40.0)
    sessions_per_week = _int(request.form.get('sessions_per_week')) or (3 if category == 'language' else 2)
    session_duration = request.form.get('session_duration', '1h30').strip()

    if not code:
        prefix = 'LANG' if category == 'language' else 'SOUT'
        count = Tariff.query.count() + 1
        code = f"TRF-{prefix}-{count:02d}"

    trf = Tariff(
        code=code,
        name=name,
        category=category,
        language=language,
        billing_cycle=billing_cycle,
        price=price,
        registration_fee=registration_fee,
        sessions_per_week=sessions_per_week,
        session_duration=session_duration,
        active=True
    )
    db.session.add(trf)
    db.session.commit()
    log_action('create_tariff', f'Nouveau tarif #{trf.id} ({trf.name}) créé: Prix={price} DH')

    flash(f'Tarif "{trf.name}" créé avec succès !', 'success')
    return redirect(url_for('tariffs'))



# ---------------------------------------------------------------------------
# Enrollments
# ---------------------------------------------------------------------------
def calculate_course_sessions(course_id, enroll_dt, months_count=None, custom_unit_price=None):
    if not enroll_dt:
        enroll_dt = date.today()
    course = Course.query.get(course_id)
    
    scheduled_days = set()
    if course and course.scheduled_days:
        try:
            scheduled_days = set(int(x.strip()) for x in course.scheduled_days.split(',') if x.strip().isdigit())
        except Exception:
            scheduled_days = set()

    if not scheduled_days:
        slots = ScheduleSlot.query.filter_by(course_id=course_id).all()
        if slots:
            scheduled_days = set(s.day_of_week for s in slots)

    spw = course.sessions_per_week if (course and course.sessions_per_week) else (len(scheduled_days) or 3)
    if not scheduled_days:
        if spw == 1:
            scheduled_days = {0}
        elif spw == 2:
            scheduled_days = {1, 3}
        elif spw == 4:
            scheduled_days = {0, 1, 3, 4}
        elif spw == 5:
            scheduled_days = {0, 1, 2, 3, 4}
        elif spw == 6:
            scheduled_days = {0, 1, 2, 3, 4, 5}
        else:
            scheduled_days = {0, 2, 4}

    if not months_count or months_count <= 0:
        months_count = 1
    else:
        months_count = int(months_count)

    total_sessions = 0
    remaining_sessions = 0

    curr_y = enroll_dt.year
    curr_m = enroll_dt.month

    # 1. Calculate Month 1 sessions
    _, month1_num_days = calendar.monthrange(curr_y, curr_m)
    month1_total_sessions = 0
    month1_remaining_sessions = 0

    for day in range(1, month1_num_days + 1):
        cur_date = date(curr_y, curr_m, day)
        if cur_date.weekday() in scheduled_days:
            month1_total_sessions += 1
            if cur_date >= enroll_dt:
                month1_remaining_sessions += 1

    if month1_total_sessions == 0:
        month1_total_sessions = spw * 4
        month1_remaining_sessions = spw * 4

    total_sessions = 0
    remaining_sessions = 0

    for i in range(months_count):
        m_y = curr_y + ((curr_m - 1 + i) // 12)
        m_m = ((curr_m - 1 + i) % 12) + 1
        _, num_days = calendar.monthrange(m_y, m_m)

        for day in range(1, num_days + 1):
            cur_date = date(m_y, m_m, day)
            dow = cur_date.weekday()
            if dow in scheduled_days:
                total_sessions += 1
                if cur_date >= enroll_dt:
                    remaining_sessions += 1

    if total_sessions == 0:
        total_sessions = spw * 4 * months_count
        remaining_sessions = spw * 4 * months_count

    raw_course_price = course.price if course else 0.0
    cycle_months = 1
    if course and course.billing_cycle in ('3months', 'trimestriel', '3 mois', 'quarterly'):
        cycle_months = 3
    elif course and course.billing_cycle in ('6months', 'semestriel', '6 mois'):
        cycle_months = 6
    elif course and course.billing_cycle in ('annual', 'annuel', '12months'):
        cycle_months = 12

    if course and getattr(course, 'unit_monthly_price', None) and course.unit_monthly_price > 0:
        unit_monthly_price = course.unit_monthly_price
    else:
        unit_monthly_price = (raw_course_price / cycle_months) if cycle_months > 0 else raw_course_price
    
    if custom_unit_price is None and has_request_context():
        custom_unit_price = request.args.get('custom_unit_price')
    if custom_unit_price:
        try:
            unit_monthly_price = float(custom_unit_price)
        except:
            pass

    full_price = round(unit_monthly_price * months_count, 2)

    monthly_tuition = unit_monthly_price

    if total_sessions > 0:
        price_per_session = full_price / total_sessions
        current_month_earned = round(price_per_session * month1_remaining_sessions, 2)
    else:
        current_month_earned = monthly_tuition

    current_month_earned = min(monthly_tuition, current_month_earned)
    deferred_next_month = max(0.0, round(full_price - current_month_earned, 2))

    return {
        'total_sessions': total_sessions,
        'remaining_sessions': remaining_sessions,
        'month1_total_sessions': month1_total_sessions,
        'month1_remaining_sessions': month1_remaining_sessions,
        'full_price': full_price,
        'monthly_tuition': monthly_tuition,
        'current_month_earned': current_month_earned,
        'deferred_next_month': deferred_next_month,
        'months_count': months_count
    }


@app.route('/api/calculate_prorated')
@login_required
@role_required('admin', 'secretary')
def api_calculate_prorated():
    cid = _int(request.args.get('course_id'))
    edt = parse_date(request.args.get('enroll_date')) or date.today()
    mc = _int(request.args.get('months_count'))
    res = calculate_course_sessions(cid, edt, months_count=mc)
    
    c = Course.query.get(cid)
    ct = CourseTeacher.query.filter_by(course_id=cid, teacher_id=c.teacher_id).first() if (c and c.teacher_id) else None
    pct = ct.compensation_value if (ct and ct.compensation_type == 'percentage') else 50.0

    scheduled_days = set()
    if c and c.scheduled_days:
        try:
            scheduled_days = set(int(x.strip()) for x in c.scheduled_days.split(',') if x.strip().isdigit())
        except Exception:
            scheduled_days = set()
    if not scheduled_days:
        scheduled_days = {0, 2, 4}

    end_dt = calculate_last_session_date(edt, res['total_sessions'], scheduled_days)
    if edt.day == 1 and res.get('months_count', 1) == 1:
        _, last_day = calendar.monthrange(edt.year, edt.month)
        m_end = date(edt.year, edt.month, last_day)
        if end_dt < m_end:
            end_dt = m_end
    res['end_date'] = end_dt.strftime('%d/%m/%Y')

    res['teacher_percentage'] = pct
    res['teacher_earned'] = round(res['current_month_earned'] * (pct / 100.0), 2)
    res['registration_fee'] = c.registration_fee if (c and c.registration_fee is not None) else (200.0 if (c and c.category == 'language') else 40.0)
    res['unit_monthly_price'] = round(res['full_price'] / res['months_count'], 2) if res['months_count'] > 0 else res['full_price']
    return jsonify(res)


def calculate_transfer_split(enrollment, target_course, transfer_date, custom_monthly_price=None, start_date=None, end_date=None):
    """Calcule le partage équitable de la cotisation et des salaires enseignants lors d'un transfert d'élève."""
    if not enrollment or not target_course:
        return {}

    start_dt = start_date or enrollment.enroll_date or date.today()
    transfer_dt = transfer_date or date.today()

    orig_dur = enrollment.duration_months if hasattr(enrollment, 'duration_months') else 1
    max_cycle_end = start_dt + timedelta(days=int(orig_dur * 31) + 5)

    end_dt = end_date or enrollment.custom_end_date or enrollment.end_date
    if not end_dt or end_dt > max_cycle_end or end_dt <= start_dt:
        end_dt = min(max_cycle_end, start_dt + timedelta(days=max(30, int(30.4 * orig_dur))))

    if end_dt <= start_dt:
        end_dt = start_dt + timedelta(days=30)

    if transfer_dt < start_dt:
        transfer_dt = start_dt
    if transfer_dt > end_dt:
        transfer_dt = end_dt

    total_price = float(custom_monthly_price) if custom_monthly_price and float(custom_monthly_price) > 0 else float(enrollment.monthly_price or target_course.price or 300.0)

    old_course = enrollment.course
    old_days = old_course.scheduled_weekdays if old_course else {0, 2, 4}
    new_days = target_course.scheduled_weekdays if target_course else {0, 2, 4}

    # 1. Nombre de jours calendaires
    if transfer_dt == start_dt:
        old_days_cnt = 0
        new_days_cnt = max(1, (end_dt - start_dt).days)
    elif transfer_dt >= end_dt:
        old_days_cnt = max(1, (end_dt - start_dt).days)
        new_days_cnt = 0
    else:
        old_days_cnt = (transfer_dt - start_dt).days + 1
        new_days_cnt = max(0, (end_dt - transfer_dt).days)

    tot_days_cnt = old_days_cnt + new_days_cnt

    # 2. Nombre de séances programmées (pour information et contrôle)
    old_sessions = 0
    cur = start_dt
    while cur <= transfer_dt:
        if cur.weekday() in old_days:
            old_sessions += 1
        cur += timedelta(days=1)

    new_sessions = 0
    cur = transfer_dt + timedelta(days=1) if transfer_dt < end_dt else transfer_dt
    while cur <= end_dt:
        if cur.weekday() in new_days:
            new_sessions += 1
        cur += timedelta(days=1)

    tot_sessions = old_sessions + new_sessions

    # 3. Ratio de répartition (au prorata des jours de la période)
    if tot_days_cnt > 0:
        ratio_old = old_days_cnt / float(tot_days_cnt)
    elif tot_sessions > 0:
        ratio_old = old_sessions / float(tot_sessions)
    else:
        ratio_old = 0.5

    ratio_old = max(0.0, min(1.0, ratio_old))

    old_share = round(total_price * ratio_old, 2)
    new_share = round(total_price - old_share, 2)

    # Informations enseignants et salaires estimés
    old_teacher = old_course.teacher if old_course else None
    new_teacher = target_course.teacher if target_course else None

    old_pct = 50.0
    if old_course and old_teacher:
        ct_old = CourseTeacher.query.filter_by(course_id=old_course.id, teacher_id=old_teacher.id).first()
        old_pct = ct_old.compensation_value if (ct_old and ct_old.compensation_value is not None) else (old_teacher.salary_amount if (old_teacher.salary_amount and old_teacher.salary_amount > 0) else 50.0)

    new_pct = 50.0
    if target_course and new_teacher:
        ct_new = CourseTeacher.query.filter_by(course_id=target_course.id, teacher_id=new_teacher.id).first()
        new_pct = ct_new.compensation_value if (ct_new and ct_new.compensation_value is not None) else (new_teacher.salary_amount if (new_teacher.salary_amount and new_teacher.salary_amount > 0) else 50.0)

    old_teacher_est = round(old_share * (old_pct / 100.0), 2)
    new_teacher_est = round(new_share * (new_pct / 100.0), 2)

    tot_paid = float(enrollment.total_paid or 0.0)
    reg_fee = max(0.0, float(enrollment.calculated_price or 0.0) - float(enrollment.monthly_price or 0.0))
    keep_paid = min(tot_paid, old_share + reg_fee)
    move_paid = round(tot_paid - keep_paid, 2)

    return {
        'total_price': total_price,
        'old_sessions': old_sessions,
        'new_sessions': new_sessions,
        'tot_sessions': tot_sessions,
        'old_days': old_days_cnt,
        'new_days': new_days_cnt,
        'tot_days': tot_days_cnt,
        'ratio_old': round(ratio_old * 100, 1),
        'ratio_new': round((1.0 - ratio_old) * 100, 1),
        'old_share': old_share,
        'new_share': new_share,
        'old_course_name': old_course.display_name if old_course else '-',
        'new_course_name': target_course.display_name,
        'old_teacher_name': old_teacher.full_name if old_teacher else 'Non assigné',
        'new_teacher_name': new_teacher.full_name if new_teacher else 'Non assigné',
        'old_pct': old_pct,
        'new_pct': new_pct,
        'old_teacher_est': old_teacher_est,
        'new_teacher_est': new_teacher_est,
        'tot_paid': tot_paid,
        'keep_paid': keep_paid,
        'move_paid': move_paid,
        'reg_fee': reg_fee,
        'start_date': start_dt.strftime('%d/%m/%Y'),
        'transfer_date': transfer_dt.strftime('%d/%m/%Y'),
        'end_date': end_dt.strftime('%d/%m/%Y'),
        'student_balance_remaining': max(0.0, round(total_price + reg_fee - tot_paid, 2))
    }


@app.route('/api/calculate_transfer_split')
@login_required
@role_required('admin', 'secretary')
def api_calculate_transfer_split():
    eid = _int(request.args.get('enrollment_id'))
    target_cid = _int(request.args.get('target_course_id'))
    transfer_dt = parse_date(request.args.get('transfer_date')) or date.today()
    custom_price = _f(request.args.get('custom_monthly_price'))
    start_dt = parse_date(request.args.get('start_date'))
    end_dt = parse_date(request.args.get('end_date'))

    e = Enrollment.query.get(eid) if eid else None
    target_course = Course.query.get(target_cid) if target_cid else None

    if not e or not target_course:
        return jsonify({'error': 'Données invalides'}), 400

    res = calculate_transfer_split(e, target_course, transfer_dt, custom_monthly_price=custom_price, start_date=start_dt, end_date=end_dt)
    return jsonify(res)


@app.route('/enrollments')
@login_required
@role_required('admin', 'secretary')
def enrollments():
    status_filter = request.args.get('status', 'active')
    q = request.args.get('q', '').strip()
    course_filter = _int(request.args.get('course_id'))

    query = Enrollment.query.options(
        joinedload(Enrollment.student),
        joinedload(Enrollment.course).joinedload(Course.teacher),
        joinedload(Enrollment.tariff)
    ).join(Student, Enrollment.student_id == Student.id, isouter=True)\
     .join(Course, Enrollment.course_id == Course.id, isouter=True)

    if status_filter != 'all':
        query = query.filter(Enrollment.status == status_filter)

    if course_filter:
        query = query.filter(Enrollment.course_id == course_filter)

    if q:
        en_filter = build_enrollment_search_filter(q)
        if en_filter is not None:
            query = query.filter(en_filter)

    enrolls = query.order_by(Enrollment.id.desc()).all()

    # High-performance batch pre-loading: eliminate N+1 queries
    pay_sums = dict(db.session.query(Payment.enrollment_id, db.func.sum(Payment.amount))
                    .filter(Payment.enrollment_id.isnot(None))
                    .group_by(Payment.enrollment_id).all())
    student_pay_sums = dict(db.session.query(Payment.student_id, db.func.sum(Payment.amount))
                            .filter(Payment.student_id.isnot(None))
                            .group_by(Payment.student_id).all())
    all_non_dropped = db.session.query(Enrollment.student_id, Enrollment.calculated_price, Enrollment.monthly_price)\
                        .filter(Enrollment.status != 'dropped').all()
    student_dues = {}
    for sid, calc_p, m_p in all_non_dropped:
        student_dues[sid] = student_dues.get(sid, 0.0) + (calc_p or m_p or 0.0)

    for e in enrolls:
        e._total_paid_cache = float(pay_sums.get(e.id, 0.0))
        if e.student:
            s_pay = float(student_pay_sums.get(e.student.id, 0.0))
            s_due = float(student_dues.get(e.student.id, 0.0))
            excess = max(0.0, s_pay - s_due)
            e.student._credit_balance_cache = round(excess + (e.student.credit_balance or 0.0), 2)

    total_due_sum = sum(e.due_amount for e in enrolls)
    total_paid_sum = sum(e.total_paid for e in enrolls)
    total_balance_sum = sum(e.balance for e in enrolls)
    expiring_count = sum(1 for e in enrolls if e.status == 'active' and e.end_date and e.days_remaining is not None and e.days_remaining <= 5)
    pending_count = Enrollment.query.filter_by(status='pending_assignment').count()
    all_trials = Enrollment.query.filter_by(status='trial').all()
    trial_count = len(all_trials)
    trial_completed_count = sum(1 for e in all_trials if e.trial_completed)
    all_courses = Course.query.filter_by(active=True).order_by(Course.name).all()

    return render_template('enrollments/list.html',
                           enrolls=enrolls,
                           status_filter=status_filter,
                           q=q,
                           course_filter=course_filter,
                           all_courses=all_courses,
                           total_due_sum=total_due_sum,
                           total_paid_sum=total_paid_sum,
                           total_balance_sum=total_balance_sum,
                           expiring_count=expiring_count,
                           pending_count=pending_count,
                           trial_count=trial_count,
                           trial_completed_count=trial_completed_count)


@app.route('/enrollments/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_new():
    if request.method == 'POST':
        d = request.form
        student_id = _int(d.get('student_id'))
        enroll_dt = parse_date(d.get('enroll_date')) or date.today()
        payment_plan = d.get('payment_plan', 'full')
        status = d.get('status', 'active')
        notes = d.get('notes')
        initial_payment = _f(d.get('initial_payment'))
        payment_method = d.get('payment_method', 'cash')

        # Multi-course selection support
        course_ids = [int(x) for x in request.form.getlist('course_ids') if x.isdigit()]
        if not course_ids and d.get('course_id'):
            c_val = _int(d.get('course_id'))
            if c_val:
                course_ids = [c_val]

        if not student_id or not course_ids:
            flash('Veuillez choisir un تلميذ وتحديد دورة تعليمية واحدة على الأقل', 'danger')
            return redirect(url_for('enrollment_new'))

        created_enrollments = []
        total_calculated_amount = 0.0

        for cid in course_ids:
            c = Course.query.get(cid)
            if not c:
                continue

            tot_sess = _int(d.get(f'total_sessions_{cid}'))
            default_unit = c.unit_monthly_price if hasattr(c, 'unit_monthly_price') else (c.price_per_month or (round(c.price / 3.0, 2) if c.billing_cycle in ('3months', 'trimestriel', '3 mois', 'quarterly') else c.price))
            m_price = _f(d.get(f'monthly_price_{cid}')) or default_unit
            reg_fee = _f(d.get(f'registration_fee_{cid}')) if d.get(f'registration_fee_{cid}') is not None else (c.registration_fee or 0.0)
            c_earned = _f(d.get(f'current_month_earned_{cid}'))
            d_amount = _f(d.get(f'deferred_amount_{cid}'))

            calc = calculate_course_sessions(cid, enroll_dt)
            tot_sess = tot_sess or calc['total_sessions']
            rem_sess = rem_sess or calc['remaining_sessions']
            m_price = m_price or calc['full_price']

            if not c_earned:
                c_earned = calc['current_month_earned']
            if not d_amount:
                d_amount = calc['deferred_next_month']

            charged_price = m_price + reg_fee

            c_obj = Course.query.get(cid)
            sched_days = set()
            if c_obj and c_obj.scheduled_days:
                try:
                    sched_days = set(int(x.strip()) for x in c_obj.scheduled_days.split(',') if x.strip().isdigit())
                except Exception:
                    sched_days = {0, 2, 4}
            else:
                sched_days = {0, 2, 4}
            m_end_dt = calculate_last_session_date(enroll_dt, tot_sess, sched_days)
            if enroll_dt.day == 1:
                _, l_d = calendar.monthrange(enroll_dt.year, enroll_dt.month)
                full_m_end = date(enroll_dt.year, enroll_dt.month, l_d)
                if m_end_dt < full_m_end:
                    m_end_dt = full_m_end

            e = Enrollment(
                student_id=student_id,
                course_id=cid,
                enroll_date=enroll_dt,
                payment_plan=payment_plan,
                status=status,
                total_sessions_month=tot_sess,
                attended_sessions_month=rem_sess,
                monthly_price=m_price,
                calculated_price=charged_price,
                current_month_earned=c_earned,
                deferred_amount=d_amount,
                custom_end_date=m_end_dt,
                notes=f"Frais d'inscription: {reg_fee} DH. " + (notes or ''),
                created_by=current_user().id if current_user() else None
            )
            db.session.add(e)
            created_enrollments.append(e)
            total_calculated_amount += charged_price

        db.session.commit()

        # Create single unified Invoice for all enrolled courses
        tva_rate = SH.get_float('tva_rate') if SH.is_enabled('enable_tva') else 0
        subtotal = round(total_calculated_amount / (1 + tva_rate / 100), 2) if tva_rate else total_calculated_amount
        tva_amt = round(subtotal * tva_rate / 100, 2)

        inv = Invoice(
            number=SH.next_invoice_number('invoice_prefix', 'next_invoice_number'),
            type='facture',
            student_id=student_id,
            enrollment_id=created_enrollments[0].id if created_enrollments else None,
            issue_date=enroll_dt,
            due_date=enroll_dt + timedelta(days=SH.get_int('due_days', 7)),
            subtotal=subtotal,
            tva_rate=tva_rate,
            tva_amount=tva_amt,
            total=total_calculated_amount,
            status='unpaid'
        )
        db.session.add(inv)
        db.session.commit()

        # Add line items to invoice
        for e in created_enrollments:
            item_desc = f"{e.course.display_name} (Scolarité)"
            item = InvoiceItem(
                invoice_id=inv.id,
                enrollment_id=e.id,
                description=item_desc,
                amount=e.monthly_price
            )
            db.session.add(item)

            reg_fee_val = max(0.0, e.calculated_price - e.monthly_price)
            if reg_fee_val > 0:
                item_reg = InvoiceItem(
                    invoice_id=inv.id,
                    enrollment_id=e.id,
                    description=f"Frais d'inscription - {e.course.display_name}",
                    amount=reg_fee_val
                )
                db.session.add(item_reg)

        # Initial payment record if paid anything today
        if initial_payment > 0:
            payment_actual_date = parse_date(d.get('payment_date')) or date.today()
            if payment_actual_date > date.today():
                payment_actual_date = date.today()
            record_payment_transaction(
                student_id=student_id,
                amount=initial_payment,
                method=payment_method,
                pay_date=payment_actual_date,
                note=f"Paiement inscription {len(created_enrollments)} cours",
                invoice_id=inv.id,
                enrollments=created_enrollments
            )
            if initial_payment >= inv.total:
                inv.status = 'paid'
            elif initial_payment > 0:
                inv.status = 'partial'

        db.session.commit()
        log_action('enroll_multi', f"Student {student_id} - {len(created_enrollments)} courses")
        flash(f"Inscription réussie ({len(created_enrollments)} cours) - Facture {inv.number}", 'success')
        return redirect(url_for('enrollments'))

    return render_template('enrollments/form.html',
                           students=Student.query.filter_by(status='active').all(),
                           courses=Course.query.filter_by(active=True).all())


@app.route('/enrollments/<int:eid>/status', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_status(eid):
    e = Enrollment.query.get_or_404(eid)
    e.status = request.form.get('status', 'active')
    db.session.commit(); flash('Statut mis à jour', 'success')
    return redirect(request.referrer or url_for('enrollments'))


@app.route('/enrollments/<int:eid>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_edit(eid):
    e = Enrollment.query.get_or_404(eid)
    if request.method == 'POST':
        d = request.form
        e.course_id = _int(d.get('course_id')) or e.course_id

        # Update dates
        new_enroll_dt = parse_date(d.get('enroll_date'))
        if new_enroll_dt:
            e.enroll_date = new_enroll_dt
            pays = Payment.query.filter_by(enrollment_id=e.id).all()
            for p in pays:
                p.date = new_enroll_dt

        if 'custom_end_date' in d:
            e.custom_end_date = parse_date(d.get('custom_end_date'))

        e.total_sessions_month = _int(d.get('total_sessions_month')) or e.total_sessions_month
        e.attended_sessions_month = _int(d.get('attended_sessions_month')) or e.attended_sessions_month
        e.monthly_price = _f(d.get('monthly_price')) or e.monthly_price
        e.calculated_price = _f(d.get('calculated_price')) or e.calculated_price

        # Auto-recalculate accounting split
        if e.total_sessions_month > 0:
            e.current_month_earned = round((e.monthly_price / e.total_sessions_month) * e.attended_sessions_month, 2)
            e.deferred_amount = max(0.0, round(e.monthly_price - e.current_month_earned, 2))

        e.status = d.get('status', 'active')
        e.notes = d.get('notes')
        db.session.commit()
        log_action('enrollment_edit', f"Enrollment {e.id} updated")
        flash('Inscription, dates et groupe mis à jour avec succès', 'success')
        return redirect(url_for('enrollments'))

    return render_template('enrollments/edit.html', e=e, courses=Course.query.filter_by(active=True).all())


@app.route('/enrollments/<int:eid>/renew', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_renew(eid):
    prev_e = Enrollment.query.get_or_404(eid)
    stu = prev_e.student

    default_renew_date = (prev_e.end_date + timedelta(days=1)) if prev_e.end_date else date.today()

    course_display_name = prev_e.course_name_display

    # Determine student's custom/negotiated monthly price
    if prev_e.monthly_price and prev_e.monthly_price > 0:
        unit_price = float(prev_e.monthly_price)
    elif prev_e.course:
        unit_price = float(prev_e.course.unit_monthly_price)
    elif prev_e.tariff:
        unit_price = float(getattr(prev_e.tariff, 'price_per_month', None) or (round(prev_e.tariff.price / 3.0, 2) if prev_e.tariff.billing_cycle in ('3months', 'trimestriel', '3 mois', 'quarterly') else prev_e.tariff.price) or 300.0)
    else:
        unit_price = float(prev_e.calculated_price or 300.0)

    # Determine previous duration
    prev_duration = prev_e.duration_months if hasattr(prev_e, 'duration_months') else 1

    if request.method == 'POST':
        d = request.form
        renew_dt = parse_date(d.get('renew_date')) or default_renew_date
        duration_months = _int(d.get('duration_months')) or prev_duration or 1
        payment_amount = _f(d.get('payment_amount'))
        payment_method = d.get('payment_method', 'cash')
        notes = d.get('notes')

        if prev_e.course_id:
            calc = calculate_course_sessions(prev_e.course_id, renew_dt, months_count=duration_months, custom_unit_price=unit_price)
        else:
            spw = prev_e.tariff.sessions_per_week if (prev_e.tariff and prev_e.tariff.sessions_per_week) else 3
            tot_s = spw * 4 * duration_months
            calc = {
                'total_sessions': tot_s,
                'remaining_sessions': tot_s,
                'full_price': round(unit_price * duration_months, 2),
                'months_count': duration_months
            }

        tot_sess = _int(d.get('total_sessions')) or calc['total_sessions']
        rem_sess = _int(d.get('attended_sessions')) or calc['remaining_sessions']
        m_price = _f(d.get('monthly_price')) or calc['full_price']

        # Calculate renewal end date (using course session schedule if course assigned)
        if prev_e.course_id:
            sched_days = prev_e.scheduled_weekdays
            renew_end_date = calculate_last_session_date(renew_dt, tot_sess, sched_days)
        elif renew_dt.day == 1:
            end_year = renew_dt.year
            end_month = renew_dt.month + duration_months - 1
            while end_month > 12:
                end_month -= 12
                end_year += 1
            _, max_d = calendar.monthrange(end_year, end_month)
            renew_end_date = date(end_year, end_month, max_d)
        else:
            end_year = renew_dt.year
            end_month = renew_dt.month + duration_months
            while end_month > 12:
                end_month -= 12
                end_year += 1
            _, max_d = calendar.monthrange(end_year, end_month)
            end_day = min(renew_dt.day, max_d)
            renew_end_date = date(end_year, end_month, end_day) - timedelta(days=1)

        new_e = Enrollment(
            student_id=stu.id,
            course_id=prev_e.course_id,
            tariff_id=prev_e.tariff_id,
            enroll_date=renew_dt,
            custom_end_date=renew_end_date,
            payment_plan='monthly' if duration_months == 1 else f'{duration_months}months',
            status='active' if prev_e.course_id else 'pending_assignment',
            total_sessions_month=tot_sess,
            attended_sessions_month=rem_sess,
            monthly_price=unit_price,
            calculated_price=m_price,
            current_month_earned=unit_price,
            deferred_amount=max(0.0, round(m_price - unit_price, 2)),
            notes=notes or f"Renouvellement ({duration_months} mois) suite à l'inscription N° {prev_e.id}",
            created_by=current_user().id if current_user() else None
        )
        db.session.add(new_e)

        # Transition prev_e: keep active only if its running period hasn't ended and renewal starts in future
        if prev_e.end_date and prev_e.end_date >= date.today() and renew_dt > date.today():
            prev_e.status = 'active'
        else:
            prev_e.status = 'completed'
        db.session.commit()

        tva_rate = SH.get_float('tva_rate') if SH.is_enabled('enable_tva') else 0
        subtotal = round(m_price / (1 + tva_rate / 100), 2) if tva_rate else m_price
        tva_amt = round(subtotal * tva_rate / 100, 2)

        inv = Invoice(
            number=SH.next_invoice_number('invoice_prefix', 'next_invoice_number'),
            type='facture',
            student_id=stu.id,
            enrollment_id=new_e.id,
            issue_date=date.today(),
            due_date=renew_dt + timedelta(days=SH.get_int('due_days', 7)),
            subtotal=subtotal,
            tva_rate=tva_rate,
            tva_amount=tva_amt,
            total=m_price,
            status='unpaid'
        )
        db.session.add(inv)
        db.session.commit()

        dur_txt = f" ({duration_months} mois)" if duration_months > 1 else ""
        item = InvoiceItem(
            invoice_id=inv.id,
            enrollment_id=new_e.id,
            description=f"Renouvellement {course_display_name}{dur_txt}",
            amount=m_price
        )
        db.session.add(item)

        # Handle Student Credit Balance (Avoir disponible) if checked
        use_credit = d.get('use_credit') == '1'
        credit_applied = 0.0
        renew_payment_date = parse_date(d.get('payment_date')) or date.today()
        if renew_payment_date > date.today():
            renew_payment_date = date.today()

        if use_credit and stu.dynamic_credit_balance > 0:
            credit_applied = min(float(stu.dynamic_credit_balance), float(m_price))
            stu.credit_balance = max(0.0, float(stu.credit_balance or 0.0) - credit_applied)
            if credit_applied > 0:
                record_payment_transaction(
                    student_id=stu.id,
                    amount=credit_applied,
                    method='credit_balance',
                    pay_date=renew_payment_date,
                    note=f"Avoir déduit sur renouvellement {course_display_name}",
                    invoice_id=inv.id,
                    enrollments=[new_e]
                )

        # Handle Previous Unpaid Balance if requested
        include_prev_bal = d.get('include_prev_balance') == '1'
        target_enrollments = [prev_e, new_e] if (include_prev_bal and prev_e.balance > 0) else [new_e]

        renew_pay_amt = max(0.0, payment_amount)
        eff_renew_method = 'differe' if renew_pay_amt <= 0 and (not payment_method or payment_method in ('cash', 'none')) else payment_method
        renew_pay_note = f"Paiement renouvellement {course_display_name}" if renew_pay_amt > 0 else f"Renouvellement différé (0 DH) {course_display_name}"
        p = record_payment_transaction(
            student_id=stu.id,
            amount=renew_pay_amt,
            method=eff_renew_method,
            pay_date=renew_payment_date,
            note=renew_pay_note,
            invoice_id=inv.id,
            enrollments=target_enrollments
        )

        db.session.commit()
        log_action('enrollment_renew', f"Student {stu.full_name} renewed {course_display_name}")
        flash(f"Abonnement renouvelé avec succès pour {stu.full_name} jusqu'au {new_e.end_date}", 'success')

        if p and renew_pay_amt > 0:
            return redirect(url_for('payment_receipt', pid=p.id))
        return redirect(url_for('invoice_view', iid=inv.id))

    if prev_e.course_id:
        calc = calculate_course_sessions(prev_e.course_id, default_renew_date, months_count=prev_duration, custom_unit_price=unit_price)
    else:
        spw = prev_e.tariff.sessions_per_week if (prev_e.tariff and prev_e.tariff.sessions_per_week) else 3
        tot_s = spw * 4 * prev_duration
        calc = {
            'total_sessions': tot_s,
            'remaining_sessions': tot_s,
            'full_price': round(unit_price * prev_duration, 2),
            'months_count': prev_duration
        }

    return render_template('enrollments/renew.html', prev_e=prev_e, stu=stu, default_renew_date=default_renew_date, calc=calc, unit_price=unit_price, prev_duration=prev_duration)


# ---------------------------------------------------------------------------
# Multi-Class Group Renewal Route (Renouvellement Groupé sur un seul reçu)
# ---------------------------------------------------------------------------
@app.route('/students/<int:sid>/renew', methods=['GET', 'POST'])
@app.route('/students/<int:sid>/renew_batch', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def student_renew_batch(sid):
    stu = Student.query.get_or_404(sid)

    # 1. Retrieve all renewable enrollments (newest per course)
    all_ens = Enrollment.query.filter_by(student_id=sid)\
        .filter(Enrollment.status.in_(['active', 'completed', 'paused', 'trial']))\
        .order_by(Enrollment.id.desc()).all()

    seen_keys = set()
    renewable_items = []
    for e in all_ens:
        key = (e.course_id, e.tariff_id)
        if key not in seen_keys:
            seen_keys.add(key)

            # Default renewal start date: day after current period ends
            def_renew_dt = (e.end_date + timedelta(days=1)) if e.end_date else date.today()

            # Unit monthly price
            if e.monthly_price and e.monthly_price > 0:
                u_price = float(e.monthly_price)
            elif e.course:
                u_price = float(e.course.unit_monthly_price)
            elif e.tariff:
                u_price = float(getattr(e.tariff, 'price_per_month', None) or (round(e.tariff.price / 3.0, 2) if e.tariff.billing_cycle in ('3months', 'trimestriel', '3 mois', 'quarterly') else e.tariff.price) or 300.0)
            else:
                u_price = float(e.calculated_price or 300.0)

            prev_dur = e.duration_months if hasattr(e, 'duration_months') else 1

            if e.course_id:
                calc = calculate_course_sessions(e.course_id, def_renew_dt, months_count=prev_dur, custom_unit_price=u_price)
            else:
                spw = e.tariff.sessions_per_week if (e.tariff and e.tariff.sessions_per_week) else 3
                tot_s = spw * 4 * prev_dur
                calc = {
                    'total_sessions': tot_s,
                    'remaining_sessions': tot_s,
                    'full_price': round(u_price * prev_dur, 2),
                    'months_count': prev_dur
                }

            renewable_items.append({
                'enrollment': e,
                'course_id': e.course_id or 0,
                'tariff_id': e.tariff_id or 0,
                'course_name': e.course_name_display,
                'teacher_name': e.course.teacher.full_name if (e.course and e.course.teacher) else 'Non assigné',
                'schedule_label': e.course.schedule_label if e.course else '3 séances/sem',
                'end_date': e.end_date,
                'days_remaining': e.days_remaining,
                'status': e.status,
                'balance': e.balance,
                'unit_price': u_price,
                'duration_months': prev_dur,
                'default_renew_date': def_renew_dt,
                'calc': calc
            })

    if not renewable_items:
        flash(f"Aucune inscription active ou récente à renouveler pour {stu.full_name}.", "warning")
        return redirect(url_for('student_view', sid=stu.id))

    if request.method == 'POST':
        d = request.form
        selected_eids = [int(x) for x in d.getlist('selected_eids') if x.isdigit()]
        if not selected_eids:
            flash("Veuillez cocher au moins une classe à renouveler.", "warning")
            return redirect(url_for('student_renew_batch', sid=sid))

        created_enrollments = []
        total_invoiced_amount = 0.0
        enrollment_meta = {}
        earliest_renew_dt = None

        for eid in selected_eids:
            prev_e = Enrollment.query.get(eid)
            if not prev_e or prev_e.student_id != sid:
                continue

            renew_dt = parse_date(d.get(f'renew_date_{eid}')) or date.today()
            if not earliest_renew_dt or renew_dt < earliest_renew_dt:
                earliest_renew_dt = renew_dt

            dur_m = _int(d.get(f'duration_months_{eid}')) or 1
            tot_sess = _int(d.get(f'total_sessions_{eid}'))
            rem_sess = _int(d.get(f'attended_sessions_{eid}'))
            notes = (d.get(f'notes_{eid}') or '').strip()

            if prev_e.monthly_price and prev_e.monthly_price > 0:
                u_price = float(prev_e.monthly_price)
            elif prev_e.course:
                u_price = float(prev_e.course.unit_monthly_price)
            else:
                u_price = 300.0

            m_price = _f(d.get(f'monthly_price_{eid}'))
            if m_price is None or m_price <= 0:
                m_price = round(u_price * dur_m, 2)

            if prev_e.course_id:
                calc = calculate_course_sessions(prev_e.course_id, renew_dt, months_count=dur_m, custom_unit_price=u_price)
            else:
                spw = prev_e.tariff.sessions_per_week if (prev_e.tariff and prev_e.tariff.sessions_per_week) else 3
                tot_s = spw * 4 * dur_m
                calc = {'total_sessions': tot_s, 'remaining_sessions': tot_s}

            tot_sess = tot_sess or calc['total_sessions']
            rem_sess = rem_sess or calc['remaining_sessions']

            # Calculate end date
            if prev_e.course_id:
                sched_days = prev_e.scheduled_weekdays
                renew_end_date = calculate_last_session_date(renew_dt, tot_sess, sched_days)
            elif renew_dt.day == 1:
                end_year = renew_dt.year
                end_month = renew_dt.month + dur_m - 1
                while end_month > 12:
                    end_month -= 12
                    end_year += 1
                _, max_d = calendar.monthrange(end_year, end_month)
                renew_end_date = date(end_year, end_month, max_d)
            else:
                end_year = renew_dt.year
                end_month = renew_dt.month + dur_m
                while end_month > 12:
                    end_month -= 12
                    end_year += 1
                _, max_d = calendar.monthrange(end_year, end_month)
                end_day = min(renew_dt.day, max_d)
                renew_end_date = date(end_year, end_month, end_day) - timedelta(days=1)

            unit_monthly = round(m_price / dur_m, 2) if dur_m > 0 else m_price
            new_e = Enrollment(
                student_id=sid,
                course_id=prev_e.course_id,
                tariff_id=prev_e.tariff_id,
                enroll_date=renew_dt,
                custom_end_date=renew_end_date,
                payment_plan='monthly' if dur_m == 1 else f'{dur_m}months',
                status='active' if prev_e.course_id else 'pending_assignment',
                total_sessions_month=tot_sess,
                attended_sessions_month=rem_sess,
                monthly_price=unit_monthly,
                calculated_price=m_price,
                current_month_earned=unit_monthly,
                deferred_amount=max(0.0, round(m_price - unit_monthly, 2)),
                notes=notes or f"Renouvellement groupé ({dur_m} mois) suite à l'inscription N° {prev_e.id}",
                created_by=current_user().id if current_user() else None
            )
            db.session.add(new_e)

            # Transition old enrollment
            if prev_e.end_date and prev_e.end_date >= date.today() and renew_dt > date.today():
                prev_e.status = 'active'
            else:
                prev_e.status = 'completed'

            created_enrollments.append(new_e)
            total_invoiced_amount += m_price
            enrollment_meta[new_e] = {
                'course_name': prev_e.course_name_display,
                'dur_m': dur_m,
                'amount': m_price
            }

        db.session.commit()

        # 2. Unified Invoice
        tva_rate = SH.get_float('tva_rate') if SH.is_enabled('enable_tva') else 0
        subtotal = round(total_invoiced_amount / (1 + tva_rate / 100), 2) if tva_rate else total_invoiced_amount
        tva_amt = round(subtotal * tva_rate / 100, 2)
        min_dt = earliest_renew_dt or date.today()

        inv = Invoice(
            number=SH.next_invoice_number('invoice_prefix', 'next_invoice_number'),
            type='facture',
            student_id=sid,
            enrollment_id=created_enrollments[0].id if created_enrollments else None,
            issue_date=date.today(),
            due_date=max(min_dt, date.today()) + timedelta(days=SH.get_int('due_days', 7)),
            subtotal=subtotal,
            tva_rate=tva_rate,
            tva_amount=tva_amt,
            total=total_invoiced_amount,
            status='unpaid'
        )
        db.session.add(inv)
        db.session.commit()

        # Invoice items
        for e in created_enrollments:
            meta = enrollment_meta[e]
            dur_txt = f" ({meta['dur_m']} mois)" if meta['dur_m'] > 1 else ""
            item = InvoiceItem(
                invoice_id=inv.id,
                enrollment_id=e.id,
                description=f"Renouvellement {meta['course_name']}{dur_txt}",
                amount=meta['amount']
            )
            db.session.add(item)
        db.session.commit()

        # 3. Shared Receipt & Credit Balance Deduction if selected
        shared_receipt_num = SH.next_invoice_number('receipt_prefix', 'next_receipt_number')
        use_credit = d.get('use_credit') == '1'
        credit_app = 0.0
        p_credit = None
        pay_date = parse_date(d.get('payment_date')) or date.today()
        if pay_date > date.today():
            pay_date = date.today()

        if use_credit and stu.dynamic_credit_balance > 0:
            credit_app = min(float(stu.dynamic_credit_balance), float(total_invoiced_amount))
            stu.credit_balance = max(0.0, float(stu.credit_balance or 0.0) - credit_app)
            if credit_app > 0:
                p_credit = record_payment_transaction(
                    student_id=sid,
                    amount=credit_app,
                    method='credit_balance',
                    pay_date=pay_date,
                    note=f"Avoir déduit sur renouvellement groupé ({len(created_enrollments)} classes)",
                    invoice_id=inv.id,
                    enrollments=created_enrollments,
                    receipt_number=shared_receipt_num
                )

        # 4. Cash / Transaction Payment
        pay_amt = _f(d.get('payment_amount'))
        if pay_amt is None:
            pay_amt = max(0.0, total_invoiced_amount - credit_app)
        pay_amt = max(0.0, pay_amt)

        pay_method = d.get('payment_method', 'cash')
        eff_method = 'differe' if pay_amt <= 0 and (not pay_method or pay_method in ('cash', 'none')) else pay_method
        courses_str = ", ".join(enrollment_meta[e]['course_name'] for e in created_enrollments)
        pay_note = f"Paiement renouvellement groupé ({len(created_enrollments)} classes): {courses_str}" if pay_amt > 0 else f"Renouvellement groupé différé (0 DH): {courses_str}"

        p = record_payment_transaction(
            student_id=sid,
            amount=pay_amt,
            method=eff_method,
            pay_date=pay_date,
            note=pay_note,
            invoice_id=inv.id,
            enrollments=created_enrollments,
            receipt_number=shared_receipt_num
        )

        db.session.commit()
        log_action('enrollment_renew_batch', f"Student {stu.full_name} renewed {len(created_enrollments)} classes on unified receipt {shared_receipt_num}")
        flash(f"Renouvellement groupé validé avec succès pour {stu.full_name} ({len(created_enrollments)} classes sur un seul reçu) !", 'success')

        target_p = p if pay_amt > 0 else (p_credit or p)
        if target_p and (pay_amt > 0 or (p_credit and p_credit.amount > 0)):
            return redirect(url_for('payment_receipt', pid=target_p.id))
        return redirect(url_for('invoice_view', iid=inv.id))

    return render_template('students/renew_batch.html', stu=stu, items=renewable_items)


# ---------------------------------------------------------------------------
# Express All-in-One Student Registration & Billing Route
# ---------------------------------------------------------------------------
@app.route('/express_enrollment', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def express_enrollment():
    if request.method == 'POST':
        d = request.form
        student_mode = d.get('student_mode', 'new')
        student_id = _int(d.get('student_id'))
        
        # 1. Obtain or Create Student
        if student_mode == 'new' or not student_id:
            full_name = (d.get('full_name') or '').strip()
            if not full_name:
                flash('Veuillez entrer le nom et prénom du nouvel élève', 'danger')
                return redirect(url_for('express_enrollment'))
            
            raw_cin = (d.get('cin') or '').strip().upper()
            raw_phone = (d.get('phone') or '').strip()
            raw_parent_phone = (d.get('parent_phone') or '').strip()

            fn_parts = full_name.split()
            first_name = fn_parts[0] if fn_parts else ''
            last_name = " ".join(fn_parts[1:]) if len(fn_parts) > 1 else ''

            # Duplicate prevention check
            existing_stu = None
            if first_name and last_name:
                q = Student.query.filter(
                    db.func.lower(Student.first_name) == first_name.lower(),
                    db.func.lower(Student.last_name) == last_name.lower()
                )
                if raw_parent_phone or raw_phone:
                    filters = []
                    if raw_parent_phone:
                        filters.append(Student.parent_phone == raw_parent_phone)
                        filters.append(Student.phone == raw_parent_phone)
                    if raw_phone:
                        filters.append(Student.phone == raw_phone)
                        filters.append(Student.parent_phone == raw_phone)
                    existing_stu = q.filter(db.or_(*filters)).first()
                if not existing_stu and raw_cin:
                    existing_stu = Student.query.filter_by(cin=raw_cin).first()

            if existing_stu:
                stu = existing_stu
                student_id = stu.id
                flash(f"L'élève {stu.full_name} ({stu.code}) existe déjà. Son dossier a été utilisé pour éviter un doublon.", 'info')
            else:
                # Auto-link family code by parent phone / phone
                fam_code = None
                p_check = raw_parent_phone or raw_phone
                if p_check and len(p_check) >= 8:
                    clean_p = p_check.replace(' ', '').replace('-', '').replace('.', '')
                    sibling = Student.query.filter(
                        db.or_(
                            Student.parent_phone.like(f"%{clean_p[-8:]}%"),
                            Student.phone.like(f"%{clean_p[-8:]}%")
                        )
                    ).first()
                    if sibling:
                        fam_code = sibling.family_code or f"FAM-{clean_p[-6:]}"
                        if not sibling.family_code:
                            sibling.family_code = fam_code
                            db.session.commit()

                stu = Student(
                    code=SH.gen_code('student_prefix', 'next_student_number'),
                    first_name=first_name,
                    last_name=last_name,
                    birth_date=parse_date(d.get('birth_date')),
                    cin=raw_cin or None,
                    phone=raw_phone or None,
                    parent_phone=raw_parent_phone or None,
                    family_code=fam_code,
                    school_level=d.get('school_level'),
                    status='active',
                    created_by=current_user().id if current_user() else None
                )
                db.session.add(stu)
                db.session.commit()
                student_id = stu.id

            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    ext = os.path.splitext(filename)[1]
                    new_fn = f"student_{stu.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_fn))
                    stu.photo = new_fn
                    db.session.commit()

            log_action('student_add', f"Student {stu.code} {stu.full_name} created via Express (CIN: {stu.cin or 'N/A'})")
        else:
            stu = Student.query.get_or_404(student_id)
            raw_cin = (d.get('cin') or '').strip().upper()
            if raw_cin and not stu.cin:
                stu.cin = raw_cin
                db.session.commit()

        course_mode = d.get('course_mode', 'specific')
        course_ids = request.form.getlist('course_ids')
        tariff_ids = request.form.getlist('tariff_ids')

        # -------------------------------------------------------------
        # SPECIAL MODE: SÉANCE D'ESSAI GRATUITE (Uniquement pour Soutien)
        # -------------------------------------------------------------
        if course_mode == 'trial':
            if not course_ids:
                flash("Veuillez sélectionner au moins une classe de soutien pour la séance d'essai gratuit", 'warning')
                return redirect(url_for('express_enrollment'))

            enroll_dt = parse_date(d.get('enroll_date')) or date.today()
            payment_method = d.get('payment_method', 'cash')
            notes = d.get('notes')
            created_trial_enrollments = []

            for cid_str in course_ids:
                cid = _int(cid_str)
                c = Course.query.get(cid)
                if not c:
                    continue
                if c.category != 'tutoring':
                    flash(f"La matière '{c.display_name}' est un cours de langue. Les séances d'essai sont exclusivement réservées aux matières de soutien scolaire.", 'danger')
                    return redirect(url_for('express_enrollment'))
                if not c.teacher_id:
                    flash(f"Impossible d'assigner l'essai à la classe '{c.display_name}' : aucun enseignant assigné.", 'danger')
                    return redirect(url_for('express_enrollment'))

                c_enroll_dt = parse_date(d.get(f'course_date_{cid}')) or enroll_dt
                e = Enrollment(
                    student_id=student_id,
                    course_id=c.id,
                    enroll_date=c_enroll_dt,
                    payment_plan='trial',
                    status='trial',
                    total_sessions_month=1,
                    attended_sessions_month=0,
                    monthly_price=0.0,
                    calculated_price=0.0,
                    current_month_earned=0.0,
                    deferred_amount=0.0,
                    custom_end_date=c_enroll_dt,
                    notes=f"🧪 Séance d'essai gratuite (Soutien). " + (notes or ''),
                    created_by=current_user().id if current_user() else None
                )
                db.session.add(e)
                created_trial_enrollments.append(e)

            db.session.commit()

            # Create 0 DH Invoice & Transaction Receipt
            inv = Invoice(
                number=SH.next_invoice_number('invoice_prefix', 'next_invoice_number'),
                type='facture',
                student_id=student_id,
                enrollment_id=created_trial_enrollments[0].id if created_trial_enrollments else None,
                issue_date=enroll_dt,
                due_date=enroll_dt,
                subtotal=0.0,
                tva_rate=0.0,
                tva_amount=0.0,
                total=0.0,
                status='paid'
            )
            db.session.add(inv)
            db.session.commit()

            for e in created_trial_enrollments:
                item = InvoiceItem(
                    invoice_id=inv.id,
                    enrollment_id=e.id,
                    description=f"🧪 Séance d'essai gratuite - {e.course_name_display}",
                    amount=0.0
                )
                db.session.add(item)

            p = record_payment_transaction(
                student_id=student_id,
                amount=0.0,
                method=payment_method,
                pay_date=date.today(),
                note="Séance d'essai gratuite (0 DH)",
                invoice_id=inv.id,
                enrollments=created_trial_enrollments
            )
            db.session.commit()

            log_action('express_enrollment_trial', f"Student {stu.full_name} registered for trial session in {[e.course_name_display for e in created_trial_enrollments]}")
            flash(f"Séance d'essai gratuite de {stu.full_name} enregistrée avec succès !", 'success')

            if p:
                return redirect(url_for('payment_receipt', pid=p.id))
            return redirect(url_for('enrollments', status='trial'))

        # -------------------------------------------------------------
        # SPECIAL MODE: COURS PARTICULIER / PERSONNALISÉ (1 PERSONNE)
        # -------------------------------------------------------------
        if course_mode == 'private':
            private_subject = (d.get('private_subject') or '').strip()
            if private_subject == 'Autre' and (d.get('private_subject_custom') or '').strip():
                private_subject = d.get('private_subject_custom').strip()
            if not private_subject:
                flash("Veuillez renseigner la matière ou la langue du cours particulier", "warning")
                return redirect(url_for('express_enrollment'))

            teacher_id = _int(d.get('private_teacher_id'))
            if not teacher_id:
                flash("Veuillez sélectionner un enseignant pour ce cours particulier", "warning")
                return redirect(url_for('express_enrollment'))

            t_obj = Teacher.query.get(teacher_id)
            if not t_obj:
                flash("Enseignant sélectionné introuvable", "danger")
                return redirect(url_for('express_enrollment'))

            room_id = _int(d.get('private_room_id')) or None
            enroll_dt = parse_date(d.get('enroll_date')) or date.today()
            category = d.get('private_category', 'language')
            level = d.get('private_level') or 'Sur mesure'
            hours = max(1.0, _f(d.get('private_hours')) or 15.0)
            hourly_rate = _f(d.get('private_hourly_rate')) or 175.0
            total_price = _f(d.get('private_total_price'))
            if not total_price or total_price <= 0:
                total_price = hours * hourly_rate

            reg_fee = _f(d.get('private_reg_fee')) or 0.0
            initial_payment = _f(d.get('initial_payment'))
            payment_method = d.get('payment_method', 'cash')
            notes = d.get('notes')

            start_time = (d.get('private_start_time') or '').strip()
            end_time = (d.get('private_end_time') or '').strip()
            private_days = request.form.getlist('private_days')

            # Calculate session duration
            sess_dur = '1h30'
            sess_mins = 90
            if start_time and end_time:
                sess_dur = calculate_duration_str(start_time, end_time) or '1h30'
                try:
                    sh, sm = map(int, start_time.split(':'))
                    eh, em = map(int, end_time.split(':'))
                    dm = (eh * 60 + em) - (sh * 60 + sm)
                    if dm > 0:
                        sess_mins = dm
                except Exception:
                    sess_mins = 90

            sess_hours = max(0.5, sess_mins / 60.0)
            tot_sess = max(1, round(hours / sess_hours))

            # Scheduled days set
            scheduled_days_set = set()
            if private_days:
                try:
                    scheduled_days_set = set(int(x) for x in private_days if x.isdigit())
                except Exception:
                    scheduled_days_set = {0, 2}
            else:
                scheduled_days_set = {0, 2}

            c_end_dt = calculate_last_session_date(enroll_dt, tot_sess, scheduled_days_set)

            # Auto-create the 1-person Course
            course_code = SH.gen_code('course_prefix', 'next_student_number')
            course_name = f"Particulier — {stu.full_name} ({private_subject})"
            new_course = Course(
                code=course_code,
                name=course_name,
                category=category,
                language=private_subject,
                level=level,
                group_name=f"1-to-1 ({int(hours)}h)",
                billing_cycle='pack',
                price=total_price,
                price_per_month=total_price,
                registration_fee=reg_fee,
                sessions_per_week=len(scheduled_days_set),
                session_duration=sess_dur,
                scheduled_days=",".join(str(d_val) for d_val in sorted(list(scheduled_days_set))),
                teacher_id=teacher_id,
                room_id=room_id,
                max_students=1,
                start_date=enroll_dt,
                end_date=c_end_dt,
                active=True,
                notes=f"Cours particulier personnalisé (1-to-1) pour {stu.full_name}. Pack {int(hours)}h à {hourly_rate:.0f} DH/h. " + (notes or '')
            )
            db.session.add(new_course)
            db.session.commit()

            # Schedule slots creation for manual timetable
            if start_time and end_time and scheduled_days_set:
                for day_val in sorted(list(scheduled_days_set)):
                    slot = ScheduleSlot(
                        course_id=new_course.id,
                        day_of_week=day_val,
                        start_time=start_time,
                        end_time=end_time
                    )
                    db.session.add(slot)

            # Course teacher assignment
            ct = CourseTeacher(
                course_id=new_course.id,
                teacher_id=teacher_id,
                start_date=enroll_dt,
                compensation_type='hourly',
                compensation_value=100.0,
                is_active=True
            )
            db.session.add(ct)

            # Enrollment
            charged_price = total_price + reg_fee
            e = Enrollment(
                student_id=student_id,
                course_id=new_course.id,
                enroll_date=enroll_dt,
                payment_plan='pack',
                status='active',
                total_sessions_month=tot_sess,
                attended_sessions_month=tot_sess,
                monthly_price=total_price,
                calculated_price=charged_price,
                current_month_earned=total_price,
                deferred_amount=0.0,
                custom_end_date=c_end_dt,
                notes=f"Cours Particulier 1-to-1 ({private_subject}). Pack {int(hours)}h. Tarif: {hourly_rate:.0f} DH/h. " + (notes or ''),
                created_by=current_user().id if current_user() else None
            )
            db.session.add(e)
            db.session.commit()

            # Process optional books if any
            book_ids = [int(x) for x in request.form.getlist('book_ids') if x.isdigit()]
            book_sales_records = []
            books_total = 0.0
            for bid in book_ids:
                b = Book.query.get(bid)
                if b and b.stock_quantity > 0:
                    qty = _int(request.form.get(f'book_qty_{bid}')) or 1
                    qty = min(qty, b.stock_quantity)
                    b_total = b.sale_price * qty
                    b.stock_quantity -= qty
                    bs = BookSale(book_id=b.id, student_id=student_id, quantity=qty, unit_price=b.sale_price, total_price=b_total, payment_method=payment_method, notes="Inclus dans inscription cours particulier", created_by=current_user().id if current_user() else None)
                    db.session.add(bs)
                    book_sales_records.append((b, qty, b_total))
                    books_total += b_total

            grand_invoice_total = charged_price + books_total

            # Invoice
            inv = Invoice(
                number=SH.next_invoice_number('invoice_prefix', 'next_invoice_number'),
                type='facture',
                student_id=student_id,
                enrollment_id=e.id,
                issue_date=enroll_dt,
                due_date=enroll_dt,
                subtotal=grand_invoice_total,
                tva_rate=0.0,
                tva_amount=0.0,
                total=grand_invoice_total,
                status='paid' if initial_payment >= grand_invoice_total else ('partial' if initial_payment > 0 else 'unpaid')
            )
            db.session.add(inv)
            db.session.commit()

            item_course = InvoiceItem(
                invoice_id=inv.id,
                enrollment_id=e.id,
                description=f"⭐ Cours Particulier (1-to-1) — {private_subject} [Pack {int(hours)}h à {hourly_rate:.0f} DH/h]",
                amount=total_price
            )
            db.session.add(item_course)

            if reg_fee > 0:
                item_reg = InvoiceItem(
                    invoice_id=inv.id,
                    enrollment_id=e.id,
                    description=f"Frais d'inscription ({private_subject})",
                    amount=reg_fee
                )
                db.session.add(item_reg)

            for b, qty, b_total in book_sales_records:
                item_b = InvoiceItem(
                    invoice_id=inv.id,
                    description=f"Manuel: {b.title} (x{qty})",
                    amount=b_total
                )
                db.session.add(item_b)

            pay_amt = max(0.0, initial_payment)
            eff_method = 'differe' if pay_amt <= 0 and (not payment_method or payment_method in ('cash', 'none')) else payment_method
            pay_note = "Paiement Inscription Cours Particulier" if pay_amt > 0 else "Inscription Cours Particulier (0 DH / Différé)"
            priv_pay_date = parse_date(d.get('payment_date')) or date.today()
            if priv_pay_date > date.today():
                priv_pay_date = date.today()
            p = record_payment_transaction(
                student_id=student_id,
                amount=pay_amt,
                method=eff_method,
                pay_date=priv_pay_date,
                note=pay_note,
                invoice_id=inv.id,
                enrollments=[e]
            )

            placement_test_id = _int(d.get('placement_test_id'))
            if placement_test_id:
                pt = PlacementTest.query.get(placement_test_id)
                if pt:
                    pt.enrolled_student_id = student_id
                    pt.enrolled_course_id = new_course.id
                    pt.status = 'completed'
                    pt.notes = (pt.notes or '') + f"\nInscrit en Cours Particulier le {datetime.now().strftime('%d/%m/%Y %H:%M')}"

            db.session.commit()
            log_action('express_enrollment_private', f"Student {stu.full_name} registered for private course {new_course.name} ({hours}h - {total_price} DH)")

            if p:
                flash(f"Classe individuelle créée ({new_course.name}) et inscription de {stu.full_name} validée avec succès !", 'success')
                return redirect(url_for('payment_receipt', pid=p.id))

            flash(f"Classe individuelle créée ({new_course.name}) et inscription de {stu.full_name} enregistrée (Solde impayé : {inv.total:.2f} {SH.get_setting('currency', 'DH')})", 'info')
            return redirect(url_for('invoice_view', iid=inv.id))

        if not course_ids and not tariff_ids:
            flash('Veuillez sélectionner au moins une classe ou une matière en attente', 'warning')
            return redirect(url_for('express_enrollment'))

        enroll_dt = parse_date(d.get('enroll_date')) or date.today()
        initial_payment = _f(d.get('initial_payment'))
        payment_method = d.get('payment_method', 'cash')
        notes = d.get('notes')

        created_enrollments = []
        total_calculated_amount = 0.0

        # Collect courses data
        selected_courses_data = []
        for cid_str in course_ids:
            cid = _int(cid_str)
            c = Course.query.get(cid)
            if not c:
                continue
                
            c_enroll_dt = parse_date(d.get(f'course_date_{cid}')) or enroll_dt

            c_months = _int(d.get(f'months_paid_{cid}')) or 1
            tot_sess = _int(d.get(f'total_sessions_{cid}'))
            rem_sess = _int(d.get(f'attended_sessions_{cid}'))
            default_unit = c.unit_monthly_price if hasattr(c, 'unit_monthly_price') else (c.price_per_month or (round(c.price / 3.0, 2) if c.billing_cycle in ('3months', 'trimestriel', '3 mois', 'quarterly') else c.price))
            m_price = _f(d.get(f'monthly_price_{cid}')) or (default_unit * c_months)
            raw_reg_fee = _f(d.get(f'registration_fee_{cid}')) if d.get(f'registration_fee_{cid}') is not None else (c.registration_fee or 0.0)
            c_earned = _f(d.get(f'current_month_earned_{cid}'))
            d_amount = _f(d.get(f'deferred_amount_{cid}'))

            calc = calculate_course_sessions(c.id, c_enroll_dt, months_count=c_months)
            tot_sess = tot_sess or calc['total_sessions']
            rem_sess = rem_sess or calc['remaining_sessions']
            m_price = m_price or calc['full_price']

            if not c_earned:
                c_earned = calc['current_month_earned']
            if not d_amount:
                d_amount = calc['deferred_next_month']

            scheduled_days = set()
            if c.scheduled_days:
                try:
                    scheduled_days = set(int(x.strip()) for x in c.scheduled_days.split(',') if x.strip().isdigit())
                except Exception:
                    scheduled_days = {0, 2, 4}
            else:
                scheduled_days = {0, 2, 4}

            form_end_dt = parse_date(d.get(f'end_date_{cid}'))
            c_end_dt = form_end_dt or calculate_last_session_date(c_enroll_dt, tot_sess, scheduled_days)
            if c_enroll_dt.day == 1 and c_months == 1:
                _, last_day = calendar.monthrange(c_enroll_dt.year, c_enroll_dt.month)
                m_end = date(c_enroll_dt.year, c_enroll_dt.month, last_day)
                if c_end_dt < m_end:
                    c_end_dt = m_end

            selected_courses_data.append({
                'course': c,
                'cid': cid,
                'enroll_dt': c_enroll_dt,
                'months': c_months,
                'tot_sess': tot_sess,
                'rem_sess': rem_sess,
                'end_dt': c_end_dt,
                'm_price': m_price,
                'reg_fee': raw_reg_fee,
                'c_earned': c_earned,
                'd_amount': d_amount
            })

        # Collect pending assignment tariffs (En attente de groupe)
        selected_tariffs_data = []
        for tid_str in tariff_ids:
            tid = _int(tid_str)
            t_obj = Tariff.query.get(tid)
            if not t_obj:
                continue

            t_enroll_dt = parse_date(d.get(f'tariff_date_{tid}')) or enroll_dt
            t_months = _int(d.get(f'tariff_months_paid_{tid}')) or 1
            t_unit = getattr(t_obj, 'price_per_month', None) or (round(t_obj.price / 3.0, 2) if t_obj.billing_cycle in ('3months', 'trimestriel', '3 mois', 'quarterly') else t_obj.price) or 300.0
            t_price = _f(d.get(f'tariff_monthly_price_{tid}')) or (t_unit * t_months)
            raw_t_reg_fee = _f(d.get(f'tariff_registration_fee_{tid}')) if d.get(f'tariff_registration_fee_{tid}') is not None else (t_obj.registration_fee or 100.0)

            spw = t_obj.sessions_per_week if t_obj.sessions_per_week else 3
            t_tot_sess = _int(d.get(f'tariff_total_sessions_{tid}')) or (spw * 4 * t_months)
            t_rem_sess = _int(d.get(f'tariff_attended_sessions_{tid}')) or t_tot_sess

            scheduled_days = {0, 2, 4}
            if spw == 1:
                scheduled_days = {0}
            elif spw == 2:
                scheduled_days = {1, 3}
            elif spw >= 4:
                scheduled_days = {0, 1, 2, 3, 4}
            t_end_dt = calculate_last_session_date(t_enroll_dt, t_tot_sess, scheduled_days)

            selected_tariffs_data.append({
                'tariff': t_obj,
                'tid': tid,
                'enroll_dt': t_enroll_dt,
                'months': t_months,
                'tot_sess': t_tot_sess,
                'rem_sess': t_rem_sess,
                'end_dt': t_end_dt,
                't_price': t_price,
                'reg_fee': raw_t_reg_fee
            })

        # Enforce multi-item registration fee rule: Keep only the single highest fee, zero out all others
        all_selected_items = selected_courses_data + selected_tariffs_data
        if len(all_selected_items) > 1:
            highest_fee = -1.0
            highest_item = None
            for item in all_selected_items:
                if item['reg_fee'] > highest_fee:
                    highest_fee = item['reg_fee']
                    highest_item = item

            for item in all_selected_items:
                if item is not highest_item:
                    item['reg_fee'] = 0.0

        enrollment_items_meta = {}
        for it in selected_courses_data:
            c = it['course']
            reg_fee = it['reg_fee']
            charged_price = it['m_price'] + reg_fee
            dur_txt = f" ({it['months']} mois)" if it.get('months') else ""

            dur_m_c = it.get('months', 1)
            unit_m_price = round(it['m_price'] / dur_m_c, 2) if dur_m_c > 0 else it['m_price']
            e = Enrollment(
                student_id=student_id,
                course_id=c.id,
                enroll_date=it['enroll_dt'],
                payment_plan='monthly' if dur_m_c == 1 else f"{dur_m_c}months",
                status='active',
                total_sessions_month=it['tot_sess'],
                attended_sessions_month=it['rem_sess'],
                monthly_price=unit_m_price,
                calculated_price=charged_price,
                current_month_earned=it['c_earned'],
                deferred_amount=it['d_amount'],
                custom_end_date=it.get('end_dt'),
                notes=f"Inscription Express{dur_txt}. Durée: {dur_m_c} mois. Frais d'inscription: {reg_fee} DH. " + (notes or ''),
                created_by=current_user().id if current_user() else None
            )
            # If student already had an active enrollment in this same course, complete only if expired or starting now
            prev_active = Enrollment.query.filter_by(student_id=student_id, course_id=c.id, status='active').all()
            for pa in prev_active:
                if pa.end_date and pa.end_date >= date.today() and it['enroll_dt'] > date.today():
                    pass  # Keep active during running period; is_attendance_eligible will handle smooth transition
                else:
                    pa.status = 'completed'

            db.session.add(e)
            created_enrollments.append(e)
            enrollment_items_meta[e] = {
                'tuition': it['m_price'],
                'reg_fee': reg_fee,
                'months': dur_m_c
            }
            total_calculated_amount += charged_price

        for it in selected_tariffs_data:
            t_obj = it['tariff']
            t_reg_fee = it['reg_fee']
            t_charged = it['t_price'] + t_reg_fee
            t_months = it['months']
            t_unit_m_price = round(it['t_price'] / t_months, 2) if t_months > 0 else it['t_price']

            prev_active_t = Enrollment.query.filter_by(student_id=student_id, tariff_id=t_obj.id, status='pending_assignment').all()
            for pa in prev_active_t:
                if pa.end_date and pa.end_date >= date.today() and it['enroll_dt'] > date.today():
                    pass
                else:
                    pa.status = 'completed'

            e_pending = Enrollment(
                student_id=student_id,
                course_id=None,
                tariff_id=t_obj.id,
                enroll_date=it['enroll_dt'],
                payment_plan='monthly' if t_months == 1 else f"{t_months}months",
                status='pending_assignment',
                total_sessions_month=it['tot_sess'],
                attended_sessions_month=it['rem_sess'],
                monthly_price=t_unit_m_price,
                calculated_price=t_charged,
                current_month_earned=0.0,
                deferred_amount=0.0,
                custom_end_date=it['end_dt'],
                notes=f"En attente d'affectation au groupe ({t_obj.name}). Durée: {t_months} mois. Frais d'inscription: {t_reg_fee} DH. " + (notes or ''),
                created_by=current_user().id if current_user() else None
            )
            db.session.add(e_pending)
            created_enrollments.append(e_pending)
            enrollment_items_meta[e_pending] = {
                'tuition': it['t_price'],
                'reg_fee': t_reg_fee,
                'months': t_months
            }
            total_calculated_amount += t_charged

        # Process optional selected books / manuals
        book_ids = [int(x) for x in request.form.getlist('book_ids') if x.isdigit()]
        book_sales_records = []
        for bid in book_ids:
            b = Book.query.get(bid)
            if b:
                qty = max(1, _int(request.form.get(f'book_qty_{bid}', 1)))
                b_total = round(b.sale_price * qty, 2)
                total_calculated_amount += b_total
                b.stock_quantity = max(0, (b.stock_quantity or 0) - qty)

                split = b.calculate_split()
                t_earned_total = round(split['teacher_earned'] * qty, 2)
                s_earned_total = round(split['school_earned'] * qty, 2)
                period_m = enroll_dt.strftime('%Y-%m')

                express_pay_dt = parse_date(d.get('payment_date')) or date.today()
                if express_pay_dt > date.today():
                    express_pay_dt = date.today()

                bsale = BookSale(
                    receipt_no=SH.next_invoice_number('receipt_prefix', 'next_receipt_number'),
                    book_id=b.id,
                    student_id=student_id,
                    quantity=qty,
                    unit_price=b.sale_price,
                    total_amount=b_total,
                    payment_method=payment_method,
                    sale_date=express_pay_dt,
                    recorded_by=current_user().id if current_user() else None,
                    notes="Inclus dans l'inscription express",
                    teacher_id=b.teacher_id,
                    teacher_earned=t_earned_total,
                    school_earned=s_earned_total,
                    period_month=period_m
                )
                db.session.add(bsale)
                book_sales_records.append((b, qty, b_total))

        db.session.commit()

        # Create single unified Invoice
        tva_rate = SH.get_float('tva_rate') if SH.is_enabled('enable_tva') else 0
        subtotal = round(total_calculated_amount / (1 + tva_rate / 100), 2) if tva_rate else total_calculated_amount
        tva_amt = round(subtotal * tva_rate / 100, 2)
        express_pay_dt = parse_date(d.get('payment_date')) or date.today()
        if express_pay_dt > date.today():
            express_pay_dt = date.today()

        inv = Invoice(
            number=SH.next_invoice_number('invoice_prefix', 'next_invoice_number'),
            type='facture',
            student_id=student_id,
            enrollment_id=created_enrollments[0].id if created_enrollments else None,
            issue_date=express_pay_dt,
            due_date=max(enroll_dt, date.today()) + timedelta(days=SH.get_int('due_days', 7)),
            subtotal=subtotal,
            tva_rate=tva_rate,
            tva_amount=tva_amt,
            total=total_calculated_amount,
            status='unpaid'
        )
        db.session.add(inv)
        db.session.commit()

        # Add line items to invoice
        for e in created_enrollments:
            meta = enrollment_items_meta.get(e, {})
            tuition_amt = meta.get('tuition', e.monthly_price)
            reg_fee_val = meta.get('reg_fee', max(0.0, (e.calculated_price or 0.0) - tuition_amt))
            dur_m = meta.get('months', 1)
            dur_txt = f" ({dur_m} mois)" if dur_m > 1 else ""

            item_desc = f"{e.course_name_display} (Scolarité{dur_txt})"
            item = InvoiceItem(
                invoice_id=inv.id,
                enrollment_id=e.id,
                description=item_desc,
                amount=tuition_amt
            )
            db.session.add(item)

            if reg_fee_val > 0:
                item_reg = InvoiceItem(
                    invoice_id=inv.id,
                    enrollment_id=e.id,
                    description=f"Frais d'inscription - {e.course_name_display}",
                    amount=reg_fee_val
                )
                db.session.add(item_reg)

        for b, qty, b_total in book_sales_records:
            item_b = InvoiceItem(
                invoice_id=inv.id,
                description=f"Manuel: {b.title} (x{qty})",
                amount=b_total
            )
            db.session.add(item_b)

        # Initial payment transaction record (even if 0 DH différé)
        pay_amt = max(0.0, initial_payment)
        eff_method = 'differe' if pay_amt <= 0 and (not payment_method or payment_method in ('cash', 'none')) else payment_method
        pay_note = "Paiement Inscription Express" if pay_amt > 0 else "Inscription Express (0 DH / Différé)"
        p = record_payment_transaction(
            student_id=student_id,
            amount=pay_amt,
            method=eff_method,
            pay_date=express_pay_dt,
            note=pay_note,
            invoice_id=inv.id,
            enrollments=created_enrollments
        )

        # Link PlacementTest if this express enrollment originated from a placement test
        placement_test_id = _int(d.get('placement_test_id'))
        if placement_test_id:
            pt = PlacementTest.query.get(placement_test_id)
            if pt:
                pt.enrolled_student_id = student_id
                if created_enrollments:
                    pt.enrolled_course_id = created_enrollments[0].course_id
                pt.status = 'completed'
                pt.notes = (pt.notes or '') + f"\nInscrit via Inscription Express le {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        elif d.get('auto_create_placement_test') == '1':
            # Check if any created enrollment is for a language course
            lang_enroll = None
            for e in created_enrollments:
                if e.course and (e.course.category == 'language' or e.course.language in ('Anglais', 'Français', 'Espagnol', 'Allemand', 'Arabe')):
                    lang_enroll = e
                    break
            if lang_enroll and lang_enroll.course:
                import secrets
                pt_token = secrets.token_urlsafe(16)
                new_pt = PlacementTest(
                    token=pt_token,
                    first_name=stu.first_name,
                    last_name=stu.last_name,
                    phone=stu.phone,
                    whatsapp=stu.parent_phone or stu.phone,
                    school_level=stu.school_level,
                    language=lang_enroll.course.language or 'Anglais',
                    status='pending',
                    is_submitted=False,
                    enrolled_student_id=student_id,
                    enrolled_course_id=lang_enroll.course.id,
                    notes=f"Créé automatiquement via Inscription Express ({lang_enroll.course.name}) le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    created_by=current_user().id if current_user() else None
                )
                db.session.add(new_pt)
                flash(f"🎯 Test de niveau automatique généré pour {stu.full_name} ({lang_enroll.course.language}).", "info")

        # Link TeacherStudentRequest if this express enrollment came from a teacher request
        req_id = _int(d.get('teacher_request_id'))
        if req_id:
            t_req = TeacherStudentRequest.query.get(req_id)
            if t_req:
                t_req.status = 'approved'
                t_req.enrolled_student_id = student_id
                t_req.processed_at = datetime.utcnow()
                t_req.processed_by_id = current_user().id if current_user() else None

        db.session.commit()
        log_action('express_enrollment', f"Student {stu.full_name} registered via Express for {len(created_enrollments)} items")

        if p and pay_amt > 0:
            flash(f"Inscription de {stu.full_name} enregistrée avec succès !", 'success')
            return redirect(url_for('payment_receipt', pid=p.id))

        flash(f"Inscription de {stu.full_name} enregistrée avec succès (Solde impayé : {inv.total:.2f} {SH.get_setting('currency', 'DH')})", 'info')
        return redirect(url_for('invoice_view', iid=inv.id))

    test_id = _int(request.args.get('test_id'))
    placement_test = PlacementTest.query.get(test_id) if test_id else None
    req_id = _int(request.args.get('request_id'))
    teacher_request = TeacherStudentRequest.query.get(req_id) if req_id else None

    preselected_course_id = _int(request.args.get('course_id')) or _int(request.args.get('preselect_course'))
    if teacher_request and not preselected_course_id and teacher_request.course_id:
        preselected_course_id = teacher_request.course_id

    prefill_name = (request.args.get('full_name') or (teacher_request.full_name if teacher_request else '')).strip()
    prefill_level = (request.args.get('school_level') or (teacher_request.school_level if teacher_request else '')).strip()
    
    matched_student = None
    if placement_test:
        if placement_test.enrolled_student_id:
            matched_student = Student.query.get(placement_test.enrolled_student_id)
        elif placement_test.phone:
            p_clean = placement_test.phone.strip()
            if p_clean:
                matched_student = Student.query.filter(
                    (Student.phone == p_clean) | (Student.whatsapp == p_clean) | (Student.parent_phone == p_clean)
                ).first()

    active_courses = Course.query.filter_by(active=True).order_by(Course.category, Course.name).all()
    unique_subjects = sorted(list(set(c.language for c in active_courses if c.language)))

    return render_template('enrollments/express.html',
                           students=Student.query.order_by(Student.first_name).all(),
                           courses=active_courses,
                           subjects=unique_subjects,
                           tariffs=Tariff.query.filter_by(active=True).order_by(Tariff.category, Tariff.name).all(),
                           teachers=Teacher.query.filter_by(active=True).order_by(Teacher.first_name, Teacher.last_name).all(),
                           rooms=Room.query.all(),
                           books=Book.query.filter_by(active=True).all(),
                           placement_test=placement_test,
                           teacher_request=teacher_request,
                           prefill_name=prefill_name,
                           prefill_level=prefill_level,
                           matched_student=matched_student,
                           preselected_course_id=preselected_course_id,
                           today=date.today().strftime('%Y-%m-%d'))


@app.route('/enrollments/<int:eid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def enrollment_delete(eid):
    e = Enrollment.query.get_or_404(eid)
    Payment.query.filter_by(enrollment_id=eid).delete()
    
    # Safely clean up invoice items and recalculate or delete parent invoices
    items = InvoiceItem.query.filter_by(enrollment_id=eid).all()
    for item in items:
        inv = item.invoice
        db.session.delete(item)
        if inv:
            db.session.flush()
            rem_items = InvoiceItem.query.filter_by(invoice_id=inv.id).all()
            if rem_items:
                inv.total = sum(i.amount for i in rem_items)
                tva_rate = inv.tva_rate or 0
                inv.subtotal = round(inv.total / (1 + tva_rate / 100), 2) if tva_rate else inv.total
                inv.tva_amount = round(inv.subtotal * tva_rate / 100, 2)
            else:
                db.session.delete(inv)
                
    stu_id = e.student_id
    db.session.delete(e)
    db.session.flush()

    if stu_id:
        remaining_active = Enrollment.query.filter_by(student_id=stu_id, status='active').count()
        if remaining_active == 0:
            orphan_transfers = Enrollment.query.filter_by(student_id=stu_id, status='transferred').all()
            for ot in orphan_transfers:
                ot.status = 'dropped'
                ot.notes = (ot.notes or '') + f"\n[Désinscrit - Inscription transférée #{eid} supprimée le {date.today().strftime('%d/%m/%Y')}]."

    db.session.commit()
    log_action('enrollment_delete', f"Enrollment {eid} deleted")
    flash('Inscription et paiements associés supprimés avec succès', 'success')
    return redirect(url_for('enrollments'))


# ---------------------------------------------------------------------------
# Advanced Operational Actions: Withdraw, Transfer, Pause, Resume, Substitute
# ---------------------------------------------------------------------------
@app.route('/enrollments/<int:eid>/withdraw', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_withdraw(eid):
    e = Enrollment.query.get_or_404(eid)
    stu = e.student
    d = request.form
    action = d.get('action', 'avoir')  # avoir / refund
    refund_amount = _f(d.get('refund_amount')) or 0.0

    e.status = 'dropped'
    e.notes = (e.notes or '') + f"\nDésistement le {date.today()}: Solde calculé {refund_amount} DH ({action})."

    if e.student_id:
        remaining_active = Enrollment.query.filter_by(student_id=e.student_id, status='active').filter(Enrollment.id != e.id).count()
        if remaining_active == 0:
            orphan_transfers = Enrollment.query.filter_by(student_id=e.student_id, status='transferred').all()
            for ot in orphan_transfers:
                ot.status = 'dropped'
                ot.notes = (ot.notes or '') + f"\n[Désistement - L'inscription #{e.id} a été désistée le {date.today().strftime('%d/%m/%Y')}]."

    if action == 'avoir' and refund_amount > 0:
        stu.credit_balance = (stu.credit_balance or 0.0) + refund_amount
        credit = StudentCredit(student_id=stu.id, enrollment_id=e.id, amount=refund_amount, type='avoir', note=f"Avoir suite désistement cours {e.course.display_name if e.course else ''}")
        db.session.add(credit)
        db.session.commit()
        flash(f"Désistement enregistré. Avoir de {refund_amount} DH crédité au solde de l'élève {stu.full_name}.", 'success')
    elif action == 'refund' and refund_amount > 0:
        p = record_payment_transaction(student_id=stu.id, amount=-refund_amount, method='cash', pay_date=date.today(), note=f"Remboursement désistement {e.course.display_name if e.course else ''}", enrollments=[e])
        credit = StudentCredit(student_id=stu.id, enrollment_id=e.id, amount=refund_amount, type='refund', note=f"Remboursement désistement {e.course.display_name if e.course else ''}")
        db.session.add(credit)
        db.session.commit()
        flash(f"Désistement enregistré. Remboursement de {refund_amount} DH effectué.", 'warning')
    else:
        db.session.commit()
        flash("Désistement enregistré avec succès.", 'info')

    return redirect(url_for('enrollments'))


@app.route('/enrollments/<int:eid>/transfer', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_transfer(eid):
    e = Enrollment.query.get_or_404(eid)
    target_cid = _int(request.form.get('target_course_id'))
    target_course = Course.query.get_or_404(target_cid)

    if not target_course.teacher_id:
        flash(f"Impossible de transférer vers '{target_course.display_name}' : aucun enseignant assigné.", 'danger')
        return redirect(url_for('enrollments'))

    transfer_dt = parse_date(request.form.get('transfer_date')) or date.today()
    reason = request.form.get('reason', '').strip()
    notes_reason = f" | Motif: {reason}" if reason else ""

    old_course_name = e.course.display_name if e.course else f"Cours #{e.course_id}"
    new_course_name = target_course.display_name

    # 1. Price Preservation: Keep student's agreed monthly price
    custom_monthly_price = _f(request.form.get('custom_monthly_price'))
    if custom_monthly_price and custom_monthly_price > 0:
        final_monthly_price = custom_monthly_price
    else:
        final_monthly_price = (e.monthly_price if e.monthly_price and e.monthly_price > 0 else (target_course.price or 300.0))

    # Preserve registration fee difference already accounted for
    reg_fee = max(0.0, (e.calculated_price or 0.0) - (e.monthly_price or 0.0))

    # 2. Date Preservation: Keep original subscription cycle dates
    start_dt = parse_date(request.form.get('start_date')) or e.enroll_date or date.today()
    orig_dur = e.duration_months if hasattr(e, 'duration_months') else 1
    max_contractual_end = start_dt + timedelta(days=int(orig_dur * 31) + 5)

    form_end = parse_date(request.form.get('end_date'))
    if form_end and form_end >= transfer_dt and form_end <= max_contractual_end:
        end_dt = form_end
    else:
        end_dt = e.custom_end_date or e.end_date
        if not end_dt or end_dt > max_contractual_end or end_dt <= transfer_dt:
            end_dt = min(max_contractual_end, transfer_dt + timedelta(days=30))

    # 3. Calculate or retrieve teacher prorated shares
    req_old_share = _f(request.form.get('old_teacher_share'))
    req_new_share = _f(request.form.get('new_teacher_share'))

    if req_old_share is not None and req_new_share is not None and (req_old_share + req_new_share > 0):
        old_share = req_old_share
        new_share = req_new_share
    else:
        split_info = calculate_transfer_split(e, target_course, transfer_dt, custom_monthly_price=final_monthly_price, start_date=start_dt, end_date=end_dt)
        old_share = split_info.get('old_share', round(final_monthly_price * 0.5, 2))
        new_share = split_info.get('new_share', round(final_monthly_price - old_share, 2))

    # 4. Mark old enrollment as transferred with its prorated price and end date
    e.status = 'transferred'
    e.custom_end_date = transfer_dt
    if not e.monthly_price or e.monthly_price <= 0:
        e.monthly_price = final_monthly_price
    e.calculated_price = old_share + reg_fee
    e.current_month_earned = old_share
    e.notes = (e.notes or '') + f" | Transféré vers '{new_course_name}' le {transfer_dt.strftime('%d/%m/%Y')} (Part: {old_share:.2f} DH){notes_reason}"

    # Calculate actual sessions for target course within transfer window [transfer_dt, end_dt]
    new_sched = target_course.scheduled_weekdays or {0, 2, 4}
    target_sessions = 0
    cur_d = transfer_dt
    while cur_d <= end_dt:
        if cur_d.weekday() in new_sched:
            target_sessions += 1
        cur_d += timedelta(days=1)
    if target_sessions <= 0:
        spw = target_course.sessions_per_week or 3
        target_sessions = spw * 4

    # 5. Create new enrollment with its prorated price and dates
    new_e = Enrollment(
        student_id=e.student_id,
        course_id=target_course.id,
        enroll_date=transfer_dt,
        custom_end_date=end_dt,
        payment_plan=e.payment_plan,
        status='active',
        total_sessions_month=target_sessions,
        attended_sessions_month=0,
        monthly_price=final_monthly_price,
        calculated_price=new_share,
        current_month_earned=new_share,
        deferred_amount=0.0,
        notes=f"Transféré depuis '{old_course_name}' le {transfer_dt.strftime('%d/%m/%Y')} (Part: {new_share:.2f} DH){notes_reason}",
        created_by=current_user().id if current_user() else None
    )
    db.session.add(new_e)
    db.session.commit()

    # 6. Rebalance payments between old and new enrollment
    prev_payments = Payment.query.filter_by(enrollment_id=e.id).order_by(Payment.id.asc()).all()
    tot_paid = sum(p.amount for p in prev_payments)

    # Old enrollment keeps up to its prorated due (old_share + reg_fee)
    target_keep_on_old = min(tot_paid, old_share + reg_fee)
    target_move_to_new = round(tot_paid - target_keep_on_old, 2)

    if target_move_to_new > 0 and prev_payments:
        rem_to_move = target_move_to_new
        for p in reversed(prev_payments):
            if rem_to_move <= 0:
                break
            if p.amount <= rem_to_move + 0.001:
                p.enrollment_id = new_e.id
                p.note = (p.note or '') + f" [Reporté suite transfert vers {new_course_name}]"
                rem_to_move = round(rem_to_move - p.amount, 2)
            else:
                keep_amt = round(p.amount - rem_to_move, 2)
                move_amt = rem_to_move
                p.amount = keep_amt

                split_pay = Payment(
                    receipt=f"{p.receipt}-TR" if p.receipt else SH.next_invoice_number('receipt_prefix', 'next_receipt_number'),
                    enrollment_id=new_e.id,
                    student_id=e.student_id,
                    amount=move_amt,
                    method=p.method or 'cash',
                    date=p.date or transfer_dt,
                    note=f"Report transfert (Part {new_share:.2f} DH suite transfert cours {old_course_name})",
                    recorded_by=current_user().id if current_user() else p.recorded_by,
                    invoice_id=p.invoice_id
                )
                db.session.add(split_pay)
                rem_to_move = 0.0
                break
        db.session.commit()

    # 7. Update any invoice items linked to old enrollment
    inv_items = InvoiceItem.query.filter_by(enrollment_id=e.id).all()
    for it in inv_items:
        it.amount = old_share + reg_fee
        it.description = f"{old_course_name} (Scolarité au prorata jusqu'au {transfer_dt.strftime('%d/%m')})"
        new_inv_item = InvoiceItem(
            invoice_id=it.invoice_id,
            enrollment_id=new_e.id,
            description=f"{new_course_name} (Scolarité au prorata à partir du {transfer_dt.strftime('%d/%m')})",
            amount=new_share
        )
        db.session.add(new_inv_item)
    db.session.commit()

    # Auto-resolve placement test mismatch if transferred to matching level
    mismatch_tests = PlacementTest.query.filter_by(enrolled_student_id=e.student_id, is_submitted=True, mismatch_dismissed=False).all()
    for pt in mismatch_tests:
        if pt.recommended_level and target_course.level and (pt.recommended_level[:2].upper() == target_course.level[:2].upper()):
            pt.mismatch_dismissed = True
            pt.enrolled_course_id = target_course.id
    db.session.commit()

    stu_name = e.student.full_name if e.student else f"Élève #{e.student_id}"
    log_action('enrollment_transfer', f"Enrollment {e.id} ({old_course_name}) transferred to {new_e.id} ({new_course_name}) for {stu_name} (Part ancienne: {old_share:.2f} DH, Part nouvelle: {new_share:.2f} DH)")
    flash(f"Élève {stu_name} transféré vers '{new_course_name}' avec répartition prorata : {old_share:.2f} DH (Ancien prof) et {new_share:.2f} DH (Nouveau prof) !", 'success')
    return redirect(url_for('enrollments'))


@app.route('/enrollments/<int:eid>/assign_course', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_assign_course(eid):
    e = Enrollment.query.get_or_404(eid)
    target_cid = _int(request.form.get('target_course_id'))
    start_dt = parse_date(request.form.get('start_date')) or date.today()
    target_course = Course.query.get_or_404(target_cid)

    if not target_course.teacher_id:
        flash(f"Impossible d'affecter à la classe '{target_course.display_name}' : aucun enseignant assigné.", 'danger')
        return redirect(request.referrer or url_for('enrollments'))

    e.course_id = target_course.id
    e.enroll_date = start_dt
    e.status = 'active'

    custom_price = _f(request.form.get('custom_monthly_price'))
    if custom_price and custom_price > 0:
        reg_fee = max(0.0, (e.calculated_price or 0.0) - (e.monthly_price or 0.0))
        e.monthly_price = custom_price
        e.calculated_price = custom_price + reg_fee

    dur = e.duration_months if hasattr(e, 'duration_months') else 1
    calc = calculate_course_sessions(target_course.id, start_dt, months_count=dur)
    e.total_sessions_month = calc['total_sessions']
    e.attended_sessions_month = calc['remaining_sessions']
    e.current_month_earned = calc['current_month_earned']
    e.deferred_amount = calc['deferred_next_month']
    sched = target_course.scheduled_weekdays
    new_end = calculate_last_session_date(start_dt, calc['total_sessions'], sched)
    if start_dt.day == 1 and dur == 1:
        _, l_d = calendar.monthrange(start_dt.year, start_dt.month)
        m_end = date(start_dt.year, start_dt.month, l_d)
        if new_end < m_end:
            new_end = m_end
    e.custom_end_date = new_end
    e.notes = (e.notes or '') + f" | Affecté à la classe {target_course.display_name} le {date.today().strftime('%d/%m/%Y')}"

    # Update any associated invoice item descriptions
    inv_items = InvoiceItem.query.filter_by(enrollment_id=e.id).all()
    for item in inv_items:
        if "En attente" in item.description or "(Scolarité)" in item.description:
            item.description = f"{target_course.display_name} (Scolarité)"
            if custom_price and custom_price > 0:
                item.amount = custom_price

    db.session.commit()
    log_action('enrollment_assign', f"Enrollment {e.id} assigned to Course {target_course.display_name}")
    flash(f"Élève {e.student.full_name if e.student else ''} affecté avec succès à la classe '{target_course.display_name}' !", 'success')
    return redirect(request.referrer or url_for('enrollments'))


@app.route('/enrollments/<int:eid>/validate_trial', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_validate_trial(eid):
    e = Enrollment.query.get_or_404(eid)
    if e.status != 'trial':
        flash("Cette inscription n'est pas une séance d'essai.", 'warning')
        return redirect(request.referrer or url_for('enrollments'))

    d = request.form
    official_date = parse_date(d.get('enroll_date')) or date.today()
    months = max(1, _int(d.get('months', 1)))

    # Pricing
    m_price = _f(d.get('monthly_price'))
    if m_price <= 0 and e.course:
        m_price = e.course.price
    reg_fee = _f(d.get('registration_fee'))
    total_charged = m_price + reg_fee
    initial_payment = _f(d.get('initial_payment'))
    pay_method = d.get('payment_method', 'cash')
    user_notes = d.get('notes', '').strip()

    calc = calculate_course_sessions(e.course_id, official_date, months_count=months)
    tot_sess = _int(d.get('total_sessions')) or calc['total_sessions']
    rem_sess = _int(d.get('attended_sessions')) or calc['remaining_sessions']
    c_earned = calc.get('current_month_earned', m_price)
    d_amount = calc.get('deferred_next_month', 0.0)

    scheduled_days = e.scheduled_weekdays or {0, 2, 4}
    c_end_dt = calculate_last_session_date(official_date, tot_sess, scheduled_days)

    # Convert enrollment to active
    e.status = 'active'
    e.enroll_date = official_date
    e.payment_plan = 'monthly'
    e.monthly_price = m_price
    e.calculated_price = total_charged
    e.total_sessions_month = tot_sess
    e.attended_sessions_month = rem_sess
    e.current_month_earned = c_earned
    e.deferred_amount = d_amount
    e.custom_end_date = c_end_dt
    validation_stamp = f"Validé le {date.today().strftime('%d/%m/%Y')} (après essai). Durée: {months} mois. Frais: {reg_fee:.0f} DH."
    if user_notes:
        validation_stamp += f" Remarque: {user_notes}"
    e.notes = f"{e.notes or ''} | {validation_stamp}".strip(' |')

    # Create Invoice
    inv = Invoice(
        number=SH.next_invoice_number('invoice_prefix', 'next_invoice_number'),
        type='facture',
        student_id=e.student_id,
        enrollment_id=e.id,
        issue_date=official_date,
        due_date=official_date + timedelta(days=SH.get_int('due_days', 7)),
        subtotal=total_charged,
        tva_rate=0,
        tva_amount=0,
        total=total_charged,
        status='paid' if initial_payment >= total_charged else ('partial' if initial_payment > 0 else 'unpaid')
    )
    db.session.add(inv)
    db.session.commit()

    # Invoice line items
    item_scol = InvoiceItem(
        invoice_id=inv.id,
        enrollment_id=e.id,
        description=f"{e.course_name_display} (Scolarité - {months} mois)",
        amount=m_price
    )
    db.session.add(item_scol)
    if reg_fee > 0:
        item_reg = InvoiceItem(
            invoice_id=inv.id,
            enrollment_id=e.id,
            description=f"Frais d'inscription - {e.course_name_display}",
            amount=reg_fee
        )
        db.session.add(item_reg)

    p = None
    if initial_payment > 0:
        trial_pay_date = parse_date(request.form.get('payment_date')) or date.today()
        if trial_pay_date > date.today():
            trial_pay_date = date.today()
        p = record_payment_transaction(
            student_id=e.student_id,
            amount=initial_payment,
            method=pay_method,
            pay_date=trial_pay_date,
            note="Paiement validation après séance d'essai",
            invoice_id=inv.id,
            enrollment_id=e.id,
            enrollments=[e]
        )

    db.session.commit()
    log_action('enrollment_validate_trial', f"Trial enrollment #{e.id} validated for student #{e.student_id}")
    flash(f"L'inscription de {e.student.full_name if e.student else ''} a été validée avec succès !", 'success')

    if p:
        return redirect(url_for('payment_receipt', pid=p.id))
    return redirect(url_for('invoice_view', iid=inv.id))


@app.route('/enrollments/<int:eid>/cancel_trial', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_cancel_trial(eid):
    e = Enrollment.query.get_or_404(eid)
    e.status = 'dropped'
    cancel_note = f"Séance d'essai annulée (non poursuivie) le {date.today().strftime('%d/%m/%Y')}"
    e.notes = f"{e.notes or ''} | {cancel_note}".strip(' |')
    db.session.commit()
    log_action('enrollment_cancel_trial', f"Trial enrollment #{e.id} cancelled")
    flash("La séance d'essai a été annulée avec succès.", 'info')
    return redirect(request.referrer or url_for('enrollments', status='trial'))


@app.route('/enrollments/<int:eid>/pause', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_pause(eid):
    e = Enrollment.query.get_or_404(eid)
    e.status = 'paused'
    pause_dt = parse_date(request.form.get('pause_date')) or date.today()
    e.pause_date = pause_dt
    
    custom_rem = request.form.get('remaining_sessions')
    if custom_rem and custom_rem.strip().isdigit():
        rem_sessions = max(0, int(custom_rem.strip()))
    else:
        rem_sessions = e.calculate_remaining_sessions_at(pause_dt)
    
    e.paused_sessions_remaining = rem_sessions
    note = request.form.get('notes', '').strip()
    if note:
        e.notes = f"{e.notes or ''}\n[Pause au {pause_dt.strftime('%d/%m/%Y')} : {note}]".strip()
    
    db.session.commit()
    log_action('enrollment_pause', f"Enrollment {e.id} paused on {pause_dt} with {rem_sessions} sessions saved")
    flash(f"Abonnement de {e.student.full_name if e.student else ''} gelé au {pause_dt.strftime('%d/%m/%Y')} avec {rem_sessions} séance(s) en réserve.", 'warning')
    return redirect(url_for('enrollments'))


@app.route('/enrollments/<int:eid>/resume', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def enrollment_resume(eid):
    e = Enrollment.query.get_or_404(eid)
    resume_dt = parse_date(request.form.get('resume_date')) or date.today()
    
    custom_rem = request.form.get('remaining_sessions')
    if custom_rem and custom_rem.strip().isdigit():
        rem_sessions = max(1, int(custom_rem.strip()))
    else:
        rem_sessions = e.paused_sessions_remaining or e.calculate_remaining_sessions_at(e.pause_date or date.today())
        if rem_sessions <= 0:
            rem_sessions = 1
    
    new_end_date = calculate_last_session_date(resume_dt, rem_sessions, e.scheduled_weekdays)
    
    if e.pause_date:
        paused_days = max(1, (resume_dt - e.pause_date).days)
        e.total_paused_days = (e.total_paused_days or 0) + paused_days
    
    e.custom_end_date = new_end_date
    e.status = 'active'
    e.pause_date = None
    e.paused_sessions_remaining = 0
    
    note = request.form.get('notes', '').strip()
    if note:
        e.notes = f"{e.notes or ''}\n[Reprise au {resume_dt.strftime('%d/%m/%Y')} : {note}]".strip()
    
    db.session.commit()
    new_end_str = new_end_date.strftime('%d/%m/%Y')
    log_action('enrollment_resume', f"Enrollment {e.id} resumed on {resume_dt}. {rem_sessions} sessions mapped to end on {new_end_str}")
    flash(f"Abonnement réactivé le {resume_dt.strftime('%d/%m/%Y')} ! {rem_sessions} séance(s) reportée(s) jusqu'au {new_end_str}.", 'success')
    return redirect(url_for('enrollments'))


@app.route('/api/enrollments/<int:eid>/preview-pause')
@login_required
@role_required('admin', 'secretary')
def api_enrollment_preview_pause(eid):
    e = Enrollment.query.get_or_404(eid)
    p_date = parse_date(request.args.get('pause_date')) or date.today()
    total = e.paid_sessions
    consumed = e.count_consumed_sessions(p_date)
    remaining = max(0, total - consumed)
    days_sched = list(sorted(e.scheduled_weekdays))
    days_labels = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    sched_txt = ", ".join(days_labels[d] for d in days_sched) if days_sched else "Lun, Mer, Ven"
    return jsonify({
        'student_name': e.student.full_name if e.student else '',
        'course_name': e.course.display_name if e.course else '',
        'enroll_date': e.enroll_date.strftime('%d/%m/%Y') if e.enroll_date else '—',
        'pause_date': p_date.strftime('%d/%m/%Y'),
        'total_sessions': total,
        'consumed_sessions': consumed,
        'remaining_sessions': remaining,
        'scheduled_days_text': sched_txt
    })


@app.route('/api/enrollments/<int:eid>/preview-resume')
@login_required
@role_required('admin', 'secretary')
def api_enrollment_preview_resume(eid):
    e = Enrollment.query.get_or_404(eid)
    r_date = parse_date(request.args.get('resume_date')) or date.today()
    rem_s = _int(request.args.get('remaining_sessions'))
    if not rem_s or rem_s <= 0:
        rem_s = e.paused_sessions_remaining or e.calculate_remaining_sessions_at(e.pause_date or date.today())
        if rem_s <= 0:
            rem_s = 1
    
    new_end = calculate_last_session_date(r_date, rem_s, e.scheduled_weekdays)
    days_sched = list(sorted(e.scheduled_weekdays))
    days_labels = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    sched_txt = ", ".join(days_labels[d] for d in days_sched) if days_sched else "Lundi, Mercredi, Vendredi"
    
    return jsonify({
        'student_name': e.student.full_name if e.student else '',
        'course_name': e.course.display_name if e.course else '',
        'pause_date': e.pause_date.strftime('%d/%m/%Y') if e.pause_date else '—',
        'resume_date': r_date.strftime('%d/%m/%Y'),
        'remaining_sessions': rem_s,
        'new_end_date': new_end.strftime('%Y-%m-%d'),
        'new_end_date_formatted': new_end.strftime('%d/%m/%Y'),
        'scheduled_days_text': sched_txt
    })


@app.route('/schedule/substitute', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def schedule_substitute():
    d = request.form
    cid = _int(d.get('course_id'))
    sub_tid = _int(d.get('substitute_teacher_id'))
    sdate = parse_date(d.get('session_date')) or date.today()
    stype = d.get('session_type', 'substitute')
    note = d.get('note')

    course = Course.query.get_or_404(cid)
    sub_log = SubstituteLog(
        course_id=cid,
        original_teacher_id=course.teacher_id,
        substitute_teacher_id=sub_tid,
        session_date=sdate,
        session_type=stype,
        note=note
    )
    db.session.add(sub_log)
    db.session.commit()

    flash("Séance de remplacement / rattrapage enregistrée avec succès.", 'success')
    return redirect(url_for('schedule'))


def record_payment_transaction(student_id, amount, method, pay_date, note, invoice_id=None, enrollments=None, enrollment_id=None, receipt_number=None):
    """Enregistre un paiement en ciblant précisément l'inscription concernée ou en ventilant intelligemment sur les soldes impayés."""
    today_dt = date.today()
    if not pay_date:
        pay_date = today_dt
    elif isinstance(pay_date, datetime):
        pay_date = pay_date.date()
    elif isinstance(pay_date, str):
        pay_date = parse_date(pay_date) or today_dt
    if pay_date > today_dt:
        pay_date = today_dt

    rec_num = receipt_number or SH.next_invoice_number('receipt_prefix', 'next_receipt_number')
    inv = Invoice.query.get(invoice_id) if invoice_id else None

    if enrollment_id and not enrollments:
        target_e = Enrollment.query.get(enrollment_id)
        if target_e:
            enrollments = [target_e]

    if not enrollments:
        if inv and inv.items:
            enrollments = [item.enrollment for item in inv.items if item.enrollment]
        elif student_id:
            all_active = Enrollment.query.filter_by(student_id=student_id, status='active').all()
            unpaid_enrolls = [e for e in all_active if e.balance > 0]
            if unpaid_enrolls:
                enrollments = unpaid_enrolls
            elif all_active:
                enrollments = [all_active[-1]]
            else:
                enrollments = []

    if not invoice_id:
        if enrollments:
            target_eid = enrollments[0].id
            open_inv = Invoice.query.filter_by(enrollment_id=target_eid).filter(Invoice.status != 'paid').first()
            if open_inv:
                invoice_id = open_inv.id
                inv = open_inv
        elif student_id:
            open_inv = Invoice.query.filter_by(student_id=student_id).filter(Invoice.status != 'paid').first()
            if open_inv:
                invoice_id = open_inv.id
                inv = open_inv

    created_payments = []
    if enrollments and len(enrollments) > 0:
        if len(enrollments) == 1:
            p = Payment(
                receipt=rec_num,
                enrollment_id=enrollments[0].id,
                student_id=student_id,
                amount=amount,
                method=method,
                date=pay_date,
                note=note,
                recorded_by=current_user().id if current_user() else None,
                invoice_id=invoice_id
            )
            db.session.add(p)
            created_payments.append(p)
        else:
            total_unpaid = sum(max(0.0, e.balance) for e in enrollments)
            rem_pay = amount

            if total_unpaid > 0:
                for idx, e in enumerate(enrollments):
                    if idx == len(enrollments) - 1:
                        e_amt = rem_pay
                    else:
                        e_bal = max(0.0, e.balance)
                        e_amt = round(amount * (e_bal / total_unpaid), 2)
                        rem_pay -= e_amt

                    p = Payment(
                        receipt=rec_num,
                        enrollment_id=e.id,
                        student_id=student_id,
                        amount=max(0.0, e_amt),
                        method=method,
                        date=pay_date,
                        note=note,
                        recorded_by=current_user().id if current_user() else None,
                        invoice_id=invoice_id
                    )
                    db.session.add(p)
                    created_payments.append(p)
            else:
                total_due = sum(e.due_amount for e in enrollments) or 1.0
                for idx, e in enumerate(enrollments):
                    if idx == len(enrollments) - 1:
                        e_amt = rem_pay
                    else:
                        e_amt = round(amount * (e.due_amount / total_due), 2)
                        rem_pay -= e_amt

                    p = Payment(
                        receipt=rec_num,
                        enrollment_id=e.id,
                        student_id=student_id,
                        amount=max(0.0, e_amt),
                        method=method,
                        date=pay_date,
                        note=note,
                        recorded_by=current_user().id if current_user() else None,
                        invoice_id=invoice_id
                    )
                    db.session.add(p)
                    created_payments.append(p)
    else:
        p = Payment(
            receipt=rec_num,
            student_id=student_id,
            amount=amount,
            method=method,
            date=pay_date,
            note=note,
            recorded_by=current_user().id if current_user() else None,
            invoice_id=invoice_id
        )
        db.session.add(p)
        created_payments.append(p)

    db.session.flush()

    # Dynamically align custom_end_date for touched enrollments with the newly updated paid sessions
    if enrollments:
        for e in enrollments:
            if hasattr(e, 'clear_cache'):
                e.clear_cache()
            if e and e.enroll_date and e.course:
                tot_cycle = e.total_cycle_sessions or 12
                p_sess = e.paid_sessions
                sched = e.scheduled_weekdays
                computed_contractual_end = calculate_last_session_date(e.enroll_date, tot_cycle, sched)
                dur_m = e.duration_months if hasattr(e, 'duration_months') else 1
                if e.enroll_date.day == 1:
                    c_months = dur_m
                    end_m = ((e.enroll_date.month - 1 + c_months - 1) % 12) + 1
                    end_y = e.enroll_date.year + ((e.enroll_date.month - 1 + c_months - 1) // 12)
                    _, last_d = calendar.monthrange(end_y, end_m)
                    m_end = date(end_y, end_m, last_d)
                    if computed_contractual_end < m_end:
                        computed_contractual_end = m_end

                if not e.custom_end_date:
                    e.custom_end_date = computed_contractual_end
                elif dur_m > 1 and e.custom_end_date < computed_contractual_end:
                    e.custom_end_date = computed_contractual_end

    if inv:
        db.session.flush()
        paid = inv.amount_paid
        if paid >= (inv.total or 0.0) and (inv.total or 0.0) > 0:
            inv.status = 'paid'
        elif paid > 0:
            inv.status = 'partial'
        else:
            inv.status = 'unpaid'

    return created_payments[0] if created_payments else None


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------
@app.route('/payments')
@login_required
@role_required('admin', 'secretary')
def payments():
    req_month = request.args.get('month', '')
    req_method = request.args.get('method', '')
    req_user_id = _int(request.args.get('user_id'))
    q = request.args.get('q', '').strip()

    query = Payment.query.join(Student, Payment.student_id == Student.id, isouter=True)

    cur_u = current_user()
    if cur_u and cur_u.role == 'secretary':
        req_user_id = cur_u.id
        query = query.filter(Payment.recorded_by == cur_u.id)
    elif req_user_id:
        query = query.filter(Payment.recorded_by == req_user_id)

    if req_month:
        try:
            y, m = map(int, req_month.split('-'))
            query = query.filter(db.extract('year', Payment.date) == y, db.extract('month', Payment.date) == m)
        except Exception:
            pass

    if req_method:
        query = query.filter(Payment.method == req_method)

    if q:
        q_clean = " ".join(q.split())
        tokens = q_clean.split()
        student_full_1 = db.func.coalesce(Student.first_name, '') + ' ' + db.func.coalesce(Student.last_name, '')
        student_full_2 = db.func.coalesce(Student.last_name, '') + ' ' + db.func.coalesce(Student.first_name, '')
        combined_target = student_full_1 + ' ' + student_full_2 + ' ' + db.func.coalesce(Student.code, '') + ' ' + db.func.coalesce(Payment.receipt, '')
        all_tokens_match = db.and_(*[combined_target.ilike(f"%{t}%") for t in tokens])

        query = query.filter(db.or_(
            all_tokens_match,
            student_full_1.ilike(f"%{q_clean}%"),
            student_full_2.ilike(f"%{q_clean}%"),
            Student.first_name.ilike(f"%{q_clean}%"),
            Student.last_name.ilike(f"%{q_clean}%"),
            Student.code.ilike(f"%{q_clean}%"),
            Payment.receipt.ilike(f"%{q_clean}%")
        ))

    all_payments = query.order_by(Payment.date.desc(), Payment.id.desc()).all()
    if cur_u and cur_u.role == 'secretary':
        staff_users = [cur_u]
    else:
        staff_users = User.query.filter(User.role.in_(['admin', 'secretary'])).order_by(User.full_name).all()

    total_collected_sum = sum(p.amount for p in all_payments)
    today_collected_sum = sum(p.amount for p in all_payments if p.date == date.today())
    cash_collected_sum = sum(p.amount for p in all_payments if p.method == 'cash')
    transfer_card_sum = sum(p.amount for p in all_payments if p.method in ('transfer', 'card', 'online'))

    grouped_payments = group_payments_by_receipt(all_payments)

    cur_lang = lang()
    inst_title = SH.all_settings_dict().get('inst_name', 'ILAS')
    page_title = f"{inst_title} — {'سجل المقبوضات والوصولات' if cur_lang == 'ar' else 'Journal des Paiements & Reçus'}"

    return render_template('payments/list.html',
                           title=page_title,
                           payments=grouped_payments,
                           req_month=req_month,
                           req_method=req_method,
                           req_user_id=req_user_id,
                           staff_users=staff_users,
                           q=q,
                           total_collected_sum=total_collected_sum,
                           today_collected_sum=today_collected_sum,
                           cash_collected_sum=cash_collected_sum,
                           transfer_card_sum=transfer_card_sum)


@app.route('/payments/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def payment_new():
    pre_student_id = _int(request.values.get('student_id'))
    pre_amount = _f(request.values.get('amount'))
    pre_enrollment_id = _int(request.values.get('enrollment_id'))

    if request.method == 'POST':
        d = request.form
        amount = _f(d.get('amount'))
        inv_id = _int(d.get('invoice_id')) or None
        student_id = _int(d.get('student_id'))
        enrollment_id = _int(d.get('enrollment_id')) or pre_enrollment_id
        method = d.get('method', 'cash')
        pdate = parse_date(d.get('date')) or date.today()
        note = d.get('note')

        p = record_payment_transaction(
            student_id=student_id,
            amount=amount,
            method=method,
            pay_date=pdate,
            note=note,
            invoice_id=inv_id,
            enrollment_id=enrollment_id
        )

        db.session.commit()
        log_action('payment', f"receipt {p.receipt if p else ''} {amount}")
        flash('Paiement enregistré avec succès', 'success')
        return redirect(url_for('payment_receipt', pid=p.id if p else 1))

    unpaid_invoices = Invoice.query.filter(Invoice.status != 'paid').order_by(Invoice.issue_date.desc()).all()
    target_enrollment = Enrollment.query.get(pre_enrollment_id) if pre_enrollment_id else None

    return render_template('payments/form.html',
                           students=Student.query.filter_by(status='active').all(),
                           enrolls=Enrollment.query.filter_by(status='active').all(),
                           invoices=unpaid_invoices,
                           pre_student_id=pre_student_id,
                           pre_amount=pre_amount,
                           pre_enrollment_id=pre_enrollment_id,
                           target_enrollment=target_enrollment)


@app.route('/payments/<int:pid>')
@login_required
@role_required('admin', 'secretary')
def payment_receipt(pid):
    p = Payment.query.get_or_404(pid)
    stu = p.student
    inv = p.invoice
    is_duplicata = (request.args.get('duplicata') == '1')
    
    if p.receipt:
        same_receipt_payments = Payment.query.filter_by(receipt=p.receipt).all()
        total_payment_amount = sum(pay.amount for pay in same_receipt_payments)
    else:
        same_receipt_payments = [p]
        total_payment_amount = p.amount

    enrollments = []
    if inv and inv.items:
        for item in inv.items:
            if item.enrollment and item.enrollment not in enrollments:
                enrollments.append(item.enrollment)
    if same_receipt_payments:
        for pay in same_receipt_payments:
            if pay.enrollment and pay.enrollment not in enrollments:
                enrollments.append(pay.enrollment)
    elif p.enrollment and p.enrollment not in enrollments:
        enrollments.append(p.enrollment)
    elif stu:
        enrollments = Enrollment.query.filter_by(student_id=stu.id, status='active').all()

    if inv:
        total_due_amount = inv.total or 0.0
        total_paid_cumulative = inv.amount_paid or 0.0
    elif enrollments:
        total_due_amount = sum((e.calculated_price or e.monthly_price or (e.course.price if e.course else 0.0)) for e in enrollments)
        total_paid_cumulative = sum((e.total_paid or 0.0) for e in enrollments)
    elif stu:
        total_due_amount = sum((e.calculated_price or e.monthly_price or (e.course.price if e.course else 0.0)) for e in Enrollment.query.filter_by(student_id=stu.id, status='active').all())
        total_paid_cumulative = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).filter(Payment.student_id == stu.id).scalar() or 0.0
    else:
        total_due_amount = total_payment_amount
        total_paid_cumulative = total_payment_amount

    raw_mode = (request.args.get('raw') == '1' or request.args.get('autoprint') == '1')
    receipt_design = SH.get_setting('receipt_design', 'default')
    lang = request.args.get('lang', SH.get_setting('default_lang', 'fr'))

    balance_remaining = max(0.0, round(total_due_amount - total_paid_cumulative, 2))

    # Session label
    fr_months = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    ar_months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'ماي', 'يونيو', 'يوليوز', 'غشت', 'شتنبر', 'أكتوبر', 'نونبر', 'دجنبر']
    p_dt = p.date or date.today()
    month_idx = (p_dt.month - 1) % 12
    session_fr = f"{fr_months[month_idx]} {p_dt.year}"
    session_ar = f"{ar_months[month_idx]} {p_dt.year}"
    session_label = session_ar if lang == 'ar' else session_fr

    # Method label
    methods_fr = {'cash': 'Espèces', 'transfer': 'Virement bancaire', 'card': 'Carte bancaire', 'check': 'Chèque', 'cheque': 'Chèque', 'online': 'En ligne', 'differe': 'Différé / Non payé'}
    methods_ar = {'cash': 'نقداً', 'transfer': 'تحويل بنكي', 'card': 'بطاقة بنكية', 'check': 'شيك', 'cheque': 'شيك', 'online': 'عبر الإنترنت', 'differe': 'مؤجل / غير مؤدى'}
    if total_payment_amount <= 0.01 and (not p.method or p.method in ('cash', 'differe')):
        method_label = 'مؤجل / غير مؤدى' if lang == 'ar' else 'Différé / Non payé'
    else:
        method_label = (methods_ar if lang == 'ar' else methods_fr).get(p.method, p.method or ('نقداً' if lang == 'ar' else 'Espèces'))

    # Payment status label
    if balance_remaining <= 0.01:
        status_label = 'خالص' if lang == 'ar' else 'Soldé'
    elif total_payment_amount > 0:
        status_label = 'تسبيق / دفعة' if lang == 'ar' else 'Acompte'
    else:
        status_label = 'غير مؤدى (مؤجل)' if lang == 'ar' else 'Non payé (Différé)'

    cashier_code = '01'
    if p.recorded_by:
        user_rec = User.query.get(p.recorded_by)
        if user_rec and user_rec.username:
            cashier_code = user_rec.username

    # WhatsApp Spintax Receipt Data
    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '')
    raw_parent_phone = (stu.parent_phone or '') if stu else ''
    raw_student_phone = (stu.phone or '') if stu else ''
    clean_parent = _clean_wa_phone(raw_parent_phone)
    clean_student = _clean_wa_phone(raw_student_phone)
    is_adult = bool(stu.is_adult) if stu else False
    default_recip = 'student' if (is_adult or (clean_student and not clean_parent)) else 'parent'

    # Pre-generate Spintax messages
    wa_msg_ar_parent = generate_spintax_payment_receipt(p, recipient_type='parent', lang='ar', inst_name=inst_name, inst_phone=inst_phone)
    wa_msg_fr_parent = generate_spintax_payment_receipt(p, recipient_type='parent', lang='fr', inst_name=inst_name, inst_phone=inst_phone)
    wa_msg_ar_student = generate_spintax_payment_receipt(p, recipient_type='student', lang='ar', inst_name=inst_name, inst_phone=inst_phone)
    wa_msg_fr_student = generate_spintax_payment_receipt(p, recipient_type='student', lang='fr', inst_name=inst_name, inst_phone=inst_phone)

    # Student Timetable Data for optional 80mm ticket printing
    timetable_courses = []
    timetable_course_ids = []
    if enrollments:
        for en in enrollments:
            if en.course and en.course.id not in timetable_course_ids:
                timetable_courses.append(en.course)
                timetable_course_ids.append(en.course.id)
    if not timetable_courses and stu:
        for en in stu.active_enrollments:
            if en.course and en.course.id not in timetable_course_ids:
                timetable_courses.append(en.course)
                timetable_course_ids.append(en.course.id)

    timetable_slots = []
    if timetable_course_ids:
        timetable_slots = ScheduleSlot.query.filter(ScheduleSlot.course_id.in_(timetable_course_ids)).all()
        timetable_slots.sort(key=lambda s: (s.day_of_week, s.start_time or ''))

    timetable_grid = {d: [] for d in range(7)}
    for s in timetable_slots:
        if 0 <= s.day_of_week < 7:
            timetable_grid[s.day_of_week].append(s)

    days_fr = {0: 'Lundi', 1: 'Mardi', 2: 'Mercredi', 3: 'Jeudi', 4: 'Vendredi', 5: 'Samedi', 6: 'Dimanche'}
    days_ar_bilingual = {0: 'الاثنين', 1: 'الثلاثاء', 2: 'الأربعاء', 3: 'الخميس', 4: 'الجمعة', 5: 'السبت', 6: 'الأحد'}
    with_timetable = (request.args.get('with_timetable') == '1')

    template_name = 'payments/receipt_raw.html' if raw_mode else 'payments/receipt.html'
    return render_template(template_name,
                           p=p,
                           stu=stu,
                           inv=inv,
                           enrollments=enrollments,
                           is_duplicata=is_duplicata,
                           raw_mode=raw_mode,
                           total_payment_amount=total_payment_amount,
                           total_paid_cumulative=total_paid_cumulative,
                           total_due_amount=total_due_amount,
                           balance_remaining=balance_remaining,
                           session_label=session_label,
                           method_label=method_label,
                           status_label=status_label,
                           cashier_code=cashier_code,
                           receipt_design=receipt_design,
                           raw_parent_phone=raw_parent_phone,
                           clean_parent_phone=clean_parent,
                           raw_student_phone=raw_student_phone,
                           clean_student_phone=clean_student,
                           default_recip=default_recip,
                           wa_msg_ar_parent=wa_msg_ar_parent,
                           wa_msg_fr_parent=wa_msg_fr_parent,
                           wa_msg_ar_student=wa_msg_ar_student,
                           wa_msg_fr_student=wa_msg_fr_student,
                           timetable_courses=timetable_courses,
                           timetable_grid=timetable_grid,
                           timetable_slots=timetable_slots,
                           days_fr=days_fr,
                           days_ar_bilingual=days_ar_bilingual,
                           with_timetable=with_timetable,
                           lang=lang)


@app.route('/payments/<int:pid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def payment_delete(pid):
    p = Payment.query.get_or_404(pid)
    if p.receipt:
        related = Payment.query.filter_by(receipt=p.receipt).all()
        for r in related:
            db.session.delete(r)
    else:
        db.session.delete(p)
    db.session.commit()
    flash('Paiement supprimé', 'success')
    return redirect(url_for('payments'))


# ---------------------------------------------------------------------------
# WhatsApp Digital Receipt (Anti-Ban Spintax Solution)
# ---------------------------------------------------------------------------
@app.route('/api/payments/<int:pid>/whatsapp_receipt_data')
@login_required
def api_payment_whatsapp_receipt_data(pid):
    p = Payment.query.get_or_404(pid)
    stu = p.student
    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '')

    raw_parent_phone = (stu.parent_phone or '') if stu else ''
    raw_student_phone = (stu.phone or '') if stu else ''
    clean_parent = _clean_wa_phone(raw_parent_phone)
    clean_student = _clean_wa_phone(raw_student_phone)

    is_adult = bool(stu.is_adult) if stu else False
    default_recip = 'student' if (is_adult or (clean_student and not clean_parent)) else 'parent'

    # Pre-generate Spintax messages
    msg_ar_parent = generate_spintax_payment_receipt(p, recipient_type='parent', lang='ar', inst_name=inst_name, inst_phone=inst_phone)
    msg_fr_parent = generate_spintax_payment_receipt(p, recipient_type='parent', lang='fr', inst_name=inst_name, inst_phone=inst_phone)
    msg_ar_student = generate_spintax_payment_receipt(p, recipient_type='student', lang='ar', inst_name=inst_name, inst_phone=inst_phone)
    msg_fr_student = generate_spintax_payment_receipt(p, recipient_type='student', lang='fr', inst_name=inst_name, inst_phone=inst_phone)

    # Resolve dates
    enr = p.enrollment
    if not enr and stu:
        enr = Enrollment.query.filter_by(student_id=stu.id, status='active').order_by(Enrollment.id.desc()).first()

    start_date = enr.enroll_date if enr else (p.date or date.today())
    end_date = enr.end_date if enr else (start_date + timedelta(days=30))

    start_date_str = start_date.strftime('%d/%m/%Y') if hasattr(start_date, 'strftime') else str(start_date)
    end_date_str = end_date.strftime('%d/%m/%Y') if hasattr(end_date, 'strftime') else str(end_date)

    balance = enr.balance_due if enr else 0.0

    return jsonify({
        'success': True,
        'payment_id': p.id,
        'receipt_no': p.receipt or f"REC-{p.id:04d}",
        'student_name': stu.full_name if stu else 'Élève',
        'raw_parent_phone': raw_parent_phone,
        'clean_parent_phone': clean_parent,
        'raw_student_phone': raw_student_phone,
        'clean_student_phone': clean_student,
        'default_recipient': default_recip,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'amount': p.amount or 0.0,
        'balance': balance,
        'messages': {
            'ar_parent': msg_ar_parent,
            'fr_parent': msg_fr_parent,
            'ar_student': msg_ar_student,
            'fr_student': msg_fr_student
        }
    })


@app.route('/payments/<int:pid>/send_whatsapp')
@login_required
def payment_send_whatsapp(pid):
    p = Payment.query.get_or_404(pid)
    stu = p.student
    recip = request.args.get('recipient', 'parent').strip()
    lang = request.args.get('lang', 'ar').strip()
    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '')

    target_phone = (stu.parent_phone if recip == 'parent' else stu.phone) if stu else ''
    clean_p = _clean_wa_phone(target_phone)

    msg = generate_spintax_payment_receipt(p, recipient_type=recip, lang=lang, inst_name=inst_name, inst_phone=inst_phone)
    if clean_p:
        wa_url = f"https://wa.me/{clean_p}?text={quote(msg)}"
        return redirect(wa_url)
    else:
        flash(f"Numéro WhatsApp manquant pour {recip} ({stu.full_name if stu else ''})", "warning")
        return redirect(url_for('payment_receipt', pid=p.id))



# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------
def _create_invoice(enrollment, amount, typ, label, save=True):
    tva = SH.get_float('tva_rate') if SH.is_enabled('enable_tva') else 0
    subtotal = round(amount / (1 + tva / 100), 2) if tva else amount
    tva_amt = round(subtotal * tva / 100, 2)
    inv = Invoice(
        number=SH.next_invoice_number('invoice_prefix', 'next_invoice_number'),
        type=typ, student_id=enrollment.student_id, enrollment_id=enrollment.id,
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=SH.get_int('due_days', 7)),
        subtotal=subtotal, tva_rate=tva, tva_amount=tva_amt, total=amount)
    db.session.add(inv)
    if save:
        db.session.commit()
    return inv


@app.route('/invoices')
@login_required
@role_required('admin', 'secretary')
def invoices():
    return render_template('invoices/list.html',
                           invoices=Invoice.query.order_by(Invoice.issue_date.desc()).all())


@app.route('/invoices/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def invoice_new():
    if request.method == 'POST':
        d = request.form
        e = Enrollment.query.get(_int(d.get('enrollment_id')))
        if not e:
            flash('Choisir une inscription', 'danger')
            return redirect(url_for('invoice_new'))
        amount = _f(d.get('amount')) or (e.course.price if e.course else 0)
        _create_invoice(e, amount, d.get('type', 'facture'), '')
        flash('Facture créée', 'success')
        return redirect(url_for('invoices'))
    return render_template('invoices/form.html',
                           enrolls=Enrollment.query.order_by(Enrollment.id.desc()).all())


@app.route('/invoices/<int:iid>')
@login_required
@role_required('admin', 'secretary')
def invoice_view(iid):
    inv = Invoice.query.get_or_404(iid)
    return render_template('invoices/view.html', inv=inv)


@app.route('/invoices/<int:iid>/print')
@login_required
@role_required('admin', 'secretary')
def invoice_print(iid):
    inv = Invoice.query.get_or_404(iid)
    return render_template('invoices/print.html', inv=inv)


@app.route('/invoices/<int:iid>/status', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def invoice_status(iid):
    inv = Invoice.query.get_or_404(iid)
    inv.status = request.form.get('status', 'unpaid')
    db.session.commit(); flash('Statut mis à jour', 'success')
    return redirect(url_for('invoice_view', iid=iid))


@app.route('/invoices/<int:iid>/pay', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def invoice_pay(iid):
    inv = Invoice.query.get_or_404(iid)
    d = request.form
    pay_amt = _f(d.get('amount')) or (inv.total - inv.amount_paid)
    pay_date = parse_date(d.get('date')) or date.today()
    method = d.get('method', 'cash')
    note = d.get('note')

    p = record_payment_transaction(
        student_id=inv.student_id,
        amount=pay_amt,
        method=method,
        pay_date=pay_date,
        note=note,
        invoice_id=iid
    )

    db.session.commit()
    log_action('invoice_pay', inv.number)
    flash('Paiement enregistré sur la facture', 'success')
    return redirect(url_for('invoice_view', iid=iid))


@app.route('/invoices/<int:iid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def invoice_delete(iid):
    inv = Invoice.query.get_or_404(iid)
    db.session.delete(inv); db.session.commit()
    flash('Facture supprimée', 'success')
    return redirect(url_for('invoices'))


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
DAYS_FR = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
DAYS_AR = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
DAYS = DAYS_FR


@app.route('/schedule')
@login_required
@role_required('admin', 'secretary', 'teacher')
def schedule():
    u = current_user()
    filter_teacher_id = _int(request.args.get('teacher_id'))
    filter_room_id = _int(request.args.get('room_id'))
    filter_level = request.args.get('level', '').strip()
    filter_subject = request.args.get('subject', '').strip()
    filter_group = request.args.get('group', '').strip()
    search_q = request.args.get('q', '').strip()

    query = ScheduleSlot.query.join(Course, ScheduleSlot.course_id == Course.id, isouter=True)

    if u and u.role == 'teacher':
        teacher = Teacher.query.get(u.teacher_id) if u.teacher_id else Teacher.query.filter_by(full_name=u.full_name).first()
        if teacher:
            assigned_cids = set([ct.course_id for ct in CourseTeacher.query.filter_by(teacher_id=teacher.id, is_active=True).all()])
            for c in Course.query.filter_by(teacher_id=teacher.id).all():
                assigned_cids.add(c.id)
            query = query.filter(
                ScheduleSlot.course_id.in_(assigned_cids),
                db.or_(
                    ScheduleSlot.teacher_id == teacher.id,
                    db.and_(ScheduleSlot.teacher_id.is_(None), Course.teacher_id == teacher.id)
                )
            )
        else:
            query = query.filter(ScheduleSlot.id == -1)
    else:
        if filter_teacher_id:
            query = query.filter(
                db.or_(
                    ScheduleSlot.teacher_id == filter_teacher_id,
                    db.and_(ScheduleSlot.teacher_id.is_(None), Course.teacher_id == filter_teacher_id)
                )
            )

    if filter_room_id:
        query = query.filter(Course.room_id == filter_room_id)

    if filter_level:
        query = query.filter(Course.level == filter_level)

    if filter_subject:
        query = query.filter((Course.language == filter_subject) | (Course.name.ilike(f"%{filter_subject}%")))

    if filter_group:
        num_m = re.search(r'\d+', filter_group)
        if num_m:
            num = num_m.group(0)
            query = query.filter(
                (Course.group_name.ilike(f"%groupe {num}%")) |
                (Course.group_name.ilike(f"%groupe{num}%")) |
                (Course.group_name.ilike(f"%g{num}%")) |
                (Course.name.ilike(f"%groupe {num}%")) |
                (Course.name.ilike(f"%groupe{num}%")) |
                (Course.name.ilike(f"%g{num}%"))
            )
        else:
            query = query.filter(
                (Course.group_name.ilike(f"%{filter_group}%")) |
                (Course.name.ilike(f"%{filter_group}%"))
            )

    if search_q:
        query = query.filter(
            (Course.name.ilike(f"%{search_q}%")) |
            (Course.level.ilike(f"%{search_q}%")) |
            (Course.language.ilike(f"%{search_q}%"))
        )

    slots = query.all()

    # Detect conflicts across the active timetable
    all_conflicts, slot_conflicts_map = detect_schedule_conflicts()
    total_conflicts_count = len(all_conflicts)

    # Tag each slot with its specific conflicts
    for s in slots:
        s.conflicts = slot_conflicts_map.get(s.id, [])
        s.has_conflict = len(s.conflicts) > 0

    grid = {d: [] for d in range(7)}
    for s in slots:
        grid[s.day_of_week].append(s)

    # Sort slots by start_time
    for d in range(7):
        grid[d].sort(key=lambda x: x.start_time or '')

    current_lang = session.get('lang', 'fr')
    days_list = DAYS_AR if current_lang == 'ar' else DAYS_FR

    total_slots_count = len(slots)
    active_courses_list = Course.query.filter_by(active=True).order_by(Course.name).all()
    active_courses_count = len(active_courses_list)
    total_teachers = Teacher.query.filter_by(active=True).order_by(Teacher.first_name).all()
    all_rooms = Room.query.order_by(Room.name).all()

    # Extract distinct levels, subjects, groups for filters
    all_levels = sorted(list(set(c.level for c in active_courses_list if c.level)))
    all_subjects = sorted(list(set(c.language for c in active_courses_list if c.language)))
    
    raw_groups = set()
    for c in active_courses_list:
        for t in (c.group_name, c.name):
            if t:
                m = re.search(r'(groupe\s*\d+|g\d+)', t, re.I)
                if m:
                    num = re.search(r'\d+', m.group(1)).group(0)
                    raw_groups.add(f"Groupe {num}")
    all_groups = sorted(list(raw_groups), key=lambda x: int(re.search(r'\d+', x).group(0)) if re.search(r'\d+', x) else 999)
    if not all_groups:
        all_groups = ['Groupe 1', 'Groupe 2', 'Groupe 3', 'Groupe 4']

    active_filters_count = sum(1 for x in [filter_teacher_id, filter_room_id, filter_level, filter_subject, filter_group, search_q] if x)

    return render_template('schedule.html',
                           grid=grid,
                           days=days_list,
                           slots=slots,
                           total_slots_count=total_slots_count,
                           active_courses_count=active_courses_count,
                           courses=active_courses_list,
                           teachers=total_teachers,
                           rooms=all_rooms,
                           all_levels=all_levels,
                           all_subjects=all_subjects,
                           all_groups=all_groups,
                           filter_teacher_id=filter_teacher_id,
                           filter_room_id=filter_room_id,
                           filter_level=filter_level,
                           filter_subject=filter_subject,
                           filter_group=filter_group,
                           search_q=search_q,
                           active_filters_count=active_filters_count,
                           conflicts=all_conflicts,
                           total_conflicts_count=total_conflicts_count)


def detect_schedule_conflicts(slots=None):
    """
    Détecte les chevauchements de créneaux (salles occupées ou enseignants en double séance).
    Deux créneaux sont en conflit si:
      - Même jour de semaine
      - Cours différents
      - Chevauchement horaire : (s1.start_time < s2.end_time) et (s1.end_time > s2.start_time)
      - Et soit même salle, soit même enseignant.
    """
    if slots is None:
        slots = ScheduleSlot.query.join(Course, ScheduleSlot.course_id == Course.id).filter(Course.active == True).all()

    conflicts = []
    slot_conflicts_map = {}
    seen_pairs = set()

    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            s1, s2 = slots[i], slots[j]
            if s1.day_of_week is None or s2.day_of_week is None:
                continue
            if s1.day_of_week != s2.day_of_week:
                continue
            if s1.course_id == s2.course_id:
                continue
            if not (s1.start_time and s1.end_time and s2.start_time and s2.end_time):
                continue
            
            # Chevauchement horaire
            if not (s1.start_time < s2.end_time and s1.end_time > s2.start_time):
                continue

            r1 = s1.course.room_id if s1.course else None
            r2 = s2.course.room_id if s2.course else None
            is_room = bool(r1 and r2 and r1 == r2)

            t1 = s1.effective_teacher
            t2 = s2.effective_teacher
            is_teacher = bool(t1 and t2 and t1.id == t2.id)

            if is_room or is_teacher:
                pair_key = tuple(sorted([s1.id, s2.id]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                overlap_start = max(s1.start_time, s2.start_time)
                overlap_end = min(s1.end_time, s2.end_time)
                day_name = days_fr[s1.day_of_week] if 0 <= s1.day_of_week < 7 else f"Jour {s1.day_of_week}"

                c_info = {
                    's1': s1,
                    's2': s2,
                    'day': s1.day_of_week,
                    'day_name': day_name,
                    'overlap_time': f"{overlap_start} - {overlap_end}",
                    'is_room': is_room,
                    'is_teacher': is_teacher,
                    'room': s1.course.room if is_room else None,
                    'teacher': t1 if is_teacher else None,
                }
                conflicts.append(c_info)
                slot_conflicts_map.setdefault(s1.id, []).append(c_info)
                slot_conflicts_map.setdefault(s2.id, []).append(c_info)

    return conflicts, slot_conflicts_map


@app.route('/courses/check_schedule_conflict', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def check_course_schedule_conflict():
    cid = _int(request.values.get('course_id'))
    room_id = _int(request.values.get('room_id'))
    teacher_id = _int(request.values.get('teacher_id'))
    course_name = (request.values.get('course_name') or '').strip()
    days_param = request.values.get('days', '').strip()
    def_st = (request.values.get('start_time') or '').strip()
    def_et = (request.values.get('end_time') or '').strip()

    # Try parsing slots from name
    slots_to_check = []
    if course_name:
        parsed = parse_schedule_slots_from_text(course_name)
        if parsed:
            for p in parsed:
                slots_to_check.append({
                    'day': p['day'],
                    'start_time': p['start_time'],
                    'end_time': p['end_time']
                })

    # If no slots detected from name, build from days & times
    if not slots_to_check:
        day_nums = []
        if days_param:
            for x in days_param.split(','):
                if x.strip().isdigit():
                    day_nums.append(int(x.strip()))
        st = def_st or '19:00'
        et = def_et or '20:30'
        for d in day_nums:
            slots_to_check.append({
                'day': d,
                'start_time': st,
                'end_time': et
            })

    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    detected = []

    if slots_to_check and (room_id or teacher_id):
        room_obj = Room.query.get(room_id) if room_id else None
        teacher_obj = Teacher.query.get(teacher_id) if teacher_id else None

        for sc in slots_to_check:
            d_val = sc['day']
            st_val = sc['start_time']
            et_val = sc['end_time']
            day_label = days_fr[d_val] if 0 <= d_val < 7 else f"Jour {d_val}"

            existing_slots = ScheduleSlot.query.join(Course, ScheduleSlot.course_id == Course.id).filter(
                ScheduleSlot.day_of_week == d_val,
                Course.active == True
            ).all()

            for es in existing_slots:
                if cid and es.course_id == cid:
                    continue
                if not (es.start_time and es.end_time):
                    continue
                # Overlap check
                if (st_val < es.end_time) and (et_val > es.start_time):
                    # Check Room collision
                    if room_id and es.course and es.course.room_id == room_id:
                        detected.append({
                            'type': 'room',
                            'day_name': day_label,
                            'time': f"{st_val} - {et_val}",
                            'other_time': f"{es.start_time} - {es.end_time}",
                            'room_name': room_obj.name if room_obj else f"Salle #{room_id}",
                            'other_course': es.course.display_name if es.course else "Autre cours",
                            'message': f"🚪 La salle '{room_obj.name if room_obj else room_id}' est déjà occupée le {day_label} ({es.start_time}-{es.end_time}) par : {es.course.display_name if es.course else 'Autre cours'}."
                        })
                    # Check Teacher collision
                    es_teacher = es.effective_teacher
                    if teacher_id and es_teacher and es_teacher.id == teacher_id:
                        detected.append({
                            'type': 'teacher',
                            'day_name': day_label,
                            'time': f"{st_val} - {et_val}",
                            'other_time': f"{es.start_time} - {es.end_time}",
                            'teacher_name': teacher_obj.full_name if teacher_obj else f"Prof #{teacher_id}",
                            'other_course': es.course.display_name if es.course else "Autre cours",
                            'message': f"👨‍🏫 L'enseignant(e) {teacher_obj.full_name if teacher_obj else ''} a déjà cours le {day_label} ({es.start_time}-{es.end_time}) avec : {es.course.display_name if es.course else 'Autre cours'}."
                        })

    return jsonify({
        'has_conflict': len(detected) > 0,
        'count': len(detected),
        'conflicts': detected
    })


@app.route('/schedule/available_rooms')
@login_required
@role_required('admin', 'secretary')
def schedule_available_rooms():
    course_id = _int(request.args.get('course_id'))
    day_of_week = _int(request.args.get('day_of_week'))
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')

    all_rooms = Room.query.all()
    slots_on_day = ScheduleSlot.query.filter_by(day_of_week=day_of_week).all()
    
    occupied_room_map = {}
    for slot in slots_on_day:
        if slot.course_id == course_id:
            continue
        if slot.start_time and slot.end_time and start_time and end_time:
            if (start_time < slot.end_time) and (end_time > slot.start_time):
                c = Course.query.get(slot.course_id)
                if c and c.room_id:
                    occupied_room_map[c.room_id] = c.display_name

    room_list = []
    for r in all_rooms:
        is_occ = r.id in occupied_room_map
        room_list.append({
            'id': r.id,
            'name': r.name,
            'capacity': r.capacity,
            'available': not is_occ,
            'occupied_by': occupied_room_map.get(r.id, '')
        })

    return jsonify({'rooms': room_list})


@app.route('/schedule/assign_room', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def schedule_assign_room():
    course_id = _int(request.form.get('course_id'))
    room_id = _int(request.form.get('room_id'))
    c = Course.query.get_or_404(course_id)
    if room_id:
        r = Room.query.get(room_id)
        c.room_id = room_id
        db.session.commit()
        log_action('assign_room', f"Assigned room {r.name if r else ''} to course {c.display_name}")
        
        # Check if there is a conflict on this newly assigned room
        all_conflicts, slot_map = detect_schedule_conflicts()
        course_conflicts = [conf for conf in all_conflicts if (conf['s1'].course_id == course_id or conf['s2'].course_id == course_id) and conf['is_room']]
        if course_conflicts:
            other_names = set(conf['s2'].course.display_name if conf['s1'].course_id == course_id else conf['s1'].course.display_name for conf in course_conflicts)
            flash(f"⚠️ Salle {r.name if r else ''} assignée avec alerte de conflit : elle est également occupée par ({', '.join(other_names)}).", 'warning')
        else:
            flash(f"تم تعيين القاعة {r.name if r else ''} للفوج بنجاح", 'success')
    else:
        c.room_id = None
        db.session.commit()
        flash("تم إلغاء تعيين القاعة للفوج", 'info')
    return redirect(url_for('schedule'))


@app.route('/schedule/print')
@login_required
@role_required('admin', 'secretary')
def schedule_print():
    fmt = request.args.get('format', 'a4')
    day_str = request.args.get('day', '')
    teacher_id = _int(request.args.get('teacher_id'))
    room_id = _int(request.args.get('room_id'))
    level = request.args.get('level', '').strip()
    subject = request.args.get('subject', '').strip()
    group = request.args.get('group', '').strip()
    search_q = request.args.get('q', '').strip()
    
    selected_day = None
    if day_str == 'today':
        selected_day = date.today().weekday()
    elif day_str != '' and day_str.isdigit():
        selected_day = int(day_str)

    q = ScheduleSlot.query
    if selected_day is not None:
        q = q.filter_by(day_of_week=selected_day)

    slots = q.all()
    if teacher_id:
        assigned_cids = set([ct.course_id for ct in CourseTeacher.query.filter_by(teacher_id=teacher_id, is_active=True).all()])
        for c in Course.query.filter_by(teacher_id=teacher_id).all():
            assigned_cids.add(c.id)
        slots = [s for s in slots if s.course_id in assigned_cids and (
            s.teacher_id == teacher_id or (s.teacher_id is None and s.course and s.course.teacher_id == teacher_id)
        )]
    if room_id:
        slots = [s for s in slots if s.course and s.course.room_id == room_id]
    if level:
        slots = [s for s in slots if s.course and s.course.level == level]
    if subject:
        slots = [s for s in slots if s.course and ((s.course.language and subject.lower() in s.course.language.lower()) or (s.course.name and subject.lower() in s.course.name.lower()))]
    if group:
        num_m = re.search(r'\d+', group)
        target_token = f"groupe {num_m.group(0)}" if num_m else group.lower()
        slots = [s for s in slots if s.course and (
            (s.course.group_name and target_token in s.course.group_name.lower()) or
            (s.course.name and target_token in s.course.name.lower()) or
            (num_m and f"g{num_m.group(0)}" in (s.course.name or '').lower())
        )]
    if search_q:
        q_low = search_q.lower()
        slots = [s for s in slots if s.course and (
            (s.course.name and q_low in s.course.name.lower()) or
            (s.course.level and q_low in s.course.level.lower()) or
            (s.course.language and q_low in s.course.language.lower())
        )]

    slots.sort(key=lambda x: (x.start_time or ''))

    grid = {d: [] for d in range(7)}
    for s in slots:
        grid[s.day_of_week].append(s)

    current_lang = session.get('lang', 'fr')
    days_list = DAYS_AR if current_lang == 'ar' else DAYS_FR
    
    selected_teacher = Teacher.query.get(teacher_id) if teacher_id else None
    selected_room = Room.query.get(room_id) if room_id else None
    selected_day_name = days_list[selected_day] if selected_day is not None else None

    return render_template('schedule/print.html', 
                           grid=grid, 
                           days=days_list, 
                           fmt=fmt,
                           today=date.today(),
                           selected_day=selected_day,
                           selected_day_name=selected_day_name,
                           daily_slots=slots if selected_day is not None else [],
                           selected_teacher=selected_teacher,
                           selected_room=selected_room,
                           selected_level=level,
                           selected_subject=subject,
                           selected_group=group)


# ---------------------------------------------------------------------------
# Schedule WhatsApp Broadcast & Desktop Timetable Image
# ---------------------------------------------------------------------------
@app.route('/schedule/group_whatsapp_data')
@login_required
@role_required('admin', 'secretary')
def schedule_group_whatsapp_data():
    raw_cid = request.args.get('course_id')
    raw_cids = request.args.get('course_ids', '')
    all_flag = request.args.get('all') in ('1', 'true', 'yes')
    
    courses_to_fetch = []
    if all_flag:
        courses_to_fetch = Course.query.filter_by(active=True).order_by(Course.name).all()
    elif raw_cids:
        cids = [int(x.strip()) for x in raw_cids.split(',') if x.strip().isdigit()]
        if cids:
            courses_to_fetch = Course.query.filter(Course.id.in_(cids), Course.active == True).order_by(Course.name).all()
    elif raw_cid and raw_cid.isdigit():
        c = db.session.get(Course, int(raw_cid))
        if c:
            courses_to_fetch = [c]
            
    if not courses_to_fetch:
        return jsonify({'error': 'Aucune classe trouvée'}), 400
    
    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    days_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    
    def clean_phone_num(p):
        if not p:
            return ''
        num = re.sub(r'[^0-9+]', '', str(p))
        if num.startswith('+'):
            num = num[1:]
        if num.startswith('0'):
            num = '212' + num[1:]
        elif (num.startswith('6') or num.startswith('7')) and len(num) == 9:
            num = '212' + num
        return num
        
    courses_dict = {}
    all_students_data = []
    seen_student_course = set()
    
    for course in courses_to_fetch:
        slots_q = ScheduleSlot.query.filter_by(course_id=course.id).order_by(ScheduleSlot.day_of_week, ScheduleSlot.start_time).all()
        slots_data = []
        for s in slots_q:
            d_idx = s.day_of_week if (s.day_of_week is not None and 0 <= s.day_of_week <= 6) else 0
            slots_data.append({
                'day_index': d_idx,
                'day_fr': days_fr[d_idx],
                'day_ar': days_ar[d_idx],
                'start_time': s.start_time or '',
                'end_time': s.end_time or ''
            })
        if not slots_data and course.scheduled_days:
            for d_idx in sorted(list(course.scheduled_weekdays)):
                slots_data.append({
                    'day_index': d_idx,
                    'day_fr': days_fr[d_idx],
                    'day_ar': days_ar[d_idx],
                    'start_time': '19:00',
                    'end_time': '20:30'
                })
                
        # Resolve teacher name: course.teacher -> CourseTeacher active -> 'Non assigné'
        t_name = 'Non assigné'
        if course.teacher:
            t_name = course.teacher.full_name
        else:
            ct = CourseTeacher.query.filter_by(course_id=course.id, is_active=True).first()
            if ct and ct.teacher:
                t_name = ct.teacher.full_name

        c_info = {
            'id': course.id,
            'name': course.name,
            'display_name': course.display_name,
            'group_name': course.group_name or '',
            'level': course.level or '',
            'language': course.language or '',
            'teacher_name': t_name,
            'room_name': course.room.name if course.room else 'Non assignée',
            'sessions_per_week': course.sessions_per_week or len(slots_data),
            'session_duration': course.session_duration or '1h30',
            'slots': slots_data
        }
        courses_dict[course.id] = c_info
        
        today = date.today()
        month_start = date(today.year, today.month, 1)
        _, last_day = calendar.monthrange(today.year, today.month)
        month_end = date(today.year, today.month, last_day)

        enrolls_q = Enrollment.query.filter_by(
            course_id=course.id,
            status='active'
        ).order_by(Enrollment.id.asc()).all()

        current_active_enrolls = []
        for en in enrolls_q:
            st = en.student
            if not st or st.status != 'active':
                continue
            en_start = en.enroll_date or (en.created_at.date() if en.created_at else today)
            en_end = en.end_date or en.custom_end_date
            if en_start > month_end:
                continue
            if en_end and en_end < month_start:
                continue
            current_active_enrolls.append(en)



        for e in current_active_enrolls:
            stu = e.student
            if not stu:
                continue
            clean_name = " ".join((stu.full_name or '').split()).upper()
            key = (stu.id, course.id)
            name_key = (clean_name, course.id)
            if key in seen_student_course or name_key in seen_student_course:
                continue
            seen_student_course.add(key)
            seen_student_course.add(name_key)
            
            clean_parent = clean_phone_num(stu.parent_phone)
            clean_stu = clean_phone_num(stu.whatsapp or stu.phone)
            pref_phone = clean_parent if clean_parent else clean_stu
            
            all_students_data.append({
                'id': stu.id,
                'full_name': stu.full_name,
                'first_name': stu.first_name,
                'last_name': stu.last_name,
                'course_id': course.id,
                'course_name': course.name,
                'phone': stu.phone or '',
                'parent_phone': stu.parent_phone or '',
                'whatsapp': stu.whatsapp or '',
                'clean_parent_phone': clean_parent,
                'clean_student_phone': clean_stu,
                'preferred_phone': pref_phone,
                'has_phone': bool(pref_phone)
            })
            
    all_students_data.sort(key=lambda x: (x['course_name'], x['full_name'].upper()))
    
    first_c = courses_dict[courses_to_fetch[0].id]
    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '06 60 29 11 55')
    inst_address = SH.get_setting('inst_address', 'Lot Nora, N°10, Makhlouf - Deroua')
    
    msg_ar = (
        f"السلام عليكم ورحمة الله،\n"
        f"تجدون رفقته استعمال الزمن الخاص بالتلميذ(ة) *{{nom_eleve}}* في فوج *{{classe}}* لدى {inst_name}.\n"
        f"نتمنى لكم مسيرة موفقة ونجاحاً باهراً.\n"
        f"📍 العنوان: {inst_address}\n"
        f"📞 لأي استفسار أو تواصل: {inst_phone}"
    )
    msg_fr = (
        f"Bonjour,\n"
        f"Veuillez trouver ci-joint l'emploi du temps de l'élève *{{nom_eleve}}* pour la classe *{{classe}}* à {inst_name}.\n"
        f"Nous vous souhaitons une excellente session.\n"
        f"📍 Adresse : {inst_address}\n"
        f"📞 Contact & WhatsApp : {inst_phone}"
    )
    
    return jsonify({
        'course': first_c,
        'slots': first_c['slots'],
        'courses_map': courses_dict,
        'courses_list': list(courses_dict.values()),
        'students': all_students_data,
        'students_count': len(all_students_data),
        'inst_name': inst_name,
        'inst_phone': inst_phone,
        'msg_ar': msg_ar,
        'msg_fr': msg_fr
    })


@app.route('/schedule/save_timetable_image', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def schedule_save_timetable_image():
    data = request.get_json() or {}
    image_b64 = data.get('image_base64', '')
    group_name = data.get('group_name', 'Groupe')
    
    if not image_b64:
        return jsonify({'success': False, 'error': 'Image data manquante'}), 400
        
    try:
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]
        img_bytes = base64.b64decode(image_b64)
        
        clean_name = re.sub(r'[^\w\s-]', '', group_name).strip()
        clean_name = re.sub(r'[-\s]+', '_', clean_name)
        if not clean_name:
            clean_name = 'Groupe'
            
        file_name = f"Emploi_du_Temps_{clean_name}.png"
        
        desktop_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
        if not os.path.exists(desktop_dir):
            onedrive_desktop = os.path.join(os.path.expanduser('~'), 'OneDrive', 'Desktop')
            if os.path.exists(onedrive_desktop):
                desktop_dir = onedrive_desktop
            else:
                os.makedirs(desktop_dir, exist_ok=True)
                
        file_path = os.path.join(desktop_dir, file_name)
        
        with open(file_path, 'wb') as f:
            f.write(img_bytes)
            
        log_action('export_timetable_img', f"Saved timetable image {file_name} to Desktop")
        
        return jsonify({
            'success': True,
            'file_name': file_name,
            'file_path': file_path,
            'message': f"Image enregistrée avec succès sur votre Bureau ({file_name})"
        })
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500


@app.route('/schedule/add', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def schedule_add():
    s = ScheduleSlot(
        course_id=_int(request.form.get('course_id')),
        day_of_week=_int(request.form.get('day_of_week')),
        start_time=request.form.get('start_time'),
        end_time=request.form.get('end_time'))
    db.session.add(s); db.session.commit(); flash('Créneau ajouté', 'success')
    return redirect(url_for('schedule'))


@app.route('/schedule/<int:sid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def schedule_delete(sid):
    s = ScheduleSlot.query.get_or_404(sid)
    db.session.delete(s); db.session.commit(); flash('Créneau supprimé', 'success')
    return redirect(url_for('schedule'))


@app.route('/schedule/auto_sync', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def schedule_auto_sync():
    courses = Course.query.filter_by(active=True).all()
    synced_courses = 0
    total_slots = 0
    for c in courses:
        synced, slots = sync_schedule_from_course_name(c, force_replace=True)
        if synced:
            synced_courses += 1
            total_slots += len(slots)
    if synced_courses > 0:
        flash(f"⚡ Emploi du temps synchronisé avec succès : {synced_courses} classe(s) mises à jour, {total_slots} séance(s) créées dans le planning.", "success")
    else:
        flash("Aucun cours avec horaires détectés dans son nom n'a été trouvé.", "info")
    return redirect(url_for('schedule'))


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
# Attendance & WhatsApp Anti-Ban Parent Notifications
# ---------------------------------------------------------------------------

def _clean_wa_phone(raw_phone):
    """Clean and normalize a phone number into international Moroccan format 212XXXXXXXXX."""
    if not raw_phone:
        return ''
    p = re.sub(r'[^0-9]', '', str(raw_phone))
    if p.startswith('00'):
        p = p[2:]
    elif p.startswith('0'):
        p = '212' + p[1:]
    elif len(p) == 9 and p.startswith(('6', '7')):
        p = '212' + p
    return p


def generate_spintax_absence_message(stu_name, course_name, teacher_name, att_date, status, lang='ar', inst_name=None, inst_phone=None, ref_seed=None):
    """
    Generate a dynamic, anti-ban message for attendance notification using Spintax variations.
    Each generated message has random greeting, body phrasing, closing, and a unique reference hash.
    """
    import random
    if not inst_name:
        inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    if not inst_phone:
        inst_phone = SH.get_setting('inst_phone', '')

    seed = ref_seed if ref_seed is not None else random.randint(1000, 9999)
    date_str = att_date.strftime('%d/%m/%Y') if hasattr(att_date, 'strftime') else str(att_date)

    if lang == 'fr':
        st_fr = "absent(e) 🔴" if status == 'absent' else ("en retard ⚠️" if status == 'late' else "présent(e) 🟢")
        greetings = [
            f"Bonjour, l'administration de {inst_name} vous contacte concernant votre enfant 🏫",
            f"Chers parents, message officiel de l'établissement {inst_name} 🏫",
            f"Bonjour, avis d'absence de la direction pédagogique {inst_name} 🏫",
            f"Chère famille, notification de suivi scolaire {inst_name} 🏫"
        ]
        bodies = [
            f"Nous vous informons que l'élève *{stu_name}* a été marqué(e) [{st_fr}] pour le cours de *{course_name}*{f' (Prof: {teacher_name})' if teacher_name else ''} le {date_str}.",
            f"Une mention [{st_fr}] a été enregistrée pour *{stu_name}* lors de la séance de *{course_name}* ce {date_str}.",
            f"Nous vous signalons l'absence constatée de l'élève *{stu_name}* au cours de *{course_name}* du {date_str}.",
            f"Le pointage du cours de *{course_name}* ({date_str}) indique que *{stu_name}* était [{st_fr}]."
        ]
        closings = [
            f"Merci de bien vouloir justifier cette absence en contactant l'administration au {inst_phone}.",
            f"Pour toute précision ou justificatif, notre secrétariat reste à votre écoute au {inst_phone}.",
            f"Nous vous remercions pour votre suivi attentif. Contact école : {inst_phone}.",
            f"Restant à votre entière disposition pour tout renseignement au {inst_phone}."
        ]
        g = random.choice(greetings)
        b = random.choice(bodies)
        c = random.choice(closings)
        ref_tag = f"[Réf: #AB-{seed}]"
        return f"{g}\n\n{b}\n\n{c}\n{ref_tag}"
    else:
        # Arabic Spintax (Standard for Moroccan parents)
        st_ar = "غائب(ة) 🔴" if status == 'absent' else ("متأخر(ة) ⚠️" if status == 'late' else "حاضر(ة) 🟢")
        greetings = [
            f"السلام عليكم ورحمة الله وبركاته، تحية طيبة من إدارة {inst_name} 🏫",
            f"تحية طيبة وبعد، تتشرف إدارة {inst_name} بالتواصل معكم 🏫",
            f"أهلاً وسهلاً بكم، إخبار رسمي من إدارة مؤسسة {inst_name} 🏫",
            f"السلام عليكم، إشعار تتبّع دراسي من إدارة {inst_name} 🏫"
        ]
        bodies = [
            f"نحيطكم علماً بأنه تم تسجيل حالة [{st_ar}] للتلميذ(ة) *{stu_name}* في حصة مادة *{course_name}*{f' (الأستاذ: {teacher_name})' if teacher_name else ''} بتاريخ {date_str}.",
            f"نود إبلاغكم بتسجيل [{st_ar}] بالنسبة للتلميذ(ة) *{stu_name}* خلال حصة *{course_name}* المنعقدة بتاريخ {date_str}.",
            f"نلفت عنايتكم الكريمة إلى عدم حضور التلميذ(ة) *{stu_name}* لحصة مادة *{course_name}* المبرمجة بتاريخ {date_str}.",
            f"تم رصد غياب التلميذ(ة) *{stu_name}* عن حصة *{course_name}* المقررة بتاريخ {date_str}."
        ]
        closings = [
            f"نرجو منكم تأكيد سبب الغياب والتواصل معنا عند الحاجة عبر الرقم: {inst_phone}.",
            f"شاكرين لكم حسن تتبعكم وحرصكم الدائم على مسار التلميذ. رقم الإدارة: {inst_phone}.",
            f"لأي مبرر أو استفسار، المرجو الاتصال بإدارة المعهد على الرقم: {inst_phone}. دمتم بخير.",
            f"مع متمنياتنا للتلميذ(ة) بكامل التوفيق والنجاح. هاتف الإدارة: {inst_phone}."
        ]
        g = random.choice(greetings)
        b = random.choice(bodies)
        c = random.choice(closings)
        ref_tag = f"[Réf: #AB-{seed}]"
        return f"{g}\n\n{b}\n\n{c}\n{ref_tag}"


def generate_spintax_payment_reminder(stu_name, course_name, end_date, days_remaining, balance=0, due_amount=0, lang='ar', recipient_type='parent', inst_name=None, inst_phone=None, ref_seed=None):
    """
    Generate a dynamic, anti-ban message for payment / monthly tuition renewal notification using Spintax variations.
    High politeness, warm pedagogical partnership tone, with explicit clear mention of monthly payment / fees.
    Supports recipient_type='parent' (default for kids/minors) or recipient_type='adult' (for adult learners).
    Each message has random polite greeting, courteous payment body phrasing, closing,
    and a unique reference hash [Réf: #REN-XXXX].
    """
    import random
    if not inst_name:
        inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    if not inst_phone:
        inst_phone = SH.get_setting('inst_phone', '')

    seed = ref_seed if ref_seed is not None else random.randint(1000, 9999)
    date_str = end_date.strftime('%d/%m/%Y') if hasattr(end_date, 'strftime') else str(end_date)

    # Financial line
    amt = int(balance) if (balance and balance > 0) else (int(due_amount) if (due_amount and due_amount > 0) else 0)
    amt_str_ar = f"💵 واجب الأداء الشهري: *{amt} درهم*" if amt > 0 else ""
    amt_str_fr = f"💵 Montant des frais mensuels : *{amt} DH*" if amt > 0 else ""

    if recipient_type == 'adult':
        # =========================================================================
        # ADULT LEARNER TEMPLATES (Direct, Courteous & Professional)
        # =========================================================================
        if lang == 'fr':
            greetings = [
                f"Bonjour cher(e) apprenant(e) *{stu_name}* 🌸\nL'administration de {inst_name} vous adresse ses salutations les plus cordiales et vous remercie pour votre confiance et votre assiduité dans votre formation.",
                f"Cher(e) étudiant(e) *{stu_name}*, bonjour 🌸\nToute l'équipe pédagogique et administrative de {inst_name} vous transmet ses salutations distinguées et vous félicite pour votre engagement continu dans vos cours.",
                f"Bonjour *{stu_name}* 🌸\nLa direction de {inst_name} espère que votre formation se déroule dans les meilleures conditions et vous remercie chaleureusement pour votre précieuse fidélité.",
                f"Cher(e) apprenant(e), salutations cordiales 🌸\nL'administration de l'établissement {inst_name} a le plaisir de prendre attache avec vous pour le suivi administratif de votre formation."
            ]

            if days_remaining is not None and days_remaining > 1:
                bodies = [
                    f"Nous vous rappelons avec toute la courtoisie requise que l'échéance de votre abonnement mensuel pour le cours de *{course_name}* arrive à son terme le *{date_str}* (dans {days_remaining} jours).\n{amt_str_fr}\nNous vous invitons aimablement à bien vouloir passer au secrétariat pour le *règlement des frais de ce mois*, afin de garantir la continuité de votre formation.",
                    f"Dans le cadre du suivi administratif de nos formations, nous nous permettons de vous rappeler avec bienveillance que le *paiement de votre abonnement mensuel* en *{course_name}* est prévu pour le *{date_str}* (sous {days_remaining} jours).\n{amt_str_fr}\nMerci de bien vouloir vous rapprocher de l'administration pour effectuer votre versement.",
                    f"Afin d'assurer le déroulement serein et ininterrompu de vos séances en *{course_name}*, nous vous informons cordialement que l'échéance de *paiement de vos frais mensuels* approche le *{date_str}* (dans {days_remaining} jours).\n{amt_str_fr}\nNous vous prions de bien vouloir régulariser votre règlement auprès de l'accueil.",
                    f"Nous avons l'honneur de vous informer avec amabilité que votre période mensuelle de formation en *{course_name}* arrive à échéance le *{date_str}*.\n{amt_str_fr}\nNous vous remercions par avance de bien vouloir effectuer le *paiement de votre renouvellement mensuel* à l'administration de l'institut."
                ]
            elif days_remaining == 1:
                bodies = [
                    f"Nous nous permettons de vous rappeler avec amabilité que l'échéance de *paiement de votre abonnement mensuel* pour le cours de *{course_name}* arrive à terme *demain* ({date_str}).\n{amt_str_fr}\nNous vous prions de bien vouloir vous présenter au secrétariat pour renouveler votre inscription et poursuivre vos cours.",
                    f"Avis cordial de renouvellement : votre délai d'abonnement en *{course_name}* prend fin *demain* ({date_str}).\n{amt_str_fr}\nNous vous invitons chaleureusement à passer à l'administration pour le *règlement de votre mensualité*.",
                    f"Nous vous rappelons poliment que le *paiement mensuel* pour votre cours de *{course_name}* est attendu pour *demain* ({date_str}).\n{amt_str_fr}\nMerci pour votre visite à notre bureau pour finaliser la procédure de paiement."
                ]
            elif days_remaining == 0:
                bodies = [
                    f"Nous attirons votre bienveillante attention sur le fait que la date limite de *paiement de votre abonnement mensuel* pour le cours de *{course_name}* est arrivée à terme *aujourd'hui* ({date_str}).\n{amt_str_fr}\nNous vous saurions gré de bien vouloir passer à notre secrétariat aujourd'hui pour effectuer votre versement et régulariser votre situation.",
                    f"Nous vous rappelons avec courtoisie que le terme mensuel de votre formation en *{course_name}* expire *ce jour* ({date_str}).\n{amt_str_fr}\nNous vous remercions de bien vouloir vous présenter à la caisse de l'administration pour régler les frais du nouveau mois.",
                    f"C'est aujourd'hui ({date_str}) que s'achève votre période mensuelle en *{course_name}*.\n{amt_str_fr}\nAfin de maintenir votre présence régulière, nous vous prions d'effectuer le *règlement de votre cotisation mensuelle* auprès de l'accueil."
                ]
            else:
                past_d = abs(days_remaining) if days_remaining is not None else 1
                bodies = [
                    f"Nous tenons à vous informer poliment et en toute confiance que votre abonnement pour le cours de *{course_name}* est arrivé à échéance depuis le *{date_str}* (il y a {past_d} jour{'s' if past_d > 1 else ''}).\n{amt_str_fr}\nNous vous prions d'avoir l'amabilité de passer à l'administration dans les plus brefs délais pour régler vos *frais de renouvellement* et assurer la poursuite de votre formation.",
                    f"Dans un esprit d'écoute et de bienveillance, nous vous signalons que le *paiement mensuel* de votre formation en *{course_name}* est en attente de régularisation depuis le *{date_str}*.\n{amt_str_fr}\nMerci de bien vouloir vous présenter à notre bureau pour procéder au règlement.",
                    f"Nous vous adressons ce rappel courtois concernant le *règlement de votre abonnement mensuel* échu en *{course_name}* depuis le *{date_str}*.\n{amt_str_fr}\nNous comptons sur votre diligence habituelle pour honorer vos frais auprès de la direction."
                ]

            closings = [
                f"Notre secrétariat reste à votre entière disposition et à votre écoute pour toute facilité au {inst_phone}.\nAvec nos salutations les plus respectueuses et nos souhaits de plein succès dans votre parcours.",
                f"Nous vous remercions vivement pour votre compréhension et votre ponctualité.\nPour tout échange, notre équipe est joignable au {inst_phone}.",
                f"Très honorés de vous accompagner dans votre apprentissage et à votre service au {inst_phone}.\nBien cordialement, la Direction Pédagogique et Administrative.",
                f"Nous vous réitérons toute notre estime et nos remerciements pour votre aimable coopération. Contact accueil : {inst_phone}."
            ]
        else:
            # Arabic Adult Spintax
            greetings = [
                f"السلام عليكم ورحمة الله تعالى وبركاته 🌸\nأخي الكريم / أختي الكريمة *{stu_name}*، تتشرف إدارة مؤسسة {inst_name} بالتواصل معكم، ونود أن نعرب لكم عن خالص شكرنا وتقديرنا الكبير لثقتكم واختياركم لمعهدنا لمتابعة مساركم التكويني.",
                f"تحية طيبة ملؤها التقدير والاحترام 🌸\nعزيزي(تي) المتعلم(ة) *{stu_name}*، أسرة معهد {inst_name} تحييكم أطيب تحية، ويسعدنا دوماً التواصل معكم تقديراً لالتزامكم وجديتكم في حضور الحصص والتكوين.",
                f"السلام عليكم ورحمة الله وبركاته 🌸\nالمتعلم(ة) الكريم(ة) *{stu_name}*، نرجو أن يجدكم هذا الإشعار في أتم الصحة والعافية، شاكرين لكم طيب تعاونكم والتزامكم الإيجابي مع إدارة {inst_name}.",
                f"تحية احترام وتقدير من إدارة مؤسسة {inst_name} 🌸\nإلى المتدرب(ة) الفاضل(ة) *{stu_name}*، يسرنا أن نتوجه إليكم بأصدق عبارات الشكر والامتنان على حرصكم المستمر على تطوير مهاراتكم معنا."
            ]

            if days_remaining is not None and days_remaining > 1:
                bodies = [
                    f"نود تذكيركم بكل لطف وعناية باقتراب موعد *أداء واجب الاشتراك الشهري* الخاص بكم في دورة *{course_name}*، والمحدد تاريخ استحقاقه في *{date_str}* (متبقي {days_remaining} أيام).\n{amt_str_ar}\nوحرصاً منا ومنكم على ضمان مقعدكم واستمرار استفادتكم من التكوين في أفضل الظروف، نرجو منكم التفضل بزيارة إدارة المعهد لأداء واجب التجديد.",
                    f"نلفت عنايتكم الكريمة بكل احترام إلى أن فترة الاشتراك الشهري الخاصة بكم في دورة *{course_name}* تشرف على نهايتها بحلول تاريخ *{date_str}* (بعد {days_remaining} أيام).\n{amt_str_ar}\nشاكرين لكم التكرم بالمرور على مكتب الاستقبال لتسوية *واجب الأداء الشهري* ومواصلة التكوين دون انقطاع.",
                    f"تذكيراً ودياً وأخوياً من الإدارة بأن موعد *تجديد أداء الاشتراك الشهري* الخاص بكم في *{course_name}* يحل بتاريخ *{date_str}* (تحت {days_remaining} أيام).\n{amt_str_ar}\nيرجى التفضل بموافاة الإدارة لتسوية واجب الشهر الجديد لضمان الحفاظ على المقعد والاستفادة المستمرة."
                ]
            elif days_remaining == 1:
                bodies = [
                    f"نحيطكم علماً بكل مودة وتقدير بأن موعد *أداء واجب الاشتراك الشهري* الخاص بكم في دورة *{course_name}* يحل *يوم غد* ({date_str}).\n{amt_str_ar}\nنرجو منكم التفضل بزيارة إدارة المعهد لتسديد واجب التجديد لضمان استمرارية الحصص بسلاسة وانتظام.",
                    f"نود تذكيركم بكل احترام بأن اشتراككم في حصص *{course_name}* ينتهي أجله *غداً* ({date_str}).\n{amt_str_ar}\nحرصاً على السير العادي لحصصكم، نرجو منكم التكرم بأداء *مستحقات الشهر الجديد* لدى كتابة المعهد.",
                    f"تذكيراً لطيفاً بأن غداً ({date_str}) هو آخر أجل في اشتراككم الحالي لمادة *{course_name}*.\n{amt_str_ar}\nنلتمس منكم التفضل بإتمام *إجراءات أداء الواجب الشهري* بالإدارة الكريمة."
                ]
            elif days_remaining == 0:
                bodies = [
                    f"نلفت انتباهكم الكريم بكل احترام إلى أن موعد *أداء واجب الاشتراك الشهري* لدورة *{course_name}* يحل *اليوم* ({date_str}).\n{amt_str_ar}\nنرجو منكم مشكورين التفضل بزيارة إدارة المعهد هذا اليوم لتسديد واجب التجديد الشهري ومتابعة التكوين في أحسن الظروف.",
                    f"نود إخباركم بلطف بأن فترة اشتراككم الحالية في *{course_name}* تنتهي *اليوم* ({date_str}).\n{amt_str_ar}\nشاكرين لكم التفضل بالمرور على شباك الإدارة لتسوية *واجب الأداء للشهر الموالي*.",
                    f"يحل اليوم ({date_str}) موعد تجديد *أداء واجب التكوين الشهري* الخاص بكم في دورة *{course_name}*.\n{amt_str_ar}\nنرحب بكم في مكتب الإدارة لتسوية المستحقات ومتابعة مساركم التعليمي بكل نجاح."
                ]
            else:
                past_d = abs(days_remaining) if days_remaining is not None else 1
                bodies = [
                    f"نلفت عنايتكم الكريمة بكل تقدير وأخوة إلى أن فترة اشتراككم الشهري في دورة *{course_name}* كانت قد انتهت بتاريخ *{date_str}* (منذ {past_d} أيام).\n{amt_str_ar}\nنلتمس منكم بكل لطف التفضل بالحضور إلى إدارة المعهد لتسوية *واجب الاشتراك المتأخر* وضمان استمراركم في حضور الحصص دون أي إحراج أو توقف.",
                    f"في إطار التواصل الودي والمستمر معكم، نذكركم بأن *أداء واجب التكوين الشهري* لدورة *{course_name}* بلغ نهاية أجله في *{date_str}*.\n{amt_str_ar}\nنرجو منكم التكرم بزيارة الإدارة لتسوية وضعية الأداء حرصاً على متابعة التحصيل.",
                    f"نرفع إلى كريم علمكم بكل مودة أن اشتراككم في دورة *{course_name}* منتهي الصلاحية منذ تاريخ *{date_str}*.\n{amt_str_ar}\nشاكرين لكم عنايتكم وحرصكم الدائم، نرجو منكم تسوية *واجب الاشتراك* لدى إدارة المؤسسة في أقرب وقت."
                ]

            closings = [
                f"شاكرين لكم حسن تفهمكم، ونبل تعاونكم، وثقتكم الغالية التي نعتز بها دوماً.\nفريق الإدارة رهن إشارتكم لكل استفسار أو تسهيلات عبر الهاتف: {inst_phone}.\nدمتم في حفظ الله ورعايته، مع متمنياتنا لكم بكامل التألق والنجاح في مساركم 🌟",
                f"نشكركم جزيل الشكر على سرعة تجاوبكم واهتمامكم المتواصل.\nلأي استفسار إضافي، يسعدنا تواصلكم معنا عبر الرقم: {inst_phone}.\nمع أصدق متمنياتنا لكم بمستقبل مشرق ونجاح مستمر 🌟",
                f"تقبلوا منا أسمى عبارات المودة والتقدير والاحترام.\nرقم التواصل المباشر مع إدارة المعهد: {inst_phone}.\nوفقكم الله وسدد خطاكم في مسيرتكم التعليمية والمهنية 🌟",
                f"سائلين العلي القدير لكم التوفيق والسداد في مساركم التكويني.\nللتواصل والاستعلام: {inst_phone}. دمتم سالمين 🌟"
            ]

    else:
        # =========================================================================
        # PARENT TEMPLATES (Addressed to Parents of Student)
        # =========================================================================
        if lang == 'fr':
            greetings = [
                f"Bonjour chers parents 🌸\nL'administration de {inst_name} vous adresse ses salutations les plus cordiales et vous remercie chaleureusement pour votre confiance et votre suivi régulier de la scolarité de votre enfant.",
                f"Chers parents d'élèves, bonjour 🌸\nToute l'équipe pédagogique et administrative de {inst_name} vous transmet ses salutations distinguées et vous exprime sa gratitude pour votre précieuse collaboration.",
                f"Bonjour à toute la famille 🌸\nLa direction de {inst_name} espère que vous vous portez à merveille et tient à saluer votre engagement exemplaire aux côtés de votre enfant.",
                f"Chers parents, salutations respectueuses 🌸\nL'administration de l'établissement {inst_name} a le plaisir de prendre attache avec vous pour le suivi éducatif et administratif de votre enfant."
            ]

            if days_remaining is not None and days_remaining > 1:
                bodies = [
                    f"Nous vous rappelons avec toute la courtoisie requise que le terme de l'abonnement mensuel pour l'élève *{stu_name}* dans le cours de *{course_name}* arrive à son échéance le *{date_str}* (dans {days_remaining} jours).\n{amt_str_fr}\nNous vous invitons aimablement à bien vouloir passer à notre secrétariat pour le *règlement des frais de ce mois*, afin de garantir la continuité pédagogique et préserver la place de votre enfant.",
                    f"Dans le cadre de la gestion administrative de nos cours, nous nous permettons de vous rappeler avec bienveillance que le *paiement des frais d'inscription mensuelle* de *{stu_name}* pour le cours de *{course_name}* est prévu pour le *{date_str}* (sous {days_remaining} jours).\n{amt_str_fr}\nMerci de bien vouloir vous rapprocher de l'administration pour effectuer le versement dans les meilleurs délais.",
                    f"Afin d'assurer le déroulement serein et ininterrompu des séances de l'élève *{stu_name}* en *{course_name}*, nous vous informons cordialement que l'échéance de *paiement de l'abonnement mensuel* approche le *{date_str}* (dans {days_remaining} jours).\n{amt_str_fr}\nNous vous prions de bien vouloir régulariser le règlement auprès du secrétariat.",
                    f"Nous avons l'honneur de vous informer avec amabilité que la période mensuelle pour *{stu_name}* en *{course_name}* arrive à échéance le *{date_str}*.\n{amt_str_fr}\nNous vous remercions par avance de bien vouloir effectuer le *paiement du renouvellement mensuel* à l'administration de l'institut."
                ]
            elif days_remaining == 1:
                bodies = [
                    f"Nous nous permettons de vous rappeler avec amabilité que l'échéance de *paiement des frais de scolarité mensuels* de l'élève *{stu_name}* pour le cours de *{course_name}* arrive à terme *demain* ({date_str}).\n{amt_str_fr}\nNous vous prions de bien vouloir vous présenter au secrétariat pour renouveler l'abonnement et maintenir l'accès aux cours.",
                    f"Avis cordial de renouvellement : le délai d'abonnement pour *{stu_name}* en *{course_name}* prend fin *demain* ({date_str}).\n{amt_str_fr}\nNous vous invitons chaleureusement à passer à l'administration pour effectuer le *règlement de la mensualité* et valider la réinscription.",
                    f"Nous vous rappelons poliment que le *paiement mensuel* pour le cours de *{course_name}* suivi par *{stu_name}* est attendu pour *demain* ({date_str}).\n{amt_str_fr}\nMerci pour votre visite à notre bureau pour finaliser la procédure de paiement."
                ]
            elif days_remaining == 0:
                bodies = [
                    f"Nous attirons votre bienveillante attention sur le fait que la date limite de *paiement de l'abonnement mensuel* pour l'élève *{stu_name}* ({course_name}) est arrivée à terme *aujourd'hui* ({date_str}).\n{amt_str_fr}\nNous vous saurions gré de bien vouloir passer à notre secrétariat aujourd'hui pour effectuer le versement et régulariser la situation.",
                    f"Nous vous rappelons avec déférence que le terme mensuel pour le cours de *{course_name}* suivi par *{stu_name}* expire *ce jour* ({date_str}).\n{amt_str_fr}\nNous vous remercions de bien vouloir vous présenter à la caisse de l'administration pour régler les frais du nouveau mois.",
                    f"C'est aujourd'hui ({date_str}) que s'achève la période mensuelle pour *{stu_name}* en *{course_name}*.\n{amt_str_fr}\nAfin de maintenir la présence régulière de votre enfant, nous vous prions d'effectuer le *règlement de la cotisation mensuelle* auprès de l'accueil."
                ]
            else:
                past_d = abs(days_remaining) if days_remaining is not None else 1
                bodies = [
                    f"Nous tenons à vous informer poliment et en toute confiance que l'abonnement de l'élève *{stu_name}* pour le cours de *{course_name}* est arrivé à échéance depuis le *{date_str}* (il y a {past_d} jour{'s' if past_d > 1 else ''}).\n{amt_str_fr}\nNous vous prions d'avoir l'amabilité de passer à l'administration dans les plus brefs délais pour régler les *frais de renouvellement* et assurer la poursuite des cours.",
                    f"Dans un esprit d'écoute et de partenariat, nous vous signalons avec bienveillance que le *paiement mensuel* de *{stu_name}* en *{course_name}* est en attente de régularisation depuis le *{date_str}*.\n{amt_str_fr}\nMerci de bien vouloir vous présenter à notre bureau pour procéder au règlement.",
                    f"Nous vous adressons ce rappel courtois concernant le *règlement de l'abonnement mensuel* échu de *{stu_name}* ({course_name}) depuis le *{date_str}*.\n{amt_str_fr}\nNous comptons sur votre diligence habituelle pour honorer les frais auprès de la direction."
                ]

            closings = [
                f"Notre secrétariat reste à votre entière disposition et à votre écoute pour toute facilité au {inst_phone}.\nAvec nos salutations les plus respectueuses et nos souhaits de plein épanouissement pour votre enfant.",
                f"Nous vous remercions infiniment pour votre compréhension, votre ponctualité et votre confiance renouvelée.\nPour tout échange, notre équipe est joignable au {inst_phone}.",
                f"Restant très honorés de contribuer à la réussite de votre enfant et à votre service au {inst_phone}.\nBien cordialement, la Direction Pédagogique et Administrative.",
                f"Nous vous réitérons toute notre estime et nos remerciements pour votre aimable coopération. Contact accueil : {inst_phone}."
            ]
        else:
            # Arabic Parent Spintax
            greetings = [
                f"السلام عليكم ورحمة الله تعالى وبركاته 🌸\nأولياء الأمور الكرام، تتشرف إدارة مؤسسة {inst_name} بالتواصل معكم، ونود أن نعرب لكم عن خالص شكرنا وتقديرنا الكبير لثقتكم الغالية وحرصكم الدائم على تتبع المسار الدراسي لأبنائكم.",
                f"تحية طيبة ملؤها التقدير والاحترام 🌸\nأسرة معهد {inst_name} تحييكم أطيب تحية، ويسعدنا دوماً التواصل معكم تقديراً لحرصكم المستمر واهتمامكم البالغ بالتحصيل العلمي المتميز لفلذات أكبادكم.",
                f"السلام عليكم ورحمة الله وبركاته 🌸\nإلى الآباء والأمهات الكرام، نرجو أن يجدكم هذا الإشعار وأنتم وأسرتكم في أتم الصحة والعافية، شاكرين لكم طيب تعاونكم الدائم مع إدارة {inst_name}.",
                f"تحية احترام وتقدير من إدارة مؤسسة {inst_name} 🌸\nيسرنا أن نتوجه إليكم بأصدق عبارات الشكر والامتنان على شراكتكم البناءة ومواكبتكم المستمرة لمسيرة التلميذ(ة) الدراسية."
            ]

            if days_remaining is not None and days_remaining > 1:
                bodies = [
                    f"نود تذكيركم بكل لطف وعناية باقتراب موعد *أداء واجب الاشتراك الشهري* الخاص بالتلميذ(ة) *{stu_name}* في حصص مادة *{course_name}*، والمحدد تاريخ استحقاقه في *{date_str}* (متبقي {days_remaining} أيام).\n{amt_str_ar}\nوحرصاً منا ومنكم على ضمان مقعد التلميذ واستمرار استفادته من الحصص والبرنامج الدراسي في أفضل الظروف، نرجو منكم التفضل بزيارة إدارة المعهد لأداء واجب التجديد.",
                    f"نلفت عنايتكم الكريمة بكل احترام إلى أن فترة الاشتراك الحالية للتلميذ(ة) *{stu_name}* في مادة *{course_name}* تشرف على نهايتها بحلول تاريخ *{date_str}* (بعد {days_remaining} أيام).\n{amt_str_ar}\nشاكرين لكم التكرم بالمرور على مكتب الاستقبال لتسوية *واجب الأداء الشهري* ومواصلة التمدرس دون انقطاع.",
                    f"تذكيراً ودياً وأخوياً من الإدارة بأن موعد *تجديد أداء الاشتراك الشهري* للتلميذ(ة) *{stu_name}* في *{course_name}* يحل بتاريخ *{date_str}* (تحت {days_remaining} أيام).\n{amt_str_ar}\nيرجى التفضل بموافاة الإدارة لتسوية واجب الشهر الجديد لضمان الحفاظ على المقعد والاستفادة البيداغوجية المستمرة."
                ]
            elif days_remaining == 1:
                bodies = [
                    f"نحيطكم علماً بكل مودة وتقدير بأن موعد *أداء واجب الاشتراك الشهري* للتلميذ(ة) *{stu_name}* في مادة *{course_name}* يحل *يوم غد* ({date_str}).\n{amt_str_ar}\nنرجو منكم التفضل بزيارة إدارة المعهد لتسديد واجب التجديد لضمان استمرارية الحصص بسلاسة وانتظام.",
                    f"نود تذكيركم بكل احترام بأن اشتراك التلميذ(ة) *{stu_name}* في حصص *{course_name}* ينتهي أجله *غداً* ({date_str}).\n{amt_str_ar}\nحرصاً على السير العادي لحصص التلميذ، نرجو منكم التكرم بأداء *مستحقات الشهر الجديد* لدى كتابة المعهد.",
                    f"تذكيراً لطيفاً بأن غداً ({date_str}) هو آخر أجل في الاشتراك الحالي للتلميذ(ة) *{stu_name}* لمادة *{course_name}*.\n{amt_str_ar}\nنلتمس منكم التفضل بإتمام *إجراءات أداء الواجب الشهري* بالإدارة الكريمة."
                ]
            elif days_remaining == 0:
                bodies = [
                    f"نلفت انتباهكم الكريم بكل احترام إلى أن موعد *أداء واجب الاشتراك الشهري* للتلميذ(ة) *{stu_name}* لمادة *{course_name}* يحل *اليوم* ({date_str}).\n{amt_str_ar}\nنرجو منكم مشكورين التفضل بزيارة إدارة المعهد هذا اليوم لتسديد واجب التجديد الشهري وضمان متابعة الحصص في أحسن الظروف.",
                    f"نود إخباركم بلطف بأن فترة الاشتراك الحالي للتلميذ(ة) *{stu_name}* في *{course_name}* تنتهي *اليوم* ({date_str}).\n{amt_str_ar}\nشاكرين لكم التفضل بالمرور على شباك الإدارة لتسوية *واجب الأداء للشهر الموالي*.",
                    f"يحل اليوم ({date_str}) موعد تجديد *أداء واجب التمدرس الشهري* للتلميذ(ة) *{stu_name}* في مادة *{course_name}*.\n{amt_str_ar}\nنرحب بكم في مكتب الإدارة لتسوية المستحقات ومتابعة المسار التعليمي بكل نجاح."
                ]
            else:
                past_d = abs(days_remaining) if days_remaining is not None else 1
                bodies = [
                    f"نلفت عنايتكم الكريمة بكل تقدير وأخوة إلى أن فترة الاشتراك الشهري للتلميذ(ة) *{stu_name}* في مادة *{course_name}* كانت قد انتهت بتاريخ *{date_str}* (منذ {past_d} أيام).\n{amt_str_ar}\nنلتمس منكم بكل لطف التفضل بالحضور إلى إدارة المعهد لتسوية *واجب الاشتراك المتأخر* وضمان استمرار التلميذ في حضور حصصه دون أي إحراج أو توقف.",
                    f"في إطار التواصل الودي والمستمر مع أسرتكم المحترمة، نذكركم بأن *أداء واجب التمدرس الشهري* للتلميذ(ة) *{stu_name}* في *{course_name}* بلغ نهاية أجله في *{date_str}*.\n{amt_str_ar}\nنرجو منكم التكرم بزيارة الإدارة لتسوية وضعية الأداء حرصاً على التحصيل الدراسي للتلميذ.",
                    f"نرفع إلى كريم علمكم بكل مودة أن اشتراك التلميذ(ة) *{stu_name}* لمادة *{course_name}* منتهي الصلاحية منذ تاريخ *{date_str}*.\n{amt_str_ar}\nشاكرين لكم عنايتكم وحرصكم الدائم، نرجو منكم تسوية *واجب الاشتراك* لدى إدارة المؤسسة في أقرب وقت."
                ]

            closings = [
                f"شاكرين لكم حسن تفهمكم، ونبل تعاونكم، وثقتكم الغالية التي نعتز بها دوماً.\nفريق الإدارة رهن إشارتكم لكل استفسار أو تسهيلات عبر الهاتف: {inst_phone}.\nدمتم في حفظ الله ورعايته، مع متمنياتنا للتلميذ(ة) بكامل التألق والنجاح 🌟",
                f"نشكركم جزيل الشكر على سرعة تجاوبكم واهتمامكم المتواصل.\nلأي استفسار إضافي، يسعدنا تواصلكم معنا عبر الرقم: {inst_phone}.\nمع أصدق متمنياتنا لأبنائكم بمستقبل مشرق وزاهر 🌟",
                f"تقبلوا منا أسمى عبارات المودة والتقدير والاحترام.\nرقم التواصل المباشر مع إدارة المعهد: {inst_phone}.\nوفق الله أبناءنا وبناتنا جميعاً لما فيه الخير والنجاح 🌟",
                f"سائلين العلي القدير للتلميذ(ة) التوفيق والسداد في مساره الدراسي.\nللتواصل والاستعلام: {inst_phone}. دمتم سالمين 🌟"
            ]

    g = random.choice(greetings)
    b = random.choice(bodies)
    c = random.choice(closings)
    ref_tag = f"[Réf: #REN-{seed}]"
    return f"{g}\n\n{b}\n\n{c}\n{ref_tag}"



def generate_spintax_payment_receipt(payment, recipient_type='parent', lang='ar', inst_name=None, inst_phone=None, ref_seed=None):
    """
    Generate an attractive, dynamic, anti-ban WhatsApp receipt message using Spintax variations.
    Includes:
      - N° Reçu
      - Student Full Name
      - Course Name
      - Montant Réglé (Amount in DH)
      - Date Début (start_date)
      - Date Fin / Échéance (end_date)
      - Solde Restant / Situation Financière
      - Mode de paiement
      - Date du Paiement
    Supports recipient_type='parent' or recipient_type='student'.
    Languages: lang='ar' or lang='fr'.
    Anti-Ban Engine: randomized polite greetings, body phrasing, and unique [Réf: #REC-XXXX] hash.
    """
    import random
    if not inst_name:
        inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    if not inst_phone:
        inst_phone = SH.get_setting('inst_phone', '')

    seed = ref_seed if ref_seed is not None else random.randint(1000, 9999)
    p_id = payment.id
    receipt_no = payment.receipt or f"REC-{p_id:04d}"

    stu = payment.student
    stu_name = stu.full_name if stu else "Élève"

    # Resolve Enrollment & Course & Dates
    enr = payment.enrollment
    if not enr and stu:
        enr = Enrollment.query.filter_by(student_id=stu.id, status='active').order_by(Enrollment.id.desc()).first()

    course_name = ""
    if payment.courses_description:
        course_name = payment.courses_description
    elif enr and enr.course:
        course_name = enr.course.display_name
    elif enr:
        course_name = enr.course_name_display
    else:
        course_name = "Formation Générale"

    # Dates
    start_date = None
    end_date = None
    if enr:
        start_date = enr.enroll_date or (enr.created_at.date() if enr.created_at else payment.date)
        end_date = enr.end_date
    if not start_date:
        start_date = payment.date or date.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)

    start_date_str = start_date.strftime('%d/%m/%Y') if hasattr(start_date, 'strftime') else str(start_date)
    end_date_str = end_date.strftime('%d/%m/%Y') if hasattr(end_date, 'strftime') else str(end_date)
    pay_date_str = payment.date.strftime('%d/%m/%Y') if (payment.date and hasattr(payment.date, 'strftime')) else date.today().strftime('%d/%m/%Y')

    amount = payment.amount or 0.0

    # Remaining balance
    balance = 0.0
    if enr:
        balance = enr.balance_due or 0.0
    elif payment.invoice:
        balance = max(0.0, (payment.invoice.total or 0.0) - (payment.invoice.amount_paid or 0.0))

    # Payment method translation
    methods_fr = {'cash': 'Espèces', 'transfer': 'Virement bancaire', 'card': 'Carte bancaire', 'check': 'Chèque', 'cheque': 'Chèque', 'online': 'En ligne', 'differe': 'Différé / Non payé'}
    methods_ar = {'cash': 'نقداً', 'transfer': 'تحويل بنكي', 'card': 'بطاقة بنكية', 'check': 'شيك', 'cheque': 'شيك', 'online': 'عبر الإنترنت', 'differe': 'مؤجل / غير مؤدى'}
    if amount <= 0.01 and (not payment.method or payment.method in ('cash', 'differe')):
        method_fr = 'Différé / Non payé'
        method_ar = 'مؤجل / غير مؤدى'
    else:
        method_fr = methods_fr.get(payment.method, payment.method or 'Espèces')
        method_ar = methods_ar.get(payment.method, payment.method or 'نقداً')

    # Status / Balance lines
    if balance <= 0.01:
        balance_line_ar = "▫️ *الوضعية المالية :* ✅ *خالص بالكامل (Soldé)*"
        balance_line_fr = "▫️ *Situation Financière :* ✅ *Soldé en Totalité*"
    else:
        balance_line_ar = f"▫️ *المبلغ المتبقي :* ⏳ *{balance:.0f} درهم*"
        balance_line_fr = f"▫️ *Solde Restant Dû :* ⏳ *{balance:.0f} DH*"

    if recipient_type == 'parent':
        if lang == 'fr':
            greetings = [
                f"Bonjour chers parents de l'élève *{stu_name}* 🌸,\nL'administration de *{inst_name}* vous adresse ses salutations les plus cordiales.",
                f"Chers parents d'élèves, bonjour 🌸,\nToute l'équipe administrative de *{inst_name}* vous remercie pour votre confiance et votre engagement.",
                f"Bonjour à toute la famille 🌸,\nLa direction de *{inst_name}* a le plaisir de prendre attache avec vous pour le suivi de la scolarité de votre enfant.",
                f"Chère famille de *{stu_name}*, salutations distinguées 🌸,\nNous vous transmettons ce message officiel suite au règlement effectué auprès de notre accueil."
            ]
            intros = [
                "Nous avons le plaisir de vous confirmer la bonne réception de votre paiement et vous délivrons votre reçu numérique officiel :",
                "Nous vous confirmons l'enregistrement de votre versement dans notre système académique. Voici les détails de votre reçu :",
                "Votre règlement a été validé avec succès à l'administration de l'institut. Retrouvez ci-dessous le décompte de votre reçu :",
                "Faisant suite à votre passage à l'accueil, voici le reçu de paiement attestant de votre inscription :"
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧾 *REÇU DE PAIEMENT NUMÉRIQUE*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"▫️ *N° Reçu :* #{receipt_no}\n"
                f"▫️ *Élève :* *{stu_name}*\n"
                f"▫️ *Cours / Groupe :* *{course_name}*\n"
                f"▫️ *Montant Réglé :* *{amount:.0f} DH* ({method_fr})\n"
                f"▫️ *Date Début :* 🗓️ *{start_date_str}*\n"
                f"▫️ *Date Échéance / Fin :* 🗓️ *{end_date_str}*\n"
                f"{balance_line_fr}\n"
                f"▫️ *Date de Paiement :* {pay_date_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            closings = [
                f"Nous vous remercions chaleureusement pour votre confiance et votre ponctualité.\nPour toute question, le secrétariat est joignable au : {inst_phone}.",
                f"Toute l'équipe pédagogique souhaite plein succès à notre cher(e) élève dans ses études 🌟\nContact école : {inst_phone}.",
                f"Nous restons à votre entière disposition pour tout renseignement au {inst_phone}.\nAvec nos salutations les plus respectueuses.",
                f"Merci pour votre confiance renouvelée envers notre établissement. L'accueil est à votre écoute au : {inst_phone}."
            ]
        else:
            # Arabic Parent
            greetings = [
                f"السلام عليكم ورحمة الله تعالى وبركاته 🌸\nتحية تقدير واحترام لولي أمر التلميذ(ة) *{stu_name}*،",
                f"تحية طيبة ملؤها الود والاحترام 🌸\nإلى ولي أمر التلميذ(ة) النجيب(ة) *{stu_name}*،",
                f"السلام عليكم ورحمة الله وبركاته 🌸\nأولياء أمور التلميذ(ة) *{stu_name}* الأفاضل، أسرة {inst_name} تحييكم أطيب تحية،",
                f"تحية تربوية وتقديرية من إدارة {inst_name} 🌸\nإلى ولي أمر المتعلم(ة) *{stu_name}*،"
            ]
            intros = [
                f"يسر إدارة {inst_name} أن تؤكد لكم استلام واجب الأداء بنجاح، وتجدون أسفله تفاصيل وصل الأداء الرسمي المسجل في نظامنا :",
                f"تأكيداً لعملية الأداء التي تمت بمكتب الاستقبال، نرسل لحضرتكم التوصيل الرسمي المؤكد لعملية الدفع :",
                f"نخبركم بتسجيل دفعتكم المالية بنجاح في السجل المحاسباتي للمعهد، وإليكم بيانات وصل الأداء الرقمي المعتمد :",
                f"نوافيكم ببيانات وصل الأداء الإلكتروني الرسمي الخاص باشتراك التلميذ(ة) : "
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧾 *إيصـال أداء رقمـي معتمـد*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"▫️ *رقم الوصل :* #{receipt_no}\n"
                f"▫️ *اسم التلميذ(ة) :* *{stu_name}*\n"
                f"▫️ *المادة / الفوج :* *{course_name}*\n"
                f"▫️ *المبلغ المؤدى :* *{amount:.0f} درهم* ({method_ar})\n"
                f"▫️ *تاريخ بداية الحصص :* 🗓️ *{start_date_str}*\n"
                f"▫️ *نهاية فترة الاشتراك :* 🗓️ *{end_date_str}*\n"
                f"{balance_line_ar}\n"
                f"▫️ *تاريخ الأداء :* {pay_date_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            closings = [
                f"نشكركم جزيل الشكر على ثقتكم الغالية في مؤسستنا، ونتمنى لابنكم/ابنتكم كامل التوفيق والتألق الدراسي 🌟\nلأي استفسار، كتابة المعهد رهن إشارتكم عبر الرقم : {inst_phone}",
                f"شاكرين لكم حسن تعاونكم والتزامكم الدائم، ونسأل الله التوفيق والنجاح لمسار تلميذنا العزيز 🌟\nمكتب الاستقبال في خدمتكم دوماً : {inst_phone}",
                f"نقدر عالياً حرصكم ومتابعتكم المستمرة، ونتطلع دوماً لتقديم أفضل تأطير تربوي 🌟\nللتواصل والاستعلام : {inst_phone}",
                f"خالص متمنياتنا لمسار دراسي مكلل بالتفوق والتميز بإذن الله 🌟\nهاتف إدارة المعهد : {inst_phone}"
            ]
    else:
        # recipient_type == 'student'
        if lang == 'fr':
            greetings = [
                f"Bonjour cher(e) apprenant(e) *{stu_name}* 🌸,\nL'administration de *{inst_name}* vous adresse ses cordiales salutations.",
                f"Cher(e) étudiant(e) *{stu_name}*, bonjour 🌸,\nToute l'équipe de *{inst_name}* vous remercie pour votre assiduité et votre confiance.",
                f"Bonjour *{stu_name}* 🌸,\nNous vous transmettons ce message officiel attestant de la régularisation de votre cotisation.",
                f"Salutations cordiales *{stu_name}* 🌸,\nL'administration de l'institut a le plaisir de vous transmettre votre reçu officiel."
            ]
            intros = [
                "Nous vous confirmons la bonne réception de votre paiement et vous délivrons votre reçu officiel :",
                "Votre versement a été enregistré avec succès dans notre système. Voici les détails de votre reçu :",
                "Votre inscription a été validée avec succès. Retrouvez ci-dessous les détails de votre reçu numérique :",
                "Voici l'attestation de paiement électronique officielle relative à votre formation :"
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧾 *REÇU DE PAIEMENT NUMÉRIQUE*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"▫️ *N° Reçu :* #{receipt_no}\n"
                f"▫️ *Apprenant(e) :* *{stu_name}*\n"
                f"▫️ *Cours / Niveau :* *{course_name}*\n"
                f"▫️ *Montant Réglé :* *{amount:.0f} DH* ({method_fr})\n"
                f"▫️ *Date Début :* 🗓️ *{start_date_str}*\n"
                f"▫️ *Date Échéance / Fin :* 🗓️ *{end_date_str}*\n"
                f"{balance_line_fr}\n"
                f"▫️ *Date du Paiement :* {pay_date_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            closings = [
                f"Nous vous souhaitons plein succès et une excellente progression dans votre formation 🚀\nPour toute question, l'équipe est à votre service au : {inst_phone}.",
                f"Merci pour votre confiance continue et votre ponctualité 🚀\nSecrétariat de l'institut : {inst_phone}.",
                f"Bonne continuation dans vos séances. L'administration reste à votre disposition au {inst_phone}.",
                f"Avec nos vœux de pleine réussite dans votre parcours d'apprentissage 🚀\nContact : {inst_phone}."
            ]
        else:
            # Arabic Student
            greetings = [
                f"السلام عليكم ورحمة الله وبركاته 🌸\nأخي الكريم / أختي الكريمة *{stu_name}*،",
                f"تحية طيبة ملؤها التقدير والاحترام 🌸\nعزيزي(تي) المتعلم(ة) *{stu_name}*،",
                f"السلام عليكم ورحمة الله تعالى وبركاته 🌸\nالمتدرب(ة) الفاضل(ة) *{stu_name}*، إدارة {inst_name} تحييكم أطيب تحية،",
                f"تحية احترام وتشجيع من أسرة {inst_name} 🌸\nإلى الطالب(ة) المجتهد(ة) *{stu_name}*،"
            ]
            intros = [
                f"يسر إدارة {inst_name} تأكيد استلام واجب الأداء الخاص بتكوينكم، وتجدون رفقته وصل الأداء الرسمي المعتمد :",
                f"نؤكد لكم تسجيل دفعتكم المالية بنجاح في السجل الأكاديمي، وإليكم تفاصيل الوصل الرقمي :",
                f"تم بنجاح تفعيل وتأكيد اشتراككم، وتجدون أدناه بيانات التوصيل المالي الرسمي :",
                f"نوافيكم بوصل الأداء الإلكتروني المعتمد الخاص بدورتكم التكوينية : "
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧾 *إيصـال أداء رقمـي معتمـد*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"▫️ *رقم الوصل :* #{receipt_no}\n"
                f"▫️ *المستفيد(ة) :* *{stu_name}*\n"
                f"▫️ *الدورة / الفوج :* *{course_name}*\n"
                f"▫️ *المبلغ المؤدى :* *{amount:.0f} درهم* ({method_ar})\n"
                f"▫️ *تاريخ بداية الحصص :* 🗓️ *{start_date_str}*\n"
                f"▫️ *نهاية فترة الاشتراك :* 🗓️ *{end_date_str}*\n"
                f"{balance_line_ar}\n"
                f"▫️ *تاريخ الأداء :* {pay_date_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            closings = [
                f"نتمنى لكم مساراً تكوينياً موفقاً ومكللاً بأعلى مراتب النجاح والتفوق 🚀\nكتابة المعهد رهن إشارتكم لأي مساعدة : {inst_phone}",
                f"نشكركم على اختياركم لمعهدنا وحرصكم على تطوير مهاراتكم 🚀\nلأي استفسار : {inst_phone}",
                f"بالتوفيق والنجاح الدائم في حصصكم وتكوينكم معنا 🚀\nتواصلوا معنا عبر : {inst_phone}",
                f"وفقكم الله في مساركم التعليمي ودمتم متميزين 🚀\nرقم إدارة المؤسسة : {inst_phone}"
            ]

    g = random.choice(greetings)
    intro = random.choice(intros)
    c = random.choice(closings)
    ref_tag = f"[Réf: #REC-{seed}]"
    return f"{g}\n\n{intro}\n\n{card}\n\n{c}\n{ref_tag}"




def get_course_group_label(c):
    raw = (c.group_name or c.name or '')
    grp_match = re.search(r'(GROUPE\s*\d+|GRP\s*\d+|G\d+)', raw, re.IGNORECASE)
    if grp_match:
        return grp_match.group(1).upper()
    if c.group_name and len(c.group_name.strip()) < 25:
        return c.group_name.strip()
    return 'Groupe 1'

def get_course_schedule_label(c, teacher_id=None):
    days_map = {0:'Lun', 1:'Mar', 2:'Mer', 3:'Jeu', 4:'Ven', 5:'Sam', 6:'Dim'}
    slots_q = ScheduleSlot.query.join(Course, ScheduleSlot.course_id == Course.id, isouter=True).filter(ScheduleSlot.course_id == c.id)
    if teacher_id:
        slots_q = slots_q.filter(
            db.or_(
                ScheduleSlot.teacher_id == teacher_id,
                db.and_(ScheduleSlot.teacher_id.is_(None), Course.teacher_id == teacher_id)
            )
        )
    slots = slots_q.order_by(ScheduleSlot.day_of_week, ScheduleSlot.start_time).all()
    if slots:
        day_nums = sorted(list(set(s.day_of_week for s in slots if s.day_of_week in days_map)))
        days_str = ' · '.join(days_map[d_num] for d_num in day_nums)
        time_str = f"{slots[0].start_time} - {slots[0].end_time}" if slots[0].start_time else ''
        return f"{days_str} ({time_str})" if time_str else days_str
    days_list = [int(x) for x in (c.scheduled_days or '').split(',') if x.strip().isdigit()]
    days_str = ' · '.join(days_map[d_num] for d_num in sorted(days_list) if d_num in days_map)
    return days_str or 'Horaires réguliers'

def find_nearest_course_for_attendance(courses, target_date=None, target_hm=None, teacher_id=None):
    if not courses:
        return None
    if not target_date:
        target_date = date.today()
    if not target_hm:
        target_hm = datetime.now().strftime('%H:%M')
    target_weekday = target_date.weekday()
    try:
        now_h, now_m = map(int, target_hm.split(':'))
        now_mins = now_h * 60 + now_m
    except Exception:
        now_mins = 19 * 60

    scored = []
    for c in courses:
        slots_q = ScheduleSlot.query.join(Course, ScheduleSlot.course_id == Course.id, isouter=True).filter(ScheduleSlot.course_id == c.id)
        if teacher_id:
            slots_q = slots_q.filter(
                db.or_(
                    ScheduleSlot.teacher_id == teacher_id,
                    db.and_(ScheduleSlot.teacher_id.is_(None), Course.teacher_id == teacher_id)
                )
            )
        slots = slots_q.all()
        slot_tuples = []
        if slots:
            for s in slots:
                if s.day_of_week is not None and s.start_time:
                    try:
                        sh, sm = map(int, s.start_time.split(':'))
                        eh, em = map(int, s.end_time.split(':')) if s.end_time else (sh + 1, sm + 30)
                        slot_tuples.append((s.day_of_week, sh * 60 + sm, eh * 60 + em, s.start_time))
                    except Exception:
                        pass
        if not slot_tuples and not teacher_id:
            days_list = [int(x) for x in (c.scheduled_days or '').split(',') if x.strip().isdigit()]
            for d in days_list:
                slot_tuples.append((d, 19 * 60, 20 * 60 + 30, '19:00'))

        if not slot_tuples:
            scored.append(((99, 99999), c))
            continue

        best_slot_score = (999, 99999)
        for (day, s_min, e_min, st_str) in slot_tuples:
            day_diff = (day - target_weekday) % 7
            if day_diff == 0:
                if s_min - 20 <= now_mins <= e_min + 30:
                    slot_score = (0, abs(now_mins - s_min))
                elif now_mins < s_min - 20:
                    slot_score = (1, s_min - now_mins)
                else:
                    slot_score = (2, now_mins - e_min)
            else:
                slot_score = (3 + day_diff, day_diff * 1440 + s_min)

            if slot_score < best_slot_score:
                best_slot_score = slot_score

        scored.append((best_slot_score, c))

    scored.sort(key=lambda x: (x[0][0], x[0][1]))
    return scored[0][1] if scored else courses[0]


@app.route('/attendance')
@login_required
def attendance():
    cid = _int(request.args.get('course_id'))
    att_date = request.args.get('date') or str(date.today())
    d = parse_date(att_date) or date.today()
    
    u = current_user()
    current_teacher = None
    if u and u.role == 'teacher':
        current_teacher = get_current_teacher()
        if current_teacher:
            t_cids = get_teacher_course_ids(current_teacher.id)
            courses = Course.query.filter(Course.id.in_(t_cids), Course.active == True).all() if t_cids else []
        else:
            courses = []
    else:
        courses = Course.query.filter_by(active=True).all()

    # Enrich each course with clean group, schedule, and room info
    cur_tid = current_teacher.id if current_teacher else None
    for c in courses:
        c.ui_group_label = get_course_group_label(c)
        c.ui_schedule_label = get_course_schedule_label(c, teacher_id=cur_tid)
        if cur_tid:
            t_slots = ScheduleSlot.query.join(Course, ScheduleSlot.course_id == Course.id, isouter=True).filter(
                ScheduleSlot.course_id == c.id,
                db.or_(
                    ScheduleSlot.teacher_id == cur_tid,
                    db.and_(ScheduleSlot.teacher_id.is_(None), Course.teacher_id == cur_tid)
                )
            ).all()
            if t_slots:
                sched_days = set(s.day_of_week for s in t_slots if s.day_of_week is not None)
            else:
                sched_days = c.scheduled_weekdays or set()
        else:
            sched_days = c.scheduled_weekdays or set()
        c.ui_is_today = (d.weekday() in sched_days)
        c.ui_room_name = c.room.name if c.room else ''

    course = None
    if cid:
        c_cand = Course.query.get(cid)
        if c_cand:
            if u and u.role == 'teacher':
                if any(c.id == c_cand.id for c in courses):
                    course = c_cand
            else:
                course = c_cand
    
    # Automatically pick the nearest session the teacher is teaching or about to teach
    if not course and courses:
        course = find_nearest_course_for_attendance(courses, d, teacher_id=cur_tid)
        cid = course.id if course else None

    # Sort courses so that the active course is first, then today's courses, then future courses
    def course_sort_key(c_item):
        is_sel = 0 if (course and c_item.id == course.id) else 1
        is_tod = 0 if getattr(c_item, 'ui_is_today', False) else 1
        return (is_sel, is_tod, c_item.name)

    courses.sort(key=course_sort_key)

    records = {}
    enrolls = []
    if course:
        for a in Attendance.query.filter_by(course_id=course.id, date=d).all():
            records[a.student_id] = a.status
        all_ens = Enrollment.query.filter(Enrollment.course_id == course.id, Enrollment.status.in_(['active', 'trial'])).all()
        enrolls = [e for e in all_ens if e.is_attendance_eligible(as_of_date=d) or (e.student_id in records)]

    return render_template('attendance.html',
                           courses=courses,
                           course=course,
                           d=d,
                           records=records,
                           enrolls=enrolls,
                           current_teacher=current_teacher)


@app.route('/attendance/admin')
@login_required
@role_required('admin', 'secretary', 'teacher')
def attendance_admin():
    teacher_id = _int(request.args.get('teacher_id'))
    cid = _int(request.args.get('course_id'))
    level_filter = request.args.get('level', '').strip()
    period = request.args.get('period', '').strip()
    status_filter = request.args.get('status', '').strip()  # 'all', 'absent', 'late', 'present'
    att_date = request.args.get('date', '').strip()
    search_q = request.args.get('q', '').strip()
    notified_filter = request.args.get('notified', '').strip() # 'all', 'pending', 'notified'
    open_wa = request.args.get('open_wa', '').strip()

    u = current_user()
    is_teacher = (u and u.role == 'teacher')
    current_teacher = None
    teacher_cids = []

    if is_teacher:
        current_teacher = get_current_teacher()
        if current_teacher:
            teacher_id = current_teacher.id
            teacher_cids = get_teacher_course_ids(current_teacher.id)
        else:
            teacher_id = -1
            teacher_cids = []

    if not period and not att_date:
        period = 'today'
        d = date.today()
    elif att_date:
        d = parse_date(att_date) or date.today()
    else:
        d = date.today()

    query = db.session.query(Attendance).join(Course, Attendance.course_id == Course.id).join(Student, Attendance.student_id == Student.id)

    if status_filter == 'absent':
        query = query.filter(Attendance.status == 'absent')
    elif status_filter == 'late':
        query = query.filter(Attendance.status == 'late')
    elif status_filter == 'present':
        query = query.filter(Attendance.status == 'present')
    elif status_filter == 'all':
        pass
    else:
        query = query.filter(Attendance.status.in_(['absent', 'late']))

    # Notification filter
    if notified_filter == 'pending':
        query = query.filter(Attendance.notified_at.is_(None))
    elif notified_filter == 'notified':
        query = query.filter(Attendance.notified_at.isnot(None))

    if is_teacher:
        if not teacher_cids:
            query = query.filter(Attendance.course_id == -1)
        else:
            if cid:
                if cid in teacher_cids:
                    query = query.filter(Attendance.course_id == cid)
                else:
                    query = query.filter(Attendance.course_id == -1)
            else:
                query = query.filter(Attendance.course_id.in_(teacher_cids))
    else:
        if teacher_id:
            t_cids = get_teacher_course_ids(teacher_id)
            if t_cids:
                query = query.filter(Attendance.course_id.in_(t_cids))
            else:
                query = query.filter(Attendance.course_id == -1)

        if cid:
            query = query.filter(Attendance.course_id == cid)

    if level_filter:
        query = query.filter(db.or_(Course.level == level_filter, Student.school_level == level_filter))

    if period == 'today':
        query = query.filter(Attendance.date == date.today())
    elif period == 'yesterday':
        query = query.filter(Attendance.date == date.today() - timedelta(days=1))
    elif period == 'this_week':
        start_w = date.today() - timedelta(days=date.today().weekday())
        query = query.filter(Attendance.date >= start_w, Attendance.date <= date.today())
    elif period == 'this_month':
        start_m = date(date.today().year, date.today().month, 1)
        query = query.filter(Attendance.date >= start_m, Attendance.date <= date.today())
    elif period == 'all':
        pass
    elif att_date and d:
        query = query.filter(Attendance.date == d)

    if search_q:
        stu_filter = build_student_search_filter(search_q, Student)
        if stu_filter is not None:
            query = query.filter(stu_filter)

    att_list = query.order_by(Attendance.date.desc(), Attendance.id.desc()).limit(350).all()

    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '')

    absent_records = []
    total_absent_count = 0
    total_late_count = 0
    total_notified_count = 0
    total_pending_count = 0

    for a in att_list:
        if a.status == 'absent':
            total_absent_count += 1
        elif a.status == 'late':
            total_late_count += 1

        is_notified = (a.notified_at is not None)
        if is_notified:
            total_notified_count += 1
        else:
            total_pending_count += 1

        stu = Student.query.get(a.student_id)
        c_obj = Course.query.get(a.course_id)
        
        t_obj = None
        if c_obj and c_obj.teacher_id:
            t_obj = Teacher.query.get(c_obj.teacher_id)
        if not t_obj and c_obj:
            ct = CourseTeacher.query.filter_by(course_id=c_obj.id, is_active=True).first()
            if ct:
                t_obj = Teacher.query.get(ct.teacher_id)

        raw_parent_phone = (stu.parent_phone or '') if stu else ''
        raw_student_phone = (stu.phone or '') if stu else ''
        clean_parent_phone = _clean_wa_phone(raw_parent_phone)
        clean_student_phone = _clean_wa_phone(raw_student_phone)

        # Priority: parent phone first, student phone fallback
        clean_phone = clean_parent_phone or clean_student_phone
        raw_phone = raw_parent_phone or raw_student_phone

        status_lbl = "غائب(ة) 🔴" if a.status == 'absent' else ("متأخر(ة) ⚠️" if a.status == 'late' else "حاضر(ة) 🟢")
        status_fr = "absent(e) 🔴" if a.status == 'absent' else ("en retard ⚠️" if a.status == 'late' else "présent(e) 🟢")

        # Generate unique anti-ban spintax messages
        msg_ar = generate_spintax_absence_message(
            stu.full_name if stu else '',
            c_obj.display_name if c_obj else '',
            t_obj.full_name if t_obj else '',
            a.date,
            a.status,
            lang='ar',
            inst_name=inst_name,
            inst_phone=inst_phone,
            ref_seed=a.id
        )
        msg_fr = generate_spintax_absence_message(
            stu.full_name if stu else '',
            c_obj.display_name if c_obj else '',
            t_obj.full_name if t_obj else '',
            a.date,
            a.status,
            lang='fr',
            inst_name=inst_name,
            inst_phone=inst_phone,
            ref_seed=a.id
        )

        wa_link = f"https://wa.me/{clean_phone}?text={quote(msg_ar)}" if clean_phone else None

        absent_records.append({
            'attendance': a,
            'attendance_id': a.id,
            'student': stu,
            'student_id': stu.id if stu else None,
            'student_name': stu.full_name if stu else '',
            'student_code': stu.code if stu else '',
            'parent_name': (stu.parent_name if stu else '') or 'Parent',
            'course': c_obj,
            'course_name': c_obj.display_name if c_obj else '',
            'teacher': t_obj,
            'teacher_name': t_obj.full_name if t_obj else '',
            'date': str(a.date),
            'status': a.status,
            'status_lbl': status_lbl,
            'status_fr': status_fr,
            'phone': raw_phone,
            'clean_phone': clean_phone,
            'raw_parent_phone': raw_parent_phone,
            'clean_parent_phone': clean_parent_phone,
            'raw_student_phone': raw_student_phone,
            'clean_student_phone': clean_student_phone,
            'is_notified': is_notified,
            'notified_at': a.notified_at,
            'notified_phone': a.notified_phone,
            'notified_at_str': a.notified_at.strftime('%d/%m %H:%M') if a.notified_at else None,
            'wa_link': wa_link,
            'msg_ar': msg_ar,
            'msg_fr': msg_fr
        })

    if is_teacher:
        all_teachers = [current_teacher] if current_teacher else []
        all_courses = Course.query.filter(Course.id.in_(teacher_cids), Course.active == True).order_by(Course.name).all() if teacher_cids else []
        c_lvls = [c.level for c in all_courses if c.level and c.level.strip()]
        all_levels = sorted(list(set(c_lvls)))
        selected_course = Course.query.get(cid) if (cid and cid in teacher_cids) else None
        selected_teacher = current_teacher
    else:
        all_teachers = Teacher.query.filter_by(active=True).order_by(Teacher.first_name).all()
        all_courses = Course.query.filter_by(active=True).order_by(Course.name).all()
        c_lvls = [c.level for c in all_courses if c.level and c.level.strip()]
        s_lvls = [s[0] for s in db.session.query(Student.school_level).distinct() if s[0] and s[0].strip()]
        all_levels = sorted(list(set(c_lvls + s_lvls)))
        selected_course = Course.query.get(cid) if cid else None
        selected_teacher = Teacher.query.get(teacher_id) if teacher_id else None

    return render_template('attendance_admin.html',
                           courses=all_courses,
                           all_teachers=all_teachers,
                           all_levels=all_levels,
                           selected_course=selected_course,
                           selected_teacher=selected_teacher,
                           teacher_id=teacher_id,
                           course_id=cid,
                           level_filter=level_filter,
                           period=period,
                           status_filter=status_filter,
                           notified_filter=notified_filter,
                           search_q=search_q,
                           d=d,
                           att_date=att_date,
                           absent_records=absent_records,
                           total_absent_count=total_absent_count,
                           total_late_count=total_late_count,
                           total_notified_count=total_notified_count,
                           total_pending_count=total_pending_count,
                           total_records_count=len(absent_records),
                           inst_name=inst_name,
                           inst_phone=inst_phone,
                           open_wa=open_wa)


@app.route('/attendance/mark_notified', methods=['POST'])
@login_required
@role_required('admin', 'secretary', 'teacher')
def attendance_mark_notified():
    data = request.get_json(silent=True) or request.form
    att_id = _int(data.get('attendance_id'))
    att_ids = data.get('attendance_ids')
    phone = (data.get('phone') or '').strip()
    
    now = datetime.utcnow()
    updated_ids = []
    
    if att_id:
        a = Attendance.query.get(att_id)
        if a:
            a.notified_at = now
            if phone:
                a.notified_phone = phone
            updated_ids.append(a.id)
    elif att_ids and isinstance(att_ids, list):
        for aid in att_ids:
            a = Attendance.query.get(_int(aid))
            if a:
                a.notified_at = now
                if phone:
                    a.notified_phone = phone
                updated_ids.append(a.id)
                
    db.session.commit()
    return jsonify({
        'success': True,
        'updated_count': len(updated_ids),
        'updated_ids': updated_ids,
        'notified_at': now.strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/attendance/whatsapp_queue', methods=['GET'])
@login_required
@role_required('admin', 'secretary', 'teacher')
def attendance_whatsapp_queue():
    ids_param = request.args.get('ids', '').strip()
    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '')

    u = current_user()
    is_teacher = (u and u.role == 'teacher')
    teacher_cids = []
    if is_teacher:
        current_teacher = get_current_teacher()
        teacher_cids = get_teacher_course_ids(current_teacher.id) if current_teacher else []

    query = db.session.query(Attendance).join(Course, Attendance.course_id == Course.id).join(Student, Attendance.student_id == Student.id)
    if is_teacher:
        if teacher_cids:
            query = query.filter(Attendance.course_id.in_(teacher_cids))
        else:
            query = query.filter(Attendance.course_id == -1)
    
    if ids_param:
        ids_list = [_int(x) for x in ids_param.split(',') if _int(x)]
        query = query.filter(Attendance.id.in_(ids_list))
    else:
        period = request.args.get('period', 'today')
        cid = _int(request.args.get('course_id'))
        teacher_id = _int(request.args.get('teacher_id'))
        status_filter = request.args.get('status', 'absent')
        notified_filter = request.args.get('notified', '')
        
        if status_filter in ('absent', 'late', 'present'):
            query = query.filter(Attendance.status == status_filter)
        elif status_filter == 'all':
            pass
        else:
            query = query.filter(Attendance.status.in_(['absent', 'late']))
            
        if notified_filter == 'pending':
            query = query.filter(Attendance.notified_at.is_(None))
        elif notified_filter == 'notified':
            query = query.filter(Attendance.notified_at.isnot(None))

        if cid:
            query = query.filter(Attendance.course_id == cid)
        if teacher_id:
            t_cids = get_teacher_course_ids(teacher_id)
            if t_cids:
                query = query.filter(Attendance.course_id.in_(t_cids))
        if period == 'today':
            query = query.filter(Attendance.date == date.today())
        elif period == 'yesterday':
            query = query.filter(Attendance.date == date.today() - timedelta(days=1))
        elif period == 'this_week':
            start_w = date.today() - timedelta(days=date.today().weekday())
            query = query.filter(Attendance.date >= start_w, Attendance.date <= date.today())

    att_list = query.order_by(Attendance.date.desc(), Attendance.id.desc()).limit(200).all()
    
    results = []
    for a in att_list:
        stu = Student.query.get(a.student_id)
        c_obj = Course.query.get(a.course_id)
        t_obj = Teacher.query.get(c_obj.teacher_id) if (c_obj and c_obj.teacher_id) else None

        raw_parent_phone = (stu.parent_phone or '') if stu else ''
        raw_student_phone = (stu.phone or '') if stu else ''
        clean_parent = _clean_wa_phone(raw_parent_phone)
        clean_student = _clean_wa_phone(raw_student_phone)

        msg_ar = generate_spintax_absence_message(
            stu.full_name if stu else '',
            c_obj.display_name if c_obj else '',
            t_obj.full_name if t_obj else '',
            a.date,
            a.status,
            lang='ar',
            inst_name=inst_name,
            inst_phone=inst_phone,
            ref_seed=a.id
        )
        msg_fr = generate_spintax_absence_message(
            stu.full_name if stu else '',
            c_obj.display_name if c_obj else '',
            t_obj.full_name if t_obj else '',
            a.date,
            a.status,
            lang='fr',
            inst_name=inst_name,
            inst_phone=inst_phone,
            ref_seed=a.id
        )

        results.append({
            'attendance_id': a.id,
            'student_id': stu.id if stu else None,
            'student_name': stu.full_name if stu else '',
            'student_code': stu.code if stu else '',
            'parent_name': (stu.parent_name if stu else '') or 'Parent',
            'course_name': c_obj.display_name if c_obj else '',
            'teacher_name': t_obj.full_name if t_obj else '',
            'date': str(a.date),
            'status': a.status,
            'raw_parent_phone': raw_parent_phone,
            'clean_parent_phone': clean_parent,
            'raw_student_phone': raw_student_phone,
            'clean_student_phone': clean_student,
            'clean_phone': clean_parent or clean_student,
            'is_notified': a.notified_at is not None,
            'notified_at_str': a.notified_at.strftime('%d/%m %H:%M') if a.notified_at else None,
            'msg_ar': msg_ar,
            'msg_fr': msg_fr
        })

    return jsonify({
        'success': True,
        'count': len(results),
        'records': results,
        'inst_name': inst_name,
        'inst_phone': inst_phone
    })


@app.route('/attendance/save', methods=['POST'])
@login_required
@role_required('admin', 'secretary', 'teacher')
def attendance_save():
    cid = _int(request.form.get('course_id'))
    d = parse_date(request.form.get('date')) or date.today()
    course = Course.query.get_or_404(cid)

    u = current_user()
    if u and u.role == 'teacher':
        current_teacher = get_current_teacher()
        if not current_teacher:
            flash("Aucun profil enseignant associé.", "danger")
            return redirect(url_for('attendance'))
        t_cids = get_teacher_course_ids(current_teacher.id)
        if cid not in t_cids:
            flash("Accès refusé pour ce cours.", "danger")
            return redirect(url_for('attendance'))
    
    absent_students = []
    late_students = []
    trial_students_marked = []
    expired_marked = []
    debt_marked = []
    
    for key, val in request.form.items():
        if key.startswith('st_'):
            sid = int(key.split('_')[1])
            a = Attendance.query.filter_by(course_id=cid, student_id=sid, date=d).first()
            if not a:
                a = Attendance(course_id=cid, student_id=sid, date=d)
                db.session.add(a)
            a.status = val
            
            stu = Student.query.get(sid)
            if val == 'absent':
                if stu: absent_students.append(stu)
            elif val == 'late':
                if stu: late_students.append(stu)

            if val in ('present', 'late') and stu:
                active_en = Enrollment.query.filter_by(course_id=cid, student_id=sid, status='active').order_by(Enrollment.id.desc()).first()
                if active_en:
                    if active_en.balance > 0:
                        debt_marked.append((stu, active_en, active_en.balance))
                    elif active_en.end_date and (d - active_en.end_date).days > 7 and not active_en.is_renewed:
                        expired_marked.append((stu, active_en, (d - active_en.end_date).days))

            trial_en = Enrollment.query.filter_by(course_id=cid, student_id=sid, status='trial').first()
            if trial_en and stu:
                trial_students_marked.append((stu, val, trial_en))
                
    db.session.commit()

    u = current_user()
    user_name = u.full_name or u.username if u else 'Enseignant'

    if course.scheduled_weekdays and d.weekday() not in course.scheduled_weekdays:
        flash(f"⚠️ تنبيه: تم تسجيل الحضور بتاريخ {d.strftime('%d/%m/%Y')} وهو يوم خارج جدول الحصص الرسمي لهذا الفوج.", "warning")
    
    if absent_students or late_students:
        notif_title = f"🚨 الغياب: {course.display_name} ({d})"
        notif_msg = f"قام {user_name} بتسجيل غياب {len(absent_students)} تلميذ و تأخر {len(late_students)} تلميذ. انقر هنا لإرسال رسائل WhatsApp لأولياء الأمور."
        notif_link = f"/attendance/admin?course_id={cid}&date={d}&open_wa=1"
        
        notif = SystemNotification(
            title=notif_title,
            message=notif_msg,
            link=notif_link,
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()

    if debt_marked:
        for d_stu, d_en, d_bal in debt_marked:
            notif = SystemNotification(
                title=f"⚠️ تنبيه مالي: حضور تلميذ بذمته متأخرات ({d_stu.full_name})",
                message=f"سجل الأستاذ {user_name} حضور التلميذ {d_stu.full_name} في مادة {course.display_name} بتاريخ {d} وبذمته متأخرات مالية بقيمة {d_bal:.0f} DH. يُرجى استخلاص المبلغ.",
                link=f"/students/{d_stu.id}",
                is_read=False
            )
            db.session.add(notif)
        db.session.commit()

    if expired_marked:
        for ex_stu, ex_en, ex_days in expired_marked:
            notif = SystemNotification(
                title=f"🚨 تنبيه: حضور باشتراك منتهي ({ex_stu.full_name})",
                message=f"سجل الأستاذ {user_name} حضور التلميذ {ex_stu.full_name} في مادة {course.display_name} بتاريخ {d} رغم انتهاء اشتراكه منذ {ex_days} يوماً ({ex_en.end_date}). يُرجى الاتصال به فوراً لتجديد الاشتراك.",
                link=f"/students/{ex_stu.id}",
                is_read=False
            )
            db.session.add(notif)
        db.session.commit()

    if trial_students_marked:
        for t_stu, t_val, t_en in trial_students_marked:
            st_text = "حاضر" if t_val == 'present' else ("غائب" if t_val == 'absent' else "متأخر")
            notif = SystemNotification(
                title=f"🧪 إشعار حصة تجريبية: {t_stu.full_name}",
                message=f"أجرى التلميذ(ة) {t_stu.full_name} حصته التجريبية في {course.display_name} ({st_text}). يُرجى اتخاذ القرار: تأكيد التسجيل أو تسجيل المغادرة.",
                link="/enrollments?status=trial",
                is_read=False
            )
            db.session.add(notif)
        db.session.commit()
        t_names = ", ".join(stu.full_name for stu, _, _ in trial_students_marked)
        flash(f"🧪 Alerte Séance d'Essai : {t_names} a/ont terminé leur séance d'essai (1/1). Action requise : Valider l'inscription ou Marquer Quitter / Abandon.", "warning")

    flash(f"Présences enregistrées avec succès ({len(absent_students)} absent(s), {len(late_students)} retard(s)).", 'success')
    if u and u.role == 'teacher':
        total_marked = sum(1 for k in request.form if k.startswith('st_'))
        p_cnt = max(total_marked - len(absent_students) - len(late_students), 0)
        return redirect(url_for('attendance', course_id=cid, date=d, saved=1,
                                p=p_cnt, a=len(absent_students), l=len(late_students)))
    else:
        return redirect(url_for('attendance_admin', course_id=cid, date=d, open_wa=1 if (absent_students or late_students) else ''))



@app.route('/attendance/note', methods=['POST'])
@login_required
@role_required('admin', 'secretary', 'teacher')
def attendance_note():
    """Note libre du prof après l'appel (ex: élève présent mais non inscrit).
    Crée une StaffNote (message complet) + une SystemNotification (alerte cloche)."""
    u = current_user()
    cid = _int(request.form.get('course_id'))
    d = parse_date(request.form.get('date')) or date.today()
    kind = (request.form.get('kind') or 'other').strip()
    text = (request.form.get('text') or '').strip()
    student_name = (request.form.get('student_name') or '').strip()
    course = Course.query.get(cid) if cid else None
    if not course:
        return jsonify({'success': False, 'error': 'Classe introuvable'}), 400

    if u.role == 'teacher':
        ct = get_current_teacher()
        if not ct or cid not in get_teacher_course_ids(ct.id):
            return jsonify({'success': False, 'error': 'Accès refusé'}), 403

    if not text and not student_name:
        return jsonify({'success': False, 'error': 'Message vide'}), 400

    kind_labels = {
        'unregistered': "Élève présent en classe mais NON inscrit dans ce groupe",
        'other_class': "Élève présent mais inscrit dans une AUTRE classe",
        'other': "Remarque du professeur",
    }
    kind_label = kind_labels.get(kind, kind_labels['other'])
    room_name = course.room.name if getattr(course, 'room', None) else 'Salle non définie'
    teacher_name = u.full_name or u.username
    try:
        sched = get_course_schedule_label(course)
    except Exception:
        sched = ''

    lines = [
        f"{kind_label}",
        f"Professeur : {teacher_name}",
        f"Classe : {course.display_name}",
        f"Salle : {room_name}" + (f"  ·  Horaire : {sched}" if sched else ''),
        f"Date de la séance : {d.strftime('%d/%m/%Y')}",
    ]
    if student_name:
        lines.append(f"Élève concerné : {student_name}")
    if text:
        lines.append("")
        lines.append(f"Message : {text}")
    content = "\n".join(lines)

    recipients = User.query.filter(User.role.in_(['admin', 'secretary']), User.active == True).all()
    target_ids = [r.id for r in recipients]

    title = f"📝 Note de {teacher_name} · {room_name}"
    note = StaffNote(
        title=title[:200],
        content=content,
        priority='high' if kind in ('unregistered', 'other_class') else 'normal',
        category='pedagogy',
        author_id=u.id,
        target_type='specific' if target_ids else 'all',
        target_user_ids=json.dumps(target_ids) if target_ids else None,
        status='pending',
    )
    db.session.add(note)

    preview = (text or student_name)
    if len(preview) > 90:
        preview = preview[:90] + '…'
    short = f"{kind_label} — {('Élève : ' + student_name + ' — ') if student_name else ''}{preview} (Salle : {room_name})"
    db.session.add(SystemNotification(
        title=f"📝 Note de {teacher_name}"[:150],
        message=short,
        link=url_for('staff_notes', tab='teachers'),
        is_read=False,
    ))
    db.session.commit()
    log_action('attendance_note', f"Note prof {teacher_name} ({course.display_name}, {room_name}): {kind}")
    return jsonify({'success': True})


@app.route('/attendance/propose-student', methods=['POST'])
@login_required
@role_required('teacher', 'admin', 'secretary')
def attendance_propose_student():
    """Permet au professeur de proposer un nouvel élève présent en classe (Nom + Niveau).
    La demande est enregistrée avec statut 'pending' pour validation et inscription par l'admin."""
    u = current_user()
    full_name = (request.form.get('full_name') or '').strip()
    school_level = (request.form.get('school_level') or '').strip()
    cid = _int(request.form.get('course_id'))
    notes = (request.form.get('notes') or '').strip()
    phone = (request.form.get('phone') or '').strip()

    if not full_name:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': "Veuillez saisir le nom et prénom de l'élève."}), 400
        flash("Veuillez saisir le nom et prénom de l'élève.", "danger")
        return redirect(url_for('attendance', course_id=cid) if cid else url_for('attendance'))

    course = Course.query.get(cid) if cid else None
    current_teacher = get_current_teacher() if u.role == 'teacher' else None
    tid = current_teacher.id if current_teacher else (course.teacher_id if course and course.teacher_id else None)

    if not tid and u.role == 'teacher':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': "Profil enseignant non trouvé."}), 400
        flash("Profil enseignant non trouvé.", "danger")
        return redirect(url_for('attendance'))

    if not tid:
        first_t = Teacher.query.first()
        tid = first_t.id if first_t else 1

    req_obj = TeacherStudentRequest(
        full_name=full_name,
        school_level=school_level,
        phone=phone,
        notes=notes,
        course_id=course.id if course else None,
        teacher_id=tid,
        status='pending',
        created_at=datetime.utcnow()
    )
    db.session.add(req_obj)

    # 1. System Notification for Admin / Secretary
    teacher_name = current_teacher.full_name if current_teacher else (u.full_name or u.username)
    c_label = course.display_name if course else 'Non spécifiée'
    notif_title = f"📥 Nouvel élève proposé par {teacher_name}"
    notif_msg = f"{full_name} ({school_level or 'Niveau non précisé'}) pour le groupe {c_label}."
    db.session.add(SystemNotification(
        title=notif_title[:150],
        message=notif_msg,
        link=url_for('teacher_student_requests'),
        is_read=False,
    ))

    # 2. Staff Note
    note_content = (
        f"Demande d'ajout d'élève par l'enseignant\n"
        f"Professeur : {teacher_name}\n"
        f"Élève : {full_name}\n"
        f"Niveau Scolaire : {school_level or 'Non précisé'}\n"
        f"Classe souhaitée : {c_label}\n"
    )
    if phone:
        note_content += f"Téléphone : {phone}\n"
    if notes:
        note_content += f"Remarque : {notes}\n"

    staff_note = StaffNote(
        title=f"📥 Élève proposé : {full_name} ({teacher_name})",
        content=note_content,
        priority='high',
        category='pedagogy',
        author_id=u.id,
        target_type='all',
        status='pending'
    )
    db.session.add(staff_note)
    db.session.commit()

    log_action('teacher_student_propose', f"Teacher {teacher_name} proposed student {full_name} for course {c_label}")

    msg_success = f"✅ Demande transmise avec succès à l'administration pour {full_name} !"
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'message': msg_success, 'request_id': req_obj.id})

    flash(msg_success, "success")
    return redirect(url_for('attendance', course_id=cid) if cid else url_for('attendance'))


@app.route('/admin/teacher-student-requests')
@login_required
@role_required('admin', 'secretary')
def teacher_student_requests():
    """File d'attente des élèves proposés par les professeurs pour validation et inscription express."""
    status_filter = request.args.get('status', 'all').strip()
    search_q = request.args.get('q', '').strip()
    teacher_id = _int(request.args.get('teacher_id'))

    query = TeacherStudentRequest.query

    if status_filter in ('pending', 'approved', 'rejected'):
        query = query.filter_by(status=status_filter)

    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)

    if search_q:
        q_term = f"%{search_q}%"
        query = query.filter(TeacherStudentRequest.full_name.ilike(q_term))

    requests_list = query.order_by(
        db.case((TeacherStudentRequest.status == 'pending', 0), else_=1),
        TeacherStudentRequest.created_at.desc()
    ).all()

    counts = {
        'all': TeacherStudentRequest.query.count(),
        'pending': TeacherStudentRequest.query.filter_by(status='pending').count(),
        'approved': TeacherStudentRequest.query.filter_by(status='approved').count(),
        'rejected': TeacherStudentRequest.query.filter_by(status='rejected').count(),
    }

    teachers = Teacher.query.filter_by(active=True).order_by(Teacher.first_name, Teacher.last_name).all()

    return render_template('teachers/teacher_student_requests.html',
                           requests=requests_list,
                           counts=counts,
                           current_status=status_filter,
                           teachers=teachers,
                           search_q=search_q,
                           selected_teacher_id=teacher_id)


@app.route('/admin/teacher-student-requests/<int:req_id>/reject', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def teacher_student_request_reject(req_id):
    req_obj = TeacherStudentRequest.query.get_or_404(req_id)
    reason = (request.form.get('reason') or '').strip()
    req_obj.status = 'rejected'
    req_obj.rejection_reason = reason or 'Refusé par l\'administration'
    req_obj.processed_at = datetime.utcnow()
    req_obj.processed_by_id = current_user().id
    db.session.commit()
    log_action('teacher_student_request_reject', f"Request #{req_obj.id} for {req_obj.full_name} rejected: {reason}")
    flash(f"Demande pour {req_obj.full_name} marquée comme rejetée.", "info")
    return redirect(url_for('teacher_student_requests'))


@app.route('/admin/teacher-student-requests/<int:req_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def teacher_student_request_delete(req_id):
    req_obj = TeacherStudentRequest.query.get_or_404(req_id)
    db.session.delete(req_obj)
    db.session.commit()
    flash("Demande supprimée avec succès.", "info")
    return redirect(url_for('teacher_student_requests'))


@app.route('/notifications/read/<int:nid>')
@login_required
def notification_read(nid):
    n = SystemNotification.query.get_or_404(nid)
    n.is_read = True
    db.session.commit()
    return redirect(n.link or url_for('dashboard'))


# ---------------------------------------------------------------------------
# State-Accredited Certificates & Attestations (الشواهد والشهادات المعتمدة)
# ---------------------------------------------------------------------------
@app.route('/certificates')
@login_required
@role_required('admin', 'secretary')
def certificates():
    certs = Certificate.query.order_by(Certificate.id.desc()).all()
    students = Student.query.filter_by(status='active').order_by(Student.last_name).all()
    teachers = Teacher.query.filter_by(active=True).order_by(Teacher.last_name).all()
    employees = Employee.query.filter_by(active=True).order_by(Employee.last_name).all()
    courses = Course.query.filter_by(active=True).order_by(Course.category, Course.name).all()
    return render_template(
        'certificates/list.html',
        certs=certs,
        students=students,
        teachers=teachers,
        employees=employees,
        courses=courses
    )


@app.route('/certificates/new', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def certificate_new():
    d = request.form
    cert_type = d.get('cert_type', 'Attestation de Niveau en Langue')
    recipient_type = d.get('recipient_type', 'student')  # 'student', 'teacher', 'employee', 'custom'

    stu_id = _int(d.get('student_id')) if recipient_type == 'student' else None
    teacher_id = _int(d.get('teacher_id')) if recipient_type == 'teacher' else None
    employee_id = _int(d.get('employee_id')) if recipient_type == 'employee' else None

    recipient_name = d.get('recipient_name', '').strip()
    cin = d.get('cin', '').strip()
    cnss_no = d.get('cnss_no', '').strip()
    job_title = d.get('job_title', '').strip()
    department = d.get('department', '').strip()

    start_date = parse_date(d.get('start_date'))
    end_date = parse_date(d.get('end_date'))

    stu = Student.query.get(stu_id) if stu_id else None
    teacher = Teacher.query.get(teacher_id) if teacher_id else None
    employee = Employee.query.get(employee_id) if employee_id else None

    if not recipient_name:
        if stu:
            recipient_name = stu.full_name
            if not cin and stu.cin:
                cin = stu.cin
        elif teacher:
            recipient_name = teacher.full_name
            if not cin and teacher.cin:
                cin = teacher.cin
            if not job_title:
                job_title = f"Enseignant(e) de {teacher.specialty or 'Langue'}"
        elif employee:
            recipient_name = employee.full_name
            if not cin and employee.cin:
                cin = employee.cin
            if not cnss_no and employee.cnss_no:
                cnss_no = employee.cnss_no
            if not job_title and employee.job_title:
                job_title = employee.job_title
            if not department and employee.department:
                department = employee.department
            if not start_date and employee.hire_date:
                start_date = employee.hire_date

    cid = _int(d.get('course_id')) or None
    title = d.get('title') or cert_type
    issue_dt = parse_date(d.get('issue_date')) or date.today()
    mention = d.get('mention', 'Très Bien')
    notes = d.get('notes')

    student_code = d.get('student_code', '').strip()
    birth_date = parse_date(d.get('birth_date'))
    birth_city = d.get('birth_city', '').strip()
    level = d.get('level', '').strip()

    def _parse_score(val):
        try:
            return float(str(val).replace(',', '.').strip())
        except (ValueError, TypeError, AttributeError):
            return 0.0

    score_listening = _parse_score(d.get('score_listening'))
    score_speaking = _parse_score(d.get('score_speaking'))
    score_reading = _parse_score(d.get('score_reading'))
    score_writing = _parse_score(d.get('score_writing'))
    overall_score = _parse_score(d.get('overall_score'))

    if stu:
        if not student_code:
            student_code = stu.code
        if not birth_date and stu.birth_date:
            birth_date = stu.birth_date
        if not birth_city and stu.city:
            birth_city = stu.city

    if not overall_score:
        valid_scores = [s for s in [score_listening, score_speaking, score_reading, score_writing] if s > 0]
        if valid_scores:
            overall_score = round(sum(valid_scores) / len(valid_scores), 1)

    # Prefix
    prefix = "CERT"
    if "stage" in cert_type.lower():
        prefix = "STAGE"
    elif "travail" in cert_type.lower():
        prefix = "TRAV"

    cert_no = f"{prefix}-{date.today().year}-{Certificate.query.count() + 1:04d}"

    c = Certificate(
        cert_number=cert_no,
        student_id=stu_id,
        teacher_id=teacher_id,
        employee_id=employee_id,
        course_id=cid,
        cert_type=cert_type,
        recipient_name=recipient_name,
        cin=cin,
        cnss_no=cnss_no,
        job_title=job_title,
        department=department,
        start_date=start_date,
        end_date=end_date,
        student_code=student_code,
        birth_date=birth_date,
        birth_city=birth_city,
        level=level,
        score_listening=score_listening,
        score_speaking=score_speaking,
        score_reading=score_reading,
        score_writing=score_writing,
        overall_score=overall_score,
        title=title,
        issue_date=issue_dt,
        mention=mention,
        notes=notes
    )
    db.session.add(c)
    db.session.commit()

    log_action('certificate_issue', f"{cert_type} {cert_no} issued for {c.beneficiary_name}")
    flash(f"{cert_type} ({cert_no}) générée avec succès pour {c.beneficiary_name} !", 'success')
    return redirect(url_for('certificate_print', cid=c.id))


@app.route('/certificates/<int:cid>/print')
@login_required
@role_required('admin', 'secretary')
def certificate_print(cid):
    c = Certificate.query.get_or_404(cid)
    stu = c.student

    pub = SH.get_setting('public_app_url', '').strip().rstrip('/')
    base_url = pub if pub else request.host_url.rstrip('/')
    verify_url = f"{base_url}/verify/cert/{c.cert_number}"
    qr = qr_data_uri(verify_url)

    logo_data_uri = None
    try:
        logo_path = os.path.join(BASE, 'logo_b64.txt')
        if os.path.exists(logo_path):
            with open(logo_path, 'r', encoding='utf-8') as f:
                b64 = f.read().strip()
                if b64:
                    logo_data_uri = f"data:image/png;base64,{b64}"
    except Exception:
        pass

    director_name = SH.get_setting('inst_director', 'AZIZ MARSOUL')

    return render_template('certificates/print.html', c=c, stu=stu, qr=qr, logo_data_uri=logo_data_uri, director_name=director_name, verify_url=verify_url)




@app.route('/certificates/<int:cid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def certificate_delete(cid):
    c = Certificate.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    flash('Certificat supprimé', 'success')
    return redirect(url_for('certificates'))


# ---------------------------------------------------------------------------
# Public Certificate Verification Portal (No login required)
# ---------------------------------------------------------------------------
@app.route('/verify', methods=['GET', 'POST'])
def verify_portal():
    q = request.form.get('cert_number') or request.args.get('cert_number')
    if q:
        return redirect(url_for('verify_certificate', cert_number=q.strip()))
    return render_template('certificates/verify.html', cert=None, search_mode=True)


@app.route('/verify/<cert_number>')
@app.route('/verify/cert/<cert_number>')
def verify_certificate(cert_number):
    c_num = cert_number.strip()
    cert = Certificate.query.filter(Certificate.cert_number.ilike(c_num)).first()

    logo_data_uri = None
    try:
        logo_path = os.path.join(BASE, 'logo_b64.txt')
        if os.path.exists(logo_path):
            with open(logo_path, 'r', encoding='utf-8') as f:
                b64 = f.read().strip()
                if b64:
                    logo_data_uri = f"data:image/png;base64,{b64}"
    except Exception:
        pass

    director_name = SH.get_setting('inst_director', 'AZIZ MARSOUL')
    inst_name = SH.get_setting('inst_name', 'Institut Les Sages (ILAS)')
    inst_phone = SH.get_setting('inst_phone', '+212 5 22 00 00 00')
    inst_address = SH.get_setting('inst_address', 'Centre Ville, Deroua / Casablanca')

    return render_template('certificates/verify.html',
                           cert=cert,
                           cert_number=c_num,
                           search_mode=False,
                           logo_data_uri=logo_data_uri,
                           director_name=director_name,
                           inst_name=inst_name,
                           inst_phone=inst_phone,
                           inst_address=inst_address)


# ---------------------------------------------------------------------------
# Borne Kiosk Express (Smart Attendance Station)
# ---------------------------------------------------------------------------
@app.route('/kiosk')
@login_required
def kiosk_page():
    today = date.today()
    today_scans_count = Attendance.query.filter_by(date=today, status='present').count()

    recent_atts = Attendance.query.filter_by(date=today, status='present').order_by(Attendance.id.desc()).limit(8).all()
    recent_scans = []
    for a in recent_atts:
        stu = a.student or (Student.query.get(a.student_id) if a.student_id else None)
        c = a.course or (Course.query.get(a.course_id) if a.course_id else None)
        if not stu:
            continue
        time_str = a.notified_at.strftime('%H:%M') if a.notified_at else datetime.now().strftime('%H:%M')
        recent_scans.append({
            'student_name': stu.full_name,
            'room_name': c.room.name if (c and c.room) else 'Salle ?',
            'time': time_str
        })

    return render_template('kiosk.html',
                           today_scans_count=today_scans_count,
                           recent_scans=recent_scans)



# ---------------------------------------------------------------------------
# Kiosk Search & Matching Helpers (Fuzzy, Typo-Tolerant & Prefix Matching)
# ---------------------------------------------------------------------------
import unicodedata
import difflib

def normalize_student_search_text(text):
    if not text:
        return ''
    s = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    return ' '.join(s.split())

def phonetic_search_key(text):
    s = normalize_student_search_text(text)
    if not s:
        return ''
    # Transliteration & common spelling variants (French/Arabic Moroccan transliteration)
    s = s.replace('ph', 'f').replace('ou', 'u').replace('o', 'u')
    s = s.replace('kh', 'k').replace('gh', 'g').replace('ch', 'sh')
    s = s.replace('y', 'i').replace('e', 'i')
    s = re.sub(r'c(?=[eiy])', 's', s)
    s = s.replace('c', 'k').replace('q', 'k')
    # Collapse duplicate characters (e.g., ss -> s, mm -> m, ll -> l)
    s = re.sub(r'(.)\1+', r'\1', s)
    return s

def score_token_match(qt, ct):
    if qt == ct:
        return 1.0
    if ct.startswith(qt):
        return 0.95
    qt_ph = phonetic_search_key(qt)
    ct_ph = phonetic_search_key(ct)
    if qt_ph == ct_ph:
        return 0.92
    if ct_ph.startswith(qt_ph):
        return 0.88
    # Substring in token: high if >= 3 chars, lower if 2 chars
    if qt in ct:
        return 0.80 if len(qt) >= 3 else 0.45
    r1 = difflib.SequenceMatcher(None, qt, ct).ratio()
    r2 = difflib.SequenceMatcher(None, qt_ph, ct_ph).ratio()
    best_r = max(r1, r2)
    if best_r >= 0.72 and len(qt) >= 3:
        return best_r * 0.75
    return 0.0


def score_student_kiosk_candidate(query, student):
    q_norm = normalize_student_search_text(query)
    if not q_norm:
        return 0
    c_name_norm = normalize_student_search_text(student.full_name)
    c_code_norm = normalize_student_search_text(student.code or '')
    c_phone = re.sub(r'[^0-9]', '', student.phone or '')
    c_parent_phone = re.sub(r'[^0-9]', '', student.parent_phone or '')
    c_whatsapp = re.sub(r'[^0-9]', '', student.whatsapp or '')
    q_digits = re.sub(r'[^0-9]', '', query)

    # 1. Exact student code match
    if q_norm == c_code_norm:
        return 100

    # 2. Code prefix match (only when query contains digits or is specific)
    if q_digits and (c_code_norm.startswith(q_norm) or q_digits in c_code_norm):
        return 96

    # 3. Phone match
    if q_digits and len(q_digits) >= 4 and (q_digits in c_phone or q_digits in c_parent_phone or q_digits in c_whatsapp):
        return 95

    # 4. Exact full name match
    if q_norm == c_name_norm:
        return 98

    q_tokens = q_norm.split()
    c_tokens = c_name_norm.split()
    if not q_tokens or not c_tokens:
        return 0

    # Multi-token matching: EVERY query token must find a match among candidate tokens!
    c_tokens_avail = list(c_tokens)
    token_scores = []
    for qt in q_tokens:
        best_sc = 0.0
        best_idx = -1
        for idx, ct in enumerate(c_tokens_avail):
            sc = score_token_match(qt, ct)
            if sc > best_sc:
                best_sc = sc
                best_idx = idx
        if best_sc > 0.40 and best_idx >= 0:
            token_scores.append(best_sc)
            c_tokens_avail.pop(best_idx)
        else:
            # If multi-token query and one token fails to match, reject candidate completely!
            if len(q_tokens) > 1:
                return 0
            token_scores.append(0.0)

    if not token_scores or any(s == 0 for s in token_scores):
        return 0

    avg_score = sum(token_scores) / len(token_scores)
    # Boost if first token prefix matches first word
    if c_tokens[0].startswith(q_tokens[0]):
        avg_score = min(1.0, avg_score + 0.05)

    final_score = int(avg_score * 100)
    return max(0, min(100, final_score))


def sync_student_renewed_enrollments(student_id=None):
    """
    Auto-transitions old 'active' enrollments that have already been renewed
    (e.is_renewed == True) to 'completed' once their period ends or the renewal starts,
    provided they have no unpaid balance.
    Returns the list of effective active enrollments (one per course, newest renewal wins).
    """
    today_dt = date.today()
    q = Enrollment.query.filter_by(status='active')
    if student_id is not None:
        q = q.filter_by(student_id=student_id)
    active_list = q.order_by(Enrollment.id.asc()).all()

    dirty = False
    for e in active_list:
        if e.is_renewed:
            ren = e.active_renewal
            period_over = bool(e.end_date and e.end_date < today_dt)
            renewal_started = bool(ren and ren.enroll_date and ren.enroll_date <= today_dt)
            if (period_over or renewal_started) and float(e.balance_due or 0.0) < 1.0:
                e.status = 'completed'
                dirty = True

    if dirty:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    if student_id is None:
        return []

    # Re-fetch active enrollments and deduplicate per course_id (newest renewal wins)
    remaining_active = Enrollment.query.filter_by(student_id=student_id, status='active').order_by(Enrollment.id.asc()).all()
    by_course = {}
    extra_debt_by_course = {}
    for e in remaining_active:
        key = e.course_id or f"pending_{e.id}"
        if e.is_renewed:
            # Keep track of any unpaid debt on the older enrollment, but let the renewal represent the course
            extra_debt_by_course[key] = extra_debt_by_course.get(key, 0.0) + max(0.0, float(e.balance_due or 0.0))
            continue
        by_course[key] = e

    effective_list = list(by_course.values())
    for e in effective_list:
        key = e.course_id or f"pending_{e.id}"
        e._extra_prior_debt = extra_debt_by_course.get(key, 0.0)
    return effective_list


@app.route('/api/kiosk/search', methods=['GET', 'POST'])
@login_required
def api_kiosk_search():
    """Autocomplete search endpoint for the Kiosk station."""
    q = request.args.get('q') or ''
    if not q and request.is_json:
        q = (request.get_json(silent=True) or {}).get('q', '')
    q = q.strip()
    if not q:
        return jsonify({'success': True, 'results': []})

    students = Student.query.filter(Student.status != 'archived').all()
    scored = []
    for s in students:
        score = score_student_kiosk_candidate(q, s)
        if score > 0:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    top_matches = scored[:12]

    matches = []
    for score, s in top_matches:
        photo_url = url_for('static', filename=f"uploads/{s.photo}") if s.photo else None
        active_ens = sync_student_renewed_enrollments(s.id)
        courses_str = ", ".join([e.course.display_name for e in active_ens if e.course][:2]) if active_ens else "Aucun cours actif"
        if len(active_ens) > 2:
            courses_str += f" (+{len(active_ens)-2})"

        matches.append({
            'id': s.id,
            'code': s.code or f"ETU{s.id:04d}",
            'full_name': s.full_name,
            'photo_url': photo_url,
            'school_level': s.school_level or '',
            'phone': s.phone or '',
            'parent_phone': s.parent_phone or '',
            'parent_name': s.parent_name or '',
            'courses_summary': courses_str,
            'score': score
        })

    return jsonify({
        'success': True,
        'results': matches
    })


@app.route('/api/kiosk/scan', methods=['POST'])
@login_required
def api_kiosk_scan():
    payload = request.get_json(silent=True) or {}
    student_id = payload.get('student_id')
    raw = (payload.get('code') or payload.get('query') or '').strip()

    student = None
    if student_id:
        student = Student.query.get(int(student_id))

    if not student and not raw:
        return jsonify({'success': False, 'message': 'Code vide / لم يتم إدخال أي رمز'}), 400

    if not student and raw:
        # 1. Match Student
        if '|' in raw:
            # Format: ILAS|ID|CODE|NAME
            parts = [p.strip() for p in raw.split('|')]
            if len(parts) >= 2 and parts[1].isdigit():
                student = Student.query.get(int(parts[1]))
            if not student and len(parts) >= 3 and parts[2]:
                student = Student.query.filter(Student.code.ilike(parts[2])).first()

        if not student:
            # Match by Code (case-insensitive, also handle spaces like "ILAS 218" -> "ILAS218")
            compact_code = re.sub(r'\s+', '', raw)
            student = Student.query.filter(
                (Student.code.ilike(raw)) | (Student.code.ilike(compact_code))
            ).first()

        if not student and raw.isdigit() and len(raw) <= 7:
            student = Student.query.get(int(raw))

        if not student:
            # Match by Phone
            clean_num = re.sub(r'[^0-9]', '', raw)
            if len(clean_num) >= 6:
                student = Student.query.filter(
                    (Student.phone.ilike(f"%{clean_num}%")) |
                    (Student.whatsapp.ilike(f"%{clean_num}%")) |
                    (Student.parent_phone.ilike(f"%{clean_num}%"))
                ).first()

        if not student:
            # Match by Name exact or prefix
            student = Student.query.filter(
                (Student.first_name + ' ' + Student.last_name).ilike(f"%{raw}%")
            ).first()

        if not student:
            # Fuzzy match across students with typo tolerance
            all_stus = Student.query.filter(Student.status != 'archived').all()
            best_stu = None
            best_score = 0
            for s in all_stus:
                sc = score_student_kiosk_candidate(raw, s)
                if sc > best_score:
                    best_score = sc
                    best_stu = s
            if best_stu and best_score >= 50:
                student = best_stu

    if not student:
        return jsonify({
            'success': False,
            'error': 'student_not_found',
            'message': f"Élève non reconnu ({raw}) / لم يتم العثور على التلميذ"
        }), 404

    # 2. Gatekeeper 3-Pillar Inspection (Read-Only Verification — NO ATTENDANCE WRITES)
    today = date.today()
    weekday = today.weekday()  # 0 = Lundi, 6 = Dimanche
    weekday_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    weekday_names_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    today_fr = weekday_names_fr[weekday]
    today_ar = weekday_names_ar[weekday]
    now_dt = datetime.now()
    now_min = now_dt.hour * 60 + now_dt.minute

    # Sync renewed enrollments (auto-complete old periods that were already renewed)
    enrollments = sync_student_renewed_enrollments(student.id)
    is_enrolled = len(enrollments) > 0
    enrolled_cids = [e.course_id for e in enrollments if e.course_id]

    # --- PILLAR 1: INSCRIPTION ---
    all_enrollments_info = []
    expired_course_ids = set()
    valid_course_ids = set()
    for e in enrollments:
        c = e.course
        if not c:
            continue
        extra_debt = getattr(e, '_extra_prior_debt', 0.0)
        e_debt = max(0.0, float(e.balance_due or 0.0)) + extra_debt
        is_past_end = bool(e.end_date and e.end_date < today and not e.is_renewed)
        if is_past_end:
            expired_course_ids.add(c.id)
        else:
            valid_course_ids.add(c.id)
        all_enrollments_info.append({
            'id': e.id,
            'course_id': c.id,
            'course_name': c.display_name or c.name,
            'teacher_name': c.teacher.full_name if c.teacher else 'Non assigné',
            'room_name': c.room.name if c.room else 'Salle non assignée',
            'balance_due': round(e_debt, 2),
            'start_date': e.enroll_date.strftime('%d/%m/%Y') if e.enroll_date else '—',
            'end_date': e.end_date.strftime('%d/%m/%Y') if e.end_date else '—',
            'is_expired': is_past_end,
            'status': e.status
        })

    # A student is considered expired only if they have expired courses AND (no valid courses OR today's course is expired)
    has_expired_enrollment = len(expired_course_ids) > 0 and len(valid_course_ids) == 0

    pillar1_inscription = {
        'is_enrolled': is_enrolled,
        'count': len(all_enrollments_info),
        'status_text_fr': f"Inscrit ({len(all_enrollments_info)} formation{'s' if len(all_enrollments_info) > 1 else ''})" if is_enrolled else "Non inscrit / Aucun dossier actif",
        'status_text_ar': f"مسجل ({len(all_enrollments_info)} مادة/تكوين)" if is_enrolled else "غير مسجل / لا يوجد تسجيل نشط",
        'status_class': 'success' if is_enrolled else 'danger',
        'courses': all_enrollments_info
    }

    # --- PILLAR 2: PAIEMENT ---
    total_balance_due = sum(c_info['balance_due'] for c_info in all_enrollments_info)
    total_balance_due = round(total_balance_due, 2)
    is_paid = (total_balance_due < 1.0)

    sub_status = 'valid'
    sub_msg_fr = 'Abonnement en règle'
    sub_msg_ar = 'الاشتراك ساري المفعول'
    latest_end_date = None
    if enrollments:
        end_dates = [e.end_date for e in enrollments if e.end_date]
        if end_dates:
            latest_end_date = max(end_dates).strftime('%d/%m/%Y')
        if has_expired_enrollment:
            sub_status = 'expired'
            sub_msg_fr = 'Abonnement arrivé à échéance'
            sub_msg_ar = 'الاشتراك منتهي الصلاحية'
    elif not is_enrolled:
        sub_status = 'not_enrolled'
        sub_msg_fr = 'Aucune inscription active'
        sub_msg_ar = 'غير مسجل'

    pillar2_paiement = {
        'is_paid': is_paid,
        'total_balance_due': total_balance_due,
        'status_text_fr': "À jour (0 DH dû)" if is_paid else f"Reste dû : {total_balance_due:.0f} DH",
        'status_text_ar': "مؤدى بالكامل (0 درهم)" if is_paid else f"باقي بذمته : {total_balance_due:.0f} درهم",
        'status_class': 'success' if is_paid else 'danger',
        'sub_status': sub_status,
        'message_fr': sub_msg_fr,
        'message_ar': sub_msg_ar,
        'end_date': latest_end_date or '—'
    }

    # --- PILLAR 3: SÉANCES DU JOUR (Current, Next, Previous) ---
    today_slots = ScheduleSlot.query.filter(
        ScheduleSlot.course_id.in_(enrolled_cids),
        ScheduleSlot.day_of_week == weekday
    ).all() if enrolled_cids else []

    current_session = None
    next_session = None
    previous_session = None
    next_diff_min = 999999
    prev_diff_min = 999999
    all_sessions_today = []

    for slot in today_slots:
        c = slot.course
        if not c:
            continue
        try:
            st_h, st_m = map(int, slot.start_time.split(':'))
            en_h, en_m = map(int, slot.end_time.split(':'))
        except Exception:
            continue

        slot_start_min = st_h * 60 + st_m
        slot_end_min = en_h * 60 + en_m

        slot_info = {
            'course_id': c.id,
            'course_name': c.display_name or c.name,
            'room_name': c.room.name if c.room else 'Salle non assignée',
            'teacher_name': c.teacher.full_name if c.teacher else 'Non assigné',
            'start_time': slot.start_time,
            'end_time': slot.end_time,
            'time_slot': f"{slot.start_time} - {slot.end_time}"
        }

        # Arrival window: 35 min before start to 15 min after end
        if (slot_start_min - 35) <= now_min <= (slot_end_min + 15):
            slot_info['timing_state'] = 'current'
            slot_info['status_label_fr'] = 'En cours maintenant'
            slot_info['status_label_ar'] = 'الحصة جارية الآن'
            if not current_session:
                current_session = slot_info
        elif now_min < (slot_start_min - 35):
            diff = slot_start_min - now_min
            if diff < 60:
                diff_str = f"Dans {diff} min"
            else:
                dh = diff // 60
                dm = diff % 60
                diff_str = f"Dans {dh}h{dm:02d}" if dm else f"Dans {dh}h"
            slot_info['timing_state'] = 'upcoming'
            slot_info['status_label_fr'] = f"{diff_str} (à {slot.start_time})"
            slot_info['status_label_ar'] = f"بعد {diff} دقيقة"
            slot_info['minutes_until'] = diff
            if diff < next_diff_min:
                next_diff_min = diff
                next_session = slot_info
        else:
            diff = now_min - slot_end_min
            if diff < 60:
                diff_str = f"Terminée il y a {diff} min"
            else:
                dh = diff // 60
                dm = diff % 60
                diff_str = f"Terminée il y a {dh}h{dm:02d}" if dm else f"Terminée il y a {dh}h"
            slot_info['timing_state'] = 'passed'
            slot_info['status_label_fr'] = f"{diff_str} (fin à {slot.end_time})"
            slot_info['status_label_ar'] = f"انتهت الحصة في {slot.end_time}"
            slot_info['minutes_ago'] = diff
            if diff < prev_diff_min:
                prev_diff_min = diff
                previous_session = slot_info

        all_sessions_today.append(slot_info)

    all_sessions_today.sort(key=lambda s: s['start_time'])

    has_classes_today = len(all_sessions_today) > 0
    pillar3_seances = {
        'has_classes_today': has_classes_today,
        'today_name_fr': today_fr,
        'today_name_ar': today_ar,
        'current_session': current_session,
        'next_session': next_session,
        'previous_session': previous_session,
        'all_sessions': all_sessions_today
    }

    # --- GATE VERDICT (NADRA CHAMILA) ---
    if not is_enrolled:
        verdict = {
            'status': 'not_enrolled',
            'badge_class': 'danger',
            'icon': '⛔',
            'title_fr': 'ÉLÈVE NON INSCRIT',
            'title_ar': 'تلميذ غير مسجل',
            'message_fr': 'Aucune inscription active trouvée dans le système.',
            'message_ar': 'لا يوجد أي تسجيل نشط للتلميذ بالمعهد.',
            'action_advice_fr': 'Veuillez orienter l\'élève vers l\'administration / secrétariat.',
            'action_advice_ar': 'يرجى توجيه التلميذ إلى إدارة المعهد للتسجيل.'
        }
    elif not is_paid:
        verdict = {
            'status': 'unpaid',
            'badge_class': 'warning',
            'icon': '⚠️',
            'title_fr': f"PAIEMENT EN ATTENTE — {total_balance_due:.0f} DH DÛ",
            'title_ar': f"باقي عليه واجب الأداء ({total_balance_due:.0f} درهم)",
            'message_fr': f"L'élève a un reste à payer de {total_balance_due:.0f} DH.",
            'message_ar': f"التلميذ بذمته مبلغ {total_balance_due:.0f} درهم غير مؤدى.",
            'action_advice_fr': 'Veuillez régulariser le paiement auprès du secrétariat avant accès.',
            'action_advice_ar': 'المرجو تسوية وضعية الأداء لدى سكرتارية المعهد.'
        }
    elif has_expired_enrollment:
        verdict = {
            'status': 'expired',
            'badge_class': 'warning',
            'icon': '⏳',
            'title_fr': 'ABONNEMENT EXPIRÉ',
            'title_ar': 'الاشتراك منتهي الصلاحية',
            'message_fr': 'L\'abonnement de formation est arrivé à échéance.',
            'message_ar': 'انتهت صلاحية اشتراك التلميذ في التكوين.',
            'action_advice_fr': 'Renouvellement nécessaire auprès de l\'administration.',
            'action_advice_ar': 'يتعين تجديد الاشتراك لدى إدارة المعهد.'
        }
    elif not has_classes_today:
        verdict = {
            'status': 'no_class_today',
            'badge_class': 'info',
            'icon': '🗓️',
            'title_fr': f"AUCUN COURS AUJOURD'HUI ({today_fr.upper()})",
            'title_ar': f"لا توجد أي حصة مبرمجة اليوم ({today_ar})",
            'message_fr': f"L'élève est en règle mais n'a aucune séance programmée le {today_fr}.",
            'message_ar': f"التلميذ مسجل وفي وضعية سليمة، لكن ليس لديه حصة اليوم ({today_ar}).",
            'action_advice_fr': 'Vérifier son emploi du temps des autres jours de la semaine.',
            'action_advice_ar': 'المرجو التحقق من جدول حصصه في باقي أيام الأسبوع.'
        }
    elif current_session:
        verdict = {
            'status': 'ok_current',
            'badge_class': 'success',
            'icon': '✅',
            'title_fr': f"ACCÈS AUTORISÉ — {current_session['room_name'].upper()}",
            'title_ar': f"الدخول مسموح — {current_session['room_name']}",
            'message_fr': f"Séance en cours : {current_session['course_name']} ({current_session['time_slot']})",
            'message_ar': f"الحصة جارية : {current_session['course_name']}",
            'action_advice_fr': f"Diriger l'élève vers {current_session['room_name']} (Enseignant : {current_session['teacher_name']})",
            'action_advice_ar': f"التوجه نحو {current_session['room_name']}"
        }
    elif next_session:
        verdict = {
            'status': 'ok_next',
            'badge_class': 'success',
            'icon': '✅',
            'title_fr': f"ACCÈS AUTORISÉ — COURS À {next_session['start_time']}",
            'title_ar': f"الدخول مسموح — الحصة في {next_session['start_time']}",
            'message_fr': f"Prochain cours : {next_session['course_name']} ({next_session['status_label_fr']})",
            'message_ar': f"الحصة القادمة : {next_session['course_name']}",
            'action_advice_fr': f"Salle : {next_session['room_name']} • Enseignant : {next_session['teacher_name']}",
            'action_advice_ar': f"القاعة : {next_session['room_name']}"
        }
    else:
        verdict = {
            'status': 'classes_finished',
            'badge_class': 'info',
            'icon': '🏁',
            'title_fr': 'SÉANCES DU JOUR TERMINÉES',
            'title_ar': 'انتهت حصص اليوم',
            'message_fr': f"Toutes les séances prévues le {today_fr} sont déjà terminées.",
            'message_ar': f"جميع حصص اليوم ({today_ar}) قد انتهت.",
            'action_advice_fr': 'Aucun autre cours programmé pour aujourd\'hui.',
            'action_advice_ar': 'لا توجد حصص أخرى لهذا اليوم.'
        }

    # Primary session for backward compatibility
    primary_session = current_session or next_session or previous_session
    primary_course_obj = enrollments[0].course if enrollments else None

    photo_url = url_for('static', filename=f"uploads/{student.photo}") if student.photo else None

    # Check if student was recorded present in class attendance today (Read-only check)
    existing_att = Attendance.query.filter_by(student_id=student.id, date=today).first()
    classroom_att_status = existing_att.status if existing_att else 'non_marque'

    return jsonify({
        'success': True,
        'student': {
            'id': student.id,
            'code': student.code or f"ETU{student.id:04d}",
            'full_name': student.full_name,
            'first_name': student.first_name or '',
            'last_name': student.last_name or '',
            'photo_url': photo_url,
            'school_level': student.school_level or '',
            'school_name': student.school_name or '',
            'age': student.age,
            'birth_date': student.birth_date.strftime('%d/%m/%Y') if student.birth_date else '',
            'cin': student.cin or '',
            'phone': student.phone or '',
            'whatsapp': student.whatsapp or '',
            'parent_name': student.parent_name or '',
            'parent_phone': student.parent_phone or '',
            'city': student.city or '',
            'notes': student.notes or '',
            'enrollments': all_enrollments_info
        },
        'gate_verdict': verdict,
        'pillar1_inscription': pillar1_inscription,
        'pillar2_paiement': pillar2_paiement,
        'pillar3_seances': pillar3_seances,
        # Backward-compatible fields
        'course': {
            'id': primary_session.get('course_id') if primary_session else (primary_course_obj.id if primary_course_obj else None),
            'title': primary_session.get('course_name') if primary_session else (primary_course_obj.display_name if primary_course_obj else 'Séance libre'),
            'room': primary_session.get('room_name') if primary_session else 'Salle libre',
            'teacher': primary_session.get('teacher_name') if primary_session else '—',
            'time_slot': primary_session.get('time_slot') if primary_session else 'Horaire libre',
            'is_scheduled_today': bool(primary_session)
        },
        'subscription': {
            'status': sub_status,
            'message_fr': sub_msg_fr,
            'message_ar': sub_msg_ar,
            'balance_due': total_balance_due,
            'end_date': latest_end_date
        },
        'attendance': {
            'action': 'kiosk_check_only',
            'classroom_status': classroom_att_status,
            'timestamp': now_dt.strftime('%H:%M:%S'),
            'date': today.strftime('%d/%m/%Y')
        },
        'stats': {
            'today_scans': Attendance.query.filter_by(date=today, status='present').count()
        }
    })



# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------
@app.route('/badges')
@login_required
@role_required('admin', 'secretary')
def badges():
    records = BadgeRecord.query.order_by(BadgeRecord.id.desc()).all()
    return render_template('badges/list.html', records=records,
                           students=Student.query.filter_by(status='active').all(),
                           courses=Course.query.filter_by(active=True).all())


@app.route('/badges/issue', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def badge_issue():
    b = BadgeRecord(student_id=_int(request.form.get('student_id')),
                    course_id=_int(request.form.get('course_id')) or None,
                    badge_type=request.form.get('badge_type', 'student'),
                    issue_date=parse_date(request.form.get('issue_date')) or date.today())
    db.session.add(b); db.session.commit(); flash('Badge créé', 'success')
    return redirect(url_for('badges'))


@app.route('/badges/print')
@login_required
@role_required('admin', 'secretary')
def badges_print():
    stu_id = _int(request.args.get('student_id'))
    stu_ids_param = request.args.get('student_ids', '')
    ids_param = request.args.get('ids', '')
    print_all = (request.args.get('all') == '1')

    students_to_print = []

    if stu_id:
        stu = Student.query.get(stu_id)
        if stu:
            students_to_print.append(stu)
    elif stu_ids_param:
        sids = [int(x) for x in stu_ids_param.split(',') if x.isdigit()]
        students_to_print = Student.query.filter(Student.id.in_(sids)).all()
    elif ids_param:
        recs = BadgeRecord.query.filter(BadgeRecord.id.in_([int(x) for x in ids_param.split(',') if x.isdigit()])).all()
        students_to_print = [b.student for b in recs if b.student]
    elif print_all:
        students_to_print = Student.query.filter_by(status='active').order_by(Student.last_name).all()
    else:
        students_to_print = Student.query.filter_by(status='active').order_by(Student.last_name).all()

    cards = []
    day_names = {0: 'Lundi', 1: 'Mardi', 2: 'Mercredi', 3: 'Jeudi', 4: 'Vendredi', 5: 'Samedi', 6: 'Dimanche'}
    for stu in students_to_print:
        qr = qr_data_uri(badge_qr_value(stu)) if stu else ''
        enrolls = Enrollment.query.filter_by(student_id=stu.id, status='active').all()
        courses = [e.course for e in enrolls if e.course]

        badge_courses = []
        for idx, c in enumerate(courses[:3]):
            lang_lower = (c.language or '').lower()
            name_lower = (c.name or '').lower()
            if 'ang' in lang_lower or 'eng' in lang_lower or 'ang' in name_lower or 'eng' in name_lower:
                tag = '[EN]'
                tag_color = '#a17816' if idx == 1 else ('#c0292b' if idx == 2 else '#0b1a30')
            elif 'esp' in lang_lower or 'span' in lang_lower or 'esp' in name_lower:
                tag = '[ES]'
                tag_color = '#c0292b' if idx == 2 else ('#a17816' if idx == 1 else '#0b1a30')
            elif 'all' in lang_lower or 'germ' in lang_lower or 'deutsch' in name_lower:
                tag = '[DE]'
                tag_color = '#a17816' if idx == 1 else ('#c0292b' if idx == 2 else '#0b1a30')
            elif 'arab' in lang_lower or 'arab' in name_lower:
                tag = '[AR]'
                tag_color = '#0b1a30'
            elif 'math' in name_lower:
                tag = '[MATH]'
                tag_color = '#0b1a30'
            elif 'pc' in name_lower or 'phys' in name_lower:
                tag = '[PC]'
                tag_color = '#a17816'
            elif 'svt' in name_lower:
                tag = '[SVT]'
                tag_color = '#c0292b'
            elif 'fr' in lang_lower or 'fr' in name_lower:
                tag = '[FR]'
                tag_color = '#0b1a30'
            else:
                tag = f"[{c.language[:2].upper()}]" if c.language else '[CRS]'
                tag_color = '#0b1a30'

            cls_color = 'gold' if idx == 1 else ('red' if idx == 2 else '')

            day_str = 'Samedi'
            if c.scheduled_days:
                days_list = [int(d.strip()) for d in c.scheduled_days.split(',') if d.strip().isdigit()]
                if days_list and days_list[0] in day_names:
                    day_str = day_names[days_list[0]]
            time_str = f"{day_str} • {c.session_duration or '1h30'}"
            if c.room:
                time_str += f" ({c.room.name})"
            else:
                time_str += f" (Salle 0{idx+1})"

            badge_courses.append({
                'tag': tag,
                'tag_color': tag_color,
                'class_color': cls_color,
                'name': c.display_name or c.name,
                'sub': f"Niveau {c.level}" if c.level else 'Formation continue',
                'group': c.group_name or f"Gr. 0{idx+1}",
                'schedule_sub': f"{(c.name or c.display_name)[:14]} :",
                'schedule_time': time_str
            })

        if not badge_courses:
            badge_courses.append({
                'tag': '[FR]',
                'tag_color': '#0b1a30',
                'class_color': '',
                'name': 'Formation Générale & Langues',
                'sub': 'Niveau Initial (A1-B1)',
                'group': 'Gr. 01',
                'schedule_sub': 'Formation :',
                'schedule_time': 'Samedi • 10h-12h (Salle 01)'
            })

        if len(courses) > 1:
            cursus = 'Multi-Langues' if any(c.category == 'language' for c in courses) else 'Multi-Disciplines'
        elif len(courses) == 1:
            cursus = courses[0].language or (courses[0].category.capitalize() if courses[0].category else 'Formation')
        else:
            cursus = stu.school_level or 'Formation Continue'

        exp_date = stu.end_date.strftime('%m/%Y') if stu.end_date else '08/2027'

        cards.append({
            'record': None,
            'student': stu,
            'course': courses[0] if courses else None,
            'courses': courses,
            'badge_courses': badge_courses,
            'cursus': cursus,
            'exp_date': exp_date,
            'qr': qr
        })

    conditions = SH.get_setting('badge_conditions', '')
    return render_template('badges/print.html', cards=cards, conditions=conditions)


@app.route('/badges/<int:bid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def badge_delete(bid):
    b = BadgeRecord.query.get_or_404(bid)
    db.session.delete(b); db.session.commit(); flash('Badge supprimé', 'success')
    return redirect(url_for('badges'))


def _calculate_period_teacher_payroll(start_d, end_d, selected_teacher_id=None, teacher_advances_list=None, teacher_deductions_list=None):
    today = date.today()
    target_months = set()
    if start_d and end_d:
        cur = date(start_d.year, start_d.month, 1)
        while cur <= end_d:
            target_months.add((cur.year, cur.month))
            _, num_days = calendar.monthrange(cur.year, cur.month)
            cur = cur + timedelta(days=num_days)
            cur = date(cur.year, cur.month, 1)
    elif start_d:
        target_months.add((start_d.year, start_d.month))
    elif end_d:
        target_months.add((end_d.year, end_d.month))
    else:
        target_months.add((today.year, today.month))

    sorted_months = sorted(target_months)
    all_teachers_list = Teacher.query.filter_by(active=True).order_by(Teacher.first_name.asc()).all()
    teachers_rows = []
    grand_teacher_payroll = 0.0

    for teacher in all_teachers_list:
        if selected_teacher_id and teacher.id != selected_teacher_id:
            continue
        details = []
        total_earned = 0.0

        assigned_cts = CourseTeacher.query.filter_by(teacher_id=teacher.id, is_active=True).all()
        assigned_courses = [ct.course for ct in assigned_cts if ct.course and ct.course.active]
        direct_courses = Course.query.filter_by(teacher_id=teacher.id, active=True).all()
        for c in direct_courses:
            if c not in assigned_courses:
                assigned_courses.append(c)

        for (ty, tm) in sorted_months:
            _, num_days_m = calendar.monthrange(ty, tm)
            for c in assigned_courses:
                all_c_enrolls = Enrollment.query.filter_by(course_id=c.id).filter(Enrollment.status != 'dropped').all()
                student_enrolls_map = {}
                for en in all_c_enrolls:
                    st = en.student
                    if not st:
                        continue
                    rev = calculate_enrollment_revenue_for_month(en, ty, tm)
                    if en.status == 'transferred':
                        if rev <= 0:
                            continue
                        has_active = Enrollment.query.filter_by(student_id=en.student_id, status='active').first()
                        if not has_active:
                            continue
                    else:
                        if not (rev > 0 or (en.enroll_date and en.enroll_date.year == ty and en.enroll_date.month == tm) or (en.end_date and en.end_date.year == ty and en.end_date.month == tm)):
                            continue

                    if st.id not in student_enrolls_map:
                        student_enrolls_map[st.id] = {'primary_enrollment': en, 'total_month_rev': 0.0}
                    student_enrolls_map[st.id]['total_month_rev'] += rev

                group_tuition_rev = sum(min(s_info['total_month_rev'], getattr(s_info['primary_enrollment'], 'unit_monthly_price', None) or s_info['primary_enrollment'].monthly_price or (c.unit_monthly_price if hasattr(c, 'unit_monthly_price') else (c.price_per_month or c.price or 300.0))) for s_info in student_enrolls_map.values() if s_info['total_month_rev'] > 0)
                month_students_count = len(student_enrolls_map)

                # Rémunération basée strictement sur la classe
                ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=teacher.id, is_active=True).first()
                if not ct:
                    ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=teacher.id).first()
                comp_type = ct.compensation_type if (ct and ct.compensation_type) else 'percentage'
                comp_val = ct.compensation_value if (ct and ct.compensation_value is not None) else 50.0

                earned = 0.0
                if comp_type == 'percentage':
                    earned = round(group_tuition_rev * (comp_val / 100.0), 2)
                elif comp_type == 'per_student':
                    earned = round(month_students_count * comp_val, 2)
                elif comp_type == 'fixed':
                    earned = round(comp_val, 2) if (group_tuition_rev > 0 or month_students_count > 0) else 0.0
                elif comp_type == 'hourly':
                    slots_count = ScheduleSlot.query.filter_by(course_id=c.id).count()
                    if slots_count == 0:
                        slots_count = c.sessions_per_week or 3
                    hrs = parse_duration_to_hours(c.session_duration)
                    scheduled_days = (c.scheduled_weekdays if hasattr(c, 'scheduled_weekdays') else None) or {0, 2, 4}
                    actual_sessions_in_month = sum(1 for d in range(1, num_days_m + 1) if date(ty, tm, d).weekday() in (scheduled_days or {0, 2, 4}))
                    if actual_sessions_in_month == 0:
                        actual_sessions_in_month = slots_count * 4
                    earned = round(actual_sessions_in_month * hrs * comp_val, 2) if (group_tuition_rev > 0 or month_students_count > 0) else 0.0

                if earned > 0 or month_students_count > 0:
                    total_earned += earned
                    details.append({
                        'course': c.display_name,
                        'month': f"{ty}-{tm:02d}",
                        'type': comp_type,
                        'value': comp_val,
                        'students': month_students_count,
                        'revenue': round(group_tuition_rev, 2),
                        'earned': round(earned, 2)
                    })

        t_advances = 0.0
        if teacher_advances_list:
            t_advances = sum((a.amount or 0.0) for a in teacher_advances_list if a.teacher_id == teacher.id)
        t_deductions = 0.0
        if teacher_deductions_list:
            t_deductions = sum((d.amount or 0.0) for d in teacher_deductions_list if d.teacher_id == teacher.id)
        net_payable = max(0.0, round(total_earned - t_advances - t_deductions, 2))

        grand_teacher_payroll += total_earned
        comp_label = f"{int(teacher.salary_amount) if teacher.salary_amount else 40}%" if (teacher.salary_type or 'percentage') == 'percentage' else f"{teacher.salary_type}"
        teachers_rows.append({
            'teacher': teacher,
            'name': teacher.full_name,
            'details': details,
            'groups_count': len(assigned_courses),
            'comp_label': comp_label,
            'payout': round(total_earned, 2),
            'total_earned': round(total_earned, 2),
            'advances': round(t_advances, 2),
            'deductions': round(t_deductions, 2),
            'net_payable': net_payable
        })

    return teachers_rows, round(grand_teacher_payroll, 2)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@app.route('/reports')
@login_required
@role_required('admin')
def reports():
    report = request.args.get('report', 'pnl').strip().lower()
    preset = request.args.get('preset', 'this_month').strip().lower()
    date_from_str = request.args.get('date_from', '').strip()
    date_to_str = request.args.get('date_to', '').strip()
    selected_teacher_id = _int(request.args.get('teacher_id'))
    selected_agent_id = _int(request.args.get('agent_id'))
    selected_method = request.args.get('method', 'all').strip().lower()
    selected_category = request.args.get('category', 'all').strip()
    q = request.args.get('q', '').strip()

    today = date.today()
    start_d = None
    end_d = None

    # Handle custom dates or presets
    if date_from_str or date_to_str:
        preset = 'custom'
        try:
            if date_from_str:
                start_d = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except Exception:
            start_d = None
        try:
            if date_to_str:
                end_d = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except Exception:
            end_d = None
    else:
        if preset == 'today':
            start_d = today
            end_d = today
        elif preset == 'last_7_days':
            start_d = today - timedelta(days=6)
            end_d = today
        elif preset == 'last_30_days':
            start_d = today - timedelta(days=29)
            end_d = today
        elif preset == 'this_month':
            start_d = date(today.year, today.month, 1)
            _, num_days = calendar.monthrange(today.year, today.month)
            end_d = date(today.year, today.month, num_days)
        elif preset == 'last_month':
            first_this_month = date(today.year, today.month, 1)
            last_prev_month = first_this_month - timedelta(days=1)
            start_d = date(last_prev_month.year, last_prev_month.month, 1)
            end_d = last_prev_month
        elif preset == 'this_year':
            start_d = date(today.year, 1, 1)
            end_d = date(today.year, 12, 31)
        elif preset == 'all':
            start_d = None
            end_d = None
        else:
            preset = 'this_month'
            start_d = date(today.year, today.month, 1)
            _, num_days = calendar.monthrange(today.year, today.month)
            end_d = date(today.year, today.month, num_days)

    date_from_val = start_d.strftime('%Y-%m-%d') if start_d else ''
    date_to_val = end_d.strftime('%Y-%m-%d') if end_d else ''

    if start_d and end_d:
        if start_d == end_d:
            period_label = f"Le {start_d.strftime('%d/%m/%Y')}"
        else:
            period_label = f"Du {start_d.strftime('%d/%m/%Y')} au {end_d.strftime('%d/%m/%Y')}"
    elif start_d:
        period_label = f"À partir du {start_d.strftime('%d/%m/%Y')}"
    elif end_d:
        period_label = f"Jusqu'au {end_d.strftime('%d/%m/%Y')}"
    else:
        period_label = "Tout l'historique comptable"

    # --- 1. PAYMENTS QUERY ---
    pay_query = Payment.query
    if start_d:
        pay_query = pay_query.filter(Payment.date >= start_d)
    if end_d:
        pay_query = pay_query.filter(Payment.date <= end_d)
    if selected_method and selected_method != 'all':
        pay_query = pay_query.filter(Payment.method == selected_method)
    if selected_teacher_id:
        pay_query = pay_query.join(Enrollment, Payment.enrollment_id == Enrollment.id)\
                             .join(Course, Enrollment.course_id == Course.id)\
                             .filter(Course.teacher_id == selected_teacher_id)
    if q:
        like_q = f"%{q}%"
        pay_query = pay_query.join(Student, Payment.student_id == Student.id, isouter=True)\
                             .filter(db.or_(Payment.receipt.ilike(like_q),
                                            Student.first_name.ilike(like_q),
                                            Student.last_name.ilike(like_q),
                                            Payment.note.ilike(like_q)))

    # --- 2. BOOK SALES QUERY ---
    books_query = BookSale.query
    if start_d:
        books_query = books_query.filter(BookSale.sale_date >= start_d)
    if end_d:
        books_query = books_query.filter(BookSale.sale_date <= end_d)
    if selected_method and selected_method != 'all':
        books_query = books_query.filter(BookSale.payment_method == selected_method)
    if q:
        like_q = f"%{q}%"
        books_query = books_query.join(Student, BookSale.student_id == Student.id, isouter=True)\
                                 .join(Book, BookSale.book_id == Book.id, isouter=True)\
                                 .filter(db.or_(BookSale.receipt_no.ilike(like_q),
                                                Book.title.ilike(like_q),
                                                Student.first_name.ilike(like_q),
                                                Student.last_name.ilike(like_q)))

    # Pre-filter snapshot for Agents Breakdown
    pre_agent_payments = pay_query.all()
    pre_agent_books = books_query.all() if not selected_teacher_id else []

    users_map = {u.id: u for u in User.query.all()}
    all_agents_list = User.query.filter(User.role.in_(['admin', 'secretary'])).order_by(User.full_name.asc(), User.username.asc()).all()

    agent_stats = {}
    for p in pre_agent_payments:
        uid = p.recorded_by or 0
        if uid not in agent_stats:
            u = users_map.get(uid)
            agent_stats[uid] = {
                'user_id': uid,
                'username': u.username if u else ('Système' if uid == 0 else f'Agent #{uid}'),
                'full_name': getattr(u, 'full_name', '') or (u.username if u else ('Système' if uid == 0 else f'Agent #{uid}')),
                'role': u.role if u else 'N/A',
                'payments_count': 0,
                'payments_amount': 0.0,
                'books_count': 0,
                'books_amount': 0.0,
                'total_collected': 0.0,
                'cash_amount': 0.0,
                'transfer_amount': 0.0,
                'card_amount': 0.0,
                'online_amount': 0.0
            }
        amt = p.amount or 0.0
        agent_stats[uid]['payments_count'] += 1
        agent_stats[uid]['payments_amount'] += amt
        agent_stats[uid]['total_collected'] += amt
        m = (p.method or '').lower()
        if m == 'cash':
            agent_stats[uid]['cash_amount'] += amt
        elif m == 'transfer':
            agent_stats[uid]['transfer_amount'] += amt
        elif m == 'card':
            agent_stats[uid]['card_amount'] += amt
        elif m == 'online':
            agent_stats[uid]['online_amount'] += amt

    for b in pre_agent_books:
        uid = b.recorded_by or 0
        if uid not in agent_stats:
            u = users_map.get(uid)
            agent_stats[uid] = {
                'user_id': uid,
                'username': u.username if u else ('Système' if uid == 0 else f'Agent #{uid}'),
                'full_name': getattr(u, 'full_name', '') or (u.username if u else ('Système' if uid == 0 else f'Agent #{uid}')),
                'role': u.role if u else 'N/A',
                'payments_count': 0,
                'payments_amount': 0.0,
                'books_count': 0,
                'books_amount': 0.0,
                'total_collected': 0.0,
                'cash_amount': 0.0,
                'transfer_amount': 0.0,
                'card_amount': 0.0,
                'online_amount': 0.0
            }
        b_amt = b.total_amount or 0.0
        agent_stats[uid]['books_count'] += 1
        agent_stats[uid]['books_amount'] += b_amt
        agent_stats[uid]['total_collected'] += b_amt
        bm = (b.payment_method or '').lower()
        if bm == 'cash':
            agent_stats[uid]['cash_amount'] += b_amt
        elif bm == 'transfer':
            agent_stats[uid]['transfer_amount'] += b_amt

    tot_unfiltered_rev = sum(a['total_collected'] for a in agent_stats.values())
    agents_performance = sorted(agent_stats.values(), key=lambda x: x['total_collected'], reverse=True)
    for a in agents_performance:
        a['pct'] = round((a['total_collected'] / tot_unfiltered_rev * 100), 1) if tot_unfiltered_rev > 0 else 0.0

    # Apply agent filter if specified
    if selected_agent_id is not None and selected_agent_id != 0:
        pay_query = pay_query.filter(Payment.recorded_by == selected_agent_id)
        if not selected_teacher_id:
            books_query = books_query.filter(BookSale.recorded_by == selected_agent_id)

    payments_list = pay_query.order_by(Payment.date.desc(), Payment.id.desc()).all()
    period_tuition_revenue = round(sum((p.amount or 0.0) for p in payments_list), 2)

    if selected_teacher_id or (selected_agent_id and selected_agent_id not in [b.recorded_by for b in pre_agent_books]):
        book_sales_list = [] if selected_teacher_id else books_query.order_by(BookSale.sale_date.desc(), BookSale.id.desc()).all()
    else:
        book_sales_list = books_query.order_by(BookSale.sale_date.desc(), BookSale.id.desc()).all()
    period_books_gross = round(sum((b.total_amount or 0.0) for b in book_sales_list), 2)
    period_books_teacher_due = round(sum((b.teacher_earned or 0.0) for b in book_sales_list), 2)
    period_books_revenue = round(sum(
        ((b.school_earned if b.teacher_id is not None else b.total_amount) or 0.0)
        for b in book_sales_list
    ), 2)

    # --- PÔLE D'ACTIVITÉ REVENUE BREAKDOWN ---
    pole_counts = {'language': 0, 'tutoring': 0, 'books': 0, 'other': 0}
    pole_amounts = {'language': 0.0, 'tutoring': 0.0, 'books': 0.0, 'other': 0.0}

    for p in payments_list:
        amt = p.amount or 0.0
        cat = 'other'
        if p.enrollment and p.enrollment.course:
            c_cat = (p.enrollment.course.category or '').lower()
            if 'lang' in c_cat:
                cat = 'language'
            elif 'tut' in c_cat or 'sout' in c_cat:
                cat = 'tutoring'
            else:
                cat = 'other'
        pole_amounts[cat] += amt
        pole_counts[cat] += 1

    pole_amounts['books'] = period_books_revenue
    pole_counts['books'] = len(book_sales_list)

    total_period_revenue = round(period_tuition_revenue + period_books_revenue, 2)

    pole_revenue_breakdown = [
        {
            'pole': 'language',
            'name': 'Pôle Langues Vivantes (Anglais, Français, Allemand...)',
            'icon': '🌍',
            'amount': round(pole_amounts['language'], 2),
            'count': pole_counts['language'],
            'pct': round((pole_amounts['language'] / total_period_revenue * 100), 1) if total_period_revenue > 0 else 0.0
        },
        {
            'pole': 'tutoring',
            'name': 'Pôle Soutien Scolaire & Renforcement',
            'icon': '🎓',
            'amount': round(pole_amounts['tutoring'], 2),
            'count': pole_counts['tutoring'],
            'pct': round((pole_amounts['tutoring'] / total_period_revenue * 100), 1) if total_period_revenue > 0 else 0.0
        },
        {
            'pole': 'books',
            'name': 'Vente de Manuels & Livres Scolaires',
            'icon': '📚',
            'amount': round(pole_amounts['books'], 2),
            'count': pole_counts['books'],
            'pct': round((pole_amounts['books'] / total_period_revenue * 100), 1) if total_period_revenue > 0 else 0.0
        },
        {
            'pole': 'other',
            'name': 'Frais d\'inscription & Divers',
            'icon': '📝',
            'amount': round(pole_amounts['other'], 2),
            'count': pole_counts['other'],
            'pct': round((pole_amounts['other'] / total_period_revenue * 100), 1) if total_period_revenue > 0 else 0.0
        }
    ]

    # --- 3. EXPENSES QUERY ---
    exp_query = Expense.query
    if start_d:
        exp_query = exp_query.filter(Expense.date >= start_d)
    if end_d:
        exp_query = exp_query.filter(Expense.date <= end_d)
    if selected_category and selected_category != 'all':
        exp_query = exp_query.filter(Expense.category == selected_category)
    if selected_teacher_id:
        exp_query = exp_query.filter(Expense.teacher_id == selected_teacher_id)
    if q:
        like_q = f"%{q}%"
        exp_query = exp_query.filter(db.or_(Expense.description.ilike(like_q),
                                            Expense.supplier_name.ilike(like_q),
                                            Expense.reference_no.ilike(like_q),
                                            Expense.invoice_no.ilike(like_q),
                                            Expense.category.ilike(like_q)))

    expenses_list = exp_query.order_by(Expense.date.desc(), Expense.id.desc()).all()
    period_expenses_total = round(sum((e.amount or 0.0) for e in expenses_list), 2)
    period_achats_total = round(sum((e.amount or 0.0) for e in expenses_list if e.expense_type == 'achat'), 2)
    period_charges_total = round(sum((e.amount or 0.0) for e in expenses_list if e.expense_type == 'charge'), 2)
    period_cash_outflow = round(sum((e.amount or 0.0) for e in expenses_list if e.payment_method != 'Retenue sur salaire'), 2)
    period_withholding_total = round(sum((e.amount or 0.0) for e in expenses_list if e.payment_method == 'Retenue sur salaire'), 2)

    # --- 4. MACRO P&L CALCULATIONS ---
    period_net_profit = round(total_period_revenue - period_expenses_total, 2)
    period_margin_pct = round((period_net_profit / total_period_revenue * 100), 1) if total_period_revenue > 0 else 0.0
    period_net_cash_flow = round(total_period_revenue - period_cash_outflow, 2)

    # --- 4b. TEACHERS PAYROLL & DEDUCTIONS FOR PERIOD ---
    adv_query = TeacherAdvance.query
    if start_d:
        adv_query = adv_query.filter(TeacherAdvance.date >= start_d)
    if end_d:
        adv_query = adv_query.filter(TeacherAdvance.date <= end_d)
    if selected_teacher_id:
        adv_query = adv_query.filter(TeacherAdvance.teacher_id == selected_teacher_id)
    teacher_advances_list = adv_query.order_by(TeacherAdvance.date.desc(), TeacherAdvance.id.desc()).all()

    te_query = TeacherExpense.query
    if start_d:
        te_query = te_query.filter(TeacherExpense.date >= start_d)
    if end_d:
        te_query = te_query.filter(TeacherExpense.date <= end_d)
    if selected_teacher_id:
        te_query = te_query.filter(TeacherExpense.teacher_id == selected_teacher_id)
    teacher_deductions_list = te_query.order_by(TeacherExpense.date.desc(), TeacherExpense.id.desc()).all()

    all_teachers_list = Teacher.query.filter_by(active=True).order_by(Teacher.first_name.asc()).all()
    teachers_rows, grand_teacher_payroll = _calculate_period_teacher_payroll(
        start_d, end_d,
        selected_teacher_id=selected_teacher_id,
        teacher_advances_list=teacher_advances_list,
        teacher_deductions_list=teacher_deductions_list
    )

    req_month_rep = start_d.strftime('%Y-%m') if start_d else date.today().strftime('%Y-%m')
    t_payouts_rep = TeacherSalaryPayout.query.filter_by(period_month=req_month_rep, status='paid').all()
    t_paid_rep = sum((p.net_amount or 0.0) for p in t_payouts_rep)
    pending_teacher_payroll = max(0.0, round(grand_teacher_payroll - t_paid_rep, 2))

    # --- 4c. RECURRING CHARGES INTEGRATION IN P&L ("FEN WASLIN") ---
    active_rcs = RecurringCharge.query.filter_by(active=True).all()
    total_rc_monthly_budget = round(sum((rc.amount or 0.0) for rc in active_rcs), 2)

    validated_rc_expenses = [e for e in expenses_list if e.recurring_charge_id is not None]
    validated_rc_amount = round(sum((e.amount or 0.0) for e in validated_rc_expenses), 2)
    validated_rc_count = len(validated_rc_expenses)

    pending_rc_amount = max(0.0, round(total_rc_monthly_budget - validated_rc_amount, 2))
    pending_rc_count = max(0, len(active_rcs) - validated_rc_count)

    pending_supplier_debts = round(sum((e.remaining_balance or 0.0) for e in expenses_list if e.status in ['unpaid', 'partial']), 2)
    total_pending_all_charges = round(pending_rc_amount + pending_teacher_payroll + pending_supplier_debts, 2)
    projected_total_expenses = round(period_expenses_total + total_pending_all_charges, 2)

    real_cash_val_rep = SH.get_setting(f"real_cash_amount_{req_month_rep}", "")
    real_cash_amount_rep = float(real_cash_val_rep) if real_cash_val_rep not in ['', None] else None
    real_cash_note_rep = SH.get_setting(f"real_cash_note_{req_month_rep}", "")
    real_cash_date_rep = SH.get_setting(f"real_cash_date_{req_month_rep}", "")

    if real_cash_amount_rep is not None:
        effective_cash_rep = real_cash_amount_rep
        ecart_caisse_rep = round(period_net_profit - real_cash_amount_rep, 2)
        projected_net_profit = round(effective_cash_rep - total_pending_all_charges, 2)
        projected_margin_pct = round((projected_net_profit / total_period_revenue * 100), 1) if total_period_revenue > 0 else 0.0
        is_real_cash_used_rep = True
    else:
        effective_cash_rep = period_net_profit
        ecart_caisse_rep = 0.0
        projected_net_profit = round(total_period_revenue - projected_total_expenses, 2)
        projected_margin_pct = round((projected_net_profit / total_period_revenue * 100), 1) if total_period_revenue > 0 else 0.0
        is_real_cash_used_rep = False

    rc_by_cat = {}
    for rc in active_rcs:
        c_name = rc.category or 'Autre'
        rc_by_cat[c_name] = rc_by_cat.get(c_name, 0.0) + (rc.amount or 0.0)

    recurring_pnl_data = {
        'total_budget': total_rc_monthly_budget,
        'validated_amount': validated_rc_amount,
        'validated_count': validated_rc_count,
        'pending_amount': pending_rc_amount,
        'pending_count': pending_rc_count,
        'grand_teacher_payroll': grand_teacher_payroll,
        'paid_teacher_payroll': t_paid_rep,
        'pending_teacher_payroll': pending_teacher_payroll,
        'pending_supplier_debts': pending_supplier_debts,
        'total_pending_all_charges': total_pending_all_charges,
        'projected_total_expenses': projected_total_expenses,
        'projected_net_profit': projected_net_profit,
        'projected_margin_pct': projected_margin_pct,
        'real_cash_amount': real_cash_amount_rep,
        'real_cash_note': real_cash_note_rep,
        'real_cash_date': real_cash_date_rep,
        'effective_cash': effective_cash_rep,
        'ecart_caisse': ecart_caisse_rep,
        'is_real_cash_used': is_real_cash_used_rep,
        'by_category': rc_by_cat,
        'all_rcs': active_rcs
    }

    # --- 5. PAYMENT METHODS BREAKDOWN ---
    methods_data = []
    method_configs = [
        ('cash', 'Espèces (Cash)', '💵'),
        ('transfer', 'Virement bancaire', '🏦'),
        ('card', 'Carte bancaire', '💳'),
        ('online', 'Paiement en ligne', '🌐')
    ]
    for m_code, m_label, m_icon in method_configs:
        m_payments = [p for p in payments_list if p.method == m_code]
        m_tot = round(sum((p.amount or 0.0) for p in m_payments), 2)
        m_cnt = len(m_payments)
        m_pct = round((m_tot / period_tuition_revenue * 100), 1) if period_tuition_revenue > 0 else 0.0
        methods_data.append({
            'method': m_code,
            'label': m_label,
            'icon': m_icon,
            'count': m_cnt,
            'total': m_tot,
            'pct': m_pct
        })

    # --- 6. EXPENSE CATEGORIES BREAKDOWN ---
    category_map = {}
    for e in expenses_list:
        cat_key = e.category or 'Autre'
        category_map[cat_key] = category_map.get(cat_key, 0.0) + (e.amount or 0.0)
    sorted_categories = sorted(category_map.items(), key=lambda x: x[1], reverse=True)
    expense_categories_breakdown = []
    for cat_name, cat_amt in sorted_categories:
        cat_pct = round((cat_amt / period_expenses_total * 100), 1) if period_expenses_total > 0 else 0.0
        expense_categories_breakdown.append({
            'category': cat_name,
            'amount': round(cat_amt, 2),
            'pct': cat_pct
        })

    # --- 7. DAILY CASHFLOW TIMELINE ---
    daily_map = {}
    for p in payments_list:
        d_key = p.date
        if d_key:
            if d_key not in daily_map:
                daily_map[d_key] = {'inflow': 0.0, 'outflow': 0.0, 'payments_count': 0, 'expenses_count': 0}
            daily_map[d_key]['inflow'] += (p.amount or 0.0)
            daily_map[d_key]['payments_count'] += 1

    for b in book_sales_list:
        d_key = b.sale_date
        if d_key:
            if d_key not in daily_map:
                daily_map[d_key] = {'inflow': 0.0, 'outflow': 0.0, 'payments_count': 0, 'expenses_count': 0}
            daily_map[d_key]['inflow'] += (b.total_amount or 0.0)

    for e in expenses_list:
        d_key = e.date
        if d_key:
            if d_key not in daily_map:
                daily_map[d_key] = {'inflow': 0.0, 'outflow': 0.0, 'payments_count': 0, 'expenses_count': 0}
            daily_map[d_key]['outflow'] += (e.amount or 0.0)
            daily_map[d_key]['expenses_count'] += 1

    daily_timeline = []
    weekday_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    for d_key in sorted(daily_map.keys(), reverse=True):
        in_val = round(daily_map[d_key]['inflow'], 2)
        out_val = round(daily_map[d_key]['outflow'], 2)
        daily_timeline.append({
            'date': d_key,
            'formatted_date': d_key.strftime('%d/%m/%Y'),
            'weekday': weekday_fr[d_key.weekday()],
            'inflow': in_val,
            'outflow': out_val,
            'net': round(in_val - out_val, 2),
            'payments_count': daily_map[d_key]['payments_count'],
            'expenses_count': daily_map[d_key]['expenses_count'],
        })

    # --- 8. COURSES PERFORMANCE ---
    courses_perf = []
    course_q = Course.query.filter_by(active=True)
    if selected_teacher_id:
        course_q = course_q.filter(Course.teacher_id == selected_teacher_id)

    for c in course_q.all():
        cnt = c.enrolled_count
        cap = c.max_students or 20
        fill_pct = min(100, round((cnt / cap) * 100)) if cap else 0

        c_pay_q = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))\
                            .join(Enrollment, Payment.enrollment_id == Enrollment.id)\
                            .filter(Enrollment.course_id == c.id)
        if start_d:
            c_pay_q = c_pay_q.filter(Payment.date >= start_d)
        if end_d:
            c_pay_q = c_pay_q.filter(Payment.date <= end_d)
        period_c_rev = c_pay_q.scalar() or 0.0

        all_time_rev = (db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))
                       .join(Enrollment, Payment.enrollment_id == Enrollment.id)
                       .filter(Enrollment.course_id == c.id).scalar() or 0.0)

        courses_perf.append({
            'course': c,
            'name': c.name,
            'category': c.category,
            'teacher': c.teacher.full_name if c.teacher else 'Sans prof',
            'room': c.room.name if c.room else 'Non assignée',
            'enrolled': cnt,
            'capacity': cap,
            'fill_pct': fill_pct,
            'period_revenue': round(period_c_rev, 2),
            'revenue': round(all_time_rev, 2)
        })
    courses_perf.sort(key=lambda x: x['period_revenue'], reverse=True)

    # --- 9. TEACHERS ADVANCES & DEDUCTIONS WITH DATES ---
    # NOTE: teacher_advances_list, teacher_deductions_list, all_teachers_list,
    # teachers_rows and grand_teacher_payroll are already computed in section 4b above.
    # No re-calculation needed here — we just reuse those variables for the display tables.

    # --- 10. ENROLLMENTS IN THE PERIOD WITH DATES ---
    enr_query = Enrollment.query
    if start_d:
        enr_query = enr_query.filter(Enrollment.enroll_date >= start_d)
    if end_d:
        enr_query = enr_query.filter(Enrollment.enroll_date <= end_d)
    if selected_teacher_id:
        enr_query = enr_query.join(Course, Enrollment.course_id == Course.id)\
                             .filter(Course.teacher_id == selected_teacher_id)
    period_enrollments_list = enr_query.order_by(Enrollment.enroll_date.desc(), Enrollment.id.desc()).all()

    enrollment_stats = [
        {'status': 'active', 'label': 'Inscriptions Actives (🟢)', 'count': Enrollment.query.filter_by(status='active').count()},
        {'status': 'paused', 'label': 'Abonnements Gelés (⏸️)', 'count': Enrollment.query.filter_by(status='paused').count()},
        {'status': 'completed', 'label': 'Formations Terminées (🏁)', 'count': Enrollment.query.filter_by(status='completed').count()},
        {'status': 'dropped', 'label': 'Désistements (🚪)', 'count': Enrollment.query.filter_by(status='dropped').count()},
    ]

    total_active_students = Student.query.filter_by(status='active').count()
    total_active_enrollments = Enrollment.query.filter_by(status='active').count()
    total_active_courses = Course.query.filter_by(active=True).count()
    total_teachers = Teacher.query.filter_by(active=True).count()

    return render_template('reports.html',
                           report=report,
                           preset=preset,
                           date_from=date_from_val,
                           date_to=date_to_val,
                           period_label=period_label,
                           selected_teacher_id=selected_teacher_id,
                           selected_method=selected_method,
                           selected_category=selected_category,
                           q=q,
                           all_teachers=all_teachers_list,
                           all_categories=ALL_EXPENSE_CATEGORIES,
                           period_tuition_revenue=period_tuition_revenue,
                           period_books_revenue=period_books_revenue,
                           period_books_gross=period_books_gross,
                           period_books_teacher_due=period_books_teacher_due,
                           total_period_revenue=total_period_revenue,
                           period_expenses_total=period_expenses_total,
                           period_achats_total=period_achats_total,
                           period_charges_total=period_charges_total,
                           period_cash_outflow=period_cash_outflow,
                           period_withholding_total=period_withholding_total,
                           period_net_profit=period_net_profit,
                           period_margin_pct=period_margin_pct,
                           period_net_cash_flow=period_net_cash_flow,
                           global_tuition_revenue=period_tuition_revenue,
                           global_books_revenue=period_books_revenue,
                           global_expenses_total=period_expenses_total,
                           global_total_revenue=total_period_revenue,
                           global_net_profit=period_net_profit,
                           grand_teacher_payroll=round(grand_teacher_payroll, 2),
                           total_active_students=total_active_students,
                           total_active_enrollments=total_active_enrollments,
                           total_active_courses=total_active_courses,
                           total_teachers=total_teachers,
                           payments_list=payments_list,
                           book_sales_list=book_sales_list,
                           expenses_list=expenses_list,
                           daily_timeline=daily_timeline,
                           methods_data=methods_data,
                           expense_categories_breakdown=expense_categories_breakdown,
                           courses_perf=courses_perf,
                           teachers_rows=teachers_rows,
                           teacher_advances_list=teacher_advances_list,
                           teacher_deductions_list=teacher_deductions_list,
                           selected_agent_id=selected_agent_id,
                           all_agents=all_agents_list,
                           agents_performance=agents_performance,
                           pole_revenue_breakdown=pole_revenue_breakdown,
                           recurring_pnl_data=recurring_pnl_data,
                           period_enrollments_list=period_enrollments_list,
                           enrollment_stats=enrollment_stats)


@app.route('/reports/print')
@login_required
@role_required('admin')
def reports_print():
    fmt = request.args.get('format', 'a4_landscape')
    preset = request.args.get('preset', 'this_month').strip().lower()
    date_from_str = request.args.get('date_from', '').strip()
    date_to_str = request.args.get('date_to', '').strip()
    selected_teacher_id = _int(request.args.get('teacher_id'))
    selected_method = request.args.get('method', 'all').strip().lower()

    today = date.today()
    start_d = None
    end_d = None

    if date_from_str or date_to_str:
        preset = 'custom'
        try:
            if date_from_str:
                start_d = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except Exception:
            start_d = None
        try:
            if date_to_str:
                end_d = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except Exception:
            end_d = None
    else:
        if preset == 'today':
            start_d = today
            end_d = today
        elif preset == 'last_7_days':
            start_d = today - timedelta(days=6)
            end_d = today
        elif preset == 'last_30_days':
            start_d = today - timedelta(days=29)
            end_d = today
        elif preset == 'this_month':
            start_d = date(today.year, today.month, 1)
            _, num_days = calendar.monthrange(today.year, today.month)
            end_d = date(today.year, today.month, num_days)
        elif preset == 'last_month':
            first_this_month = date(today.year, today.month, 1)
            last_prev_month = first_this_month - timedelta(days=1)
            start_d = date(last_prev_month.year, last_prev_month.month, 1)
            end_d = last_prev_month
        elif preset == 'this_year':
            start_d = date(today.year, 1, 1)
            end_d = date(today.year, 12, 31)
        elif preset == 'all':
            start_d = None
            end_d = None
        else:
            preset = 'this_month'
            start_d = date(today.year, today.month, 1)
            _, num_days = calendar.monthrange(today.year, today.month)
            end_d = date(today.year, today.month, num_days)

    if start_d and end_d:
        if start_d == end_d:
            period_label = f"Le {start_d.strftime('%d/%m/%Y')}"
        else:
            period_label = f"Du {start_d.strftime('%d/%m/%Y')} au {end_d.strftime('%d/%m/%Y')}"
    elif start_d:
        period_label = f"À partir du {start_d.strftime('%d/%m/%Y')}"
    elif end_d:
        period_label = f"Jusqu'au {end_d.strftime('%d/%m/%Y')}"
    else:
        period_label = "Tout l'historique comptable"

    # Filtered Payments
    pay_query = Payment.query
    if start_d:
        pay_query = pay_query.filter(Payment.date >= start_d)
    if end_d:
        pay_query = pay_query.filter(Payment.date <= end_d)
    if selected_method and selected_method != 'all':
        pay_query = pay_query.filter(Payment.method == selected_method)
    if selected_teacher_id:
        pay_query = pay_query.join(Enrollment, Payment.enrollment_id == Enrollment.id)\
                             .join(Course, Enrollment.course_id == Course.id)\
                             .filter(Course.teacher_id == selected_teacher_id)
    payments_list = pay_query.order_by(Payment.date.desc(), Payment.id.desc()).all()
    period_tuition_revenue = round(sum((p.amount or 0.0) for p in payments_list), 2)

    # Filtered Books
    books_query = BookSale.query
    if start_d:
        books_query = books_query.filter(BookSale.sale_date >= start_d)
    if end_d:
        books_query = books_query.filter(BookSale.sale_date <= end_d)
    if selected_method and selected_method != 'all':
        books_query = books_query.filter(BookSale.payment_method == selected_method)
    if selected_teacher_id:
        book_sales_list = []
    else:
        book_sales_list = books_query.order_by(BookSale.sale_date.desc(), BookSale.id.desc()).all()
    period_books_gross = round(sum((b.total_amount or 0.0) for b in book_sales_list), 2)
    period_books_teacher_due = round(sum((b.teacher_earned or 0.0) for b in book_sales_list), 2)
    period_books_revenue = round(sum(
        ((b.school_earned if b.teacher_id is not None else b.total_amount) or 0.0)
        for b in book_sales_list
    ), 2)

    # Filtered Expenses
    exp_query = Expense.query
    if start_d:
        exp_query = exp_query.filter(Expense.date >= start_d)
    if end_d:
        exp_query = exp_query.filter(Expense.date <= end_d)
    if selected_teacher_id:
        exp_query = exp_query.filter(Expense.teacher_id == selected_teacher_id)
    expenses_list = exp_query.order_by(Expense.date.desc(), Expense.id.desc()).all()
    period_expenses_total = round(sum((e.amount or 0.0) for e in expenses_list), 2)

    total_period_revenue = round(period_tuition_revenue + period_books_revenue, 2)
    period_net_profit = round(total_period_revenue - period_expenses_total, 2)
    period_margin_pct = round((period_net_profit / total_period_revenue * 100), 1) if total_period_revenue > 0 else 0.0

    total_active_students = Student.query.filter_by(status='active').count()
    total_active_enrollments = Enrollment.query.filter_by(status='active').count()
    total_active_courses = Course.query.filter_by(active=True).count()
    total_teachers = Teacher.query.filter_by(active=True).count()

    # Courses Performance
    courses_perf = []
    course_q = Course.query.filter_by(active=True)
    if selected_teacher_id:
        course_q = course_q.filter(Course.teacher_id == selected_teacher_id)
    for c in course_q.all():
        cnt = c.enrolled_count
        cap = c.max_students or 20
        fill_pct = min(100, round((cnt / cap) * 100)) if cap else 0
        c_pay_q = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))\
                            .join(Enrollment, Payment.enrollment_id == Enrollment.id)\
                            .filter(Enrollment.course_id == c.id)
        if start_d:
            c_pay_q = c_pay_q.filter(Payment.date >= start_d)
        if end_d:
            c_pay_q = c_pay_q.filter(Payment.date <= end_d)
        rev = c_pay_q.scalar() or 0.0
        courses_perf.append({
            'name': c.display_name,
            'teacher': c.teacher.full_name if c.teacher else 'Non assigné',
            'room': c.room.name if c.room else '—',
            'enrolled': cnt,
            'capacity': cap,
            'fill_pct': fill_pct,
            'price': c.price or 0.0,
            'revenue': round(rev, 2)
        })
    courses_perf.sort(key=lambda x: x['revenue'], reverse=True)

    # Methods stats
    methods_stats = []
    for m_key, m_lbl in [('cash', 'Espèces (Cash)'), ('transfer', 'Virement Bancaire'), ('card', 'Carte Bancaire'), ('online', 'En Ligne')]:
        m_payments = [p for p in payments_list if p.method == m_key]
        amt = round(sum((p.amount or 0.0) for p in m_payments), 2)
        cnt = len(m_payments)
        pct = round((amt / period_tuition_revenue * 100), 1) if period_tuition_revenue > 0 else 0.0
        methods_stats.append({'key': m_key, 'label': m_lbl, 'amount': amt, 'count': cnt, 'pct': pct})

    # Teachers compensation for the period
    teachers_rows, grand_teacher_payroll = _calculate_period_teacher_payroll(
        start_d, end_d,
        selected_teacher_id=selected_teacher_id
    )

    return render_template('reports_print.html',
                           fmt=fmt,
                           preset=preset,
                           period_label=period_label,
                           global_tuition_revenue=period_tuition_revenue,
                           global_books_revenue=period_books_revenue,
                           global_books_gross=period_books_gross,
                           global_books_teacher_due=period_books_teacher_due,
                           global_expenses_total=period_expenses_total,
                           global_total_revenue=total_period_revenue,
                           global_net_profit=period_net_profit,
                           period_margin_pct=period_margin_pct,
                           total_active_students=total_active_students,
                           total_active_enrollments=total_active_enrollments,
                           total_active_courses=total_active_courses,
                           total_teachers=total_teachers,
                           courses_perf=courses_perf,
                           methods_stats=methods_stats,
                           teachers_rows=teachers_rows,
                           grand_teacher_payroll=round(grand_teacher_payroll, 2),
                           payments_list=payments_list[:100],
                           expenses_list=expenses_list[:50],
                           today=date.today())


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
@app.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def settings():
    if request.method == 'POST':
        for key, val in request.form.items():
            if key.startswith('__'):
                continue
            SH.set_setting(key, val)
        db.session.commit()
        flash('Réglages enregistrés', 'success')
        return redirect(url_for('settings'))
    s = SH.all_settings_dict()
    return render_template('settings.html', s=s)


@app.route('/settings/reset', methods=['POST'])
@login_required
@role_required('admin')
def settings_reset():
    for k in SH.DEFAULTS:
        s = Setting.query.get(k)
        if s:
            db.session.delete(s)
    db.session.commit()
    SH.seed_defaults()
    flash('Réglages réinitialisés aux valeurs par défaut', 'success')
    return redirect(url_for('settings'))


@app.route('/settings/security')
@login_required
@role_required('admin', 'secretary')
def settings_security():
    blocked_ips = BlockedIP.query.order_by(BlockedIP.id.desc()).all()
    recent_attempts = LoginAttempt.query.order_by(LoginAttempt.id.desc()).limit(50).all()
    return render_template('security.html', blocked_ips=blocked_ips, attempts=recent_attempts)


@app.route('/settings/security/unblock/<int:bid>', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def settings_security_unblock(bid):
    blk = db.session.get(BlockedIP, bid)
    if blk:
        blk.is_blocked = False
        blk.failed_attempts = 0
        blk.blocked_until = None
        db.session.commit()
        flash(f"L'adresse IP {blk.ip_address} a été débloquée avec succès.", 'success')
    return redirect(url_for('settings_security'))


@app.route('/api/live_logins')
@login_required
@role_required('admin', 'secretary')
def api_live_logins():
    last_id = request.args.get('last_id', 0, type=int)
    max_id = db.session.query(db.func.max(LoginAttempt.id)).scalar() or 0

    if last_id > 0:
        new_attempts = LoginAttempt.query.filter(LoginAttempt.id > last_id).order_by(LoginAttempt.id.asc()).limit(20).all()
    else:
        new_attempts = []

    recent = LoginAttempt.query.order_by(LoginAttempt.id.desc()).limit(15).all()
    unread_cnt = SystemNotification.query.filter_by(is_read=False).count()

    def format_att(a):
        user_obj = User.query.filter(db.func.lower(User.username) == a.username.lower()).first() if a.username else None
        role_key = user_obj.role if user_obj else ('teacher' if 'prof' in (a.username or '').lower() else ('admin' if (a.username or '').lower() == 'admin' else 'user'))
        role_labels = {'admin': 'Administrateur', 'secretary': 'Secrétaire', 'teacher': 'Enseignant', 'user': 'Utilisateur'}
        role_display = role_labels.get(role_key, role_key.capitalize())
        full_name = user_obj.full_name if user_obj else (a.username or 'Inconnu')
        
        is_local = a.ip_address in ('127.0.0.1', 'localhost', '::1') or (a.ip_address and a.ip_address.startswith('192.168.'))

        attempt_dt = a.attempted_at or a.created_at
        time_str = attempt_dt.strftime('%H:%M:%S') if attempt_dt else '--:--:--'
        date_str = attempt_dt.strftime('%d/%m/%Y') if attempt_dt else '--/--/----'

        return {
            'id': a.id,
            'username': a.username or 'inconnu',
            'full_name': full_name,
            'role': role_key,
            'role_display': role_display,
            'ip_address': a.ip_address,
            'is_local': is_local,
            'success': bool(a.success),
            'time': time_str,
            'date': date_str
        }

    # New system notifications (absence alerts, teacher notes, ...) for live pop-ups
    last_notif_id = request.args.get('last_notif_id', type=int)
    notif_max_id = db.session.query(db.func.max(SystemNotification.id)).scalar() or 0
    new_notifs = []
    if last_notif_id is not None and last_notif_id >= 0:
        rows = SystemNotification.query.filter(
            SystemNotification.id > last_notif_id,
            SystemNotification.is_read == False
        ).order_by(SystemNotification.id.asc()).limit(10).all()
        for n in rows:
            new_notifs.append({
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'link': url_for('notification_read', nid=n.id),
                'time': n.created_at.strftime('%H:%M') if n.created_at else '',
            })

    return jsonify({
        'success': True,
        'max_id': max_id,
        'new_events': [format_att(a) for a in new_attempts],
        'recent': [format_att(a) for a in recent],
        'unread_notifications_count': unread_cnt,
        'notif_max_id': notif_max_id,
        'new_notifications': new_notifs
    })



# ---------------------------------------------------------------------------
# Books & School Manuals Inventory Management (الكتب والمقررات الدراسية)
# ---------------------------------------------------------------------------
@app.route('/books')
@login_required
@role_required('admin', 'secretary')
def books():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    stock_status = request.args.get('stock_status', '').strip()

    query = Book.query.filter_by(active=True)
    if q:
        query = query.filter(db.or_(
            Book.title.ilike(f'%{q}%'),
            Book.code.ilike(f'%{q}%'),
            Book.publisher.ilike(f'%{q}%'),
            Book.level.ilike(f'%{q}%')
        ))
    if category:
        query = query.filter_by(category=category)

    all_books = query.order_by(Book.category, Book.title).all()

    if stock_status == 'low':
        book_list = [b for b in all_books if b.is_low_stock and b.stock_quantity > 0]
    elif stock_status == 'out':
        book_list = [b for b in all_books if b.stock_quantity <= 0]
    else:
        book_list = all_books

    total_books_types = len(all_books)
    total_inventory_qty = sum(b.stock_quantity for b in all_books)
    total_stock_value = sum(b.stock_quantity * b.purchase_price for b in all_books)
    total_sales_potential = sum(b.stock_quantity * b.sale_price for b in all_books)
    low_stock_count = sum(1 for b in all_books if b.is_low_stock)

    recent_sales = BookSale.query.order_by(BookSale.sale_date.desc(), BookSale.id.desc()).limit(8).all()

    return render_template('books/list.html',
                           books=book_list,
                           q=q,
                           category=category,
                           stock_status=stock_status,
                           total_books_types=total_books_types,
                           total_inventory_qty=total_inventory_qty,
                           total_stock_value=total_stock_value,
                           total_sales_potential=total_sales_potential,
                           low_stock_count=low_stock_count,
                           recent_sales=recent_sales)


@app.route('/books/new', methods=['GET', 'POST'])
@app.route('/books/<int:bid>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def book_form(bid=None):
    book = Book.query.get(bid) if bid else None
    if request.method == 'POST':
        d = request.form
        if not book:
            code = d.get('code') or f"LIV-{Book.query.count() + 1:03d}"
            book = Book(code=code)
            db.session.add(book)
        else:
            if d.get('code'):
                book.code = d.get('code')

        book.title = d.get('title', '').strip()
        book.publisher = d.get('publisher', '').strip()
        book.category = d.get('category', 'language')
        book.level = d.get('level', '').strip()
        book.purchase_price = _f(d.get('purchase_price'))
        book.sale_price = _f(d.get('sale_price'))
        book.stock_quantity = _int(d.get('stock_quantity'))
        book.min_stock_alert = _int(d.get('min_stock_alert')) or 5
        book.notes = d.get('notes', '').strip()
        book.active = True

        # Teacher Deposition & Commission
        book.teacher_id = _int(d.get('teacher_id')) or None
        book.payout_type = d.get('payout_type', 'fixed')
        book.teacher_share = _f(d.get('teacher_share'))

        if not book.title or book.sale_price < 0:
            flash('Veuillez remplir correctement le titre et le prix de vente du manuel.', 'danger')
            teachers = Teacher.query.filter_by(active=True).order_by(Teacher.first_name).all()
            return render_template('books/form.html', book=book, teachers=teachers)

        db.session.commit()
        log_action('book_save', f"Book {book.code} {book.title}")
        flash(f"Manuel '{book.title}' enregistré avec succès !", 'success')
        return redirect(url_for('books'))

    teachers = Teacher.query.filter_by(active=True).order_by(Teacher.first_name).all()
    return render_template('books/form.html', book=book, teachers=teachers)


@app.route('/books/<int:bid>/restock', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def book_restock(bid):
    book = Book.query.get_or_404(bid)
    qty = _int(request.form.get('add_quantity'))
    if qty > 0:
        book.stock_quantity = (book.stock_quantity or 0) + qty
        db.session.commit()
        log_action('book_restock', f"Restocked +{qty} of {book.title}")
        flash(f"Stock mis à jour (+{qty} exemplaires pour '{book.title}'). Nouveau stock : {book.stock_quantity}", 'success')
    return redirect(url_for('books'))


@app.route('/books/<int:bid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def book_delete(bid):
    book = Book.query.get_or_404(bid)
    sales_count = BookSale.query.filter_by(book_id=bid).count()
    if sales_count > 0:
        book.active = False
        db.session.commit()
        flash(f"Le manuel '{book.title}' a été archivé car il contient un historique de {sales_count} vente(s).", 'warning')
    else:
        db.session.delete(book)
        db.session.commit()
        flash('Manuel supprimé avec succès.', 'success')
    return redirect(url_for('books'))


@app.route('/books/sell', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'secretary')
def book_sell():
    if request.method == 'POST':
        d = request.form
        book_id = _int(d.get('book_id'))
        student_id = _int(d.get('student_id')) or None
        qty = max(1, _int(d.get('quantity', 1)))
        pay_method = d.get('payment_method', 'cash')
        sale_dt = parse_date(d.get('sale_date')) or date.today()
        notes = d.get('notes', '').strip()

        book = Book.query.get_or_404(book_id)
        if book.stock_quantity < qty:
            flash(f"Stock insuffisant pour '{book.title}'. Stock disponible : {book.stock_quantity}", 'danger')
            return redirect(url_for('book_sell'))

        unit_price = _f(d.get('unit_price')) or book.sale_price
        total_amount = round(unit_price * qty, 2)

        # Decrement stock
        book.stock_quantity = max(0, book.stock_quantity - qty)

        # Calculate Teacher vs School Split
        split = book.calculate_split(unit_price)
        t_earned_total = round(split['teacher_earned'] * qty, 2)
        s_earned_total = round(split['school_earned'] * qty, 2)
        period_m = sale_dt.strftime('%Y-%m')

        rec_num = SH.next_invoice_number('receipt_prefix', 'next_receipt_number')
        u = current_user()
        sale = BookSale(
            receipt_no=rec_num,
            book_id=book.id,
            student_id=student_id,
            quantity=qty,
            unit_price=unit_price,
            total_amount=total_amount,
            payment_method=pay_method,
            sale_date=sale_dt,
            recorded_by=u.id if u else None,
            notes=notes,
            teacher_id=book.teacher_id,
            teacher_earned=t_earned_total,
            school_earned=s_earned_total,
            period_month=period_m
        )
        db.session.add(sale)

        # Also create a Payment entry so it reflects in daily cashflow
        note_teacher = f" [Prof. {book.teacher.full_name}: +{t_earned_total} DH]" if book.teacher else ""
        p = Payment(
            receipt=rec_num,
            student_id=student_id,
            amount=total_amount,
            method=pay_method,
            date=sale_dt,
            note=f"Vente Manuel: {book.title} (x{qty}){note_teacher}",
            recorded_by=u.id if u else None
        )
        db.session.add(p)

        db.session.commit()
        log_action('book_sale', f"Sold {qty}x {book.title} for {total_amount} DH (Receipt {rec_num})")
        flash(f"Vente enregistrée avec succès ({qty}x {book.title} - {total_amount} DH). Reçu N° {rec_num}", 'success')

        return redirect(url_for('payment_receipt', pid=p.id))

    pre_book_id = _int(request.args.get('book_id'))
    pre_student_id = _int(request.args.get('student_id'))

    books_avail = Book.query.filter_by(active=True).all()
    students_list = Student.query.filter_by(status='active').order_by(Student.first_name).all()

    return render_template('books/sale_form.html',
                           books=books_avail,
                           students=students_list,
                           pre_book_id=pre_book_id,
                           pre_student_id=pre_student_id,
                           today=date.today().strftime('%Y-%m-%d'))


@app.route('/books/sales')
@login_required
@role_required('admin', 'secretary')
def book_sales():
    q = request.args.get('q', '').strip()
    month = request.args.get('month', '').strip()
    req_user_id = _int(request.args.get('user_id'))

    query = BookSale.query.join(Book, BookSale.book_id == Book.id, isouter=True)\
                          .join(Student, BookSale.student_id == Student.id, isouter=True)

    cur_u = current_user()
    if cur_u and cur_u.role == 'secretary':
        req_user_id = cur_u.id
        query = query.filter(BookSale.recorded_by == cur_u.id)
    elif req_user_id:
        query = query.filter(BookSale.recorded_by == req_user_id)

    if q:
        q_clean = " ".join(q.split())
        tokens = q_clean.split()
        student_full_1 = db.func.coalesce(Student.first_name, '') + ' ' + db.func.coalesce(Student.last_name, '')
        student_full_2 = db.func.coalesce(Student.last_name, '') + ' ' + db.func.coalesce(Student.first_name, '')
        combined_target = student_full_1 + ' ' + student_full_2 + ' ' + db.func.coalesce(Student.code, '') + ' ' + db.func.coalesce(Book.title, '') + ' ' + db.func.coalesce(BookSale.receipt_no, '')
        all_tokens_match = db.and_(*[combined_target.ilike(f"%{t}%") for t in tokens])

        query = query.filter(db.or_(
            all_tokens_match,
            Book.title.ilike(f"%{q_clean}%"),
            BookSale.receipt_no.ilike(f"%{q_clean}%"),
            student_full_1.ilike(f"%{q_clean}%"),
            student_full_2.ilike(f"%{q_clean}%"),
            Student.first_name.ilike(f"%{q_clean}%"),
            Student.last_name.ilike(f"%{q_clean}%"),
            Student.code.ilike(f"%{q_clean}%")
        ))

    if month:
        try:
            y, m = map(int, month.split('-'))
            query = query.filter(
                db.extract('year', BookSale.sale_date) == y,
                db.extract('month', BookSale.sale_date) == m
            )
        except Exception:
            pass

    sales_list = query.order_by(BookSale.sale_date.desc(), BookSale.id.desc()).all()
    if cur_u and cur_u.role == 'secretary':
        staff_users = [cur_u]
    else:
        staff_users = User.query.filter(User.role.in_(['admin', 'secretary'])).order_by(User.full_name).all()
    total_sales_revenue = sum(s.total_amount for s in sales_list)
    total_items_sold = sum(s.quantity for s in sales_list)

    return render_template('books/sales_list.html',
                           sales=sales_list,
                           total_sales_revenue=total_sales_revenue,
                           total_items_sold=total_items_sold,
                           staff_users=staff_users,
                           req_user_id=req_user_id,
                           q=q,
                           month=month)


# ---------------------------------------------------------------------------
# Backups & Database Management (النسخ الاحتياطي وقاعدة البيانات)
# ---------------------------------------------------------------------------
@app.route('/settings/backups')
@login_required
@role_required('admin')
def settings_backups():
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    db_path = os.path.join(BASE, 'institut.db')
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    backup_files = []
    for f in sorted(os.listdir(BACKUPS_DIR), reverse=True):
        if f.endswith('.zip') or f.endswith('.db'):
            f_path = os.path.join(BACKUPS_DIR, f)
            st = os.stat(f_path)
            backup_files.append({
                'filename': f,
                'size': st.st_size,
                'created_at': datetime.fromtimestamp(st.st_mtime),
                'is_zip': f.endswith('.zip')
            })

    return render_template('backups.html',
                           backups=backup_files,
                           db_size=db_size,
                           db_path=db_path)


@app.route('/settings/backups/create', methods=['POST'])
@login_required
@role_required('admin')
def settings_backups_create():
    fn = create_auto_backup(reason='manual')
    if fn:
        log_action('backup_create', f"Manual backup created: {fn}")
        flash(f"Sauvegarde créée avec succès : {fn}", 'success')
    else:
        flash("Erreur lors de la création de la sauvegarde.", 'danger')
    return redirect(url_for('settings_backups'))


@app.route('/settings/backups/download/<path:filename>')
@login_required
@role_required('admin')
def settings_backups_download(filename):
    safe_fn = os.path.basename(filename)
    f_path = os.path.join(BACKUPS_DIR, safe_fn)
    if os.path.exists(f_path):
        return send_file(f_path, as_attachment=True, download_name=safe_fn)
    flash("Fichier de sauvegarde introuvable.", 'danger')
    return redirect(url_for('settings_backups'))


@app.route('/settings/backups/download_current_db')
@login_required
@role_required('admin')
def settings_backups_download_current():
    db_path = os.path.join(BASE, 'institut.db')
    if os.path.exists(db_path):
        fn = f"institut_live_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        return send_file(db_path, as_attachment=True, download_name=fn)
    flash("Base de données introuvable.", 'danger')
    return redirect(url_for('settings_backups'))


@app.route('/settings/backups/restore', methods=['POST'])
@login_required
@role_required('admin')
def settings_backups_restore():
    if 'backup_file' not in request.files:
        flash("Veuillez sélectionner un fichier de sauvegarde (.zip ou .db).", 'danger')
        return redirect(url_for('settings_backups'))

    f = request.files['backup_file']
    if not f or not f.filename:
        flash("Aucun fichier sélectionné.", 'danger')
        return redirect(url_for('settings_backups'))

    filename = secure_filename(f.filename)
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ('.zip', '.db'):
        flash("Format invalide. Seuls les fichiers .zip et .db sont acceptés.", 'danger')
        return redirect(url_for('settings_backups'))

    # 1. Pre-restore safety backup
    create_auto_backup(reason='pre_restore_safety')

    temp_save_path = os.path.join(BACKUPS_DIR, f"temp_upload_{filename}")
    f.save(temp_save_path)

    db_target = os.path.join(BASE, 'institut.db')

    try:
        if ext == '.zip':
            with zipfile.ZipFile(temp_save_path, 'r') as zf:
                if 'institut.db' in zf.namelist():
                    zf.extract('institut.db', BASE)
                else:
                    db_files = [m for m in zf.namelist() if m.endswith('.db')]
                    if db_files:
                        with zf.open(db_files[0]) as source, open(db_target, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    else:
                        flash("Le fichier ZIP ne contient aucune base de données valide.", 'danger')
                        if os.path.exists(temp_save_path):
                            os.remove(temp_save_path)
                        return redirect(url_for('settings_backups'))
        elif ext == '.db':
            shutil.copy2(temp_save_path, db_target)

        if os.path.exists(temp_save_path):
            os.remove(temp_save_path)

        auto_migrate_db()
        log_action('backup_restore', f"Database restored from {filename}")
        flash(f"Base de données restaurée avec succès depuis '{filename}' ! Une sauvegarde de sécurité pré-restauration a été enregistrée.", 'success')
    except Exception as e:
        flash(f"Erreur lors de la restauration : {e}", 'danger')

    return redirect(url_for('settings_backups'))


@app.route('/settings/backups/delete/<path:filename>', methods=['POST'])
@login_required
@role_required('admin')
def settings_backups_delete(filename):
    safe_fn = os.path.basename(filename)
    f_path = os.path.join(BACKUPS_DIR, safe_fn)
    if os.path.exists(f_path):
        os.remove(f_path)
        log_action('backup_delete', f"Backup deleted: {safe_fn}")
        flash(f"Sauvegarde '{safe_fn}' supprimée.", 'success')
    return redirect(url_for('settings_backups'))


# ---------------------------------------------------------------------------
# Visual & Printable Interactive User Guide (دليل الاستخدام الشامل والطباعة)
# ---------------------------------------------------------------------------
@app.route('/guide')
@login_required
@role_required('admin', 'secretary')
def user_guide():
    return render_template('guide.html')


# ---------------------------------------------------------------------------
# Excel / CSV Data Import & Export System (نظام استيراد البيانات من ملفات إكسيل)
# ---------------------------------------------------------------------------
def generate_excel_template_bytes(target):
    import io
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # remove default sheet

    header_fill = PatternFill(start_color="0B3D6E", end_color="0B3D6E", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center")

    thin = Side(border_style="thin", color="CBD5E1")
    border = Border(top=thin, left=thin, right=thin, bottom=thin)

    def add_sheet(sheet_title, headers, samples):
        ws = wb.create_sheet(title=sheet_title)
        ws.row_dimensions[1].height = 28
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = align_center
            cell.border = border

        for row_idx, row_data in enumerate(samples, 2):
            ws.row_dimensions[row_idx].height = 22
            for col_idx, val in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.alignment = align_left
                cell.border = border
                cell.font = Font(name="Calibri", size=10)

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

    # 1. Students Schema
    headers_stu = ['prenom', 'nom', 'genre', 'telephone', 'telephone_parent', 'nom_parent', 'niveau_scolaire', 'etablissement', 'cin', 'ville', 'adresse', 'date_naissance', 'remarques']
    samples_stu = [
        ['Karim', 'Benali', 'M', '0655443322', '0699887766', 'Mohamed Benali', '2Bac PC', 'Lycée Al Khawarizmi', 'BK123456', 'Deroua', 'Hay Annasr N° 12', '2008-05-14', 'Élève sérieux'],
        ['Fatima', 'Zahra', 'F', '0611223344', '0622334455', 'Amina Zahra', '1Bac SM', 'Lycée Ibn Sina', 'BL654321', 'Nouaceur', 'Centre Ville', '2009-11-20', ''],
        ['Youssef', 'Idrissi', 'M', '0633445566', '0644556677', 'Omar Idrissi', '3AC', 'Collège Al Qods', '', 'Deroua', 'Lotissement Al Wafa', '2011-03-08', '']
    ]

    # 2. Teachers Schema
    headers_tea = ['prenom', 'nom', 'specialite', 'telephone', 'email', 'cin', 'type_salaire', 'montant_salaire', 'remarques']
    samples_tea = [
        ['Ahmed', 'Alami', 'Mathématiques', '0611223344', 'ahmed.alami@gmail.com', 'A456789', 'percentage', '50.0', 'Professeur 2Bac SM/PC'],
        ['Khadija', 'Mansouri', 'Français', '0677889900', 'k.mansouri@yahoo.fr', 'B987654', 'percentage', '50.0', 'Cycle Collège & Lycée'],
        ['Said', 'Tahiri', 'Anglais', '0655667788', 'said.tahiri@gmail.com', 'C112233', 'percentage', '50.0', 'Langue vivante A1-B2']
    ]

    # 3. Courses Schema
    headers_cou = ['nom_classe', 'categorie', 'matiere', 'niveau', 'groupe', 'prix_mensuel', 'frais_inscription', 'enseignant', 'salle', 'duree_seance', 'jours']
    samples_cou = [
        ['Mathématiques 2Bac Biof', 'tutoring', 'Mathématiques', '2Bac Biof', 'Groupe A', 300.0, 40.0, 'Ahmed Alami', 'Salle 1', '2h00', '0,2,4'],
        ['Physique Chimie 2Bac', 'tutoring', 'Physique-Chimie', '2Bac PC', 'Groupe 1', 300.0, 40.0, 'Professeur PC', 'Salle 2', '2h00', '1,3'],
        ['Anglais Général A2', 'language', 'Anglais', 'A2', 'Groupe Soir', 250.0, 200.0, 'Said Tahiri', 'Salle 3', '1h30', '0,2,4']
    ]

    if target == 'students':
        add_sheet('Élèves', headers_stu, samples_stu)
    elif target == 'teachers':
        add_sheet('Enseignants', headers_tea, samples_tea)
    elif target == 'courses':
        add_sheet('Classes', headers_cou, samples_cou)
    else:  # All in one
        add_sheet('Élèves', headers_stu, samples_stu)
        add_sheet('Enseignants', headers_tea, samples_tea)
        add_sheet('Classes', headers_cou, samples_cou)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


@app.route('/import')
@login_required
@role_required('admin')
def import_page():
    return render_template('import_data.html')


@app.route('/import/template/<target>')
@login_required
@role_required('admin')
def import_download_template(target):
    if target not in ('students', 'teachers', 'courses', 'all'):
        target = 'all'

    data_bytes = generate_excel_template_bytes(target)
    filename = f"modele_import_{target}_{date.today().strftime('%Y%m%d')}.xlsx"
    return send_file(data_bytes, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _norm_col_name(c):
    if not c:
        return ""
    import unicodedata
    s = str(c).lower().strip()
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8')
    return s.replace(' ', '_').replace('-', '_').replace('.', '').replace('/', '_')


@app.route('/import/upload', methods=['POST'])
@login_required
@role_required('admin')
def import_upload_data():
    if 'data_file' not in request.files:
        flash("Veuillez sélectionner un fichier Excel (.xlsx, .xls) ou CSV.", "danger")
        return redirect(url_for('import_page'))

    f = request.files['data_file']
    if not f or not f.filename:
        flash("Aucun fichier sélectionné.", "danger")
        return redirect(url_for('import_page'))

    filename = secure_filename(f.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ('.xlsx', '.xls', '.csv'):
        flash("Format de fichier non pris en charge. Veuillez fournir un fichier .xlsx ou .csv.", "danger")
        return redirect(url_for('import_page'))

    target_choice = request.form.get('target_type', 'auto')

    # Parse with pandas
    import pandas as pd
    try:
        if ext == '.csv':
            try:
                dfs = {'Data': pd.read_csv(f, sep=None, engine='python', encoding='utf-8')}
            except Exception:
                f.seek(0)
                dfs = {'Data': pd.read_csv(f, sep=';', encoding='latin1')}
        else:
            dfs = pd.read_excel(f, sheet_name=None)
    except Exception as e:
        flash(f"Erreur lors de la lecture du fichier Excel : {e}", "danger")
        return redirect(url_for('import_page'))

    # Results tracker
    res = {
        'students_created': 0,
        'students_updated': 0,
        'teachers_created': 0,
        'teachers_updated': 0,
        'courses_created': 0,
        'courses_updated': 0,
        'errors': []
    }

    # Helper date parser
    def _parse_cell_date(val):
        if pd.isna(val) or val is None or str(val).strip() == '':
            return None
        if isinstance(val, (datetime, date)):
            return val if isinstance(val, date) else val.date()
        s = str(val).strip().split(' ')[0]
        return parse_date(s)

    for sheet_name, df in dfs.items():
        if df.empty:
            continue

        sheet_norm = sheet_name.lower()
        col_map = {_norm_col_name(c): c for c in df.columns}

        def get_v(row, *aliases):
            for a in aliases:
                norm_a = _norm_col_name(a)
                if norm_a in col_map:
                    val = row[col_map[norm_a]]
                    if not pd.isna(val):
                        return str(val).strip()
            return None

        # Determine if this sheet is Students, Teachers, or Courses
        is_students = ('eleve' in sheet_norm or 'student' in sheet_norm or 'tilmid' in sheet_norm or
                       target_choice == 'students' or
                       ('nom' in col_map and ('parent' in str(col_map) or 'niveau' in str(col_map))))
        
        is_teachers = ('enseignant' in sheet_norm or 'prof' in sheet_norm or 'teacher' in sheet_norm or 'ostad' in sheet_norm or
                       target_choice == 'teachers' or
                       ('specialite' in col_map or 'specialty' in col_map or 'salaire' in col_map))

        is_courses = ('classe' in sheet_norm or 'cours' in sheet_norm or 'course' in sheet_norm or 'matiere' in sheet_norm or 'fawj' in sheet_norm or
                      target_choice == 'courses' or
                      ('nom_classe' in col_map or 'prix_mensuel' in col_map or 'matiere' in col_map))

        # 1. PROCESS STUDENTS
        if is_students and not is_teachers and not is_courses:
            for idx, row in df.iterrows():
                row_num = idx + 2
                nom = get_v(row, 'nom', 'last_name', 'nom_famille', 'النسب', 'اسم_العائلة')
                prenom = get_v(row, 'prenom', 'first_name', 'الاسم', 'الاسم_الشخصي')
                if not prenom and not nom:
                    continue  # skip empty line

                phone = get_v(row, 'telephone', 'phone', 'tel', 'gsm', 'الهاتف', 'mobile')
                parent_phone = get_v(row, 'telephone_parent', 'parent_phone', 'tel_parent', 'هاتف_الولي', 'هاتف_الاب')
                cin = get_v(row, 'cin', 'cnie', 'بطاقة_التعريف')
                
                # Check duplicate
                stu = None
                if cin:
                    stu = Student.query.filter(Student.cin.ilike(cin)).first()
                if not stu and phone:
                    stu = Student.query.filter(Student.phone == phone).first()
                if not stu and parent_phone:
                    stu = Student.query.filter((Student.parent_phone == parent_phone) & (Student.first_name.ilike(prenom or ''))).first()
                if not stu and prenom and nom:
                    stu = Student.query.filter(Student.first_name.ilike(prenom) & Student.last_name.ilike(nom)).first()

                if stu:
                    # Update empty info
                    if not stu.phone and phone: stu.phone = phone
                    if not stu.parent_phone and parent_phone: stu.parent_phone = parent_phone
                    if not stu.cin and cin: stu.cin = cin
                    res['students_updated'] += 1
                else:
                    new_code = SH.gen_code('student_prefix', 'next_student_number')
                    stu = Student(
                        code=new_code,
                        first_name=prenom or 'Élève',
                        last_name=nom or '',
                        gender=get_v(row, 'genre', 'sexe', 'gender') or 'M',
                        phone=phone,
                        parent_phone=parent_phone,
                        parent_name=get_v(row, 'nom_parent', 'parent_name', 'tuteur'),
                        school_level=get_v(row, 'niveau_scolaire', 'school_level', 'niveau', 'level', 'المستوى'),
                        school_name=get_v(row, 'etablissement', 'school_name', 'ecole', 'المؤسسة'),
                        cin=cin,
                        city=get_v(row, 'ville', 'city', 'المدينة') or 'Deroua',
                        address=get_v(row, 'adresse', 'address', 'العنوان'),
                        birth_date=_parse_cell_date(get_v(row, 'date_naissance', 'birth_date')),
                        notes=get_v(row, 'remarques', 'notes', 'observations', 'ملاحظات'),
                        status='active',
                        created_by=current_user().id if current_user() else None
                    )
                    db.session.add(stu)
                    res['students_created'] += 1

        # 2. PROCESS TEACHERS
        elif is_teachers and not is_courses:
            for idx, row in df.iterrows():
                row_num = idx + 2
                nom = get_v(row, 'nom', 'last_name', 'النسب')
                prenom = get_v(row, 'prenom', 'first_name', 'الاسم')
                if not prenom and not nom:
                    continue

                phone = get_v(row, 'telephone', 'phone', 'tel', 'الهاتف')
                cin = get_v(row, 'cin', 'cnie')
                specialty = get_v(row, 'specialite', 'specialty', 'matiere', 'التخصص') or 'Général'

                t_obj = None
                if cin:
                    t_obj = Teacher.query.filter(Teacher.cin.ilike(cin)).first()
                if not t_obj and phone:
                    t_obj = Teacher.query.filter(Teacher.phone == phone).first()
                if not t_obj and prenom and nom:
                    t_obj = Teacher.query.filter(Teacher.first_name.ilike(prenom) & Teacher.last_name.ilike(nom)).first()

                sal_type = get_v(row, 'type_salaire', 'salary_type', 'mode') or 'percentage'
                sal_amount = _f(get_v(row, 'montant_salaire', 'salary_amount', 'pourcentage', 'salaire')) or 50.0

                if t_obj:
                    if not t_obj.phone and phone: t_obj.phone = phone
                    if not t_obj.specialty and specialty: t_obj.specialty = specialty
                    res['teachers_updated'] += 1
                else:
                    new_code = SH.gen_code('course_prefix', 'next_student_number')
                    t_obj = Teacher(
                        code=new_code,
                        first_name=prenom or 'Professeur',
                        last_name=nom or '',
                        specialty=specialty,
                        phone=phone,
                        email=get_v(row, 'email', 'courriel'),
                        cin=cin,
                        salary_type=sal_type,
                        salary_amount=sal_amount,
                        active=True,
                        notes=get_v(row, 'remarques', 'notes')
                    )
                    db.session.add(t_obj)
                    res['teachers_created'] += 1

        # 3. PROCESS COURSES / CLASSES
        elif is_courses:
            for idx, row in df.iterrows():
                row_num = idx + 2
                course_name = get_v(row, 'nom_classe', 'course_name', 'nom', 'classe', 'cours', 'الفوج')
                if not course_name:
                    continue

                category = get_v(row, 'categorie', 'category', 'type') or 'tutoring'
                if category not in ('tutoring', 'language'):
                    category = 'tutoring'

                subject = get_v(row, 'matiere', 'subject', 'language', 'المادة') or course_name
                level = get_v(row, 'niveau', 'level', 'المستوى') or ''
                group_name = get_v(row, 'groupe', 'group_name', 'groupe_nom') or 'Groupe A'
                price = _f(get_v(row, 'prix_mensuel', 'prix', 'price', 'tarif', 'الثمن')) or 300.0
                reg_fee = _f(get_v(row, 'frais_inscription', 'registration_fee', 'frais', 'واجب_التسجيل')) or (40.0 if category == 'tutoring' else 100.0)

                # Look up teacher
                teacher_name = get_v(row, 'enseignant', 'professeur', 'teacher', 'prof', 'الاستاذ')
                teacher_id = None
                if teacher_name:
                    t_match = Teacher.query.filter(
                        (Teacher.first_name + ' ' + Teacher.last_name).ilike(f"%{teacher_name}%") |
                        Teacher.last_name.ilike(f"%{teacher_name}%") |
                        Teacher.specialty.ilike(f"%{teacher_name}%")
                    ).first()
                    if t_match:
                        teacher_id = t_match.id

                # Look up room
                room_name = get_v(row, 'salle', 'room', 'القاعة')
                room_id = None
                if room_name:
                    r_match = Room.query.filter(Room.name.ilike(f"%{room_name}%")).first()
                    if not r_match:
                        r_match = Room(name=room_name, capacity=20)
                        db.session.add(r_match)
                        db.session.flush()
                    room_id = r_match.id

                cou_obj = Course.query.filter(Course.name.ilike(course_name)).first()
                if cou_obj:
                    cou_obj.price = price
                    if teacher_id: cou_obj.teacher_id = teacher_id
                    if room_id: cou_obj.room_id = room_id
                    res['courses_updated'] += 1
                else:
                    new_code = SH.gen_code('course_prefix', 'next_student_number')
                    cou_obj = Course(
                        code=new_code,
                        name=course_name,
                        category=category,
                        language=subject,
                        level=level,
                        group_name=group_name,
                        price=price,
                        price_per_month=price,
                        registration_fee=reg_fee,
                        billing_cycle='monthly',
                        teacher_id=teacher_id,
                        room_id=room_id,
                        session_duration=get_v(row, 'duree_seance', 'duration', 'duree') or '2h00',
                        scheduled_days=get_v(row, 'jours', 'days', 'scheduled_days') or '0,2,4',
                        active=True
                    )
                    db.session.add(cou_obj)
                    res['courses_created'] += 1

                db.session.flush()
                sync_schedule_from_course_name(cou_obj)

    try:
        db.session.commit()
        log_action('data_import', f"Import completed: {res['students_created']} students, {res['teachers_created']} teachers, {res['courses_created']} courses")
        msg = f"Importation réussie : {res['students_created']} élève(s) créés ({res['students_updated']} mis à jour), {res['teachers_created']} enseignant(s) créés, {res['courses_created']} classe(s) créées."
        flash(msg, "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'enregistrement des données importées : {e}", "danger")

    return render_template('import_data.html', results=res)






# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@app.route('/users')
@login_required
@role_required('admin')
def users():
    teachers = Teacher.query.filter_by(active=True).order_by(Teacher.last_name).all()
    return render_template('users.html',
                           users=User.query.order_by(User.id).all(),
                           teachers=teachers)


@app.route('/users/new', methods=['POST'])
@login_required
@role_required('admin')
def user_new():
    username = request.form.get('username', '').strip()
    role = request.form.get('role', 'admin')
    teacher_id = _int(request.form.get('teacher_id')) if role == 'teacher' else None

    if User.query.filter(db.func.lower(User.username) == username.lower()).first():
        flash(f"Le nom d'utilisateur '@{username}' existe déjà.", 'danger')
        return redirect(url_for('users'))

    if role == 'teacher' and teacher_id:
        existing_u = User.query.filter_by(teacher_id=teacher_id).first()
        if existing_u:
            teacher_obj = Teacher.query.get(teacher_id)
            t_name = teacher_obj.full_name if teacher_obj else 'cet enseignant'
            flash(f"Impossible de créer un deuxième compte : L'enseignant '{t_name}' possède déjà un compte d'accès (@{existing_u.username}).", 'danger')
            return redirect(url_for('users'))

    commission_rate = max(0.0, min(100.0, _f(request.form.get('commission_rate', 0.0)))) if role == 'secretary' else 0.0

    raw_password = request.form.get('password', '').strip()
    if not raw_password:
        if role == 'teacher' and teacher_id:
            raw_password = str(teacher_id)
        else:
            raw_password = 'password'

    u = User(username=username,
             full_name=request.form.get('full_name'),
             role=role,
             teacher_id=teacher_id,
             commission_rate=commission_rate,
             active=True)
    u.set_password(raw_password)
    db.session.add(u); db.session.commit(); flash(f"Utilisateur '@{u.username}' créé avec succès.", 'success')
    return redirect(url_for('users'))


@app.route('/users/<int:uid>/commission', methods=['POST'])
@login_required
@role_required('admin')
def user_commission(uid):
    u = User.query.get_or_404(uid)
    rate = max(0.0, min(100.0, _f(request.form.get('commission_rate', 0.0))))
    u.commission_rate = rate
    db.session.commit()
    flash(f"Taux de bonus pour @{u.username} mis à jour : {u.commission_rate:.1f}%", 'success')
    return redirect(request.referrer or url_for('users'))


@app.route('/users/<int:uid>/edit', methods=['POST'])
@login_required
@role_required('admin')
def user_edit(uid):
    u = User.query.get_or_404(uid)
    full_name = request.form.get('full_name', '').strip()
    role = request.form.get('role', u.role)
    new_password = request.form.get('password', '').strip()
    teacher_id = _int(request.form.get('teacher_id')) if role == 'teacher' else None

    if full_name:
        u.full_name = full_name
    u.role = role
    u.teacher_id = teacher_id

    if role == 'secretary':
        rate = _f(request.form.get('commission_rate', 0.0))
        u.commission_rate = max(0.0, min(100.0, rate))
    else:
        u.commission_rate = 0.0

    if new_password:
        u.set_password(new_password)

    db.session.commit()
    flash(f"Compte @{u.username} mis à jour avec succès (Rôle : {u.role}, Taux prime : {u.commission_rate:.1f}%).", 'success')
    return redirect(url_for('users'))


@app.route('/users/<int:uid>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def user_toggle(uid):
    u = User.query.get_or_404(uid)
    u.active = not u.active
    db.session.commit(); flash('Utilisateur mis à jour', 'success')
    return redirect(url_for('users'))


@app.route('/users/<int:uid>/reset', methods=['POST'])
@login_required
@role_required('admin')
def user_reset(uid):
    u = User.query.get_or_404(uid)
    u.set_password(request.form.get('password') or 'password')
    db.session.commit(); flash('Mot de passe réinitialisé', 'success')
    return redirect(url_for('users'))


@app.route('/users/<int:uid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def user_delete(uid):
    u = User.query.get_or_404(uid)
    if u.id == current_user().id:
        flash("Impossible de supprimer votre propre compte", 'danger')
        return redirect(url_for('users'))
    db.session.delete(u); db.session.commit(); flash('Utilisateur supprimé', 'success')
    return redirect(url_for('users'))


@app.route('/users/activity')
@app.route('/users/<int:uid>/activity')
@login_required
@role_required('admin', 'secretary')
def user_activity(uid=None):
    cur = current_user()
    if cur.role == 'secretary':
        req_uid = cur.id
        selected_user = cur
        users_list = [cur]
    else:
        users_list = User.query.filter(User.role.in_(['admin', 'secretary'])).order_by(User.full_name, User.username).all()
        if 'user_id' in request.args:
            req_uid = _int(request.args.get('user_id'))
        elif uid:
            req_uid = uid
        else:
            req_uid = None
        selected_user = User.query.get(req_uid) if req_uid else None

    period = request.args.get('period', 'today')
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    today_dt = date.today()
    if period == 'today':
        d_start = today_dt
        d_end = today_dt
    elif period == 'yesterday':
        d_start = today_dt - timedelta(days=1)
        d_end = today_dt - timedelta(days=1)
    elif period == 'week':
        d_start = today_dt - timedelta(days=today_dt.weekday())
        d_end = today_dt
    elif period == 'month':
        d_start = today_dt.replace(day=1)
        d_end = today_dt
    elif period == 'custom' and (start_date_str or end_date_str):
        d_start = parse_date(start_date_str) if start_date_str else None
        d_end = parse_date(end_date_str) if end_date_str else None
    elif period == 'all':
        d_start = None
        d_end = None
    else:
        d_start = today_dt
        d_end = today_dt
        period = 'today'

    # 1. Payments Query
    pq = Payment.query.join(Student, Payment.student_id == Student.id, isouter=True)
    if selected_user:
        pq = pq.filter(Payment.recorded_by == selected_user.id)
    if d_start:
        pq = pq.filter(Payment.date >= d_start)
    if d_end:
        pq = pq.filter(Payment.date <= d_end)
    # Exclude internal course transfer reports (-TR) from cash collections
    pq = pq.filter(~Payment.receipt.ilike('%-TR%'))
    pq = pq.filter(~Payment.note.ilike('%Report transfert%'))
    payments = pq.order_by(Payment.date.desc(), Payment.id.desc()).all()

    # Differentiate tuition payments vs standalone manual sales in payments list
    tuition_payments = [p for p in payments if not (p.note and 'Vente Manuel' in p.note)]
    total_tuition_collected = sum(p.amount for p in tuition_payments)
    total_cash_collected = sum(p.amount for p in payments if p.method == 'cash')
    total_bank_collected = sum(p.amount for p in payments if p.method in ('transfer', 'card', 'online'))

    # 2. Book Sales Query
    bq = BookSale.query.join(Book, BookSale.book_id == Book.id, isouter=True)\
                       .join(Student, BookSale.student_id == Student.id, isouter=True)
    if selected_user:
        bq = bq.filter(BookSale.recorded_by == selected_user.id)
    if d_start:
        bq = bq.filter(BookSale.sale_date >= d_start)
    if d_end:
        bq = bq.filter(BookSale.sale_date <= d_end)
    book_sales = bq.order_by(BookSale.sale_date.desc(), BookSale.id.desc()).all()

    total_books_collected = sum(s.total_amount for s in book_sales)
    total_books_sold_count = sum(s.quantity for s in book_sales)
    grand_total_revenue = total_tuition_collected + total_books_collected

    # 3. Students Created Query
    sq = Student.query
    if selected_user:
        sq = sq.filter(Student.created_by == selected_user.id)
    if d_start:
        sq = sq.filter(db.func.date(Student.created_at) >= d_start)
    if d_end:
        sq = sq.filter(db.func.date(Student.created_at) <= d_end)
    students_created = sq.order_by(Student.created_at.desc(), Student.id.desc()).all()

    # 4. Enrollments Created Query
    eq = Enrollment.query.join(Student, Enrollment.student_id == Student.id, isouter=True)\
                         .join(Course, Enrollment.course_id == Course.id, isouter=True)
    if selected_user:
        eq = eq.filter(Enrollment.created_by == selected_user.id)
    if d_start and d_end:
        eq = eq.filter(db.or_(
            db.func.date(Enrollment.created_at).between(d_start, d_end),
            Enrollment.enroll_date.between(d_start, d_end)
        ))
    elif d_start:
        eq = eq.filter(db.or_(
            db.func.date(Enrollment.created_at) >= d_start,
            Enrollment.enroll_date >= d_start
        ))
    elif d_end:
        eq = eq.filter(db.or_(
            db.func.date(Enrollment.created_at) <= d_end,
            Enrollment.enroll_date <= d_end
        ))
    enrollments_created = eq.order_by(db.func.coalesce(db.func.date(Enrollment.created_at), Enrollment.enroll_date).desc(), Enrollment.id.desc()).all()

    # Commissions / Primes calculées pour chaque inscription
    commission_details = []
    total_commission_confirmed = 0.0
    total_commission_remaining = 0.0
    total_commission_pending = 0.0
    count_pending_group = 0
    count_confirmed = 0
    count_new_students = 0
    count_renewals = 0

    for e in enrollments_created:
        target_usr = selected_user or e.creator
        u_rate = target_usr.commission_rate if target_usr else 0.0
        c_detail = calculate_enrollment_secretary_bonus(e, commission_rate=u_rate, user=target_usr)
        commission_details.append(c_detail)
        if c_detail['is_new_student']:
            count_new_students += 1
            if c_detail['is_pending_group']:
                total_commission_pending += c_detail['bonus_potential']
                count_pending_group += 1
            elif c_detail['is_confirmed']:
                total_commission_confirmed += c_detail['bonus_earned']
                total_commission_remaining += c_detail['bonus_remaining']
                count_confirmed += 1
            else:
                total_commission_remaining += c_detail['bonus_remaining']
        else:
            count_renewals += 1

    total_commission_confirmed = round(total_commission_confirmed, 2)
    total_commission_remaining = round(total_commission_remaining, 2)
    total_commission_pending = round(total_commission_pending, 2)
    total_commission_all = round(total_commission_confirmed + total_commission_remaining + total_commission_pending, 2)

    # 5. Activity Logs (Audit Trail) Query
    lq = LogEntry.query.join(User, LogEntry.user_id == User.id, isouter=True)
    if selected_user:
        lq = lq.filter(LogEntry.user_id == selected_user.id)
    if d_start:
        lq = lq.filter(db.func.date(LogEntry.created_at) >= d_start)
    if d_end:
        lq = lq.filter(db.func.date(LogEntry.created_at) <= d_end)
    logs = lq.order_by(LogEntry.created_at.desc(), LogEntry.id.desc()).limit(200).all()

    # Friendly action translations for the audit trail
    ACTION_TITLES = {
        'login': 'Connexion au système',
        'student_save': 'Modification / Ajout fiche élève',
        'student_add': 'Nouvel élève inscrit (Express)',
        'student_archive': 'Archivage élève',
        'student_delete': 'Suppression fiche élève',
        'enroll_multi': 'Nouvelle inscription aux cours',
        'express_enrollment': 'Pack Inscription Express complet',
        'enrollment_edit': 'Modification inscription',
        'enrollment_renew': 'Renouvellement abonnement élève',
        'enrollment_transfer': 'Transfert de classe / groupe',
        'enrollment_assign': 'Affectation depuis liste d\'attente',
        'enrollment_pause': 'Mise en pause abonnement',
        'enrollment_resume': 'Reprise d\'abonnement',
        'enrollment_delete': 'Suppression inscription',
        'payment': 'Encaissement de paiement',
        'invoice_pay': 'Règlement de facture',
        'book_sale': 'Vente manuel au comptoir',
        'book_save': 'Création / mise à jour manuel',
        'book_restock': 'Réapprovisionnement de stock',
        'expense_add': 'Enregistrement achat / charge',
        'expense_edit': 'Modification achat / charge',
        'expense_pay': 'Règlement achat / charge',
        'expense_delete': 'Suppression achat / charge',
        'supplier_add': 'Création fournisseur',
        'supplier_edit': 'Modification fournisseur',
        'supplier_delete': 'Archivage fournisseur',
        'certificate_issue': 'Délivrance attestation / certificat',
        'badge_create': 'Impression badge ID',
        'backup_create': 'Sauvegarde de la base de données',
        'backup_restore': 'Restauration de base de données',
        'data_import': 'Import massif de données'
    }

    return render_template('user_activity.html',
                           users=users_list,
                           selected_user=selected_user,
                           period=period,
                           d_start=d_start,
                           d_end=d_end,
                           start_date_str=start_date_str or (d_start.strftime('%Y-%m-%d') if d_start else ''),
                           end_date_str=end_date_str or (d_end.strftime('%Y-%m-%d') if d_end else ''),
                           payments=tuition_payments,
                           book_sales=book_sales,
                           students=students_created,
                           enrollments=enrollments_created,
                           commission_details=commission_details,
                           total_commission_confirmed=total_commission_confirmed,
                           total_commission_remaining=total_commission_remaining,
                           total_commission_pending=total_commission_pending,
                           total_commission_all=total_commission_all,
                           count_pending_group=count_pending_group,
                           count_confirmed=count_confirmed,
                           count_new_students=count_new_students,
                           count_renewals=count_renewals,
                           logs=logs,
                           action_titles=ACTION_TITLES,
                           total_tuition_collected=total_tuition_collected,
                           total_books_collected=total_books_collected,
                           grand_total_revenue=grand_total_revenue,
                           total_cash_collected=total_cash_collected,
                           total_bank_collected=total_bank_collected,
                           total_books_sold_count=total_books_sold_count,
                           students_count=len(students_created),
                           enrollments_count=len(enrollments_created),
                           operations_count=len(logs))


@app.route('/users/activity/primes-report')
@login_required
@role_required('admin', 'secretary')
def user_activity_primes_report():
    cur = current_user()
    if cur.role == 'secretary':
        req_uid = cur.id
        selected_user = cur
        users_list = [cur]
    else:
        users_list = User.query.filter(User.role.in_(['admin', 'secretary'])).order_by(User.full_name, User.username).all()
        if 'user_id' in request.args and request.args.get('user_id'):
            req_uid = _int(request.args.get('user_id'))
            selected_user = User.query.get(req_uid) if req_uid else None
        else:
            # Par défaut, si l'utilisateur connecté est mriliass, sélectionner son compte
            if cur.username and cur.username.lower() == 'mriliass':
                selected_user = cur
            else:
                mr_u = User.query.filter(db.func.lower(User.username) == 'mriliass').first()
                selected_user = mr_u or cur

    period = request.args.get('period', 'month')
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    today_dt = date.today()
    if period == 'today':
        d_start = today_dt
        d_end = today_dt
    elif period == 'yesterday':
        d_start = today_dt - timedelta(days=1)
        d_end = today_dt - timedelta(days=1)
    elif period == 'week':
        d_start = today_dt - timedelta(days=today_dt.weekday())
        d_end = today_dt
    elif period == 'month':
        d_start = today_dt.replace(day=1)
        d_end = today_dt
    elif period == 'custom' and (start_date_str or end_date_str):
        d_start = parse_date(start_date_str) if start_date_str else None
        d_end = parse_date(end_date_str) if end_date_str else None
    elif period == 'all':
        d_start = None
        d_end = None
    else:
        d_start = today_dt.replace(day=1)
        d_end = today_dt
        period = 'month'

    eq = Enrollment.query.join(Student, Enrollment.student_id == Student.id, isouter=True)\
                         .join(Course, Enrollment.course_id == Course.id, isouter=True)
    if selected_user:
        eq = eq.filter(Enrollment.created_by == selected_user.id)
    if d_start and d_end:
        eq = eq.filter(db.or_(
            db.func.date(Enrollment.created_at).between(d_start, d_end),
            Enrollment.enroll_date.between(d_start, d_end)
        ))
    elif d_start:
        eq = eq.filter(db.or_(
            db.func.date(Enrollment.created_at) >= d_start,
            Enrollment.enroll_date >= d_start
        ))
    elif d_end:
        eq = eq.filter(db.or_(
            db.func.date(Enrollment.created_at) <= d_end,
            Enrollment.enroll_date <= d_end
        ))
    enrollments_list = eq.order_by(Enrollment.enroll_date.asc(), Enrollment.id.asc()).all()

    confirmed_primes = []
    pending_primes = []
    excluded_enrollments = []

    total_confirmed_amount = 0.0
    total_pending_amount = 0.0
    count_lang = 0
    total_lang = 0.0
    count_soutien = 0
    total_soutien = 0.0
    total_tuition_prime_students = 0.0

    # Group enrollments by student to show pack courses cleanly
    student_other_courses = {}
    for e in enrollments_list:
        if e.student_id:
            student_other_courses.setdefault(e.student_id, []).append(e)

    for e in enrollments_list:
        target_usr = selected_user or e.creator
        u_rate = target_usr.commission_rate if target_usr else 0.0
        cd = calculate_enrollment_secretary_bonus(e, commission_rate=u_rate, user=target_usr)

        # Find receipt numbers for this student
        receipts = []
        if e.student_id:
            pmts = Payment.query.filter_by(student_id=e.student_id).filter(Payment.amount > 0).order_by(Payment.date.desc()).all()
            receipts = [p.receipt or f"REC-{p.id}" for p in pmts[:2]]
        cd['receipts_str'] = ", ".join(receipts) if receipts else "—"

        # Other courses in pack for this student
        others = [
            oe.course.name if oe.course else "Cours"
            for oe in student_other_courses.get(e.student_id, [])
            if oe.id != e.id and getattr(oe, 'status', None) not in ['dropped', 'cancelled']
        ]
        cd['other_pack_courses'] = others

        if cd['bonus_earned'] > 0:
            confirmed_primes.append(cd)
            total_confirmed_amount += cd['bonus_earned']
            total_tuition_prime_students += cd['total_paid']
            if cd['bonus_earned'] >= 50.0:
                count_lang += 1
                total_lang += cd['bonus_earned']
            else:
                count_soutien += 1
                total_soutien += cd['bonus_earned']
        elif cd['bonus_remaining'] > 0 or cd['is_pending_group']:
            pending_primes.append(cd)
            total_pending_amount += (cd['bonus_remaining'] or cd['bonus_potential'])
        else:
            excluded_enrollments.append(cd)

    return render_template('primes_report.html',
                           users=users_list,
                           selected_user=selected_user,
                           period=period,
                           d_start=d_start,
                           d_end=d_end,
                           start_date_str=start_date_str or (d_start.strftime('%Y-%m-%d') if d_start else ''),
                           end_date_str=end_date_str or (d_end.strftime('%Y-%m-%d') if d_end else ''),
                           confirmed_primes=confirmed_primes,
                           pending_primes=pending_primes,
                           excluded_enrollments=excluded_enrollments,
                           total_confirmed_amount=round(total_confirmed_amount, 2),
                           total_pending_amount=round(total_pending_amount, 2),
                           count_lang=count_lang,
                           total_lang=round(total_lang, 2),
                           count_soutien=count_soutien,
                           total_soutien=round(total_soutien, 2),
                           total_tuition_prime_students=round(total_tuition_prime_students, 2),
                           total_enrollments_count=len(enrollments_list),
                           now_dt=datetime.now())


@app.route('/users/activity/cloture')
@login_required
@role_required('admin', 'secretary')
def user_activity_cloture():
    cur = current_user()
    if cur.role == 'secretary':
        req_uid = cur.id
        selected_user = cur
        users_list = [cur]
    else:
        users_list = User.query.filter(User.role.in_(['admin', 'secretary'])).order_by(User.full_name, User.username).all()
        req_uid = _int(request.args.get('user_id')) if 'user_id' in request.args and request.args.get('user_id') else None
        selected_user = User.query.get(req_uid) if req_uid else None

    period = request.args.get('period', 'today')
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()
    print_format = request.args.get('format', '80mm')

    today_dt = date.today()
    if period == 'today':
        d_start = today_dt
        d_end = today_dt
    elif period == 'yesterday':
        d_start = today_dt - timedelta(days=1)
        d_end = today_dt - timedelta(days=1)
    elif period == 'week':
        d_start = today_dt - timedelta(days=today_dt.weekday())
        d_end = today_dt
    elif period == 'month':
        d_start = today_dt.replace(day=1)
        d_end = today_dt
    elif period == 'custom' and (start_date_str or end_date_str):
        d_start = parse_date(start_date_str) if start_date_str else None
        d_end = parse_date(end_date_str) if end_date_str else None
    elif period == 'all':
        d_start = None
        d_end = None
    else:
        d_start = today_dt
        d_end = today_dt
        period = 'today'

    # 1. Payments Query
    pq = Payment.query.join(Student, Payment.student_id == Student.id, isouter=True)
    if selected_user:
        pq = pq.filter(Payment.recorded_by == selected_user.id)
    if d_start:
        pq = pq.filter(Payment.date >= d_start)
    if d_end:
        pq = pq.filter(Payment.date <= d_end)
    pq = pq.filter(~Payment.receipt.ilike('%-TR%'))
    pq = pq.filter(~Payment.note.ilike('%Report transfert%'))
    payments = pq.order_by(Payment.date.asc(), Payment.id.asc()).all()

    # Differentiate tuition payments vs manual sales in payments list
    tuition_payments = [p for p in payments if not (p.note and 'Vente Manuel' in p.note)]
    total_tuition_collected = sum(p.amount for p in tuition_payments)

    # 2. Book Sales Query
    bq = BookSale.query.join(Book, BookSale.book_id == Book.id, isouter=True)\
                       .join(Student, BookSale.student_id == Student.id, isouter=True)
    if selected_user:
        bq = bq.filter(BookSale.recorded_by == selected_user.id)
    if d_start:
        bq = bq.filter(BookSale.sale_date >= d_start)
    if d_end:
        bq = bq.filter(BookSale.sale_date <= d_end)
    book_sales = bq.order_by(BookSale.sale_date.asc(), BookSale.id.asc()).all()

    total_books_collected = sum(s.total_amount for s in book_sales)
    total_books_sold_count = sum(s.quantity for s in book_sales)
    grand_total_revenue = total_tuition_collected + total_books_collected

    # Standalone book sales: book sales without a corresponding Payment entry
    payment_receipts = {p.receipt for p in payments if p.receipt}
    standalone_book_sales = [b for b in book_sales if b.receipt_no not in payment_receipts]

    cash_from_payments = sum(p.amount for p in payments if (p.method or '').lower() == 'cash')
    cash_from_standalone_books = sum(b.total_amount for b in standalone_book_sales if (b.payment_method or 'cash').lower() == 'cash')
    total_cash_drawer = cash_from_payments + cash_from_standalone_books

    bank_from_payments = sum(p.amount for p in payments if (p.method or '').lower() in ('transfer', 'card', 'online'))
    bank_from_standalone_books = sum(b.total_amount for b in standalone_book_sales if (b.payment_method or '').lower() in ('transfer', 'card', 'online'))
    total_bank_collected = bank_from_payments + bank_from_standalone_books

    other_from_payments = sum(p.amount for p in payments if (p.method or '').lower() not in ('cash', 'transfer', 'card', 'online'))
    other_from_standalone_books = sum(b.total_amount for b in standalone_book_sales if (b.payment_method or '').lower() not in ('cash', 'transfer', 'card', 'online', ''))
    total_other_collected = other_from_payments + other_from_standalone_books

    # Unified chronological transactions list
    transactions = []
    for p in payments:
        is_book = bool(p.note and 'Vente Manuel' in p.note)
        t_time = p.created_at.strftime('%H:%M') if p.created_at else ''
        user_obj = p.creator
        uid = p.recorded_by
        u_name = (user_obj.full_name or user_obj.username) if user_obj else (f'Utilisateur #{uid}' if uid else 'Non assigné')
        u_username = user_obj.username if user_obj else ''
        transactions.append({
            'receipt': p.receipt or f'REC-{p.id:04d}',
            'date': p.date,
            'time': t_time,
            'sort_key': (p.date or date.min, t_time, p.id),
            'student_name': p.student.full_name if p.student else ('Comptoir Vente Manuel' if is_book else 'Comptoir Libre'),
            'student_code': p.student.code if p.student else '',
            'label': 'Livre' if is_book else 'Scolarité',
            'detail': p.courses_description or p.note or 'Scolarité',
            'method': p.method or 'cash',
            'amount': p.amount,
            'is_cash': (p.method or '').lower() == 'cash',
            'user_id': uid,
            'agent_name': u_name,
            'agent_username': u_username
        })

    for b in standalone_book_sales:
        t_time = b.created_at.strftime('%H:%M') if b.created_at else ''
        user_obj = b.user
        uid = b.recorded_by
        u_name = (user_obj.full_name or user_obj.username) if user_obj else (f'Utilisateur #{uid}' if uid else 'Non assigné')
        u_username = user_obj.username if user_obj else ''
        transactions.append({
            'receipt': b.receipt_no or f'LIVRE-{b.id:04d}',
            'date': b.sale_date,
            'time': t_time,
            'sort_key': (b.sale_date or date.min, t_time, b.id),
            'student_name': b.student.full_name if b.student else 'Comptoir Vente Manuel',
            'student_code': b.student.code if b.student else '',
            'label': 'Livre',
            'detail': f"{b.book.title if b.book else 'Manuel'} (x{b.quantity})",
            'method': b.payment_method or 'cash',
            'amount': b.total_amount,
            'is_cash': (b.payment_method or 'cash').lower() == 'cash',
            'user_id': uid,
            'agent_name': u_name,
            'agent_username': u_username
        })

    transactions.sort(key=lambda x: x['sort_key'])

    # Build per-user aggregation summaries and receipts by user
    users_dict = {}
    for t in transactions:
        uid = t.get('user_id')
        if uid not in users_dict:
            users_dict[uid] = {
                'id': uid,
                'name': t.get('agent_name') or 'Non assigné',
                'username': t.get('agent_username') or '',
                'cash': 0.0,
                'bank': 0.0,
                'other': 0.0,
                'total': 0.0,
                'receipts_count': 0,
                'cash_count': 0,
                'bank_count': 0,
                'transactions': []
            }
        u_entry = users_dict[uid]
        amt = float(t.get('amount') or 0.0)
        u_entry['total'] += amt
        if t.get('is_cash'):
            u_entry['cash'] += amt
            u_entry['cash_count'] += 1
        elif (t.get('method') or '').lower() in ('transfer', 'card', 'online'):
            u_entry['bank'] += amt
            u_entry['bank_count'] += 1
        else:
            u_entry['other'] += amt
        u_entry['receipts_count'] += 1
        u_entry['transactions'].append(t)

    # Sort each user's transactions chronologically
    for u_data in users_dict.values():
        u_data['transactions'].sort(key=lambda x: x['sort_key'])

    user_summaries = list(users_dict.values())
    user_summaries.sort(key=lambda x: x['total'], reverse=True)

    # 3. Operational Counts
    sq = Student.query
    if selected_user:
        sq = sq.filter(Student.created_by == selected_user.id)
    if d_start:
        sq = sq.filter(db.func.date(Student.created_at) >= d_start)
    if d_end:
        sq = sq.filter(db.func.date(Student.created_at) <= d_end)
    students_created_count = sq.count()

    eq = Enrollment.query
    if selected_user:
        eq = eq.filter(Enrollment.created_by == selected_user.id)
    if d_start and d_end:
        eq = eq.filter(db.or_(
            db.func.date(Enrollment.created_at).between(d_start, d_end),
            Enrollment.enroll_date.between(d_start, d_end)
        ))
    elif d_start:
        eq = eq.filter(db.or_(
            db.func.date(Enrollment.created_at) >= d_start,
            Enrollment.enroll_date >= d_start
        ))
    elif d_end:
        eq = eq.filter(db.or_(
            db.func.date(Enrollment.created_at) <= d_end,
            Enrollment.enroll_date <= d_end
        ))
    enrollments_created_count = eq.count()

    # Bonus calculation if secretary
    secretary_bonus_earned = 0.0
    if selected_user and selected_user.role == 'secretary':
        enrollments_list = eq.all()
        for e in enrollments_list:
            c_detail = calculate_enrollment_secretary_bonus(e, commission_rate=selected_user.commission_rate or 0.0, user=selected_user)
            if c_detail.get('is_new_student') and c_detail.get('is_confirmed'):
                secretary_bonus_earned += c_detail.get('bonus_earned', 0.0)
    secretary_bonus_earned = round(secretary_bonus_earned, 2)

    return render_template('cloture_print.html',
                           users=users_list,
                           selected_user=selected_user,
                           cur_user=cur,
                           period=period,
                           d_start=d_start,
                           d_end=d_end,
                           start_date_str=start_date_str or (d_start.strftime('%Y-%m-%d') if d_start else ''),
                           end_date_str=end_date_str or (d_end.strftime('%Y-%m-%d') if d_end else ''),
                           print_format=print_format,
                           total_tuition_collected=total_tuition_collected,
                           total_books_collected=total_books_collected,
                           grand_total_revenue=grand_total_revenue,
                           total_cash_drawer=total_cash_drawer,
                           total_bank_collected=total_bank_collected,
                           total_other_collected=total_other_collected,
                           total_books_sold_count=total_books_sold_count,
                           transactions=transactions,
                           user_summaries=user_summaries,
                           receipts_count=len(transactions),
                           cash_transactions_count=len([t for t in transactions if t['is_cash']]),
                           bank_transactions_count=len([t for t in transactions if not t['is_cash']]),
                           students_created_count=students_created_count,
                           enrollments_created_count=enrollments_created_count,
                           secretary_bonus_earned=secretary_bonus_earned,
                           now=datetime.now())


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


_float = _f


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# init & run
# ---------------------------------------------------------------------------
@app.cli.command('init')
def init_db():
    db.create_all()
    SH.seed_defaults()
    if User.query.count() == 0:
        a = User(username='admin', full_name='Administrateur', role='admin', active=True)
        a.set_password('admin')
        db.session.add(a)
        db.session.commit()
        print("Admin créé : admin/admin")
    print("DB initialisée")


def open_browser(port, url):
    """Ouvre le navigateur automatiquement après le démarrage."""
    try:
        time.sleep(2)
        webbrowser.open(url)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# QR Code & Barcode (générés localement, offline)
# ---------------------------------------------------------------------------
import io
import base64
import qrcode
import barcode
from barcode.writer import ImageWriter


def qr_data_uri(text, box_size=5, border=2):
    """Génère un QR code en data URI (base64)."""
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=box_size, border=border)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B3D6E", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def barcode_data_uri(text, module_height=9, module_width=0.28, font_size=9):
    """Génère un code-barres (Code128) en data URI (base64)."""
    try:
        code128 = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        writer.set_options({'module_height': module_height, 'module_width': module_width,
                            'font_size': font_size, 'text_distance': 2,
                            'foreground': '#0B3D6E', 'background': '#ffffff'})
        b = code128(text, writer=writer)
        buf = io.BytesIO()
        b.write(buf)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def badge_qr_value(student):
    """Le contenu encodé dans le QR / code-barres = ID + code élève."""
    if not student:
        return ""
    return f"ILAS|{student.id}|{student.code or ''}|{student.full_name}"


def auto_migrate_db():
    """Vérifie et ajoute automatiquement les nouvelles colonnes SQLite si nécessaires."""
    import sqlite3
    db_path = os.path.join(BASE, 'institut.db')
    if not os.path.exists(db_path):
        return
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")

        def add_cols_if_missing(table_name, cols_defs):
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing = set(row[1] for row in cursor.fetchall())
            if not existing:
                return
            for col_name, col_type in cols_defs:
                if col_name not in existing:
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                    except Exception as ex:
                        print(f">>> Migration note on {table_name}.{col_name}:", ex)

        # 1. enrollments
        add_cols_if_missing('enrollments', [
            ('total_sessions_month', 'INTEGER DEFAULT 0'),
            ('attended_sessions_month', 'INTEGER DEFAULT 0'),
            ('monthly_price', 'REAL DEFAULT 0.0'),
            ('calculated_price', 'REAL DEFAULT 0.0'),
            ('current_month_earned', 'REAL DEFAULT 0.0'),
            ('deferred_amount', 'REAL DEFAULT 0.0'),
            ('pause_date', 'DATE'),
            ('paused_sessions_remaining', 'INTEGER DEFAULT 0'),
            ('total_paused_days', 'INTEGER DEFAULT 0'),
            ('custom_end_date', 'DATE'),
            ('created_by', 'INTEGER REFERENCES users(id)')
        ])

        # 2. students
        add_cols_if_missing('students', [
            ('family_code', 'VARCHAR(30)'),
            ('credit_balance', 'REAL DEFAULT 0.0'),
            ('school_level', 'VARCHAR(60)'),
            ('school_name', 'VARCHAR(120)'),
            ('parent_name', 'VARCHAR(120)'),
            ('parent_phone', 'VARCHAR(30)'),
            ('whatsapp', 'VARCHAR(30)'),
            ('city', 'VARCHAR(60)'),
            ('cin', 'VARCHAR(30)'),
            ('created_by', 'INTEGER REFERENCES users(id)')
        ])

        # 3. courses
        add_cols_if_missing('courses', [
            ('tariff_id', 'INTEGER REFERENCES tariffs(id)'),
            ('sessions_per_week', 'INTEGER DEFAULT 3'),
            ('session_duration', "VARCHAR(30) DEFAULT '1h30'"),
            ('scheduled_days', "VARCHAR(30) DEFAULT '0,2,4'"),
            ('registration_fee', 'REAL DEFAULT 100.0'),
            ('price_per_month', 'REAL DEFAULT 0.0'),
            ('group_name', 'VARCHAR(60)'),
            ('billing_cycle', "VARCHAR(30) DEFAULT 'monthly'")
        ])

        # 4. course_teachers
        add_cols_if_missing('course_teachers', [
            ('start_date', 'DATE'),
            ('end_date', 'DATE'),
            ('is_active', 'BOOLEAN DEFAULT 1'),
            ('compensation_type', "VARCHAR(20) DEFAULT 'percentage'"),
            ('compensation_value', 'REAL DEFAULT 50.0')
        ])

        # 4b. schedule_slots
        add_cols_if_missing('schedule_slots', [
            ('teacher_id', 'INTEGER REFERENCES teachers(id)')
        ])

        # 5. users
        add_cols_if_missing('users', [
            ('teacher_id', 'INTEGER REFERENCES teachers(id)'),
            ('commission_rate', 'REAL DEFAULT 0.0')
        ])

        # 6. login_attempts
        add_cols_if_missing('login_attempts', [
            ('attempted_at', 'DATETIME'),
            ('username', 'VARCHAR(80)'),
            ('success', 'BOOLEAN DEFAULT 0')
        ])

        # 7. payments
        add_cols_if_missing('payments', [
            ('invoice_id', 'INTEGER REFERENCES invoices(id)'),
            ('recorded_by', 'INTEGER REFERENCES users(id)'),
            ('receipt', 'VARCHAR(30)')
        ])

        # 8. invoices
        add_cols_if_missing('invoices', [
            ('tva_rate', 'REAL DEFAULT 0.0'),
            ('tva_amount', 'REAL DEFAULT 0.0')
        ])

        # 9. expenses
        add_cols_if_missing('expenses', [
            ('expense_type', "VARCHAR(20) DEFAULT 'charge'"),
            ('supplier_id', 'INTEGER REFERENCES suppliers(id)'),
            ('supplier_name', 'VARCHAR(120)'),
            ('invoice_no', 'VARCHAR(60)'),
            ('due_date', 'DATE'),
            ('status', "VARCHAR(20) DEFAULT 'paid'"),
            ('paid_amount', 'REAL DEFAULT 0.0'),
            ('tax_amount', 'REAL DEFAULT 0.0'),
            ('receipt_file', 'VARCHAR(255)'),
            ('notes', 'TEXT'),
            ('teacher_id', 'INTEGER REFERENCES teachers(id)'),
            ('teacher_expense_id', 'INTEGER REFERENCES teacher_expenses(id)'),
            ('recurring_charge_id', 'INTEGER REFERENCES recurring_charges(id)'),
            ('recurring_month', 'VARCHAR(7)')
        ])

        # 10. teacher_advances
        add_cols_if_missing('teacher_advances', [
            ('receipt_no', 'VARCHAR(30)'),
            ('teacher_id', 'INTEGER REFERENCES teachers(id)'),
            ('amount', 'REAL DEFAULT 0.0'),
            ('date', 'DATE'),
            ('period_month', 'VARCHAR(7)'),
            ('payment_method', "VARCHAR(30) DEFAULT 'Espèces'"),
            ('reference_no', 'VARCHAR(50)'),
            ('status', "VARCHAR(20) DEFAULT 'paid'"),
            ('expense_id', 'INTEGER REFERENCES expenses(id)'),
            ('notes', 'TEXT'),
            ('recorded_by', 'INTEGER REFERENCES users(id)'),
            ('created_at', 'DATETIME')
        ])

        # 11. teacher_expenses (Frais, Copies, Livres déduits sur paie)
        add_cols_if_missing('teacher_expenses', [
            ('receipt_no', 'VARCHAR(30)'),
            ('teacher_id', 'INTEGER REFERENCES teachers(id)'),
            ('expense_type', "VARCHAR(30) DEFAULT 'copies'"),
            ('title', 'VARCHAR(150)'),
            ('unit_price', 'REAL DEFAULT 0.0'),
            ('quantity', 'INTEGER DEFAULT 1'),
            ('amount', 'REAL DEFAULT 0.0'),
            ('date', 'DATE'),
            ('period_month', 'VARCHAR(7)'),
            ('payment_method', "VARCHAR(30) DEFAULT 'Retenue sur salaire'"),
            ('status', "VARCHAR(20) DEFAULT 'pending'"),
            ('expense_id', 'INTEGER REFERENCES expenses(id)'),
            ('notes', 'TEXT'),
            ('recorded_by', 'INTEGER REFERENCES users(id)'),
            ('created_at', 'DATETIME')
        ])

        # 12. teacher_salary_payouts (Règlements effectifs des salaires nets)
        add_cols_if_missing('teacher_salary_payouts', [
            ('receipt_no', 'VARCHAR(30)'),
            ('teacher_id', 'INTEGER REFERENCES teachers(id)'),
            ('period_month', 'VARCHAR(7)'),
            ('gross_amount', 'REAL DEFAULT 0.0'),
            ('advances_deducted', 'REAL DEFAULT 0.0'),
            ('expenses_deducted', 'REAL DEFAULT 0.0'),
            ('prior_credit_deducted', 'REAL DEFAULT 0.0'),
            ('net_amount', 'REAL DEFAULT 0.0'),
            ('payment_date', 'DATE'),
            ('payment_method', "VARCHAR(30) DEFAULT 'Espèces'"),
            ('reference_no', 'VARCHAR(50)'),
            ('status', "VARCHAR(20) DEFAULT 'paid'"),
            ('expense_id', 'INTEGER REFERENCES expenses(id)'),
            ('notes', 'TEXT'),
            ('recorded_by', 'INTEGER REFERENCES users(id)'),
            ('created_at', 'DATETIME')
        ])

        # 13. teacher_charge_items (Catalogue dynamique des charges enseignants)
        add_cols_if_missing('teacher_charge_items', [
            ('name', 'VARCHAR(150)'),
            ('category', "VARCHAR(30) DEFAULT 'supplies'"),
            ('unit_price', 'REAL DEFAULT 0.0'),
            ('unit_label', "VARCHAR(50) DEFAULT 'unité'"),
            ('is_default', 'BOOLEAN DEFAULT 0'),
            ('active', 'BOOLEAN DEFAULT 1'),
            ('created_at', 'DATETIME')
        ])

        # 14. certificates (Attestation de Langue, Stage, Travail)
        add_cols_if_missing('certificates', [
            ('employee_id', 'INTEGER REFERENCES employees(id)'),
            ('teacher_id', 'INTEGER REFERENCES teachers(id)'),
            ('recipient_name', 'VARCHAR(150)'),
            ('cin', 'VARCHAR(30)'),
            ('cnss_no', 'VARCHAR(30)'),
            ('job_title', 'VARCHAR(120)'),
            ('department', 'VARCHAR(120)'),
            ('start_date', 'DATE'),
            ('end_date', 'DATE'),
            ('student_code', 'VARCHAR(50)'),
            ('birth_date', 'DATE'),
            ('birth_city', 'VARCHAR(80)'),
            ('level', 'VARCHAR(50)'),
            ('score_listening', 'REAL DEFAULT 0.0'),
            ('score_speaking', 'REAL DEFAULT 0.0'),
            ('score_reading', 'REAL DEFAULT 0.0'),
            ('score_writing', 'REAL DEFAULT 0.0'),
            ('overall_score', 'REAL DEFAULT 0.0')
        ])

        # 15. placement_questions (Listening / Audio support)
        add_cols_if_missing('placement_questions', [
            ('audio_url', 'VARCHAR(255)'),
            ('audio_script', 'TEXT'),
            ('max_plays', 'INTEGER DEFAULT 2')
        ])

        # Tables auto-creation (if missing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(120) UNIQUE NOT NULL,
                category VARCHAR(60) DEFAULT 'Général',
                contact_person VARCHAR(100),
                phone VARCHAR(30),
                email VARCHAR(120),
                address VARCHAR(255),
                city VARCHAR(60) DEFAULT 'Marrakech',
                ice VARCHAR(30),
                if_code VARCHAR(30),
                notes TEXT,
                active BOOLEAN DEFAULT 1,
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_charges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(150) NOT NULL,
                category VARCHAR(50) NOT NULL DEFAULT 'Loyer des locaux',
                amount REAL NOT NULL DEFAULT 0.0,
                day_of_month INTEGER DEFAULT 1,
                payment_method VARCHAR(50) DEFAULT 'Espèces',
                supplier_id INTEGER REFERENCES suppliers(id),
                supplier_name VARCHAR(120),
                beneficiary VARCHAR(150),
                active BOOLEAN DEFAULT 1,
                notes TEXT,
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(30) UNIQUE,
                title VARCHAR(150) NOT NULL,
                publisher VARCHAR(100),
                category VARCHAR(30) DEFAULT 'language',
                level VARCHAR(60),
                purchase_price REAL DEFAULT 0.0,
                sale_price REAL DEFAULT 0.0,
                stock_quantity INTEGER DEFAULT 0,
                min_stock_alert INTEGER DEFAULT 5,
                active BOOLEAN DEFAULT 1,
                notes TEXT,
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS book_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no VARCHAR(30),
                book_id INTEGER NOT NULL REFERENCES books(id),
                student_id INTEGER REFERENCES students(id),
                quantity INTEGER DEFAULT 1 NOT NULL,
                unit_price REAL NOT NULL,
                total_amount REAL NOT NULL,
                payment_method VARCHAR(20) DEFAULT 'cash',
                sale_date DATE NOT NULL,
                recorded_by INTEGER REFERENCES users(id),
                notes VARCHAR(255),
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id),
                enrollment_id INTEGER REFERENCES enrollments(id),
                amount REAL NOT NULL,
                type VARCHAR(20) DEFAULT 'avoir',
                note TEXT,
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS substitute_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL REFERENCES courses(id),
                original_teacher_id INTEGER REFERENCES teachers(id),
                substitute_teacher_id INTEGER NOT NULL REFERENCES teachers(id),
                session_date DATE NOT NULL,
                session_type VARCHAR(20) DEFAULT 'substitute',
                note TEXT,
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(150) NOT NULL,
                message TEXT NOT NULL,
                link VARCHAR(255),
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cert_number VARCHAR(50) UNIQUE,
                student_id INTEGER REFERENCES students(id),
                course_id INTEGER REFERENCES courses(id),
                cert_type VARCHAR(50) DEFAULT 'Attestation de Formation',
                title VARCHAR(150),
                issue_date DATE,
                mention VARCHAR(50) DEFAULT 'Très Bien',
                notes TEXT,
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blocked_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address VARCHAR(45) UNIQUE NOT NULL,
                reason VARCHAR(255) DEFAULT 'Multiple failed login attempts',
                failed_attempts INTEGER DEFAULT 5,
                is_blocked BOOLEAN DEFAULT 1,
                created_at DATETIME,
                blocked_until DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_type VARCHAR(20) DEFAULT 'charge',
                category VARCHAR(50) NOT NULL,
                description VARCHAR(255) NOT NULL,
                amount REAL NOT NULL,
                date DATE NOT NULL,
                payment_method VARCHAR(50) DEFAULT 'Espèces',
                reference_no VARCHAR(50),
                invoice_no VARCHAR(60),
                supplier_id INTEGER REFERENCES suppliers(id),
                supplier_name VARCHAR(120),
                due_date DATE,
                status VARCHAR(20) DEFAULT 'paid',
                paid_amount REAL DEFAULT 0.0,
                tax_amount REAL DEFAULT 0.0,
                receipt_file VARCHAR(255),
                notes TEXT,
                user_id INTEGER REFERENCES users(id),
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_advances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no VARCHAR(30) UNIQUE,
                teacher_id INTEGER NOT NULL REFERENCES teachers(id),
                amount REAL NOT NULL,
                date DATE NOT NULL,
                period_month VARCHAR(7) NOT NULL,
                payment_method VARCHAR(30) DEFAULT 'Espèces',
                reference_no VARCHAR(50),
                status VARCHAR(20) DEFAULT 'paid',
                expense_id INTEGER REFERENCES expenses(id),
                notes TEXT,
                recorded_by INTEGER REFERENCES users(id),
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no VARCHAR(30) UNIQUE,
                teacher_id INTEGER NOT NULL REFERENCES teachers(id),
                expense_type VARCHAR(30) DEFAULT 'copies',
                title VARCHAR(150) NOT NULL,
                unit_price REAL DEFAULT 0.0,
                quantity INTEGER DEFAULT 1,
                amount REAL NOT NULL,
                date DATE NOT NULL,
                period_month VARCHAR(7) NOT NULL,
                payment_method VARCHAR(30) DEFAULT 'Retenue sur salaire',
                status VARCHAR(20) DEFAULT 'pending',
                expense_id INTEGER REFERENCES expenses(id),
                notes TEXT,
                recorded_by INTEGER REFERENCES users(id),
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_salary_payouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no VARCHAR(30) UNIQUE,
                teacher_id INTEGER NOT NULL REFERENCES teachers(id),
                period_month VARCHAR(7) NOT NULL,
                gross_amount REAL DEFAULT 0.0,
                advances_deducted REAL DEFAULT 0.0,
                expenses_deducted REAL DEFAULT 0.0,
                net_amount REAL NOT NULL,
                payment_date DATE NOT NULL,
                payment_method VARCHAR(30) DEFAULT 'Espèces',
                reference_no VARCHAR(50),
                status VARCHAR(20) DEFAULT 'paid',
                expense_id INTEGER REFERENCES expenses(id),
                notes TEXT,
                recorded_by INTEGER REFERENCES users(id),
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_charge_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(150) NOT NULL,
                category VARCHAR(30) DEFAULT 'supplies',
                unit_price REAL DEFAULT 0.0,
                unit_label VARCHAR(50) DEFAULT 'unité',
                is_default BOOLEAN DEFAULT 0,
                active BOOLEAN DEFAULT 1,
                created_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_payment_visibility (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                is_visible BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME,
                UNIQUE(teacher_id, year, month)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tpv_teacher_ym ON teacher_payment_visibility(teacher_id, year, month)")

        conn.commit()
        conn.close()
    except Exception as e:
        print(">>> Auto migration notice:", e)


def seed_default_teacher_charges():
    """Pré-remplit les articles standards connus dans le catalogue des charges enseignants."""
    defaults = [
        ('Photocopies / Tirages de cours', 'copies', 0.50, 'page'),
        ('Marqueur pour tableau blanc', 'supplies', 8.00, 'marqueur'),
        ('Ramette de papier A4 (500 f.)', 'paper', 45.00, 'ramette'),
        ('Effaceur de tableau', 'supplies', 15.00, 'unité'),
        ('Lot Stylos & Fournitures', 'supplies', 5.00, 'lot'),
        ('Manuel / Livre scolaire', 'book', 0.00, 'livre'),
        ('Cahier de texte / Registre', 'supplies', 20.00, 'cahier'),
    ]
    try:
        if TeacherChargeItem.query.count() == 0:
            for name, cat, price, unit in defaults:
                item = TeacherChargeItem(name=name, category=cat, unit_price=price, unit_label=unit, is_default=True, active=True)
                db.session.add(item)
            db.session.commit()
            print(">>> Catalogue des charges enseignants initialisé avec les articles par défaut.")
    except Exception as e:
        db.session.rollback()
        print(">>> Notice seed charges:", e)



# ==============================================================================
# MODULE : TESTS DE NIVEAU POUR LES LANGUES (PLACEMENT TESTS)
# ==============================================================================

def get_placement_test_url(token):
    # 1. Setting from database (excluding localhost)
    pub = SH.get_setting('public_app_url', '').strip().rstrip('/')
    if pub and not ('localhost' in pub.lower() or '127.0.0.1' in pub):
        return f"{pub}/test/{token}"
    # 2. Check current request host, but strictly exclude localhost / 127.0.0.1 / local IPs
    try:
        from flask import has_request_context, request
        if has_request_context() and request.host:
            host = request.host.lower()
            if not ('localhost' in host or '127.0.0.1' in host or '0.0.0.0' in host):
                proto = request.headers.get('X-Forwarded-Proto', request.scheme or 'https')
                return f"{proto}://{request.host}/test/{token}"
    except Exception:
        pass
    # 3. Canonical Cloudflare Tunnel online domain
    return f"https://app.institutilas.com/test/{token}"


def generate_spintax_placement_test_invite(test, recipient_type='student', lang='ar', inst_name=None, inst_phone=None, test_url=None, ref_seed=None):
    """
    Generate an anti-ban WhatsApp invitation message for a placement test using Spintax variations.
    Includes:
      - Candidate Name
      - Target Language & Flag
      - Estimated duration (3-5 minutes)
      - Anti-guessing recommendation (cocher 'Je ne sais pas' si on ne sait pas)
      - Direct public test URL
      - Randomized greetings, intros, guidance, and closings
      - Unique anti-ban hash [Réf: #TEST-XXXX]
    Supports recipient_type='parent' or recipient_type='student'.
    Languages: lang='ar' or lang='fr'.
    """
    import random
    if not inst_name:
        inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    if not inst_phone:
        inst_phone = SH.get_setting('inst_phone', '')
    if not test_url:
        test_url = get_placement_test_url(test.token)

    seed = ref_seed if ref_seed is not None else random.randint(1000, 9999)
    cand_name = test.full_name or "Candidat"

    lang_data = {
        'Anglais': {'fr': 'Anglais', 'ar': 'اللغة الإنجليزية', 'flag': '🇬🇧'},
        'Français': {'fr': 'Français', 'ar': 'اللغة الفرنسية', 'flag': '🇫🇷'},
        'Espagnol': {'fr': 'Espagnol', 'ar': 'اللغة الإسبانية', 'flag': '🇪🇸'},
        'Allemand': {'fr': 'Allemand', 'ar': 'اللغة الألمانية', 'flag': '🇩🇪'}
    }.get(test.language, {'fr': test.language or 'Langue', 'ar': test.language or 'اللغات', 'flag': '🌐'})

    lang_fr = lang_data['fr']
    lang_ar = lang_data['ar']
    lang_flag = lang_data['flag']

    if recipient_type == 'parent':
        if lang == 'fr':
            greetings = [
                f"Bonjour chers parents de l'élève *{cand_name}* 🌸,\nL'équipe de *{inst_name}* vous adresse ses salutations les plus cordiales.",
                f"Chers parents d'élèves, bonjour 🌸,\nToute la direction pédagogique de *{inst_name}* vous remercie pour votre confiance.",
                f"Bonjour à toute la famille 🌸,\nL'administration de *{inst_name}* a le plaisir de prendre attache avec vous pour le parcours scolaire de votre enfant.",
                f"Chère famille de *{cand_name}*, salutations distinguées 🌸,\nNous vous transmettons ce message pour l'évaluation diagnostique de niveau."
            ]
            intros = [
                f"Afin d'orienter au mieux votre enfant vers le groupe d'apprentissage parfaitement adapté à son niveau, nous vous transmettons le lien direct de son *test de positionnement* en *{lang_fr}* :",
                f"Pour garantir une progression optimale et intégrer la classe adéquate, voici l'accès sécurisé au *test de niveau* en *{lang_fr}* de votre enfant :",
                f"Dans le cadre de son inscription, nous vous invitons à lui faire passer ce diagnostic linguistique rapide et intuitif :",
                f"Nous avons le plaisir de mettre à votre disposition la plateforme de test de niveau de *{inst_name}* pour orienter efficacement votre enfant :"
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 *TEST DE POSITIONNEMENT EN LIGNE*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"▫️ *Candidat(e) :* *{cand_name}*\n"
                f"▫️ *Langue évaluée :* {lang_flag} *{lang_fr}*\n"
                f"▫️ *Durée estimée :* ⏱️ *3 à 5 minutes chrono*\n"
                f"▫️ *Format :* Accessible directement sur smartphone\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 *Lien d'accès au test :*\n"
                f"👉 {test_url}\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            guides = [
                "💡 *Conseil :* Ce test évalue les compétences réelles. Encouragez votre enfant à cocher *(❓ Je ne sais pas)* s'il ignore une réponse plutôt que de deviner au hasard.",
                "💡 *Recommandation :* Pour un résultat fidèle, le test doit être passé individuellement dans un endroit calme, avec le son activé pour les courts extraits audio.",
                "💡 *Indication importante :* Une option *(❓ Je ne sais pas)* est disponible pour éviter les réponses au hasard et garantir une orientation pédagogique sur-mesure.",
                "💡 *Pratique :* Le test est fluide et rapide. Prévoyez des écouteurs pour les questions d'écoute afin de faciliter la compréhension."
            ]
            closings = [
                f"Dès validation du test, notre équipe pédagogique prendra connaissance des résultats pour vous conseiller le groupe idéal 🌟\nPour toute question, le secrétariat est joignable au : {inst_phone}",
                f"Nous souhaitons une excellente évaluation à votre enfant ! Toute notre équipe reste à votre écoute au {inst_phone}.",
                f"Merci pour votre collaboration et votre réactivité. L'accueil est à votre disposition au : {inst_phone}",
                f"Nous restons à votre entière disposition pour finaliser son inscription au {inst_phone}.\nAvec nos salutations les plus respectueuses."
            ]
        else:
            # Arabic Parent
            greetings = [
                f"السلام عليكم ورحمة الله تعالى وبركاته 🌸\nتحية تقدير واحترام لولي أمر التلميذ(ة) *{cand_name}*،",
                f"تحية طيبة ملؤها الود والاحترام 🌸\nإلى ولي أمر المتعلم(ة) *{cand_name}*، أسرة *{inst_name}* تحييكم أطيب تحية،",
                f"السلام عليكم ورحمة الله وبركاته 🌸\nأولياء أمور التلميذ(ة) العزيز(ة) *{cand_name}* الأفاضل،",
                f"تحية تربوية وتقديرية من إدارة *{inst_name}* 🌸\nإلى ولي أمر التلميذ(ة) *{cand_name}*،"
            ]
            intros = [
                f"في إطار تحديد الفوج والبرنامج التعليمي الأنسب لابنكم/ابنتكم، يسعدنا موافاتكم برابط *اختبار تحديد المستوى* الرقمي الخاص بـ *{lang_ar}* :",
                f"حرصاً منا على تسجيل التلميذ(ة) في المستوى الدقيق الذي يضمن تطوره وتألقه، نرسل لحضرتكم الرابط المباشر لاجتياز *اختبار المستوى* في *{lang_ar}* :",
                f"يشرف إدارة المعهد أن تضع رهن إشارتكم المنصة الرقمية لاجتياز اختبار التقويم الأولي في *{lang_ar}* لتحديد المجموعة المناسبة :",
                f"من أجل توجيه أكاديمي دقيق ومدروس، ندعوكم لمواكبة ابنكم/ابنتكم لاجتياز *اختبار تقييم المستوى* السريع والمعتمد :"
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 *اختبـار تحديـد المستـوى الأكاديمـي*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"▫️ *المترشح(ة) :* *{cand_name}*\n"
                f"▫️ *اللغة المستهدفة :* {lang_flag} *{lang_ar}*\n"
                f"▫️ *المدة المقدرة :* ⏱️ *3 إلى 5 دقائق فقط*\n"
                f"▫️ *طريقة الإجابة :* أسئلة سريعة ومباشرة من الهاتف\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 *رابط الاختبار المباشر :*\n"
                f"👉 {test_url}\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            guides = [
                "💡 *ملاحظة هامة :* الاختبار مصمم ليقيس المستوى الفعلي. يُرجى توجيهه بعدم التخمين واختيار خيار *(❓ لا أعلم)* عند عدم معرفة الإجابة، مع توفير مكان هادئ للاستماع.",
                "💡 *إرشادات :* الاختبار سريع وسلس ومناسب للهاتف الذكي. إذا تعذر معرفة أي جواب، يُفضّل اختيار *(❓ لا أعلم)* لضمان توجيه دقيق للقسم المناسب.",
                "💡 *نصيحة توجيهية :* للحصول على تقييم صحيح 100%، نوصي بالإجابة الشخصية بدون مساعدة، واختيار *(❓ لا أعلم)* للأسئلة غير المعروفة.",
                "💡 *تعليمات :* يُرجى فتح الرابط واستعمال سماعات الأذن للمقاطع الصوتية القصيرة. خيار *(❓ لا أعلم)* يساعدنا في اكتشاف مستواه الحقيقي بدقة."
            ]
            closings = [
                f"بمجرد انتهاء الاختبار، ستتوصل الإدارة بالنتيجة فوراً لإتمام التسجيل واقتراح الفوج الملائم 🌟\nلأي مساعدة، مكتب الاستقبال رهن إشارتكم عبر الرقم : {inst_phone}",
                f"نتمنى لابنكم/ابنتكم كامل التوفيق والتألق في هذا الاختبار 🌟\nفريق {inst_name} في خدمتكم دائماً : {inst_phone}",
                f"شاكرين لكم حسن تعاونكم الدائم وثقتكم الغالية بمؤسستنا 🌟\nللتواصل والاستفسار : {inst_phone}",
                f"نحن رهن إشارتكم لمواكبتكم في جميع مراحل التسجيل والتوجيه 🌟\nهاتف إدارة المعهد : {inst_phone}"
            ]
    else:
        # recipient_type == 'student'
        if lang == 'fr':
            greetings = [
                f"Bonjour cher(e) apprenant(e) *{cand_name}* 🌸,\nL'équipe de *{inst_name}* te souhaite la bienvenue !",
                f"Cher(e) étudiant(e) *{cand_name}*, bonjour 🌸,\nToute l'équipe pédagogique de *{inst_name}* est ravie de t'accompagner.",
                f"Bonjour *{cand_name}* 🌸,\nVoici ton accès officiel pour réaliser ton test d'évaluation linguistique.",
                f"Salutations cordiales *{cand_name}* 🌸,\nL'administration de *{inst_name}* te contacte pour la préparation de ton inscription."
            ]
            intros = [
                f"Afin de déterminer précisément ton niveau actuel et de t'intégrer dans le groupe le plus stimulant, voici ton *test de positionnement* en *{lang_fr}* :",
                f"Pour démarrer ta formation dans les meilleures conditions et cibler tes besoins, nous t'invitons à passer ce diagnostic rapide :",
                f"Voici le lien sécurisé direct vers ton test de niveau digital en *{lang_fr}* :",
                f"Avant de finaliser ton inscription, découvre ton niveau réel grâce à ce test rapide et intuitif :"
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 *TEST DE POSITIONNEMENT EN LIGNE*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"▫️ *Apprenant(e) :* *{cand_name}*\n"
                f"▫️ *Langue du test :* {lang_flag} *{lang_fr}*\n"
                f"▫️ *Durée estimée :* ⏱️ *3 à 5 minutes chrono*\n"
                f"▫️ *Support :* Smartphone ou Ordinateur\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 *Lien direct d'accès au test :*\n"
                f"👉 {test_url}\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            guides = [
                "💡 *Conseil :* Le test ne prend que 3 à 5 minutes. Ne cherche pas sur Internet : si tu ne connais pas une réponse, clique simplement sur *(❓ Je ne sais pas)*.",
                "💡 *Recommandation :* Installe-toi au calme avec des écouteurs pour les questions d'audio. Le bouton *(❓ Je ne sais pas)* évite le hasard et garantit un groupe adapté.",
                "💡 *Astuce :* Réponds spontanément. Ce n'est pas un examen éliminatoire mais un outil pour mesurer ton niveau réel et te faire progresser !",
                "💡 *Important :* En évitant de deviner au hasard grâce à l'option *(❓ Je ne sais pas)*, tu seras placé exactement dans la classe qui correspond à ton profil."
            ]
            closings = [
                f"Bonne chance pour ton test ! Nous avons hâte de t'accueillir pour ta première séance 🚀\nPour toute question, le secrétariat est joignable au : {inst_phone}",
                f"Dès réception de tes réponses, nous validons ton groupe et ton planning 🚀\nContact de l'institut : {inst_phone}",
                f"Nous te souhaitons un plein succès dans ton parcours linguistique 🚀\nL'administration reste à ton écoute au {inst_phone}.",
                f"À très vite dans nos cours ! N'hésite pas si tu as la moindre question : {inst_phone}"
            ]
        else:
            # Arabic Student
            greetings = [
                f"السلام عليكم ورحمة الله وبركاته 🌸\nأهلاً بك عزيزي(تي) *{cand_name}*، أسرة *{inst_name}* تحييك،",
                f"تحية طيبة ملؤها التقدير والتشجيع 🌸\nعزيزي(تي) المتعلم(ة) *{cand_name}*،",
                f"السلام عليكم ورحمة الله تعالى وبركاته 🌸\nالمتدرب(ة) الفاضل(ة) *{cand_name}*، نتمنى أن تكون بأفضل حال،",
                f"مرحباً بك *{cand_name}* 🌸\nيسر إدارة معهد *{inst_name}* التواصل معك لانطلاقة دورتك التكوينية،"
            ]
            intros = [
                f"من أجل تحديد مستواك بدقة وتوجيهك للفوج الأنسب لقدراتك وطموحاتك، نضع بين يديك رابط *اختبار تحديد المستوى* في *{lang_ar}* :",
                f"استعداداً لبدء دورتك التكوينية في أفضل الظروف، ندعوك لاجتياز هذا التقييم الأولي السريع في *{lang_ar}* :",
                f"إليك الرابط المباشر والخاص بك لاجتياز اختبار تقييم المستوى الرقمي والمعتمد لدى معهدنا :",
                f"لبدء تجربتك التعليمية بنجاح، يُرجى اجتياز اختبار المستوى السريع لتحديد برنامجك التكويني الملائم :"
            ]
            card = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 *اختبـار تحديـد المستـوى الأكاديمـي*\n"
                f"🏛️ *{inst_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"▫️ *المستفيد(ة) :* *{cand_name}*\n"
                f"▫️ *اللغة المختارة :* {lang_flag} *{lang_ar}*\n"
                f"▫️ *المدة المقدرة :* ⏱️ *3 إلى 5 دقائق فقط*\n"
                f"▫️ *طريقة الاجتياز :* عبر هاتفك الذكي مباشرة\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 *رابط الاختبار المباشر :*\n"
                f"👉 {test_url}\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            guides = [
                "💡 *نصيحة هامة :* الاختبار سريع (3-5 دقائق). أجب بمفردك بدون قلق، وإذا واجهت سؤالاً لم تعرفه، اختر خيار *(❓ لا أعلم)* دون تردد لتحديد مستواك الحقيقي.",
                "💡 *إرشادات :* استعمل هاتفك في مكان هادئ واستخدم السماعات للاستماع. اختيار *(❓ لا أعلم)* يساعدنا في وضعك في الفوج المناسب لك تماماً.",
                "💡 *توجيه :* لا تخمن الإجابات عشوائياً، فالهدف هو اكتشاف مستواك الفعلي. خيار *(❓ لا أعلم)* متاح دائماً.",
                "💡 *معلومة :* الاختبار يغطي المستويات الأساسية والمتوسطة بطريقة تفاعلية وممتعة لمساعدتك على الانطلاق بقوة."
            ]
            closings = [
                f"نتمنى لك كامل التوفيق والتألق في هذا الاختبار ونحن بانتظارك في معهدنا 🚀\nلأي مساعدة تواصل معنا عبر : {inst_phone}",
                f"بمجرد إنهائك للاختبار، سيقوم مستشار التوجيه بالاطلاع على نتيجتك لإتمام تسجيلك 🚀\nفريقنا رهن إشارتك : {inst_phone}",
                f"بالتوفيق والنجاح الدائم في مسيرتك التعليمية وتطوير مهاراتك معنا 🚀\nرقم المعهد : {inst_phone}",
                f"نحن متحمسون لانضمامك إلى برامجنا اللغوية المميزة 🚀\nلأي استفسار : {inst_phone}"
            ]

    g = random.choice(greetings)
    intro = random.choice(intros)
    guide = random.choice(guides)
    c = random.choice(closings)
    ref_tag = f"[Réf: #TEST-{seed}]"

    return f"{g}\n\n{intro}\n\n{card}\n\n{guide}\n\n{c}\n{ref_tag}"


def generate_placement_qr_bytes(target_url):
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#0B3D6E', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()


@app.route('/placement-tests')
@login_required
@role_required('admin', 'secretary')
def placement_tests():
    query_search = request.args.get('q', '').strip()
    selected_lang = request.args.get('lang', '').strip()
    selected_status = request.args.get('status', '').strip()
    
    # Auto-show QR if coming from creation redirect
    auto_id = request.args.get('auto_qr')
    auto_test = PlacementTest.query.get(auto_id) if auto_id else None

    q = PlacementTest.query
    if query_search:
        term = f"%{query_search}%"
        q = q.filter(
            db.or_(
                PlacementTest.first_name.ilike(term),
                PlacementTest.last_name.ilike(term),
                PlacementTest.phone.ilike(term)
            )
        )
    if selected_lang:
        q = q.filter_by(language=selected_lang)
    if selected_status == 'pending':
        q = q.filter_by(status='pending')
    elif selected_status == 'completed':
        q = q.filter_by(status='completed', enrolled_course_id=None)
    elif selected_status == 'enrolled':
        q = q.filter(PlacementTest.enrolled_course_id != None)

    tests_list = q.order_by(PlacementTest.id.desc()).all()

    total_tests = PlacementTest.query.count()
    pending_tests = PlacementTest.query.filter_by(status='pending').count()
    completed_tests = PlacementTest.query.filter_by(status='completed').count()
    enrolled_tests = PlacementTest.query.filter(PlacementTest.enrolled_course_id != None).count()

    return render_template(
        'placement_tests/index.html',
        tests=tests_list,
        total_tests=total_tests,
        pending_tests=pending_tests,
        completed_tests=completed_tests,
        enrolled_tests=enrolled_tests,
        search_query=query_search,
        selected_lang=selected_lang,
        selected_status=selected_status,
        auto_show_qr_id=auto_test.id if auto_test else None,
        auto_show_name=auto_test.full_name if auto_test else None,
        auto_show_lang=auto_test.language if auto_test else None,
        auto_show_token=auto_test.token if auto_test else None,
        auto_show_phone=auto_test.phone if auto_test else None
    )


@app.route('/placement-tests/new', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def placement_test_new():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    phone = request.form.get('phone', '').strip()
    whatsapp = request.form.get('whatsapp', '').strip() or phone
    language = request.form.get('language', 'Anglais').strip()
    school_level = request.form.get('school_level', '').strip()
    birth_date = parse_date(request.form.get('birth_date'))
    objective = request.form.get('objective', '').strip()
    notes = request.form.get('notes', '').strip()

    if not first_name or not last_name:
        flash('Veuillez renseigner le nom et prénom du candidat.', 'danger')
        return redirect(url_for('placement_tests'))

    # Generate unique session token
    tok = uuid.uuid4().hex[:16]

    test = PlacementTest(
        token=tok,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        whatsapp=whatsapp,
        language=language,
        school_level=school_level,
        birth_date=birth_date,
        objective=objective,
        notes=notes,
        status='pending',
        is_submitted=False,
        created_by=current_user().id if current_user() else None
    )
    db.session.add(test)
    db.session.commit()

    log_action('placement_test_create', f"Pré-inscription test {language} pour {test.full_name}")
    flash(f"Session de test de niveau générée pour {test.full_name} ({language}) !", 'success')

    return redirect(url_for('placement_tests', auto_qr=test.id))


@app.route('/placement-tests/<int:test_id>')
@login_required
@role_required('admin', 'secretary')
def placement_test_view(test_id):
    test = PlacementTest.query.get_or_404(test_id)
    
    # Parse answers breakdown if available
    answers_list = []
    skills_breakdown = {}
    if test.answers_json:
        try:
            answers_list = json.loads(test.answers_json)
            for a in answers_list:
                cat = a.get('category') or 'Général'
                if cat not in skills_breakdown:
                    skills_breakdown[cat] = {'score': 0, 'total': 0, 'pct': 0}
                skills_breakdown[cat]['total'] += 1
                if a.get('is_correct'):
                    skills_breakdown[cat]['score'] += 1
            for cat in skills_breakdown:
                t = skills_breakdown[cat]['total']
                s = skills_breakdown[cat]['score']
                skills_breakdown[cat]['pct'] = round((s / t * 100), 1) if t > 0 else 0
        except Exception:
            pass

    # Fetch language courses for assignment
    available_courses = Course.query.filter(
        Course.active == True,
        Course.category == 'language',
        Course.language == test.language
    ).order_by(Course.level, Course.name).all()

    if not available_courses:
        # Fallback to all language courses
        available_courses = Course.query.filter_by(active=True, category='language').order_by(Course.name).all()

    rec_code = (test.recommended_level or '').split('(')[0].strip() if test.recommended_level else ''
    suggested_courses = []
    other_courses = []
    for c in available_courses:
        c_lvl = c.level or ''
        if rec_code and rec_code in c_lvl:
            suggested_courses.append(c)
        else:
            other_courses.append(c)

    return render_template(
        'placement_tests/view.html',
        test=test,
        answers_list=answers_list,
        skills_breakdown=skills_breakdown,
        available_courses=available_courses,
        suggested_courses=suggested_courses,
        other_courses=other_courses
    )


@app.route('/placement-tests/<int:test_id>/qr')
@login_required
@role_required('admin', 'secretary')
def placement_test_qr(test_id):
    test = PlacementTest.query.get_or_404(test_id)
    return render_template('placement_tests/qr_print.html', test=test)


@app.route('/placement-tests/<int:test_id>/qr-image')
def placement_test_qr_image(test_id):
    test = PlacementTest.query.get_or_404(test_id)
    url = get_placement_test_url(test.token)
    img_bytes = generate_placement_qr_bytes(url)
    return Response(img_bytes, mimetype='image/png')


# ---------------------------------------------------------------------------
# WhatsApp Placement Test Link (Anti-Ban Spintax Solution)
# ---------------------------------------------------------------------------
@app.route('/api/placement-tests/<int:test_id>/whatsapp_data')
@login_required
def api_placement_test_whatsapp_data(test_id):
    test = PlacementTest.query.get_or_404(test_id)
    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '')
    test_url = get_placement_test_url(test.token)

    # Resolve candidate & parent phone
    stu = None
    if test.enrolled_student_id:
        stu = Student.query.get(test.enrolled_student_id)
    if not stu and test.phone:
        stu = Student.query.filter((Student.phone == test.phone) | (Student.parent_phone == test.phone)).first()

    raw_student_phone = test.phone or (stu.phone if stu else '')
    raw_parent_phone = (stu.parent_phone if (stu and stu.parent_phone) else '')
    if not raw_parent_phone and test.whatsapp and test.whatsapp != test.phone:
        raw_parent_phone = test.whatsapp

    clean_student = _clean_wa_phone(raw_student_phone)
    clean_parent = _clean_wa_phone(raw_parent_phone)

    is_young = (test.school_level in ['Primaire', 'Collégien']) if test.school_level else False
    default_recip = 'parent' if (is_young and clean_parent) else 'student' if clean_student else 'parent'

    # Pre-generate Spintax messages
    msg_ar_student = generate_spintax_placement_test_invite(test, recipient_type='student', lang='ar', inst_name=inst_name, inst_phone=inst_phone, test_url=test_url)
    msg_fr_student = generate_spintax_placement_test_invite(test, recipient_type='student', lang='fr', inst_name=inst_name, inst_phone=inst_phone, test_url=test_url)
    msg_ar_parent = generate_spintax_placement_test_invite(test, recipient_type='parent', lang='ar', inst_name=inst_name, inst_phone=inst_phone, test_url=test_url)
    msg_fr_parent = generate_spintax_placement_test_invite(test, recipient_type='parent', lang='fr', inst_name=inst_name, inst_phone=inst_phone, test_url=test_url)

    return jsonify({
        'success': True,
        'test_id': test.id,
        'candidate_name': test.full_name,
        'language': test.language,
        'test_url': test_url,
        'raw_student_phone': raw_student_phone,
        'clean_student_phone': clean_student,
        'raw_parent_phone': raw_parent_phone,
        'clean_parent_phone': clean_parent,
        'default_recipient': default_recip,
        'messages': {
            'ar_student': msg_ar_student,
            'fr_student': msg_fr_student,
            'ar_parent': msg_ar_parent,
            'fr_parent': msg_fr_parent
        }
    })


@app.route('/placement-tests/<int:test_id>/send_whatsapp')
@login_required
def placement_test_send_whatsapp(test_id):
    test = PlacementTest.query.get_or_404(test_id)
    recip = request.args.get('recipient', 'student').strip()
    lang = request.args.get('lang', 'ar').strip()
    inst_name = SH.get_setting('inst_name', 'Institut ILAS')
    inst_phone = SH.get_setting('inst_phone', '')
    test_url = get_placement_test_url(test.token)

    stu = None
    if test.enrolled_student_id:
        stu = Student.query.get(test.enrolled_student_id)
    if not stu and test.phone:
        stu = Student.query.filter((Student.phone == test.phone) | (Student.parent_phone == test.phone)).first()

    override_phone = request.args.get('phone', '').strip()
    if override_phone:
        target_phone = override_phone
    elif recip == 'parent':
        target_phone = (stu.parent_phone if (stu and stu.parent_phone) else (test.whatsapp if test.whatsapp != test.phone else test.phone))
    else:
        target_phone = test.phone or (stu.phone if stu else '')

    clean_p = _clean_wa_phone(target_phone)
    msg = generate_spintax_placement_test_invite(test, recipient_type=recip, lang=lang, inst_name=inst_name, inst_phone=inst_phone, test_url=test_url)

    if clean_p:
        wa_url = f"https://wa.me/{clean_p}?text={quote(msg)}"
        return redirect(wa_url)
    else:
        flash(f"Numéro WhatsApp introuvable pour {recip} ({test.full_name})", "warning")
        return redirect(url_for('placement_test_view', test_id=test.id))



@app.route('/placement-tests/<int:test_id>/assign', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def placement_test_assign(test_id):
    test = PlacementTest.query.get_or_404(test_id)
    course_id = request.form.get('course_id')

    if not course_id:
        flash('Veuillez sélectionner un cours.', 'danger')
        return redirect(url_for('placement_test_view', test_id=test.id))

    course = Course.query.get_or_404(course_id)

    # 1. Find or create Student
    stu = None
    if test.enrolled_student_id:
        stu = Student.query.get(test.enrolled_student_id)
    elif test.phone:
        stu = Student.query.filter_by(phone=test.phone).first()

    if not stu:
        stu = Student(
            code=SH.gen_code('student_prefix', 'next_student_number'),
            first_name=test.first_name,
            last_name=test.last_name,
            phone=test.phone,
            whatsapp=test.whatsapp or test.phone,
            email=test.email,
            birth_date=test.birth_date,
            school_level=test.school_level,
            notes=f"Inscrit suite au test de niveau {test.language} (Score: {int(test.score)}/{int(test.max_score)} - {test.recommended_level})",
            created_by=current_user().id if current_user() else None
        )
        db.session.add(stu)
        db.session.flush()

    # 2. Check if already enrolled in this course
    existing_enroll = Enrollment.query.filter_by(student_id=stu.id, course_id=course.id, status='active').first()
    if not existing_enroll:
        price = course.price_per_month or course.price or 0.0
        enroll = Enrollment(
            student_id=stu.id,
            course_id=course.id,
            enroll_date=date.today(),
            monthly_price=price,
            calculated_price=price,
            status='active',
            notes=f"Orientation automatique suite au test de niveau ({test.recommended_level})",
            created_by=current_user().id if current_user() else None
        )
        db.session.add(enroll)

    test.enrolled_student_id = stu.id
    test.enrolled_course_id = course.id
    test.mismatch_dismissed = True
    db.session.commit()

    log_action('placement_test_assign', f"Affectation {stu.full_name} -> {course.name}")
    flash(f"Félicitations ! L'élève {stu.full_name} a été affecté et inscrit avec succès dans le cours {course.name} !", 'success')

    return redirect(url_for('student_view', sid=stu.id))


@app.route('/placement-tests/<int:test_id>/dismiss_mismatch', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def placement_test_dismiss_mismatch(test_id):
    test = PlacementTest.query.get_or_404(test_id)
    test.mismatch_dismissed = True
    db.session.commit()
    log_action('placement_test_mismatch_dismissed', f"Level mismatch alert dismissed for test {test.id} ({test.full_name})")
    flash("L'alerte de changement de niveau a été marquée comme traitée avec succès.", "success")
    redirect_to = request.form.get('redirect_to')
    if redirect_to:
        return redirect(redirect_to)
    if test.enrolled_student_id:
        return redirect(url_for('student_view', sid=test.enrolled_student_id))
    return redirect(url_for('placement_test_view', test_id=test.id))


@app.route('/placement-tests/<int:test_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def placement_test_delete(test_id):
    test = PlacementTest.query.get_or_404(test_id)
    name = test.full_name
    db.session.delete(test)
    db.session.commit()
    log_action('placement_test_delete', f"Test {name} supprimé")
    flash(f"Le test de {name} a été supprimé.", 'warning')
    return redirect(url_for('placement_tests'))


@app.route('/placement-tests/<int:test_id>/reset', methods=['POST'])
@login_required
@role_required('admin', 'secretary')
def placement_test_reset(test_id):
    test = PlacementTest.query.get_or_404(test_id)
    test.status = 'pending'
    test.is_submitted = False
    test.score = 0.0
    test.max_score = 0.0
    test.percentage = 0.0
    test.recommended_level = None
    test.answers_json = None
    test.submitted_at = None
    test.enrolled_course_id = None
    test.enrolled_student_id = None
    db.session.commit()
    log_action('placement_test_reset', f"Test {test.full_name} réinitialisé")
    flash(f"Le test de {test.full_name} a été réinitialisé. Le candidat peut à nouveau passer le test via son QR Code !", 'info')
    return redirect(url_for('placement_test_view', test_id=test.id))



@app.route('/placement-tests/questions')
@login_required
@role_required('admin', 'secretary')
def placement_questions_list():
    selected_lang = request.args.get('lang', '').strip()
    selected_level = request.args.get('level', '').strip()

    q = PlacementQuestion.query.filter_by(active=True)
    if selected_lang:
        q = q.filter_by(language=selected_lang)
    if selected_level:
        q = q.filter_by(level=selected_level)

    questions = q.order_by(PlacementQuestion.language, PlacementQuestion.level, PlacementQuestion.order_num).all()

    return render_template(
        'placement_tests/questions.html',
        questions=questions,
        selected_lang=selected_lang,
        selected_level=selected_level
    )


# ==============================================================================
# CANDIDATE MOBILE TEST INTERFACE (PUBLIC ACCESSIBLE VIA QR CODE)
# ==============================================================================

@app.route('/test/<token>', methods=['GET', 'POST'])
def candidate_take_test(token):
    test = PlacementTest.query.filter_by(token=token).first_or_404()

    # STRICT SECURITY: Once submitted, link can never be retaken!
    if test.is_submitted or test.status == 'completed':
        return render_template('placement_tests/already_completed.html', test=test)

    # Fetch questions for this test language ordered by order_num (A1 -> A2 -> B1)
    questions = PlacementQuestion.query.filter_by(
        language=test.language,
        active=True
    ).order_by(PlacementQuestion.order_num).all()

    if request.method == 'POST':
        # Double check to prevent race condition
        if test.is_submitted or test.status == 'completed':
            return render_template('placement_tests/already_completed.html', test=test)

        total_score = 0
        score_a1 = 0
        total_a1 = 0
        score_a2 = 0
        total_a2 = 0
        score_b1 = 0
        total_b1 = 0
        answers_log = []

        for q in questions:
            chosen = (request.form.get(f"q_{q.id}") or '').strip()
            # If student chose 'IDK' (Je ne sais pas), it is recorded as non-guessed zero
            is_idk = (chosen == 'IDK')
            is_correct = (chosen == q.correct_option) if not is_idk else False
            if is_correct:
                total_score += 1

            # Tally scores per CEFR level
            q_lvl = (q.level or '').upper()
            if 'A1' in q_lvl:
                total_a1 += 1
                if is_correct: score_a1 += 1
            elif 'A2' in q_lvl:
                total_a2 += 1
                if is_correct: score_a2 += 1
            elif 'B1' in q_lvl:
                total_b1 += 1
                if is_correct: score_b1 += 1

            answers_log.append({
                'question_id': q.id,
                'level': q.level,
                'category': q.category,
                'question': q.question_text,
                'chosen': 'IDK' if is_idk else (chosen or 'Non répondu'),
                'correct': q.correct_option,
                'is_correct': is_correct,
                'is_idk': is_idk,
                'audio_url': q.audio_url,
                'audio_script': q.audio_script
            })

        max_score = len(questions)
        percentage = round((total_score / max_score * 100), 1) if max_score > 0 else 0.0

        # Cambridge/Oxford Linguistic Mastery Gate Algorithm:
        # Prevents lucky guessing from skipping foundational levels:
        if total_a1 > 0 and score_a1 < 3:
            # Failed foundational A1 (scored less than 3/4 on basic grammar/vocab) -> Placed in A1
            rec_level = 'A1 (Débutant)'
        elif (score_a1 >= 3 and score_a2 >= 3 and score_b1 >= 3) or (total_score >= 10 and score_a1 >= 3):
            # Mastered A1 (>=3), mastered A2 (>=3), and demonstrated solid B1 skills (>=3) -> Placed in B1
            rec_level = 'B1 (Intermédiaire)'
        elif (score_a1 >= 3 and score_a2 >= 2) or (total_score >= 6 and score_a1 >= 3):
            # Solid A1 foundation + basic A2 skills -> Placed in A2
            rec_level = 'A2 (Élémentaire)'
        else:
            rec_level = 'A1 (Débutant)'

        test.score = float(total_score)
        test.max_score = float(max_score)
        test.percentage = percentage
        test.recommended_level = rec_level
        test.answers_json = json.dumps(answers_log)
        test.is_submitted = True
        test.status = 'completed'
        test.submitted_at = datetime.utcnow()
        db.session.commit()

        return render_template('placement_tests/success_submitted.html', test=test)

    return render_template('placement_tests/take_test.html', test=test, questions=questions)


@app.route('/lapagetest')
def lapagetest_alias():
    """Friendly route alias if requested directly."""
    return render_template('placement_tests/already_completed.html', test=PlacementTest(
        first_name='Cher', last_name='Candidat', language='Langues', submitted_at=datetime.utcnow()
    ))


# ==============================================================================
# MODULE : CAHIER DE LIAISON & CONSIGNES INTERNES (STAFF NOTES)
# ==============================================================================

@app.route('/staff-notes')
@login_required
def staff_notes():
    u = current_user()
    active_tab = request.args.get('tab', 'staff').strip()
    selected_priority = request.args.get('priority', '').strip()
    selected_category = request.args.get('category', '').strip()
    search_q = request.args.get('q', '').strip()

    # Base query
    q = StaffNote.query

    if selected_priority:
        q = q.filter_by(priority=selected_priority)
    if selected_category:
        q = q.filter_by(category=selected_category)
    if search_q:
        term = f"%{search_q}%"
        q = q.join(StaffNote.author).filter(
            db.or_(
                StaffNote.title.ilike(term),
                StaffNote.content.ilike(term),
                User.full_name.ilike(term),
                User.username.ilike(term)
            )
        )

    # Apply tab logic
    if active_tab in ('active', 'teachers', 'staff'):
        q = q.filter_by(status='pending')
    elif active_tab == 'assigned_me':
        q = q.filter_by(status='pending')
    elif active_tab == 'my_sent':
        q = q.filter_by(author_id=u.id)
    elif active_tab == 'resolved':
        q = q.filter_by(status='done')

    all_notes = q.order_by(StaffNote.is_pinned.desc(), StaffNote.id.desc()).all()

    # Security filtering by user visibility and author role
    visible_notes = []
    for n in all_notes:
        if not n.is_visible_to(u):
            continue
        is_from_teacher = bool(n.author and n.author.role == 'teacher')
        if active_tab == 'teachers':
            if is_from_teacher:
                visible_notes.append(n)
        elif active_tab == 'staff':
            if not is_from_teacher:
                visible_notes.append(n)
        elif active_tab == 'assigned_me':
            if n.target_type == 'all' or (u.id in n.get_target_ids()):
                visible_notes.append(n)
        else:
            visible_notes.append(n)

    # Compute summary counts
    all_pending = StaffNote.query.filter_by(status='pending').all()
    pending_count = sum(1 for n in all_pending if n.is_visible_to(u))
    urgent_count = sum(1 for n in all_pending if n.priority == 'urgent' and n.is_visible_to(u))
    teacher_pending_count = sum(1 for n in all_pending if n.is_visible_to(u) and n.author and n.author.role == 'teacher')
    staff_pending_count = sum(1 for n in all_pending if n.is_visible_to(u) and (not n.author or n.author.role in ('admin', 'secretary')))
    
    today_start = datetime.combine(date.today(), datetime.min.time())
    resolved_today_count = StaffNote.query.filter(
        StaffNote.status == 'done',
        StaffNote.resolved_at >= today_start
    ).count()

    # Active staff users for recipient checkboxes in modal
    active_users = User.query.filter_by(active=True).order_by(User.role, User.full_name).all()

    return render_template(
        'staff_notes/index.html',
        notes=visible_notes,
        active_tab=active_tab,
        selected_priority=selected_priority,
        selected_category=selected_category,
        search_query=search_q,
        pending_count=pending_count,
        urgent_count=urgent_count,
        teacher_pending_count=teacher_pending_count,
        staff_pending_count=staff_pending_count,
        resolved_today_count=resolved_today_count,
        active_users=active_users
    )


@app.route('/staff-notes/new', methods=['POST'])
@login_required
def staff_notes_new():
    u = current_user()
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    priority = request.form.get('priority', 'normal').strip()
    category = request.form.get('category', 'general').strip()
    due_date = parse_date(request.form.get('due_date'))
    is_pinned = bool(request.form.get('is_pinned'))

    if not title or not content:
        flash('Veuillez renseigner le titre et le contenu de la note.', 'danger')
        return redirect(url_for('staff_notes'))

    target_all = bool(request.form.get('target_all'))
    selected_uids = request.form.getlist('target_user_ids')

    if target_all or not selected_uids:
        target_type = 'all'
        target_json = None
    else:
        target_type = 'specific'
        clean_uids = []
        for x in selected_uids:
            try: clean_uids.append(int(x))
            except: pass
        target_json = json.dumps(clean_uids)

    note = StaffNote(
        title=title,
        content=content,
        priority=priority,
        category=category,
        due_date=due_date,
        is_pinned=is_pinned,
        author_id=u.id,
        target_type=target_type,
        target_user_ids=target_json,
        status='pending'
    )
    db.session.add(note)
    db.session.commit()

    log_action('staff_note_create', f"Note de liaison créée : {title} par {u.full_name or u.username}")
    flash('Consigne / Note de liaison enregistrée avec succès !', 'success')
    return redirect(url_for('staff_notes'))


@app.route('/staff-notes/<int:note_id>/toggle-status', methods=['POST'])
@login_required
def staff_notes_toggle_status(note_id):
    u = current_user()
    note = StaffNote.query.get_or_404(note_id)

    if not note.is_visible_to(u):
        flash('Accès non autorisé à cette consigne.', 'danger')
        return redirect(url_for('staff_notes'))

    if note.status == 'pending':
        note.status = 'done'
        note.resolved_by_id = u.id
        note.resolved_at = datetime.utcnow()
        note.resolution_note = request.form.get('resolution_note', '').strip() or None
        log_action('staff_note_resolve', f"Note #{note.id} marquée comme traitée par {u.full_name or u.username}")
        flash(f'La consigne "{note.title}" a été marquée comme traitée ✅', 'success')
    else:
        note.status = 'pending'
        note.resolved_by_id = None
        note.resolved_at = None
        note.resolution_note = None
        log_action('staff_note_reopen', f"Note #{note.id} rouverte par {u.full_name or u.username}")
        flash(f'La consigne "{note.title}" a été rouverte 🔄', 'info')

    db.session.commit()
    return redirect(url_for('staff_notes'))


@app.route('/staff-notes/<int:note_id>/mark-read', methods=['POST'])
@login_required
def staff_notes_mark_read(note_id):
    u = current_user()
    note = StaffNote.query.get_or_404(note_id)
    if note.is_visible_to(u):
        note.mark_read(u.id)
        db.session.commit()
    return jsonify({'success': True})


@app.route('/staff-notes/<int:note_id>/delete', methods=['POST'])
@login_required
def staff_notes_delete(note_id):
    u = current_user()
    note = StaffNote.query.get_or_404(note_id)

    # Only author or admin can delete
    if u.role != 'admin' and note.author_id != u.id:
        flash('Vous ne pouvez pas supprimer cette note.', 'danger')
        return redirect(url_for('staff_notes'))

    t = note.title
    db.session.delete(note)
    db.session.commit()
    log_action('staff_note_delete', f"Note supprimée : {t}")
    flash(f'La note "{t}" a été supprimée.', 'warning')
    return redirect(url_for('staff_notes'))


if __name__ == '__main__':
    with app.app_context():
        auto_migrate_db()
        db.create_all()
        SH.seed_defaults()
        seed_default_teacher_charges()
        if User.query.count() == 0:
            a = User(username='admin', full_name='Administrateur', role='admin', active=True)
            a.set_password('admin')
            db.session.add(a)
            db.session.commit()
            print(">>> Admin créé : admin/admin")
        # Automatic startup backup
        try:
            bk_file = create_auto_backup('startup')
            if bk_file:
                print(f">>> Sauvegarde automatique de la base effectuée : {bk_file}")
        except Exception:
            pass
    import socket
    port = int(os.environ.get('PORT', sys.argv[1] if len(sys.argv) > 1 else 8080))
    local_ip = '127.0.0.1'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print(f">>> Application démarrée localement : http://localhost:{port}")
    print(f">>> Accessible sur le Réseau Local (Wi-Fi/LAN) via : http://{local_ip}:{port}")
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or app.debug is False:
        threading.Thread(target=open_browser, args=(port, f'http://localhost:{port}'), daemon=True).start()
    app.run(host='0.0.0.0', port=port, debug=True)
