-- ============================================
-- Script: 19_alter_table_empresa_logo_invertir.sql
-- Descripción: Añade campo para invertir logo en header
-- Fecha: 2026-01-08
-- ============================================

-- Añadir campo invertir_logo a la tabla empresa_logo
-- Si es 1, el logo se invierte (filtro brightness(0) invert(1)) para verse bien sobre fondo rojo
-- Si es 0 o NULL, el logo se muestra sin filtro

ALTER TABLE empresa_logo
ADD invertir_logo BIT DEFAULT 0;

GO

-- Comentario del campo
EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Si es 1, aplica filtro de inversión al logo para headers oscuros/rojos. Si es 0, muestra logo sin filtro.',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'empresa_logo',
    @level2type = N'COLUMN', @level2name = N'invertir_logo';
