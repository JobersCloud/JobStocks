-- ============================================================================
-- BASE DE DATOS: ApiRestStocks (BD del Cliente/Tenant)
-- Proposito: Tablas de la aplicacion web + vistas que apuntan al ERP (cristal).
--            Cada instalacion/cliente tiene su propia copia de esta BD.
-- ============================================================================
-- En UNDEFASA: dbname = ApiRestStocks
--              dbserver = host.docker.internal (Docker) o 192.168.0.50 (local)
-- ============================================================================

USE ApiRestStocks;
GO

-- ############################################################################
-- SECCION 1: TABLAS DE LA APLICACION
-- ############################################################################

-- ============================================================================
-- TABLA: users
-- Usuarios del sistema con autenticacion, roles y verificacion email.
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
BEGIN
    CREATE TABLE users (
        id                              INT IDENTITY(1,1) PRIMARY KEY,
        username                        NVARCHAR(50)    NOT NULL,
        password_hash                   NVARCHAR(255)   NOT NULL,
        email                           NVARCHAR(100)   NULL,
        full_name                       NVARCHAR(100)   NULL,
        active                          BIT             DEFAULT 1,
        created_at                      DATETIME        DEFAULT GETDATE(),
        updated_at                      DATETIME        DEFAULT GETDATE(),
        pais                            VARCHAR(100)    NULL,
        email_verificado                BIT             DEFAULT 0,
        token_verificacion              VARCHAR(100)    NULL,
        token_expiracion                DATETIME        NULL,
        rol                             VARCHAR(20)     NOT NULL DEFAULT 'usuario',
        debe_cambiar_password           BIT             NOT NULL DEFAULT 0,
        company_name                    NVARCHAR(200)   NULL,
        cif_nif                         VARCHAR(50)     NULL,
        fecha_ultimo_cambio_password    DATETIME        NULL,
        login_attempts                  INT             DEFAULT 0,
        locked_until                    DATETIME        NULL,
        CONSTRAINT UQ_users_username    UNIQUE (username),
        CONSTRAINT CHK_username_length  CHECK (LEN(username) >= 3),
        CONSTRAINT CHK_email_format     CHECK (email LIKE '%_@__%.__%' OR email IS NULL),
        CONSTRAINT CHK_rol_values       CHECK (rol IN ('usuario', 'administrador', 'superusuario'))
    );

    CREATE INDEX idx_username   ON users(username);
    CREATE INDEX idx_email      ON users(email);
    CREATE INDEX idx_active     ON users(active);
    CREATE INDEX idx_users_rol  ON users(rol);
END
GO

-- Trigger: actualizar updated_at automaticamente
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'trg_users_updated_at')
BEGIN
    EXEC('CREATE TRIGGER trg_users_updated_at ON users AFTER UPDATE AS
    BEGIN
        SET NOCOUNT ON;
        UPDATE users SET updated_at = GETDATE()
        FROM users u INNER JOIN inserted i ON u.id = i.id;
    END');
END
GO

-- ============================================================================
-- TABLA: users_empresas
-- Relacion N:M entre usuarios y empresas. Almacena rol, permisos
-- y visibilidad de modulos por cada combinacion usuario-empresa.
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users_empresas')
BEGIN
    CREATE TABLE users_empresas (
        id                      INT IDENTITY(1,1) PRIMARY KEY,
        user_id                 INT             NOT NULL,
        empresa_id              VARCHAR(5)      NOT NULL,
        cliente_id              VARCHAR(20)     NULL,           -- Codigo cliente ERP
        rol                     VARCHAR(20)     NOT NULL DEFAULT 'usuario',
        mostrar_precios         BIT             DEFAULT 0,      -- Mostrar precios en grid
        administrador_clientes  BIT             DEFAULT 0,      -- Admin de clientes (comercial)
        visible_pedidos         BIT             DEFAULT 0,      -- Ver seccion pedidos
        visible_albaranes       BIT             DEFAULT 0,      -- Ver seccion albaranes
        visible_facturas        BIT             DEFAULT 0,      -- Ver seccion facturas
        visible_propuestas      BIT             DEFAULT 1,      -- Ver seccion propuestas
        visible_stock_anulados  BIT             DEFAULT 0,      -- Ver stock anulados
        control                 VARCHAR(20)     NULL,           -- Codigo comercial ERP (vincula clientes)
        fecha_creacion          DATETIME        DEFAULT GETDATE(),
        CONSTRAINT FK_users_empresas_user   FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT UQ_user_empresa          UNIQUE (user_id, empresa_id),
        CONSTRAINT CK_users_empresas_rol    CHECK (rol IN ('usuario', 'administrador', 'superusuario'))
    );

    CREATE INDEX IX_users_empresas_empresa ON users_empresas(empresa_id);
    CREATE INDEX IX_users_empresas_user    ON users_empresas(user_id);
END
GO

-- ============================================================================
-- TABLA: email_config
-- Configuraciones SMTP por empresa. Soporta autenticacion basica y OAuth2.
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'email_config')
BEGIN
    CREATE TABLE email_config (
        id                      INT IDENTITY(1,1) PRIMARY KEY,
        nombre_configuracion    VARCHAR(100)    NOT NULL,
        smtp_server             VARCHAR(200)    NOT NULL,
        smtp_port               INT             NOT NULL,
        email_from              VARCHAR(200)    NOT NULL,
        email_password          VARCHAR(500)    NOT NULL,
        email_to                VARCHAR(200)    NOT NULL,
        activo                  BIT             NOT NULL DEFAULT 1,
        fecha_creacion          DATETIME        NOT NULL DEFAULT GETDATE(),
        fecha_modificacion      DATETIME        NULL,
        empresa_id              VARCHAR(5)      NOT NULL DEFAULT '1',
        auth_method             VARCHAR(10)     DEFAULT 'basic',        -- 'basic' o 'oauth2'
        oauth2_tenant_id        VARCHAR(100)    NULL,
        oauth2_client_id        VARCHAR(100)    NULL,
        oauth2_client_secret    VARCHAR(500)    NULL
    );

    CREATE INDEX IX_email_config_empresa_id ON email_config(empresa_id);
