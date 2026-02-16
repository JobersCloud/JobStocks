-- ============================================================================
-- Script: 36_create_view_externos_formatos.sql
-- Descripción: Vista para consulta de formatos desde sistema externo
-- Fecha: 2026-02-16
-- ============================================================================

USE ApiRestStocks;
GO

-- Crear o reemplazar vista de formatos
IF EXISTS (SELECT 1 FROM sys.views WHERE name = 'view_externos_formatos')
BEGIN
    DROP VIEW view_externos_formatos;
    PRINT 'Vista view_externos_formatos eliminada para recrear';
END
GO

CREATE VIEW [dbo].[view_externos_formatos]
AS
    SELECT
        empresa,    -- Identificador de empresa
        codigo,     -- Código del formato
        abreviado   -- Nombre abreviado del formato
    FROM cristal.dbo.formatos
GO

PRINT 'Vista view_externos_formatos creada correctamente';
GO

-- Verificar datos de la vista
SELECT TOP 10
    empresa,
    codigo,
    abreviado
FROM view_externos_formatos
ORDER BY empresa, codigo;
GO

PRINT '============================================================================';
PRINT 'Script completado exitosamente';
PRINT 'Vista: view_externos_formatos';
PRINT 'Origen: cristal.dbo.formatos';
PRINT 'Campos: empresa, codigo, abreviado';
PRINT '============================================================================';
