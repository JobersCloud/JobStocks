-- ============================================================================
-- Script: activate_pending_users.sql
-- Descripción: Activar usuarios pendientes de verificación de email
-- Uso: Solo para entorno de desarrollo/pruebas
-- ============================================================================

USE ApiRestStocks;
GO

-- Ver usuarios pendientes de verificación
PRINT 'Usuarios pendientes de verificación:';
SELECT
    id,
    username,
    email,
    full_name,
    pais,
    active,
    email_verificado
FROM users
WHERE email_verificado = 0;
GO

-- Activar todos los usuarios pendientes
UPDATE users
SET
    active = 1,
    email_verificado = 1,
    token_verificacion = NULL,
    token_expiracion = NULL
WHERE email_verificado = 0;
GO

PRINT 'Usuarios activados exitosamente';
PRINT 'Total de usuarios activados: ' + CAST(@@ROWCOUNT AS VARCHAR(10));
GO

-- Ver estado final
SELECT
    id,
    username,
    email,
    active,
    email_verificado
FROM users;
GO
