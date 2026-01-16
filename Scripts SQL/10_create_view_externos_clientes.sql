-- ============================================================================
-- Script: 10_create_view_externos_clientes.sql
-- Descripción: Vista para consulta de clientes desde sistema externo
-- Fecha: 2025-12-29
-- ============================================================================

USE ApiRestStocks;
GO

-- Crear o reemplazar vista de clientes
IF EXISTS (SELECT 1 FROM sys.views WHERE name = 'view_externos_clientes')
BEGIN
    DROP VIEW view_externos_clientes;
    PRINT 'Vista view_externos_clientes eliminada para recrear';
END
GO

CREATE VIEW [dbo].[view_externos_clientes]
AS
    SELECT
        empresa,    -- Identificador de empresa (multi-empresa)
        codigo,     -- Código del cliente
        razon       -- Razón social del cliente
    FROM cristal.dbo.genter
    WHERE tipoter = 'C'  -- Solo clientes (tipo tercero = C)
GO

PRINT 'Vista view_externos_clientes creada correctamente';
GO

-- Verificar datos de la vista
SELECT TOP 10
    empresa,
    codigo,
    razon
FROM view_externos_clientes
ORDER BY razon;
GO

PRINT '============================================================================';
PRINT 'Script completado exitosamente';
PRINT 'Vista: view_externos_clientes';
PRINT 'Origen: cristal.dbo.genter (tipoter = ''C'')';
PRINT 'Campos: empresa, codigo, razon';
PRINT '============================================================================';
