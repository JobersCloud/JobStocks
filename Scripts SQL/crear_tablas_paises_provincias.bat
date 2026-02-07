@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
REM ============================================
REM Script: crear_tablas_paises_provincias.bat
REM Crea las tablas paises y provincias en el
REM servidor DESTINO copiando estructura completa
REM (columnas + PK + indices) y datos del ORIGEN.
REM
REM Usa generar_ddl_tabla.sql para extraer el DDL
REM ============================================

SET SERVIDOR_ORIGEN=192.168.100.5
SET SERVIDOR_DESTINO=10.1.99.4
SET BD=cristal

SET USUARIO_ORIGEN=sa
SET CLAVE_ORIGEN=desa2012

SET USUARIO_DESTINO=sa
SET CLAVE_DESTINO=Crijob2015Desa

SET DATOS=C:\TEMP\sync_cristal
SET SCRIPT_DIR=%~dp0

cls
echo.
echo ============================================
echo    CREAR TABLAS PAISES Y PROVINCIAS
echo ============================================
echo.
echo    ORIGEN:  %SERVIDOR_ORIGEN% / %BD%
echo    DESTINO: %SERVIDOR_DESTINO% / %BD%
echo.
echo ============================================
echo.

if not exist "%DATOS%" mkdir "%DATOS%"

REM Verificar que existe el script SQL
if not exist "%SCRIPT_DIR%generar_ddl_tabla.sql" (
    echo ERROR: No se encuentra generar_ddl_tabla.sql
    echo Debe estar en la misma carpeta que este .bat
    pause
    exit /b 1
)

REM ============================================
REM VERIFICAR CONEXIONES
REM ============================================
echo [1/5] Verificando conexiones...
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
REM GENERAR DDL DESDE ORIGEN
REM ============================================
echo [2/5] Generando estructura desde origen...
echo.

call :generar_ddl paises
call :generar_ddl provincias

echo.

REM ============================================
REM CREAR TABLAS EN DESTINO
REM ============================================
echo [3/5] Creando tablas en destino...
echo.

call :crear_en_destino paises
call :crear_en_destino provincias

echo.

REM ============================================
REM COPIAR DATOS
REM ============================================
echo [4/5] Copiando datos...
echo.

call :copiar_datos paises
call :copiar_datos provincias

echo.

REM ============================================
REM VERIFICAR
REM ============================================
echo [5/5] Verificando...
echo.

call :verificar paises
call :verificar provincias

echo.
echo ============================================
echo COMPLETADO
echo ============================================
echo.
echo Las tablas existen en destino con PK e indices.
echo Las sincronizaciones periodicas las mantendran.
echo.
echo DDL generado en:
echo   %DATOS%\ddl_paises.sql
echo   %DATOS%\ddl_provincias.sql
echo.
pause
exit /b 0

REM ============================================
REM FUNCION: generar_ddl
REM Ejecuta generar_ddl_tabla.sql en ORIGEN
REM y guarda la salida (CREATE TABLE+PK+INDEX)
REM ============================================
:generar_ddl
set T=%~1
<nul set /p="     %T%... "

sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -v TABLA="%T%" -i "%SCRIPT_DIR%generar_ddl_tabla.sql" -h -1 -W > "%DATOS%\ddl_%T%.sql" 2>nul

REM Verificar que se genero algo
for %%A in ("%DATOS%\ddl_%T%.sql") do set FSIZE=%%~zA
if "!FSIZE!"=="" set FSIZE=0
if !FSIZE! LSS 20 (
    echo ERROR - no se genero DDL
    echo     Revisar que la tabla existe en origen
) else (
    echo OK
    type "%DATOS%\ddl_%T%.sql"
    echo.
)
goto :eof

REM ============================================
REM FUNCION: crear_en_destino
REM ============================================
:crear_en_destino
set T=%~1
<nul set /p="     %T%... "

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "IF OBJECT_ID('dbo.%T%') IS NOT NULL DROP TABLE dbo.%T%" > nul 2>&1

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -i "%DATOS%\ddl_%T%.sql" > "%DATOS%\create_%T%_log.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo CREADA
) else (
    echo ERROR
    type "%DATOS%\create_%T%_log.txt"
)
goto :eof

REM ============================================
REM FUNCION: copiar_datos
REM ============================================
:copiar_datos
set T=%~1
<nul set /p="     %T%... "
bcp %BD%.dbo.%T% out "%DATOS%\%T%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -n > nul 2>&1
bcp %BD%.dbo.%T% in "%DATOS%\%T%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -n > nul 2>&1
echo OK
goto :eof

REM ============================================
REM FUNCION: verificar
REM ============================================
:verificar
set T=%~1
<nul set /p="     %T%... "

sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.%T%" > "%DATOS%\cnt_o.txt" 2>nul
set /p CNT_O=<"%DATOS%\cnt_o.txt"

sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.%T%" > "%DATOS%\cnt_d.txt" 2>nul
set /p CNT_D=<"%DATOS%\cnt_d.txt"

if "!CNT_O!"=="!CNT_D!" (
    echo !CNT_O! origen = !CNT_D! destino [OK]
) else (
    echo !CNT_O! origen / !CNT_D! destino [DIFERENCIA!]
)
goto :eof
