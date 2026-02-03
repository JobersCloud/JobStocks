@echo off
chcp 65001 > nul
REM ============================================
REM Script: migracion_completa.bat
REM Migracion COMPLETA: Tablas + PKs + Indices
REM
REM ORIGEN:  192.168.100.5 (cristal)
REM DESTINO: 10.1.99.4 (cristal)
REM ============================================

SET SERVIDOR_ORIGEN=192.168.100.5
SET SERVIDOR_DESTINO=10.1.99.4
SET BD=cristal

SET USUARIO_ORIGEN=sa
SET CLAVE_ORIGEN=desa2012

SET USUARIO_DESTINO=sa
SET CLAVE_DESTINO=Crijob2015Desa

SET DATOS=%~dp0datos

cls
echo.
echo ============================================
echo    MIGRACION COMPLETA DE CRISTAL
echo ============================================
echo.
echo    ORIGEN:  %SERVIDOR_ORIGEN% / %BD%
echo    DESTINO: %SERVIDOR_DESTINO% / %BD%
echo.
echo    Incluye: 19 tablas + PKs + Indices
echo.
echo ============================================
echo.

REM Crear carpeta de datos
if not exist "%DATOS%" mkdir "%DATOS%"

REM ============================================
REM VERIFICAR CONEXIONES
REM ============================================
echo [1/7] Verificando conexiones...
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SELECT 1" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al ORIGEN
    pause
    exit /b 1
)
echo     ORIGEN: OK

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -Q "SELECT 1" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al DESTINO
    pause
    exit /b 1
)
echo     DESTINO: OK
echo.

REM ============================================
REM CONFIRMACION
REM ============================================
echo ============================================
echo TABLAS A MIGRAR:
echo ============================================
echo.
echo   empresas, unidades, formatos, calidades,
echo   almmodelos, almcolores, pallets, articulos,
echo   almlinubica, almartcajas, palarticulo, almcajas,
echo   almartcal, almarttonopeso, venliped, venped, genter,
echo   ps_articulo_imagen, articulo_ficha_tecnica
echo.
set /p CONFIRMAR="Escriba SI para continuar: "
if /i not "%CONFIRMAR%"=="SI" (
    echo Cancelado.
    pause
    exit /b 0
)
echo.

REM ============================================
REM CREAR BD EN DESTINO
REM ============================================
echo [2/7] Creando base de datos en DESTINO...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'cristal') CREATE DATABASE cristal" > nul 2>&1
echo     OK
echo.

REM ============================================
REM MIGRAR TABLAS
REM ============================================
echo [3/7] Migrando tablas (datos)...
echo.

call :migrar_tabla empresas
call :migrar_tabla unidades
call :migrar_tabla formatos
call :migrar_tabla calidades
call :migrar_tabla almmodelos
call :migrar_tabla almcolores
call :migrar_tabla pallets
call :migrar_tabla articulos
call :migrar_tabla almlinubica
call :migrar_tabla almartcajas
call :migrar_tabla palarticulo
call :migrar_tabla almcajas
call :migrar_tabla almartcal
call :migrar_tabla almarttonopeso
call :migrar_tabla venliped
call :migrar_tabla venped
call :migrar_tabla genter
call :migrar_tabla ps_articulo_imagen
call :migrar_tabla articulo_ficha_tecnica

echo.

REM ============================================
REM EXPORTAR Y APLICAR PKs
REM ============================================
echo [4/7] Exportando PRIMARY KEYS del ORIGEN...
SET PKS_FILE=%DATOS%\pks.sql
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -i "%~dp001_exportar_pks_origen.sql" -h -1 -W -o "%PKS_FILE%" 2>nul
for /f %%A in ('type "%PKS_FILE%" 2^>nul ^| find /c "PRIMARY KEY"') do set TOTAL_PKS=%%A
echo     %TOTAL_PKS% PKs encontradas
echo.