END
GO

-- ============================================================================
-- TABLA: api_keys
-- Claves API para integraciones externas (ej: PowerBuilder, ERP).
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'api_keys')
BEGIN
    CREATE TABLE api_keys (
        id                  INT IDENTITY(1,1) PRIMARY KEY,
        user_id             INT             NOT NULL,
        api_key             VARCHAR(64)     NOT NULL UNIQUE,
        nombre              VARCHAR(100)    NOT NULL,
        activo              BIT             DEFAULT 1,
        fecha_creacion      DATETIME        DEFAULT GETDATE(),
        fecha_ultimo_uso    DATETIME        NULL,
        connection          VARCHAR(10)     NULL,           -- Soporte multi-empresa
        CONSTRAINT FK_api_keys_user FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE INDEX idx_api_key ON api_keys(api_key);
END
GO

-- ============================================================================
-- TABLA: parametros
-- Configuracion clave-valor por empresa. Controla funcionalidades del sistema.
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parametros')
BEGIN
    CREATE TABLE parametros (
        id                  INT IDENTITY(1,1) PRIMARY KEY,
        clave               VARCHAR(50)     NOT NULL,
        valor               VARCHAR(500)    NOT NULL,
        descripcion         VARCHAR(200)    NULL,
        fecha_modificacion  DATETIME        DEFAULT GETDATE(),
        empresa_id          VARCHAR(5)      NOT NULL DEFAULT '1'
    );

    CREATE UNIQUE INDEX UQ_parametros_clave_empresa ON parametros(clave, empresa_id);
    CREATE INDEX IX_parametros_empresa_id ON parametros(empresa_id);
END
GO

-- Parametros conocidos (insertar por empresa):
-- PERMITIR_REGISTRO          '0'   Registro publico de usuarios
-- PERMITIR_PROPUESTAS        '1'   Funcionalidad de propuestas/carrito
-- WHATSAPP_NUMERO            ''    Numero WhatsApp contacto
-- GRID_CON_IMAGENES          '0'   Mostrar imagenes en grid
-- PAGINACION_GRID            '1'   Activar paginacion backend
-- PAGINACION_LIMITE          '50'  Registros por pagina
-- PERMITIR_FIRMA             '1'   Firma en propuestas
-- MODO_ESPEJO                '0'   Sincronizacion espejo
-- FECHA_ULTIMA_SINCRONIZACION ''   Ultima sync BCP
-- PERMITIR_BUSQUEDA_VOZ      '0'   Busqueda por voz
-- MOSTRAR_PRECIOS            '0'   Precios en grid
-- STOCK_COLUMNAS_OPCIONALES  '[]'  JSON array columnas opcionales
-- VISIBLE_PEDIDOS            '0'   Seccion pedidos visible globalmente
-- VISIBLE_ALBARANES          '0'   Seccion albaranes visible
-- VISIBLE_FACTURAS           '0'   Seccion facturas visible
-- VISIBLE_PROPUESTAS         '1'   Seccion propuestas visible
-- VISIBLE_STOCK_ANULADOS     '0'   Stock anulados visible
-- FACTURAS_PDF_DIRECTORIO    ''    Ruta PDFs facturas
-- VISIBLE_BUSQUEDA_MAGICA    '1'   Busqueda magica visible

-- ============================================================================
-- TABLA: propuestas (Cabecera de solicitudes/pedidos web)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'propuestas')
BEGIN
    CREATE TABLE propuestas (
        id                  INT IDENTITY(1,1) PRIMARY KEY,
        user_id             INT             NOT NULL,
        fecha               DATETIME        DEFAULT GETDATE(),
        comentarios         NVARCHAR(MAX)   NULL,
        estado              VARCHAR(20)     DEFAULT 'Enviada',
        total_items         INT             NULL,
        fecha_modificacion  DATETIME        NULL,
        empresa_id          VARCHAR(5)      NOT NULL DEFAULT '1',
        referencia          VARCHAR(100)    NULL,           -- Referencia del cliente
        cliente_id          VARCHAR(20)     NULL,           -- Codigo cliente ERP
        CONSTRAINT FK_propuestas_user       FOREIGN KEY (user_id) REFERENCES users(id),
        CONSTRAINT CHK_propuestas_estado    CHECK (estado IN ('Enviada', 'Procesada', 'Cancelada'))
    );

    CREATE INDEX idx_propuestas_user_id     ON propuestas(user_id);
    CREATE INDEX idx_propuestas_fecha       ON propuestas(fecha);
    CREATE INDEX idx_propuestas_estado      ON propuestas(estado);
    CREATE INDEX IX_propuestas_empresa_id   ON propuestas(empresa_id);
    CREATE INDEX IX_propuestas_cliente_id   ON propuestas(cliente_id);
