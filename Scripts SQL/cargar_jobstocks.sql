-- ============================================
-- Script: cargar_jobstocks.sql
-- Descripcion: Copia las 15 tablas necesarias de cristal
--              desde servidor origen a servidor destino
--
-- Servidor Origen: 192.168.100.5 (cristal)
-- Servidor Destino: 10.1.99.4 (cristal)
--
-- Ejecutar desde: SSMS conectado a 10.1.99.4
-- ============================================

USE master;
GO

-- ============================================
-- PASO 1: Crear base de datos cristal si no existe
-- ============================================
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'cristal')
BEGIN
    CREATE DATABASE cristal;
    PRINT 'Base de datos cristal creada';
END
ELSE
BEGIN
    PRINT 'Base de datos cristal ya existe';
END
GO

-- ============================================
-- PASO 2: Configurar Linked Server al origen
-- ============================================
IF EXISTS (SELECT * FROM sys.servers WHERE name = 'SERVIDOR_ORIGEN')
BEGIN
    EXEC sp_dropserver 'SERVIDOR_ORIGEN', 'droplogins';
    PRINT 'Linked Server anterior eliminado';
END
GO

EXEC sp_addlinkedserver
    @server = 'SERVIDOR_ORIGEN',
    @srvproduct = '',
    @provider = 'SQLNCLI11',
    @datasrc = '192.168.100.5';
GO

EXEC sp_addlinkedsrvlogin
    @rmtsrvname = 'SERVIDOR_ORIGEN',
    @useself = 'FALSE',
    @locallogin = NULL,
    @rmtuser = 'sa',
    @rmtpassword = 'desa2012';
GO

PRINT 'Linked Server SERVIDOR_ORIGEN configurado';
GO

-- ============================================
-- PASO 3: Crear tablas y copiar datos
-- ============================================
USE cristal;
GO

