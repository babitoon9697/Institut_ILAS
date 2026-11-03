# -*- coding: utf-8 -*-
"""
gdrive_service.py
Service complet pour l'intégration Google Drive de l'Institut ILAS:
- Authentification OAuth 2.0 (Compte personnel / professionnel Google) & Compte de service (Service Account)
- Téléversement automatique des sauvegardes de la base SQLite (.zip)
- Téléversement automatique des exports complets Excel (.xlsx) de toutes les données
- Nettoyage et rotation automatique des anciennes sauvegardes sur Google Drive
- Suivi du statut quotidien et rappels à 22:00
"""

import os
import sys
import json
import time
import zipfile
import urllib.parse
from datetime import datetime, date
import requests

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import settings_helper
import excel_export_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/userinfo.email',
]


def is_gdrive_configured():
    """Vérifie si Google Drive est prêt et configuré (OAuth ou Service Account)."""
    auth_type = settings_helper.get_setting('gdrive_auth_type', 'oauth2')
    if auth_type == 'service_account':
        sa_json = settings_helper.get_setting('gdrive_service_account_json', '').strip()
        return bool(sa_json)
    else:
        refresh_token = settings_helper.get_setting('gdrive_refresh_token', '').strip()
        client_id = settings_helper.get_setting('gdrive_client_id', '').strip()
        client_secret = settings_helper.get_setting('gdrive_client_secret', '').strip()
        return bool(refresh_token and client_id and client_secret)


def get_oauth_authorization_url(redirect_uri, state=None):
    """Génère l'URL d'autorisation OAuth2 Google."""
    client_id = settings_helper.get_setting('gdrive_client_id', '').strip()
    if not client_id:
        raise ValueError("Google Client ID manquant. Veuillez le renseigner dans les réglages.")

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true'
    }
    if state:
        params['state'] = state

    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(code, redirect_uri):
    """
    Échange le code d'autorisation OAuth2 contre les jetons (access_token & refresh_token).
    Récupère également l'adresse email du compte Google connecté.
    """
    client_id = settings_helper.get_setting('gdrive_client_id', '').strip()
    client_secret = settings_helper.get_setting('gdrive_client_secret', '').strip()

    if not client_id or not client_secret:
        raise ValueError("Client ID ou Client Secret introuvable.")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    res = requests.post(token_url, data=data, timeout=15)
    token_json = res.json()

    if res.status_code != 200 or 'error' in token_json:
        err_msg = token_json.get('error_description') or token_json.get('error') or res.text
        raise RuntimeError(f"Erreur d'authentification Google : {err_msg}")

    access_token = token_json.get('access_token', '')
    refresh_token = token_json.get('refresh_token', '')
    expires_in = token_json.get('expires_in', 3600)
    expiry_ts = int(time.time()) + int(expires_in)

    # Récupérer l'email de l'utilisateur Google
    account_email = ""
    try:
        userinfo_res = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={'Authorization': f"Bearer {access_token}"},
            timeout=10
        )
        if userinfo_res.status_code == 200:
            account_email = userinfo_res.json().get('email', '')
    except Exception:
        pass

    # Enregistrer dans la base de données
    settings_helper.set_setting('gdrive_access_token', access_token)
    if refresh_token:
        settings_helper.set_setting('gdrive_refresh_token', refresh_token)
    settings_helper.set_setting('gdrive_token_expiry', str(expiry_ts))
    if account_email:
        settings_helper.set_setting('gdrive_account_email', account_email)
    settings_helper.set_setting('gdrive_auth_type', 'oauth2')
    settings_helper.set_setting('gdrive_enabled', '1')
    settings_helper.set_setting('gdrive_token_expired', '0')
    settings_helper.set_setting('gdrive_last_backup_error', '')
    if settings_helper.get_setting('gdrive_last_backup_status') == 'failed':
        settings_helper.set_setting('gdrive_last_backup_status', 'connected')

    from models import db
    db.session.commit()
    settings_helper.invalidate_cache()

    return {
        'email': account_email,
        'has_refresh_token': bool(refresh_token)
    }


