-- Script para añadir parámetro PERMITIR_PROPUESTAS
-- Este parámetro controla si los usuarios pueden crear propuestas/solicitudes
-- Fecha: 2026-01-02

USE ApiRestStocks;
GO

-- Insertar parámetro PERMITIR_PROPUESTAS si no existe
IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'PERMITIR_PROPUESTAS')
BEGIN
    INSERT INTO parametros (clave, valor, descripcion)
    VALUES ('PERMITIR_PROPUESTAS', '1', 'Permitir crear propuestas/solicitudes de productos (0=No, 1=Sí)');

    PRINT 'Parámetro PERMITIR_PROPUESTAS creado correctamente';
END
ELSE
BEGIN
    PRINT 'El parámetro PERMITIR_PROPUESTAS ya existe';
END
GO
