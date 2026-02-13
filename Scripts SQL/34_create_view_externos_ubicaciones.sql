-- ============================================================================
-- Script: 34_create_view_externos_ubicaciones.sql
-- Descripción: Vista para consulta de stock por ubicación de almacén
-- Fecha: 2026-02-12
-- Origen: cristal.dbo.almlinubica
-- ============================================================================

USE ApiRestStocks;
GO

-- Crear o reemplazar vista de ubicaciones
IF EXISTS (SELECT 1 FROM sys.views WHERE name = 'view_externos_ubicaciones')
BEGIN
    DROP VIEW view_externos_ubicaciones;
    PRINT 'Vista view_externos_ubicaciones eliminada para recrear';
END
GO

CREATE VIEW [dbo].[view_externos_ubicaciones]
AS
SELECT
    u.empresa,
    u.almacen,
    u.zona,
    u.fila,
    u.altura,
    u.linea,
    u.articulo AS codigo,
    a.descripcion,
    f.abreviado AS formato,
    m.descripcion AS serie,
    cal.abreviado AS calidad,
    u.tono,
    u.tonochar,
    u.calibre,
    u.existencias,
    u.ubicacion,
    u.tipo_unidad AS unidad,
    u.referencia,
    u.tipo_pallet,
    p.resumido AS pallet,
    u.caja,
    u.sector,
    u.externo,
    u.f_alta,
    u.preferencia_carga
FROM cristal.dbo.almlinubica u
    LEFT OUTER JOIN cristal.dbo.articulos a
        ON u.empresa = a.empresa
        AND u.articulo = a.codigo
    LEFT OUTER JOIN cristal.dbo.formatos f
        ON a.empresa = f.empresa
        AND a.formato = f.codigo
    LEFT OUTER JOIN cristal.dbo.almmodelos m
        ON a.empresa = m.empresa
        AND a.modelo = m.modelo
    LEFT OUTER JOIN cristal.dbo.calidades cal
        ON u.empresa = cal.empresa
        AND u.calidad = cal.codigo
    LEFT OUTER JOIN cristal.dbo.pallets p
        ON u.empresa = p.empresa
        AND u.tipo_pallet = p.codigo
WHERE u.existencias > 0;
GO

PRINT 'Vista view_externos_ubicaciones creada correctamente';
GO

-- Verificar datos de la vista
SELECT TOP 10
    empresa,
    almacen,
    ubicacion,
    codigo,
    descripcion,
    formato,
    calidad,
    tonochar,
    calibre,
    existencias,
    pallet
FROM view_externos_ubicaciones
ORDER BY empresa, almacen, ubicacion;
GO

PRINT '============================================================================';
PRINT 'Script completado exitosamente';
PRINT 'Vista: view_externos_ubicaciones';
PRINT 'Origen: cristal.dbo.almlinubica + JOINs descriptivos';
PRINT 'Campos principales: empresa, almacen, zona, fila, altura, ubicacion,';
PRINT '  codigo, descripcion, formato, serie, calidad, tono/tonochar, calibre,';
PRINT '  existencias, referencia, tipo_pallet, pallet, caja, sector, externo';
PRINT 'Filtro: solo líneas con existencias > 0';
PRINT '============================================================================';
