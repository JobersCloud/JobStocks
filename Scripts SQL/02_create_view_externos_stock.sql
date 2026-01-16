-- ============================================
-- Vista: view_externos_stock
-- Descripción: Stock de productos con existencias disponibles
-- Base de datos: ApiRestStocks
-- Dependencia: Base de datos cristal (tablas externas)
-- ============================================

USE ApiRestStocks;
GO

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE VIEW [dbo].[view_externos_stock]
AS
SELECT
    almlinubica.empresa AS empresa,
    almlinubica.articulo AS codigo,
    almlinubica.referencia AS referencia,
    almlinubica.tipo_pallet AS tipo_pallet,
    articulos.descripcion AS descripcion,
    formatos.abreviado AS formato,
    almmodelos.descripcion AS serie,
    calidades.abreviado AS calidad,
    almlinubica.tonochar AS tono,
    CONVERT(varchar, almlinubica.calibre) AS calibre,
    pallets.resumido AS pallet,
    pallets.unidadescaja AS unidadescaja,
    pallets.cajaspallet AS cajaspallet,
    almcolores.descripcion AS color,
    unidades.abreviado AS unidad,
    ISNULL(SUM(almlinubica.existencias), 0) -
    ISNULL(
        (SELECT SUM(venliped.cantidad)
         FROM cristal.dbo.venliped
         WHERE venliped.empresa = cristal.dbo.almlinubica.empresa
           AND venliped.referencia = cristal.dbo.almlinubica.referencia
           AND venliped.tipo_pallet = cristal.dbo.almlinubica.tipo_pallet
           AND venliped.situacion IN ('C','P')),
        0
    ) AS existencias

FROM cristal.dbo.almlinubica
    LEFT OUTER JOIN cristal.dbo.articulos
        ON almlinubica.empresa = articulos.empresa
        AND almlinubica.articulo = articulos.codigo
    LEFT OUTER JOIN cristal.dbo.formatos
        ON articulos.empresa = formatos.empresa
        AND articulos.formato = formatos.codigo
    LEFT OUTER JOIN cristal.dbo.almmodelos
        ON articulos.empresa = almmodelos.empresa
        AND articulos.modelo = almmodelos.modelo
    LEFT OUTER JOIN cristal.dbo.calidades
        ON almlinubica.empresa = calidades.empresa
        AND almlinubica.calidad = calidades.codigo
    LEFT OUTER JOIN cristal.dbo.pallets
        ON almlinubica.empresa = pallets.empresa
        AND almlinubica.tipo_pallet = pallets.codigo
    LEFT OUTER JOIN cristal.dbo.almcolores
        ON articulos.empresa = almcolores.empresa
        AND articulos.color = almcolores.color
    LEFT OUTER JOIN cristal.dbo.unidades
        ON articulos.unidad = unidades.codigo

GROUP BY
    almlinubica.empresa,
    almlinubica.articulo,
    almlinubica.referencia,
    almlinubica.tipo_pallet,
    articulos.descripcion,
    formatos.abreviado,
    almmodelos.descripcion,
    calidades.abreviado,
    almlinubica.tonochar,
    CONVERT(varchar, almlinubica.calibre),
    pallets.resumido,
    pallets.unidadescaja,
    pallets.cajaspallet,
    almcolores.descripcion,
    unidades.abreviado

HAVING
    ISNULL(SUM(almlinubica.existencias), 0) -
    ISNULL(
        (SELECT SUM(venliped.cantidad)
         FROM cristal.dbo.venliped
         WHERE venliped.empresa = cristal.dbo.almlinubica.empresa
           AND venliped.referencia = cristal.dbo.almlinubica.referencia
           AND venliped.tipo_pallet = cristal.dbo.almlinubica.tipo_pallet
           AND venliped.situacion IN ('C','P')),
        0
    ) > 0;
GO

PRINT 'Vista view_externos_stock creada exitosamente';
