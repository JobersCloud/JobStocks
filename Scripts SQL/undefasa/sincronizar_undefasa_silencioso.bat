@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
REM ============================================
REM Script: sincronizar_undefasa_silencioso.bat
REM Sincronizacion SIN MENSAJES (Tarea Programada)
REM ORIGEN:  192.168.0.73 / euro
REM DESTINO: 192.168.0.50 / Undefasa
REM BCP usa -w (compatible 2008 a 2025)
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

REM Verificar conexiones
"!SQLCMD170!" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -Q "SELECT 1" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 exit /b 1
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -Q "SELECT 1" -h -1 -W -C > nul 2>&1
if %ERRORLEVEL% NEQ 0 exit /b 1

REM Tablas normales
call :st empresas
call :st unidades
call :st formatos
call :st calidades
call :st almmodelos
call :st almcolores
call :st pallets
call :st articulos
call :st almalmacen
call :st almubimapa
call :st almlinubica
call :st almlinubica_bloqueo
call :st almartcajas
call :st palarticulo
call :st almcajas
call :st almartcal
REM call :st almarttonopeso
call :st venliped
call :sv
call :st genter
call :st paises
call :st provincias
call :st tono
call :st calibre
call :st ean13
call :st almartpallet

REM Tablas con blobs
REM call :st articulo_ficha_tecnica
REM call :st articulo_ficha_tecnica_tono

REM Imagenes
call :si

REM Vaciar log
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "DECLARE @logName NVARCHAR(128); SELECT @logName = name FROM sys.master_files WHERE database_id = DB_ID('%BD_DESTINO%') AND type_desc = 'LOG'; ALTER DATABASE %BD_DESTINO% SET RECOVERY SIMPLE; DBCC SHRINKFILE (@logName, 1); ALTER DATABASE %BD_DESTINO% SET RECOVERY FULL;" > nul 2>&1

REM Registrar fecha
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d ApiRestStocks -C -Q "UPDATE parametros SET valor = CONVERT(VARCHAR(19), GETDATE(), 120), fecha_modificacion = GETDATE() WHERE clave = 'FECHA_ULTIMA_SINCRONIZACION'" > nul 2>&1

exit /b 0

REM ============================================
REM :st - Sync tabla
REM ============================================
:st
set T=%~1
"!SQLCMD170!" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='%T%' AND TABLE_SCHEMA='dbo'" > "%DATOS%\so.txt" 2>nul
set /p SO=<"%DATOS%\so.txt"
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; IF OBJECT_ID('dbo.%T%','U') IS NULL SELECT '0' ELSE SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='%T%' AND TABLE_SCHEMA='dbo'" > "%DATOS%\sd.txt" 2>nul
set /p SD=<"%DATOS%\sd.txt"
if NOT "!SO!"=="!SD!" call :cr %T%
"!SQLCMD170!" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -W -Q "SET NOCOUNT ON; SELECT ISNULL(CHECKSUM_AGG(BINARY_CHECKSUM(*)),0) FROM dbo.%T% WITH (NOLOCK)" > "%DATOS%\co.txt" 2>nul
set /p CO=<"%DATOS%\co.txt"
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; SELECT ISNULL(CHECKSUM_AGG(BINARY_CHECKSUM(*)),0) FROM dbo.%T% WITH (NOLOCK)" > "%DATOS%\cd.txt" 2>nul
set /p CD=<"%DATOS%\cd.txt"
if "!CO!"=="!CD!" goto :eof
"!BCP170!" "SELECT * FROM %BD_ORIGEN%.dbo.%T% WITH (NOLOCK)" queryout "%DATOS%\%T%.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -w > nul 2>&1
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.%T%" > nul 2>&1
"!BCP170!" %BD_DESTINO%.dbo.%T% in "%DATOS%\%T%.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -w > nul 2>&1
goto :eof

REM ============================================
REM :cr - Create tabla en destino desde esquema origen
REM ============================================
:cr
set TR=%~1
"!SQLCMD170!" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -y 8000 -o "%DATOS%\create_%TR%.sql" -Q "SET NOCOUNT ON; DECLARE @cols NVARCHAR(MAX) = ''; SELECT @cols = @cols + ', ' + QUOTENAME(COLUMN_NAME) + ' ' + DATA_TYPE + CASE WHEN DATA_TYPE IN ('char','varchar','nchar','nvarchar') THEN '(' + CASE WHEN CHARACTER_MAXIMUM_LENGTH = -1 THEN 'MAX' ELSE CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR) END + ')' WHEN DATA_TYPE IN ('decimal','numeric') THEN '(' + CAST(NUMERIC_PRECISION AS VARCHAR) + ',' + CAST(NUMERIC_SCALE AS VARCHAR) + ')' ELSE '' END + ' NULL' FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '%TR%' AND TABLE_SCHEMA = 'dbo' ORDER BY ORDINAL_POSITION; SET @cols = STUFF(@cols, 1, 2, ''); SELECT 'IF OBJECT_ID(''dbo.%TR%'',''U'') IS NOT NULL DROP TABLE dbo.%TR%; CREATE TABLE dbo.%TR% (' + @cols + ');';" 2>nul
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -i "%DATOS%\create_%TR%.sql" > nul 2>&1
goto :eof