END
GO

-- Trigger: actualizar fecha_modificacion
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'trg_propuestas_updated_at')
BEGIN
    EXEC('CREATE TRIGGER trg_propuestas_updated_at ON propuestas AFTER UPDATE AS
    BEGIN
        SET NOCOUNT ON;
        UPDATE propuestas SET fecha_modificacion = GETDATE()
        FROM propuestas p INNER JOIN inserted i ON p.id = i.id;
    END');
END
GO

-- ============================================================================
-- TABLA: propuestas_lineas (Detalle/lineas de solicitudes)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'propuestas_lineas')
BEGIN
    CREATE TABLE propuestas_lineas (
        id                      INT IDENTITY(1,1) PRIMARY KEY,
        propuesta_id            INT             NOT NULL,
        codigo                  VARCHAR(50)     NULL,
        descripcion             NVARCHAR(200)   NULL,
        formato                 VARCHAR(50)     NULL,
        calidad                 VARCHAR(20)     NULL,
        color                   VARCHAR(50)     NULL,
        tono                    VARCHAR(20)     NULL,
        calibre                 VARCHAR(20)     NULL,
        pallet                  VARCHAR(50)     NULL,
        caja                    VARCHAR(50)     NULL,
        unidad                  VARCHAR(20)     NULL,
        existencias             DECIMAL(18,2)   NULL,
        cantidad_solicitada     DECIMAL(18,2)   NULL,
        CONSTRAINT FK_propuestas_lineas_propuesta FOREIGN KEY (propuesta_id)
            REFERENCES propuestas(id) ON DELETE CASCADE
    );

    CREATE INDEX idx_propuestas_lineas_propuesta_id ON propuestas_lineas(propuesta_id);
    CREATE INDEX idx_propuestas_lineas_codigo       ON propuestas_lineas(codigo);
END
GO

-- ============================================================================
-- TABLA: consultas (Consultas sobre productos enviadas por usuarios)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'consultas')
BEGIN
    CREATE TABLE consultas (
        id                      INT IDENTITY(1,1) PRIMARY KEY,
        empresa_id              VARCHAR(5)      NOT NULL,
        codigo_producto         VARCHAR(50)     NOT NULL,
        descripcion_producto    VARCHAR(255)    NULL,
        formato                 VARCHAR(50)     NULL,
        calidad                 VARCHAR(50)     NULL,
        color                   VARCHAR(50)     NULL,
        tono                    VARCHAR(50)     NULL,
        calibre                 VARCHAR(50)     NULL,
        nombre_cliente          VARCHAR(100)    NOT NULL,
        email_cliente           VARCHAR(100)    NOT NULL,
        telefono_cliente        VARCHAR(20)     NULL,
        mensaje                 TEXT            NOT NULL,
        user_id                 INT             NULL,
        estado                  VARCHAR(20)     DEFAULT 'pendiente',
        respuesta               TEXT            NULL,
        fecha_respuesta         DATETIME        NULL,
        respondido_por          INT             NULL,
        fecha_creacion          DATETIME        DEFAULT GETDATE(),
        CONSTRAINT FK_consultas_user        FOREIGN KEY (user_id) REFERENCES users(id),
        CONSTRAINT FK_consultas_respondido  FOREIGN KEY (respondido_por) REFERENCES users(id),
        CONSTRAINT CK_consultas_estado      CHECK (estado IN ('pendiente', 'respondida', 'cerrada'))
    );

    CREATE INDEX IX_consultas_empresa   ON consultas(empresa_id);
    CREATE INDEX IX_consultas_estado    ON consultas(estado);
    CREATE INDEX IX_consultas_fecha     ON consultas(fecha_creacion DESC);
END
GO

-- ============================================================================
-- TABLA: empresa_logo (Logos, favicons y tema de color por empresa)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'empresa_logo')
BEGIN
    CREATE TABLE empresa_logo (
        codigo              VARCHAR(5)      NOT NULL PRIMARY KEY,   -- empresa_id
        logo                VARBINARY(MAX)  NULL,                   -- Logo binario
        favicon             VARBINARY(MAX)  NULL,                   -- Favicon binario
        tema                VARCHAR(20)     DEFAULT 'rubi',         -- rubi|zafiro|esmeralda|amatista|ambar|grafito
        invertir_logo       BIT             DEFAULT 0,              -- Invertir colores en header
        fecha_creacion      DATETIME        DEFAULT GETDATE(),
        fecha_modificacion  DATETIME        DEFAULT GETDATE()
    );
