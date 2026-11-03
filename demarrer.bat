@echo off
title Institut Les Sages ILAS - Application de Gestion
cd /d "%~dp0"

echo ====================================================
echo     INSTITUT LES SAGES ILAS - SYSTEME DE GESTION
echo ====================================================
echo.

set P=

where python >nul 2>nul
if %errorlevel%==0 set P=python

if defined P goto deps

where py >nul 2>nul
if %errorlevel%==0 set P=py

if defined P goto deps

echo.
echo [ATTENTION] Python n'est pas encore installe sur ce PC.
echo.
echo Veillez installer Python (cochez "Add Python to PATH") :
echo https://www.python.org/downloads/
echo.
echo Une fois Python installe, double-cliquez a nouveau sur demarrer.bat
echo.
pause
exit /b 1

:deps
echo [1/3] Verification et installation automatique des bibliotheques...
%P% -m pip install -r requirements.txt --quiet

echo [2/3] Verification de la base de donnees...
%P% -c "from app import app, db, auto_migrate_db; app.app_context().push(); auto_migrate_db()" >nul 2>nul

echo [3/3] Demarrage du tunnel Cloudflare (En Ligne)...
start /b "" %P% start_remote_tunnel.py

echo.
echo ====================================================
echo    L'APPLICATION EST EN COURS DE FONCTIONNEMENT !
echo    ACCES LOCAL    : http://localhost:8080
echo    ACCES EN LIGNE : https://ilas.moropay.trade
echo ====================================================
echo.
echo    [CONSEIL] Ne fermez pas cette fenetre noire pendant
echo    que vous utilisez le systeme.
echo.

start "" "http://localhost:8080"
%P% app.py 8080

echo.
echo L'application s'est arretee.
pause
