-- ============================================================
-- Script 34: Añadir campos de bloqueo de cuenta a tabla users
-- Fecha: 2026-02-21
-- Descripción: Campos para controlar intentos fallidos de login
--              y bloqueo temporal de cuenta
-- ============================================================

-- Añadir campo para contar intentos fallidos de login
ALTER TABLE users ADD login_attempts INT DEFAULT 0;

-- Añadir campo para fecha/hora hasta la que está bloqueada la cuenta
ALTER TABLE users ADD locked_until DATETIME NULL;
