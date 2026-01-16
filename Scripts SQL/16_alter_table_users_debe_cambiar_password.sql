-- ============================================================================
-- Script: 16_alter_table_users_debe_cambiar_password.sql
-- Description: Add debe_cambiar_password field to users table
-- Database: ApiRestStocks
-- Date: 2026-01-04
-- ============================================================================

USE ApiRestStocks;
GO

-- ================== Add debe_cambiar_password column ==================
IF NOT EXISTS (SELECT 1 FROM sys.columns
               WHERE object_id = OBJECT_ID('users')
               AND name = 'debe_cambiar_password')
BEGIN
    ALTER TABLE users
    ADD debe_cambiar_password BIT NOT NULL DEFAULT 0;

    PRINT 'Column debe_cambiar_password added to users table';
END
ELSE
BEGIN
    PRINT 'Column debe_cambiar_password already exists in users table';
END
GO

-- Verify changes
SELECT
    c.name AS column_name,
    t.name AS data_type,
    c.is_nullable,
    ISNULL(dc.definition, '') AS default_value
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
WHERE c.object_id = OBJECT_ID('users')
AND c.name = 'debe_cambiar_password';
GO

PRINT '============================================================================';
PRINT 'Script completed successfully';
PRINT '============================================================================';
