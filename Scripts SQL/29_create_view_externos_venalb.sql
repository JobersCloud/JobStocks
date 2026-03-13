-- ============================================
-- Script: 29_create_view_externos_venalb.sql
-- Descripcion: Vista de cabecera de albaranes de venta
-- Base de datos: ApiRestStocks
-- Origen datos: cristal.dbo.venalb + cristal.dbo.genter
-- ============================================

USE ApiRestStocks;
GO

IF OBJECT_ID('dbo.view_externos_venalb', 'V') IS NOT NULL
    DROP VIEW dbo.view_externos_venalb;
GO

CREATE VIEW dbo.view_externos_venalb AS
SELECT
    a.empresa,
    a.anyo,
    a.albaran,
    a.falbaran AS fecha,
    a.fentrega AS fecha_entrega,
    RTRIM(a.cliente) AS cliente,
    RTRIM(ISNULL(c.razon, '')) AS cliente_nombre,
    RTRIM(ISNULL(a.serie, '')) AS serie,
    ISNULL(a.bruto, 0) AS bruto,
    ISNULL(a.importe_dto, 0) AS importe_dto,
    ISNULL(a.total_neto, 0) AS total,
    ISNULL(a.peso, 0) AS peso,
    RTRIM(ISNULL(a.divisa, '')) AS divisa,
    RTRIM(ISNULL(a.usuario, '')) AS usuario,
    a.falta AS fecha_alta
FROM cristal.dbo.venalb a
LEFT JOIN cristal.dbo.genter c ON a.cliente = c.codigo AND a.empresa = c.empresa AND c.tipoter = 'C'
WHERE a.empresa IS NOT NULL
  AND a.anyo IS NOT NULL
  AND a.albaran IS NOT NULL
  AND ISNULL(a.deposito, '') <> '';
GO

-- Verificar
SELECT TOP 10 * FROM dbo.view_externos_venalb ORDER BY fecha DESC;
GO
