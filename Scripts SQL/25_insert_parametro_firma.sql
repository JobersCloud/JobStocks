-- ============================================================
-- Script: 25_insert_parametro_firma.sql
-- Descripción: Añadir parámetro para habilitar/deshabilitar firma de propuestas
-- Fecha: 2026-01-22
-- ============================================================

-- Insertar parámetro PERMITIR_FIRMA para empresa por defecto
INSERT INTO parametros (clave, valor, descripcion, fecha_modificacion, empresa_id)
VALUES ('PERMITIR_FIRMA', '1', 'Habilita/deshabilita la opción de firma digital en propuestas (1=habilitado, 0=deshabilitado)', GETDATE(), '1');

-- Nota: Este INSERT puede fallar si el parámetro ya existe para esa empresa
-- En ese caso, usar UPDATE:
-- UPDATE parametros SET valor = '1' WHERE clave = 'PERMITIR_FIRMA' AND empresa_id = '1';
