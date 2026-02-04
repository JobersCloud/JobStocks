-- ============================================================
--      Script: 30_alter_table_users_cif_nif.sql
--      Descripcion: Añade campo CIF/VAT/NIF a tabla users
--      Fecha: 2026-02-04
-- ============================================================

-- Añadir columna cif_nif (opcional)
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('users') AND name = 'cif_nif'
)
BEGIN
    ALTER TABLE users ADD cif_nif VARCHAR(50) NULL;
    PRINT 'Columna cif_nif añadida a tabla users';
END
ELSE
BEGIN
    PRINT 'La columna cif_nif ya existe en tabla users';
END
GO
