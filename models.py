# -*- coding: utf-8 -*-
import re
from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import synonym, validates
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


MATIERE_CONFIG = {
    'Français': {
        'icon': '🇫🇷',
        'color': '#2563eb',
        'bg': '#eff6ff',
        'border': '#bfdbfe',
        'priority': 1,
        'name_ar': 'اللغة الفرنسية'
    },
    'Anglais': {
        'icon': '🇬🇧',
        'color': '#0284c7',
        'bg': '#f0f9ff',
        'border': '#bae6fd',
        'priority': 2,
        'name_ar': 'اللغة الإنجليزية'
    },
    'Espagnol': {
        'icon': '🇪🇸',
        'color': '#ea580c',
        'bg': '#fff7ed',
        'border': '#fed7aa',
        'priority': 3,
        'name_ar': 'اللغة الإسبانية'
    },
    'Allemand': {
        'icon': '🇩🇪',
        'color': '#b45309',
        'bg': '#fefce8',
        'border': '#fef08a',
        'priority': 4,
        'name_ar': 'اللغة الألمانية'
    },
    'Mathématiques': {
        'icon': '📐',
        'color': '#7c3aed',
        'bg': '#faf5ff',
        'border': '#e9d5ff',
        'priority': 5,
        'name_ar': 'الرياضيات'
    },
    'Physique-Chimie': {
        'icon': '⚗️',
        'color': '#0891b2',
        'bg': '#ecfeff',
        'border': '#a5f3fc',
        'priority': 6,
        'name_ar': 'الفيزياء والكيمياء'
    },
    'SVT': {
        'icon': '🧬',
        'color': '#16a34a',
        'bg': '#f0fdf4',
        'border': '#bbf7d0',
        'priority': 7,
        'name_ar': 'علوم الحياة والأرض'
    },
    'Arabe': {
        'icon': '📖',
        'color': '#059669',
        'bg': '#ecfdf5',
        'border': '#a7f3d0',
        'priority': 8,
        'name_ar': 'اللغة العربية'
    },
    'Soutien Scolaire': {
        'icon': '📚',
        'color': '#4f46e5',
        'bg': '#eef2ff',
        'border': '#c7d2fe',
        'priority': 9,
        'name_ar': 'الدعم المدرسي'
    },
    'Autre': {
        'icon': '📝',
        'color': '#64748b',
        'bg': '#f8fafc',
        'border': '#cbd5e1',
        'priority': 99,
        'name_ar': 'مواد أخرى'
    }
}


def get_course_matiere(c, name=None, cat=None):
    if hasattr(c, 'language'):
        lang = getattr(c, 'language', '') or ''
        name = getattr(c, 'name', '') or ''
        cat = getattr(c, 'category', '') or ''
    elif isinstance(c, dict):
        lang = c.get('language', '') or ''
        name = c.get('name', '') or ''
        cat = c.get('category', '') or ''
    else:
        lang = str(c or '')
        name = str(name or '')
        cat = str(cat or '')

    l = lang.strip().lower()
    n = name.strip().lower()

    if any(k in l for k in ['soutien', 'primaire']) or any(k in n for k in ['soutien primaire', 'primaire - toutes']):
        return 'Soutien Scolaire'
    if any(k in l for k in ['fran', 'français', 'francais']) or 'francais' in n or 'français' in n:
        return 'Français'
    if any(k in l for k in ['espagn', 'esp']) or 'espagnol' in n:
        return 'Espagnol'
    if any(k in l for k in ['ang', 'angl', 'english']) or 'anglais' in n or 'english' in n:
        return 'Anglais'
    if any(k in l for k in ['allem', 'germ', 'deutsch']) or 'allemand' in n:
        return 'Allemand'
    if any(k in l for k in ['math']) or 'math' in n:
        return 'Mathématiques'
    if any(k in l for k in ['pc', 'physiq']) or 'physique' in n or ' pc' in n or '(pc)' in n:
        return 'Physique-Chimie'
    if 'svt' in l or 'svt' in n:
        return 'SVT'
    if 'arabe' in l or 'arabe' in n:
        return 'Arabe'
    if 'soutien' in l or 'soutien' in n:
        return 'Soutien Scolaire'
    if lang.strip():
        return lang.strip().capitalize()
    if cat == 'language':
        return 'Langues'
    return 'Autre'


def get_teacher_primary_matiere(t):
    spec = (getattr(t, 'specialty', '') or '').strip().lower()
    if any(k in spec for k in ['fran', 'fr reg', 'fr']):
        return 'Français'
    if any(k in spec for k in ['esp']):
        return 'Espagnol'
    if any(k in spec for k in ['ang']):
        return 'Anglais'
    if any(k in spec for k in ['allem', 'germ']):
        return 'Allemand'
    if any(k in spec for k in ['math']):
        return 'Mathématiques'
    if any(k in spec for k in ['pc', 'physiq']):
        return 'Physique-Chimie'
    if 'svt' in spec:
        return 'SVT'
    if hasattr(t, 'id') and t.id:
        try:
            c = Course.query.filter_by(teacher_id=t.id, active=True).first()
            if c:
                return get_course_matiere(c)
        except Exception:
            pass
    return 'Autre'


def get_matiere_priority(matiere_name):
    cfg = MATIERE_CONFIG.get(matiere_name)
    if cfg:
        return cfg.get('priority', 50)
    return 50



class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='admin')  # admin / accountant / teacher
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    active = db.Column(db.Boolean, default=True)
    commission_rate = db.Column(db.Float, default=0.0)  # Percentage bonus on school net for inscriptions (e.g. 10.0 for 10%)
    plain_password = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher_profile = db.relationship('Teacher', foreign_keys=[teacher_id], backref=db.backref('user_account', uselist=False))

    def set_password(self, pw, save_plain=True):
        self.password_hash = generate_password_hash(pw)
        if save_plain:
            self.plain_password = pw

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class Setting(db.Model):
    __tablename__ = 'settings'
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, default='')


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True)
    title = db.Column(db.String(20), default='M.')  # M., Mme, Dr., Prof.
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    gender = db.Column(db.String(10))
    birth_date = db.Column(db.Date)
    city = db.Column(db.String(100))
    address = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    cin = db.Column(db.String(30))
    diploma = db.Column(db.String(150))
    years_experience = db.Column(db.Integer, default=0)
    contract_type = db.Column(db.String(50), default='vacation')  # vacation / cdi / cdd / freelance
    specialty = db.Column(db.String(120))
    subjects_taught = db.Column(db.String(255))
    availability = db.Column(db.String(255))
    bank_name = db.Column(db.String(80))
    bank_rib = db.Column(db.String(34))
    bank_account_holder = db.Column(db.String(120))
    bank_agency = db.Column(db.String(100))
    emergency_contact = db.Column(db.String(150))
    photo = db.Column(db.String(255))
    nfc_uid = db.Column(db.String(50), nullable=True, index=True)
    salary_type = db.Column(db.String(20), default='monthly')  # monthly / hourly / per_student
    salary_amount = db.Column(db.Float, default=0)
    hire_date = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @full_name.expression
    def full_name(cls):
        return db.func.coalesce(cls.first_name, '') + ' ' + db.func.coalesce(cls.last_name, '')

    @property
    def avatar_url(self):
        if self.photo:
            return f"/static/uploads/{self.photo}"
        return f"https://ui-avatars.com/api/?name={self.first_name}+{self.last_name}&background=0B3D6E&color=fff&size=128"

    @property
    def primary_matiere(self):
        return get_teacher_primary_matiere(self)


class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    capacity = db.Column(db.Integer, default=20)
    notes = db.Column(db.String(255))


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    gender = db.Column(db.String(10))
    birth_date = db.Column(db.Date)
    phone = db.Column(db.String(30))
    whatsapp = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    city = db.Column(db.String(60))
    cin = db.Column(db.String(30))
    school_level = db.Column(db.String(60))     # niveau scolaire (bac, 1bac, collège...)
    school_name = db.Column(db.String(120))
    parent_name = db.Column(db.String(120))
    parent_phone = db.Column(db.String(30))
    family_code = db.Column(db.String(30))       # Code famille / إخوة
    credit_balance = db.Column(db.Float, default=0.0) # Solde Avoir (DH)
    status = db.Column(db.String(20), default='active')  # active / inactive
    photo = db.Column(db.String(255))
    nfc_uid = db.Column(db.String(50), unique=True, nullable=True) # Badge NFC / RFID UID
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])

    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @full_name.expression
    def full_name(cls):
        return db.func.coalesce(cls.first_name, '') + ' ' + db.func.coalesce(cls.last_name, '')

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = date.today()
        try:
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        except Exception:
            return None

    @property
    def is_adult(self):
        if self.age is not None:
            return self.age >= 18
        if self.cin and self.cin.strip():
            return True
        # If student has their own phone but neither parent_phone nor parent_name:
        if (self.phone and self.phone.strip()) and not (self.parent_phone and self.parent_phone.strip()) and not (self.parent_name and self.parent_name.strip()):
            return True
        return False

    @property
    def end_date(self):
        if getattr(self, '_end_date_cache', None) is not None:
            return self._end_date_cache
        enrolls = Enrollment.query.filter_by(student_id=self.id, status='active').all()
        dates = [e.end_date for e in enrolls if e.end_date]
        res = max(dates) if dates else None
        self._end_date_cache = res
        return res

    @property
    def has_pack(self):
        return any(e.is_pack for e in self.active_enrollments)

    @property
    def pack_remaining_sessions(self):
        return sum(e.remaining_sessions for e in self.active_enrollments if e.is_pack)

    @property
    def days_remaining(self):
        if getattr(self, '_days_remaining_cache', None) is not None:
            return self._days_remaining_cache
        ed = self.end_date
        res = (ed - date.today()).days if ed else None
        self._days_remaining_cache = res
        return res

    @property
    def enrollments(self):
        return Enrollment.query.filter_by(student_id=self.id).order_by(Enrollment.id.desc()).all()

    @property
    def active_enrollments(self):
        return Enrollment.query.filter_by(student_id=self.id).filter(Enrollment.status.in_(['active', 'trial', 'paused'])).all()

    @property
    def active_enrollment(self):
        return Enrollment.query.filter_by(student_id=self.id, status='active').order_by(Enrollment.id.desc()).first()

    @property
    def level_mismatch_test(self):
        tests = PlacementTest.query.filter_by(enrolled_student_id=self.id, is_submitted=True)\
            .order_by(PlacementTest.id.desc()).all()
        for t in tests:
            if t.is_level_mismatch:
                return t
        return None

    @property
    def dynamic_credit_balance(self):
        if getattr(self, '_credit_balance_cache', None) is not None:
            return self._credit_balance_cache
        total_payments = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).filter(Payment.student_id == self.id).scalar() or 0.0
        total_due = 0.0
        enrolls = Enrollment.query.filter_by(student_id=self.id).filter(Enrollment.status != 'dropped').all()
        for e in enrolls:
            total_due += (e.calculated_price or e.monthly_price or 0.0)
        
        excess = max(0.0, total_payments - total_due)
        res = round(excess + (self.credit_balance or 0.0), 2)
        self._credit_balance_cache = res
        return res


