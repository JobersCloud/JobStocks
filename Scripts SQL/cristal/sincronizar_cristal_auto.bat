@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
REM ============================================
REM Script: sincronizar_cristal_auto.bat
REM Version para TAREAS PROGRAMADAS (sin interaccion)
REM
REM Genera log en C:\TEMP\sync_cristal\logs\
REM ============================================

SET SERVIDOR_ORIGEN=192.168.100.5
SET SERVIDOR_DESTINO=10.1.99.4
SET BD=cristal

SET USUARIO_ORIGEN=sa
SET CLAVE_ORIGEN=desa2012

SET USUARIO_DESTINO=sa
SET CLAVE_DESTINO=Crijob2015Desa

SET DATOS=C:\TEMP\sync_cristal

REM Carpeta del propio .bat: alli estan los scripts _sync_*.sql
SET SQLDIR=%~dp0

REM Contador de tablas que han fallado
SET ERRORES=0
REM Logs en la misma carpeta del script
SET SCRIPT_DIR=%~dp0
SET LOGS=%SCRIPT_DIR%logs

REM Crear carpetas si no existen
if not exist "%DATOS%" mkdir "%DATOS%"
if not exist "%LOGS%" mkdir "%LOGS%"

REM Nombre del log solo con fecha (1 fichero por dia, se sobreescribe en cada ejecucion)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set FECHA=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%
SET LOGFILE=%LOGS%\sync_%FECHA%.log

REM Redirigir toda la salida al log
call :main > "%LOGFILE%" 2>&1
exit /b %ERRORLEVEL%

:main
echo ============================================
echo    SINCRONIZACION DE CRISTAL (AUTO)
echo    Fecha: %FECHA% %HORA:~0,2%:%HORA:~3,2%:%HORA:~6,2%
echo ============================================
echo.
echo    ORIGEN:  %SERVIDOR_ORIGEN% / %BD%
echo    DESTINO: %SERVIDOR_DESTINO% / %BD%
echo.
echo ============================================
echo.

REM ============================================
REM VERIFICAR CONEXIONES
REM ============================================
echo [1/6] Verificando entorno...
REM ============================================
REM VERIFICAR SCRIPTS AUXILIARES
REM ============================================
set FALTAN=
for %%F in (_sync_firma_columnas.sql _sync_firma_indices.sql _sync_gen_tabla.sql _sync_gen_indices.sql) do if not exist "%SQLDIR%%%F" set FALTAN=1
if defined FALTAN (
    echo     ERROR: faltan los scripts _sync_*.sql junto a este .bat
    echo     Copia la carpeta completa, no solo el .bat
    exit /b 1
)
echo     Scripts auxiliares: OK
echo.
echo [2/6] Verificando conexiones...
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SELECT 1" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al ORIGEN
    exit /b 1
)
echo     ORIGEN: OK

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SELECT 1" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     ERROR: No se puede conectar al DESTINO
    exit /b 1
)
echo     DESTINO: OK
echo.

REM ============================================
REM SINCRONIZAR TABLAS NORMALES
REM ============================================
echo [3/6] Sincronizando tablas normales...
echo.

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
call :sync_tabla venclientes
call :sync_tabla vencomerciales
call :sync_tabla venagentes
call :sync_tabla genter
call :sync_tabla paises
call :sync_tabla provincias

echo.

REM ============================================
REM SINCRONIZAR TABLAS CON BLOBS
REM ============================================
echo [4/6] Sincronizando tablas con blobs...
echo.

call :sync_blob ps_articulo_imagen
call :sync_blob articulo_ficha_tecnica
call :sync_blob articulo_ficha_tecnica_tono

echo.

REM ============================================
REM VACIAR LOG DE TRANSACCIONES EN DESTINO
REM ============================================
echo [5/6] Vaciando log de transacciones en destino...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "DECLARE @logName NVARCHAR(128); SELECT @logName = name FROM sys.master_files WHERE database_id = DB_ID('%BD%') AND type_desc = 'LOG'; ALTER DATABASE %BD% SET RECOVERY SIMPLE; DBCC SHRINKFILE (@logName, 1); ALTER DATABASE %BD% SET RECOVERY FULL;" > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     OK
) else (
    echo     No se pudo vaciar - puede requerir permisos
)

echo.

