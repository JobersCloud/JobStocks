-- ============================================
-- Tabla: users
-- Descripción: Usuarios para autenticación
-- Base de datos: ApiRestStocks
-- ============================================

USE ApiRestStocks;
GO

-- Eliminar tabla si existe (opcional, para pruebas)
-- DROP TABLE IF EXISTS users;
-- GO

-- Crear tabla de usuarios
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(50) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL,
    email NVARCHAR(100),
    full_name NVARCHAR(100),
    active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),

    -- Constraints
    CONSTRAINT CHK_username_length CHECK (LEN(username) >= 3),
    CONSTRAINT CHK_email_format CHECK (email LIKE '%_@__%.__%' OR email IS NULL)
);
GO

-- Índices para mejorar rendimiento
CREATE INDEX idx_username ON users(username);
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_active ON users(active);
GO

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER trg_users_updated_at
ON users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE users
    SET updated_at = GETDATE()
    FROM users u
    INNER JOIN inserted i ON u.id = i.id;
END;
GO

PRINT 'Tabla users creada exitosamente';
