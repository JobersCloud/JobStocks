-- ============================================================================
-- Script: 32_alter_view_clientes_direccion.sql
-- Descripcion: Ampliar vista de clientes con campos de direccion
-- Fecha: 2026-02-06
-- ============================================================================

USE ApiRestStocks;
GO

-- Recrear vista con campos de direccion
IF EXISTS (SELECT 1 FROM sys.views WHERE name = 'view_externos_clientes')
BEGIN
    DROP VIEW view_externos_clientes;
    PRINT 'Vista view_externos_clientes eliminada para recrear';
END
GO

CREATE VIEW [dbo].[view_externos_clientes]
AS
    SELECT
        empresa,                    -- Identificador de empresa (multi-empresa)
        codigo,                     -- Codigo del cliente
        razon,                      -- Razon social del cliente
        domicilio,                  -- Direccion/calle
        cod_postal AS codpos,       -- Codigo postal (alias normalizado)
        poblacion,                  -- Ciudad/poblacion
        provincia,                  -- Provincia
        pais                        -- Pais
    FROM cristal.dbo.genter
    WHERE tipoter = 'C'  -- Solo clientes (tipo tercero = C)
GO

PRINT 'Vista view_externos_clientes recreada con campos de direccion';
GO

-- Verificar datos de la vista
SELECT TOP 10
    empresa, codigo, razon, domicilio, codpos, poblacion, provincia, pais
FROM view_externos_clientes
ORDER BY razon;
GO

PRINT '============================================================================';
PRINT 'Script completado exitosamente';
PRINT 'Vista: view_externos_clientes';
PRINT 'Campos nuevos: domicilio, codpos, poblacion, provincia, pais';
PRINT '============================================================================';