class Tariff(db.Model):
    __tablename__ = 'tariffs'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(20), default='language')  # language / tutoring
    language = db.Column(db.String(60))   # Anglais, Français, Espagnol, Allemand...
    billing_cycle = db.Column(db.String(30), default='monthly')  # monthly / 1month / 3months
    price = db.Column(db.Float, default=0.0)
    registration_fee = db.Column(db.Float, default=100.0)
    sessions_per_week = db.Column(db.Integer, default=3)
    session_duration = db.Column(db.String(30), default='1h30')
    active = db.Column(db.Boolean, default=True)

    @property
    def display_name(self):
        cycle_txt = "3 mois" if self.billing_cycle == '3months' else "1 mois"
        return f"{self.name} — {self.price:.0f} DH ({cycle_txt})"

    @property
    def price_per_month(self):
        cycle = (self.billing_cycle or 'monthly').lower()
        if cycle in ('3months', 'trimestriel', '3 mois', 'quarterly'):
            return round((self.price or 0.0) / 3.0, 2)
        elif cycle in ('6months', 'semestriel', '6 mois'):
            return round((self.price or 0.0) / 6.0, 2)
        elif cycle in ('annual', 'annuel', '12months'):
            return round((self.price or 0.0) / 12.0, 2)
        return self.price or 0.0

    @property
    def unit_monthly_price(self):
        return self.price_per_month


def smart_shorten_course_name(name, course=None):
    """
    Stratégie Intelligente de Raccourcissement de Nom de Cours :
    Nettoie les intitulés surchargés (jours, heures, séances, durées)
    pour produire un titre concis, clair et adapté au ticket 80mm.
    Exemples :
    - 'Anglais 3S/sem (1h30)GROUPE 1: MARDI 19:00 - 20:30-VENDREDI' -> 'Anglais (A1) - G1'
    - 'G1Soutien 2 BAC SX - Maths LUNDI -20:30-22:00' -> '2 BAC SX - Maths (G1)'
    - 'Soutien TC - Physique Chimie (PC) LUNDI ET JEUDI' -> 'TC - PC'
    """
    if not name and course:
        name = getattr(course, 'name', '') or ''
    if not name:
        return 'Cours'
        
    raw = str(name).strip()
    if not raw:
        return 'Cours'
        
    # Protection : Si l'intitulé correspond à des frais d'inscription ou de dossier, ne pas le transformer en cours
    if re.search(r"\b(?:frais\s*d['\’]?\s*inscription|frais\s*de\s*dossier|registration\s*fee)\b", raw, re.IGNORECASE):
        return "Frais d'inscription"
    if re.search(r"(?:واجبات\s*التسجيل|رسوم\s*التسجيل)", raw):
        return "واجبات التسجيل"
    if re.search(r"^\s*(?:manuel|livre|livres|manuels)\s*:\s*", raw, re.IGNORECASE):
        return raw

    # 1. Extraction du Groupe (G1, G2, etc.)
    grp = None
    m_grp = re.search(r'\b(?:GROUPE|GRP|GR|G)\s*[:#\-]?\s*(\d+|[A-C])\b', raw, re.IGNORECASE)
    if m_grp:
        grp = f"G{m_grp.group(1).upper()}"
    elif course and getattr(course, 'group_name', None):
        m_cg = re.search(r'\b(?:GROUPE|GRP|GR|G)\s*[:#\-]?\s*(\d+|[A-C])\b', course.group_name, re.IGNORECASE)
        if m_cg:
            grp = f"G{m_cg.group(1).upper()}"

    is_soutien = (course and getattr(course, 'category', None) == 'soutien') or bool(re.search(r'\b(?:soutien|coll|bac|primaire|lycee|lycée)\b', raw, re.IGNORECASE))
    
    if is_soutien:
        # Match level: 2 BAC, 1 BAC, TC, 3 Coll, 2 Coll, 1 Coll, Primaire
        m_lvl = re.search(r'\b(2\s*BAC|1\s*BAC|TC|T\.C\.?|3\s*Coll\w*|2\s*Coll\w*|1\s*Coll\w*|Primaire)\b', raw, re.IGNORECASE)
        level_str = m_lvl.group(1).replace('  ', ' ') if m_lvl else ''
        
        # Match filiere: SX, SM, PC, SVT, Eco, Sciences
        m_fil = re.search(r'\b(SX|SM|PC|SVT|Eco|Sciences?)\b', raw, re.IGNORECASE)
        fil_str = m_fil.group(1).upper() if m_fil else ''
        
        # Match matiere: Maths, Physique, Chimie, PC, SVT, Francais, Philo, Anglais
        m_mat = re.search(r'\b(Maths?|Mathématiques|Physique\s*[-/]?\s*Chimie(?:\s*\(PC\))?|PC\b|SVT|Français(?:\s*Régional)?|Francais|Philosophie|Philo|Anglais)\b', raw, re.IGNORECASE)
        mat_str = ''
        if m_mat:
            m_raw = m_mat.group(1)
            if 'physique' in m_raw.lower() or m_raw.upper() == 'PC':
                mat_str = 'PC'
            elif 'math' in m_raw.lower():
                mat_str = 'Maths'
            elif 'philo' in m_raw.lower():
                mat_str = 'Philo'
            elif 'régional' in m_raw.lower() or 'regional' in m_raw.lower():
                mat_str = 'Français Rég.'
            else:
                mat_str = m_raw.capitalize()
        elif course and getattr(course, 'matiere', None):
            mat_str = course.matiere
            if mat_str == 'Physique-Chimie':
                mat_str = 'PC'
            elif mat_str == 'Mathématiques':
                mat_str = 'Maths'
            
        parts = []
        lvl_fil = f"{level_str} {fil_str}".strip() if (level_str and fil_str and fil_str != mat_str) else (level_str or fil_str)
        if lvl_fil:
            parts.append(lvl_fil)
        if mat_str:
            parts.append(mat_str)
            
        if parts:
            res = ' - '.join(parts)
            if grp and grp not in res:
                res = f"{res} ({grp})"
            return res

    # 2. Pour les langues
    lang = None
    for l in ['Anglais', 'Français', 'Francais', 'Allemand', 'Espagnol', 'Italien', 'Turc', 'Arabe']:
        if re.search(r'\b' + l + r'\b', raw, re.IGNORECASE):
            lang = 'Français' if l.lower() in ('français', 'francais') else l
            break
    if not lang and course and getattr(course, 'language', None):
        lang = course.language.strip()
        
    audience = ''
    m_aud = re.search(r'\b(Kids|Teens|Ados?|Adultes?|Enfants?|Enf|Ado\s*\d*|Avancé|Débutant)\b', raw, re.IGNORECASE)
    if m_aud:
        audience = m_aud.group(1).capitalize()
    
    level_code = ''
    m_lvl = re.search(r'\b([A-C][1-2])\b', raw)
    if m_lvl:
        level_code = m_lvl.group(1).upper()
    elif course and getattr(course, 'level', None):
        m_clvl = re.search(r'\b([A-C][1-2])\b', course.level)
        if m_clvl:
            level_code = m_clvl.group(1).upper()

    if lang:
        res = lang
        extras = []
        if audience:
            extras.append(audience)
        if level_code and level_code not in extras:
            extras.append(level_code)
        if extras:
            res = f"{res} ({' '.join(extras)})"
        if grp:
            res = f"{res} - {grp}"
        return res

    # 3. Fallback générique : nettoyage des durées et jours
    s = raw
    s = re.sub(r'\(\s*\d+\s*h\s*\d*\s*\)', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\b\d+\s*s\s*(?:/\s*sem|\s*/)?\b', '', s, flags=re.IGNORECASE)
    days_pattern = r'\b(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche|lun|mar|mer|jeu|ven|sam|dim)\b.*'
    s = re.sub(days_pattern, '', s, flags=re.IGNORECASE)
    s = re.sub(r'[\•\*\:\-\/\–\—]+', ' ', s)
    s = ' '.join(s.split())
    if len(s) > 28:
        s = s[:25] + '...'
    if grp and grp not in s:
        s = f"{s} ({grp})"
    return s or 'Cours'


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True)
    name = db.Column(db.String(120), nullable=False)
    tariff_id = db.Column(db.Integer, db.ForeignKey('tariffs.id'), nullable=True)
    category = db.Column(db.String(20), default='language')  # language / tutoring
    language = db.Column(db.String(60))   # Anglais, Français, Espagnol...
    level = db.Column(db.String(60))      # Débutant, Intermédiaire, Avancé / classe scolaire
    group_name = db.Column(db.String(60)) # Groupe A...
    billing_cycle = db.Column(db.String(30), default='monthly')  # monthly / 1month / 3months
    price = db.Column(db.Float, default=0)        # prix total du cycle
    price_per_month = db.Column(db.Float, default=0)
    registration_fee = db.Column(db.Float, default=100.0)  # Frais d'inscription (Anglais 100, Français 100, Allemand 200, Espagnol 200, Soutien 40)
    sessions_per_week = db.Column(db.Integer, default=3)  # Nombre de séances / semaine
    session_duration = db.Column(db.String(30), default='1h30')  # Durée par séance (1h30, 2h00, 2h15...)
    scheduled_days = db.Column(db.String(30), default='0,2,4')  # 0=Lundi, 1=Mardi, 2=Mercredi, 3=Jeudi, 4=Vendredi, 5=Samedi, 6=Dimanche
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)
    max_students = db.Column(db.Integer, default=20)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)

    tariff = db.relationship('Tariff')
    teacher = db.relationship('Teacher')
    room = db.relationship('Room')

    @property
    def unit_monthly_price(self):
        if self.price_per_month and self.price_per_month > 0:
            return self.price_per_month
        cycle = (self.billing_cycle or 'monthly').lower()
        if cycle in ('3months', 'trimestriel', '3 mois', 'quarterly'):
            return round((self.price or 0.0) / 3.0, 2)
        elif cycle in ('6months', 'semestriel', '6 mois'):
            return round((self.price or 0.0) / 6.0, 2)
        elif cycle in ('annual', 'annuel', '12months'):
            return round((self.price or 0.0) / 12.0, 2)
        return self.price or 0.0

    @property
    def enrolled_count(self):
        ens = Enrollment.query.filter(Enrollment.course_id == self.id, Enrollment.status.in_(['active', 'trial'])).all()
        return sum(1 for e in ens if e.is_attendance_eligible())

    @property
    def display_name(self):
        if self.name and self.name.strip():
            return self.name.strip()
        lang_part = self.language or ('Langue' if self.category == 'language' else 'Soutien')
        lvl_part = f"({self.level})" if self.level else ""
        return f"{lang_part} {lvl_part}".strip()

    @property
    def full_display_name(self):
        base = self.display_name
        parts = [base]
        if self.group_name and self.group_name not in base:
            parts.append(f"[{self.group_name}]")
        return " ".join(parts)

    @property
    def receipt_name(self):
        return smart_shorten_course_name(self.name, self)

    @property
    def matiere(self):
        return get_course_matiere(self)

    @property
    def scheduled_weekdays(self):
        scheduled_days = set()
        if self.scheduled_days:
            try:
                scheduled_days = set(int(x.strip()) for x in self.scheduled_days.split(',') if x.strip().isdigit())
            except Exception:
                scheduled_days = set()

        if not scheduled_days:
            spw = self.sessions_per_week if self.sessions_per_week else 3
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
        return scheduled_days

    @property
    def schedule_label(self):
        days_map = {0: 'Lun', 1: 'Mar', 2: 'Mer', 3: 'Jeu', 4: 'Ven', 5: 'Sam', 6: 'Dim'}
        try:
            from models import ScheduleSlot
            slots = ScheduleSlot.query.filter_by(course_id=self.id).order_by(ScheduleSlot.day_of_week, ScheduleSlot.start_time).all()
            if slots:
                day_nums = sorted(list(set(s.day_of_week for s in slots if s.day_of_week in days_map)))
                days_str = ' • '.join(days_map[d_num] for d_num in day_nums)
                time_str = f"{slots[0].start_time}-{slots[0].end_time}" if slots[0].start_time else ''
                return f"{days_str} ({time_str})" if time_str else days_str
        except Exception:
            pass
        if self.scheduled_days:
            try:
                days_list = [int(x) for x in self.scheduled_days.split(',') if x.strip().isdigit()]
                if days_list:
                    days_str = ' • '.join(days_map[d_num] for d_num in sorted(days_list) if d_num in days_map)
                    dur = f" ({self.session_duration})" if self.session_duration else ""
                    return f"{days_str}{dur}"
            except Exception:
                pass
        spw = self.sessions_per_week or 3
        dur = self.session_duration or '1h30'
        return f"{spw} séances/sem ({dur})"

    @property
    def target_audience(self):
        n = (self.name or '').upper()
        lvl = (self.level or '').upper()
        if any(k in n or k in lvl for k in ['KID', 'ENF', 'PRIMAIRE', 'JUNIOR', 'PETIT']):
            return 'kids'
        if any(k in n or k in lvl for k in ['ADO', 'COLLEGE', 'COLLÈGE', 'BAC', 'TRONC', 'LYCEE', 'LYCÉE', 'JEUNE']):
            return 'teens'
        return 'adults'

    @property
    def timing_slot(self):
        sched = (self.schedule_label or '').upper()
        if 'SAM' in sched or 'DIM' in sched:
            return 'weekend'
        if any(h in sched for h in ['18:', '19:', '20:', '21:', '22:']):
            return 'evening'
        return 'day'

    @property
    def category_group(self):
        n = (self.name or '').lower()
        gn = (self.group_name or '').lower()
        if 'particulier' in n or 'particulier' in gn:
            return '👑 Cours Particuliers & Entreprises'
        if self.category == 'language':
            lang = (self.language or 'Langue').strip().lower()
            if 'anglais' in lang:
                return '🇬🇧 Langues : Anglais'
            if 'fran' in lang:
                return '🇫🇷 Langues : Français'
            if 'allemand' in lang:
                return '🇩🇪 Langues : Allemand'
            if 'espagnol' in lang:
                return '🇪🇸 Langues : Espagnol'
            return f'🌐 Langues : {self.language or "Général"}'
        else:
            lvl = ((self.level or '') + ' ' + (self.name or '')).lower()
            if '2 bac' in lvl or '2ème bac' in lvl or '2eme bac' in lvl:
                return '📐 Soutien Scolaire : 2ème BAC'
            if '1 bac' in lvl or '1ère bac' in lvl or '1ere bac' in lvl:
                return '📐 Soutien Scolaire : 1ère BAC'
            if 'tronc commun' in lvl or ' tc ' in lvl or 'soutien tc' in lvl:
                return '📐 Soutien Scolaire : Tronc Commun'
            if 'coll' in lvl:
                return '📚 Soutien Scolaire : Collège'
            if 'prim' in lvl:
                return '✏️ Soutien Scolaire : Primaire'
            return '📚 Soutien Scolaire : Autres'

    @property
    def category_sort_key(self):
        g = self.category_group
        order = {
            '🇬🇧 Langues : Anglais': '01',
            '🇫🇷 Langues : Français': '02',
            '🇩🇪 Langues : Allemand': '03',
            '🇪🇸 Langues : Espagnol': '04',
            '📐 Soutien Scolaire : 2ème BAC': '05',
            '📐 Soutien Scolaire : 1ère BAC': '06',
            '📐 Soutien Scolaire : Tronc Commun': '07',
            '📚 Soutien Scolaire : Collège': '08',
            '✏️ Soutien Scolaire : Primaire': '09',
            '👑 Cours Particuliers & Entreprises': '10',
        }
        return order.get(g, '99')

    @property
    def assign_dropdown_label(self):
        n = (self.name or '').lower()
        gn = (self.group_name or '').lower()
        if 'particulier' in n or 'particulier' in gn:
            prefix = "👑 VIP / Particulier"
        elif self.category == 'language':
            prefix = self.language or "Langue"
        else:
            prefix = self.matiere or self.language or "Soutien"
        
        lvl_str = f" • {self.level}" if self.level and self.level.lower() not in (self.name or '').lower() else ""
        t_name = f"Prof: {self.teacher.full_name}" if self.teacher else "⚠️ Sans prof assigné"
        price_dh = f"{self.price:.0f} DH" if self.price else "0 DH"
        count_str = f"{self.enrolled_count}/{self.max_students or 20} él."
        sched = self.schedule_label or ""
        sched_part = f" [{sched}]" if sched and sched not in (self.name or '') else ""

        return f"[{prefix}{lvl_str}] {self.display_name}{sched_part} — {t_name} ({count_str}) — {price_dh}"


