-- ============================================
-- Script: 11_alter_table_users_rol.sql
-- Descripción: Añadir campo rol a tabla users
-- Base de datos: ApiRestStocks
-- Fecha: 2025-12-30
-- ============================================

USE ApiRestStocks;
GO

-- Verificar si la columna ya existe antes de añadirla
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'rol'
)
BEGIN
    -- Añadir columna rol con valor por defecto 'usuario'
    ALTER TABLE users
    ADD rol VARCHAR(20) NOT NULL DEFAULT 'usuario';

    PRINT 'Columna rol añadida exitosamente';
END
ELSE
BEGIN
    PRINT 'La columna rol ya existe';
END
GO

-- Crear constraint para validar valores permitidos
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
    WHERE TABLE_NAME = 'users' AND CONSTRAINT_NAME = 'CHK_rol_values'
)
BEGIN
    ALTER TABLE users
    ADD CONSTRAINT CHK_rol_values
    CHECK (rol IN ('usuario', 'administrador', 'superusuario'));

    PRINT 'Constraint CHK_rol_values creado exitosamente';
END
GO

-- Crear índice para consultas por rol
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'idx_users_rol' AND object_id = OBJECT_ID('users')
)
BEGIN
    CREATE INDEX idx_users_rol ON users(rol);
    PRINT 'Índice idx_users_rol creado exitosamente';
END
GO

-- Actualizar usuarios existentes: el primer usuario será superusuario
-- (Opcional - ejecutar manualmente si se desea)
-- UPDATE users SET rol = 'superusuario' WHERE id = 1;

PRINT 'Script completado exitosamente';
