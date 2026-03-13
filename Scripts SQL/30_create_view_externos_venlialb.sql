-- ============================================
-- Script: 30_create_view_externos_venlialb.sql
-- Descripcion: Vista de lineas de albaranes de venta
-- Base de datos: ApiRestStocks
-- Origen datos: cristal.dbo.venlialb
-- ============================================

USE ApiRestStocks;
GO

IF OBJECT_ID('dbo.view_externos_venlialb', 'V') IS NOT NULL
    DROP VIEW dbo.view_externos_venlialb;
GO

CREATE VIEW dbo.view_externos_venlialb AS
SELECT
    empresa,
    anyo,
    albaran,
    linea,
    RTRIM(ISNULL(articulo, '')) AS articulo,
    RTRIM(ISNULL(descripcion, '')) AS descripcion,
    RTRIM(ISNULL(formato, '')) AS formato,
    RTRIM(ISNULL(calidad, '')) AS calidad,
    ISNULL(tono, 0) AS tono,
    ISNULL(calibre, 0) AS calibre,
    ISNULL(cantidad, 0) AS cantidad,
    ISNULL(precio, 0) AS precio,
    ISNULL(importe, 0) AS importe,
    ISNULL(pallets, 0) AS pallets,
    ISNULL(total_cajas, 0) AS cajas,
    falbaran AS fecha,
    RTRIM(ISNULL(situacion, '')) AS situacion
FROM cristal.dbo.venlialb
WHERE empresa IS NOT NULL
  AND anyo IS NOT NULL
  AND albaran IS NOT NULL;
GO

-- Verificar
SELECT TOP 10 * FROM dbo.view_externos_venlialb ORDER BY anyo DESC, albaran DESC, linea;
GO
