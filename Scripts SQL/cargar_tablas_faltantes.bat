@echo off
chcp 65001 > nul
REM ============================================
REM Script: cargar_tablas_faltantes.bat
REM Carga las 4 tablas faltantes para view_externos_stock:
REM   - palarticulo
REM   - almcajas
REM   - almartcal
REM   - almarttonopeso
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
echo    CARGAR TABLAS FALTANTES PARA VISTA
echo ============================================
echo.
echo    ORIGEN:  %SERVIDOR_ORIGEN% / %BD%
echo    DESTINO: %SERVIDOR_DESTINO% / %BD%
echo.
echo    Tablas: palarticulo, almcajas, almartcal, almarttonopeso
echo.
echo ============================================
echo.

REM Verificar conexiones
echo [1] Verificando conexion al ORIGEN...
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SELECT 'OK'" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al ORIGEN
    pause
    exit /b 1
)
echo     OK

echo [2] Verificando conexion al DESTINO...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SELECT 'OK'" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al DESTINO
    pause
    exit /b 1
)
echo     OK
echo.

REM Crear carpeta de datos
if not exist "%DATOS%" mkdir "%DATOS%"

echo [3] Migrando tablas...
echo.

call :migrar_tabla palarticulo
call :migrar_tabla almcajas
call :migrar_tabla almartcal
call :migrar_tabla almarttonopeso

echo.
echo [4] Creando PRIMARY KEYS...
SET TABLAS_SQL='palarticulo','almcajas','almartcal','almarttonopeso'
SET PKS_FILE=%DATOS%\pks_faltantes.sql
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT 'ALTER TABLE [dbo].[' + t.name + '] ADD CONSTRAINT [' + i.name + '] PRIMARY KEY ' + CASE WHEN i.type = 1 THEN 'CLUSTERED' ELSE 'NONCLUSTERED' END + ' (' + STUFF((SELECT ', [' + c.name + ']' FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') + ');' FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name IN (%TABLAS_SQL%) ORDER BY t.name" -h -1 -W -o "%PKS_FILE%" 2>nul
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%PKS_FILE%" 2>nul
echo     OK

echo [5] Creando INDICES...
SET INDICES_FILE=%DATOS%\indices_faltantes.sql
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT 'CREATE ' + CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END + CASE WHEN i.type = 1 THEN 'CLUSTERED ' ELSE 'NONCLUSTERED ' END + 'INDEX [' + i.name + '] ON [dbo].[' + t.name + '] (' + STUFF((SELECT ', [' + c.name + ']' + CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0 ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') + ');' AS sql_script FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name IN (%TABLAS_SQL%) ORDER BY t.name, i.name" -h -1 -W -o "%INDICES_FILE%" 2>nul
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%INDICES_FILE%" 2>nul
echo     OK

echo.
echo [6] Verificando registros...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT 'palarticulo', COUNT(*) FROM dbo.palarticulo UNION ALL SELECT 'almcajas', COUNT(*) FROM dbo.almcajas UNION ALL SELECT 'almartcal', COUNT(*) FROM dbo.almartcal UNION ALL SELECT 'almarttonopeso', COUNT(*) FROM dbo.almarttonopeso" -W -s" | "
echo.
echo ============================================
echo TABLAS, PKs E INDICES CARGADOS
echo ============================================
pause
exit /b 0

REM ============================================
REM FUNCION: migrar_tabla
REM ============================================
:migrar_tabla
set TABLA=%1
echo     %TABLA%...

REM Eliminar tabla en destino si existe
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "IF OBJECT_ID('dbo.%TABLA%', 'U') IS NOT NULL DROP TABLE dbo.%TABLA%" > nul 2>&1

REM Exportar datos desde origen
bcp %BD%.dbo.%TABLA% out "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1

REM Generar CREATE TABLE
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT TOP 0 * INTO ##temp_%TABLA% FROM dbo.%TABLA%; DECLARE @sql NVARCHAR(MAX); SET @sql = (SELECT 'CREATE TABLE dbo.%TABLA% (' + STUFF((SELECT ', ' + c.name + ' ' + t.name + CASE WHEN t.name IN ('varchar','nvarchar','char','nchar','varbinary','binary') THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(CASE WHEN t.name LIKE 'n%%' THEN c.max_length/2 ELSE c.max_length END AS VARCHAR) END + ')' WHEN t.name IN ('decimal','numeric') THEN '(' + CAST(c.precision AS VARCHAR) + ',' + CAST(c.scale AS VARCHAR) + ')' ELSE '' END + CASE WHEN c.is_nullable = 0 THEN ' NOT NULL' ELSE ' NULL' END FROM tempdb.sys.columns c JOIN tempdb.sys.types t ON c.user_type_id = t.user_type_id WHERE c.object_id = OBJECT_ID('tempdb..##temp_%TABLA%') ORDER BY c.column_id FOR XML PATH('')), 1, 2, '') + ')'); DROP TABLE ##temp_%TABLA%; PRINT @sql;" -h -1 -W > "%DATOS%\%TABLA%_create.sql" 2>nul

REM Crear tabla en destino
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%DATOS%\%TABLA%_create.sql" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo        ERROR creando tabla
    goto :eof
)

REM Importar datos
bcp %BD%.dbo.%TABLA% in "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo        ERROR importando datos
) else (
    echo        OK
)

goto :eof
