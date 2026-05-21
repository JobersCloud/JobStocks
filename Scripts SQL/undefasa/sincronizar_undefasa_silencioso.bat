@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
REM ============================================
REM Script: sincronizar_undefasa_silencioso.bat
REM Sincronizacion con BCP (SIN MENSAJES - Tarea Programada)
REM
REM ORIGEN:  192.168.0.73 / euro (Undefasa ERP)
REM DESTINO: 192.168.0.50 / Undefasa (Docker SQL Server 2025)
REM ============================================

SET SERVIDOR_ORIGEN=192.168.0.73
SET SERVIDOR_DESTINO=192.168.0.50,1433
SET BD_ORIGEN=euro
SET BD_DESTINO=Undefasa

SET USUARIO_ORIGEN=sa
SET CLAVE_ORIGEN=FLASH

SET USUARIO_DESTINO=sa
SET "PW_DEST=Undef@s@2026%%$"

SET "SQLCMD170=C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE"
SET "BCP170=C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\bcp.exe"

SET DATOS=C:\TEMP\sync_undefasa
SET RUTA_IMAGENES=Z:\
SET EMPRESA_ID=1

if not exist "%DATOS%" mkdir "%DATOS%"

REM ============================================
REM VERIFICAR CONEXIONES
REM ============================================
"!SQLCMD170!" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -Q "SELECT 1" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 exit /b 1

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -Q "SELECT 1" -h -1 -W -C > nul 2>&1
if %ERRORLEVEL% NEQ 0 exit /b 1

REM ============================================
REM SINCRONIZAR TABLAS NORMALES
REM ============================================
call :sync_tabla empresas
call :sync_tabla unidades
call :sync_tabla formatos
call :sync_tabla calidades
call :sync_tabla almmodelos
call :sync_tabla almcolores
call :sync_tabla pallets
call :sync_tabla articulos
call :sync_tabla almalmacen
call :sync_tabla almubimapa
call :sync_tabla almlinubica
call :sync_tabla almlinubica_bloqueo
call :sync_tabla almartcajas
call :sync_tabla palarticulo
call :sync_tabla almcajas
call :sync_tabla almartcal
call :sync_tabla almarttonopeso
call :sync_tabla venliped
call :sync_venped
call :sync_tabla genter
call :sync_tabla paises
call :sync_tabla provincias
call :sync_tabla tono
call :sync_tabla calibre
call :sync_tabla ean13

REM ============================================
REM SINCRONIZAR TABLAS CON BLOBS
REM ============================================
call :sync_blob articulo_ficha_tecnica
call :sync_blob articulo_ficha_tecnica_tono

REM ============================================
REM SINCRONIZAR IMAGENES DESDE DIRECTORIO
REM ============================================
call :sync_imagenes_directorio

REM ============================================
REM VACIAR LOG DE TRANSACCIONES EN DESTINO
REM ============================================
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "DECLARE @logName NVARCHAR(128); SELECT @logName = name FROM sys.master_files WHERE database_id = DB_ID('%BD_DESTINO%') AND type_desc = 'LOG'; ALTER DATABASE %BD_DESTINO% SET RECOVERY SIMPLE; DBCC SHRINKFILE (@logName, 1); ALTER DATABASE %BD_DESTINO% SET RECOVERY FULL;" > nul 2>&1

REM ============================================
REM ACTUALIZAR FECHA DE SINCRONIZACION
REM ============================================
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d ApiRestStocks -C -Q "UPDATE parametros SET valor = CONVERT(VARCHAR(19), GETDATE(), 120), fecha_modificacion = GETDATE() WHERE clave = 'FECHA_ULTIMA_SINCRONIZACION'" > nul 2>&1

exit /b 0

REM ============================================
REM FUNCION: recrear_si_esquema_cambia
REM ============================================
:recrear_si_esquema_cambia
set TABLA_RE=%~1

"!SQLCMD170!" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -W -Q "SET NOCOUNT ON; SELECT CAST(COUNT(*) AS VARCHAR) + '-' + ISNULL(CAST(CHECKSUM_AGG(BINARY_CHECKSUM(COLUMN_NAME, DATA_TYPE, ISNULL(CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR),''), ISNULL(CAST(NUMERIC_PRECISION AS VARCHAR),''))) AS VARCHAR),'0') FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '%TABLA_RE%' AND TABLE_SCHEMA = 'dbo'" > "%DATOS%\schema_o.txt" 2>nul
set /p SCHEMA_O=<"%DATOS%\schema_o.txt"

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; IF OBJECT_ID('dbo.%TABLA_RE%','U') IS NULL SELECT '0-0' ELSE SELECT CAST(COUNT(*) AS VARCHAR) + '-' + ISNULL(CAST(CHECKSUM_AGG(BINARY_CHECKSUM(COLUMN_NAME, DATA_TYPE, ISNULL(CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR),''), ISNULL(CAST(NUMERIC_PRECISION AS VARCHAR),''))) AS VARCHAR),'0') FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '%TABLA_RE%' AND TABLE_SCHEMA = 'dbo'" > "%DATOS%\schema_d.txt" 2>nul
set /p SCHEMA_D=<"%DATOS%\schema_d.txt"

