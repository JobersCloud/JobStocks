@echo off
REM ============================================================
REM Script de despliegue para servidor UNDEFASA (62.15.189.138 (192.168.0.50))
REM Sube archivos y publica con canary: la imagen nueva se prueba
REM en un contenedor aparte ANTES de tocar el que esta sirviendo,
REM asi un fallo no deja la web caida.
REM ============================================================

echo ========================================
echo   Desplegando en servidor UNDEFASA
echo   IP: 62.15.189.138 (192.168.0.50)
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [0/3] Comprobando que el servidor responde...
ssh -o BatchMode=yes -o ConnectTimeout=10 undefasa@62.15.189.138 "true"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: el servidor no responde por SSH. No se ha subido nada.
    pause
    exit /b 1
)

echo [1/3] Subiendo archivos (sin docker-compose.yml ni videos)...
REM NO subir docker-compose.yml - UNDEFASA tiene su propia config con jobers-net
scp -r backend undefasa@62.15.189.138:/home/undefasa/apirest/
REM Subir frontend excluyendo videos (.mp4) via tar+ssh
tar cf - --exclude="*.mp4" frontend | ssh undefasa@62.15.189.138 "cd /home/undefasa/apirest && tar xf -"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir archivos
    pause
    exit /b 1
)

echo.
echo [2/3] Ajustando permisos...
ssh undefasa@62.15.189.138 "chmod -R 755 /home/undefasa/apirest/frontend"

echo.
echo [3/3] Publicando con canary...
scp deploy\publica_remoto.sh undefasa@62.15.189.138:/tmp/
ssh undefasa@62.15.189.138 "APP_DIR=/home/undefasa/apirest CONTAINER=apirest-backend bash /tmp/publica_remoto.sh"

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