REM ============================================
REM ACTUALIZAR FECHA DE SINCRONIZACION
REM ============================================
echo [6/6] Registrando fecha de sincronizacion...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d ApiRestStocks -Q "UPDATE parametros SET valor = CONVERT(VARCHAR(19), GETDATE(), 120), fecha_modificacion = GETDATE() WHERE clave = 'FECHA_ULTIMA_SINCRONIZACION'" > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     OK
) else (
    echo     No se pudo actualizar - verificar que existe el parametro
)

echo.
if !ERRORES! GTR 0 (
    echo ============================================
    echo   ATENCION: !ERRORES! tablas con ERROR
    echo   Revisa arriba las lineas marcadas como ERROR
    echo ============================================
    echo.
)
echo ============================================
echo SINCRONIZACION COMPLETADA
echo ============================================
echo.
exit /b !ERRORES!

REM ============================================
REM FUNCION: sync_tabla
REM
REM   1. Compara el esquema de columnas ORIGEN vs DESTINO. Si ha cambiado
REM      (campo nuevo, tipo distinto, tabla inexistente) reconstruye la
REM      tabla en DESTINO con la definicion exacta del ORIGEN.
REM   2. Compara CHECKSUM de datos y recarga con BCP si difiere.
REM   3. Verifica que el numero de filas cargadas coincide con el ORIGEN.
REM   4. Replica en DESTINO la PK y los indices tal y como estan en ORIGEN.
REM
REM   Salvaguardas:
REM   - Si no se puede leer el esquema del ORIGEN la tabla se OMITE y el
REM     destino no se toca: un corte de red no puede borrar nada.
REM   - El script de reconstruccion solo se ejecuta si esta completo, es
REM     decir si lleva el centinela "-- FIN_SCRIPT_OK" al final.
REM   - Tras cargar se comparan filas ORIGEN vs DESTINO: si no cuadran se
REM     marca ERROR en vez de dar la tabla por buena.
REM ============================================
:sync_tabla
set TABLA=%~1
set ETIQUETA=
set IDXTAG=
set FORZAR=
set RECREAR_FALLO=
<nul set /p="     %TABLA%... "

REM --- Esquema de columnas en ORIGEN ---
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -v TABLA="%TABLA%" -i "%SQLDIR%_sync_firma_columnas.sql" -o "%DATOS%\fcol_o.txt" > nul 2>&1
set TAM_O=0
for %%A in ("%DATOS%\fcol_o.txt") do set TAM_O=%%~zA
if !TAM_O! LSS 5 (
    echo ERROR: no se pudo leer el esquema del ORIGEN - tabla omitida
    set /a ERRORES+=1
    goto :eof
)

REM --- Esquema de columnas en DESTINO ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -v TABLA="%TABLA%" -i "%SQLDIR%_sync_firma_columnas.sql" -o "%DATOS%\fcol_d.txt" > nul 2>&1

REM --- Si el esquema ha cambiado, reconstruir la tabla en DESTINO ---
fc /b "%DATOS%\fcol_o.txt" "%DATOS%\fcol_d.txt" > nul 2>&1
if errorlevel 1 call :recrear_tabla
if "!RECREAR_FALLO!"=="1" goto :eof

REM --- Checksum de datos ORIGEN ---
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT ISNULL(CHECKSUM_AGG(BINARY_CHECKSUM(*)),0) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\chk_o.txt" 2>nul
set /p CHK_O=<"%DATOS%\chk_o.txt"

REM --- Checksum de datos DESTINO ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT ISNULL(CHECKSUM_AGG(BINARY_CHECKSUM(*)),0) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\chk_d.txt" 2>nul
set /p CHK_D=<"%DATOS%\chk_d.txt"

REM --- Filas en ORIGEN ---
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

if "!FORZAR!"=="1" goto :st_cargar
if not "!CHK_O!"=="!CHK_D!" goto :st_cargar
set ETIQUETA==
set CNT_D=!CNT_O!
goto :st_indices

:st_cargar
bcp "SELECT * FROM %BD%.dbo.%TABLA% WITH (NOLOCK)" queryout "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "TRUNCATE TABLE dbo.%TABLA%" > nul 2>&1
bcp %BD%.dbo.%TABLA% in "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n > nul 2>&1

