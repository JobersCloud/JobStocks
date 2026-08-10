-- ============================================================================
-- BASE DE DATOS: jobers_control_usuarios (Central)
-- Proposito: Control central multi-tenant. Mapea dominios a conexiones
--            y almacena credenciales de BD por cada empresa/cliente.
-- ============================================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'jobers_control_usuarios')
BEGIN
    CREATE DATABASE jobers_control_usuarios;
END
GO

USE jobers_control_usuarios;
GO

-- ============================================================================
-- TABLA: empresa_cliente
-- Registro de todos los clientes/tenants del sistema.
-- Cada fila define la conexion a la BD de un cliente.
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'empresa_cliente')
BEGIN
    CREATE TABLE empresa_cliente (
        empresa_cli_id          INT IDENTITY(1,1) PRIMARY KEY,
        empresa_cli_nombre      VARCHAR(100)    NULL,       -- Nombre del tenant
        empresa_cli_dbserver    VARCHAR(200)    NULL,       -- Servidor SQL del cliente
        empresa_cli_dbport      INT             NULL,       -- Puerto (default 1433)
        empresa_cli_dblogin     VARCHAR(100)    NULL,       -- Usuario BD
        empresa_cli_dbpass      VARCHAR(200)    NULL,       -- Password BD
        empresa_cli_dbname      VARCHAR(100)    NULL,       -- Nombre BD (ej: ApiRestStocks)
        empresa_cli_correo_id   INT             NULL,       -- Referencia config email
        empresa_cli_key_ws      VARCHAR(200)    NULL,       -- API key web services
        empresa_cli_cif         VARCHAR(50)     NULL,       -- CIF/NIF empresa
        empresa_cli_traductor   VARCHAR(50)     NULL,       -- Flag traductor
        empresa_cli_tipo        INT             NULL,       -- Tipo de empresa
        empresa_erp             VARCHAR(20)     NULL        -- Codigo empresa en ERP (cristal)
    );
END
GO

-- ============================================================================
-- TABLA: dominios
-- Mapea subdominios/hostnames a un connection_id (empresa_cli_id)
-- para enrutamiento multi-tenant automatico.
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dominios')
BEGIN
    CREATE TABLE dominios (
        id                  INT IDENTITY(1,1) PRIMARY KEY,
        dominio             VARCHAR(255)    NOT NULL,       -- ej: stocks.undefasa.com
        connection_id       VARCHAR(10)     NOT NULL,       -- FK logica a empresa_cliente.empresa_cli_id
        descripcion         VARCHAR(255)    NULL,
        activo              BIT             DEFAULT 1,
        fecha_creacion      DATETIME        DEFAULT GETDATE(),
        fecha_modificacion  DATETIME        DEFAULT GETDATE()
    );

    CREATE UNIQUE INDEX IX_dominios_dominio ON dominios(dominio);
END
GO

-- ============================================================================
-- RELACION:
--   dominios.connection_id --> empresa_cliente.empresa_cli_id
--
-- FLUJO:
--   HTTP Request (hostname)
--     --> dominios (busca por dominio WHERE activo=1)
--     --> connection_id
--     --> empresa_cliente (busca por empresa_cli_id)
--     --> dbserver, dbport, dblogin, dbpass, dbname
--     --> Conexion dinamica a la BD del cliente (ApiRestStocks)
-- ============================================================================
