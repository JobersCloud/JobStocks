-- ============================================
-- Script: 19_alter_table_propuestas_referencia.sql
-- Descripcion: Añade campo referencia a propuestas
-- Fecha: 2026-01-08
-- ============================================

-- Añadir campo referencia (opcional, para referencia del cliente)
ALTER TABLE propuestas
ADD referencia VARCHAR(100) NULL;

-- Comentario del campo
EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Referencia opcional del cliente para la propuesta',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'propuestas',
    @level2type = N'COLUMN', @level2name = 'referencia';

PRINT 'Campo referencia añadido a tabla propuestas';
