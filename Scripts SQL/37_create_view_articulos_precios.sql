-- ============================================================
-- Script: 37_create_view_articulos_precios.sql
-- Descripcion: Vista de precios por articulo+calidad
-- Fecha: 2026-02-23
-- NOTA: Este script NO se ejecuta en migraciones automaticas.
--       Debe crearse manualmente en cada instalacion que lo necesite.
--       Requiere primero crear la tabla precios_formato_calidad.
-- ============================================================

-- Paso 1: Crear tabla de precios por formato y calidad
-- (Ajustar segun necesidades del cliente)
/*
CREATE TABLE precios_formato_calidad (
    empresa VARCHAR(5) NOT NULL,
    formato VARCHAR(50) NOT NULL,
    calidad VARCHAR(20) NOT NULL,
    precio DECIMAL(18,2) NOT NULL,
    PRIMARY KEY (empresa, formato, calidad)
);
*/

-- Paso 2: Crear vista que devuelve precio por articulo+calidad
-- La vista cruza stock con precios por formato+calidad
/*
CREATE VIEW view_externos_articulos_precios AS
SELECT DISTINCT
    s.empresa,
    s.codigo,
    s.calidad,
    p.precio
FROM view_externos_stock s
INNER JOIN precios_formato_calidad p
    ON s.empresa = p.empresa
    AND s.formato = p.formato
    AND s.calidad = p.calidad;
*/

-- Paso 3: Activar el parametro MOSTRAR_PRECIOS para la empresa
-- UPDATE parametros SET valor = '1' WHERE clave = 'MOSTRAR_PRECIOS' AND empresa_id = '1';
