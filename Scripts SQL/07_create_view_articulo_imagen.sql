-- ============================================
-- Script: 07_create_view_articulo_imagen.sql
-- Descripción: Vista para imágenes de artículos
-- Base de datos: ApiRestStocks
-- Origen: cristal.dbo.ps_articulo_imagen
-- ============================================

USE ApiRestStocks;
GO

-- Crear vista que apunta a la tabla de imágenes en cristal
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_articulo_imagen')
BEGIN
    DROP VIEW view_articulo_imagen;
END
GO

CREATE VIEW view_articulo_imagen AS
SELECT
    id,
    articulo AS codigo,
    foto AS imagen
FROM cristal.dbo.ps_articulo_imagen;
GO

PRINT 'Vista view_articulo_imagen creada correctamente';
GO
