@echo off
chcp 65001 > nul
REM ============================================
REM Script: diagnostico_tabla.bat
REM Muestra PKs e indices de una tabla en ORIGEN y DESTINO
REM Uso: diagnostico_tabla.bat [nombre_tabla]
REM ============================================

SET SERVIDOR_ORIGEN=192.168.100.5
SET SERVIDOR_DESTINO=10.1.99.4
SET BD=cristal

SET USUARIO_ORIGEN=sa
SET CLAVE_ORIGEN=desa2012

SET USUARIO_DESTINO=sa
SET CLAVE_DESTINO=Crijob2015Desa

SET TABLA=%1
if "%TABLA%"=="" SET TABLA=almlinubica

cls
echo.
echo ============================================
echo    DIAGNOSTICO DE TABLA: %TABLA%
echo ============================================
echo.

echo ============================================
echo ORIGEN (%SERVIDOR_ORIGEN%)
echo ============================================
echo.
echo --- PRIMARY KEY ---
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT i.name AS PK_Name, CASE WHEN i.type = 1 THEN 'CLUSTERED' ELSE 'NONCLUSTERED' END AS Tipo, STUFF((SELECT ', ' + c.name FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') AS Columnas FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name = '%TABLA%'" -W -s" | "
echo.
echo --- INDICES ---
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT i.name AS Index_Name, CASE WHEN i.type = 1 THEN 'CLUSTERED' WHEN i.type = 2 THEN 'NONCLUSTERED' ELSE 'OTRO' END AS Tipo, CASE WHEN i.is_unique = 1 THEN 'SI' ELSE 'NO' END AS Unico, STUFF((SELECT ', ' + c.name FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0 ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') AS Columnas FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name = '%TABLA%' ORDER BY i.name" -W -s" | "
echo.
echo --- REGISTROS ---
sqlcmd -S %SERVIDOR_ORIGEN% -U %USUARIO_ORIGEN% -P %CLAVE_ORIGEN% -d %BD% -Q "SET NOCOUNT ON; SELECT COUNT(*) AS Total FROM dbo.%TABLA%" -W -h -1

echo.
echo ============================================
echo DESTINO (%SERVIDOR_DESTINO%)
echo ============================================
echo.
echo --- PRIMARY KEY ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT i.name AS PK_Name, CASE WHEN i.type = 1 THEN 'CLUSTERED' ELSE 'NONCLUSTERED' END AS Tipo, STUFF((SELECT ', ' + c.name FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') AS Columnas FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.is_primary_key = 1 AND t.name = '%TABLA%'" -W -s" | "
echo.
echo --- INDICES ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT i.name AS Index_Name, CASE WHEN i.type = 1 THEN 'CLUSTERED' WHEN i.type = 2 THEN 'NONCLUSTERED' ELSE 'OTRO' END AS Tipo, CASE WHEN i.is_unique = 1 THEN 'SI' ELSE 'NO' END AS Unico, STUFF((SELECT ', ' + c.name FROM sys.index_columns ic JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0 ORDER BY ic.key_ordinal FOR XML PATH('')), 1, 2, '') AS Columnas FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND t.name = '%TABLA%' ORDER BY i.name" -W -s" | "
echo.
echo --- REGISTROS ---
sqlcmd -S %SERVIDOR_DESTINO% -U %USUARIO_DESTINO% -P %CLAVE_DESTINO% -d %BD% -Q "SET NOCOUNT ON; SELECT COUNT(*) AS Total FROM dbo.%TABLA%" -W -h -1

echo.
echo ============================================
pause
