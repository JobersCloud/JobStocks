-- ============================================
-- Script: 01_exportar_pks_origen.sql
-- Ejecutar en ORIGEN (192.168.100.5) -> cristal
-- Genera scripts CREATE para PRIMARY KEYS
-- ============================================

USE cristal;
GO

SET NOCOUNT ON;

-- Generar scripts de PRIMARY KEYS
SELECT
    'IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = ''' + i.name + ''' AND object_id = OBJECT_ID(''dbo.' + t.name + ''')) ' +
    'ALTER TABLE [dbo].[' + t.name + '] ADD CONSTRAINT [' + i.name + '] PRIMARY KEY ' +
    CASE WHEN i.type = 1 THEN 'CLUSTERED' ELSE 'NONCLUSTERED' END + ' (' +
    STUFF((
        SELECT ', [' + c.name + ']'
        FROM sys.index_columns ic
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id
        ORDER BY ic.key_ordinal
        FOR XML PATH('')
    ), 1, 2, '') + ');'
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE i.is_primary_key = 1
AND t.name IN (
    'empresas','unidades','formatos','calidades','almmodelos','almcolores',
    'pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas',
    'almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica'
)
ORDER BY t.name;
GO