class CourseTeacher(db.Model):
    __tablename__ = 'course_teachers'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    compensation_type = db.Column(db.String(20), default='percentage')  # percentage / fixed / hourly / per_student
    compensation_value = db.Column(db.Float, default=50.0)
    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    course = db.relationship('Course', backref=db.backref('teacher_assignments', cascade='all, delete-orphan'))
    teacher = db.relationship('Teacher', backref=db.backref('course_assignments', cascade='all, delete-orphan'))


def calculate_last_session_date(enroll_dt, total_sessions, scheduled_days):
    if not enroll_dt or total_sessions <= 0:
        return enroll_dt or date.today()

    if not scheduled_days:
        scheduled_days = {0, 2, 4}

    sessions_counted = 0
    cur_dt = enroll_dt
    last_session_dt = enroll_dt

    for _ in range(730):
        if cur_dt.weekday() in scheduled_days:
            sessions_counted += 1
            if sessions_counted == total_sessions:
                last_session_dt = cur_dt
            elif sessions_counted > total_sessions:
                # cur_dt is the next session date after the last paid session
                # The end date is the eve (day before) this next session:
                return cur_dt - timedelta(days=1)
        cur_dt += timedelta(days=1)

    return last_session_dt


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    enroll_date = db.Column(db.Date, default=date.today)
    payment_plan = db.Column(db.String(30), default='full')  # full / installment
    status = db.Column(db.String(20), default='active')  # active / completed / dropped
    total_sessions_month = db.Column(db.Integer, default=0)
    attended_sessions_month = db.Column(db.Integer, default=0)
    monthly_price = db.Column(db.Float, default=0.0)
    calculated_price = db.Column(db.Float, default=0.0)
    current_month_earned = db.Column(db.Float, default=0.0)
    deferred_amount = db.Column(db.Float, default=0.0)
    pause_date = db.Column(db.Date, nullable=True)
    paused_sessions_remaining = db.Column(db.Integer, default=0)
    total_paused_days = db.Column(db.Integer, default=0)
    tariff_id = db.Column(db.Integer, db.ForeignKey('tariffs.id'), nullable=True)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_reminder_at = db.Column(db.DateTime, nullable=True)
    last_reminder_phone = db.Column(db.String(30), nullable=True)
    reminder_count = db.Column(db.Integer, default=0)
    rest_promise_date = db.Column(db.Date, nullable=True)
    rest_promise_note = db.Column(db.String(255), nullable=True)

    student = db.relationship('Student')
    course = db.relationship('Course')
    tariff = db.relationship('Tariff')
    creator = db.relationship('User', foreign_keys=[created_by])

    @property
    def is_pending(self):
        return self.status == 'pending_assignment' or self.course_id is None

    @property
    def is_pack(self):
        if self.payment_plan == 'pack':
            return True
        if self.course and self.course.billing_cycle == 'pack':
            return True
        if self.course and 'particulier' in (self.course.name or '').lower():
            return True
        return False

    @property
    def remaining_sessions(self):
        tot = self.total_sessions_month or 1
        att = self.attended_sessions_month or 0
        return max(0, tot - att)

    @property
    def course_name_display(self):
        if self.course:
            return self.course.display_name
        if self.tariff:
            return f"{self.tariff.name} (En attente)"
        return "En attente d'affectation"

    @property
    def pending_days_since_stage(self):
        """Days elapsed since creation (if reminder_count == 0) or since last_reminder_at."""
        if self.status != 'pending_assignment':
            return 0
        now_dt = datetime.utcnow()
        ref_dt = self.last_reminder_at if (self.reminder_count and self.last_reminder_at) else (self.created_at or now_dt)
        return max(0, (now_dt - ref_dt).days)

    @property
    def pending_total_days(self):
        """Total days since pre-inscription creation."""
        if not self.created_at:
            return 0
        return max(0, (datetime.utcnow() - self.created_at).days)

    @property
    def pending_reminder_stage(self):
        """Current reminder stage: 1, 2, or 3."""
        count = self.reminder_count or 0
        return min(3, count + 1)

    @property
    def is_pending_reminder_due(self):
        """True if 10 days have elapsed since creation (stage 1) or since last_reminder_at (stage 2/3), and reminder_count < 3."""
        if self.status != 'pending_assignment':
            return False
        count = self.reminder_count or 0
        if count >= 3:
            return False
        return self.pending_days_since_stage >= 10

    @property
    def is_pending_auto_removal_due(self):
        """True if 3 reminders have been sent and 24 hours have elapsed without course assignment."""
        if self.status != 'pending_assignment':
            return False
        count = self.reminder_count or 0
        if count < 3 or not self.last_reminder_at:
            return False
        seconds_since = (datetime.utcnow() - self.last_reminder_at).total_seconds()
        return seconds_since >= 24 * 3600

    @property
    def pending_hours_until_auto_removal(self):
        """Hours remaining before auto-removal (if reminder_count >= 3)."""
        if self.status != 'pending_assignment' or (self.reminder_count or 0) < 3 or not self.last_reminder_at:
            return None
        seconds_since = (datetime.utcnow() - self.last_reminder_at).total_seconds()
        rem_sec = max(0, 24 * 3600 - seconds_since)
        return round(rem_sec / 3600.0, 1)

    @property
    def scheduled_weekdays(self):
        scheduled_days = set()
        if self.course and self.course.scheduled_days:
            try:
                scheduled_days = set(int(x.strip()) for x in self.course.scheduled_days.split(',') if x.strip().isdigit())
            except Exception:
                scheduled_days = set()

        if not scheduled_days:
            spw = self.course.sessions_per_week if (self.course and self.course.sessions_per_week) else 3
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
        return scheduled_days

    @property
    def duration_months(self):
        # 1. Explicit notes check
        if self.notes:
            lower_notes = self.notes.lower()
            if '1 mois' in lower_notes or '1mois' in lower_notes:
                return 1
            if '3 mois' in lower_notes or '3mois' in lower_notes:
                return 3
            if '2 mois' in lower_notes or '2mois' in lower_notes:
                return 2
            if '6 mois' in lower_notes or '6mois' in lower_notes:
                return 6
            if '12 mois' in lower_notes or '12mois' in lower_notes:
                return 12

        # 2. Total sessions check
        if self.total_sessions_month and self.total_sessions_month > 0:
            if self.total_sessions_month <= 16:
                return 1
            spw = self.course.sessions_per_week if (self.course and self.course.sessions_per_week) else 3
            # Special case for Soutien Primaire (spw=5): 20-24 sessions is 1 month
            if spw == 5 and self.total_sessions_month <= 24:
                return 1
            if spw == 2:
                if 16 <= self.total_sessions_month <= 19:
                    return 2
                if 24 <= self.total_sessions_month <= 28:
                    return 3
            if 24 <= self.total_sessions_month <= 28 and spw == 3:
                return 2
            if 36 <= self.total_sessions_month <= 44 and spw == 3:
                return 3
            m = int(round(self.total_sessions_month / (spw * 4.33)))
            if m >= 1:
                return m

        # 3. Explicit dates check
        ed = self.custom_end_date
        st = self.enroll_date
        if st and ed:
            days = (ed - st).days
            if days > 0:
                calc_m = int(round(days / 30.4))
                if calc_m >= 1:
                    return calc_m

        # 4. Explicit payment_plan check
        if self.payment_plan:
            plan = str(self.payment_plan).lower()
            if '3month' in plan or plan == 'quarterly':
                return 3
            elif '6month' in plan:
                return 6
            elif '12month' in plan or plan == 'annual':
                return 12
            elif plan in ('monthly', 'trial', '1month', '1'):
                return 1

        return 1

    @property
    def total_cycle_sessions(self):
        if self.is_pack:
            return self.total_sessions_month or 1
        spw = self.course.sessions_per_week if (self.course and self.course.sessions_per_week) else 3
        dur = self.duration_months
        if dur == 1:
            if self.total_sessions_month and 4 <= self.total_sessions_month <= (spw * 6):
                return self.total_sessions_month
            return spw * 4

        expected = spw * 13 if dur == 3 else (spw * 4 * dur)
        if self.total_sessions_month and self.total_sessions_month >= int(expected * 0.7):
            return self.total_sessions_month
        return max(expected, self.total_sessions_month or 0)

    def calculate_remaining_sessions_at(self, check_date=None):
        if self.status == 'paused' and self.paused_sessions_remaining and self.paused_sessions_remaining > 0:
            return self.paused_sessions_remaining

        if not check_date:
            check_date = date.today()

        ed = self.end_date
        if not ed or check_date >= ed:
            return 0

        scheduled_days = self.scheduled_weekdays
        cnt = 0
        cur = check_date
        while cur <= ed:
            if cur.weekday() in scheduled_days:
                cnt += 1
            cur += timedelta(days=1)

        tot = self.total_cycle_sessions
        if cnt > 0:
            return min(tot, cnt) if tot > 0 else cnt

        spw = self.course.sessions_per_week if (self.course and self.course.sessions_per_week) else 3
        days_left = (ed - check_date).days
        est = max(1, int(round((days_left / 7.0) * spw)))
        return min(tot, est) if tot > 0 else est

    def count_consumed_sessions(self, as_of_date=None):
        if not as_of_date:
            as_of_date = date.today()

        tot = self.total_cycle_sessions
        rem = self.calculate_remaining_sessions_at(as_of_date)
        if tot < rem:
            tot = rem
        return max(0, tot - rem)

    def clear_cache(self):
        self._total_paid_cache = None
        self._paid_sessions_cache = None
        self._end_date_cache = None
        self._days_remaining_cache = None

    @property
    def total_paid(self):
        if getattr(self, '_total_paid_cache', None) is not None:
            return self._total_paid_cache
        val = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))\
            .filter(Payment.enrollment_id == self.id).scalar() or 0
        self._total_paid_cache = val
        return val

    @property
    def is_trial(self):
        return self.status == 'trial'

    @property
    def trial_attended_count(self):
        """Number of attendance marks (present, absent, late) for this trial student in this course"""
        if self.status != 'trial':
            return 0
        from models import Attendance
        q = Attendance.query.filter(Attendance.course_id == self.course_id, Attendance.student_id == self.student_id)
        if self.enroll_date:
            q = q.filter(Attendance.date >= self.enroll_date)
        return q.count()

    @property
    def trial_completed(self):
        """True if the student has taken their 1 trial session or the session date has passed"""
        if self.status != 'trial':
            return False
        if self.trial_attended_count >= 1:
            return True
        ed = self.custom_end_date or self.enroll_date
        if ed and ed < date.today():
            return True
        return False

    @property
    def due_amount(self):
        if self.status in ('trial', 'dropped'):
            return 0.0
        if self.calculated_price is not None:
            return self.calculated_price
        if self.monthly_price and self.monthly_price > 0:
            dur = self.duration_months or 1
            return round(self.monthly_price * dur, 2)
        if self.course:
            dur = self.duration_months or 1
            unit = self.course.unit_monthly_price if hasattr(self.course, 'unit_monthly_price') else (self.course.price_per_month or (round(self.course.price / 3.0, 2) if self.course.billing_cycle in ('3months', 'trimestriel', '3 mois', 'quarterly') else self.course.price))
            return round(unit * dur, 2)
        return 0.0

    @property
    def unit_monthly_price(self):
        dur = self.duration_months or 1
        if self.monthly_price and self.monthly_price > 0:
            if dur > 1 and self.monthly_price > 600:
                # If monthly_price was mistakenly stored as the multi-month cycle total (e.g. 1050 or 1300 for 3 months)
                c_unit = self.course.unit_monthly_price if (self.course and hasattr(self.course, 'unit_monthly_price')) else None
                if c_unit and self.monthly_price > (c_unit * 1.35):
                    return round(self.monthly_price / dur, 2)
                if self.calculated_price and self.calculated_price > 600 and abs(self.monthly_price - self.calculated_price) <= 250:
                    return round(self.monthly_price / dur, 2)
            return round(self.monthly_price, 2)
        if self.course and hasattr(self.course, 'unit_monthly_price') and self.course.unit_monthly_price:
            return round(self.course.unit_monthly_price, 2)
        if self.course:
            return self.course.price_per_month or (round(self.course.price / 3.0, 2) if self.course.billing_cycle in ('3months', 'trimestriel', '3 mois', 'quarterly') else self.course.price) or 300.0
        return 300.0

    @property
    def balance_due(self):
        return max(0.0, round((self.due_amount or 0.0) - (self.total_paid or 0.0), 2))

    @property
    def current_month_revenue(self):
        if self.status == 'trial':
            return 0.0
        if self.current_month_earned and self.current_month_earned > 0:
            return self.current_month_earned
        if self.total_sessions_month and self.total_sessions_month > 0:
            return round((self.due_amount / self.total_sessions_month) * self.attended_sessions_month, 2)
        return self.due_amount

    @property
    def next_month_deferred(self):
        if self.status == 'trial':
            return 0.0
        if self.deferred_amount and self.deferred_amount > 0:
            return self.deferred_amount
        return max(0.0, round(self.due_amount - self.current_month_revenue, 2))

    @property
    def balance(self):
        if self.status in ('trial', 'dropped'):
            return 0.0
        return max(0, self.due_amount - self.total_paid)

    @property
    def paid_sessions(self):
        if getattr(self, '_paid_sessions_cache', None) is not None:
            return self._paid_sessions_cache
        if self.status == 'trial':
            return 1

        tot_cycle = self.total_cycle_sessions
        if not tot_cycle or tot_cycle <= 0:
            tot_cycle = 12

        tot_paid = float(self.total_paid or 0.0)
        due = float(self.due_amount or 0.0)

        # 1. If fully paid or overpaid, grant full cycle sessions
        if due > 0 and tot_paid >= due:
            self._paid_sessions_cache = tot_cycle
            return tot_cycle

        # 2. If zero paid yet, they have 0 paid sessions
        if tot_paid <= 0:
            self._paid_sessions_cache = 0
            return 0

        # 3. Partial payment calculation
        reg_fee = 0.0
        if self.notes and "Frais d'inscription:" in self.notes:
            import re
            m = re.search(r"Frais d'inscription:\s*([\d\.]+)\s*DH", self.notes)
            if m:
                try:
                    reg_fee = float(m.group(1))
                except Exception:
                    reg_fee = 0.0
        elif self.calculated_price is not None and self.monthly_price is not None:
            dur = self.duration_months or 1
            diff = float(self.calculated_price) - float(self.unit_monthly_price * dur)
            if 0 < diff <= 250:
                reg_fee = diff
        else:
            reg_fee = float(self.course.registration_fee or 0.0) if self.course else 0.0

        dur = self.duration_months or 1
        tuition_total = float(self.unit_monthly_price * dur) if dur > 1 else float(self.monthly_price or 0.0)
        if tuition_total <= 0 or (due - reg_fee > tuition_total):
            tuition_total = max(1.0, due - reg_fee)

        tuition_paid = max(0.0, tot_paid - reg_fee)

        # If they paid something, but it only covers the registration fee (or less):
        if tuition_paid <= 0:
            self._paid_sessions_cache = 0
            return 0  # 0 tuition sessions paid

        # Calculate proportionally based on tuition paid
        ratio = tuition_paid / tuition_total
        calc_sessions = int(round(ratio * tot_cycle))
        
        res = max(1, min(tot_cycle, calc_sessions))
        self._paid_sessions_cache = res
        return res

    custom_end_date = db.Column(db.Date, nullable=True)

    @property
    def end_date(self):
        if getattr(self, '_end_date_cache', None) is not None:
            return self._end_date_cache

        # Packs are strictly session-based, NOT calendar-based (no fixed expiry date)
        if self.is_pack:
            self._end_date_cache = None
            return None

        # If student has paid 0 DH and has an outstanding balance due:
        if (self.total_paid or 0) <= 0 and (self.balance or 0) > 0:
            dt = self.enroll_date or (self.created_at.date() if self.created_at else date.today())
            self._end_date_cache = dt
            return dt

        # If student made a partial payment, end date must reflect only the sessions paid for
        if self.total_paid > 0 and self.balance > 0 and self.paid_sessions < self.total_cycle_sessions:
            if self.paid_sessions > 0:
                dt = self.enroll_date or (self.created_at.date() if self.created_at else date.today())
                total_sessions = self.paid_sessions
                scheduled_days = self.scheduled_weekdays
                base_end = calculate_last_session_date(dt, total_sessions, scheduled_days)
                if self.total_paused_days and self.total_paused_days > 0:
                    res = base_end + timedelta(days=self.total_paused_days)
                else:
                    res = base_end
                self._end_date_cache = res
                return res
            else:
                dt = self.enroll_date or (self.created_at.date() if self.created_at else date.today())
                self._end_date_cache = dt
                return dt

        if self.custom_end_date:
            # Safety guard: If custom_end_date <= enroll_date but student is active and has paid > 0,
            # this custom_end_date is just an old trial session date artifact! Do NOT lock them to it.
            if self.total_paid > 0 and self.status == 'active' and self.enroll_date and self.custom_end_date <= self.enroll_date:
                pass
            else:
                self._end_date_cache = self.custom_end_date
                return self.custom_end_date
        dt = self.enroll_date or (self.created_at.date() if self.created_at else date.today())

        total_sessions = self.paid_sessions
        scheduled_days = self.scheduled_weekdays

        if self.balance == 0 and scheduled_days:
            spw = len(scheduled_days)
            min_sessions = spw * 4
            if total_sessions < min_sessions:
                total_sessions = min_sessions

        base_end = calculate_last_session_date(dt, total_sessions, scheduled_days)
        if self.balance == 0 and dt.day == 1:
            import calendar
            _, last_d = calendar.monthrange(dt.year, dt.month)
            m_end = date(dt.year, dt.month, last_d)
            if base_end < m_end:
                base_end = m_end

        if self.total_paused_days and self.total_paused_days > 0:
            res = base_end + timedelta(days=self.total_paused_days)
        else:
            res = base_end
        self._end_date_cache = res
        return res

    @property
    def days_remaining(self):
        if getattr(self, '_days_remaining_cache', None) is not None:
            return self._days_remaining_cache
        ed = self.end_date
        if not ed:
            res = None
        elif self.status == 'paused' and self.pause_date:
            res = max(0, (ed - self.pause_date).days)
        else:
            res = (ed - date.today()).days
        self._days_remaining_cache = res
        return res

    @property
    def reminder_diff_days(self):
        if not self.last_reminder_at:
            return None
        return (date.today() - self.last_reminder_at.date()).days

    def reminder_status_label(self, lang='fr'):
        if not self.last_reminder_at:
            return 'لم يُرسل بعد' if lang == 'ar' else 'En attente'
        diff = max(0, self.reminder_diff_days or 0)
        time_str = self.last_reminder_at.strftime('%H:%M')
        date_str = self.last_reminder_at.strftime('%d/%m')
        if lang == 'ar':
            if diff == 0:
                return f"اليوم ({time_str})"
            elif diff == 1:
                return f"بالأمس ({date_str})"
            elif diff == 2:
                return f"منذ يومين ({date_str})"
            elif 3 <= diff <= 10:
                return f"منذ {diff} أيام ({date_str})"
            else:
                return f"منذ {diff} يوماً ({date_str})"
        else:
            if diff == 0:
                return f"Aujourd'hui ({time_str})"
            elif diff == 1:
                return f"Hier ({date_str})"
            else:
                return f"Il y a {diff} jours ({date_str})"

    @property
    def active_renewal(self):
        """Returns the active subsequent enrollment if this enrollment was renewed or replaced"""
        if not self.student_id or not self.id:
            return None
        q = Enrollment.query.filter(
            Enrollment.student_id == self.student_id,
            Enrollment.id > self.id,
            Enrollment.status == 'active'
        )
        if self.course_id:
            q = q.filter(Enrollment.course_id == self.course_id)
        elif self.tariff_id:
            q = q.filter(Enrollment.tariff_id == self.tariff_id)
        else:
            return None
        return q.order_by(Enrollment.id.desc()).first()

    @property
    def is_renewed(self):
        """True if the student has renewed or has an active subsequent subscription for this course"""
        return self.active_renewal is not None

    @property
    def is_partial_payment(self):
        return (self.total_paid or 0) > 0 and (self.balance or 0) > 0

    @property
    def is_totally_unpaid(self):
        return (self.total_paid or 0) <= 0 and (self.balance or 0) > 0

    @property
    def has_active_promise(self):
        if not self.rest_promise_date or (self.balance or 0) <= 0:
            return False
        return date.today() < self.rest_promise_date

    @property
    def promise_days_left(self):
        if not self.rest_promise_date:
            return None
        return (self.rest_promise_date - date.today()).days

    @property
    def promise_status(self):
        if not self.rest_promise_date or (self.balance or 0) <= 0:
            return None
        today = date.today()
        if today < self.rest_promise_date:
            return 'active'
        elif today == self.rest_promise_date:
            return 'due_today'
        else:
            return 'expired'

    def is_attendance_eligible(self, as_of_date=None):
        """
        Determines whether a student must appear in the attendance / roll call sheet:
        1. Student must exist and be active.
        2. Enrollment status must be 'active' or 'trial' (or 'completed' whose period is still running before renewal).
        3. Do not include future enrollments starting more than 7 days ahead.
        4. If renewed by a newer active enrollment in the same course, exclude older enrollment once renewal begins.
        5. Students stay visible until manually removed ("Retirer de la classe").
        """
        if not as_of_date:
            as_of_date = date.today()
        
        st = self.student
        if not st or getattr(st, 'status', 'active') != 'active':
            return False

        if self.status not in ['active', 'trial']:
            # If completed due to renewal booked in advance, but current period has not ended yet:
            if self.status == 'completed' and self.end_date and self.end_date >= as_of_date:
                ren = self.active_renewal
                if not (ren and ren.enroll_date and as_of_date >= ren.enroll_date):
                    pass  # Still eligible during its running window
                else:
                    return False
            else:
                return False

        en_dt = self.enroll_date or (self.created_at.date() if self.created_at else as_of_date)

        # Do not include future enrollments starting more than 7 days ahead
        if en_dt > as_of_date + timedelta(days=7):
            return False

        # If renewed by a newer active enrollment in the same course:
        # Exclude this enrollment ONLY if the renewal has already started or if this enrollment's end_date has passed
        if self.is_renewed:
            ren = self.active_renewal
            ren_dt = ren.enroll_date if (ren and ren.enroll_date) else None
            if ren_dt and as_of_date >= ren_dt:
                return False
            if self.end_date and as_of_date > self.end_date:
                return False

        return True

    def attendance_badge_info(self, as_of_date=None):
        """Returns dict with badge style, label_fr, label_ar for attendance displays"""
        if not as_of_date:
            as_of_date = date.today()

        if self.status == 'trial':
            if self.trial_completed:
                return {
                    'type': 'trial_done',
                    'fr': "⚠️ ESSAI EFFECTUÉ (1/1) · En attente d'inscription/paiement",
                    'ar': "⚠️ أجرى الحصة (1/1) · في انتظار الأداء والتأكيد",
                    'bg': '#fee2e2',
                    'color': '#b91c1c',
                    'border': '#fca5a5'
                }
            return {
                'type': 'trial',
                'fr': "🧪 ESSAI (Séance d'essai)",
                'ar': "🧪 حصة تجريبية (ESSAI)",
                'bg': '#fef3c7',
                'color': '#b45309',
                'border': '#fde68a'
            }

        paid = float(self.total_paid or 0.0)
        en_dt = self.enroll_date or (self.created_at.date() if self.created_at else as_of_date)
        ed = self.end_date

        if paid <= 0:
            return {
                'type': 'unpaid',
                'fr': "🔴 NON PAYÉ (0 DH)",
                'ar': "🔴 لم يؤدِ الواجب (0 درهم)",
                'bg': '#fef2f2',
                'color': '#dc2626',
                'border': '#fecaca'
            }

        # Clear outstanding tuition debt alert
        if self.balance > 0:
            if self.paid_sessions <= 0:
                return {
                    'type': 'unpaid',
                    'fr': f"⚠️ Scolarité impayée (Reste {self.balance:.0f} DH)",
                    'ar': f"⚠️ واجب الشهر غير مؤدى (باقي {self.balance:.0f} درهم)",
                    'bg': '#fee2e2',
                    'color': '#b91c1c',
                    'border': '#fca5a5'
                }
            else:
                return {
                    'type': 'partial',
                    'fr': f"⚠️ Paiement partiel ({self.paid_sessions} séan. - Reste {self.balance:.0f} DH)",
                    'ar': f"⚠️ أداء جزئي ({self.paid_sessions} حصص - باقي {self.balance:.0f} درهم)",
                    'bg': '#fef3c7',
                    'color': '#b45309',
                    'border': '#fde68a'
                }

        if ed and as_of_date > ed:
            days_past = (as_of_date - ed).days
            return {
                'type': 'expired',
                'fr': f"🔴 Expiré ({days_past}j) · Non payé / Non renouvelé",
                'ar': f"🔴 منتهي ({days_past} يوماً) · غير مجدد / غير مؤدى",
                'bg': '#fef2f2',
                'color': '#b91c1c',
                'border': '#fca5a5'
            }

        return {
            'type': 'valid',
            'fr': '✓ Inscrit validé',
            'ar': '✓ تسجيل مؤكد',
            'bg': '#ecfdf5',
            'color': '#047857',
            'border': '#a7f3d0'
        }




