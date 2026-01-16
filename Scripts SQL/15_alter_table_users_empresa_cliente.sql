-- ============================================================================
-- Script: 15_alter_table_users_empresa_cliente.sql
-- Description: Add empresa_id and cliente_id fields to users table
-- Database: ApiRestStocks
-- Date: 2026-01-04
-- ============================================================================

USE ApiRestStocks;
GO

-- ================== PART 1: Add empresa_id column ==================
IF NOT EXISTS (SELECT 1 FROM sys.columns
               WHERE object_id = OBJECT_ID('users')
               AND name = 'empresa_id')
BEGIN
    -- First add as NULL to handle existing records
    ALTER TABLE users
    ADD empresa_id VARCHAR(5) NULL;

    PRINT 'Column empresa_id added to users table';

    -- Update existing records with empresa_id = '1' (default)
    UPDATE users
    SET empresa_id = '1'
    WHERE empresa_id IS NULL;

    PRINT 'Existing users updated with empresa_id = ''1''';

    -- Now make column NOT NULL with DEFAULT '1'
    ALTER TABLE users
    ALTER COLUMN empresa_id VARCHAR(5) NOT NULL;

    -- Add default constraint
    ALTER TABLE users
    ADD CONSTRAINT DF_users_empresa_id DEFAULT '1' FOR empresa_id;

    PRINT 'Column empresa_id configured as NOT NULL with DEFAULT ''1''';
END
ELSE
BEGIN
    PRINT 'Column empresa_id already exists in users table';
END
GO

-- ================== PART 2: Add cliente_id column ==================
IF NOT EXISTS (SELECT 1 FROM sys.columns
               WHERE object_id = OBJECT_ID('users')
               AND name = 'cliente_id')
BEGIN
    -- Add as nullable (not all users need to be linked to a client)
    ALTER TABLE users
    ADD cliente_id VARCHAR(20) NULL;

    PRINT 'Column cliente_id added to users table';
END
ELSE
BEGIN
    PRINT 'Column cliente_id already exists in users table';
END
GO

-- ================== PART 3: Create indexes for performance ==================
IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE name = 'IX_users_empresa_id'
               AND object_id = OBJECT_ID('users'))
BEGIN
    CREATE INDEX IX_users_empresa_id ON users(empresa_id);
    PRINT 'Index IX_users_empresa_id created';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE name = 'IX_users_cliente_id'
               AND object_id = OBJECT_ID('users'))
BEGIN
    CREATE INDEX IX_users_cliente_id ON users(cliente_id);
    PRINT 'Index IX_users_cliente_id created';
END
GO

-- ================== PART 4: Create composite index ==================
IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE name = 'IX_users_empresa_cliente'
               AND object_id = OBJECT_ID('users'))
BEGIN
    CREATE INDEX IX_users_empresa_cliente ON users(empresa_id, cliente_id);
    PRINT 'Composite index IX_users_empresa_cliente created';
END
GO

-- Verify changes
SELECT
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.is_nullable,
    ISNULL(dc.definition, '') AS default_value
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
WHERE c.object_id = OBJECT_ID('users')
AND c.name IN ('empresa_id', 'cliente_id')
ORDER BY c.name;
GO

PRINT '============================================================================';
PRINT 'Script completed successfully';
PRINT 'IMPORTANT: Existing users have empresa_id = ''1'' and cliente_id = NULL';
PRINT '============================================================================';
