-- ============================================
-- Script: 13_alter_table_email_config_empresa.sql
-- Descripción: Añadir campo empresa_id a la tabla email_config
-- Base de datos: ApiRestStocks
-- ============================================

USE ApiRestStocks;
GO

-- Añadir columna empresa_id
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('email_config') AND name = 'empresa_id')
BEGIN
    ALTER TABLE email_config
    ADD empresa_id VARCHAR(5) NOT NULL DEFAULT '1';

    PRINT 'Columna empresa_id añadida a email_config';
END
ELSE
BEGIN
    PRINT 'La columna empresa_id ya existe en email_config';
END
GO

-- Crear índice para optimizar consultas por empresa
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_email_config_empresa_id' AND object_id = OBJECT_ID('email_config'))
BEGIN
    CREATE INDEX IX_email_config_empresa_id ON email_config(empresa_id);
    PRINT 'Índice IX_email_config_empresa_id creado';
END
GO

-- Modificar la restricción de activo: solo una configuración activa POR EMPRESA
-- Primero eliminamos el constraint si existe
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_email_config_activo_empresa' AND object_id = OBJECT_ID('email_config'))
BEGIN
    DROP INDEX UQ_email_config_activo_empresa ON email_config;
    PRINT 'Índice único anterior eliminado';
END
GO

PRINT 'Script 13_alter_table_email_config_empresa.sql ejecutado correctamente';
