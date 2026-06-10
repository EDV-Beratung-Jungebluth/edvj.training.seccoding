@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  CRM-Demo starten
echo ============================================

REM --- Keycloak (Docker) starten ---
echo [1/3] Starte Keycloak per Docker Compose...
docker compose up -d
if errorlevel 1 (
    echo FEHLER: Docker Compose konnte nicht gestartet werden.
    echo Ist Docker Desktop aktiv?
    pause
    exit /b 1
)

REM --- Warten bis Keycloak bereit ist ---
echo [2/3] Warte auf Keycloak (http://localhost:8080)...
:warte
timeout /t 3 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://localhost:8080/realms/demo | findstr /c:"200" >nul 2>&1
if errorlevel 1 goto warte
echo        Keycloak ist bereit.

REM --- Django-Server starten ---
echo [3/3] Starte Django auf http://localhost:8125 ...
echo.
echo  Demo-Benutzer:  reader / reader123   (nur Lesen)
echo                  writer / writer123   (Lesen und Schreiben)
echo.
echo  Zum Beenden: Strg+C
echo ============================================
call .venv\Scripts\activate.bat
python manage.py runserver 8125
