-- ============================================================
-- Script: 42_create_table_favoritos.sql
-- Descripción: Tabla de productos favoritos por usuario
-- Fecha: 2026-03-04
-- ============================================================

CREATE TABLE favoritos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    empresa_id VARCHAR(5) NOT NULL,
    codigo VARCHAR(50) NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_favoritos_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT UQ_favoritos_user_empresa_codigo UNIQUE (user_id, empresa_id, codigo)
);

CREATE INDEX idx_favoritos_user_empresa ON favoritos(user_id, empresa_id);
