@echo off
REM ============================================================
REM Script de despliegue para servidor OVH (51.68.44.136)
REM Sube archivos y reinicia Docker (downtime minimo)
REM ============================================================

echo ========================================
echo   Desplegando en servidor OVH
echo   IP: 51.68.44.136
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [1/5] Subiendo archivos (sin videos promocionales)...
scp -r backend docker-compose.yml ubuntu@51.68.44.136:/opt/ApiRestExternos/
REM Subir frontend excluyendo videos (.mp4) via tar+ssh
tar cf - --exclude="*.mp4" frontend | ssh ubuntu@51.68.44.136 "cd /opt/ApiRestExternos && tar xf -"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir archivos
    pause
    exit /b 1
)

echo.
echo [2/5] Ajustando permisos...
ssh ubuntu@51.68.44.136 "sudo chmod -R 755 /opt/ApiRestExternos/frontend"

echo.
echo [3/5] Construyendo nueva imagen (app sigue funcionando)...
ssh ubuntu@51.68.44.136 "cd /opt/ApiRestExternos && sudo docker compose build"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al construir imagen
    pause
    exit /b 1
)

echo.
echo [4/5] Reiniciando contenedores (downtime minimo)...
ssh ubuntu@51.68.44.136 "cd /opt/ApiRestExternos && sudo docker compose down --remove-orphans && sudo docker compose up -d"

echo.
echo [5/5] Verificando version...
timeout /t 8 /nobreak > nul
ssh ubuntu@51.68.44.136 "curl -s http://localhost:5000/api/version"

echo.
echo ========================================
echo   Despliegue completado!
echo ========================================
pause
