@echo off
REM ============================================================
REM Script de despliegue para servidor OVH (51.68.44.136)
REM Sube archivos y reinicia Docker
REM ============================================================

echo ========================================
echo   Desplegando en servidor OVH
echo   IP: 51.68.44.136
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [1/4] Subiendo archivos...
scp -r backend frontend docker-compose.yml ubuntu@51.68.44.136:/opt/ApiRestExternos/

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir archivos
    pause
    exit /b 1
)

echo.
echo [2/4] Ajustando permisos...
ssh ubuntu@51.68.44.136 "sudo chmod -R 755 /opt/ApiRestExternos/frontend"

echo.
echo [3/4] Reiniciando Docker...
ssh ubuntu@51.68.44.136 "cd /opt/ApiRestExternos && sudo docker compose down && sudo docker compose up -d --build"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al reiniciar Docker
    pause
    exit /b 1
)

echo.
echo [4/4] Verificando version...
timeout /t 5 /nobreak > nul
ssh ubuntu@51.68.44.136 "curl -s http://localhost:5000/api/version"

echo.
echo ========================================
echo   Despliegue completado!
echo ========================================
pause