REM --- Verificar que se han cargado todas las filas ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"
if not "!CNT_O!"=="!CNT_D!" (
    echo ERROR: la carga ha fallado - ORIGEN=!CNT_O! DESTINO=!CNT_D!
    set /a ERRORES+=1
    goto :eof
)
set ETIQUETA=!ETIQUETA!sync

:st_indices
call :sync_indices
echo !CNT_D! registros [!ETIQUETA!!IDXTAG!]
goto :eof

REM ============================================
REM FUNCION: recrear_tabla
REM   Reconstruye la tabla en DESTINO con la definicion del ORIGEN.
REM   Solo toca el destino si el script generado esta completo.
REM ============================================
:recrear_tabla
set RECREAR_FALLO=
if exist "%DATOS%\create_%TABLA%.sql" del "%DATOS%\create_%TABLA%.sql" > nul 2>&1
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -v TABLA="%TABLA%" -i "%SQLDIR%_sync_gen_tabla.sql" -o "%DATOS%\create_%TABLA%.sql" > nul 2>&1

findstr /C:"-- FIN_SCRIPT_OK" "%DATOS%\create_%TABLA%.sql" > nul 2>&1
if errorlevel 1 (
    echo ERROR: script de creacion incompleto - la tabla NO se ha tocado
    set /a ERRORES+=1
    set RECREAR_FALLO=1
    goto :eof
)

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%DATOS%\create_%TABLA%.sql" > nul 2>&1

REM --- Comprobar que el destino ya tiene el esquema del origen ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -v TABLA="%TABLA%" -i "%SQLDIR%_sync_firma_columnas.sql" -o "%DATOS%\fcol_d.txt" > nul 2>&1
fc /b "%DATOS%\fcol_o.txt" "%DATOS%\fcol_d.txt" > nul 2>&1
if errorlevel 1 (
    echo ERROR: no se pudo aplicar el nuevo esquema en DESTINO
    set /a ERRORES+=1
    set RECREAR_FALLO=1
    goto :eof
)

set ETIQUETA=schema+
set FORZAR=1
goto :eof

REM ============================================
REM FUNCION: sync_indices
REM   Deja en DESTINO la misma PK e indices que tiene el ORIGEN.
REM   Se ejecuta despues de cargar los datos para no ralentizar el BCP.
REM   Un fallo aqui no invalida los datos: se marca con [idx?].
REM ============================================
:sync_indices
set IDXTAG=
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -v TABLA="%TABLA%" -i "%SQLDIR%_sync_firma_indices.sql" -o "%DATOS%\fidx_o.txt" > nul 2>&1
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -v TABLA="%TABLA%" -i "%SQLDIR%_sync_firma_indices.sql" -o "%DATOS%\fidx_d.txt" > nul 2>&1

fc /b "%DATOS%\fidx_o.txt" "%DATOS%\fidx_d.txt" > nul 2>&1
if not errorlevel 1 goto :eof

if exist "%DATOS%\index_%TABLA%.sql" del "%DATOS%\index_%TABLA%.sql" > nul 2>&1
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -v TABLA="%TABLA%" -i "%SQLDIR%_sync_gen_indices.sql" -o "%DATOS%\index_%TABLA%.sql" > nul 2>&1

findstr /C:"-- FIN_SCRIPT_OK" "%DATOS%\index_%TABLA%.sql" > nul 2>&1
if errorlevel 1 (
    set IDXTAG=+idx?
    goto :eof
)

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%DATOS%\index_%TABLA%.sql" > nul 2>&1

REM --- Comprobar que han quedado igual que en el origen ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -v TABLA="%TABLA%" -i "%SQLDIR%_sync_firma_indices.sql" -o "%DATOS%\fidx_d.txt" > nul 2>&1
fc /b "%DATOS%\fidx_o.txt" "%DATOS%\fidx_d.txt" > nul 2>&1
if errorlevel 1 (
    set IDXTAG=+idx?
    goto :eof
)
set IDXTAG=+idx
goto :eof

REM ============================================
REM FUNCION: sync_blob (tablas con imagenes / PDF)
REM   Compara COUNT en lugar de CHECKSUM para no leer los blobs.
REM   Si el esquema del ORIGEN ha cambiado AVISA pero NO reconstruye la
REM   tabla: eso obligaria a volver a transferir todos los blobs. Cuando
REM   salga el aviso hay que ajustar la tabla a mano y relanzar.
REM ============================================
:sync_blob
set TABLA=%~1
set AVISOTAG=
<nul set /p="     %TABLA%... "

