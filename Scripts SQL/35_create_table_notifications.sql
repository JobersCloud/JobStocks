-- ============================================================
-- Script 35: Crear tabla notifications
-- Fecha: 2026-02-21
-- Descripción: Tabla para almacenar notificaciones de usuarios
--              (cambios de estado en propuestas, respuestas a
--              consultas, nuevas propuestas para admins, etc.)
-- ============================================================

CREATE TABLE notifications (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    empresa_id VARCHAR(5) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    titulo NVARCHAR(200) NOT NULL,
    mensaje NVARCHAR(500),
    data NVARCHAR(MAX),
    leida BIT DEFAULT 0,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_user ON notifications(user_id, empresa_id, leida);
CREATE INDEX idx_notifications_fecha ON notifications(fecha_creacion DESC);