class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    receipt = db.Column(db.String(30), index=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20), default='cash')  # cash / transfer / card / online
    date = db.Column(db.Date, default=date.today)
    note = db.Column(db.String(255))
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    enrollment = db.relationship('Enrollment')
    student = db.relationship('Student')
    invoice = db.relationship('Invoice')
    creator = db.relationship('User', foreign_keys=[recorded_by])

    @validates('date')
    def validate_payment_date(self, key, value):
        if value:
            if isinstance(value, datetime):
                value = value.date()
            if isinstance(value, str):
                try:
                    value = datetime.strptime(value.strip(), '%Y-%m-%d').date()
                except Exception:
                    value = date.today()
            if isinstance(value, date) and value > date.today():
                return date.today()
        return value or date.today()

    @property
    def courses_description(self):
        if self.invoice and self.invoice.items:
            return ", ".join(item.description for item in self.invoice.items)
        if self.enrollment:
            return self.enrollment.course_name_display
        if self.student:
            active_e = Enrollment.query.filter_by(student_id=self.student_id).all()
            if active_e:
                return ", ".join(e.course_name_display for e in active_e)
        return self.note or "Paiement Général"


class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(30), unique=True)
    type = db.Column(db.String(10), default='facture')  # facture / devis
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'))
    issue_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0)
    tva_rate = db.Column(db.Float, default=0)
    tva_amount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='unpaid')  # paid / unpaid / partial
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student')
    enrollment = db.relationship('Enrollment')

    @property
    def amount_paid(self):
        if self.enrollment_id:
            return db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))\
                .filter(db.or_(
                    Payment.invoice_id == self.id,
                    db.and_(Payment.enrollment_id == self.enrollment_id, Payment.invoice_id.is_(None))
                )).scalar() or 0
        return db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))\
            .filter(Payment.invoice_id == self.id).scalar() or 0


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'), nullable=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, default=0.0)

    invoice = db.relationship('Invoice', backref=db.backref('items', cascade='all, delete-orphan'))
    enrollment = db.relationship('Enrollment')



