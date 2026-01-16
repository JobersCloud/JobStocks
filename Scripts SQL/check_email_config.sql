-- ============================================================================
-- Script: check_email_config.sql
-- Descripción: Verificar configuración de email
-- ============================================================================

USE ApiRestStocks;
GO

-- Ver configuraciones de email existentes
SELECT
    id,
    nombre_configuracion,
    smtp_server,
    smtp_port,
    email_from,
    email_to,
    activo,
    fecha_creacion
FROM email_config;
GO

-- Ver si hay alguna configuración activa
SELECT
    id,
    nombre_configuracion,
    smtp_server,
    smtp_port,
    email_from,
    activo
FROM email_config
WHERE activo = 1;
GO

PRINT 'Si no hay configuración activa, los emails de verificación no se enviarán';
PRINT 'Usa el endpoint /api/email-config para configurar SMTP desde el frontend';
