-- ============================================================================
-- Script: 45_fix_columnas_sync_destino.sql
-- Descripcion: Anade al servidor DESTINO (10.1.99.4, BD cristal) las columnas
--              nuevas que existen en ORIGEN (192.168.100.5) y que provocaban
--              que el "bcp -n" (formato nativo) fallase en silencio dejando
--              las tablas vacias.
--
--              Sintoma: genter, venclientes, vencomerciales y almcolores
--              quedaban con 1 registro -> la ayuda de clientes no devolvia nada.
--
-- Fecha: 2026-09-14
-- Ejecutar en: SERVIDOR_DESTINO (10.1.99.4), base de datos [cristal]
-- ============================================================================

USE cristal;
GO

IF COL_LENGTH('dbo.genter', 'copia_agente') IS NULL
BEGIN
    ALTER TABLE dbo.genter ADD copia_agente varchar(1) NULL;
    PRINT 'genter.copia_agente anadida';
END
ELSE PRINT 'genter.copia_agente ya existe';
GO

IF COL_LENGTH('dbo.venclientes', 'adjuntar_declaracion_resp') IS NULL
BEGIN
    ALTER TABLE dbo.venclientes ADD adjuntar_declaracion_resp varchar(1) NULL;
    PRINT 'venclientes.adjuntar_declaracion_resp anadida';
END
ELSE PRINT 'venclientes.adjuntar_declaracion_resp ya existe';
GO

IF COL_LENGTH('dbo.vencomerciales', 'recibir_resumen_diario') IS NULL
BEGIN
    ALTER TABLE dbo.vencomerciales ADD recibir_resumen_diario varchar(1) NULL;
    PRINT 'vencomerciales.recibir_resumen_diario anadida';
END
ELSE PRINT 'vencomerciales.recibir_resumen_diario ya existe';
GO

IF COL_LENGTH('dbo.almcolores', 'tipocolor') IS NULL
BEGIN
    ALTER TABLE dbo.almcolores ADD tipocolor varchar(5) NULL;
    PRINT 'almcolores.tipocolor anadida';
END
ELSE PRINT 'almcolores.tipocolor ya existe';
GO

PRINT '============================================================';
PRINT 'Listo. Relanzar sincronizar_cristal.bat para cargar los datos.';
PRINT '============================================================';
GO
