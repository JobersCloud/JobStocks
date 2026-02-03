@echo off
chcp 65001 > nul
REM ============================================
REM Script: verificar_indices_destino.bat
REM Muestra PKs e indices actuales en DESTINO
REM ============================================

SET SERVIDOR_DESTINO=10.1.99.4
SET BD=cristal
SET USUARIO_DESTINO=sa
SET CLAVE_DESTINO=Crijob2015Desa

cls
echo.
echo ============================================
echo    VERIFICAR INDICES EN DESTINO
echo ============================================
echo.
echo    Servidor: %SERVIDOR_DESTINO% / %BD%
echo.
echo ============================================
echo.

echo Verificando conexion...
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SELECT 1" -h -1 -W > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se puede conectar al servidor
    pause
    exit /b 1
)
echo OK
echo.

echo ============================================
echo TABLAS EXISTENTES:
echo ============================================
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT name AS Tabla FROM sys.tables WHERE name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY name" -W
echo.

echo ============================================
echo PRIMARY KEYS:
echo ============================================
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT t.name AS Tabla, i.name AS PK_Name, CASE WHEN i.type = 1 THEN 'CLUSTERED' ELSE 'NONCLUSTERED' END AS Tipo FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name" -W -s" | "
echo.

echo ============================================
echo INDICES (no PKs):
echo ============================================
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT t.name AS Tabla, i.name AS Index_Name, CASE WHEN i.type = 1 THEN 'CLUSTERED' WHEN i.type = 2 THEN 'NONCLUSTERED' ELSE 'OTRO' END AS Tipo FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name IN ('empresas','unidades','formatos','calidades','almmodelos','almcolores','pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas','almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica') ORDER BY t.name, i.name" -W -s" | "
echo.

echo ============================================
echo CONTEO DE REGISTROS:
echo ============================================
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT 'empresas' AS Tabla, COUNT(*) AS Registros FROM dbo.empresas UNION ALL SELECT 'unidades', COUNT(*) FROM dbo.unidades UNION ALL SELECT 'formatos', COUNT(*) FROM dbo.formatos UNION ALL SELECT 'calidades', COUNT(*) FROM dbo.calidades UNION ALL SELECT 'almmodelos', COUNT(*) FROM dbo.almmodelos UNION ALL SELECT 'almcolores', COUNT(*) FROM dbo.almcolores UNION ALL SELECT 'pallets', COUNT(*) FROM dbo.pallets UNION ALL SELECT 'articulos', COUNT(*) FROM dbo.articulos UNION ALL SELECT 'almlinubica', COUNT(*) FROM dbo.almlinubica UNION ALL SELECT 'almartcajas', COUNT(*) FROM dbo.almartcajas UNION ALL SELECT 'palarticulo', COUNT(*) FROM dbo.palarticulo UNION ALL SELECT 'almcajas', COUNT(*) FROM dbo.almcajas UNION ALL SELECT 'almartcal', COUNT(*) FROM dbo.almartcal UNION ALL SELECT 'almarttonopeso', COUNT(*) FROM dbo.almarttonopeso UNION ALL SELECT 'venliped', COUNT(*) FROM dbo.venliped UNION ALL SELECT 'venped', COUNT(*) FROM dbo.venped UNION ALL SELECT 'genter', COUNT(*) FROM dbo.genter UNION ALL SELECT 'ps_articulo_imagen', COUNT(*) FROM dbo.ps_articulo_imagen UNION ALL SELECT 'articulo_ficha', COUNT(*) FROM dbo.articulo_ficha_tecnica" -W -s" | "

echo.
echo ============================================
pause