class Attendance(db.Model):
    __tablename__ = 'attendances'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(10), default='present')  # present / absent / late
    notified_at = db.Column(db.DateTime, nullable=True)   # Timestamp of WhatsApp notification
    notified_phone = db.Column(db.String(30), nullable=True) # Phone number notified
    __table_args__ = (db.UniqueConstraint('course_id', 'student_id', 'date', name='uniq_att'),)

    student = db.relationship('Student')
    course = db.relationship('Course')


class StaffAttendanceLog(db.Model):
    __tablename__ = 'staff_attendance_logs'
    id = db.Column(db.Integer, primary_key=True)
    person_type = db.Column(db.String(20), nullable=False, index=True)  # 'teacher' or 'employee'
    person_id = db.Column(db.Integer, nullable=False, index=True)
    punch_type = db.Column(db.String(10), nullable=False)  # 'in' (entrée) or 'out' (sortie)
    punch_time = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    device = db.Column(db.String(50), default='kiosk')  # 'kiosk', 'manual', 'rfid', etc.
    ip_address = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def person(self):
        if self.person_type == 'teacher':
            return Teacher.query.get(self.person_id)
        elif self.person_type == 'employee':
            return Employee.query.get(self.person_id)
        return None

    @property
    def person_name(self):
        p = self.person
        return p.full_name if p else f"ID #{self.person_id}"

    @property
    def person_role(self):
        if self.person_type == 'teacher':
            p = self.person
            return f"Professeur ({p.specialty or p.primary_matiere or 'Enseignant'})" if p else 'Professeur'
        elif self.person_type == 'employee':
            p = self.person
            return f"{p.job_title} ({p.department})" if p else 'Personnel'
        return 'Personnel'

    @property
    def person_code(self):
        p = self.person
        return (p.code or f"ID-{p.id}") if p else '—'

    @property
    def formatted_time(self):
        return self.punch_time.strftime('%H:%M:%S') if self.punch_time else '—'

    @property
    def formatted_date(self):
        return self.date.strftime('%d/%m/%Y') if self.date else '—'