END
GO

-- ============================================================================
-- TABLA: user_sessions (Sesiones activas para tracking y expulsion)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_sessions')
BEGIN
    CREATE TABLE user_sessions (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        session_token   VARCHAR(64)     NOT NULL UNIQUE,
        user_id         INT             NOT NULL,
        empresa_id      VARCHAR(5)      NOT NULL,
        ip_address      VARCHAR(45)     NULL,               -- IPv4 o IPv6
        created_at      DATETIME        DEFAULT GETDATE(),
        last_activity   DATETIME        DEFAULT GETDATE(),
        CONSTRAINT FK_user_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE INDEX IX_user_sessions_user_id       ON user_sessions(user_id);
    CREATE INDEX IX_user_sessions_empresa_id    ON user_sessions(empresa_id);
    CREATE INDEX IX_user_sessions_last_activity ON user_sessions(last_activity);
END
GO

-- ============================================================================
-- TABLA: audit_log (Auditoria de acciones de usuarios)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'audit_log')
BEGIN
    CREATE TABLE audit_log (
        id          INT IDENTITY(1,1) PRIMARY KEY,
        fecha       DATETIME        DEFAULT GETDATE() NOT NULL,
        user_id     INT             NULL,
        username    VARCHAR(100)    NULL,
        empresa_id  VARCHAR(5)      NULL,
        accion      VARCHAR(50)     NOT NULL,       -- LOGIN, LOGOUT, USER_CREATE, etc.
        recurso     VARCHAR(100)    NULL,            -- Tipo recurso afectado
        recurso_id  VARCHAR(100)    NULL,            -- ID recurso (hasta 64 chars hex)
        ip_address  VARCHAR(45)     NULL,
        user_agent  VARCHAR(1000)   NULL,
        detalles    NVARCHAR(MAX)   NULL,            -- JSON con detalles extra
        resultado   VARCHAR(20)     DEFAULT 'SUCCESS'-- SUCCESS, FAILED, BLOCKED
    );

    CREATE INDEX IX_audit_log_fecha     ON audit_log(fecha DESC);
    CREATE INDEX IX_audit_log_user      ON audit_log(user_id);
    CREATE INDEX IX_audit_log_accion    ON audit_log(accion);
    CREATE INDEX IX_audit_log_empresa   ON audit_log(empresa_id);
    CREATE INDEX IX_audit_log_resultado ON audit_log(resultado);
END
GO

-- ============================================================================
-- TABLA: notifications (Notificaciones push para usuarios)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'notifications')
BEGIN
    CREATE TABLE notifications (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        user_id         INT             NOT NULL,
        empresa_id      VARCHAR(5)      NOT NULL,
        tipo            VARCHAR(50)     NOT NULL,
        titulo          NVARCHAR(200)   NOT NULL,
        mensaje         NVARCHAR(500)   NULL,
        data            NVARCHAR(MAX)   NULL,           -- JSON payload
        leida           BIT             DEFAULT 0,
        fecha_creacion  DATETIME        DEFAULT GETDATE(),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE INDEX idx_notifications_user  ON notifications(user_id, empresa_id, leida);
    CREATE INDEX idx_notifications_fecha ON notifications(fecha_creacion DESC);
END
GO

-- ============================================================================
-- TABLA: favoritos (Productos favoritos por usuario con variante completa)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'favoritos')
BEGIN
    CREATE TABLE favoritos (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        user_id         INT             NOT NULL,
        empresa_id      VARCHAR(5)      NOT NULL,
        codigo          VARCHAR(50)     NOT NULL,
        calidad         VARCHAR(50)     NULL,
        tono            VARCHAR(50)     NULL,
        calibre         VARCHAR(50)     NULL,
        pallet          VARCHAR(50)     NULL,
        caja            VARCHAR(50)     NULL,
        fecha_creacion  DATETIME        DEFAULT GETDATE(),
        CONSTRAINT FK_favoritos_user FOREIGN KEY (user_id) REFERENCES users(id),
        CONSTRAINT UQ_favoritos_user_empresa_variante
            UNIQUE (user_id, empresa_id, codigo, calidad, tono, calibre, pallet, caja)
    );

    CREATE INDEX idx_favoritos_user_empresa ON favoritos(user_id, empresa_id);
END
GO

-- ============================================================================
-- TABLA: image_embeddings (Vectores de imagenes para busqueda visual)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'image_embeddings')
BEGIN
    CREATE TABLE image_embeddings (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        imagen_id       INT             NOT NULL,       -- Ref a ps_articulo_imagen.id
        codigo          VARCHAR(50)     NOT NULL,       -- Codigo articulo
        empresa_id      VARCHAR(5)      NOT NULL DEFAULT '1',
        embedding       VARBINARY(MAX)  NOT NULL,       -- Vector serializado
        embedding_type  VARCHAR(20)     DEFAULT 'histogram',
        created_at      DATETIME        DEFAULT GETDATE()
    );

    CREATE INDEX IX_embeddings_codigo  ON image_embeddings(codigo);
    CREATE INDEX IX_embeddings_empresa ON image_embeddings(empresa_id);
