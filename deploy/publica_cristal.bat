@echo off
REM ============================================================
REM Script de despliegue para servidor CRISTAL (10.1.99.4)
REM Sube archivos y reinicia Docker
REM ============================================================

echo ========================================
echo   Desplegando en servidor CRISTAL
echo   IP: 10.1.99.4
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [1/4] Subiendo archivos (sin .env - cada servidor tiene su config)...
REM Excluir .env del backend para no sobrescribir configuracion del servidor
ssh administrador@10.1.99.4 "cp /var/jobstocks/backend/.env /tmp/.env.backup 2>/dev/null || true"
scp -r backend frontend docker-compose.yml administrador@10.1.99.4:/var/jobstocks/
ssh administrador@10.1.99.4 "cp /tmp/.env.backup /var/jobstocks/backend/.env 2>/dev/null || true"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir archivos
    pause
    exit /b 1
)

echo.
echo [2/4] Ajustando permisos...
ssh administrador@10.1.99.4 "chmod -R 755 /var/jobstocks/frontend"

echo.
echo [3/4] Reiniciando Docker...
ssh administrador@10.1.99.4 "cd /var/jobstocks && echo 'crijob15' | sudo -S docker-compose down && echo 'crijob15' | sudo -S docker-compose up -d --build"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al reiniciar Docker
    pause
    exit /b 1
)

echo.
echo [4/4] Verificando version...
timeout /t 10 /nobreak > nul
ssh administrador@10.1.99.4 "curl -s http://localhost:5000/api/version"

echo.
echo ========================================
echo   Despliegue completado!
echo ========================================
pause