def disconnect_gdrive():
    """Supprime les identifiants Google Drive enregistrés."""
    from models import db
    settings_helper.set_setting('gdrive_access_token', '')
    settings_helper.set_setting('gdrive_refresh_token', '')
    settings_helper.set_setting('gdrive_account_email', '')
    settings_helper.set_setting('gdrive_token_expiry', '')
    settings_helper.set_setting('gdrive_service_account_json', '')
    settings_helper.set_setting('gdrive_token_expired', '0')
    settings_helper.set_setting('gdrive_last_backup_error', '')
    settings_helper.set_setting('gdrive_last_backup_status', 'disconnected')
    db.session.commit()
    settings_helper.invalidate_cache()


def get_drive_credentials():
    """Charge et rafraîchit automatiquement les identifiants Google Drive."""
    auth_type = settings_helper.get_setting('gdrive_auth_type', 'oauth2')

    if auth_type == 'service_account':
        sa_raw = settings_helper.get_setting('gdrive_service_account_json', '').strip()
        if not sa_raw:
            raise ValueError("Configuration Compte de Service Google manquante.")
        sa_info = json.loads(sa_raw)
        creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
        return creds

    # Mode OAuth 2.0
    client_id = settings_helper.get_setting('gdrive_client_id', '').strip()
    client_secret = settings_helper.get_setting('gdrive_client_secret', '').strip()
    refresh_token = settings_helper.get_setting('gdrive_refresh_token', '').strip()
    access_token = settings_helper.get_setting('gdrive_access_token', '').strip()

    if not client_id or not client_secret or not refresh_token:
        raise ValueError("Google Drive n'est pas encore connecté. Veuillez renseigner vos identifiants.")

    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    # Rafraîchir le token si expiré
    try:
        if not creds.valid or not access_token:
            creds.refresh(Request())
            settings_helper.set_setting('gdrive_access_token', creds.token or '')
            settings_helper.set_setting('gdrive_token_expired', '0')
            try:
                from models import db
                db.session.commit()
            except Exception:
                pass
    except Exception as e:
        err_str = str(e)
        if any(w in err_str.lower() for w in ['invalid_grant', 'expired', 'revoked', 'token has been expired']):
            settings_helper.set_setting('gdrive_token_expired', '1')
            settings_helper.set_setting('gdrive_last_backup_status', 'failed')
            settings_helper.set_setting('gdrive_last_backup_error', err_str)
            try:
                from models import db
                db.session.commit()
                settings_helper.invalidate_cache()
            except Exception:
                pass
        raise

    return creds


def get_drive_service():
    """Retourne une instance du client API Google Drive v3."""
    creds = get_drive_credentials()
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


def get_or_create_folder(folder_name='Institut_ILAS_Backups', service=None):
    """
    Recherche ou crée le dossier de sauvegarde dans Google Drive.
    Retourne l'ID du dossier.
    """
    if service is None:
        service = get_drive_service()

    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])

    if files:
        return files[0]['id']

    # Création du dossier
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder.get('id')


def upload_file_to_drive(file_path, folder_id, mime_type=None, new_name=None, service=None):
    """
    Téléverse un fichier local vers le dossier Google Drive spécifié.
    Retourne les métadonnées du fichier (id, name, webViewLink, size).
    """
    if service is None:
        service = get_drive_service()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier à téléverser introuvable : {file_path}")

    filename = new_name or os.path.basename(file_path)
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }

    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    file_obj = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink, size'
    ).execute()

    return file_obj


def rotate_backups_on_drive(folder_id, keep_last=30, service=None):
    """Supprime les anciennes sauvegardes du dossier Google Drive pour ne garder que les N plus récentes."""
    if service is None:
        service = get_drive_service()

    try:
        q = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=q,
            spaces='drive',
            fields='files(id, name, createdTime, mimeType)',
            orderBy='createdTime desc',
            pageSize=100
        ).execute()
        files = results.get('files', [])

        # On filtre les fichiers de sauvegarde (.zip et .xlsx)
        backup_files = [f for f in files if f.get('mimeType') != 'application/vnd.google-apps.folder']

        if len(backup_files) > keep_last:
            for old_file in backup_files[keep_last:]:
                try:
                    service.files().delete(fileId=old_file['id']).execute()
                except Exception:
                    pass
    except Exception:
        pass


