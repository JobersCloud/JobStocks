-- ============================================
-- Script: 31_create_view_externos_venfac.sql
-- Descripcion: Vista de cabecera de facturas de venta
-- Base de datos: ApiRestStocks
-- Origen datos: cristal.dbo.venfac + cristal.dbo.genter
-- ============================================

USE ApiRestStocks;
GO

IF OBJECT_ID('dbo.view_externos_venfac', 'V') IS NOT NULL
    DROP VIEW dbo.view_externos_venfac;
GO

CREATE VIEW dbo.view_externos_venfac AS
SELECT
    f.empresa,
    f.anyo,
    f.factura,
    f.ffactura AS fecha,
    RTRIM(f.cliente) AS cliente,
    RTRIM(ISNULL(c.razon, '')) AS cliente_nombre,
    RTRIM(ISNULL(f.serie, '')) AS serie,
    ISNULL(f.total_neto -f.importe_dto, 0) AS base_imponible,
    ISNULL(f.iva, 0) AS iva,
    ISNULL(f.total_fac, 0) AS total,
    RTRIM(ISNULL(f.divisa, '')) AS divisa,
    RTRIM(ISNULL(f.usuario, '')) AS usuario,
    f.falta AS fecha_alta
FROM cristal.dbo.venfac f
LEFT JOIN cristal.dbo.genter c ON f.cliente = c.codigo AND f.empresa = c.empresa AND c.tipoter = 'C'
WHERE f.empresa IS NOT NULL
  AND f.anyo IS NOT NULL
  AND f.factura IS NOT NULL;
GO

-- Verificar
SELECT TOP 10 * FROM dbo.view_externos_venfac ORDER BY fecha DESC;
GO
