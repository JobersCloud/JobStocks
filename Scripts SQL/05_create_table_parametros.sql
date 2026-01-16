-- ============================================
-- Script: 05_create_table_parametros.sql
-- Descripción: Tabla para parámetros de configuración
-- Base de datos: ApiRestStocks
-- ============================================

USE ApiRestStocks;
GO

-- Crear tabla parametros
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parametros')
BEGIN
    CREATE TABLE parametros (
        id INT IDENTITY(1,1) PRIMARY KEY,
        clave VARCHAR(50) NOT NULL UNIQUE,
        valor VARCHAR(500) NOT NULL,
        descripcion VARCHAR(200) NULL,
        fecha_modificacion DATETIME DEFAULT GETDATE()
    );

    -- Insertar parámetro de registro
    INSERT INTO parametros (clave, valor, descripcion)
    VALUES ('PERMITIR_REGISTRO', '0', 'Permitir registro público de usuarios (0=No, 1=Sí)');

    PRINT 'Tabla parametros creada correctamente';
END
ELSE
BEGIN
    PRINT 'La tabla parametros ya existe';
END
GO
