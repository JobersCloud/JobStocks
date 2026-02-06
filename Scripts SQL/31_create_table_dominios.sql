-- ============================================
-- Script: 31_create_table_dominios.sql
-- Fecha: 2026-02-05
-- Descripcion: Tabla para mapear dominios/subdominios a connection_id
-- Base de datos: BD CENTRAL (jobers_control_usuarios)
-- ============================================

-- Crear tabla dominios
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dominios')
BEGIN
    CREATE TABLE dominios (
        id INT IDENTITY(1,1) PRIMARY KEY,
        dominio VARCHAR(255) NOT NULL,           -- ej: empresa1.tudominio.com
        connection_id VARCHAR(10) NOT NULL,       -- ID de empresas_cli
        descripcion VARCHAR(255) NULL,            -- Nombre descriptivo (opcional)
        activo BIT DEFAULT 1,
        fecha_creacion DATETIME DEFAULT GETDATE(),
        fecha_modificacion DATETIME DEFAULT GETDATE()
    );

    -- Indice unico para dominio
    CREATE UNIQUE INDEX IX_dominios_dominio ON dominios(dominio);

    PRINT 'Tabla dominios creada correctamente';
END
ELSE
BEGIN
    PRINT 'La tabla dominios ya existe';
END
GO

-- Insertar dominios de ejemplo (ajustar segun necesidad)
-- INSERT INTO dominios (dominio, connection_id, descripcion) VALUES
-- ('prolife-area.cristalceramicas.com', '1', 'Cristal Ceramicas - Produccion'),
-- ('localhost', '1', 'Desarrollo local'),
-- ('127.0.0.1', '1', 'Desarrollo local IP');
