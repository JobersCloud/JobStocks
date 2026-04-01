@echo off
REM ============================================================
REM Script para configurar HTTPS en servidor OVH para UNDEFASA
REM Sube archivos y ejecuta instalacion
REM ============================================================

echo ========================================
echo   Configurando HTTPS en OVH
echo   Dominio: stocks.undefasa.com
echo ========================================
echo.

cd /d "C:\Users\jobers\Documents\Ejercicios Python\JobStocks"

echo [1/3] Subiendo archivos de configuracion...
scp deploy/nginx-undefasa.conf deploy/instalar-https-undefasa.sh ubuntu@51.68.44.136:/opt/ApiRestExternos/deploy/

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir archivos
    pause
    exit /b 1
)

echo.
echo [2/3] Ejecutando instalacion de HTTPS...
echo       (Esto puede tardar 1-2 minutos)
ssh ubuntu@51.68.44.136 "chmod +x /opt/ApiRestExternos/deploy/instalar-https-undefasa.sh && sudo /opt/ApiRestExternos/deploy/instalar-https-undefasa.sh"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo en la instalacion
    pause
    exit /b 1
)

echo.
echo [3/3] Verificando HTTPS...
timeout /t 5 /nobreak > nul
curl -s https://stocks.undefasa.com/api/version

echo.
echo ========================================
echo   HTTPS configurado!
echo   URL: https://stocks.undefasa.com
echo ========================================
pause
