-- ============================================================
-- Script: 25_alter_table_propuestas_cliente.sql
-- Descripcion: Añadir campo cliente_id a la tabla propuestas
-- Fecha: 2026-01-22
-- ============================================================

-- Verificar si la columna ya existe antes de añadirla
IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'propuestas'
    AND COLUMN_NAME = 'cliente_id'
)
BEGIN
    ALTER TABLE propuestas
    ADD cliente_id VARCHAR(20) NULL;

    PRINT 'Columna cliente_id añadida a tabla propuestas';
END
ELSE
BEGIN
    PRINT 'La columna cliente_id ya existe en tabla propuestas';
END
GO

-- Crear índice para mejorar consultas por cliente
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_propuestas_cliente_id'
    AND object_id = OBJECT_ID('propuestas')
)
BEGIN
    CREATE INDEX IX_propuestas_cliente_id ON propuestas(cliente_id);
    PRINT 'Índice IX_propuestas_cliente_id creado';
END
GO
