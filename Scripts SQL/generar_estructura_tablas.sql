-- ============================================
-- Script: generar_estructura_tablas.sql
-- Genera los CREATE TABLE de las 13 tablas
--
-- EJECUTAR SOLO EN: 192.168.100.5 (servidor ORIGEN)
-- ============================================

USE cristal;
GO

-- ============================================
-- CONTROL DE SEGURIDAD: Verificar servidor
-- ============================================
DECLARE @servidor VARCHAR(100) = CAST(CONNECTIONPROPERTY('local_net_address') AS VARCHAR(100));
DECLARE @nombre_servidor VARCHAR(100) = @@SERVERNAME;

PRINT '============================================';
PRINT 'VERIFICACION DE SERVIDOR';
PRINT '============================================';
PRINT 'Servidor conectado: ' + ISNULL(@nombre_servidor, 'desconocido');
PRINT 'IP del servidor: ' + ISNULL(@servidor, 'desconocido');
PRINT '';

-- Verificar que NO estamos en el servidor destino (10.1.99.4)
IF @servidor LIKE '%10.1.99.4%' OR @nombre_servidor LIKE '%10.1.99%'
BEGIN
    RAISERROR('============================================', 16, 1);
    RAISERROR('ERROR: SERVIDOR INCORRECTO!', 16, 1);
    RAISERROR('Este script debe ejecutarse en 192.168.100.5', 16, 1);
    RAISERROR('Estas conectado al servidor DESTINO (10.1.99.4)', 16, 1);
    RAISERROR('============================================', 16, 1);
    RETURN;
END

-- Verificar que estamos en el servidor origen
IF @servidor NOT LIKE '%192.168.100.5%' AND @nombre_servidor NOT LIKE '%192.168.100%'
BEGIN
    PRINT 'ADVERTENCIA: No se pudo confirmar que este es el servidor 192.168.100.5';
    PRINT 'IP detectada: ' + ISNULL(@servidor, 'NULL');
    PRINT '';
    PRINT 'Si estas seguro de que es el servidor correcto, continua.';
    PRINT 'De lo contrario, CANCELA la ejecucion (boton Cancelar o Ctrl+C)';
    PRINT '';
    WAITFOR DELAY '00:00:05'; -- Pausa de 5 segundos para que el usuario pueda cancelar
END
ELSE
BEGIN
    PRINT 'OK: Servidor ORIGEN verificado (192.168.100.5)';
END

PRINT '============================================';
PRINT '';
GO

SET NOCOUNT ON;

DECLARE @tablas TABLE (nombre VARCHAR(100));
INSERT INTO @tablas VALUES
    ('empresas'), ('unidades'), ('formatos'), ('calidades'),
    ('almmodelos'), ('almcolores'), ('pallets'), ('articulos'),
    ('almlinubica'), ('venliped'), ('venped'), ('genter'),
    ('ps_articulo_imagen'), ('articulo_ficha_tecnica');

DECLARE @tabla VARCHAR(100);
DECLARE @sql NVARCHAR(MAX);

PRINT '-- ============================================';
PRINT '-- CREAR BASE DE DATOS Y TABLAS EN DESTINO';
PRINT '-- Ejecutar en servidor: 10.1.99.4';
PRINT '-- ============================================';
PRINT '';
PRINT 'USE master;';
PRINT 'GO';
PRINT '';
PRINT 'IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = ''cristal'')';
PRINT 'BEGIN';
PRINT '    CREATE DATABASE cristal;';
PRINT 'END';
PRINT 'GO';
PRINT '';
PRINT 'USE cristal;';
PRINT 'GO';
PRINT '';

DECLARE tabla_cursor CURSOR FOR
SELECT nombre FROM @tablas;

OPEN tabla_cursor;
FETCH NEXT FROM tabla_cursor INTO @tabla;

WHILE @@FETCH_STATUS = 0
BEGIN
    PRINT '-- ------------------------------------------';
    PRINT '-- Tabla: ' + @tabla;
    PRINT '-- ------------------------------------------';
    PRINT 'IF OBJECT_ID(''dbo.' + @tabla + ''', ''U'') IS NOT NULL DROP TABLE dbo.' + @tabla + ';';
    PRINT 'GO';
    PRINT '';

    -- Generar CREATE TABLE
    SELECT @sql = 'CREATE TABLE dbo.' + @tabla + ' (' + CHAR(13) + CHAR(10) +
        STUFF((
            SELECT ',' + CHAR(13) + CHAR(10) + '    ' +
                c.COLUMN_NAME + ' ' +
                UPPER(c.DATA_TYPE) +
                CASE
                    WHEN c.DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar')
                        THEN '(' + CASE WHEN c.CHARACTER_MAXIMUM_LENGTH = -1 THEN 'MAX' ELSE CAST(c.CHARACTER_MAXIMUM_LENGTH AS VARCHAR) END + ')'
                    WHEN c.DATA_TYPE IN ('varbinary', 'binary')
                        THEN '(' + CASE WHEN c.CHARACTER_MAXIMUM_LENGTH = -1 THEN 'MAX' ELSE CAST(c.CHARACTER_MAXIMUM_LENGTH AS VARCHAR) END + ')'
                    WHEN c.DATA_TYPE IN ('decimal', 'numeric')
                        THEN '(' + CAST(c.NUMERIC_PRECISION AS VARCHAR) + ',' + CAST(c.NUMERIC_SCALE AS VARCHAR) + ')'
                    ELSE ''
                END +
                CASE WHEN c.IS_NULLABLE = 'NO' THEN ' NOT NULL' ELSE ' NULL' END
            FROM INFORMATION_SCHEMA.COLUMNS c
            WHERE c.TABLE_NAME = @tabla AND c.TABLE_SCHEMA = 'dbo'
            ORDER BY c.ORDINAL_POSITION
            FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 3, '    ') +
        CHAR(13) + CHAR(10) + ');'
    FROM INFORMATION_SCHEMA.TABLES t
    WHERE t.TABLE_NAME = @tabla AND t.TABLE_SCHEMA = 'dbo';

    PRINT @sql;
    PRINT 'GO';
    PRINT '';

    FETCH NEXT FROM tabla_cursor INTO @tabla;
END

CLOSE tabla_cursor;
DEALLOCATE tabla_cursor;

PRINT '-- ============================================';
PRINT '-- FIN DE SCRIPT DE CREACION DE TABLAS';
PRINT '-- ============================================';
GO