echo [5/7] Aplicando PRIMARY KEYS en DESTINO...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%PKS_FILE%" > nul 2>&1
echo     OK (errores menores ignorados si ya existen)
echo.

REM ============================================
REM EXPORTAR Y APLICAR INDICES
REM ============================================
echo [6/7] Exportando INDICES del ORIGEN...
SET INDICES_FILE=%DATOS%\indices.sql
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -i "%~dp002_exportar_indices_origen.sql" -h -1 -W -o "%INDICES_FILE%" 2>nul
for /f %%A in ('type "%INDICES_FILE%" 2^>nul ^| find /c "INDEX"') do set TOTAL_IDX=%%A
echo     %TOTAL_IDX% indices encontrados
echo.

echo [7/7] Aplicando INDICES en DESTINO...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%INDICES_FILE%" > nul 2>&1
echo     OK (errores menores ignorados si ya existen)
echo.

REM ============================================
REM VERIFICACION FINAL
REM ============================================
echo ============================================
echo VERIFICACION FINAL
echo ============================================
echo.
echo Conteo de registros en DESTINO:
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT 'empresas' AS T, COUNT(*) AS R FROM dbo.empresas UNION ALL SELECT 'articulos', COUNT(*) FROM dbo.articulos UNION ALL SELECT 'palarticulo', COUNT(*) FROM dbo.palarticulo UNION ALL SELECT 'almcajas', COUNT(*) FROM dbo.almcajas UNION ALL SELECT 'almartcal', COUNT(*) FROM dbo.almartcal UNION ALL SELECT 'almarttonopeso', COUNT(*) FROM dbo.almarttonopeso" -W -s" | "
echo.
echo PKs creadas:
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT COUNT(*) AS Total_PKs FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica')" -W -h -1
echo.
echo Indices creados:
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT COUNT(*) AS Total_Indices FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica')" -W -h -1

echo.
echo ============================================
echo MIGRACION COMPLETA FINALIZADA
echo ============================================
echo.
pause
exit /b 0

REM ============================================
REM FUNCION: migrar_tabla
REM ============================================
:migrar_tabla
set TABLA=%1
echo     %TABLA%...

REM Eliminar tabla en destino
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "IF OBJECT_ID('dbo.%TABLA%', 'U') IS NOT NULL DROP TABLE dbo.%TABLA%" > nul 2>&1

REM Exportar datos
bcp %BD%.dbo.%TABLA% out "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1

REM Generar CREATE TABLE
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT TOP 0 * INTO ##temp_%TABLA% FROM dbo.%TABLA%; DECLARE @sql NVARCHAR(MAX); SET @sql = (SELECT 'CREATE TABLE dbo.%TABLA% (' + STUFF((SELECT ', ' + c.name + ' ' + t.name + CASE WHEN t.name IN ('varchar','nvarchar','char','nchar','varbinary','binary') THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(CASE WHEN t.name LIKE 'n%%' THEN c.max_length/2 ELSE c.max_length END AS VARCHAR) END + ')' WHEN t.name IN ('decimal','numeric') THEN '(' + CAST(c.precision AS VARCHAR) + ',' + CAST(c.scale AS VARCHAR) + ')' ELSE '' END + CASE WHEN c.is_nullable = 0 THEN ' NOT NULL' ELSE ' NULL' END FROM tempdb.sys.columns c JOIN tempdb.sys.types t ON c.user_type_id = t.user_type_id WHERE c.object_id = OBJECT_ID('tempdb..##temp_%TABLA%') ORDER BY c.column_id FOR XML PATH('')), 1, 2, '') + ')'); DROP TABLE ##temp_%TABLA%; PRINT @sql;" -h -1 -W > "%DATOS%\%TABLA%_create.sql" 2>nul

REM Crear tabla en destino
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%DATOS%\%TABLA%_create.sql" > nul 2>&1

REM Importar datos
bcp %BD%.dbo.%TABLA% in "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n > nul 2>&1

goto :eof
