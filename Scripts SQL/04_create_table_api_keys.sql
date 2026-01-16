-- ============================================
-- Script: 04_create_table_api_keys.sql
-- Descripción: Tabla para almacenar API Keys
-- Base de datos: ApiRestStocks
-- ============================================

USE ApiRestStocks;
GO

-- Crear tabla api_keys
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'api_keys')
BEGIN
    CREATE TABLE api_keys (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        api_key VARCHAR(64) NOT NULL UNIQUE,
        nombre VARCHAR(100) NOT NULL,
        activo BIT DEFAULT 1,
        fecha_creacion DATETIME DEFAULT GETDATE(),
        fecha_ultimo_uso DATETIME NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE INDEX idx_api_key ON api_keys(api_key);

    PRINT 'Tabla api_keys creada correctamente';
END
ELSE
BEGIN
    PRINT 'La tabla api_keys ya existe';
END
GO
