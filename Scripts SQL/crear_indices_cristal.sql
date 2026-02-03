-- ============================================
-- Script: crear_indices_cristal.sql
-- Genera y ejecuta los índices y PKs para las tablas de cristal
-- Ejecutar en: 10.1.99.4 -> cristal
-- ============================================

USE cristal;
GO

PRINT '============================================';
PRINT 'CREANDO PRIMARY KEYS E INDICES';
PRINT '============================================';
PRINT '';

-- ============================================
-- PASO 1: Generar script de PKs desde ORIGEN
-- Ejecutar esta consulta en el servidor ORIGEN (192.168.100.5)
-- y copiar el resultado aquí
-- ============================================

-- Para ver las PKs que existen en ORIGEN, ejecuta esto en 192.168.100.5:
/*
SELECT
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
*/

-- ============================================
-- PASO 2: Generar script de INDICES desde ORIGEN
-- Ejecutar esta consulta en el servidor ORIGEN (192.168.100.5)
-- y copiar el resultado aquí
-- ============================================

-- Para ver los índices que existen en ORIGEN, ejecuta esto en 192.168.100.5:
/*
SELECT
    'CREATE ' +
    CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END +
    CASE WHEN i.type = 1 THEN 'CLUSTERED ' ELSE 'NONCLUSTERED ' END +
    'INDEX [' + i.name + '] ON [dbo].[' + t.name + '] (' +
    STUFF((
        SELECT ', [' + c.name + ']' + CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END
        FROM sys.index_columns ic
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0
        ORDER BY ic.key_ordinal
        FOR XML PATH('')
    ), 1, 2, '') + ');'
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
*/

-- ============================================
-- VERIFICAR QUÉ HAY ACTUALMENTE EN DESTINO
-- ============================================
PRINT 'PRIMARY KEYS actuales en DESTINO:';
SELECT t.name AS Tabla, i.name AS PK_Name
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE i.is_primary_key = 1
AND t.name IN (
    'empresas','unidades','formatos','calidades','almmodelos','almcolores',
    'pallets','articulos','almlinubica','almartcajas','palarticulo','almcajas',
    'almartcal','almarttonopeso','venliped','venped','genter','ps_articulo_imagen','articulo_ficha_tecnica'
)
ORDER BY t.name;

PRINT '';
PRINT 'INDICES actuales en DESTINO:';
SELECT t.name AS Tabla, i.name AS Index_Name, i.type_desc AS Tipo
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

PRINT '';
PRINT '============================================';
PRINT 'FIN DE VERIFICACION';
PRINT '============================================';
GO
