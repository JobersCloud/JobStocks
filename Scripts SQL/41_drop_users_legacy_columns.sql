-- ============================================================
-- Script: 41_drop_users_legacy_columns.sql
-- Descripcion: Eliminar columnas empresa_id y cliente_id de
--              la tabla users, ya que están en users_empresas
-- Fecha: 2026-03-03
-- ============================================================
-- NOTA: Estos campos fueron añadidos por el script 15 y migrados
-- a users_empresas por el script 17. El backend ya lee
-- exclusivamente de users_empresas (ue.cliente_id, ue.empresa_id).
-- Mantenerlos en users genera confusión y datos desincronizados.
-- ============================================================

USE ApiRestStocks;
GO

-- ================== PART 1: Eliminar indices sobre cliente_id ==================

IF EXISTS (SELECT 1 FROM sys.indexes
           WHERE name = 'IX_users_cliente_id'
           AND object_id = OBJECT_ID('users'))
BEGIN
    DROP INDEX IX_users_cliente_id ON users;
    PRINT 'Indice IX_users_cliente_id eliminado';
END
GO

IF EXISTS (SELECT 1 FROM sys.indexes
           WHERE name = 'IX_users_empresa_cliente'
           AND object_id = OBJECT_ID('users'))
BEGIN
    DROP INDEX IX_users_empresa_cliente ON users;
    PRINT 'Indice IX_users_empresa_cliente eliminado';
END
GO

IF EXISTS (SELECT 1 FROM sys.indexes
           WHERE name = 'IX_users_empresa_id'
           AND object_id = OBJECT_ID('users'))
BEGIN
    DROP INDEX IX_users_empresa_id ON users;
    PRINT 'Indice IX_users_empresa_id eliminado';
END
GO

-- ================== PART 2: Eliminar columna cliente_id ==================

IF EXISTS (SELECT 1 FROM sys.columns
           WHERE object_id = OBJECT_ID('users')
           AND name = 'cliente_id')
BEGIN
    ALTER TABLE users DROP COLUMN cliente_id;
    PRINT 'Columna cliente_id eliminada de users';
END
GO

-- ================== PART 3: Eliminar columna empresa_id ==================

-- Primero eliminar el default constraint si existe
DECLARE @constraint_name NVARCHAR(200);
SELECT @constraint_name = dc.name
FROM sys.default_constraints dc
INNER JOIN sys.columns c ON dc.parent_object_id = c.object_id
    AND dc.parent_column_id = c.column_id
WHERE c.object_id = OBJECT_ID('users')
AND c.name = 'empresa_id';

IF @constraint_name IS NOT NULL
BEGIN
    EXEC('ALTER TABLE users DROP CONSTRAINT ' + @constraint_name);
    PRINT 'Constraint ' + @constraint_name + ' eliminado';
END
GO

IF EXISTS (SELECT 1 FROM sys.columns
           WHERE object_id = OBJECT_ID('users')
           AND name = 'empresa_id')
BEGIN
    ALTER TABLE users DROP COLUMN empresa_id;
    PRINT 'Columna empresa_id eliminada de users';
END
GO

-- ================== Verificacion ==================

PRINT '';
PRINT '============================================================';
PRINT 'Limpieza completada.';
PRINT 'Las columnas empresa_id y cliente_id de users han sido eliminadas.';
PRINT 'Estos datos se gestionan ahora exclusivamente en users_empresas.';
PRINT '============================================================';

-- Mostrar columnas actuales de users
SELECT c.name AS columna, t.name AS tipo, c.max_length, c.is_nullable
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('users')
ORDER BY c.column_id;
GO