END
GO

-- ============================================================================
-- TABLA: backup_config (Configuraciones de backup de BD)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'backup_config')
BEGIN
    CREATE TABLE backup_config (
        id                  INT IDENTITY(1,1) PRIMARY KEY,
        empresa_id          VARCHAR(5)      NOT NULL,
        nombre              VARCHAR(100)    NOT NULL,
        tipo_bd             VARCHAR(10)     NOT NULL DEFAULT 'cliente',  -- cliente|central
        protocolo           VARCHAR(10)     NOT NULL DEFAULT 'local',   -- local|ftp|sftp
        ruta_local          VARCHAR(500)    NULL,
        host                VARCHAR(255)    NULL,
        puerto              INT             NULL DEFAULT 22,
        usuario             VARCHAR(100)    NULL,
        password            VARCHAR(500)    NULL,
        ruta_remota         VARCHAR(500)    NULL,
        frecuencia          VARCHAR(20)     NOT NULL DEFAULT 'manual',  -- manual|daily|weekly|monthly
        hora                INT             NULL DEFAULT 3,
        dia_semana          INT             NULL DEFAULT 1,
        dia_mes             INT             NULL DEFAULT 1,
        activo              BIT             DEFAULT 1,
        fecha_creacion      DATETIME        DEFAULT GETDATE(),
        fecha_modificacion  DATETIME        DEFAULT GETDATE(),
        ultima_ejecucion    DATETIME        NULL,
        CONSTRAINT UQ_backup_config_nombre UNIQUE (empresa_id, nombre)
    );
END
GO

-- ============================================================================
-- TABLA: backup_history (Historial de ejecuciones de backup)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'backup_history')
BEGIN
    CREATE TABLE backup_history (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        config_id       INT             NULL,           -- Ref a backup_config.id
        empresa_id      VARCHAR(5)      NOT NULL,
        tipo_bd         VARCHAR(10)     NOT NULL,
        nombre_archivo  VARCHAR(255)    NOT NULL,
        tamano_mb       DECIMAL(18,2)   NULL,
        estado          VARCHAR(20)     NOT NULL DEFAULT 'running',  -- running|success|error
        mensaje         NVARCHAR(MAX)   NULL,
        protocolo       VARCHAR(10)     NULL,
        destino         VARCHAR(500)    NULL,
        fecha_inicio    DATETIME        NOT NULL DEFAULT GETDATE(),
        fecha_fin       DATETIME        NULL,
        duracion_seg    INT             NULL,
        usuario_id      INT             NULL
    );

    CREATE INDEX idx_backup_history_empresa ON backup_history(empresa_id, fecha_inicio DESC);
END
GO

-- ============================================================================
-- TABLA: factura_pdf (Indice de PDFs de facturas en disco)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'factura_pdf')
BEGIN
    CREATE TABLE factura_pdf (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        empresa         VARCHAR(5)      NOT NULL,
        anyo            INT             NOT NULL,
        factura         INT             NOT NULL,
        filename        VARCHAR(500)    NOT NULL,
        fecha_registro  DATETIME        DEFAULT GETDATE()
    );

    CREATE INDEX idx_factura_pdf_lookup ON factura_pdf(empresa, anyo, factura);
END
GO


-- ############################################################################
-- SECCION 2: VISTAS (apuntan a cristal.dbo.* = BD ERP)
-- ############################################################################

-- ============================================================================
-- VISTA: view_users_con_empresa
-- Helper: JOIN users + users_empresas para consultas rapidas.
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_users_con_empresa')
    DROP VIEW view_users_con_empresa;
GO
CREATE VIEW view_users_con_empresa AS
SELECT
    u.id, u.username, u.password_hash, u.email, u.full_name,
    u.pais, u.active, u.email_verificado, u.debe_cambiar_password,
    u.created_at AS fecha_creacion,
    ue.empresa_id, ue.cliente_id, ue.rol
FROM users u
INNER JOIN users_empresas ue ON u.id = ue.user_id;
GO

-- ============================================================================
-- VISTA: view_externos_stock
-- Stock disponible con existencias netas (descontando pedidos pendientes).
-- Origen: cristal.dbo.almlinubica + tablas maestras
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_stock')
    DROP VIEW view_externos_stock;
