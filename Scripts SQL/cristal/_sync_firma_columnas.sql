-- ============================================================================
-- _sync_firma_columnas.sql
-- Devuelve la firma del esquema de columnas de una tabla (una linea por columna).
-- Se ejecuta en ORIGEN y en DESTINO y los dos ficheros se comparan con FC.
-- Si difieren, la tabla del destino se reconstruye con la definicion del origen.
-- Parametro: -v TABLA="nombre_tabla"
-- ============================================================================
SET NOCOUNT ON;

SELECT
      CAST(ORDINAL_POSITION AS VARCHAR(5)) + '|'
    + (COLUMN_NAME COLLATE Latin1_General_BIN) + '|'
    + (DATA_TYPE COLLATE Latin1_General_BIN) + '|'
    + CAST(ISNULL(CHARACTER_MAXIMUM_LENGTH, 0) AS VARCHAR(12)) + '|'
    + CAST(ISNULL(NUMERIC_PRECISION, 0) AS VARCHAR(5)) + '|'
    + CAST(ISNULL(NUMERIC_SCALE, 0) AS VARCHAR(5)) + '|'
    + CAST(ISNULL(DATETIME_PRECISION, 0) AS VARCHAR(5)) + '|'
    + (IS_NULLABLE COLLATE Latin1_General_BIN)
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo'
  AND TABLE_NAME = '$(TABLA)'
ORDER BY ORDINAL_POSITION;