class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    exam_name = db.Column(db.String(120))
    date = db.Column(db.Date, default=date.today)
    score = db.Column(db.Float)
    max_score = db.Column(db.Float, default=20)


class ScheduleSlot(db.Model):
    __tablename__ = 'schedule_slots'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    day_of_week = db.Column(db.Integer)  # 0=Monday
    start_time = db.Column(db.String(5))
    end_time = db.Column(db.String(5))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)

    course = db.relationship('Course')
    teacher = db.relationship('Teacher')
    room = db.relationship('Room')

    @property
    def effective_teacher(self):
        return self.teacher or (self.course.teacher if self.course else None)

    @property
    def effective_room(self):
        return self.room or (self.course.room if self.course else None)


class LogEntry(db.Model):
    __tablename__ = 'activity_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(120))
    detail = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])


class BadgeRecord(db.Model):
    __tablename__ = 'badge_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    issue_date = db.Column(db.Date, default=date.today)
    badge_type = db.Column(db.String(20), default='student')  # student / course / completion
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student')
    course = db.relationship('Course')


class StudentCredit(db.Model):
    __tablename__ = 'student_credits'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), default='avoir')  # avoir / used / refund
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student')
    enrollment = db.relationship('Enrollment')


class SubstituteLog(db.Model):
    __tablename__ = 'substitute_logs'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    original_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    substitute_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    session_type = db.Column(db.String(20), default='substitute')  # substitute / rattrapage
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course')
    substitute_teacher = db.relationship('Teacher', foreign_keys=[substitute_teacher_id])


class SystemNotification(db.Model):
    __tablename__ = 'system_notifications'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Certificate(db.Model):
    __tablename__ = 'certificates'
    id = db.Column(db.Integer, primary_key=True)
    cert_number = db.Column(db.String(50), unique=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    cert_type = db.Column(db.String(60), default='Attestation de Formation')
    recipient_name = db.Column(db.String(150), nullable=True)
    cin = db.Column(db.String(30), nullable=True)
    cnss_no = db.Column(db.String(30), nullable=True)
    job_title = db.Column(db.String(120), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    student_code = db.Column(db.String(50), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    birth_city = db.Column(db.String(80), nullable=True)
    level = db.Column(db.String(50), nullable=True)  # ex: A1, A2, B1, B2, C1
    score_listening = db.Column(db.Float, default=0.0)  # /100
    score_speaking = db.Column(db.Float, default=0.0)   # /100
    score_reading = db.Column(db.Float, default=0.0)    # /100
    score_writing = db.Column(db.Float, default=0.0)    # /100
    overall_score = db.Column(db.Float, default=0.0)    # /100
    title = db.Column(db.String(150))
    issue_date = db.Column(db.Date, default=date.today)
    mention = db.Column(db.String(50), default='Très Bien')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student')
    employee = db.relationship('Employee')
    teacher = db.relationship('Teacher')
    course = db.relationship('Course')

    @property
    def beneficiary_name(self):
        if self.recipient_name and self.recipient_name.strip():
            return self.recipient_name.strip()
        if self.student:
            return self.student.full_name
        if self.employee:
            return self.employee.full_name
        if self.teacher:
            return self.teacher.full_name
        return "—"

    @property
    def beneficiary_cin(self):
        if self.cin and self.cin.strip():
            return self.cin.strip()
        if self.student and self.student.cin:
            return self.student.cin
        if self.employee and self.employee.cin:
            return self.employee.cin
        if self.teacher and self.teacher.cin:
            return self.teacher.cin
        return ""

    @property
    def display_student_code(self):
        if self.student_code and self.student_code.strip():
            return self.student_code.strip()
        if self.student and self.student.code:
            return self.student.code
        return ""

    @property
    def effective_birth_date(self):
        if self.birth_date:
            return self.birth_date
        if self.student and self.student.birth_date:
            return self.student.birth_date
        return None

    @property
    def effective_birth_city(self):
        if self.birth_city and self.birth_city.strip():
            return self.birth_city.strip()
        if self.student and self.student.city:
            return self.student.city
        return "Casablanca"

    @property
    def age_years(self):
        bdate = self.effective_birth_date
        if not bdate:
            return None
        today = date.today()
        return today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))

    @property
    def calculated_overall_score(self):
        if self.overall_score is not None and self.overall_score > 0:
            return round(self.overall_score, 1)
        scores = [s for s in [self.score_listening, self.score_speaking, self.score_reading, self.score_writing] if s is not None and s > 0]
        if scores:
            return round(sum(scores) / len(scores), 1)
        return None




class BlockedIP(db.Model):
    __tablename__ = 'blocked_ips'
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False)
    reason = db.Column(db.String(255), default='Multiple failed login attempts')
    failed_attempts = db.Column(db.Integer, default=5)
    is_blocked = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    blocked_until = db.Column(db.DateTime, nullable=True)


class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    username = db.Column(db.String(80), nullable=True)
    success = db.Column(db.Boolean, default=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = synonym('attempted_at')


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    category = db.Column(db.String(60), default='Général')  # Papeterie, Librairie, Propriétaire, Énergie & Télécom, Maintenance, Prestataire...
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    city = db.Column(db.String(60), default='Marrakech')
    ice = db.Column(db.String(30))  # Identifiant Commun de l'Entreprise marocain
    if_code = db.Column(db.String(30))  # Identifiant Fiscal
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    expenses = db.relationship('Expense', backref='supplier', lazy='dynamic')

    @property
    def total_invoiced(self):
        return sum((e.amount or 0.0) for e in self.expenses)

    @property
    def total_paid(self):
        return sum((e.paid_amount or 0.0) if e.status == 'partial' else ((e.amount or 0.0) if e.status == 'paid' else 0.0) for e in self.expenses)

    @property
    def balance_due(self):
        return max(0.0, round(self.total_invoiced - self.total_paid, 2))


class RecurringCharge(db.Model):
    """Modèle des charges d'exploitation fixes / récurrentes mensuelles (Loyer, Salaire fixe employé, Wifi, etc.)"""
    __tablename__ = 'recurring_charges'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)             # Ex: Loyer Centre Principal, Abonnement Fibre Orange, Femme de ménage...
    category = db.Column(db.String(50), nullable=False, default='Loyer des locaux')
    amount = db.Column(db.Float, nullable=False, default=0.0)     # Montant mensuel prévisionnel en DH
    day_of_month = db.Column(db.Integer, default=1)              # Jour habituel d'échéance (1 à 31)
    payment_method = db.Column(db.String(50), default='Espèces') # Espèces, Virement, Chèque...
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    supplier_name = db.Column(db.String(120), nullable=True)     # Saisie libre ou dénormalisé
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True) # Liaison automatique employé
    beneficiary = db.Column(db.String(150), nullable=True)       # Nom bénéficiaire (Propriétaire, Employé séparé...)
    active = db.Column(db.Boolean, default=True)                 # Actif ou En pause
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship('Supplier', foreign_keys=[supplier_id])
    employee = db.relationship('Employee', foreign_keys=[employee_id])

    @property
    def effective_beneficiary(self):
        if self.employee:
            return f"{self.employee.full_name} ({self.employee.job_title})"
        if self.beneficiary:
            return self.beneficiary
        if self.supplier:
            return self.supplier.name
        return self.supplier_name or "—"


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    expense_type = db.Column(db.String(20), default='charge')  # 'achat' (Fournitures, Livres, Matériel) / 'charge' (Loyer, Eau/Élec, Salaires...)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    payment_method = db.Column(db.String(50), default='Espèces')
    reference_no = db.Column(db.String(50), nullable=True)  # Réf / N° Reçu
    invoice_no = db.Column(db.String(60), nullable=True)    # N° Facture / Bon fournisseur
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    supplier_name = db.Column(db.String(120), nullable=True) # Saisie libre ou nom dénormalisé
    due_date = db.Column(db.Date, nullable=True)            # Date d'échéance de paiement
    status = db.Column(db.String(20), default='paid')       # 'paid', 'unpaid', 'partial'
    paid_amount = db.Column(db.Float, default=0.0)          # Montant réglé
    tax_amount = db.Column(db.Float, default=0.0)           # TVA déductible optionnelle
    receipt_file = db.Column(db.String(255), nullable=True) # Pièce jointe / Facture / Photo reçu
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    teacher_expense_id = db.Column(db.Integer, nullable=True)
    recurring_charge_id = db.Column(db.Integer, db.ForeignKey('recurring_charges.id'), nullable=True)
    recurring_month = db.Column(db.String(7), nullable=True)  # Mois rattaché 'YYYY-MM'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')
    teacher = db.relationship('Teacher', foreign_keys=[teacher_id])
    recurring_charge = db.relationship('RecurringCharge', backref=db.backref('expenses', lazy='dynamic'))

    @property
    def effective_supplier(self):
        if self.supplier:
            return self.supplier.name
        return self.supplier_name or "—"

    @property
    def remaining_balance(self):
        if self.status == 'paid':
            return 0.0
        amt = self.amount or 0.0
        paid = self.paid_amount or 0.0
        return max(0.0, round(amt - paid, 2))

    @property
    def is_overdue(self):
        if self.status != 'paid' and self.due_date and self.due_date < date.today():
            return True
        return False

    @property
    def type_badge_label_fr(self):
        return "Achat" if self.expense_type == 'achat' else "Charge"

    @property
    def type_badge_label_ar(self):
        return "مشتريات" if self.expense_type == 'achat' else "مصاريف"


