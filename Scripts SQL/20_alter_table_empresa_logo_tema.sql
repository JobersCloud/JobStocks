-- ============================================
-- Script: 20_alter_table_empresa_logo_tema.sql
-- Descripción: Añade campo para tema de colores por empresa
-- Fecha: 2026-01-08
-- ============================================

-- Añadir campo tema a la tabla empresa_logo
-- Valores posibles: 'rubi', 'zafiro', 'esmeralda', 'amatista', 'ambar', 'grafito'
-- Por defecto 'rubi' (el tema rojo actual)

ALTER TABLE empresa_logo
ADD tema VARCHAR(20) DEFAULT 'rubi';

GO

-- Comentario del campo
EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Tema de colores para la empresa. Valores: rubi (rojo), zafiro (azul), esmeralda (verde), amatista (purpura), ambar (naranja), grafito (gris)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'empresa_logo',
    @level2type = N'COLUMN', @level2name = N'tema';