if "!SCHEMA_O!"=="!SCHEMA_D!" (
    set RECREADA=0
) else (
    "!SQLCMD170!" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -y 8000 -o "%DATOS%\create_%TABLA_RE%.sql" -Q "SET NOCOUNT ON; DECLARE @cols NVARCHAR(MAX) = ''; SELECT @cols = @cols + ', ' + QUOTENAME(COLUMN_NAME) + ' ' + DATA_TYPE + CASE WHEN DATA_TYPE IN ('char','varchar','nchar','nvarchar') THEN '(' + CASE WHEN CHARACTER_MAXIMUM_LENGTH = -1 THEN 'MAX' ELSE CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR) END + ')' WHEN DATA_TYPE IN ('decimal','numeric') THEN '(' + CAST(NUMERIC_PRECISION AS VARCHAR) + ',' + CAST(NUMERIC_SCALE AS VARCHAR) + ')' ELSE '' END + ' NULL' FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '%TABLA_RE%' AND TABLE_SCHEMA = 'dbo' ORDER BY ORDINAL_POSITION; SET @cols = STUFF(@cols, 1, 2, ''); SELECT 'IF OBJECT_ID(''dbo.%TABLA_RE%'',''U'') IS NOT NULL DROP TABLE dbo.%TABLA_RE%; CREATE TABLE dbo.%TABLA_RE% (' + @cols + ');';"

    "!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -i "%DATOS%\create_%TABLA_RE%.sql" > nul 2>&1
    set RECREADA=1
)
goto :eof

REM ============================================
REM FUNCION: sync_tabla
REM ============================================
:sync_tabla
set TABLA=%~1

call :recrear_si_esquema_cambia %TABLA%

"!SQLCMD170!" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -W -Q "SET NOCOUNT ON; SELECT ISNULL(CHECKSUM_AGG(BINARY_CHECKSUM(*)),0) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\chk_o.txt" 2>nul
set /p CHK_O=<"%DATOS%\chk_o.txt"

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; SELECT ISNULL(CHECKSUM_AGG(BINARY_CHECKSUM(*)),0) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\chk_d.txt" 2>nul
set /p CHK_D=<"%DATOS%\chk_d.txt"

if "!RECREADA!"=="1" goto :sync_tabla_do_s
if "!CHK_O!"=="!CHK_D!" goto :eof

:sync_tabla_do_s
"!BCP170!" "SELECT * FROM %BD_ORIGEN%.dbo.%TABLA% WITH (NOLOCK)" queryout "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -N > nul 2>&1
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.%TABLA%" > nul 2>&1
"!BCP170!" %BD_DESTINO%.dbo.%TABLA% in "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -N > nul 2>&1
goto :eof

REM ============================================
REM FUNCION: sync_blob
REM ============================================
:sync_blob
set TABLA=%~1

call :recrear_si_esquema_cambia %TABLA%

"!SQLCMD170!" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"

if "!RECREADA!"=="1" goto :sync_blob_do_s
if "!CNT_O!"=="!CNT_D!" goto :eof

:sync_blob_do_s
"!BCP170!" "SELECT * FROM %BD_ORIGEN%.dbo.%TABLA% WITH (NOLOCK)" queryout "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -N > nul 2>&1
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.%TABLA%" > nul 2>&1
"!BCP170!" %BD_DESTINO%.dbo.%TABLA% in "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -N > nul 2>&1
goto :eof

REM ============================================
REM FUNCION: sync_venped
REM ============================================
:sync_venped
call :recrear_si_esquema_cambia venped

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.venped" > nul 2>&1
"!BCP170!" "SELECT * FROM %BD_ORIGEN%.dbo.venped WITH (NOLOCK) WHERE pedido IN (SELECT venliped.pedido FROM %BD_ORIGEN%.dbo.venliped WITH (NOLOCK) WHERE venliped.empresa = venped.empresa AND venliped.anyo = venped.anyo)" queryout "%DATOS%\venped.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -N > nul 2>&1
"!BCP170!" %BD_DESTINO%.dbo.venped in "%DATOS%\venped.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -N > nul 2>&1
goto :eof

REM ============================================
REM FUNCION: sync_imagenes_directorio
REM ============================================
:sync_imagenes_directorio

set CNT_FILES=0
for %%F in ("%RUTA_IMAGENES%*@*.jpg") do set /a CNT_FILES+=1

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; IF OBJECT_ID('dbo.ps_articulo_imagen','U') IS NULL SELECT '0' ELSE SELECT CAST(COUNT(*) AS VARCHAR) FROM dbo.ps_articulo_imagen" > "%DATOS%\cnt_img.txt" 2>nul
set /p CNT_IMG=<"%DATOS%\cnt_img.txt"

if "!CNT_FILES!"=="!CNT_IMG!" goto :eof

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "IF OBJECT_ID('dbo.ps_articulo_imagen','U') IS NULL CREATE TABLE dbo.ps_articulo_imagen (id numeric(18,0) IDENTITY(1,1) NULL, empresa varchar(5) NULL, articulo varchar(20) NULL, foto image NULL, predeterminada int NULL, width_thumbnail int NULL, height_thumbnail int NULL, thumbnail image NULL, nombre varchar(100) NULL, web_id numeric(18,0) NULL);" > nul 2>&1

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.ps_articulo_imagen" > nul 2>&1

> "%DATOS%\insert_imagenes.sql" echo SET NOCOUNT ON;

for %%F in ("%RUTA_IMAGENES%*@*.jpg") do (
    set "FILENAME=%%~nF"
    for /f "tokens=1 delims=@" %%C in ("!FILENAME!") do set "CODIGO=%%C"
    >> "%DATOS%\insert_imagenes.sql" echo INSERT INTO dbo.ps_articulo_imagen (empresa, articulo, foto, nombre) SELECT '%EMPRESA_ID%', '!CODIGO!', BulkColumn, '%%~nxF' FROM OPENROWSET(BULK '%%F', SINGLE_BLOB) AS img;
)

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -i "%DATOS%\insert_imagenes.sql" > nul 2>&1
goto :eof
