# -*- coding: utf-8 -*-
from models import db, Setting

DEFAULTS = {
    # -- Général / Institut --
    "inst_name": "Institut Atlas des Langues",
    "inst_tagline": "Langues & Soutien Scolaire",
    "inst_address": "12, Avenue Mohammed V",
    "inst_city": "Casablanca",
    "inst_phone": "0522-00-00-00",
    "inst_whatsapp": "06-00-00-00-00",
    "inst_email": "contact@institutilas.com",
    "inst_website": "www.institut.ma",
    "inst_ice": "000000000000000000",
    "inst_if": "0000000",
    "inst_rc": "000000",
    "inst_patente": "00000000",
    "inst_cnss": "000000",
    "currency": "MAD",
    "school_year": "2025/2026",

    # -- Wi-Fi de l'établissement --
    "wifi_floor1_ssid": "TP-Link-569C",
    "wifi_floor1_pass": "87646535",
    "wifi_floor2_ssid": "TP_Link_5758_5G",
    "wifi_floor2_pass": "30957008",

    # -- Langue & apparence --
    "default_lang": "fr",
    "theme_color": "#1f6feb",
    "session_timeout_minutes": "30",

    # -- Facturation / TVA --
    "tva_rate": "0",
    "invoice_prefix": "FA-",
    "quote_prefix": "DEV-",
    "next_invoice_number": "1",
    "receipt_prefix": "REC-",
    "next_receipt_number": "1",
    "receipt_design": "default",
    "due_days": "7",
    "invoice_footer": "Merci de votre confiance. Paiement par espèces, virement ou carte.",
    "auto_invoice_on_enroll": "1",
    "enable_partial_payment": "1",
    "enable_tva": "0",
    "bank_name": "",
    "bank_rib": "",
    "bank_holder": "",

    # -- Paiements (méthodes activées) --
    "pay_cash": "1",
    "pay_transfer": "1",
    "pay_card": "1",
    "pay_online": "1",

    # -- Élèves --
    "student_prefix": "ETU",
    "next_student_number": "1",
    "student_photo": "1",

    # -- Cours --
    "course_prefix": "CRS",

    # -- Fonctionnalités --
    "enable_attendance": "1",
    "enable_grades": "1",
    "enable_badges": "1",
    "late_minutes_threshold": "10",

    # -- Badges (template) --
    "badge_template": "student",   # student / course
    "badge_width_mm": "85",
    "badge_height_mm": "54",
    "badge_show_photo": "1",
    "badge_show_code": "1",
    "badge_show_course": "1",
    "badge_show_institute": "1",
    "badge_background_color": "#ffffff",
    "badge_font_size": "12",
    "badge_conditions": "Cette carte est la propriété de l'institut. Elle est strictement personnelle et non transférable. L'élève s'engage à respecter le règlement intérieur de l'établissement. En cas de perte, veuillez contacter l'administration.",

    # -- Enseignants & Tirages --
    "teacher_copy_price_page": "0.50",

    # -- Sauvegarde Google Drive & Exports Automatiques --
    "gdrive_enabled": "1",
    "gdrive_auth_type": "oauth2",  # oauth2 / service_account
    "gdrive_client_id": "",
    "gdrive_client_secret": "",
    "gdrive_refresh_token": "",
    "gdrive_access_token": "",
    "gdrive_token_expiry": "",
    "gdrive_account_email": "",
    "gdrive_service_account_json": "",
    "gdrive_folder_name": "Institut_ILAS_Backups",
    "gdrive_backup_time": "22:00",
    "gdrive_ask_at_22": "1",
    "gdrive_export_excels": "1",
    "gdrive_last_backup_date": "",
    "gdrive_last_backup_time": "",
    "gdrive_last_backup_status": "never",
    "gdrive_last_backup_error": "",
    "gdrive_last_backup_file": "",
    "gdrive_last_excel_file": "",
    "gdrive_last_classes_file": "",
    "gdrive_last_backup_link": "",
    "gdrive_last_excel_link": "",
    "gdrive_last_classes_link": "",
}


_SETTINGS_CACHE = None


def _load_cache():
    global _SETTINGS_CACHE
    try:
        out = dict(DEFAULTS)
        for s in Setting.query.all():
            out[s.key] = s.value
        _SETTINGS_CACHE = out
    except Exception:
        return DEFAULTS
    return _SETTINGS_CACHE


def invalidate_cache():
    global _SETTINGS_CACHE
    _SETTINGS_CACHE = None


def get_setting(key, default=None):
    global _SETTINGS_CACHE
    if _SETTINGS_CACHE is None:
        _load_cache()
    if _SETTINGS_CACHE and key in _SETTINGS_CACHE and _SETTINGS_CACHE[key] != '':
        return _SETTINGS_CACHE[key]
    return default if default is not None else DEFAULTS.get(key, '')


def get_int(key, default=0):
    try:
        return int(get_setting(key, default))
    except (TypeError, ValueError):
        return default


def get_float(key, default=0.0):
    try:
        return float(get_setting(key, default))
    except (TypeError, ValueError):
        return default


def set_setting(key, value):
    global _SETTINGS_CACHE
    s = Setting.query.get(key)
    if s is None:
        s = Setting(key=key, value=str(value))
        db.session.add(s)
    else:
        s.value = str(value)
    if _SETTINGS_CACHE is not None:
        _SETTINGS_CACHE[key] = str(value)


def is_enabled(key):
    return get_setting(key, "0") == "1"


def all_settings_dict():
    global _SETTINGS_CACHE
    if _SETTINGS_CACHE is None:
        _load_cache()
    return dict(_SETTINGS_CACHE) if _SETTINGS_CACHE else dict(DEFAULTS)


def seed_defaults():
    for k, v in DEFAULTS.items():
        if Setting.query.get(k) is None:
            db.session.add(Setting(key=k, value=str(v)))
    db.session.commit()
    invalidate_cache()


def gen_code(prefix_key, next_key):
    """Génère un code type ETU001 et incrémente le compteur."""
    n = get_int(next_key, 1)
    set_setting(next_key, n + 1)
    db.session.commit()
    prefix = get_setting(prefix_key, "ETU")
    return f"{prefix}{n:03d}"


def next_invoice_number(prefix_key="invoice_prefix", next_key="next_invoice_number"):
    n = get_int(next_key, 1)
    set_setting(next_key, n + 1)
    db.session.commit()
    prefix = get_setting(prefix_key, "FA-")
    return f"{prefix}{n:04d}"
