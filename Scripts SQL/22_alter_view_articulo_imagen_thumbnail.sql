-- =============================================
-- Script: 22_alter_view_articulo_imagen_thumbnail.sql
-- Descripcion: Actualiza vista para incluir campo thumbnail
-- Autor: Jobers
-- Fecha: 2026-01-09
-- =============================================
-- PREREQUISITO: Ejecutar primero en la base de datos cristal:
-- ALTER TABLE cristal.dbo.ps_articulo_imagen ADD thumbnail VARBINARY(MAX) NULL;
-- =============================================

USE ApiRestStocks;
GO

-- Actualizar vista para incluir el campo thumbnail
ALTER VIEW view_articulo_imagen AS
SELECT
    id,
    articulo AS codigo,
    foto AS imagen,
    thumbnail
FROM cristal.dbo.ps_articulo_imagen;
GO

PRINT 'Vista view_articulo_imagen actualizada con campo thumbnail';
GO