REM ============================================
REM :sv - Sync venped
REM ============================================
:sv
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -Q "SET NOCOUNT ON; IF OBJECT_ID('dbo.venped','U') IS NULL SELECT 'NOTABLE' ELSE SELECT '0'" > "%DATOS%\cd.txt" 2>nul
set /p CD=<"%DATOS%\cd.txt"
if "!CD!"=="NOTABLE" call :cr venped
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "TRUNCATE TABLE dbo.venped" > nul 2>&1
"!BCP170!" "SELECT * FROM %BD_ORIGEN%.dbo.venped WITH (NOLOCK) WHERE pedido IN (SELECT venliped.pedido FROM %BD_ORIGEN%.dbo.venliped WITH (NOLOCK) WHERE venliped.empresa = venped.empresa AND venliped.anyo = venped.anyo)" queryout "%DATOS%\venped.bcp" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -w > nul 2>&1
"!BCP170!" %BD_DESTINO%.dbo.venped in "%DATOS%\venped.bcp" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -w > nul 2>&1
goto :eof

REM ============================================
REM :si - Sync imagenes (solo nuevas, solo @1, solo web='S', reducidas)
REM ============================================
:si
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -C -Q "IF OBJECT_ID('dbo.ps_articulo_imagen','U') IS NULL CREATE TABLE dbo.ps_articulo_imagen (id numeric(18,0) IDENTITY(1,1) NOT NULL, empresa varchar(5) NULL, articulo varchar(20) NULL, foto image NULL, predeterminada int NULL, width_thumbnail int NULL, height_thumbnail int NULL, thumbnail image NULL, nombre varchar(100) NULL, web_id numeric(18,0) NULL);" > nul 2>&1
"!SQLCMD170!" -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD_ORIGEN% -h -1 -W -o "%DATOS%\articulos_web.txt" -Q "SET NOCOUNT ON; SELECT RTRIM(codigo) FROM dbo.articulos WITH (NOLOCK) WHERE web = 'S'"
"!SQLCMD170!" -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P"!PW_DEST!" -d %BD_DESTINO% -h -1 -W -C -o "%DATOS%\imagenes_existentes.txt" -Q "SET NOCOUNT ON; SELECT RTRIM(nombre) FROM dbo.ps_articulo_imagen"
powershell -ExecutionPolicy Bypass -Command ^
 "$webCodes = Get-Content '%DATOS%\articulos_web.txt' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }; " ^
 "$webSet = New-Object System.Collections.Generic.HashSet[string]; " ^
 "foreach ($c in $webCodes) { [void]$webSet.Add($c) }; " ^
 "$existentes = Get-Content '%DATOS%\imagenes_existentes.txt' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }; " ^
 "$existSet = New-Object System.Collections.Generic.HashSet[string]; " ^
 "foreach ($e in $existentes) { [void]$existSet.Add($e) }; " ^
 "$connStr = 'Server=%SERVIDOR_DESTINO%;Database=%BD_DESTINO%;User Id=%USUARIO_DESTINO%;Password=!PW_DEST!;TrustServerCertificate=True;Connection Timeout=30'; " ^
 "$conn = New-Object System.Data.SqlClient.SqlConnection($connStr); " ^
 "$conn.Open(); " ^
 "Add-Type -AssemblyName System.Drawing; " ^
 "$files = Get-ChildItem -Path '%RUTA_IMAGENES%*@1.jpg' -File; " ^
 "$nuevas = 0; $saltadas = 0; $maxWidth = 800; " ^
 "foreach ($f in $files) { " ^
 "  $codigo = $f.BaseName.Split('@')[0]; " ^
 "  if (-not $webSet.Contains($codigo)) { continue }; " ^
 "  if ($existSet.Contains($f.Name)) { $saltadas++; continue }; " ^
 "  $nuevas++; " ^
 "  try { " ^
 "    $img = [System.Drawing.Image]::FromFile($f.FullName); " ^
 "    if ($img.Width -gt $maxWidth) { " ^
 "      $ratio = $maxWidth / $img.Width; " ^
 "      $newH = [int]($img.Height * $ratio); " ^
 "      $bmp = New-Object System.Drawing.Bitmap($maxWidth, $newH); " ^
 "      $g = [System.Drawing.Graphics]::FromImage($bmp); " ^
 "      $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic; " ^
 "      $g.DrawImage($img, 0, 0, $maxWidth, $newH); " ^
 "      $g.Dispose(); $img.Dispose(); " ^
 "      $ms = New-Object System.IO.MemoryStream; " ^
 "      $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Jpeg); " ^
 "      $bytes = $ms.ToArray(); $ms.Dispose(); $bmp.Dispose(); " ^
 "    } else { " ^
 "      $img.Dispose(); " ^
 "      $bytes = [System.IO.File]::ReadAllBytes($f.FullName); " ^
 "    } " ^
 "  } catch { $bytes = [System.IO.File]::ReadAllBytes($f.FullName) }; " ^
 "  $cmd = $conn.CreateCommand(); " ^
 "  $cmd.CommandTimeout = 300; " ^
 "  $cmd.CommandText = 'INSERT INTO dbo.ps_articulo_imagen (empresa, articulo, foto, nombre) VALUES (@e, @a, @f, @n)'; " ^
 "  [void]$cmd.Parameters.AddWithValue('@e', '%EMPRESA_ID%'); " ^
 "  [void]$cmd.Parameters.AddWithValue('@a', $codigo); " ^
 "  $p = $cmd.Parameters.Add('@f', [System.Data.SqlDbType]::Image); $p.Value = $bytes; " ^
 "  [void]$cmd.Parameters.AddWithValue('@n', $f.Name); " ^
 "  $cmd.ExecuteNonQuery() ^| Out-Null; " ^
 "} " ^
 "$conn.Close();"
goto :eof
