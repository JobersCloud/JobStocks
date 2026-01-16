-- ============================================
-- Script: 06_alter_table_users_pais.sql
-- Descripción: Añadir campo pais y verificación email a users
-- Base de datos: ApiRestStocks
-- ============================================

USE ApiRestStocks;
GO

-- Añadir campo pais
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'pais')
BEGIN
    ALTER TABLE users ADD pais VARCHAR(100) NULL;
    PRINT 'Campo pais añadido a tabla users';
END
GO

-- Añadir campo email_verificado
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'email_verificado')
BEGIN
    ALTER TABLE users ADD email_verificado BIT DEFAULT 0;
    PRINT 'Campo email_verificado añadido a tabla users';
END
GO

-- Añadir campo token_verificacion
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'token_verificacion')
BEGIN
    ALTER TABLE users ADD token_verificacion VARCHAR(100) NULL;
    PRINT 'Campo token_verificacion añadido a tabla users';
END
GO

-- Añadir campo token_expiracion
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'token_expiracion')
BEGIN
    ALTER TABLE users ADD token_expiracion DATETIME NULL;
    PRINT 'Campo token_expiracion añadido a tabla users';
END
GO

-- Marcar usuarios existentes como verificados
UPDATE users SET email_verificado = 1 WHERE email_verificado IS NULL OR email_verificado = 0;
PRINT 'Usuarios existentes marcados como verificados';
GO
