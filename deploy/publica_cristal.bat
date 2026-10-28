@echo off
REM ============================================================
REM Script de despliegue para servidor CRISTAL (10.1.99.4)
REM Sube archivos y publica con canary: la imagen nueva se prueba
REM en un contenedor aparte ANTES de tocar el que esta sirviendo,
REM asi un fallo no deja la web caida.
REM ============================================================

echo ========================================
echo   Desplegando en servidor CRISTAL
echo   IP: 10.1.99.4
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [0/3] Comprobando que el servidor responde...
ssh -o BatchMode=yes -o ConnectTimeout=10 administrador@10.1.99.4 "true"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: el servidor no responde por SSH. No se ha subido nada.
    pause
    exit /b 1
)

echo [1/3] Subiendo archivos (sin .env ni videos promocionales)...
REM Backup del .env del servidor
ssh administrador@10.1.99.4 "cp /var/jobstocks/backend/.env /tmp/.env.backup 2>/dev/null || true"
scp docker-compose.yml administrador@10.1.99.4:/var/jobstocks/
scp -r backend administrador@10.1.99.4:/var/jobstocks/
ssh administrador@10.1.99.4 "cp /tmp/.env.backup /var/jobstocks/backend/.env 2>/dev/null || true"
REM Subir frontend excluyendo videos (.mp4) via tar+ssh
tar cf - --exclude="*.mp4" frontend | ssh administrador@10.1.99.4 "cd /var/jobstocks && tar xf -"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir archivos
    pause
    exit /b 1
)

echo.
echo [2/3] Ajustando permisos...
ssh administrador@10.1.99.4 "chmod -R 755 /var/jobstocks/frontend"

echo.
echo [3/3] Publicando con canary...
scp deploy\publica_remoto.sh administrador@10.1.99.4:/tmp/
ssh administrador@10.1.99.4 "APP_DIR=/var/jobstocks CONTAINER=apirest-backend SUDO_PASS='crijob15' bash /tmp/publica_remoto.sh"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo   DESPLIEGUE ABORTADO
    echo   Sigue en marcha la version anterior
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Despliegue completado!
echo ========================================
pause
