@echo off
chcp 65001 > nul
REM ============================================
REM Script: migrar_indices.bat
REM Exporta PKs e indices del ORIGEN y los aplica en DESTINO
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
echo    MIGRAR PRIMARY KEYS E INDICES
echo ============================================
echo.
echo    ORIGEN:  %SERVIDOR_ORIGEN% / %BD%
echo    DESTINO: %SERVIDOR_DESTINO% / %BD%
echo.
echo ============================================
echo.

REM Crear carpeta de datos
if not exist "%DATOS%" mkdir "%DATOS%"

REM ============================================
REM VERIFICAR CONEXIONES
REM ============================================
echo [1] Verificando conexiones...
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SELECT 1" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al ORIGEN
    pause
    exit /b 1
)
echo     ORIGEN: OK

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SELECT 1" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al DESTINO
    pause
    exit /b 1
)
echo     DESTINO: OK
echo.

REM ============================================
REM EXPORTAR PRIMARY KEYS
REM ============================================
echo [2] Exportando PRIMARY KEYS del ORIGEN...
SET PKS_FILE=%DATOS%\pks_exportadas.sql
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -i "%~dp001_exportar_pks_origen.sql" -h -1 -W -o "%PKS_FILE%"
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR exportando PKs
    pause
    exit /b 1
)
for /f %%A in ('type "%PKS_FILE%" ^| find /c "PRIMARY KEY"') do set TOTAL_PKS=%%A
echo     %TOTAL_PKS% PRIMARY KEYS encontradas
echo.

REM ============================================
REM EXPORTAR INDICES
REM ============================================
echo [3] Exportando INDICES del ORIGEN...
SET INDICES_FILE=%DATOS%\indices_exportados.sql
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -i "%~dp002_exportar_indices_origen.sql" -h -1 -W -o "%INDICES_FILE%"
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR exportando indices
    pause
    exit /b 1
)
for /f %%A in ('type "%INDICES_FILE%" ^| find /c "INDEX"') do set TOTAL_IDX=%%A
echo     %TOTAL_IDX% INDICES encontrados
echo.

REM ============================================
REM APLICAR PRIMARY KEYS EN DESTINO
REM ============================================
echo [4] Aplicando PRIMARY KEYS en DESTINO...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%PKS_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     Algunas PKs ya existian o hubo errores menores
) else (
    echo     OK
)
echo.

REM ============================================
REM APLICAR INDICES EN DESTINO
REM ============================================
echo [5] Aplicando INDICES en DESTINO...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%INDICES_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     Algunos indices ya existian o hubo errores menores
) else (
    echo     OK
)
echo.

REM ============================================
REM VERIFICACION
REM ============================================
echo [6] Verificando en DESTINO...
echo.
echo PRIMARY KEYS en DESTINO:
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT t.name AS Tabla, i.name AS PK FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name" -W -s" | "
echo.
echo INDICES en DESTINO:
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT t.name AS Tabla, i.name AS Indice FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name, i.name" -W -s" | "

echo.
echo ============================================
echo MIGRACION DE PKs E INDICES COMPLETADA
echo ============================================
echo.
echo Archivos generados:
echo   - %PKS_FILE%
echo   - %INDICES_FILE%
echo.
pause
