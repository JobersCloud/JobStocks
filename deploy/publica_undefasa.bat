@echo off
REM ============================================================
REM Script de despliegue para servidor UNDEFASA (62.15.189.138)
REM Sube archivos y reinicia Docker (downtime minimo)
REM ============================================================

echo ========================================
echo   Desplegando en servidor UNDEFASA
echo   IP: 62.15.189.138 (192.168.0.50)
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [1/5] Subiendo archivos (sin .env ni videos promocionales)...
scp docker-compose.yml undefasa@62.15.189.138:/home/undefasa/apirest/
scp -r backend undefasa@62.15.189.138:/home/undefasa/apirest/
REM Subir frontend excluyendo videos (.mp4) via tar+ssh
tar cf - --exclude="*.mp4" frontend | ssh undefasa@62.15.189.138 "cd /home/undefasa/apirest && tar xf -"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir archivos
    pause
    exit /b 1
)

echo.
echo [2/5] Ajustando permisos...
ssh undefasa@62.15.189.138 "chmod -R 755 /home/undefasa/apirest/frontend"

echo.
echo [3/5] Construyendo nueva imagen (app sigue funcionando)...
ssh undefasa@62.15.189.138 "cd /home/undefasa/apirest && docker compose build"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al construir imagen
    pause
    exit /b 1
)

echo.
echo [4/5] Reiniciando contenedores (downtime minimo)...
ssh undefasa@62.15.189.138 "cd /home/undefasa/apirest && docker compose down && docker compose up -d"

echo.
echo [5/5] Verificando version...
timeout /t 8 /nobreak > nul
ssh undefasa@62.15.189.138 "curl -s http://localhost:5000/api/version"

echo.
echo ========================================
echo   Despliegue completado!
echo ========================================
pause
