@echo off
REM ============================================================
REM Script de despliegue para servidor OVH (51.68.44.136)
REM Sube archivos y publica con canary: la imagen nueva se prueba
REM en un contenedor aparte ANTES de tocar el que esta sirviendo,
REM asi un fallo no deja la web caida.
REM ============================================================

echo ========================================
echo   Desplegando en servidor OVH
echo   IP: 51.68.44.136
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [0/3] Comprobando que el servidor responde...
ssh -o BatchMode=yes -o ConnectTimeout=10 ubuntu@51.68.44.136 "true"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: el servidor no responde por SSH. No se ha subido nada.
    pause
    exit /b 1
)

echo [1/3] Subiendo archivos (sin videos promocionales)...
scp -r backend docker-compose.yml ubuntu@51.68.44.136:/opt/ApiRestExternos/
REM Subir frontend excluyendo videos (.mp4) via tar+ssh
tar cf - --exclude="*.mp4" frontend | ssh ubuntu@51.68.44.136 "cd /opt/ApiRestExternos && tar xf -"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir archivos
    pause
    exit /b 1
)

echo.
echo [2/3] Ajustando permisos...
ssh ubuntu@51.68.44.136 "sudo chmod -R 755 /opt/ApiRestExternos/frontend"

echo.
echo [3/3] Publicando con canary...
scp deploy\publica_remoto.sh ubuntu@51.68.44.136:/tmp/
ssh ubuntu@51.68.44.136 "APP_DIR=/opt/ApiRestExternos CONTAINER=apirest-backend USE_SUDO=1 bash /tmp/publica_remoto.sh"

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