def perform_full_backup(reason='auto'):
    """
    Exécute une sauvegarde complète :
    1. Crée l'archive ZIP de la base SQLite
    2. Exporte toutes les données dans un fichier Excel multi-feuilles
    3. Téléverse les deux fichiers vers Google Drive dans le dossier configuré
    4. Effectue la rotation des sauvegardes sur Google Drive
    5. Met à jour les paramètres de statut de l'application
    """
    from models import db

    now_dt = datetime.now()
    today_str = now_dt.strftime('%Y-%m-%d')
    ts = now_dt.strftime('%Y%m%d_%H%M%S')

    os.makedirs(BACKUPS_DIR, exist_ok=True)
    db_path = os.path.join(BASE_DIR, 'institut.db')

    if not os.path.exists(db_path):
        raise FileNotFoundError("Base de données institut.db introuvable.")

    result = {
        'status': 'error',
        'db_zip_name': None,
        'db_zip_link': None,
        'excel_name': None,
        'excel_link': None,
        'error': None,
        'timestamp': now_dt.strftime('%d/%m/%Y à %H:%M:%S')
    }

    try:
        # 1. Créer la sauvegarde ZIP de la base de données
        zip_filename = f"backup_ilas_{reason}_{ts}.zip"
        zip_filepath = os.path.join(BACKUPS_DIR, zip_filename)
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_path, arcname='institut.db')
        result['db_zip_name'] = zip_filename

        # Rotation locale (15 dernières)
        all_local_backups = sorted(
            [f for f in os.listdir(BACKUPS_DIR) if f.startswith('backup_') and f.endswith('.zip')],
            key=lambda x: os.path.getmtime(os.path.join(BACKUPS_DIR, x)),
            reverse=True
        )
        for old in all_local_backups[15:]:
            try:
                os.remove(os.path.join(BACKUPS_DIR, old))
            except Exception:
                pass

        # 2. Exporter les fichiers Excel si l'option est activée
        export_excels = settings_helper.get_setting('gdrive_export_excels', '1') == '1'
        excel_filepath = None
        classes_filepath = None
        if export_excels:
            # A. Classeur dédié Classes & Élèves groupés par classe
            classes_filename = f"ILAS_Classes_et_Eleves_{ts}.xlsx"
            classes_filepath = os.path.join(BACKUPS_DIR, classes_filename)
            excel_export_service.create_classes_students_excel(db_path=db_path, output_path=classes_filepath)
            result['classes_excel_name'] = classes_filename

            # B. Classeur Export Global complet (19 tables)
            excel_filename = f"ILAS_Export_Global_{ts}.xlsx"
            excel_filepath = os.path.join(BACKUPS_DIR, excel_filename)
            excel_export_service.create_master_excel_export(db_path=db_path, output_path=excel_filepath)
            result['excel_name'] = excel_filename

        # 3. Téléverser sur Google Drive si configuré
        if not is_gdrive_configured():
            raise RuntimeError("Google Drive non configuré ou compte non lié.")

        service = get_drive_service()
        folder_name = settings_helper.get_setting('gdrive_folder_name', 'Institut_ILAS_Backups') or 'Institut_ILAS_Backups'
        folder_id = get_or_create_folder(folder_name=folder_name, service=service)

        # Upload de la base de données ZIP
        db_upload = upload_file_to_drive(
            zip_filepath,
            folder_id,
            mime_type='application/zip',
            new_name=zip_filename,
            service=service
        )
        result['db_zip_link'] = db_upload.get('webViewLink')

        # Upload de l'Excel Classes & Élèves
        if classes_filepath and os.path.exists(classes_filepath):
            classes_upload = upload_file_to_drive(
                classes_filepath,
                folder_id,
                mime_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                new_name=result['classes_excel_name'],
                service=service
            )
            result['classes_excel_link'] = classes_upload.get('webViewLink')

        # Upload de l'Excel Global
        if excel_filepath and os.path.exists(excel_filepath):
            excel_upload = upload_file_to_drive(
                excel_filepath,
                folder_id,
                mime_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                new_name=result['excel_name'],
                service=service
            )
            result['excel_link'] = excel_upload.get('webViewLink')

        # Rotation des fichiers dans Google Drive (garder 30 versions)
        rotate_backups_on_drive(folder_id=folder_id, keep_last=30, service=service)

        # Enregistrer le succès
        result['status'] = 'success'
        settings_helper.set_setting('gdrive_last_backup_date', today_str)
        settings_helper.set_setting('gdrive_last_backup_time', now_dt.strftime('%Y-%m-%d %H:%M:%S'))
        settings_helper.set_setting('gdrive_last_backup_status', 'success')
        settings_helper.set_setting('gdrive_last_backup_file', zip_filename)
        settings_helper.set_setting('gdrive_last_backup_link', result['db_zip_link'] or '')
        settings_helper.set_setting('gdrive_token_expired', '0')
        if result.get('classes_excel_name'):
            settings_helper.set_setting('gdrive_last_classes_file', result['classes_excel_name'])
            settings_helper.set_setting('gdrive_last_classes_link', result['classes_excel_link'] or '')
        if result.get('excel_name'):
            settings_helper.set_setting('gdrive_last_excel_file', result['excel_name'])
            settings_helper.set_setting('gdrive_last_excel_link', result['excel_link'] or '')
        settings_helper.set_setting('gdrive_last_backup_error', '')

        db.session.commit()
        settings_helper.invalidate_cache()

    except Exception as e:
        err_str = str(e)
        result['status'] = 'error'
        result['error'] = err_str
        settings_helper.set_setting('gdrive_last_backup_status', 'failed')
        settings_helper.set_setting('gdrive_last_backup_error', err_str)
        settings_helper.set_setting('gdrive_last_backup_time', now_dt.strftime('%Y-%m-%d %H:%M:%S'))
        if any(w in err_str.lower() for w in ['invalid_grant', 'expired', 'revoked', 'token has been expired']):
            settings_helper.set_setting('gdrive_token_expired', '1')
        try:
            db.session.commit()
            settings_helper.invalidate_cache()
        except Exception:
            pass

    return result


