@echo off
REM ============================================
REM Script: exportar_tablas.bat
REM Exporta las 14 tablas desde servidor ORIGEN
REM
REM SERVIDOR ORIGEN: 192.168.100.5 (cristal)
REM ============================================

SET SERVIDOR=192.168.100.5
SET BD=cristal
SET USUARIO=sa
SET CLAVE=desa2012
SET DESTINO=%~dp0datos

echo.
echo ============================================
echo    EXPORTAR TABLAS - CONTROL DE SEGURIDAD
echo ============================================
echo.
echo    SERVIDOR ORIGEN: %SERVIDOR%
echo    BASE DE DATOS:   %BD%
echo    USUARIO:         %USUARIO%
echo.
echo    Este script EXPORTA datos DESDE el servidor origen.
echo    Los archivos se guardaran en: %DESTINO%
echo.
echo ============================================
echo.

REM Verificar conectividad al servidor correcto
echo Verificando conexion al servidor %SERVIDOR%...
sqlcmd -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -d %BD% -Q "SELECT 'OK' AS Estado" -h -1 > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================
    echo ERROR: No se puede conectar a %SERVIDOR%
    echo Verifica que el servidor este disponible
    echo y las credenciales sean correctas.
    echo ============================================
    pause
    exit /b 1
)
echo OK: Conexion verificada a %SERVIDOR%
echo.

REM Confirmar antes de continuar
echo ============================================
echo CONFIRMAR EXPORTACION
echo ============================================
echo.
echo Vas a EXPORTAR las 14 tablas desde:
echo    Servidor: %SERVIDOR%
echo    BD: %BD%
echo.
set /p CONFIRMAR="Escriba SI para continuar: "
if /i not "%CONFIRMAR%"=="SI" (
    echo.
    echo Operacion cancelada por el usuario.
    pause
    exit /b 0
)

echo.
echo ============================================
echo EXPORTANDO TABLAS DESDE %SERVIDOR%
echo ============================================
echo.

REM Crear carpeta de datos si no existe
if not exist "%DESTINO%" mkdir "%DESTINO%"

echo [1/14] Exportando empresas...
bcp %BD%.dbo.empresas out "%DESTINO%\empresas.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en empresas

echo [2/14] Exportando unidades...
bcp %BD%.dbo.unidades out "%DESTINO%\unidades.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en unidades

echo [3/14] Exportando formatos...
bcp %BD%.dbo.formatos out "%DESTINO%\formatos.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en formatos

echo [4/14] Exportando calidades...
bcp %BD%.dbo.calidades out "%DESTINO%\calidades.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en calidades

echo [5/14] Exportando almmodelos...
bcp %BD%.dbo.almmodelos out "%DESTINO%\almmodelos.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en almmodelos

echo [6/14] Exportando almcolores...
bcp %BD%.dbo.almcolores out "%DESTINO%\almcolores.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en almcolores

echo [7/14] Exportando pallets...
bcp %BD%.dbo.pallets out "%DESTINO%\pallets.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en pallets

echo [8/14] Exportando articulos...
bcp %BD%.dbo.articulos out "%DESTINO%\articulos.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en articulos

echo [9/14] Exportando almlinubica...
bcp %BD%.dbo.almlinubica out "%DESTINO%\almlinubica.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en almlinubica

echo [10/14] Exportando almartcajas...
bcp %BD%.dbo.almartcajas out "%DESTINO%\almartcajas.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en almartcajas

echo [11/14] Exportando venliped...
bcp %BD%.dbo.venliped out "%DESTINO%\venliped.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en venliped

echo [12/14] Exportando genter...
bcp %BD%.dbo.genter out "%DESTINO%\genter.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en genter

echo [13/14] Exportando ps_articulo_imagen...
bcp %BD%.dbo.ps_articulo_imagen out "%DESTINO%\ps_articulo_imagen.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en ps_articulo_imagen

echo [14/14] Exportando articulo_ficha_tecnica...
bcp %BD%.dbo.articulo_ficha_tecnica out "%DESTINO%\articulo_ficha_tecnica.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en articulo_ficha_tecnica

echo.
echo ============================================
echo EXPORTACION COMPLETADA
echo Archivos guardados en: %DESTINO%
echo ============================================
echo.
echo Archivos generados:
dir "%DESTINO%\*.bcp" /b
echo.
echo Siguiente paso: Ejecutar importar_tablas.bat
echo.
pause
