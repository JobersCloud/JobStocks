-- ============================================================================
-- _sync_firma_indices.sql
-- Firma de PK e indices de una tabla: una linea por cada columna de cada indice.
-- Se ejecuta en ORIGEN y en DESTINO y los dos ficheros se comparan con FC.
-- Las lineas son cortas a proposito para que sqlcmd -W no las trunque.
-- Parametro: -v TABLA="nombre_tabla"
-- ============================================================================
SET NOCOUNT ON;

SELECT linea
FROM (
    SELECT
        (i.name COLLATE Latin1_General_BIN) AS orden1,
        1 AS orden2,
        ic.key_ordinal AS orden3,
        CAST(
              (i.name COLLATE Latin1_General_BIN) + '|'
            + (i.type_desc COLLATE Latin1_General_BIN)
            + '|pk=' + CAST(i.is_primary_key AS VARCHAR(1))
            + '|uq=' + CAST(i.is_unique AS VARCHAR(1))
            + '|KEY' + CAST(ic.key_ordinal AS VARCHAR(5)) + '='
            + (c.name COLLATE Latin1_General_BIN)
            + CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END
            AS VARCHAR(250)) AS linea
    FROM sys.indexes i
    JOIN sys.index_columns ic
      ON ic.object_id = i.object_id AND ic.index_id = i.index_id
    JOIN sys.columns c
      ON c.object_id = ic.object_id AND c.column_id = ic.column_id
    WHERE i.object_id = OBJECT_ID('dbo.$(TABLA)')
      AND i.type > 0
      AND ic.is_included_column = 0

    UNION ALL

    SELECT
        (i.name COLLATE Latin1_General_BIN),
        2,
        0,
        CAST(
              (i.name COLLATE Latin1_General_BIN)
            + '|INCLUDE=' + (c.name COLLATE Latin1_General_BIN)
            AS VARCHAR(250))
    FROM sys.indexes i
    JOIN sys.index_columns ic
      ON ic.object_id = i.object_id AND ic.index_id = i.index_id
    JOIN sys.columns c
      ON c.object_id = ic.object_id AND c.column_id = ic.column_id
    WHERE i.object_id = OBJECT_ID('dbo.$(TABLA)')
      AND i.type > 0
      AND ic.is_included_column = 1
) x
ORDER BY orden1, orden2, orden3, linea;