def export_excels_only_to_drive():
    """Génère et téléverse immédiatement les deux fichiers Excel complets vers Google Drive."""
    from models import db

    if not is_gdrive_configured():
        raise RuntimeError("Google Drive non configuré ou compte non connecté.")

    now_dt = datetime.now()
    ts = now_dt.strftime('%Y%m%d_%H%M%S')
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    db_path = os.path.join(BASE_DIR, 'institut.db')

    # A. Classes & Élèves
    classes_filename = f"ILAS_Classes_et_Eleves_{ts}.xlsx"
    classes_filepath = os.path.join(BACKUPS_DIR, classes_filename)
    excel_export_service.create_classes_students_excel(db_path=db_path, output_path=classes_filepath)

    # B. Export Global
    excel_filename = f"ILAS_Export_Global_{ts}.xlsx"
    excel_filepath = os.path.join(BACKUPS_DIR, excel_filename)
    excel_export_service.create_master_excel_export(db_path=db_path, output_path=excel_filepath)

    service = get_drive_service()
    folder_name = settings_helper.get_setting('gdrive_folder_name', 'Institut_ILAS_Backups') or 'Institut_ILAS_Backups'
    folder_id = get_or_create_folder(folder_name=folder_name, service=service)

    # Upload Classes & Élèves
    classes_upload = upload_file_to_drive(
        classes_filepath,
        folder_id,
        mime_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        new_name=classes_filename,
        service=service
    )
    classes_link = classes_upload.get('webViewLink', '')

    # Upload Global
    excel_upload = upload_file_to_drive(
        excel_filepath,
        folder_id,
        mime_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        new_name=excel_filename,
        service=service
    )
    link = excel_upload.get('webViewLink', '')

    settings_helper.set_setting('gdrive_last_classes_file', classes_filename)
    settings_helper.set_setting('gdrive_last_classes_link', classes_link)
    settings_helper.set_setting('gdrive_last_excel_file', excel_filename)
    settings_helper.set_setting('gdrive_last_excel_link', link)
    db.session.commit()
    settings_helper.invalidate_cache()

    return {
        'classes_filename': classes_filename,
        'classes_link': classes_link,
        'filename': excel_filename,
        'link': link,
        'size': os.path.getsize(classes_filepath) + os.path.getsize(excel_filepath)
    }


