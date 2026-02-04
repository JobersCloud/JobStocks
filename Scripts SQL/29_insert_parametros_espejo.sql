-- =============================================
-- Script: 29_insert_parametros_espejo.sql
-- Descripcion: Añadir parámetros para modo espejo y fecha de sincronización
-- Fecha: 2026-02-04
-- =============================================

USE ApiRestStocks;
GO

-- Parámetro MODO_ESPEJO: indica si la BD trabaja como espejo de otra
-- Valores: '0' = BD original, '1' = BD espejo
INSERT INTO parametros (clave, valor, descripcion, empresa_id)
SELECT 'MODO_ESPEJO', '0', 'Indica si la base de datos es un espejo (copia sincronizada de otra BD). 0=Original, 1=Espejo', empresa_id
FROM (SELECT DISTINCT empresa_id FROM parametros) AS empresas
WHERE NOT EXISTS (
    SELECT 1 FROM parametros p
    WHERE p.clave = 'MODO_ESPEJO' AND p.empresa_id = empresas.empresa_id
);
GO

-- Parámetro FECHA_ULTIMA_SINCRONIZACION: fecha de la última carga de datos
-- Formato: YYYY-MM-DD HH:MM:SS
INSERT INTO parametros (clave, valor, descripcion, empresa_id)
SELECT 'FECHA_ULTIMA_SINCRONIZACION', '', 'Fecha y hora de la última sincronización de datos desde la BD origen', empresa_id
FROM (SELECT DISTINCT empresa_id FROM parametros) AS empresas
WHERE NOT EXISTS (
    SELECT 1 FROM parametros p
    WHERE p.clave = 'FECHA_ULTIMA_SINCRONIZACION' AND p.empresa_id = empresas.empresa_id
);
GO

PRINT 'Parámetros de modo espejo creados correctamente';
GO
