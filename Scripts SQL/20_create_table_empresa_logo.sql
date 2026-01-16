-- ============================================
-- Script: 20_create_table_empresa_logo.sql
-- Descripción: Crear tabla para logos y favicons por empresa
-- Fecha: 2026-01-08
-- ============================================

USE ApiRestStocks;
GO

-- Crear tabla empresa_logo
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'empresa_logo')
BEGIN
    CREATE TABLE empresa_logo (
        codigo VARCHAR(5) NOT NULL PRIMARY KEY,
        logo VARBINARY(MAX) NULL,
        favicon VARBINARY(MAX) NULL,
        fecha_creacion DATETIME DEFAULT GETDATE(),
        fecha_modificacion DATETIME DEFAULT GETDATE()
    );

    PRINT 'Tabla empresa_logo creada correctamente';
END
ELSE
BEGIN
    PRINT 'La tabla empresa_logo ya existe';
END
GO

-- Crear índice por código
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_empresa_logo_codigo')
BEGIN
    CREATE INDEX IX_empresa_logo_codigo ON empresa_logo(codigo);
    PRINT 'Índice IX_empresa_logo_codigo creado';
END
GO

-- Comentarios de la tabla
EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Tabla para almacenar logos y favicons por empresa',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'empresa_logo';
GO

PRINT 'Script ejecutado correctamente';
GO
