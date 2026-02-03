@echo off
chcp 65001 > nul
REM ============================================
REM Script: cargar_jobstocks.bat
REM Copia las 19 tablas de cristal entre servidores
REM INCLUYE: Datos + Primary Keys + Indices
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
SET SCRIPTS=%~dp0

cls
echo.
echo ============================================
echo    CARGAR JOBSTOCKS - MIGRACION COMPLETA
echo ============================================
echo.
echo    ORIGEN:  %SERVIDOR_ORIGEN% / %BD%
echo    DESTINO: %SERVIDOR_DESTINO% / %BD%
echo.
echo    Incluye: Datos + PKs + Indices
echo.
echo ============================================
echo.

REM ============================================
REM VERIFICAR CONEXIONES
REM ============================================
echo [1/8] Verificando conexion al ORIGEN (%SERVIDOR_ORIGEN%)...
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SELECT 'OK'" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al ORIGEN
    echo     Servidor: %SERVIDOR_ORIGEN%
    echo     Usuario: %USUARIO_ORIGEN%
    pause
    exit /b 1
)
echo     OK
echo.

echo [2/8] Verificando conexion al DESTINO (%SERVIDOR_DESTINO%)...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -Q "SELECT 'OK'" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al DESTINO
    echo     Servidor: %SERVIDOR_DESTINO%
    echo     Usuario: %USUARIO_DESTINO%
    pause
    exit /b 1
)
echo     OK
echo.

REM ============================================
REM CONFIRMACION
REM ============================================
echo ============================================
echo TABLAS A MIGRAR (19 tablas):
echo ============================================
echo.
echo   empresas, unidades, formatos, calidades,
echo   almmodelos, almcolores, pallets, articulos,
echo   almlinubica, almartcajas, palarticulo, almcajas,
echo   almartcal, almarttonopeso, venliped, venped, genter,
echo   ps_articulo_imagen, articulo_ficha_tecnica
echo.
echo DESDE: %SERVIDOR_ORIGEN%
echo HACIA: %SERVIDOR_DESTINO%
echo.
echo Se copiaran: DATOS + PRIMARY KEYS + INDICES
echo.
set /p CONFIRMAR="Escriba SI para continuar: "
if /i not "%CONFIRMAR%"=="SI" (
    echo Cancelado.
    pause
    exit /b 0
)
echo.

REM Crear carpeta de datos
if not exist "%DATOS%" mkdir "%DATOS%"

REM ============================================
REM CREAR BD CRISTAL EN DESTINO
REM ============================================
echo [3/8] Creando base de datos cristal en DESTINO...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'cristal') CREATE DATABASE cristal" > nul 2>&1
echo     OK
echo.

REM ============================================
REM EXPORTAR E IMPORTAR CADA TABLA
REM ============================================
echo [4/8] Migrando tablas (datos)...
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
echo ============================================
echo [5/8] EXPORTANDO PRIMARY KEYS del ORIGEN
echo ============================================
echo.
SET PKS_FILE=%DATOS%\primary_keys.sql

REM Usar archivo SQL externo si existe, sino query inline
if exist "%SCRIPTS%01_exportar_pks_origen.sql" (
    sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -i "%SCRIPTS%01_exportar_pks_origen.sql" -h -1 -W -o "%PKS_FILE%" 2>nul
) else (
    sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT 'IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = ''' + i.name + ''' AND object_id = OBJECT_ID(''dbo.' + t.name + ''')) ALTER TABLE [dbo].[' + t.name + '] ADD CONSTRAINT [' + i.name + '] PRIMARY KEY ' + CASE WHEN i.type = 1 THEN 'CLUSTERED' ELSE 'NONCLUSTERED' END + ' (' + STUFF((SELECT ', [' + c.name + ']' FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') + ');' FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name" -h -1 -W -o "%PKS_FILE%" 2>nul
)

for /f %%A in ('type "%PKS_FILE%" 2^>nul ^| find /c "PRIMARY KEY"') do set TOTAL_PKS=%%A
echo     %TOTAL_PKS% PRIMARY KEYS encontradas

echo.
echo ============================================
echo [6/8] APLICANDO PRIMARY KEYS en DESTINO
echo ============================================
echo.
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%PKS_FILE%" 2>nul
echo     PKs aplicadas (errores menores ignorados si ya existen)

echo.
echo ============================================
echo [7/8] EXPORTANDO Y APLICANDO INDICES
echo ============================================
echo.
SET INDICES_FILE=%DATOS%\indices.sql

REM Usar archivo SQL externo si existe, sino query inline
if exist "%SCRIPTS%02_exportar_indices_origen.sql" (
    sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -i "%SCRIPTS%02_exportar_indices_origen.sql" -h -1 -W -o "%INDICES_FILE%" 2>nul
) else (
    sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT 'IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = ''' + i.name + ''' AND object_id = OBJECT_ID(''dbo.' + t.name + ''')) CREATE ' + CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END + CASE WHEN i.type = 1 THEN 'CLUSTERED ' ELSE 'NONCLUSTERED ' END + 'INDEX [' + i.name + '] ON [dbo].[' + t.name + '] (' + STUFF((SELECT ', [' + c.name + ']' + CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE '' END FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0 ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') + ');' FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name, i.name" -h -1 -W -o "%INDICES_FILE%" 2>nul
)