GO
CREATE VIEW [dbo].[view_externos_stock] AS
SELECT
    almlinubica.empresa         AS empresa,
    almlinubica.articulo        AS codigo,
    almlinubica.referencia      AS referencia,
    almlinubica.tipo_pallet     AS tipo_pallet,
    articulos.descripcion       AS descripcion,
    formatos.abreviado          AS formato,
    almmodelos.descripcion      AS serie,
    calidades.abreviado         AS calidad,
    almlinubica.tonochar        AS tono,
    CONVERT(varchar, almlinubica.calibre) AS calibre,
    pallets.resumido            AS pallet,
    pallets.unidadescaja        AS unidadescaja,
    pallets.cajaspallet         AS cajaspallet,
    almcolores.descripcion      AS color,
    unidades.abreviado          AS unidad,
    ISNULL(SUM(almlinubica.existencias), 0) -
    ISNULL((SELECT SUM(venliped.cantidad)
            FROM cristal.dbo.venliped
            WHERE venliped.empresa = cristal.dbo.almlinubica.empresa
              AND venliped.referencia = cristal.dbo.almlinubica.referencia
              AND venliped.tipo_pallet = cristal.dbo.almlinubica.tipo_pallet
              AND venliped.situacion IN ('C','P')), 0) AS existencias
FROM cristal.dbo.almlinubica
    LEFT OUTER JOIN cristal.dbo.articulos   ON almlinubica.empresa = articulos.empresa  AND almlinubica.articulo = articulos.codigo
    LEFT OUTER JOIN cristal.dbo.formatos    ON articulos.empresa   = formatos.empresa   AND articulos.formato   = formatos.codigo
    LEFT OUTER JOIN cristal.dbo.almmodelos  ON articulos.empresa   = almmodelos.empresa AND articulos.modelo    = almmodelos.modelo
    LEFT OUTER JOIN cristal.dbo.calidades   ON almlinubica.empresa = calidades.empresa  AND almlinubica.calidad = calidades.codigo
    LEFT OUTER JOIN cristal.dbo.pallets     ON almlinubica.empresa = pallets.empresa     AND almlinubica.tipo_pallet = pallets.codigo
    LEFT OUTER JOIN cristal.dbo.almcolores  ON articulos.empresa   = almcolores.empresa AND articulos.color     = almcolores.color
    LEFT OUTER JOIN cristal.dbo.unidades    ON articulos.unidad    = unidades.codigo
GROUP BY
    almlinubica.empresa, almlinubica.articulo, almlinubica.referencia, almlinubica.tipo_pallet,
    articulos.descripcion, formatos.abreviado, almmodelos.descripcion, calidades.abreviado,
    almlinubica.tonochar, CONVERT(varchar, almlinubica.calibre),
    pallets.resumido, pallets.unidadescaja, pallets.cajaspallet,
    almcolores.descripcion, unidades.abreviado
HAVING
    ISNULL(SUM(almlinubica.existencias), 0) -
    ISNULL((SELECT SUM(venliped.cantidad)
            FROM cristal.dbo.venliped
            WHERE venliped.empresa = cristal.dbo.almlinubica.empresa
              AND venliped.referencia = cristal.dbo.almlinubica.referencia
              AND venliped.tipo_pallet = cristal.dbo.almlinubica.tipo_pallet
              AND venliped.situacion IN ('C','P')), 0) > 0;
GO

-- NOTA: En algunas instalaciones esta vista incluye columnas adicionales:
-- ean13, pesocaja, pesopallet, tipo_producto, piezascaja
-- Estas se anaden manualmente por instalacion segun las necesidades.

-- ============================================================================
-- VISTA: view_articulo_imagen
-- Imagenes de articulos (fotos + thumbnails).
-- Origen: cristal.dbo.ps_articulo_imagen
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_articulo_imagen')
    DROP VIEW view_articulo_imagen;
GO
CREATE VIEW view_articulo_imagen AS
SELECT id, empresa, articulo AS codigo, foto AS imagen, thumbnail
FROM cristal.dbo.ps_articulo_imagen;
GO

-- ============================================================================
-- VISTA: view_externos_clientes
-- Clientes del ERP (tipoter='C') con direccion.
-- Origen: cristal.dbo.genter
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_clientes')
    DROP VIEW view_externos_clientes;
GO
CREATE VIEW [dbo].[view_externos_clientes] AS
SELECT
    empresa, codigo, razon, domicilio,
    cod_postal AS codpos, poblacion, provincia, pais
FROM cristal.dbo.genter
WHERE tipoter = 'C';
GO

-- ============================================================================
-- VISTA: view_externos_venped (Pedidos - cabecera)
-- Origen: cristal.dbo.venped + genter
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_venped')
    DROP VIEW view_externos_venped;
GO
CREATE VIEW dbo.view_externos_venped AS
SELECT
    p.empresa, p.anyo, p.pedido,
    p.fpedido AS fecha, p.fentrega AS fecha_entrega,
    RTRIM(p.cliente) AS cliente,
    RTRIM(ISNULL(c.razon, '')) AS cliente_nombre,
    p.numpedcli AS pedido_cliente,
    RTRIM(ISNULL(p.serie, '')) AS serie,
    ISNULL(p.bruto, 0) AS bruto,
    ISNULL(p.importe_dto, 0) AS importe_dto,
    ISNULL(p.total_neto, 0) AS total,
    ISNULL(p.peso, 0) AS peso,
    RTRIM(ISNULL(p.divisa, '')) AS divisa,
    RTRIM(ISNULL(p.usuario, '')) AS usuario,
    p.falta AS fecha_alta
