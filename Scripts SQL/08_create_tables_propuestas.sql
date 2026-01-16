-- ============================================
-- Tablas: propuestas y propuestas_lineas
-- Descripcion: Almacenar solicitudes enviadas por email
-- Base de datos: ApiRestStocks
-- ============================================

USE ApiRestStocks;
GO

-- ============================================
-- Tabla: propuestas (Cabecera)
-- ============================================
CREATE TABLE propuestas (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    fecha DATETIME DEFAULT GETDATE(),
    comentarios NVARCHAR(MAX),
    estado VARCHAR(20) DEFAULT 'Enviada',
    total_items INT,
    fecha_modificacion DATETIME,

    CONSTRAINT FK_propuestas_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT CHK_propuestas_estado CHECK (estado IN ('Enviada', 'Procesada', 'Cancelada'))
);
GO

-- Indices para propuestas
CREATE INDEX idx_propuestas_user_id ON propuestas(user_id);
CREATE INDEX idx_propuestas_fecha ON propuestas(fecha);
CREATE INDEX idx_propuestas_estado ON propuestas(estado);
GO

-- Trigger para actualizar fecha_modificacion
CREATE TRIGGER trg_propuestas_updated_at
ON propuestas
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE propuestas
    SET fecha_modificacion = GETDATE()
    FROM propuestas p
    INNER JOIN inserted i ON p.id = i.id;
END;
GO

-- ============================================
-- Tabla: propuestas_lineas (Detalle)
-- ============================================
CREATE TABLE propuestas_lineas (
    id INT IDENTITY(1,1) PRIMARY KEY,
    propuesta_id INT NOT NULL,
    codigo VARCHAR(50),
    descripcion NVARCHAR(200),
    formato VARCHAR(50),
    calidad VARCHAR(20),
    color VARCHAR(50),
    tono VARCHAR(20),
    calibre VARCHAR(20),
    pallet VARCHAR(50),
    caja VARCHAR(50),
    unidad VARCHAR(20),
    existencias DECIMAL(18,2),
    cantidad_solicitada DECIMAL(18,2),

    CONSTRAINT FK_propuestas_lineas_propuesta FOREIGN KEY (propuesta_id) REFERENCES propuestas(id) ON DELETE CASCADE
);
GO

-- Indices para propuestas_lineas
CREATE INDEX idx_propuestas_lineas_propuesta_id ON propuestas_lineas(propuesta_id);
CREATE INDEX idx_propuestas_lineas_codigo ON propuestas_lineas(codigo);
GO

PRINT 'Tablas propuestas y propuestas_lineas creadas exitosamente';
GO
