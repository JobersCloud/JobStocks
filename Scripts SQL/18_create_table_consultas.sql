-- =============================================
-- Script: 18_create_table_consultas.sql
-- Descripción: Tabla para consultas sobre productos
-- Fecha: 2026-01-04
-- =============================================

USE ApiRestStocks;
GO

-- 1. Crear tabla de consultas
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'consultas')
BEGIN
    CREATE TABLE consultas (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empresa_id VARCHAR(5) NOT NULL,
        -- Datos del producto consultado
        codigo_producto VARCHAR(50) NOT NULL,
        descripcion_producto VARCHAR(255),
        formato VARCHAR(50),
        calidad VARCHAR(50),
        color VARCHAR(50),
        tono VARCHAR(50),
        calibre VARCHAR(50),
        -- Datos del cliente
        nombre_cliente VARCHAR(100) NOT NULL,
        email_cliente VARCHAR(100) NOT NULL,
        telefono_cliente VARCHAR(20),
        -- Consulta
        mensaje TEXT NOT NULL,
        -- Usuario logueado (opcional)
        user_id INT NULL,
        -- Estado y seguimiento
        estado VARCHAR(20) DEFAULT 'pendiente',  -- pendiente, respondida, cerrada
        respuesta TEXT NULL,
        fecha_respuesta DATETIME NULL,
        respondido_por INT NULL,
        -- Timestamps
        fecha_creacion DATETIME DEFAULT GETDATE(),
        -- Foreign keys
        CONSTRAINT FK_consultas_user FOREIGN KEY (user_id) REFERENCES users(id),
        CONSTRAINT FK_consultas_respondido FOREIGN KEY (respondido_por) REFERENCES users(id),
        CONSTRAINT CK_consultas_estado CHECK (estado IN ('pendiente', 'respondida', 'cerrada'))
    );

    PRINT 'Tabla consultas creada correctamente';
END
ELSE
BEGIN
    PRINT 'La tabla consultas ya existe';
END
GO

-- 2. Crear índices
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_consultas_empresa')
BEGIN
    CREATE INDEX IX_consultas_empresa ON consultas(empresa_id);
    PRINT 'Índice IX_consultas_empresa creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_consultas_estado')
BEGIN
    CREATE INDEX IX_consultas_estado ON consultas(estado);
    PRINT 'Índice IX_consultas_estado creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_consultas_fecha')
BEGIN
    CREATE INDEX IX_consultas_fecha ON consultas(fecha_creacion DESC);
    PRINT 'Índice IX_consultas_fecha creado';
END
GO

-- 3. Insertar parámetro para número de WhatsApp (si no existe)
IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'WHATSAPP_NUMERO' AND empresa_id = '1')
BEGIN
    INSERT INTO parametros (clave, valor, descripcion, empresa_id)
    VALUES ('WHATSAPP_NUMERO', '', 'Número de WhatsApp para consultas (formato: 34XXXXXXXXX)', '1');
    PRINT 'Parámetro WHATSAPP_NUMERO creado para empresa 1';
END
GO

-- Verificar estructura
SELECT
    c.name AS columna,
    t.name AS tipo,
    c.max_length,
    c.is_nullable
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE object_id = OBJECT_ID('consultas')
ORDER BY c.column_id;
