@echo off
title INSTITUT ILAS - TEST ET VERIFICATION BASE DE DONNEES
cd /d "%~dp0"

echo ====================================================
echo   VERIFICATION DE LA BASE DE DONNEES INSTITUT ILAS
echo ====================================================
echo.

set P=
where python >nul 2>nul
if %errorlevel%==0 set P=python
if not defined P (
    where py >nul 2>nul
    if %errorlevel%==0 set P=py
)

if not defined P (
    echo Python n'est pas trouve.
    pause
    exit /b 1
)

%P% CHECK_MY_DATABASE.py
echo.
pause
