-- ============================================================================
-- Script: cleanup_test_user.sql
-- Descripción: Limpiar usuarios de prueba pendientes de verificación
-- Uso: Reemplaza 'TU_EMAIL_AQUI' con el email de prueba
-- ============================================================================

USE ApiRestStocks;
GO

-- Ver usuarios pendientes de verificación
SELECT
    id,
    username,
    email,
    full_name,
    pais,
    active,
    email_verificado,
    token_verificacion,
    token_expiracion
FROM users
WHERE email_verificado = 0;
GO

-- Eliminar usuario de prueba específico (REEMPLAZA EL EMAIL)
-- DELETE FROM users WHERE email = 'TU_EMAIL_AQUI' AND email_verificado = 0;
-- GO

-- O eliminar TODOS los usuarios no verificados (USAR CON CUIDADO)
-- DELETE FROM users WHERE email_verificado = 0;
-- GO

PRINT 'Para eliminar un usuario, descomenta una de las líneas DELETE arriba';
