-- =============================================
-- Script: 17_create_table_users_empresas.sql
-- Descripción: Crear tabla de relación users-empresas
--              Permite que un usuario tenga diferentes
--              cliente_id y rol en cada empresa
-- Fecha: 2026-01-04
-- =============================================

USE ApiRestStocks;
GO

-- 1. Crear la nueva tabla de relación
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users_empresas')
BEGIN
    CREATE TABLE users_empresas (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        empresa_id VARCHAR(5) NOT NULL,
        cliente_id VARCHAR(20) NULL,
        rol VARCHAR(20) NOT NULL DEFAULT 'usuario',
        fecha_creacion DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_users_empresas_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT UQ_user_empresa UNIQUE (user_id, empresa_id),
        CONSTRAINT CK_users_empresas_rol CHECK (rol IN ('usuario', 'administrador', 'superusuario'))
    );

    PRINT 'Tabla users_empresas creada correctamente';
END
ELSE
BEGIN
    PRINT 'La tabla users_empresas ya existe';
END
GO

-- 2. Crear índices para optimizar consultas
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_users_empresas_empresa')
BEGIN
    CREATE INDEX IX_users_empresas_empresa ON users_empresas(empresa_id);
    PRINT 'Índice IX_users_empresas_empresa creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_users_empresas_user')
BEGIN
    CREATE INDEX IX_users_empresas_user ON users_empresas(user_id);
    PRINT 'Índice IX_users_empresas_user creado';
END
GO

-- 3. Migrar datos existentes de users a users_empresas
-- Solo si hay datos en users con empresa_id
IF EXISTS (SELECT 1 FROM users WHERE empresa_id IS NOT NULL)
BEGIN
    INSERT INTO users_empresas (user_id, empresa_id, cliente_id, rol)
    SELECT
        id,
        ISNULL(empresa_id, '1'),
        cliente_id,
        ISNULL(rol, 'usuario')
    FROM users
    WHERE NOT EXISTS (
        SELECT 1 FROM users_empresas ue
        WHERE ue.user_id = users.id AND ue.empresa_id = ISNULL(users.empresa_id, '1')
    );

    PRINT 'Datos migrados de users a users_empresas';
END
GO

-- 4. Eliminar columnas de la tabla users (después de verificar migración)
-- NOTA: Ejecutar manualmente después de verificar que la migración fue exitosa

/*
-- Eliminar foreign keys si existen
-- ALTER TABLE users DROP CONSTRAINT IF EXISTS FK_xxx;

-- Eliminar columnas
ALTER TABLE users DROP COLUMN empresa_id;
ALTER TABLE users DROP COLUMN cliente_id;
ALTER TABLE users DROP COLUMN rol;

PRINT 'Columnas empresa_id, cliente_id y rol eliminadas de users';
*/

-- 5. Vista para facilitar consultas (usuario con datos de empresa)
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_users_con_empresa')
BEGIN
    DROP VIEW view_users_con_empresa;
END
GO

CREATE VIEW view_users_con_empresa AS
SELECT
    u.id,
    u.username,
    u.password_hash,
    u.email,
    u.full_name,
    u.pais,
    u.active,
    u.email_verificado,
    u.debe_cambiar_password,
    u.fecha_creacion,
    ue.empresa_id,
    ue.cliente_id,
    ue.rol
FROM users u
INNER JOIN users_empresas ue ON u.id = ue.user_id;
GO

PRINT 'Vista view_users_con_empresa creada';
GO

-- Verificar estructura
SELECT
    c.name AS columna,
    t.name AS tipo,
    c.max_length,
    c.is_nullable
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE object_id = OBJECT_ID('users_empresas')
ORDER BY c.column_id;
