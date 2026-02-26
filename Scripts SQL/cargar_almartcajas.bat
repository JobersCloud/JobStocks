@echo off
chcp 65001 > nul
REM ============================================
REM Script: cargar_almartcajas.bat
REM Copia SOLO la tabla almartcajas entre servidores
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
SET TABLA=almartcajas

cls
echo.
echo ============================================
echo    CARGAR TABLA: %TABLA%
echo ============================================
echo.
echo    ORIGEN:  %SERVIDOR_ORIGEN% / %BD%
echo    DESTINO: %SERVIDOR_DESTINO% / %BD%
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

echo [3] Exportando %TABLA% desde ORIGEN...
bcp %BD%.dbo.%TABLA% out "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n -C 65001
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR exportando
    pause
    exit /b 1
)
echo     OK

echo [4] Eliminando tabla en DESTINO si existe...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "IF OBJECT_ID('dbo.%TABLA%', 'U') IS NOT NULL DROP TABLE dbo.%TABLA%" > nul 2>&1
echo     OK

echo [5] Generando estructura de tabla...
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT TOP 0 * INTO ##temp_%TABLA% FROM dbo.%TABLA%; DECLARE @sql NVARCHAR(MAX); SET @sql = (SELECT 'CREATE TABLE dbo.%TABLA% (' + STUFF((SELECT ', ' + c.name + ' ' + t.name + CASE WHEN t.name IN ('varchar','nvarchar','char','nchar','varbinary','binary') THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(CASE WHEN t.name LIKE 'n%%' THEN c.max_length/2 ELSE c.max_length END AS VARCHAR) END + ')' WHEN t.name IN ('decimal','numeric') THEN '(' + CAST(c.precision AS VARCHAR) + ',' + CAST(c.scale AS VARCHAR) + ')' ELSE '' END + CASE WHEN c.is_nullable = 0 THEN ' NOT NULL' ELSE ' NULL' END FROM tempdb.sys.columns c JOIN tempdb.sys.types t ON c.user_type_id = t.user_type_id WHERE c.object_id = OBJECT_ID('tempdb..##temp_%TABLA%') ORDER BY c.column_id FOR XML PATH('')), 1, 2, '') + ')'); DROP TABLE ##temp_%TABLA%; PRINT @sql;" -h -1 -W > "%DATOS%\%TABLA%_create.sql" 2>nul
echo     OK

echo [6] Creando tabla en DESTINO...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%DATOS%\%TABLA%_create.sql" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR creando tabla
    pause
    exit /b 1
)
echo     OK

echo [7] Importando datos...
bcp %BD%.dbo.%TABLA% in "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR importando
    pause
    exit /b 1
)
echo     OK

echo.
echo [8] Verificando...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT '%TABLA%: ' + CAST(COUNT(*) AS VARCHAR) + ' filas' FROM dbo.%TABLA%" -h -1 -W
echo.
echo ============================================
echo TABLA %TABLA% CARGADA EXITOSAMENTE
echo ============================================
pause
