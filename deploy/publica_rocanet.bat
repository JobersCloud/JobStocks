@echo off
REM ============================================================
REM Script de despliegue para servidor ROCANET (Baldocer)
REM   SSH: 2.139.245.207 puerto 20122 (solo desde IPs Jobers)
REM   App: /home/rocanet/apirest
REM
REM Sube archivos y publica con canary: la imagen nueva se prueba
REM en un contenedor aparte ANTES de tocar el que esta sirviendo,
REM asi un fallo no deja la web caida.
REM
REM Particularidades de este servidor:
REM  - NO se sube docker-compose.yml (tiene config propia: jobers-net,
REM    FLASK_ENV=development, volumen del frontend, DEFAULT_CONNECTION)
REM  - El frontend va montado como volumen de solo lectura, asi que los
REM    cambios de HTML/JS/CSS entran al instante, sin reconstruir
REM  - sudo es sin contrasena (USE_SUDO=1)
REM  - Su red corta conexiones salientes a ratos: si el build falla en la
REM    capa del ODBC o de pip, repetirlo antes de buscar explicaciones
REM ============================================================

set RNHOST=israel.aucejo.jobers@2.139.245.207
set RNPORT=20122
set RNDIR=/home/rocanet/apirest

echo ========================================
echo   Desplegando en servidor ROCANET
echo   2.139.245.207:20122  (Baldocer)
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [0/4] Comprobando que el servidor responde...
ssh -o BatchMode=yes -o ConnectTimeout=15 -p %RNPORT% %RNHOST% "true"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: el servidor no responde por SSH. No se ha subido nada.
    echo Ojo: en esta cuenta caduca la contrasena UNIX por politica de
    echo Baldocer. Si sale "Your password has expired", hay que entrar con
    echo TTY: ssh -t -p %RNPORT% %RNHOST%
    pause
    exit /b 1
)

echo.
echo [1/4] Copia de seguridad del frontend que hay ahora...
ssh -p %RNPORT% %RNHOST% "cd %RNDIR% && tar czf /tmp/frontend-backup-$(date +%%Y%%m%%d-%%H%%M).tgz frontend && ls -la /tmp/frontend-backup-*.tgz | tail -3"

echo.
echo [2/4] Subiendo archivos (sin docker-compose.yml ni videos)...
REM Backup del .env del servidor: lleva su configuracion, no la nuestra
ssh -p %RNPORT% %RNHOST% "cp %RNDIR%/backend/.env /tmp/.env.backup 2>/dev/null || true"
scp -P %RNPORT% -r backend %RNHOST%:%RNDIR%/
ssh -p %RNPORT% %RNHOST% "cp /tmp/.env.backup %RNDIR%/backend/.env 2>/dev/null || true"
REM Frontend por tar+ssh, excluyendo videos promocionales
tar cf - --exclude="*.mp4" frontend | ssh -p %RNPORT% %RNHOST% "cd %RNDIR% && tar xf -"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir archivos
    pause
    exit /b 1
)

echo.
echo [3/4] Ajustando permisos...
ssh -p %RNPORT% %RNHOST% "chmod -R 755 %RNDIR%/frontend"

echo.
echo [4/4] Publicando con canary...
scp -P %RNPORT% deploy\publica_remoto.sh %RNHOST%:/tmp/
ssh -p %RNPORT% %RNHOST% "APP_DIR=%RNDIR% CONTAINER=apirest-backend USE_SUDO=1 SOLO_CANARY=%SOLO_CANARY% bash /tmp/publica_remoto.sh"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo   DESPLIEGUE ABORTADO
    echo   Sigue en marcha la version anterior
    echo   Frontend anterior en /tmp/frontend-backup-*.tgz
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Despliegue completado!
echo ========================================
pause
