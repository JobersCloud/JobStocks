-- =============================================
-- Script: 24_create_table_audit_log.sql
-- Descripcion: Crear tabla de auditoria de usuarios
-- Base de datos: BD del cliente (misma que user_sessions)
-- Fecha: 2026-01-20
-- =============================================

-- Si la tabla existe sin IDENTITY, eliminarla y recrear
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'audit_log')
BEGIN
    DROP TABLE audit_log;
    PRINT 'Tabla audit_log eliminada para recrear con IDENTITY';
END
GO

-- Crear tabla audit_log con IDENTITY
CREATE TABLE audit_log (
    id INT IDENTITY(1,1) PRIMARY KEY,
    fecha DATETIME DEFAULT GETDATE() NOT NULL,
    user_id INT NULL,
    username VARCHAR(100) NULL,
    empresa_id VARCHAR(5) NULL,
    accion VARCHAR(50) NOT NULL,
    recurso VARCHAR(100) NULL,           -- tipo de recurso afectado
    recurso_id VARCHAR(100) NULL,        -- ID del recurso afectado (token hex 64 chars)
    ip_address VARCHAR(45) NULL,         -- IPv4 o IPv6
    user_agent VARCHAR(1000) NULL,       -- navegador/cliente (algunos son muy largos)
    detalles NVARCHAR(MAX) NULL,         -- JSON con detalles adicionales
    resultado VARCHAR(20) DEFAULT 'SUCCESS'  -- SUCCESS, FAILED, BLOCKED
);
GO

-- Indices para busquedas eficientes
CREATE INDEX IX_audit_log_fecha ON audit_log(fecha DESC);
CREATE INDEX IX_audit_log_user ON audit_log(user_id);
CREATE INDEX IX_audit_log_accion ON audit_log(accion);
CREATE INDEX IX_audit_log_empresa ON audit_log(empresa_id);
CREATE INDEX IX_audit_log_resultado ON audit_log(resultado);
GO

PRINT 'Tabla audit_log creada correctamente con IDENTITY';
GO