REM --- Aviso si el esquema del origen ha cambiado ---
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -v TABLA="%TABLA%" -i "%SQLDIR%_sync_firma_columnas.sql" -o "%DATOS%\fcol_o.txt" > nul 2>&1
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -v TABLA="%TABLA%" -i "%SQLDIR%_sync_firma_columnas.sql" -o "%DATOS%\fcol_d.txt" > nul 2>&1
fc /b "%DATOS%\fcol_o.txt" "%DATOS%\fcol_d.txt" > nul 2>&1
if errorlevel 1 set AVISOTAG= [AVISO: esquema distinto del origen]

REM --- Filas en ORIGEN ---
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

REM --- Filas en DESTINO ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"

if "!CNT_O!"=="!CNT_D!" (
    echo !CNT_O! registros [=]!AVISOTAG!
    goto :eof
)

echo sincronizando...
<nul set /p="                              exportando... "
bcp "SELECT * FROM %BD%.dbo.%TABLA% WITH (NOLOCK)" queryout "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
echo OK
<nul set /p="                              importando... "
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "TRUNCATE TABLE dbo.%TABLA%" > nul 2>&1
bcp %BD%.dbo.%TABLA% in "%DATOS%\%TABLA%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n > nul 2>&1

REM --- Verificar que se han cargado todas las filas ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.%TABLA% WITH (NOLOCK)" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"
if not "!CNT_O!"=="!CNT_D!" (
    echo ERROR: la carga ha fallado - ORIGEN=!CNT_O! DESTINO=!CNT_D!!AVISOTAG!
    set /a ERRORES+=1
    goto :eof
)
echo OK [!CNT_D! registros] [sync]!AVISOTAG!
goto :eof

REM ============================================
REM FUNCION: sync_venped (solo pedidos que tienen lineas)
REM   Mismo control de esquema, indices y verificacion de filas.
REM ============================================
:sync_venped
set TABLA=venped
set IDXTAG=
set RECREAR_FALLO=
<nul set /p="     venped (con lineas)... "

REM --- Esquema de columnas en ORIGEN ---
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -v TABLA="venped" -i "%SQLDIR%_sync_firma_columnas.sql" -o "%DATOS%\fcol_o.txt" > nul 2>&1
set TAM_O=0
for %%A in ("%DATOS%\fcol_o.txt") do set TAM_O=%%~zA
if !TAM_O! LSS 5 (
    echo ERROR: no se pudo leer el esquema del ORIGEN - tabla omitida
    set /a ERRORES+=1
    goto :eof
)

REM --- Esquema de columnas en DESTINO ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -v TABLA="venped" -i "%SQLDIR%_sync_firma_columnas.sql" -o "%DATOS%\fcol_d.txt" > nul 2>&1

fc /b "%DATOS%\fcol_o.txt" "%DATOS%\fcol_d.txt" > nul 2>&1
if errorlevel 1 call :recrear_tabla
if "!RECREAR_FALLO!"=="1" goto :eof

REM --- Filas que se van a copiar (solo pedidos con lineas) ---
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM %BD%.dbo.venped WITH (NOLOCK) WHERE pedido IN (SELECT venliped.pedido FROM %BD%.dbo.venliped WITH (NOLOCK) WHERE venliped.empresa = venped.empresa AND venliped.anyo = venped.anyo)" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

bcp "SELECT * FROM %BD%.dbo.venped WITH (NOLOCK) WHERE pedido IN (SELECT venliped.pedido FROM %BD%.dbo.venliped WITH (NOLOCK) WHERE venliped.empresa = venped.empresa AND venliped.anyo = venped.anyo)" queryout "%DATOS%\venped.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "TRUNCATE TABLE dbo.venped" > nul 2>&1
bcp %BD%.dbo.venped in "%DATOS%\venped.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n > nul 2>&1

REM --- Verificar que se han cargado todas las filas ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.venped WITH (NOLOCK)" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"
if not "!CNT_O!"=="!CNT_D!" (
    echo ERROR: la carga ha fallado - ORIGEN=!CNT_O! DESTINO=!CNT_D!
    set /a ERRORES+=1
    goto :eof
)

call :sync_indices
echo !CNT_D! registros [sync!IDXTAG!]
goto :eof