for /f %%A in ('type "%INDICES_FILE%" 2^>nul ^| find /c "INDEX"') do set TOTAL_IDX=%%A
echo     %TOTAL_IDX% INDICES encontrados

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%INDICES_FILE%" 2>nul
echo     Indices aplicados (errores menores ignorados si ya existen)

echo.
echo ============================================
echo [8/8] VERIFICACION FINAL
echo ============================================
echo.
echo --- CONTEO DE REGISTROS ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT 'empresas', COUNT(*) FROM dbo.empresas UNION ALL SELECT 'unidades', COUNT(*) FROM dbo.unidades UNION ALL SELECT 'formatos', COUNT(*) FROM dbo.formatos UNION ALL SELECT 'calidades', COUNT(*) FROM dbo.calidades UNION ALL SELECT 'almmodelos', COUNT(*) FROM dbo.almmodelos UNION ALL SELECT 'almcolores', COUNT(*) FROM dbo.almcolores UNION ALL SELECT 'pallets', COUNT(*) FROM dbo.pallets UNION ALL SELECT 'articulos', COUNT(*) FROM dbo.articulos UNION ALL SELECT 'almlinubica', COUNT(*) FROM dbo.almlinubica UNION ALL SELECT 'almartcajas', COUNT(*) FROM dbo.almartcajas UNION ALL SELECT 'palarticulo', COUNT(*) FROM dbo.palarticulo UNION ALL SELECT 'almcajas', COUNT(*) FROM dbo.almcajas UNION ALL SELECT 'almartcal', COUNT(*) FROM dbo.almartcal UNION ALL SELECT 'almarttonopeso', COUNT(*) FROM dbo.almarttonopeso UNION ALL SELECT 'venliped', COUNT(*) FROM dbo.venliped UNION ALL SELECT 'venped', COUNT(*) FROM dbo.venped UNION ALL SELECT 'genter', COUNT(*) FROM dbo.genter UNION ALL SELECT 'ps_articulo_imagen', COUNT(*) FROM dbo.ps_articulo_imagen UNION ALL SELECT 'articulo_ficha', COUNT(*) FROM dbo.articulo_ficha_tecnica" -W -s" | "

echo.
echo --- PRIMARY KEYS CREADAS ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT t.name AS Tabla, i.name AS PK FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name" -W -s" | "

echo.
echo --- INDICES CREADOS ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT COUNT(*) AS Total_Indices FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica')" -W -h -1

echo.
echo ============================================
echo MIGRACION COMPLETADA EXITOSAMENTE
echo ============================================
echo.
echo Archivos generados en: %DATOS%
echo   - primary_keys.sql
echo   - indices.sql
echo   - [tabla]_create.sql (por cada tabla)
echo   - [tabla].bcp (datos binarios)
echo.
pause
exit /b 0

REM ============================================
REM FUNCION: migrar_tabla
REM ============================================
:migrar_tabla
set TABLA=%1
echo     %TABLA%...

REM Paso A: Eliminar tabla en destino si existe
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "IF OBJECT_ID('dbo.%TABLA%', 'U') IS NOT NULL DROP TABLE dbo.%TABLA%" > nul 2>&1

REM Paso B: Exportar datos + formato desde origen
bcp %BD%.dbo.%TABLA% format nul -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n -f "%DATOS%\%TABLA%.fmt" > nul 2>&1
bcp %BD%.dbo.%TABLA% out "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1

REM Paso C: Crear tabla vacia en destino (copiando estructura)
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT TOP 0 * INTO ##temp_%TABLA% FROM dbo.%TABLA%; DECLARE @sql NVARCHAR(MAX); SET @sql = (SELECT 'CREATE TABLE dbo.%TABLA% (' + STUFF((SELECT ', ' + c.name + ' ' + t.name + CASE WHEN t.name IN ('varchar','nvarchar','char','nchar','varbinary','binary') THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(CASE WHEN t.name LIKE 'n%%' THEN c.max_length/2 ELSE c.max_length END AS VARCHAR) END + ')' WHEN t.name IN ('decimal','numeric') THEN '(' + CAST(c.precision AS VARCHAR) + ',' + CAST(c.scale AS VARCHAR) + ')' ELSE '' END + CASE WHEN c.is_nullable = 0 THEN ' NOT NULL' ELSE ' NULL' END FROM tempdb.sys.columns c JOIN tempdb.sys.types t ON c.user_type_id = t.user_type_id WHERE c.object_id = OBJECT_ID('tempdb..##temp_%TABLA%') ORDER BY c.column_id FOR XML PATH('')), 1, 2, '') + ')'); DROP TABLE ##temp_%TABLA%; PRINT @sql;" -h -1 -W > "%DATOS%\%TABLA%_create.sql" 2>nul

REM Ejecutar CREATE TABLE en destino
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%DATOS%\%TABLA%_create.sql" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo        ERROR creando tabla
    goto :eof
)

REM Paso D: Importar datos
bcp %BD%.dbo.%TABLA% in "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo        ERROR importando datos
) else (
    echo        OK
)

goto :eof
