-- ============================================
-- Script: 28_create_view_externos_venliped.sql
-- Descripcion: Vista de lineas de pedidos de venta
-- Base de datos: ApiRestStocks
-- Origen datos: cristal.dbo.venliped
-- ============================================

USE ApiRestStocks;
GO

IF OBJECT_ID('dbo.view_externos_venliped', 'V') IS NOT NULL
    DROP VIEW dbo.view_externos_venliped;
GO

CREATE VIEW dbo.view_externos_venliped AS
SELECT
    empresa,
    anyo,
    pedido,
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
    fpedido AS fecha_pedido,
    fentrega AS fecha_entrega,
    RTRIM(ISNULL(situacion, '')) AS situacion
FROM cristal.dbo.venliped
WHERE empresa IS NOT NULL
  AND anyo IS NOT NULL
  AND pedido IS NOT NULL;
GO

-- Verificar
SELECT TOP 10 * FROM dbo.view_externos_venliped ORDER BY anyo DESC, pedido DESC, linea;
GO
