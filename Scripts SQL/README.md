# Scripts SQL - ApiRestStocks

Scripts para crear la estructura de base de datos del proyecto.

## Orden de ejecución

Ejecutar en SQL Server Management Studio en este orden:

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `01_create_table_users.sql` | Tabla de usuarios para autenticación |
| 2 | `02_create_view_externos_stock.sql` | Vista de stock (requiere BD cristal) |
| 3 | `03_create_table_email_config.sql` | Configuración SMTP para emails |

## Requisitos previos

- SQL Server 2008 o superior
- Base de datos `ApiRestStocks` creada
- Acceso a base de datos `cristal` (para la vista de stock)

## Crear base de datos

```sql
CREATE DATABASE ApiRestStocks;
GO
```

## Notas

- La vista `view_externos_stock` depende de tablas en la BD `cristal`
- La tabla `users` incluye un trigger para actualizar `updated_at`
- Ejecutar `create_admin.py` después para crear el primer usuario
