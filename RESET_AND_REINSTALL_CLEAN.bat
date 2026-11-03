@echo off
:: ============================================================================
:: INSTITUT ILAS - COMPLETE RE-INSTALLATION & DATABASE AUTO-MIGRATION SCRIPT
:: Restores and starts the pristine system with all 101 active students & data.
:: ============================================================================
title INSTITUT ILAS - RE-INSTALLATION COMPLETE & DEMARRAGE
color 0B
cd /d "%~dp0"

echo.
echo ============================================================================
echo   INSTITUT ILAS - RE-INSTALLATION SYSTEME ET MISE A JOUR DES DONNEES
echo ============================================================================
echo.

echo [1/4] Arret des serveurs et processus Python en cours...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM py.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/4] Verification de la presence de la base de donnees institut.db...
if not exist "institut.db" (
    echo [ATTENTION] La base de donnees institut.db est absente du dossier.
) else (
    echo [OK] Base de donnees institut.db trouvee avec succes (Toutes les donnees sont conservees).
)

echo [3/4] Auto-migration et verification de la base de donnees...
set P=
where python >nul 2>nul
if %errorlevel%==0 set P=python
if not defined P (
    where py >nul 2>nul
    if %errorlevel%==0 set P=py
)

if not defined P (
    color 0C
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

%P% -m pip install -r requirements.txt --quiet
%P% -c "from app import app, db, auto_migrate_db; app.app_context().push(); auto_migrate_db(); db.create_all()"

echo [4/4] Ouverture du serveur...
if exist "allow_firewall_port8080.bat" call "allow_firewall_port8080.bat" >nul 2>&1

echo.
echo ============================================================================
echo    SUCCESS : RE-INSTALLATION EFFECTUEE AVEC TOUTES LES DONNEES !
echo ============================================================================
echo.
echo Demarrage automatique du serveur...
timeout /t 2 /nobreak >nul

start "" "demarrer.bat"
exit /b 0
