-- ============================================
-- Script: 27_create_view_externos_venped.sql
-- Descripcion: Vista de cabecera de pedidos de venta
-- Base de datos: ApiRestStocks
-- Origen datos: cristal.dbo.venped + cristal.dbo.genter
-- ============================================

USE ApiRestStocks;
GO

IF OBJECT_ID('dbo.view_externos_venped', 'V') IS NOT NULL
    DROP VIEW dbo.view_externos_venped;
GO

CREATE VIEW dbo.view_externos_venped AS
SELECT
    p.empresa,
    p.anyo,
    p.pedido,
    p.fpedido AS fecha,
    p.fentrega AS fecha_entrega,
    RTRIM(p.cliente) AS cliente,
    RTRIM(ISNULL(c.razon, '')) AS cliente_nombre,
    p.numpedcli AS pedido_cliente,
    RTRIM(ISNULL(p.serie, '')) AS serie,
    ISNULL(p.bruto, 0) AS bruto,
    ISNULL(p.importe_dto, 0) AS importe_dto,
    ISNULL(p.total_neto, 0) AS total,
    ISNULL(p.peso, 0) AS peso,
    RTRIM(ISNULL(p.divisa, '')) AS divisa,
    RTRIM(ISNULL(p.usuario, '')) AS usuario,
    p.falta AS fecha_alta
FROM cristal.dbo.venped p
LEFT JOIN cristal.dbo.genter c ON p.cliente = c.codigo AND p.empresa = c.empresa AND c.tipoter = 'C'
WHERE p.empresa IS NOT NULL
  AND p.anyo IS NOT NULL
  AND p.pedido IS NOT NULL;
GO

-- Verificar
SELECT TOP 10 * FROM dbo.view_externos_venped ORDER BY fecha DESC;
GO
