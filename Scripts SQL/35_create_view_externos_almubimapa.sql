-- ============================================
-- Script: 35_create_view_externos_almubimapa.sql
-- Descripcion: Vista para mapa de ubicaciones del almacen (definicion de huecos)
-- Tabla origen: cristal.dbo.almubimapa
-- ============================================

CREATE VIEW [dbo].[view_externos_almubimapa]
AS
SELECT [empresa]
      ,[almacen]
      ,[zona]
      ,[fila_desde]
      ,[fila_hasta]
      ,[altura_desde]
      ,[altura_hasta]
      ,[largo]
  FROM [cristal].[dbo].[almubimapa]
GO