class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True)
    title = db.Column(db.String(150), nullable=False)
    publisher = db.Column(db.String(100))  # Cambridge, Oxford, Hachette...
    category = db.Column(db.String(30), default='language')  # language / tutoring / general
    level = db.Column(db.String(60))  # A1, A2, B1, 2Bac...
    purchase_price = db.Column(db.Float, default=0.0)
    sale_price = db.Column(db.Float, default=0.0)
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock_alert = db.Column(db.Integer, default=5)
    active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Teacher Deposition & Commission
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    payout_type = db.Column(db.String(20), default='fixed')  # 'fixed' (DH/unité) or 'percentage' (% prix vente)
    teacher_share = db.Column(db.Float, default=0.0)         # Montant fixe en DH OU pourcentage (%)

    teacher = db.relationship('Teacher', foreign_keys=[teacher_id])

    @property
    def is_teacher_product(self):
        return bool(self.teacher_id)

    def calculate_split(self, unit_price=None):
        price = unit_price if unit_price is not None else (self.sale_price or 0.0)
        if not self.teacher_id:
            return {'teacher_earned': 0.0, 'school_earned': round(price, 2)}
        if self.payout_type == 'percentage':
            pct = min(100.0, max(0.0, float(self.teacher_share or 0.0)))
            t_amt = round(price * (pct / 100.0), 2)
            s_amt = max(0.0, round(price - t_amt, 2))
            return {'teacher_earned': t_amt, 'school_earned': s_amt}
        else:
            # fixed DH per unit
            t_amt = min(price, max(0.0, float(self.teacher_share or 0.0)))
            s_amt = max(0.0, round(price - t_amt, 2))
            return {'teacher_earned': t_amt, 'school_earned': s_amt}

    @property
    def is_low_stock(self):
        return self.stock_quantity <= (self.min_stock_alert or 5)

    @property
    def display_name(self):
        pub = f" ({self.publisher})" if self.publisher else ""
        prof = f" [Prof. {self.teacher.full_name}]" if self.teacher else ""
        return f"{self.title}{pub}{prof} — {self.sale_price:.0f} DH"


class BookSale(db.Model):
    __tablename__ = 'book_sales'
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(30), index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), default='cash')
    sale_date = db.Column(db.Date, default=date.today, nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Teacher commission tracking
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    teacher_earned = db.Column(db.Float, default=0.0)
    school_earned = db.Column(db.Float, default=0.0)
    period_month = db.Column(db.String(7), nullable=True)  # 'YYYY-MM'

    book = db.relationship('Book')
    student = db.relationship('Student')
    user = db.relationship('User')
    teacher = db.relationship('Teacher', foreign_keys=[teacher_id])

    @validates('sale_date')
    def validate_sale_date(self, key, value):
        if value:
            if isinstance(value, datetime):
                value = value.date()
            if isinstance(value, str):
                try:
                    value = datetime.strptime(value.strip(), '%Y-%m-%d').date()
                except Exception:
                    value = date.today()
            if isinstance(value, date) and value > date.today():
                return date.today()
        return value or date.today()


class TeacherAdvance(db.Model):
    __tablename__ = 'teacher_advances'
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(30), unique=True, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    period_month = db.Column(db.String(7), nullable=False)  # 'YYYY-MM' (e.g. '2026-09')
    payment_method = db.Column(db.String(30), default='Espèces')  # 'Espèces', 'Virement', 'Chèque'
    reference_no = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='paid')  # 'paid', 'deducted', 'cancelled'
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref=db.backref('advances', lazy='dynamic', cascade='all, delete-orphan'))
    creator = db.relationship('User', foreign_keys=[recorded_by])
    expense = db.relationship('Expense', foreign_keys=[expense_id])


class TeacherExpense(db.Model):
    __tablename__ = 'teacher_expenses'
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(30), unique=True, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    expense_type = db.Column(db.String(30), default='copies')  # 'copies', 'book', 'paper', 'supplies', 'other'
    title = db.Column(db.String(150), nullable=False)
    unit_price = db.Column(db.Float, default=0.0)      # Prix par page ou unitaire (DH)
    quantity = db.Column(db.Integer, default=1)        # Nombre de copies/pages ou unités
    amount = db.Column(db.Float, nullable=False)       # Montant total à déduire (DH)
    date = db.Column(db.Date, default=date.today, nullable=False)
    period_month = db.Column(db.String(7), nullable=False)  # 'YYYY-MM' (mois de déduction sur paie)
    payment_method = db.Column(db.String(30), default='Retenue sur salaire')
    status = db.Column(db.String(20), default='pending')  # 'pending', 'deducted', 'cancelled'
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref=db.backref('teacher_expenses', lazy='dynamic', cascade='all, delete-orphan'))
    creator = db.relationship('User', foreign_keys=[recorded_by])
    expense = db.relationship('Expense', foreign_keys=[expense_id])

    @property
    def type_badge_label_fr(self):
        labels = {
            'copies': 'Photocopies / Tirages',
            'book': 'Livre / Manuel',
            'paper': 'Papier / Ramette',
            'supplies': 'Fournitures pédagogiques',
            'other': 'Autre charge'
        }
        return labels.get(self.expense_type, 'Frais Enseignant')

    @property
    def type_badge_label_ar(self):
        labels = {
            'copies': 'تصوير ونسخ وثائق',
            'book': 'كتاب / مقرر دراسي',
            'paper': 'أوراق وطباعة',
            'supplies': 'لوازم تعليمية',
            'other': 'مصاريف أخرى'
        }
        return labels.get(self.expense_type, 'مصاريف الأستاذ')


class TeacherSalaryPayout(db.Model):
    __tablename__ = 'teacher_salary_payouts'
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(30), unique=True, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False, index=True)
    period_month = db.Column(db.String(7), nullable=False, index=True)  # 'YYYY-MM' (ex: '2026-09')
    gross_amount = db.Column(db.Float, default=0.0)
    advances_deducted = db.Column(db.Float, default=0.0)
    expenses_deducted = db.Column(db.Float, default=0.0)
    prior_credit_deducted = db.Column(db.Float, default=0.0)
    book_sales_added = db.Column(db.Float, default=0.0)  # Gains sur vente d'articles/livres ajoutés au salaire
    net_amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, default=date.today, nullable=False)
    payment_method = db.Column(db.String(30), default='Espèces')  # 'Espèces', 'Virement', 'Chèque'
    reference_no = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='paid')  # 'paid', 'cancelled'
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref=db.backref('salary_payouts', lazy='dynamic', cascade='all, delete-orphan'))
    creator = db.relationship('User', foreign_keys=[recorded_by])
    expense = db.relationship('Expense', foreign_keys=[expense_id])


class TeacherPaymentVisibility(db.Model):
    __tablename__ = 'teacher_payment_visibility'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False, index=True)  # 1 to 12
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher = db.relationship('Teacher', backref=db.backref('payment_visibilities', lazy='dynamic', cascade='all, delete-orphan'))

    __table_args__ = (
        db.UniqueConstraint('teacher_id', 'year', 'month', name='uq_teacher_pay_vis'),
    )

    @property
    def period_month(self):
        return f"{self.year:04d}-{self.month:02d}"


class TeacherChargeItem(db.Model):
    __tablename__ = 'teacher_charge_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(30), default='supplies')  # copies, supplies, paper, book, other
    unit_price = db.Column(db.Float, default=0.0)
    unit_label = db.Column(db.String(50), default='unité')
    is_default = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TeacherCandidate(db.Model):
    """CV bank / pre-inscription for teacher candidates."""
    __tablename__ = 'teacher_candidates'
    id = db.Column(db.Integer, primary_key=True)
    # Identity
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(150))
    cin = db.Column(db.String(30))
    gender = db.Column(db.String(10), default='M')  # M / F
    date_of_birth = db.Column(db.Date)
    city = db.Column(db.String(100))
    # Academic
    specialty = db.Column(db.String(200))        # Mathématiques, Physique, …
    diplomas = db.Column(db.Text)                # Free text: Licence, Master, …
    years_experience = db.Column(db.Integer, default=0)
    availability = db.Column(db.String(200))     # e.g. "Matin, Soir, Week-end"
    expected_salary = db.Column(db.Float)
    # Application info
    source = db.Column(db.String(30), default='walk-in')  # walk-in / referral / online / other
    deposit_date = db.Column(db.Date, default=datetime.utcnow)
    cv_filename = db.Column(db.String(255))      # uploaded file name
    notes = db.Column(db.Text)
    # Status lifecycle
    status = db.Column(db.String(20), default='pending')  # pending / contacted / interview / hired / rejected / archived
    status_note = db.Column(db.String(300))
    # Conversion
    converted_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    converted_at = db.Column(db.DateTime, nullable=True)
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    converted_teacher = db.relationship('Teacher', foreign_keys=[converted_teacher_id])

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def status_label(self):
        labels = {
            'pending': 'En attente',
            'contacted': 'Contacté(e)',
            'interview': 'Entretien',
            'hired': 'Recruté(e)',
            'rejected': 'Rejeté(e)',
            'archived': 'Archivé(e)',
        }
        return labels.get(self.status, self.status)

    @property
    def status_color(self):
        colors = {
            'pending': '#f39c12',
            'contacted': '#3498db',
            'interview': '#9b59b6',
            'hired': '#27ae60',
            'rejected': '#e74c3c',
            'archived': '#95a5a6',
        }
        return colors.get(self.status, '#666')


# ---------------------------------------------------------------------------
# Employee & Staff Payroll Management (Personnel & Employés d'Institut)
# ---------------------------------------------------------------------------
class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, index=True, nullable=False)  # ex: EMP-001
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    cin = db.Column(db.String(30), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    photo = db.Column(db.String(255), nullable=True)
    nfc_uid = db.Column(db.String(50), nullable=True, index=True)
    job_title = db.Column(db.String(100), default='Employé(e)', nullable=False)  # Secrétaire, Femme de ménage, Agent d'accueil, Sécurité...
    department = db.Column(db.String(60), default='Administration')  # Administration, Accueil, Ménage/Entretien, Sécurité...
    salary_type = db.Column(db.String(30), default='monthly')  # monthly (Mensuel fixe), daily (Journalier), hourly (Horaire)
    base_salary = db.Column(db.Float, default=0.0, nullable=False)  # Salaire de base mensuel en DH
    hire_date = db.Column(db.Date, default=date.today)
    active = db.Column(db.Boolean, default=True)
    bank_name = db.Column(db.String(60), nullable=True)
    rib = db.Column(db.String(40), nullable=True)
    cnss_no = db.Column(db.String(40), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    payouts = db.relationship('EmployeeSalaryPayout', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    advances = db.relationship('EmployeeAdvance', backref='employee', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def avatar_url(self):
        if getattr(self, 'photo', None):
            return f"/static/uploads/{self.photo}"
        return f"https://ui-avatars.com/api/?name={self.first_name}+{self.last_name}&background=10b981&color=fff&size=128"

    @property
    def formatted_salary(self):
        return f"{self.base_salary:.2f} DH"


class EmployeeSalaryPayout(db.Model):
    __tablename__ = 'employee_salary_payouts'
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(40), unique=True, index=True, nullable=False)  # EMP-SAL-YYYYMM-XXXX
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    period_month = db.Column(db.String(7), nullable=False, index=True)  # 'YYYY-MM' (ex: '2026-09')
    base_salary = db.Column(db.Float, default=0.0)
    bonus_amount = db.Column(db.Float, default=0.0)  # Primes, gratifications, heures supp
    bonus_notes = db.Column(db.String(255), nullable=True)
    advances_deducted = db.Column(db.Float, default=0.0)  # Acomptes déduits
    deductions_amount = db.Column(db.Float, default=0.0)  # Absences ou retenues
    deductions_notes = db.Column(db.String(255), nullable=True)
    net_amount = db.Column(db.Float, nullable=False)  # Net versé
    payment_date = db.Column(db.Date, default=date.today, nullable=False)
    payment_method = db.Column(db.String(30), default='Espèces')  # 'Espèces', 'Virement', 'Chèque'
    reference_no = db.Column(db.String(60), nullable=True)
    status = db.Column(db.String(20), default='paid')  # 'paid', 'cancelled'
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[recorded_by])
    expense = db.relationship('Expense', foreign_keys=[expense_id])


class EmployeeAdvance(db.Model):
    __tablename__ = 'employee_advances'
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(40), unique=True, index=True, nullable=True)  # EMP-ADV-YYYYMM-XXXX
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    period_month = db.Column(db.String(7), nullable=False, index=True)  # 'YYYY-MM'
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    payment_method = db.Column(db.String(30), default='Espèces')
    reference_no = db.Column(db.String(60), nullable=True)
    status = db.Column(db.String(20), default='paid')  # 'paid', 'deducted', 'cancelled'
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[recorded_by])
    expense = db.relationship('Expense', foreign_keys=[expense_id])


