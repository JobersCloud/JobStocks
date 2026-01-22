-- ============================================================
-- Script: 26_insert_parametro_paginacion.sql
-- Descripcion: Añadir parámetro para habilitar paginación en grid sin imágenes
-- Fecha: 2026-01-22
-- ============================================================

-- Insertar parámetro de paginación para empresa por defecto
-- Valores: 1 = Paginación habilitada, 0 = Sin paginación (carga todo)
IF NOT EXISTS (
    SELECT 1 FROM parametros
    WHERE clave = 'PAGINACION_GRID' AND empresa_id = '1'
)
BEGIN
    INSERT INTO parametros (clave, valor, descripcion, empresa_id)
    VALUES ('PAGINACION_GRID', '1', 'Habilitar paginación en vista de tabla/grid sin imágenes. 1=Habilitado, 0=Deshabilitado', '1');
    PRINT 'Parámetro PAGINACION_GRID insertado para empresa 1';
END
ELSE
BEGIN
    PRINT 'El parámetro PAGINACION_GRID ya existe para empresa 1';
END
GO

-- Insertar parámetro para tamaño de página
IF NOT EXISTS (
    SELECT 1 FROM parametros
    WHERE clave = 'PAGINACION_LIMITE' AND empresa_id = '1'
)
BEGIN
    INSERT INTO parametros (clave, valor, descripcion, empresa_id)
    VALUES ('PAGINACION_LIMITE', '50', 'Número de registros por página en vista de tabla/grid. Valores recomendados: 25, 50, 100', '1');
    PRINT 'Parámetro PAGINACION_LIMITE insertado para empresa 1';
END
ELSE
BEGIN
    PRINT 'El parámetro PAGINACION_LIMITE ya existe para empresa 1';
END
GO
