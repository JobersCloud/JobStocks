@echo off
chcp 65001 > nul
REM ============================================
REM Script: aplicar_pks_indices_todas.bat
REM Aplica PKs e indices de TODAS las 19 tablas
REM Exporta de ORIGEN y aplica en DESTINO directamente
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
echo    APLICAR PKs E INDICES - TODAS LAS TABLAS
echo ============================================
echo.

if not exist "%DATOS%" mkdir "%DATOS%"

echo [1/4] Verificando conexiones...
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SELECT 1" -h -1 > nul 2>&1
if %ERRORLEVEL% NEQ 0 (echo ERROR ORIGEN & pause & exit /b 1)
echo     ORIGEN: OK

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SELECT 1" -h -1 > nul 2>&1
if %ERRORLEVEL% NEQ 0 (echo ERROR DESTINO & pause & exit /b 1)
echo     DESTINO: OK
echo.

echo [2/4] Exportando PRIMARY KEYS...
SET PKS_FILE=%DATOS%\all_pks.sql
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -o "%PKS_FILE%" -Q "SET NOCOUNT ON; SELECT 'IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = ''' + i.name + ''' AND object_id = OBJECT_ID(''dbo.' + t.name + ''')) ALTER TABLE [dbo].[' + t.name + '] ADD CONSTRAINT [' + i.name + '] PRIMARY KEY ' + CASE WHEN i.type = 1 THEN 'CLUSTERED' ELSE 'NONCLUSTERED' END + ' (' + STUFF((SELECT ', [' + c.name + ']' FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') + ');' FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name"

for /f %%A in ('type "%PKS_FILE%" ^| find /c "PRIMARY KEY"') do set TOTAL_PKS=%%A
echo     %TOTAL_PKS% PKs exportadas
echo.

echo [3/4] Exportando INDICES...
SET IDX_FILE=%DATOS%\all_indices.sql
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -o "%IDX_FILE%" -Q "SET NOCOUNT ON; SELECT 'IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = ''' + i.name + ''' AND object_id = OBJECT_ID(''dbo.' + t.name + ''')) CREATE ' + CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END + 'NONCLUSTERED INDEX [' + i.name + '] ON [dbo].[' + t.name + '] (' + STUFF((SELECT ', [' + c.name + ']' FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0 ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') + ');' FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name, i.name"

for /f %%A in ('type "%IDX_FILE%" ^| find /c "INDEX"') do set TOTAL_IDX=%%A
echo     %TOTAL_IDX% indices exportados
echo.

echo [4/4] Aplicando en DESTINO...
echo.
echo     Aplicando PKs...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%PKS_FILE%" 2>&1 | findstr /i "error"
echo     Aplicando Indices...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%IDX_FILE%" 2>&1 | findstr /i "error"
echo.

echo ============================================
echo VERIFICACION - PKs en DESTINO:
echo ============================================
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT t.name AS Tabla, i.name AS PK FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name" -W -s"|"

echo.
echo ============================================
echo VERIFICACION - Total Indices por Tabla:
echo ============================================
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT t.name AS Tabla, COUNT(*) AS Indices FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') GROUP BY t.name ORDER BY t.name" -W -s"|"

echo.
echo ============================================
echo COMPLETADO
echo ============================================
pause
