@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
REM ============================================
REM Script: sincronizar_undefasa_silencioso.bat
REM Sincronizacion con BCP (SIN MENSAJES - para Tarea Programada)
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

REM Rutas a herramientas nuevas (ODBC 17 - soporta -C para TLS)
SET "SQLCMD170=C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE"
SET "BCP170=C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\bcp.exe"

SET DATOS=C:\TEMP\sync_undefasa

if not exist "%DATOS%" mkdir "%DATOS%"

REM ============================================
REM VERIFICAR CONEXIONES
REM ============================================
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -Q "SELECT 1" -h -1 -W > nul 2>&1
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

REM ============================================
REM SINCRONIZAR TABLAS CON BLOBS
REM ============================================
call :sync_imagenes
call :sync_fichas
call :sync_fichas_tono

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
REM FUNCION: sync_tabla (compara CHECKSUM)
REM ============================================
:sync_tabla
set TABLA=%~1

sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -W -Q "SET NOCOUNT ON; SELECT ISNULL(CHECKSUM_AGG(BINARY_CHECKSUM(*)),0) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\chk_o.txt" 2>nul
set /p CHK_O=<"%DATOS%\chk_o.txt"

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; SELECT ISNULL(CHECKSUM_AGG(BINARY_CHECKSUM(*)),0) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\chk_d.txt" 2>nul
set /p CHK_D=<"%DATOS%\chk_d.txt"

if "!CHK_O!"=="!CHK_D!" goto :eof

bcp "SELECT * FROM %BD_ORIGEN%.dbo.%TABLA% WITH (NOLOCK)" queryout "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.%TABLA%" > nul 2>&1
"!BCP170!" %BD_DESTINO%.dbo.%TABLA% in "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -n -C > nul 2>&1
goto :eof

REM ============================================
REM FUNCION: sync_imagenes (compara COUNT)
REM ============================================
:sync_imagenes
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.ps_articulo_imagen WITH (NOLOCK)" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.ps_articulo_imagen WITH (NOLOCK)" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"

if "!CNT_O!"=="!CNT_D!" goto :eof

bcp "SELECT * FROM %BD_ORIGEN%.dbo.ps_articulo_imagen WITH (NOLOCK)" queryout "%DATOS%\ps_articulo_imagen.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.ps_articulo_imagen" > nul 2>&1
"!BCP170!" %BD_DESTINO%.dbo.ps_articulo_imagen in "%DATOS%\ps_articulo_imagen.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -n -C > nul 2>&1
goto :eof

REM ============================================
REM FUNCION: sync_fichas (compara COUNT)
REM ============================================
:sync_fichas
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.articulo_ficha_tecnica WITH (NOLOCK)" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.articulo_ficha_tecnica WITH (NOLOCK)" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"

if "!CNT_O!"=="!CNT_D!" goto :eof

bcp "SELECT * FROM %BD_ORIGEN%.dbo.articulo_ficha_tecnica WITH (NOLOCK)" queryout "%DATOS%\articulo_ficha_tecnica.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.articulo_ficha_tecnica" > nul 2>&1
"!BCP170!" %BD_DESTINO%.dbo.articulo_ficha_tecnica in "%DATOS%\articulo_ficha_tecnica.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -n -C > nul 2>&1
goto :eof

REM ============================================
REM FUNCION: sync_fichas_tono (compara COUNT)
REM ============================================
:sync_fichas_tono
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.articulo_ficha_tecnica_tono WITH (NOLOCK)" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.articulo_ficha_tecnica_tono WITH (NOLOCK)" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"

if "!CNT_O!"=="!CNT_D!" goto :eof

bcp "SELECT * FROM %BD_ORIGEN%.dbo.articulo_ficha_tecnica_tono WITH (NOLOCK)" queryout "%DATOS%\articulo_ficha_tecnica_tono.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.articulo_ficha_tecnica_tono" > nul 2>&1
"!BCP170!" %BD_DESTINO%.dbo.articulo_ficha_tecnica_tono in "%DATOS%\articulo_ficha_tecnica_tono.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -n -C > nul 2>&1
goto :eof

REM ============================================
REM FUNCION: sync_venped (siempre sincroniza)
REM ============================================
:sync_venped
bcp "SELECT * FROM %BD_ORIGEN%.dbo.venped WITH (NOLOCK) WHERE pedido IN (SELECT venliped.pedido FROM %BD_ORIGEN%.dbo.venliped WITH (NOLOCK) WHERE venliped.empresa = venped.empresa AND venliped.anyo = venped.anyo)" queryout "%DATOS%\venped.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.venped" > nul 2>&1
"!BCP170!" %BD_DESTINO%.dbo.venped in "%DATOS%\venped.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -n -C > nul 2>&1
goto :eof