class PlacementTest(db.Model):
    __tablename__ = 'placement_tests'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, index=True, nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    whatsapp = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    school_level = db.Column(db.String(60), nullable=True)
    objective = db.Column(db.String(150), nullable=True)
    language = db.Column(db.String(50), nullable=False, index=True)
    status = db.Column(db.String(20), default='pending', index=True)  # 'pending', 'completed'
    is_submitted = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float, default=0.0)
    max_score = db.Column(db.Float, default=0.0)
    percentage = db.Column(db.Float, default=0.0)
    recommended_level = db.Column(db.String(50), nullable=True)
    answers_json = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    enrolled_course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    enrolled_student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    mismatch_dismissed = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])
    enrolled_course = db.relationship('Course', foreign_keys=[enrolled_course_id])
    enrolled_student = db.relationship('Student', foreign_keys=[enrolled_student_id])

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @property
    def is_enrolled(self):
        return self.enrolled_course_id is not None or self.enrolled_student_id is not None

    @property
    def target_enrolled_course(self):
        if self.enrolled_course:
            return self.enrolled_course
        if self.enrolled_student:
            for e in self.enrolled_student.enrollments:
                if e.status in ('active', 'trial', 'paused') and e.course:
                    if e.course.category == 'language' or (e.course.language and e.course.language.lower() in (self.language or '').lower()):
                        return e.course
        return None

    @property
    def is_level_mismatch(self):
        """Détecte si le niveau recommandé diffère du niveau de la classe assignée ou inscrite."""
        if self.mismatch_dismissed:
            return False
        if not self.is_submitted or not self.recommended_level:
            return False
        
        target_course = self.target_enrolled_course
        if not target_course or not target_course.level:
            return False

        rec_str = (self.recommended_level or '').strip()
        c_str = (target_course.level or '').strip()

        rec_code = rec_str[:2].upper()
        c_code = c_str[:2].upper()

        valid_cefr = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
        if rec_code in valid_cefr and c_code in valid_cefr:
            return rec_code != c_code

        return rec_str.lower() != c_str.lower()


class PlacementQuestion(db.Model):
    __tablename__ = 'placement_questions'
    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(50), nullable=False, index=True)
    level = db.Column(db.String(20), nullable=False, index=True)  # 'A1', 'A2', 'B1', 'B2'
    category = db.Column(db.String(50), default='Grammaire')
    question_text = db.Column(db.Text, nullable=False)
    context_text = db.Column(db.Text, nullable=True)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=True)
    correct_option = db.Column(db.String(5), nullable=False)  # 'A', 'B', 'C', 'D'
    explanation = db.Column(db.Text, nullable=True)
    order_num = db.Column(db.Integer, default=1)
    active = db.Column(db.Boolean, default=True)
    audio_url = db.Column(db.String(255), nullable=True)  # Path or URL to MP3/audio file
    audio_script = db.Column(db.Text, nullable=True)      # Audio transcript / dialogue text
    max_plays = db.Column(db.Integer, default=2)          # Max listens allowed (exam condition)


class StaffNote(db.Model):
    __tablename__ = 'staff_notes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='normal', index=True)  # 'normal', 'high', 'urgent'
    category = db.Column(db.String(50), default='general', index=True)  # 'general', 'reception', 'finance', 'pedagogy', 'maintenance'
    
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_type = db.Column(db.String(20), default='all')  # 'all' ou 'specific'
    target_user_ids = db.Column(db.Text, nullable=True)   # JSON list of user IDs, e.g. "[1, 9]"
    
    status = db.Column(db.String(20), default='pending', index=True)  # 'pending' (À traiter), 'done' (Traité / Réglé)
    is_pinned = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date, nullable=True)
    
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_note = db.Column(db.Text, nullable=True)
    
    read_by_json = db.Column(db.Text, nullable=True)  # JSON dict of user IDs to timestamp: {"1": "04/10/2026 à 18:30"}
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship('User', foreign_keys=[author_id])
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_id])

    def get_target_ids(self):
        import json
        if not self.target_user_ids or self.target_type == 'all':
            return []
        try:
            return [int(x) for x in json.loads(self.target_user_ids)]
        except Exception:
            return []

    def is_visible_to(self, user):
        if not user:
            return False
        # Admins and author can always see
        if user.role == 'admin' or user.id == self.author_id:
            return True
        if self.target_type == 'all':
            return True
        target_ids = self.get_target_ids()
        return user.id in target_ids

    def get_read_users(self):
        import json
        if not self.read_by_json:
            return {}
        try:
            return json.loads(self.read_by_json)
        except Exception:
            return {}

    def is_read_by(self, user_id):
        return str(user_id) in self.get_read_users()

    def mark_read(self, user_id):
        import json
        reads = self.get_read_users()
        uid_str = str(user_id)
        if uid_str not in reads:
            reads[uid_str] = datetime.utcnow().strftime('%d/%m/%Y à %H:%M')
            self.read_by_json = json.dumps(reads)

    @property
    def priority_label(self):
        labels = {
            'urgent': {'fr': 'Urgent', 'ar': 'عاجل', 'color': '#ef4444', 'bg': '#fee2e2', 'icon': '🔴'},
            'high': {'fr': 'Important', 'ar': 'هام', 'color': '#f97316', 'bg': '#ffedd5', 'icon': '🟠'},
            'normal': {'fr': 'Normal', 'ar': 'عادي', 'color': '#10b981', 'bg': '#dcfce7', 'icon': '🟢'}
        }
        return labels.get(self.priority, labels['normal'])

    @property
    def category_label(self):
        cats = {
            'general': {'fr': 'Général', 'ar': 'عام', 'icon': '📌'},
            'reception': {'fr': 'Accueil & Inscription', 'ar': 'الاستقبال والتسجيل', 'icon': '👋'},
            'finance': {'fr': 'Paiement & Caisse', 'ar': 'الأداء والصندوق', 'icon': '💰'},
            'pedagogy': {'fr': 'Pédagogie & Profs', 'ar': 'بيداغوجي والأساتذة', 'icon': '📚'},
            'maintenance': {'fr': 'Locaux & Matériel', 'ar': 'القاعات والمعدات', 'icon': '🔑'}
        }
        return cats.get(self.category, cats['general'])


class TeacherStudentRequest(db.Model):
    """Demande d'ajout d'élève soumise par un enseignant en attente de validation admin."""
    __tablename__ = 'teacher_student_requests'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    school_level = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    status = db.Column(db.String(30), default='pending', index=True)  # 'pending', 'approved', 'rejected'
    rejection_reason = db.Column(db.String(255), nullable=True)
    enrolled_student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    course = db.relationship('Course', backref=db.backref('teacher_student_requests', lazy=True))
    teacher = db.relationship('Teacher', backref=db.backref('student_requests', lazy=True))
    enrolled_student = db.relationship('Student', backref=db.backref('teacher_requests', lazy=True))
    processed_by = db.relationship('User', foreign_keys=[processed_by_id])


class TeacherWeeklyPlan(db.Model):
    """Fiche pedagogique hebdomadaire soumise par les professeurs de langues."""
    __tablename__ = 'teacher_weekly_plans'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False, index=True)
    week_start_date = db.Column(db.Date, nullable=False, index=True)
    week_end_date = db.Column(db.Date, nullable=False)
    language = db.Column(db.String(10), default='en')  # 'en', 'fr', 'de', 'es', 'ar'
    communicative_objectives = db.Column(db.Text, nullable=True)
    grammar_syntax = db.Column(db.Text, nullable=True)
    vocab_lexicon = db.Column(db.Text, nullable=True)
    sessions_json = db.Column(db.Text, nullable=True)  # JSON string containing session list
    upcoming_evaluations = db.Column(db.Text, nullable=True)
    special_needs = db.Column(db.Text, nullable=True)
    supplies_needed = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='submitted', index=True)  # 'draft', 'submitted', 'validated'
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_by = db.Column(db.String(50), default='teacher')  # 'teacher', 'admin'
    validated_at = db.Column(db.DateTime, nullable=True)
    validated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher = db.relationship('Teacher', backref=db.backref('weekly_pedagogical_plans', lazy='dynamic', cascade='all, delete-orphan'))
    validated_by = db.relationship('User', foreign_keys=[validated_by_id])

    @property
    def sessions_list(self):
        if not self.sessions_json:
            return []
        try:
            import json
            return json.loads(self.sessions_json)
        except Exception:
            return []


class BadgeDistributionBatch(db.Model):
    """Lot de distribution des badges imprimés pour tournée en classe."""
    __tablename__ = 'badge_distribution_batches'
    id = db.Column(db.Integer, primary_key=True)
    batch_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(150), default='Lot de distribution de badges')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    total_scanned = db.Column(db.Integer, default=0)
    total_present_today = db.Column(db.Integer, default=0)
    total_no_class_today = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default='saved')  # 'saved', 'completed'

    created_by = db.relationship('User', foreign_keys=[created_by_id])
    items = db.relationship('BadgeDistributionItem', backref='batch', cascade='all, delete-orphan', order_by='BadgeDistributionItem.id.asc()')

    @property
    def total_delivered(self):
        return sum(1 for it in self.items if it.is_delivered and it.has_class_today)

    @property
    def total_pending(self):
        present = self.total_present_today or 0
        return max(0, present - self.total_delivered)

    @property
    def delivery_pct(self):
        present = self.total_present_today or 0
        if present == 0:
            return 100 if self.total_scanned > 0 else 0
        return int(round(self.total_delivered / present * 100))

    @property
    def rooms_summary(self):
        rooms = set()
        for it in self.items:
            if it.has_class_today and it.room_name:
                rooms.add(it.room_name)
        return ", ".join(sorted(list(rooms))) if rooms else "Aucune"



class BadgeDistributionItem(db.Model):
    """Badge individuel scanné dans le lot de distribution avec son affectation de salle."""
    __tablename__ = 'badge_distribution_items'
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('badge_distribution_batches.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    scanned_raw = db.Column(db.String(100), nullable=True)

    has_class_today = db.Column(db.Boolean, default=False)
    course_name = db.Column(db.String(150), nullable=True)
    room_name = db.Column(db.String(100), nullable=True)
    teacher_name = db.Column(db.String(100), nullable=True)
    time_slot = db.Column(db.String(50), nullable=True)
    timing_state = db.Column(db.String(30), nullable=True)
    next_class_info = db.Column(db.String(150), nullable=True)

    is_delivered = db.Column(db.Boolean, default=False)
    delivered_at = db.Column(db.DateTime, nullable=True)

    student = db.relationship('Student')





