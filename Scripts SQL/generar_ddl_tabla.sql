-- ============================================
-- Script: generar_ddl_tabla.sql
-- Genera DDL completo (CREATE TABLE + PK + INDICES)
-- para una tabla pasada como variable $(TABLA)
-- Uso: sqlcmd -v TABLA="paises" -i generar_ddl_tabla.sql
-- ============================================
SET NOCOUNT ON;

DECLARE @tabla NVARCHAR(128) = '$(TABLA)';
DECLARE @obj_id INT = OBJECT_ID('dbo.' + @tabla);

IF @obj_id IS NULL BEGIN
    PRINT '-- ERROR: tabla dbo.' + @tabla + ' no encontrada';
    RETURN;
END

-- ==============================
-- 1. CREATE TABLE con columnas
-- ==============================
DECLARE @cols NVARCHAR(MAX) = '';

SELECT @cols = @cols
    + CASE WHEN @cols != '' THEN ', ' ELSE '' END
    + c.name + ' ' + tp.name
    + CASE
        WHEN tp.name IN ('varchar','nvarchar','char','nchar','varbinary')
            THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX'
                 ELSE CAST(CASE WHEN tp.name IN ('nvarchar','nchar') THEN c.max_length / 2
                           ELSE c.max_length END AS VARCHAR(10))
                 END + ')'
        WHEN tp.name IN ('decimal','numeric')
            THEN '(' + CAST(c.precision AS VARCHAR(10)) + ',' + CAST(c.scale AS VARCHAR(10)) + ')'
        ELSE ''
      END
    + CASE WHEN c.is_identity = 1 THEN ' IDENTITY(1,1)' ELSE '' END
    + CASE WHEN c.is_nullable = 0 THEN ' NOT NULL' ELSE ' NULL' END
FROM sys.columns c
JOIN sys.types tp ON c.user_type_id = tp.user_type_id
WHERE c.object_id = @obj_id
ORDER BY c.column_id;

PRINT 'CREATE TABLE dbo.' + @tabla + ' (' + @cols + ');';
PRINT 'GO';

-- ==============================
-- 2. PRIMARY KEY
-- ==============================
DECLARE @pk_name NVARCHAR(128) = NULL;
DECLARE @pk_cols NVARCHAR(MAX) = '';
DECLARE @pk_idx INT;

SELECT @pk_name = i.name, @pk_idx = i.index_id
FROM sys.indexes i
WHERE i.object_id = @obj_id AND i.is_primary_key = 1;

IF @pk_name IS NOT NULL BEGIN
    SELECT @pk_cols = @pk_cols
        + CASE WHEN @pk_cols != '' THEN ', ' ELSE '' END
        + c.name
    FROM sys.index_columns ic
    JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    WHERE ic.object_id = @obj_id AND ic.index_id = @pk_idx
    ORDER BY ic.key_ordinal;

    PRINT 'ALTER TABLE dbo.' + @tabla + ' ADD CONSTRAINT ' + @pk_name + ' PRIMARY KEY (' + @pk_cols + ');';
    PRINT 'GO';
END

-- ==============================
-- 3. INDICES (no PK)
-- ==============================
DECLARE @idx_name NVARCHAR(128), @idx_id INT, @idx_unique BIT;

DECLARE idx_cursor CURSOR LOCAL FAST_FORWARD FOR
    SELECT i.name, i.index_id, i.is_unique
    FROM sys.indexes i
    WHERE i.object_id = @obj_id
      AND i.is_primary_key = 0
      AND i.type > 0
      AND i.name IS NOT NULL
    ORDER BY i.index_id;

OPEN idx_cursor;
FETCH NEXT FROM idx_cursor INTO @idx_name, @idx_id, @idx_unique;

WHILE @@FETCH_STATUS = 0 BEGIN
    DECLARE @idx_cols NVARCHAR(MAX) = '';

    SELECT @idx_cols = @idx_cols
        + CASE WHEN @idx_cols != '' THEN ', ' ELSE '' END
        + c.name
    FROM sys.index_columns ic
    JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    WHERE ic.object_id = @obj_id AND ic.index_id = @idx_id
    ORDER BY ic.key_ordinal;

    PRINT 'CREATE '
        + CASE WHEN @idx_unique = 1 THEN 'UNIQUE ' ELSE '' END
        + 'INDEX ' + @idx_name + ' ON dbo.' + @tabla + ' (' + @idx_cols + ');';
    PRINT 'GO';

    FETCH NEXT FROM idx_cursor INTO @idx_name, @idx_id, @idx_unique;
END

CLOSE idx_cursor;
DEALLOCATE idx_cursor;
