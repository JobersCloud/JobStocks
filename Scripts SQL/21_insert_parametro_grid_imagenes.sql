-- =============================================
-- Script: 21_insert_parametro_grid_imagenes.sql
-- Descripcion: Inserta parametro GRID_CON_IMAGENES
-- Autor: Jobers
-- Fecha: 2026-01-09
-- =============================================

USE ApiRestStocks;
GO

-- Insertar parametro para empresa 1 (por defecto desactivado)
IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'GRID_CON_IMAGENES' AND empresa_id = '1')
BEGIN
    INSERT INTO parametros (clave, valor, descripcion, empresa_id)
    VALUES ('GRID_CON_IMAGENES', '0', 'Mostrar imagenes en tabla y tarjetas de stock', '1');
    PRINT 'Parametro GRID_CON_IMAGENES creado para empresa 1';
END
ELSE
BEGIN
    PRINT 'Parametro GRID_CON_IMAGENES ya existe para empresa 1';
END
GO
