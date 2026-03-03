-- ============================================================
-- Script: 39_alter_table_users_empresas_admin_clientes.sql
-- Fecha: 2026-02-28
-- Descripcion: Añadir campo administrador_clientes a users_empresas
--              Si está activo, el usuario puede cambiar el cliente
--              al confirmar una propuesta (buscador habilitado).
--              Si no, el cliente queda bloqueado al pre-asignado.
-- ============================================================

ALTER TABLE users_empresas ADD administrador_clientes BIT DEFAULT 0;
GO
