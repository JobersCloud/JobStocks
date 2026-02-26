@echo off
REM ============================================================
REM Script para configurar HTTPS en servidor CRISTAL
REM Sube archivos y ejecuta instalacion
REM ============================================================

echo ========================================
echo   Configurando HTTPS en CRISTAL
echo   Dominio: prolife-area.cristalceramicas.com
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [1/3] Subiendo archivos de configuracion...
scp deploy/nginx-cristal.conf deploy/instalar-https-cristal.sh administrador@10.1.99.4:/var/jobstocks/deploy/

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir archivos
    pause
    exit /b 1
)

echo.
echo [2/3] Ejecutando instalacion de HTTPS...
echo       (Esto puede tardar 1-2 minutos)
ssh administrador@10.1.99.4 "chmod +x /var/jobstocks/deploy/instalar-https-cristal.sh && echo 'crijob15' | sudo -S /var/jobstocks/deploy/instalar-https-cristal.sh"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo en la instalacion
    pause
    exit /b 1
)

echo.
echo [3/3] Verificando HTTPS...
timeout /t 5 /nobreak > nul
curl -s https://prolife-area.cristalceramicas.com/api/version

echo.
echo ========================================
echo   HTTPS configurado!
echo   URL: https://prolife-area.cristalceramicas.com
echo ========================================
pause
