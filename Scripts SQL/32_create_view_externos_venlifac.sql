-- ============================================
-- Script: 32_create_view_externos_venlifac.sql
-- Descripcion: Vista de lineas de facturas de venta
-- Base de datos: ApiRestStocks
-- Origen datos: cristal.dbo.venlifac
-- ============================================

USE ApiRestStocks;
GO

IF OBJECT_ID('dbo.view_externos_venlifac', 'V') IS NOT NULL
    DROP VIEW dbo.view_externos_venlifac;
GO

CREATE VIEW dbo.view_externos_venlifac AS
SELECT
    empresa,
    anyo,
    factura,
    linea,
    RTRIM(ISNULL(articulo, '')) AS articulo,
    RTRIM(ISNULL(descripcion, '')) AS descripcion,
    RTRIM(ISNULL(formato, '')) AS formato,
    RTRIM(ISNULL(calidad, '')) AS calidad,
    ISNULL(tono, 0) AS tono,
    ISNULL(calibre, 0) AS calibre,
    ISNULL(cantidad, 0) AS cantidad,
    ISNULL(precio, 0) AS precio,
    ISNULL(neto, 0) AS importe,
    ISNULL(pallets, 0) AS pallets,
    ISNULL(total_cajas, 0) AS cajas,
    ffactura AS fecha,
    RTRIM(ISNULL(situacion, '')) AS situacion
FROM cristal.dbo.venlifac
WHERE empresa IS NOT NULL
  AND anyo IS NOT NULL
  AND factura IS NOT NULL;
GO

-- Verificar
SELECT TOP 10 * FROM dbo.view_externos_venlifac ORDER BY anyo DESC, factura DESC, linea;
GO