def get_daily_backup_status():
    """
    Vérifie l'état de la sauvegarde du jour :
    - Retourne si la sauvegarde a été faite aujourd'hui
    - Indique si l'heure limite (22:00) est dépassée
    - Détermine si l'application doit afficher la modale de rappel à l'utilisateur
    """
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    current_time_str = now.strftime('%H:%M')

    scheduled_time = settings_helper.get_setting('gdrive_backup_time', '22:00') or '22:00'
    last_backup_date = settings_helper.get_setting('gdrive_last_backup_date', '')
    last_status = settings_helper.get_setting('gdrive_last_backup_status', 'never')
    last_backup_time = settings_helper.get_setting('gdrive_last_backup_time', '')
    last_error = settings_helper.get_setting('gdrive_last_backup_error', '')
    last_file = settings_helper.get_setting('gdrive_last_backup_file', '')
    last_link = settings_helper.get_setting('gdrive_last_backup_link', '')
    last_classes_file = settings_helper.get_setting('gdrive_last_classes_file', '')
    last_classes_link = settings_helper.get_setting('gdrive_last_classes_link', '')
    last_excel_file = settings_helper.get_setting('gdrive_last_excel_file', '')
    last_excel_link = settings_helper.get_setting('gdrive_last_excel_link', '')
    account_email = settings_helper.get_setting('gdrive_account_email', '')
    gdrive_enabled = settings_helper.get_setting('gdrive_enabled', '1') == '1'
    ask_at_22 = settings_helper.get_setting('gdrive_ask_at_22', '1') == '1'

    configured = is_gdrive_configured()
    last_error_str = str(last_error or '')
    token_expired = bool(
        settings_helper.get_setting('gdrive_token_expired', '0') == '1' or
        any(w in last_error_str.lower() for w in ['invalid_grant', 'expired or revoked', 'token has been expired'])
    )
    today_backup_done = (last_backup_date == today_str and last_status == 'success')

    # Heure actuelle par rapport à scheduled_time (par défaut 22:00)
    try:
        sched_h, sched_m = map(int, scheduled_time.split(':'))
    except Exception:
        sched_h, sched_m = 22, 0

    is_time_to_ask = False
    if ask_at_22 and not today_backup_done:
        # Si on est entre scheduled_time (ex: 22:00) et 04:00 du matin le lendemain
        if now.hour > sched_h or (now.hour == sched_h and now.minute >= sched_m) or now.hour < 4:
            is_time_to_ask = True

    return {
        'today': today_str,
        'current_time': current_time_str,
        'scheduled_time': scheduled_time,
        'configured': configured,
        'token_expired': token_expired,
        'enabled': gdrive_enabled,
        'account_email': account_email,
        'today_backup_done': today_backup_done,
        'is_time_to_ask': is_time_to_ask,
        'last_backup_date': last_backup_date,
        'last_backup_time': last_backup_time,
        'last_status': last_status,
        'last_error': last_error,
        'last_file': last_file,
        'last_link': last_link,
        'last_classes_file': last_classes_file,
        'last_classes_link': last_classes_link,
        'last_excel_file': last_excel_file,
        'last_excel_link': last_excel_link
    }
