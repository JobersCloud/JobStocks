-- ============================================================================
-- _sync_gen_tabla.sql
-- Genera el script DROP + CREATE TABLE del DESTINO a partir del ORIGEN.
-- Se ejecuta SOLO en ORIGEN y su salida se guarda en un .sql que despues se
-- ejecuta en DESTINO.
--
-- IMPORTANTE: emite una linea por columna (lineas cortas) para que sqlcmd -W
-- no pueda truncarlas, y termina con el centinela "-- FIN_SCRIPT_OK".
-- El .bat SOLO ejecuta el script si encuentra ese centinela, de modo que un
-- script incompleto nunca puede llegar a borrar la tabla del destino.
--
-- Parametro: -v TABLA="nombre_tabla"
-- ============================================================================
SET NOCOUNT ON;

SELECT linea
FROM (
    SELECT 1 AS orden1, 0 AS orden2,
           CAST('IF OBJECT_ID(''dbo.$(TABLA)'',''U'') IS NOT NULL DROP TABLE dbo.$(TABLA);' AS VARCHAR(250)) AS linea
    WHERE EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                  WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '$(TABLA)' AND TABLE_TYPE = 'BASE TABLE')

    UNION ALL
    SELECT 2, 0, CAST('GO' AS VARCHAR(250))
    WHERE EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                  WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '$(TABLA)' AND TABLE_TYPE = 'BASE TABLE')

    UNION ALL
    SELECT 3, 0, CAST('CREATE TABLE dbo.$(TABLA) (' AS VARCHAR(250))
    WHERE EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                  WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '$(TABLA)' AND TABLE_TYPE = 'BASE TABLE')

    UNION ALL
    SELECT 4, ORDINAL_POSITION,
        CAST(
              CASE WHEN ORDINAL_POSITION = 1 THEN '  ' ELSE ' ,' END
            + QUOTENAME(COLUMN_NAME COLLATE DATABASE_DEFAULT) + ' '
            + (DATA_TYPE COLLATE DATABASE_DEFAULT)
            + CASE
                WHEN DATA_TYPE IN ('char','varchar','nchar','nvarchar','binary','varbinary')
                    THEN '(' + CASE WHEN CHARACTER_MAXIMUM_LENGTH = -1
                                    THEN 'MAX'
                                    ELSE CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR(12)) END + ')'
                WHEN DATA_TYPE IN ('decimal','numeric')
                    THEN '(' + CAST(NUMERIC_PRECISION AS VARCHAR(5)) + ','
                             + CAST(NUMERIC_SCALE AS VARCHAR(5)) + ')'
                WHEN DATA_TYPE IN ('datetime2','time','datetimeoffset')
                    THEN '(' + CAST(DATETIME_PRECISION AS VARCHAR(5)) + ')'
                ELSE '' END
            + CASE WHEN IS_NULLABLE = 'YES' THEN ' NULL' ELSE ' NOT NULL' END
            AS VARCHAR(250))
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '$(TABLA)'

    UNION ALL
    SELECT 5, 0, CAST(');' AS VARCHAR(250))
    WHERE EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                  WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '$(TABLA)' AND TABLE_TYPE = 'BASE TABLE')

    UNION ALL
    SELECT 6, 0, CAST('GO' AS VARCHAR(250))
    WHERE EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                  WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '$(TABLA)' AND TABLE_TYPE = 'BASE TABLE')

    UNION ALL
    SELECT 9, 0, CAST('-- FIN_SCRIPT_OK' AS VARCHAR(250))
    WHERE EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                  WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '$(TABLA)' AND TABLE_TYPE = 'BASE TABLE')
) x
ORDER BY orden1, orden2;
