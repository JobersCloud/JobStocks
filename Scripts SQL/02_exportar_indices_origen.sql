-- ============================================
-- Script: 02_exportar_indices_origen.sql
-- Ejecutar en ORIGEN (192.168.100.5) -> cristal
-- Genera scripts CREATE para INDICES (no PKs)
-- ============================================

USE cristal;
GO

SET NOCOUNT ON;

-- Generar scripts de INDICES
SELECT
    'IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = ''' + i.name + ''' AND object_id = OBJECT_ID(''dbo.' + t.name + ''')) ' +
    'CREATE ' +
    CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END +
    CASE WHEN i.type = 1 THEN 'CLUSTERED ' ELSE 'NONCLUSTERED ' END +
    'INDEX [' + i.name + '] ON [dbo].[' + t.name + '] (' +
    STUFF((
        SELECT ', [' + c.name + ']' + CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE '' END
        FROM sys.index_columns ic
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0
        ORDER BY ic.key_ordinal
        FOR XML PATH('')
    ), 1, 2, '') + ')' +
    CASE
        WHEN (SELECT COUNT(*) FROM sys.index_columns ic WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 1) > 0
        THEN ' INCLUDE (' + STUFF((
            SELECT ', [' + c.name + ']'
            FROM sys.index_columns ic
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 1
            ORDER BY ic.key_ordinal
            FOR XML PATH('')
        ), 1, 2, '') + ')'
        ELSE ''
    END + ';'
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE i.type > 0
AND i.is_primary_key = 0
AND i.is_unique_constraint = 0
AND t.name IN (
    'empresas','unidades','formatos','calidades','almmodelos','almcolores',
    'pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas',
    'almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica'
)
ORDER BY t.name, i.name;
GO
