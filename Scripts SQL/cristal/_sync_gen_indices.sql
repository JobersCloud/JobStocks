-- ============================================================================
-- _sync_gen_indices.sql
-- Genera el script que replica en DESTINO la PK y los indices del ORIGEN.
-- Se ejecuta SOLO en ORIGEN y su salida se guarda en un .sql que despues se
-- ejecuta en DESTINO.
--
-- El script generado primero borra TODOS los indices/PK que tenga la tabla en
-- destino (bloque dinamico que se evalua alli) y despues los crea igual que en
-- origen. Termina con el centinela "-- FIN_SCRIPT_OK".
--
-- No replica indices filtrados ni opciones de indice (FILLFACTOR, etc.):
-- el ERP no los usa en estas tablas.
--
-- Parametro: -v TABLA="nombre_tabla"
-- ============================================================================
SET NOCOUNT ON;

WITH idx AS (
    SELECT
        i.object_id,
        i.index_id,
        i.name,
        i.type,
        i.type_desc,
        i.is_primary_key,
        i.is_unique,
        ROW_NUMBER() OVER (ORDER BY i.type, (i.name COLLATE Latin1_General_BIN)) AS rk,
        (SELECT COUNT(*) FROM sys.index_columns ic2
         WHERE ic2.object_id = i.object_id AND ic2.index_id = i.index_id
           AND ic2.is_included_column = 1) AS n_incluidas
    FROM sys.indexes i
    WHERE i.object_id = OBJECT_ID('dbo.$(TABLA)')
      AND i.type > 0
      AND i.has_filter = 0
)
SELECT linea
FROM (
    -- Bloque de borrado (se evalua en DESTINO)
    SELECT 0 AS orden1, 1 AS orden2, 0 AS orden3,
           CAST('DECLARE @drop NVARCHAR(MAX) = N'''';' AS VARCHAR(250)) AS linea
    UNION ALL SELECT 0, 2, 0, CAST('SELECT @drop = @drop + CASE WHEN i.is_primary_key = 1' AS VARCHAR(250))
    UNION ALL SELECT 0, 3, 0, CAST('    THEN N''ALTER TABLE dbo.$(TABLA) DROP CONSTRAINT '' + QUOTENAME(i.name) + N'';''' AS VARCHAR(250))
    UNION ALL SELECT 0, 4, 0, CAST('    ELSE N''DROP INDEX '' + QUOTENAME(i.name) + N'' ON dbo.$(TABLA);'' END' AS VARCHAR(250))
    UNION ALL SELECT 0, 5, 0, CAST('FROM sys.indexes i WHERE i.object_id = OBJECT_ID(''dbo.$(TABLA)'') AND i.type > 0;' AS VARCHAR(250))
    UNION ALL SELECT 0, 6, 0, CAST('IF @drop <> N'''' EXEC sp_executesql @drop;' AS VARCHAR(250))
    UNION ALL SELECT 0, 7, 0, CAST('GO' AS VARCHAR(250))

    -- Cabecera de cada indice
    UNION ALL
    SELECT rk, 1, 0,
        CAST(CASE WHEN is_primary_key = 1
             THEN 'ALTER TABLE dbo.$(TABLA) ADD CONSTRAINT '
                  + QUOTENAME(name COLLATE DATABASE_DEFAULT)
                  + ' PRIMARY KEY ' + (type_desc COLLATE DATABASE_DEFAULT)
             ELSE 'CREATE ' + CASE WHEN is_unique = 1 THEN 'UNIQUE ' ELSE '' END
                  + (type_desc COLLATE DATABASE_DEFAULT) + ' INDEX '
                  + QUOTENAME(name COLLATE DATABASE_DEFAULT) + ' ON dbo.$(TABLA)'
             END AS VARCHAR(250))
    FROM idx

    UNION ALL SELECT rk, 2, 0, CAST('(' AS VARCHAR(250)) FROM idx

    -- Columnas clave
    UNION ALL
    SELECT i.rk, 3, ic.key_ordinal,
        CAST(CASE WHEN ic.key_ordinal = 1 THEN '  ' ELSE ' ,' END
             + QUOTENAME(c.name COLLATE DATABASE_DEFAULT)
             + CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END
             AS VARCHAR(250))
    FROM idx i
    JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
    JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
    WHERE ic.is_included_column = 0

    UNION ALL SELECT rk, 4, 0, CAST(')' AS VARCHAR(250)) FROM idx

    -- Columnas incluidas (solo indices que no son PK)
    UNION ALL SELECT rk, 5, 0, CAST('INCLUDE (' AS VARCHAR(250))
        FROM idx WHERE is_primary_key = 0 AND n_incluidas > 0

    UNION ALL
    SELECT i.rk, 6, ic.index_column_id,
        CAST(CASE WHEN ic.index_column_id = (SELECT MIN(ic3.index_column_id)
                                             FROM sys.index_columns ic3
                                             WHERE ic3.object_id = i.object_id
                                               AND ic3.index_id = i.index_id
                                               AND ic3.is_included_column = 1)
                  THEN '  ' ELSE ' ,' END
             + QUOTENAME(c.name COLLATE DATABASE_DEFAULT) AS VARCHAR(250))
    FROM idx i
    JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
    JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
    WHERE ic.is_included_column = 1 AND i.is_primary_key = 0

    UNION ALL SELECT rk, 7, 0, CAST(')' AS VARCHAR(250))
        FROM idx WHERE is_primary_key = 0 AND n_incluidas > 0

    UNION ALL SELECT rk, 8, 0, CAST(';' AS VARCHAR(250)) FROM idx
    UNION ALL SELECT rk, 9, 0, CAST('GO' AS VARCHAR(250)) FROM idx

    UNION ALL SELECT 999999, 0, 0, CAST('-- FIN_SCRIPT_OK' AS VARCHAR(250))
) x
ORDER BY orden1, orden2, orden3;
