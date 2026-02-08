-- ============================================================
-- Script: 33_alter_table_users_password_expiry.sql
-- Descripcion: Añadir columna fecha_ultimo_cambio_password a users
-- Para expiración periódica de contraseñas
-- ============================================================

-- Añadir columna si no existe
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'fecha_ultimo_cambio_password'
)
BEGIN
    ALTER TABLE users ADD fecha_ultimo_cambio_password DATETIME NULL;

    -- Inicializar con la fecha actual para usuarios existentes
    UPDATE users SET fecha_ultimo_cambio_password = GETDATE();

    PRINT 'Columna fecha_ultimo_cambio_password añadida a users';
END
ELSE
BEGIN
    PRINT 'La columna fecha_ultimo_cambio_password ya existe';
END
GO