FROM cristal.dbo.venped p
LEFT JOIN cristal.dbo.genter c
    ON p.cliente = c.codigo AND p.empresa = c.empresa AND c.tipoter = 'C'
WHERE p.empresa IS NOT NULL AND p.anyo IS NOT NULL AND p.pedido IS NOT NULL;
GO

-- ============================================================================
-- VISTA: view_externos_venliped (Pedidos - lineas)
-- Origen: cristal.dbo.venliped
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_venliped')
    DROP VIEW view_externos_venliped;
GO
CREATE VIEW dbo.view_externos_venliped AS
SELECT
    empresa, anyo, pedido, linea,
    RTRIM(ISNULL(articulo, '')) AS articulo,
    RTRIM(ISNULL(descripcion, '')) AS descripcion,
    RTRIM(ISNULL(formato, '')) AS formato,
    RTRIM(ISNULL(calidad, '')) AS calidad,
    ISNULL(tono, 0) AS tono,
    ISNULL(calibre, 0) AS calibre,
    ISNULL(cantidad, 0) AS cantidad,
    ISNULL(precio, 0) AS precio,
    ISNULL(importe, 0) AS importe,
    ISNULL(pallets, 0) AS pallets,
    ISNULL(total_cajas, 0) AS cajas,
    fpedido AS fecha_pedido,
    fentrega AS fecha_entrega,
    RTRIM(ISNULL(situacion, '')) AS situacion
FROM cristal.dbo.venliped
WHERE empresa IS NOT NULL AND anyo IS NOT NULL AND pedido IS NOT NULL;
GO

-- ============================================================================
-- VISTA: view_externos_venalb (Albaranes - cabecera)
-- Origen: cristal.dbo.venalb + genter
-- Filtro: excluye depositos vacios
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_venalb')
    DROP VIEW view_externos_venalb;
GO
CREATE VIEW dbo.view_externos_venalb AS
SELECT
    a.empresa, a.anyo, a.albaran,
    a.falbaran AS fecha, a.fentrega AS fecha_entrega,
    RTRIM(a.cliente) AS cliente,
    RTRIM(ISNULL(c.razon, '')) AS cliente_nombre,
    RTRIM(ISNULL(a.serie, '')) AS serie,
    ISNULL(a.bruto, 0) AS bruto,
    ISNULL(a.importe_dto, 0) AS importe_dto,
    ISNULL(a.total_neto, 0) AS total,
    ISNULL(a.peso, 0) AS peso,
    RTRIM(ISNULL(a.divisa, '')) AS divisa,
    RTRIM(ISNULL(a.usuario, '')) AS usuario,
    a.falta AS fecha_alta
FROM cristal.dbo.venalb a
LEFT JOIN cristal.dbo.genter c
    ON a.cliente = c.codigo AND a.empresa = c.empresa AND c.tipoter = 'C'
WHERE a.empresa IS NOT NULL AND a.anyo IS NOT NULL AND a.albaran IS NOT NULL
  AND ISNULL(a.deposito, '') <> '';
GO

-- ============================================================================
-- VISTA: view_externos_venlialb (Albaranes - lineas)
-- Origen: cristal.dbo.venlialb
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_venlialb')
    DROP VIEW view_externos_venlialb;
GO
CREATE VIEW dbo.view_externos_venlialb AS
SELECT
    empresa, anyo, albaran, linea,
    RTRIM(ISNULL(articulo, '')) AS articulo,
    RTRIM(ISNULL(descripcion, '')) AS descripcion,
    RTRIM(ISNULL(formato, '')) AS formato,
    RTRIM(ISNULL(calidad, '')) AS calidad,
    ISNULL(tono, 0) AS tono,
    ISNULL(calibre, 0) AS calibre,
    ISNULL(cantidad, 0) AS cantidad,
    ISNULL(precio, 0) AS precio,
    ISNULL(importe, 0) AS importe,
    ISNULL(pallets, 0) AS pallets,
    ISNULL(total_cajas, 0) AS cajas,
    falbaran AS fecha,
    RTRIM(ISNULL(situacion, '')) AS situacion
FROM cristal.dbo.venlialb
WHERE empresa IS NOT NULL AND anyo IS NOT NULL AND albaran IS NOT NULL;
GO

-- ============================================================================
-- VISTA: view_externos_venfac (Facturas - cabecera)
-- Origen: cristal.dbo.venfac + genter
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_venfac')
    DROP VIEW view_externos_venfac;
GO
CREATE VIEW dbo.view_externos_venfac AS
SELECT
    f.empresa, f.anyo, f.factura,
    f.ffactura AS fecha,
    RTRIM(f.cliente) AS cliente,
    RTRIM(ISNULL(c.razon, '')) AS cliente_nombre,
    RTRIM(ISNULL(f.serie, '')) AS serie,
    ISNULL(f.total_neto - f.importe_dto, 0) AS base_imponible,
    ISNULL(f.iva, 0) AS iva,
    ISNULL(f.total_fac, 0) AS total,
    RTRIM(ISNULL(f.divisa, '')) AS divisa,
    RTRIM(ISNULL(f.usuario, '')) AS usuario,
    f.falta AS fecha_alta
