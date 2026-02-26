@echo off
REM ============================================
REM Script: importar_tablas.bat
REM Importa las 13 tablas al servidor DESTINO
REM
REM SERVIDOR DESTINO: 10.1.99.4 (cristal)
REM ============================================

SET SERVIDOR=10.1.99.4
SET BD=cristal
SET USUARIO=sa
SET CLAVE=Crijob2015Desa
SET ORIGEN=%~dp0datos

echo.
echo ============================================
echo    IMPORTAR TABLAS - CONTROL DE SEGURIDAD
echo ============================================
echo.
echo    SERVIDOR DESTINO: %SERVIDOR%
echo    BASE DE DATOS:    %BD%
echo    USUARIO:          %USUARIO%
echo.
echo    Este script IMPORTA datos AL servidor destino.
echo    Los archivos se leeran de: %ORIGEN%
echo.
echo ============================================
echo.

REM Verificar que existen los archivos de datos
if not exist "%ORIGEN%\empresas.bcp" (
    echo ============================================
    echo ERROR: No se encontraron los archivos de datos.
    echo.
    echo Debes ejecutar primero: exportar_tablas.bat
    echo.
    echo Buscando en: %ORIGEN%
    echo ============================================
    pause
    exit /b 1
)
echo OK: Archivos de datos encontrados en %ORIGEN%
echo.

REM Verificar conectividad al servidor destino
echo Verificando conexion al servidor %SERVIDOR%...
sqlcmd -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -Q "SELECT 'OK' AS Estado" -h -1 > nul 2>&1
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

REM Verificar que NO es el servidor origen (proteccion)
sqlcmd -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -Q "SELECT SERVERPROPERTY('MachineName')" -h -1 2>nul | findstr /i "192.168.100" > nul
if %ERRORLEVEL% EQU 0 (
    echo ============================================
    echo ERROR: SERVIDOR INCORRECTO!
    echo.
    echo Este script debe ejecutarse contra 10.1.99.4
    echo Parece que estas conectado al servidor ORIGEN.
    echo ============================================
    pause
    exit /b 1
)

REM Confirmar antes de continuar
echo ============================================
echo CONFIRMAR IMPORTACION
echo ============================================
echo.
echo ATENCION: Vas a IMPORTAR datos a:
echo    Servidor: %SERVIDOR%
echo    BD: %BD%
echo.
echo Las tablas existentes seran REEMPLAZADAS.
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
echo IMPORTANDO TABLAS A %SERVIDOR%
echo ============================================
echo.

echo [1/13] Importando empresas...
bcp %BD%.dbo.empresas in "%ORIGEN%\empresas.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en empresas

echo [2/13] Importando unidades...
bcp %BD%.dbo.unidades in "%ORIGEN%\unidades.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en unidades

echo [3/13] Importando formatos...
bcp %BD%.dbo.formatos in "%ORIGEN%\formatos.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en formatos

echo [4/13] Importando calidades...
bcp %BD%.dbo.calidades in "%ORIGEN%\calidades.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en calidades

echo [5/13] Importando almmodelos...
bcp %BD%.dbo.almmodelos in "%ORIGEN%\almmodelos.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en almmodelos

echo [6/13] Importando almcolores...
bcp %BD%.dbo.almcolores in "%ORIGEN%\almcolores.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en almcolores

echo [7/13] Importando pallets...
bcp %BD%.dbo.pallets in "%ORIGEN%\pallets.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en pallets

echo [8/13] Importando articulos...
bcp %BD%.dbo.articulos in "%ORIGEN%\articulos.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en articulos

echo [9/13] Importando almlinubica...
bcp %BD%.dbo.almlinubica in "%ORIGEN%\almlinubica.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en almlinubica

echo [10/13] Importando venliped...
bcp %BD%.dbo.venliped in "%ORIGEN%\venliped.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en venliped

echo [11/13] Importando genter...
bcp %BD%.dbo.genter in "%ORIGEN%\genter.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en genter

echo [12/13] Importando ps_articulo_imagen...
bcp %BD%.dbo.ps_articulo_imagen in "%ORIGEN%\ps_articulo_imagen.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en ps_articulo_imagen

echo [13/13] Importando articulo_ficha_tecnica...
bcp %BD%.dbo.articulo_ficha_tecnica in "%ORIGEN%\articulo_ficha_tecnica.bcp" -S %SERVIDOR% -U %USUARIO% -P %CLAVE% -n -C 65001
if %ERRORLEVEL% NEQ 0 echo    ERROR en articulo_ficha_tecnica

echo.
echo ============================================
echo IMPORTACION COMPLETADA
echo ============================================
echo.
echo Verifica los datos ejecutando en SSMS:
echo    SELECT 'empresas', COUNT(*) FROM cristal.dbo.empresas
echo    UNION ALL
echo    SELECT 'articulos', COUNT(*) FROM cristal.dbo.articulos
echo    ... etc
echo.
pause
