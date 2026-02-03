-- ============================================
-- Script: 25_alter_table_users_company_name.sql
-- Fecha: 2026-02-03
-- Descripcion: Añade campo company_name a la tabla users
-- ============================================

-- Añadir campo company_name (opcional)
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'company_name'
)
BEGIN
    ALTER TABLE users ADD company_name NVARCHAR(200) NULL;
    PRINT 'Campo company_name añadido a la tabla users';
END
ELSE
BEGIN
    PRINT 'El campo company_name ya existe en la tabla users';
END
GO
