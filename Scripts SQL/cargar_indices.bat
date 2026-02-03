@echo off
chcp 65001 > nul
REM ============================================
REM Script: cargar_indices.bat
REM Exporta índices del ORIGEN y los crea en DESTINO
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
SET INDICES_FILE=%DATOS%\indices_cristal.sql

cls
echo.
echo ============================================
echo    CARGAR INDICES DE CRISTAL
echo ============================================
echo.
echo    ORIGEN:  %SERVIDOR_ORIGEN% / %BD%
echo    DESTINO: %SERVIDOR_DESTINO% / %BD%
echo.
echo ============================================
echo.

REM Crear carpeta de datos
if not exist "%DATOS%" mkdir "%DATOS%"

echo [1] Verificando conexiones...
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SELECT 'OK'" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al ORIGEN
    pause
    exit /b 1
)
echo     ORIGEN: OK

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SELECT 'OK'" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al DESTINO
    pause
    exit /b 1
)
echo     DESTINO: OK
echo.

echo [2] Exportando indices del ORIGEN...
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT 'CREATE ' + CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END + CASE WHEN i.type = 1 THEN 'CLUSTERED ' ELSE 'NONCLUSTERED ' END + 'INDEX [' + i.name + '] ON [dbo].[' + t.name + '] (' + STUFF((SELECT ', [' + c.name + ']' + CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0 ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') + ')' + CASE WHEN (SELECT COUNT(*) FROM sys.index_columns ic WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 1) > 0 THEN ' INCLUDE (' + STUFF((SELECT ', [' + c.name + ']' FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 1 ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') + ')' ELSE '' END + ';' AS sql_script FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name, i.name" -h -1 -W -o "%INDICES_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo     ERROR exportando indices
    pause
    exit /b 1
)

REM Contar indices exportados
for /f %%A in ('type "%INDICES_FILE%" ^| find /c "CREATE"') do set TOTAL_INDICES=%%A
echo     %TOTAL_INDICES% indices exportados
echo.

echo [3] Creando indices en DESTINO...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%INDICES_FILE%" -b 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo     Algunos indices ya existian o hubo errores menores
) else (
    echo     OK
)
echo.

echo [4] Exportando PRIMARY KEYS del ORIGEN...
SET PKS_FILE=%DATOS%\primary_keys_cristal.sql
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT 'ALTER TABLE [dbo].[' + t.name + '] ADD CONSTRAINT [' + i.name + '] PRIMARY KEY ' + CASE WHEN i.type = 1 THEN 'CLUSTERED' ELSE 'NONCLUSTERED' END + ' (' + STUFF((SELECT ', [' + c.name + ']' FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') + ');' FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name" -h -1 -W -o "%PKS_FILE%"

for /f %%A in ('type "%PKS_FILE%" ^| find /c "PRIMARY KEY"') do set TOTAL_PKS=%%A
echo     %TOTAL_PKS% primary keys exportadas
echo.

echo [5] Creando PRIMARY KEYS en DESTINO...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%PKS_FILE%" -b 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo     Algunas PKs ya existian o hubo errores menores
) else (
    echo     OK
)
echo.

echo ============================================
echo INDICES Y PKs CARGADOS
echo ============================================
echo.
echo Archivos generados:
echo   - %INDICES_FILE%
echo   - %PKS_FILE%
echo.
pause