-- ------------------------------------------
-- Tabla 1: empresas
-- ------------------------------------------
PRINT 'Procesando tabla: empresas...';
IF OBJECT_ID('dbo.empresas', 'U') IS NOT NULL DROP TABLE dbo.empresas;
SELECT * INTO dbo.empresas FROM SERVIDOR_ORIGEN.cristal.dbo.empresas;
PRINT '  - empresas: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 2: unidades
-- ------------------------------------------
PRINT 'Procesando tabla: unidades...';
IF OBJECT_ID('dbo.unidades', 'U') IS NOT NULL DROP TABLE dbo.unidades;
SELECT * INTO dbo.unidades FROM SERVIDOR_ORIGEN.cristal.dbo.unidades;
PRINT '  - unidades: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 3: formatos
-- ------------------------------------------
PRINT 'Procesando tabla: formatos...';
IF OBJECT_ID('dbo.formatos', 'U') IS NOT NULL DROP TABLE dbo.formatos;
SELECT * INTO dbo.formatos FROM SERVIDOR_ORIGEN.cristal.dbo.formatos;
PRINT '  - formatos: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 4: calidades
-- ------------------------------------------
PRINT 'Procesando tabla: calidades...';
IF OBJECT_ID('dbo.calidades', 'U') IS NOT NULL DROP TABLE dbo.calidades;
SELECT * INTO dbo.calidades FROM SERVIDOR_ORIGEN.cristal.dbo.calidades;
PRINT '  - calidades: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 5: almmodelos
-- ------------------------------------------
PRINT 'Procesando tabla: almmodelos...';
IF OBJECT_ID('dbo.almmodelos', 'U') IS NOT NULL DROP TABLE dbo.almmodelos;
SELECT * INTO dbo.almmodelos FROM SERVIDOR_ORIGEN.cristal.dbo.almmodelos;
PRINT '  - almmodelos: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 6: almcolores
-- ------------------------------------------
PRINT 'Procesando tabla: almcolores...';
IF OBJECT_ID('dbo.almcolores', 'U') IS NOT NULL DROP TABLE dbo.almcolores;
SELECT * INTO dbo.almcolores FROM SERVIDOR_ORIGEN.cristal.dbo.almcolores;
PRINT '  - almcolores: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 7: pallets
-- ------------------------------------------
PRINT 'Procesando tabla: pallets...';
IF OBJECT_ID('dbo.pallets', 'U') IS NOT NULL DROP TABLE dbo.pallets;
SELECT * INTO dbo.pallets FROM SERVIDOR_ORIGEN.cristal.dbo.pallets;
PRINT '  - pallets: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 8: articulos
-- ------------------------------------------
PRINT 'Procesando tabla: articulos...';
IF OBJECT_ID('dbo.articulos', 'U') IS NOT NULL DROP TABLE dbo.articulos;
SELECT * INTO dbo.articulos FROM SERVIDOR_ORIGEN.cristal.dbo.articulos;
PRINT '  - articulos: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 9: almlinubica
-- ------------------------------------------
PRINT 'Procesando tabla: almlinubica...';
IF OBJECT_ID('dbo.almlinubica', 'U') IS NOT NULL DROP TABLE dbo.almlinubica;
SELECT * INTO dbo.almlinubica FROM SERVIDOR_ORIGEN.cristal.dbo.almlinubica;
PRINT '  - almlinubica: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 10: almartcajas
-- ------------------------------------------
PRINT 'Procesando tabla: almartcajas...';
IF OBJECT_ID('dbo.almartcajas', 'U') IS NOT NULL DROP TABLE dbo.almartcajas;
SELECT * INTO dbo.almartcajas FROM SERVIDOR_ORIGEN.cristal.dbo.almartcajas;
PRINT '  - almartcajas: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 11: venliped
-- ------------------------------------------
PRINT 'Procesando tabla: venliped...';
IF OBJECT_ID('dbo.venliped', 'U') IS NOT NULL DROP TABLE dbo.venliped;
SELECT * INTO dbo.venliped FROM SERVIDOR_ORIGEN.cristal.dbo.venliped;
PRINT '  - venliped: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 12: venped
-- ------------------------------------------
PRINT 'Procesando tabla: venped...';
IF OBJECT_ID('dbo.venped', 'U') IS NOT NULL DROP TABLE dbo.venped;
SELECT * INTO dbo.venped FROM SERVIDOR_ORIGEN.cristal.dbo.venped;
PRINT '  - venped: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 13: genter (clientes)
-- ------------------------------------------
PRINT 'Procesando tabla: genter...';
IF OBJECT_ID('dbo.genter', 'U') IS NOT NULL DROP TABLE dbo.genter;
SELECT * INTO dbo.genter FROM SERVIDOR_ORIGEN.cristal.dbo.genter;
PRINT '  - genter: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 14: ps_articulo_imagen
-- ------------------------------------------
PRINT 'Procesando tabla: ps_articulo_imagen...';
IF OBJECT_ID('dbo.ps_articulo_imagen', 'U') IS NOT NULL DROP TABLE dbo.ps_articulo_imagen;
SELECT * INTO dbo.ps_articulo_imagen FROM SERVIDOR_ORIGEN.cristal.dbo.ps_articulo_imagen;
PRINT '  - ps_articulo_imagen: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ------------------------------------------
-- Tabla 15: articulo_ficha_tecnica
-- ------------------------------------------
PRINT 'Procesando tabla: articulo_ficha_tecnica...';
IF OBJECT_ID('dbo.articulo_ficha_tecnica', 'U') IS NOT NULL DROP TABLE dbo.articulo_ficha_tecnica;
SELECT * INTO dbo.articulo_ficha_tecnica FROM SERVIDOR_ORIGEN.cristal.dbo.articulo_ficha_tecnica;
PRINT '  - articulo_ficha_tecnica: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' filas copiadas';
GO

-- ============================================
-- PASO 4: Verificar tablas copiadas
-- ============================================
PRINT '';
PRINT '============================================';
PRINT 'RESUMEN DE TABLAS COPIADAS';
PRINT '============================================';

SELECT
    t.name AS Tabla,
    p.rows AS Filas
FROM sys.tables t
JOIN sys.partitions p ON t.object_id = p.object_id
WHERE p.index_id IN (0, 1)
  AND t.name IN (
    'empresas', 'unidades', 'formatos', 'calidades',
    'almmodelos', 'almcolores', 'pallets', 'articulos',
    'almlinubica', 'venliped', 'venped', 'genter',
    'ps_articulo_imagen', 'articulo_ficha_tecnica'
  )
ORDER BY t.name;
GO

-- ============================================
-- PASO 5: Limpiar Linked Server (opcional)
-- ============================================
-- Descomenta las siguientes lineas si quieres eliminar el linked server
-- EXEC sp_dropserver 'SERVIDOR_ORIGEN', 'droplogins';
-- PRINT 'Linked Server eliminado';
-- GO

PRINT '';
PRINT '============================================';
PRINT 'CARGA COMPLETADA EXITOSAMENTE';
PRINT '============================================';
GO
