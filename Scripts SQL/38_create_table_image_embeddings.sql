-- ============================================================
-- Script: 38_create_table_image_embeddings.sql
-- Descripcion: Tabla para almacenar embeddings de imagenes
-- para busqueda visual (CBIR - Content-Based Image Retrieval)
-- Fecha: 2026-02-25
-- ============================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'image_embeddings')
BEGIN
    CREATE TABLE image_embeddings (
        id INT IDENTITY(1,1) PRIMARY KEY,
        imagen_id INT NOT NULL,
        codigo VARCHAR(50) NOT NULL,
        empresa_id VARCHAR(5) NOT NULL DEFAULT '1',
        embedding VARBINARY(MAX) NOT NULL,
        embedding_type VARCHAR(20) DEFAULT 'histogram',
        created_at DATETIME DEFAULT GETDATE()
    );

    CREATE INDEX IX_embeddings_codigo ON image_embeddings(codigo);
    CREATE INDEX IX_embeddings_empresa ON image_embeddings(empresa_id);

    PRINT 'Tabla image_embeddings creada correctamente';
END
ELSE
BEGIN
    PRINT 'La tabla image_embeddings ya existe';
END
GO