FROM cristal.dbo.venfac f
LEFT JOIN cristal.dbo.genter c
    ON f.cliente = c.codigo AND f.empresa = c.empresa AND c.tipoter = 'C'
WHERE f.empresa IS NOT NULL AND f.anyo IS NOT NULL AND f.factura IS NOT NULL;
GO

-- ============================================================================
-- VISTA: view_externos_venlifac (Facturas - lineas)
-- Origen: cristal.dbo.venlifac
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_venlifac')
    DROP VIEW view_externos_venlifac;
GO
CREATE VIEW dbo.view_externos_venlifac AS
SELECT
    empresa, anyo, factura, linea,
    RTRIM(ISNULL(articulo, '')) AS articulo,
    RTRIM(ISNULL(descripcion, '')) AS descripcion,
    RTRIM(ISNULL(formato, '')) AS formato,
    RTRIM(ISNULL(calidad, '')) AS calidad,
    ISNULL(tono, 0) AS tono,
    ISNULL(calibre, 0) AS calibre,
    ISNULL(cantidad, 0) AS cantidad,
    ISNULL(precio, 0) AS precio,
    ISNULL(neto, 0) AS importe,
    ISNULL(pallets, 0) AS pallets,
    ISNULL(total_cajas, 0) AS cajas,
    ffactura AS fecha,
    RTRIM(ISNULL(situacion, '')) AS situacion
FROM cristal.dbo.venlifac
WHERE empresa IS NOT NULL AND anyo IS NOT NULL AND factura IS NOT NULL;
GO

-- ============================================================================
-- VISTA: view_externos_formatos
-- Catalogo de formatos.
-- Origen: cristal.dbo.formatos
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_formatos')
    DROP VIEW view_externos_formatos;
GO
CREATE VIEW [dbo].[view_externos_formatos] AS
SELECT empresa, codigo, abreviado
FROM cristal.dbo.formatos;
GO

-- ============================================================================
-- VISTA: view_externos_ubicaciones
-- Stock por ubicacion fisica en almacen (con existencias > 0).
-- Origen: cristal.dbo.almlinubica + tablas maestras
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_ubicaciones')
    DROP VIEW view_externos_ubicaciones;
GO
CREATE VIEW [dbo].[view_externos_ubicaciones] AS
SELECT
    u.empresa, u.almacen, u.zona, u.fila, u.altura, u.linea,
    u.articulo AS codigo,
    a.descripcion,
    f.abreviado AS formato,
    m.descripcion AS serie,
    cal.abreviado AS calidad,
    u.tono, u.tonochar, u.calibre, u.existencias, u.ubicacion,
    u.tipo_unidad AS unidad,
    u.referencia, u.tipo_pallet,
    p.resumido AS pallet,
    u.caja, u.sector, u.externo, u.f_alta, u.preferencia_carga
FROM cristal.dbo.almlinubica u
    LEFT OUTER JOIN cristal.dbo.articulos   a   ON u.empresa = a.empresa   AND u.articulo    = a.codigo
    LEFT OUTER JOIN cristal.dbo.formatos    f   ON a.empresa = f.empresa   AND a.formato     = f.codigo
    LEFT OUTER JOIN cristal.dbo.almmodelos  m   ON a.empresa = m.empresa   AND a.modelo      = m.modelo
    LEFT OUTER JOIN cristal.dbo.calidades   cal ON u.empresa = cal.empresa AND u.calidad     = cal.codigo
    LEFT OUTER JOIN cristal.dbo.pallets     p   ON u.empresa = p.empresa   AND u.tipo_pallet = p.codigo
WHERE u.existencias > 0;
GO

-- ============================================================================
-- VISTA: view_externos_almubimapa
-- Mapa fisico de ubicaciones del almacen.
-- Origen: cristal.dbo.almubimapa
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'view_externos_almubimapa')
    DROP VIEW view_externos_almubimapa;
GO
CREATE VIEW [dbo].[view_externos_almubimapa] AS
SELECT [empresa], [almacen], [zona],
       [fila_desde], [fila_hasta],
       [altura_desde], [altura_hasta],
       [largo]
FROM [cristal].[dbo].[almubimapa];
GO

-- ============================================================================
-- VISTAS OPCIONALES (creadas manualmente por instalacion):
--
-- view_externos_stock_anulados  - Stock de articulos anulados (misma estructura que view_externos_stock)
-- view_externos_almlinubica     - Detalle de almlinubica con lookups
-- view_externos_almalmacen      - Catalogo de almacenes (empresa, codigo, descripcion)
-- view_externos_empresas        - Catalogo de empresas (empresa, nombre)
-- view_comercial_clientes       - Mapeo comercial->clientes (cliente, control, empresa)
-- view_comerciales              - Lista de comerciales para autocomplete
-- view_externos_articulos_precios - Precios por formato+calidad (requiere tabla precios_formato_calidad)
-- ============================================================================
