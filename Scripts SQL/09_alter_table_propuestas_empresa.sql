-- ============================================================================
-- Script: 09_alter_table_propuestas_empresa.sql
-- Descripción: Agregar campo empresa_id a la tabla propuestas (multi-empresa)
-- Fecha: 2025-12-29
-- ============================================================================

USE ApiRestStocks;
GO

-- Agregar columna empresa_id a la tabla propuestas
IF NOT EXISTS (SELECT 1 FROM sys.columns
               WHERE object_id = OBJECT_ID('propuestas')
               AND name = 'empresa_id')
BEGIN
    -- Primero agregar como NULL para poder insertar en registros existentes
    ALTER TABLE propuestas
    ADD empresa_id VARCHAR(5) NULL;

    PRINT 'Columna empresa_id agregada a la tabla propuestas';

    -- Actualizar registros existentes con empresa_id = '1' (empresa por defecto)
    UPDATE propuestas
    SET empresa_id = '1'
    WHERE empresa_id IS NULL;

    PRINT 'Propuestas existentes actualizadas con empresa_id = ''1''';

    -- Ahora hacer la columna NOT NULL con DEFAULT '1'
    ALTER TABLE propuestas
    ALTER COLUMN empresa_id VARCHAR(5) NOT NULL;

    -- Agregar constraint de default
    ALTER TABLE propuestas
    ADD CONSTRAINT DF_propuestas_empresa_id DEFAULT '1' FOR empresa_id;

    PRINT 'Columna empresa_id configurada como NOT NULL con DEFAULT ''1''';
END
ELSE
BEGIN
    PRINT 'La columna empresa_id ya existe en la tabla propuestas';
END
GO

-- Crear índice para mejorar performance en búsquedas por empresa
IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE name = 'IX_propuestas_empresa_id'
               AND object_id = OBJECT_ID('propuestas'))
BEGIN
    CREATE INDEX IX_propuestas_empresa_id ON propuestas(empresa_id);
    PRINT 'Índice IX_propuestas_empresa_id creado';
END
ELSE
BEGIN
    PRINT 'El índice IX_propuestas_empresa_id ya existe';
END
GO

-- Verificar cambios
SELECT
    id,
    empresa_id,
    user_id,
    fecha,
    estado,
    total_items,
    comentarios
FROM propuestas
ORDER BY id DESC;
GO

PRINT '============================================================================';
PRINT 'Script completado exitosamente';
PRINT 'IMPORTANTE: Las propuestas existentes tienen empresa_id = ''1''';
PRINT 'Las nuevas propuestas heredarán el empresa_id del contexto del usuario';
PRINT '============================================================================';
