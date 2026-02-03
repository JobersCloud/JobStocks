@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
REM ============================================
REM Script: sincronizar_cristal.bat
REM Sincronizacion con BCP
REM
REM Tablas normales: Compara CHECKSUM (detecta inserts/updates/deletes)
REM Tablas con blobs: Compara COUNT (mas rapido, evita leer blobs)
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

REM Usar ruta sin espacios para evitar problemas con sqlcmd/bcp
SET DATOS=C:\TEMP\sync_cristal

cls
echo.
echo ============================================
echo    SINCRONIZACION DE CRISTAL
echo ============================================
echo.
echo    ORIGEN:  %SERVIDOR_ORIGEN% / %BD%
echo    DESTINO: %SERVIDOR_DESTINO% / %BD%
echo.
echo ============================================
echo.

if not exist "%DATOS%" mkdir "%DATOS%"

REM ============================================
REM VERIFICAR CONEXIONES
REM ============================================
echo [1/4] Verificando conexiones...
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
REM SINCRONIZAR TABLAS NORMALES
REM ============================================
echo [2/4] Sincronizando tablas normales...
echo.

call :sync_tabla empresas
call :sync_tabla unidades
call :sync_tabla formatos
call :sync_tabla calidades
call :sync_tabla almmodelos
call :sync_tabla almcolores
call :sync_tabla pallets
call :sync_tabla articulos
call :sync_tabla almlinubica
call :sync_tabla almartcajas
call :sync_tabla palarticulo
call :sync_tabla almcajas
call :sync_tabla almartcal
call :sync_tabla almarttonopeso
call :sync_tabla venliped
call :sync_tabla venped
call :sync_tabla genter

echo.

REM ============================================
REM SINCRONIZAR TABLAS CON BLOBS
REM ============================================
echo [3/4] Sincronizando tablas con blobs...
echo.

call :sync_imagenes
call :sync_fichas

echo.

REM ============================================
REM VACIAR LOG DE TRANSACCIONES EN DESTINO
REM ============================================
echo [4/4] Vaciando log de transacciones en destino...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "DECLARE @logName NVARCHAR(128); SELECT @logName = name FROM sys.master_files WHERE database_id = DB_ID('%BD%') AND type_desc = 'LOG'; ALTER DATABASE %BD% SET RECOVERY SIMPLE; DBCC SHRINKFILE (@logName, 1); ALTER DATABASE %BD% SET RECOVERY FULL;" > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     OK
) else (
    echo     No se pudo vaciar - puede requerir permisos
)

echo.
echo ============================================
echo SINCRONIZACION COMPLETADA
echo ============================================
echo.
pause
exit /b 0

REM ============================================
REM FUNCION: sync_tabla (compara CHECKSUM)
REM ============================================
:sync_tabla
set TABLA=%~1
<nul set /p="     %TABLA%... "

REM Obtener checksum ORIGEN
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT ISNULL(CHECKSUM_AGG(BINARY_CHECKSUM(*)),0) FROM dbo.%TABLA%" > "%DATOS%\chk_o.txt" 2>nul
set /p CHK_O=<"%DATOS%\chk_o.txt"

REM Obtener checksum DESTINO
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT ISNULL(CHECKSUM_AGG(BINARY_CHECKSUM(*)),0) FROM dbo.%TABLA%" > "%DATOS%\chk_d.txt" 2>nul
set /p CHK_D=<"%DATOS%\chk_d.txt"

REM Obtener count para mostrar
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.%TABLA%" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

REM Comparar checksums
if "!CHK_O!"=="!CHK_D!" (
    echo !CNT_O! registros [=]
) else (
    bcp %BD%.dbo.%TABLA% out "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
    sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "TRUNCATE TABLE dbo.%TABLA%" > nul 2>&1
    bcp %BD%.dbo.%TABLA% in "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n > nul 2>&1
    echo !CNT_O! registros [sync]
)
goto :eof

REM ============================================
REM FUNCION: sync_imagenes (compara COUNT - evita leer blobs)
REM ============================================
:sync_imagenes
<nul set /p="     ps_articulo_imagen... "

REM Obtener count ORIGEN
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.ps_articulo_imagen" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

REM Obtener count DESTINO
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.ps_articulo_imagen" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"

REM Comparar counts
if "!CNT_O!"=="!CNT_D!" (
    echo !CNT_O! registros [=]
) else (
    echo sincronizando...
    <nul set /p="                              exportando... "
    bcp %BD%.dbo.ps_articulo_imagen out "%DATOS%\ps_articulo_imagen.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
    echo OK
    <nul set /p="                              importando... "
    sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "TRUNCATE TABLE dbo.ps_articulo_imagen" > nul 2>&1
    bcp %BD%.dbo.ps_articulo_imagen in "%DATOS%\ps_articulo_imagen.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n > nul 2>&1
    echo OK [!CNT_O! registros] [sync]
)
goto :eof

REM ============================================
REM FUNCION: sync_fichas (compara COUNT - evita leer blobs)
REM ============================================
:sync_fichas
<nul set /p="     articulo_ficha_tecnica... "

REM Obtener count ORIGEN
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.articulo_ficha_tecnica" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

REM Obtener count DESTINO
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.articulo_ficha_tecnica" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"

REM Comparar counts
if "!CNT_O!"=="!CNT_D!" (
    echo !CNT_O! registros [=]
) else (
    echo sincronizando...
    <nul set /p="                              exportando... "
    bcp %BD%.dbo.articulo_ficha_tecnica out "%DATOS%\articulo_ficha_tecnica.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
    echo OK
    <nul set /p="                              importando... "
    sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "TRUNCATE TABLE dbo.articulo_ficha_tecnica" > nul 2>&1
    bcp %BD%.dbo.articulo_ficha_tecnica in "%DATOS%\articulo_ficha_tecnica.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n > nul 2>&1
    echo OK [!CNT_O! registros] [sync]
)
goto :eof
