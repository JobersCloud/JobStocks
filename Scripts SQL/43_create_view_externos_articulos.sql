-- ============================================
-- Script: 43_create_view_externos_articulos.sql
-- Descripcion: Vista de articulos (maestro) independiente del stock
-- Fecha: 2026-03-05
-- ============================================
-- NOTA: Esta vista debe crearse manualmente en cada instalacion.
-- La tabla origen varia segun el ERP (ej: cristal.dbo.ps_articulo).
-- Los campos minimos requeridos son: empresa, codigo, descripcion, formato.
-- ============================================

-- Ejemplo generico (adaptar a cada instalacion):
/*
CREATE VIEW view_externos_articulos AS
SELECT
    empresa,
    codigo,
    descripcion,
    formato
FROM cristal.dbo.ps_articulo
WHERE activo = 1;
*/
