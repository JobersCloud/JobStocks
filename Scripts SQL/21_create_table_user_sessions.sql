-- ============================================================
-- Tabla: user_sessions
-- Descripcion: Almacena sesiones activas de usuarios
-- Fecha: 2026-01-10
-- ============================================================

USE ApiRestStocks;
GO

-- Crear tabla de sesiones
CREATE TABLE user_sessions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    session_token VARCHAR(64) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    empresa_id VARCHAR(5) NOT NULL,
    ip_address VARCHAR(45),                    -- Soporta IPv4 e IPv6
    created_at DATETIME DEFAULT GETDATE(),     -- Fecha de login
    last_activity DATETIME DEFAULT GETDATE(),  -- Ultima actividad
    CONSTRAINT FK_user_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
GO

-- Indices para busquedas rapidas
CREATE INDEX IX_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IX_user_sessions_empresa_id ON user_sessions(empresa_id);
CREATE INDEX IX_user_sessions_last_activity ON user_sessions(last_activity);
GO

PRINT 'Tabla user_sessions creada correctamente';
