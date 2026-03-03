-- =============================================
-- Script: 40_alter_view_articulo_imagen_empresa.sql
-- Descripcion: Actualiza vista para incluir campo empresa
--              Permite filtrar imagenes por empresa_id
-- Autor: Jobers
-- Fecha: 2026-02-28
-- =============================================

USE ApiRestStocks;
GO

ALTER VIEW view_articulo_imagen AS
SELECT
    id,
    empresa,
    articulo AS codigo,
    foto AS imagen,
    thumbnail
FROM cristal.dbo.ps_articulo_imagen;
GO

PRINT 'Vista view_articulo_imagen actualizada con campo empresa';
GO
