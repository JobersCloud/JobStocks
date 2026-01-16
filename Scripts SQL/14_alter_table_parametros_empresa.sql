-- ============================================
-- Script: 14_alter_table_parametros_empresa.sql
-- Descripción: Añadir campo empresa_id a la tabla parametros
-- Base de datos: ApiRestStocks
-- ============================================

USE ApiRestStocks;
GO

-- Añadir columna empresa_id
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('parametros') AND name = 'empresa_id')
BEGIN
    ALTER TABLE parametros
    ADD empresa_id VARCHAR(5) NOT NULL DEFAULT '1';

    PRINT 'Columna empresa_id añadida a parametros';
END
ELSE
BEGIN
    PRINT 'La columna empresa_id ya existe en parametros';
END
GO

-- Crear índice para optimizar consultas por empresa
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_parametros_empresa_id' AND object_id = OBJECT_ID('parametros'))
BEGIN
    CREATE INDEX IX_parametros_empresa_id ON parametros(empresa_id);
    PRINT 'Índice IX_parametros_empresa_id creado';
END
GO

-- Crear índice único compuesto: clave + empresa_id
-- Esto permite tener el mismo parámetro con diferentes valores por empresa
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_parametros_clave_empresa' AND object_id = OBJECT_ID('parametros'))
BEGIN
    -- Primero eliminar el posible índice único anterior solo por clave
    IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_parametros_clave' AND object_id = OBJECT_ID('parametros'))
    BEGIN
        DROP INDEX UQ_parametros_clave ON parametros;
        PRINT 'Índice único anterior por clave eliminado';
    END

    CREATE UNIQUE INDEX UQ_parametros_clave_empresa ON parametros(clave, empresa_id);
    PRINT 'Índice único UQ_parametros_clave_empresa creado';
END
GO

-- Insertar parámetros por defecto para empresa '1' si no existen
-- (Los existentes ya tendrán empresa_id = '1' por el DEFAULT)

PRINT 'Script 14_alter_table_parametros_empresa.sql ejecutado correctamente';
