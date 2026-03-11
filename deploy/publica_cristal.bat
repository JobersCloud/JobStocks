@echo off
REM ============================================================
REM Script de despliegue para servidor CRISTAL (10.1.99.4)
REM Sube archivos y reinicia Docker (downtime minimo)
REM ============================================================

echo ========================================
echo   Desplegando en servidor CRISTAL
echo   IP: 10.1.99.4
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [1/5] Subiendo archivos (sin .env ni videos promocionales)...
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
echo [2/5] Ajustando permisos...
ssh administrador@10.1.99.4 "chmod -R 755 /var/jobstocks/frontend"

echo.
echo [3/5] Construyendo nueva imagen (app sigue funcionando)...
ssh administrador@10.1.99.4 "cd /var/jobstocks && echo 'crijob15' | sudo -S docker-compose build"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al construir imagen
    pause
    exit /b 1
)

echo.
echo [4/5] Reiniciando contenedores (downtime minimo)...
ssh administrador@10.1.99.4 "cd /var/jobstocks && echo 'crijob15' | sudo -S docker-compose down && echo 'crijob15' | sudo -S docker-compose up -d"

echo.
echo [5/5] Verificando version...
timeout /t 8 /nobreak > nul
ssh administrador@10.1.99.4 "curl -s http://localhost:5000/api/version"

echo.
echo ========================================
echo   Despliegue completado!
echo ========================================
pause
