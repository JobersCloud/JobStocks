# ============================================================
#      ██╗ ██████╗ ██████╗ ███████╗██████╗ ███████╗
#      ██║██╔═══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝
#      ██║██║   ██║██████╔╝█████╗  ██████╔╝███████╗
# ██   ██║██║   ██║██╔══██╗██╔══╝  ██╔══██╗╚════██║
# ╚█████╔╝╚██████╔╝██████╔╝███████╗██║  ██║███████║
#  ╚════╝  ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝
#
#                ──  Jobers - Iaucejo  ──
#
# Autor : iaucejo
# Fecha : 2026-02-09
# ============================================================

"""
Definiciones de migraciones de BD para ApiRestExternos.

Cada migración tiene:
  - version (int): Número secuencial único
  - description (str): Descripción corta
  - app_version (str): Versión de la app que introdujo el cambio
  - sql (list[str]): Sentencias SQL idempotentes (IF NOT EXISTS)

REGLAS:
  - Nunca usar DROP TABLE/DROP DATABASE
  - Siempre usar IF NOT EXISTS para idempotencia
  - Nuevas migraciones se añaden AL FINAL con version incrementada
  - No modificar migraciones ya desplegadas
"""

MIGRATIONS = [

    # ================================================================
    # TABLA USERS - Base
    # ================================================================

    {
        'version': 1,
        'description': 'Crear tabla users base',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
            BEGIN
                CREATE TABLE users (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(50) NOT NULL,
                    password_hash NVARCHAR(255) NOT NULL,
                    email NVARCHAR(100),
                    full_name NVARCHAR(100),
                    active BIT DEFAULT 1,
                    created_at DATETIME DEFAULT GETDATE(),
                    updated_at DATETIME DEFAULT GETDATE()
                );
                CREATE INDEX idx_username ON users(username);
                CREATE INDEX idx_email ON users(email);
                CREATE INDEX idx_active ON users(active);
            END""",
            """IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_users_username' AND object_id = OBJECT_ID('users'))
            BEGIN
                IF NOT EXISTS (SELECT * FROM sys.indexes WHERE is_unique = 1 AND object_id = OBJECT_ID('users')
                               AND name LIKE '%username%')
                BEGIN
                    CREATE UNIQUE INDEX UQ_users_username ON users(username);
                END
            END""",
        ]
    },

    # ================================================================
    # TABLA USERS - Columnas adicionales
    # ================================================================

    {
        'version': 2,
        'description': 'Campos pais y verificacion email en users',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'pais')
            BEGIN
                ALTER TABLE users ADD pais VARCHAR(100) NULL;
            END""",
            """IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'email_verificado')
            BEGIN
                ALTER TABLE users ADD email_verificado BIT DEFAULT 0;
            END""",
            """IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'token_verificacion')
            BEGIN
                ALTER TABLE users ADD token_verificacion VARCHAR(100) NULL;
            END""",
            """IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'token_expiracion')
            BEGIN
                ALTER TABLE users ADD token_expiracion DATETIME NULL;
            END""",
        ]
    },

    {
        'version': 3,
        'description': 'Campo rol en users',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'rol')
            BEGIN
                ALTER TABLE users ADD rol VARCHAR(20) NOT NULL DEFAULT 'usuario';
            END""",
            """IF NOT EXISTS (SELECT 1 FROM sys.indexes
                WHERE name = 'idx_users_rol' AND object_id = OBJECT_ID('users'))
            BEGIN
                CREATE INDEX idx_users_rol ON users(rol);
            END""",
        ]
    },

    {
        'version': 4,
        'description': 'Campos empresa_id y cliente_id en users',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM sys.columns
                WHERE object_id = OBJECT_ID('users') AND name = 'empresa_id')
            BEGIN
                ALTER TABLE users ADD empresa_id VARCHAR(5) NULL;
                UPDATE users SET empresa_id = '1' WHERE empresa_id IS NULL;
            END""",
            """IF NOT EXISTS (SELECT 1 FROM sys.columns
                WHERE object_id = OBJECT_ID('users') AND name = 'cliente_id')
            BEGIN
                ALTER TABLE users ADD cliente_id VARCHAR(20) NULL;
            END""",
            """IF NOT EXISTS (SELECT 1 FROM sys.indexes
                WHERE name = 'IX_users_empresa_id' AND object_id = OBJECT_ID('users'))
            BEGIN
                CREATE INDEX IX_users_empresa_id ON users(empresa_id);
            END""",
            """IF NOT EXISTS (SELECT 1 FROM sys.indexes
                WHERE name = 'IX_users_cliente_id' AND object_id = OBJECT_ID('users'))
            BEGIN
                CREATE INDEX IX_users_cliente_id ON users(cliente_id);
            END""",
        ]
    },

    {
        'version': 5,
        'description': 'Campo debe_cambiar_password en users',
        'app_version': 'v1.2.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM sys.columns
                WHERE object_id = OBJECT_ID('users') AND name = 'debe_cambiar_password')
            BEGIN
                ALTER TABLE users ADD debe_cambiar_password BIT NOT NULL DEFAULT 0;
            END""",
        ]
    },

    {
        'version': 6,
        'description': 'Campo company_name en users',
        'app_version': 'v1.20.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'company_name')
            BEGIN
                ALTER TABLE users ADD company_name NVARCHAR(200) NULL;
            END""",
        ]
    },

    {
        'version': 7,
        'description': 'Campo cif_nif en users',
        'app_version': 'v1.22.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM sys.columns
                WHERE object_id = OBJECT_ID('users') AND name = 'cif_nif')
            BEGIN
                ALTER TABLE users ADD cif_nif VARCHAR(50) NULL;
            END""",
        ]
    },

    {
        'version': 8,
        'description': 'Campo fecha_ultimo_cambio_password en users',
        'app_version': 'v1.26.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'fecha_ultimo_cambio_password')
            BEGIN
                ALTER TABLE users ADD fecha_ultimo_cambio_password DATETIME NULL;
                UPDATE users SET fecha_ultimo_cambio_password = GETDATE();
            END""",
        ]
    },

    # ================================================================
    # TABLA EMAIL_CONFIG
    # ================================================================

    {
        'version': 9,
        'description': 'Crear tabla email_config',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'email_config')
            BEGIN
                CREATE TABLE email_config (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    nombre_configuracion VARCHAR(100) NOT NULL,
                    smtp_server VARCHAR(200) NOT NULL,
                    smtp_port INT NOT NULL,
                    email_from VARCHAR(200) NOT NULL,
                    email_password VARCHAR(500) NOT NULL,
                    email_to VARCHAR(200) NOT NULL,
                    activo BIT NOT NULL DEFAULT 1,
                    fecha_creacion DATETIME NOT NULL DEFAULT GETDATE(),
                    fecha_modificacion DATETIME NULL
                );
            END""",
        ]
    },

    {
        'version': 10,
        'description': 'Campo empresa_id en email_config',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.columns
                WHERE object_id = OBJECT_ID('email_config') AND name = 'empresa_id')
            BEGIN
                ALTER TABLE email_config ADD empresa_id VARCHAR(5) NOT NULL DEFAULT '1';
            END""",
            """IF NOT EXISTS (SELECT * FROM sys.indexes
                WHERE name = 'IX_email_config_empresa_id' AND object_id = OBJECT_ID('email_config'))
            BEGIN
                CREATE INDEX IX_email_config_empresa_id ON email_config(empresa_id);
            END""",
        ]
    },

    # ================================================================
    # TABLA API_KEYS
    # ================================================================

    {
        'version': 11,
        'description': 'Crear tabla api_keys',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'api_keys')
            BEGIN
                CREATE TABLE api_keys (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    user_id INT NOT NULL,
                    api_key VARCHAR(64) NOT NULL UNIQUE,
                    nombre VARCHAR(100) NOT NULL,
                    activo BIT DEFAULT 1,
                    fecha_creacion DATETIME DEFAULT GETDATE(),
                    fecha_ultimo_uso DATETIME NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                CREATE INDEX idx_api_key ON api_keys(api_key);
            END""",
        ]
    },

    # ================================================================
    # TABLA PARAMETROS
    # ================================================================

    {
        'version': 12,
        'description': 'Crear tabla parametros',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parametros')
            BEGIN
                CREATE TABLE parametros (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    clave VARCHAR(50) NOT NULL,
                    valor VARCHAR(500) NOT NULL,
                    descripcion VARCHAR(200) NULL,
                    fecha_modificacion DATETIME DEFAULT GETDATE()
                );
            END""",
        ]
    },

    {
        'version': 13,
        'description': 'Campo empresa_id en parametros + indice unico',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.columns
                WHERE object_id = OBJECT_ID('parametros') AND name = 'empresa_id')
            BEGIN
                ALTER TABLE parametros ADD empresa_id VARCHAR(5) NOT NULL DEFAULT '1';
            END""",
            """IF NOT EXISTS (SELECT * FROM sys.indexes
                WHERE name = 'IX_parametros_empresa_id' AND object_id = OBJECT_ID('parametros'))
            BEGIN
                CREATE INDEX IX_parametros_empresa_id ON parametros(empresa_id);
            END""",
            """IF NOT EXISTS (SELECT * FROM sys.indexes
                WHERE name = 'UQ_parametros_clave_empresa' AND object_id = OBJECT_ID('parametros'))
            BEGIN
                CREATE UNIQUE INDEX UQ_parametros_clave_empresa ON parametros(clave, empresa_id);
            END""",
        ]
    },

    {
        'version': 14,
        'description': 'Parametro PERMITIR_REGISTRO',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'PERMITIR_REGISTRO' AND empresa_id = '1')
            BEGIN
                INSERT INTO parametros (clave, valor, descripcion, empresa_id)
                VALUES ('PERMITIR_REGISTRO', '0', 'Permitir registro publico de usuarios (0=No, 1=Si)', '1');
            END""",
        ]
    },

    {
        'version': 15,
        'description': 'Parametro PERMITIR_PROPUESTAS',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'PERMITIR_PROPUESTAS' AND empresa_id = '1')
            BEGIN
                INSERT INTO parametros (clave, valor, descripcion, empresa_id)
                VALUES ('PERMITIR_PROPUESTAS', '1', 'Permitir crear propuestas/solicitudes de productos (0=No, 1=Si)', '1');
            END""",
        ]
    },

    # ================================================================
    # TABLAS PROPUESTAS
    # ================================================================

    {
        'version': 16,
        'description': 'Crear tabla propuestas (cabecera)',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'propuestas')
            BEGIN
                CREATE TABLE propuestas (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    user_id INT NOT NULL,
                    fecha DATETIME DEFAULT GETDATE(),
                    comentarios NVARCHAR(MAX),
                    estado VARCHAR(20) DEFAULT 'Enviada',
                    total_items INT,
                    fecha_modificacion DATETIME,
                    CONSTRAINT FK_propuestas_user FOREIGN KEY (user_id) REFERENCES users(id),
                    CONSTRAINT CHK_propuestas_estado CHECK (estado IN ('Enviada', 'Procesada', 'Cancelada'))
                );
                CREATE INDEX idx_propuestas_user_id ON propuestas(user_id);
                CREATE INDEX idx_propuestas_fecha ON propuestas(fecha);
                CREATE INDEX idx_propuestas_estado ON propuestas(estado);
            END""",
        ]
    },

    {
        'version': 17,
        'description': 'Crear tabla propuestas_lineas (detalle)',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'propuestas_lineas')
            BEGIN
                CREATE TABLE propuestas_lineas (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    propuesta_id INT NOT NULL,
                    codigo VARCHAR(50),
                    descripcion NVARCHAR(200),
                    formato VARCHAR(50),
                    calidad VARCHAR(20),
                    color VARCHAR(50),
                    tono VARCHAR(20),
                    calibre VARCHAR(20),
                    pallet VARCHAR(50),
                    caja VARCHAR(50),
                    unidad VARCHAR(20),
                    existencias DECIMAL(18,2),
                    cantidad_solicitada DECIMAL(18,2),
                    CONSTRAINT FK_propuestas_lineas_propuesta FOREIGN KEY (propuesta_id)
                        REFERENCES propuestas(id) ON DELETE CASCADE
                );
                CREATE INDEX idx_propuestas_lineas_propuesta_id ON propuestas_lineas(propuesta_id);
                CREATE INDEX idx_propuestas_lineas_codigo ON propuestas_lineas(codigo);
            END""",
        ]
    },

    {
        'version': 18,
        'description': 'Campo empresa_id en propuestas',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM sys.columns
                WHERE object_id = OBJECT_ID('propuestas') AND name = 'empresa_id')
            BEGIN
                ALTER TABLE propuestas ADD empresa_id VARCHAR(5) NULL;
                UPDATE propuestas SET empresa_id = '1' WHERE empresa_id IS NULL;
            END""",
            """IF NOT EXISTS (SELECT 1 FROM sys.indexes
                WHERE name = 'IX_propuestas_empresa_id' AND object_id = OBJECT_ID('propuestas'))
            BEGIN
                CREATE INDEX IX_propuestas_empresa_id ON propuestas(empresa_id);
            END""",
        ]
    },

    {
        'version': 19,
        'description': 'Campo referencia en propuestas',
        'app_version': 'v1.10.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM sys.columns
                WHERE object_id = OBJECT_ID('propuestas') AND name = 'referencia')
            BEGIN
                ALTER TABLE propuestas ADD referencia VARCHAR(100) NULL;
            END""",
        ]
    },

    {
        'version': 20,
        'description': 'Campo cliente_id en propuestas',
        'app_version': 'v1.15.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'propuestas' AND COLUMN_NAME = 'cliente_id')
            BEGIN
                ALTER TABLE propuestas ADD cliente_id VARCHAR(20) NULL;
            END""",
            """IF NOT EXISTS (SELECT 1 FROM sys.indexes
                WHERE name = 'IX_propuestas_cliente_id' AND object_id = OBJECT_ID('propuestas'))
            BEGIN
                CREATE INDEX IX_propuestas_cliente_id ON propuestas(cliente_id);
            END""",
        ]
    },

    # ================================================================
    # TABLA CONSULTAS
    # ================================================================

    {
        'version': 21,
        'description': 'Crear tabla consultas',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'consultas')
            BEGIN
                CREATE TABLE consultas (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    empresa_id VARCHAR(5) NOT NULL,
                    codigo_producto VARCHAR(50) NOT NULL,
                    descripcion_producto VARCHAR(255),
                    formato VARCHAR(50),
                    calidad VARCHAR(50),
                    color VARCHAR(50),
                    tono VARCHAR(50),
                    calibre VARCHAR(50),
                    nombre_cliente VARCHAR(100) NOT NULL,
                    email_cliente VARCHAR(100) NOT NULL,
                    telefono_cliente VARCHAR(20),
                    mensaje TEXT NOT NULL,
                    user_id INT NULL,
                    estado VARCHAR(20) DEFAULT 'pendiente',
                    respuesta TEXT NULL,
                    fecha_respuesta DATETIME NULL,
                    respondido_por INT NULL,
                    fecha_creacion DATETIME DEFAULT GETDATE(),
                    CONSTRAINT FK_consultas_user FOREIGN KEY (user_id) REFERENCES users(id),
                    CONSTRAINT FK_consultas_respondido FOREIGN KEY (respondido_por) REFERENCES users(id),
                    CONSTRAINT CK_consultas_estado CHECK (estado IN ('pendiente', 'respondida', 'cerrada'))
                );
            END""",
            """IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_consultas_empresa')
            BEGIN
                CREATE INDEX IX_consultas_empresa ON consultas(empresa_id);
            END""",
            """IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_consultas_estado')
            BEGIN
                CREATE INDEX IX_consultas_estado ON consultas(estado);
            END""",
            """IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_consultas_fecha')
            BEGIN
                CREATE INDEX IX_consultas_fecha ON consultas(fecha_creacion DESC);
            END""",
        ]
    },

    {
        'version': 22,
        'description': 'Parametro WHATSAPP_NUMERO',
        'app_version': 'v1.0.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'WHATSAPP_NUMERO' AND empresa_id = '1')
            BEGIN
                INSERT INTO parametros (clave, valor, descripcion, empresa_id)
                VALUES ('WHATSAPP_NUMERO', '', 'Numero de WhatsApp para consultas (formato: 34XXXXXXXXX)', '1');
            END""",
        ]
    },

    # ================================================================
    # TABLA EMPRESA_LOGO
    # ================================================================

    {
        'version': 23,
        'description': 'Crear tabla empresa_logo',
        'app_version': 'v1.5.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'empresa_logo')
            BEGIN
                CREATE TABLE empresa_logo (
                    codigo VARCHAR(5) NOT NULL PRIMARY KEY,
                    logo VARBINARY(MAX) NULL,
                    favicon VARBINARY(MAX) NULL,
                    fecha_creacion DATETIME DEFAULT GETDATE(),
                    fecha_modificacion DATETIME DEFAULT GETDATE()
                );
            END""",
        ]
    },

    {
        'version': 24,
        'description': 'Campo tema en empresa_logo',
        'app_version': 'v1.5.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.columns
                WHERE object_id = OBJECT_ID('empresa_logo') AND name = 'tema')
            BEGIN
                ALTER TABLE empresa_logo ADD tema VARCHAR(20) DEFAULT 'rubi';
            END""",
        ]
    },

    {
        'version': 25,
        'description': 'Campo invertir_logo en empresa_logo',
        'app_version': 'v1.5.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.columns
                WHERE object_id = OBJECT_ID('empresa_logo') AND name = 'invertir_logo')
            BEGIN
                ALTER TABLE empresa_logo ADD invertir_logo BIT DEFAULT 0;
            END""",
        ]
    },

    # ================================================================
    # TABLA USER_SESSIONS
    # ================================================================

    {
        'version': 26,
        'description': 'Crear tabla user_sessions',
        'app_version': 'v1.1.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_sessions')
            BEGIN
                CREATE TABLE user_sessions (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    session_token VARCHAR(64) NOT NULL UNIQUE,
                    user_id INT NOT NULL,
                    empresa_id VARCHAR(5) NOT NULL,
                    ip_address VARCHAR(45),
                    created_at DATETIME DEFAULT GETDATE(),
                    last_activity DATETIME DEFAULT GETDATE(),
                    CONSTRAINT FK_user_sessions_user FOREIGN KEY (user_id)
                        REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE INDEX IX_user_sessions_user_id ON user_sessions(user_id);
                CREATE INDEX IX_user_sessions_empresa_id ON user_sessions(empresa_id);
                CREATE INDEX IX_user_sessions_last_activity ON user_sessions(last_activity);
            END""",
        ]
    },

    # ================================================================
    # TABLA AUDIT_LOG
    # ================================================================

    {
        'version': 27,
        'description': 'Crear tabla audit_log',
        'app_version': 'v1.2.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'audit_log')
            BEGIN
                CREATE TABLE audit_log (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    fecha DATETIME DEFAULT GETDATE() NOT NULL,
                    user_id INT NULL,
                    username VARCHAR(100) NULL,
                    empresa_id VARCHAR(5) NULL,
                    accion VARCHAR(50) NOT NULL,
                    recurso VARCHAR(100) NULL,
                    recurso_id VARCHAR(100) NULL,
                    ip_address VARCHAR(45) NULL,
                    user_agent VARCHAR(1000) NULL,
                    detalles NVARCHAR(MAX) NULL,
                    resultado VARCHAR(20) DEFAULT 'SUCCESS'
                );
                CREATE INDEX IX_audit_log_fecha ON audit_log(fecha DESC);
                CREATE INDEX IX_audit_log_user ON audit_log(user_id);
                CREATE INDEX IX_audit_log_accion ON audit_log(accion);
                CREATE INDEX IX_audit_log_empresa ON audit_log(empresa_id);
                CREATE INDEX IX_audit_log_resultado ON audit_log(resultado);
            END""",
        ]
    },

    # ================================================================
    # PARAMETROS ADICIONALES
    # ================================================================

    {
        'version': 28,
        'description': 'Parametro GRID_CON_IMAGENES',
        'app_version': 'v1.8.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'GRID_CON_IMAGENES' AND empresa_id = '1')
            BEGIN
                INSERT INTO parametros (clave, valor, descripcion, empresa_id)
                VALUES ('GRID_CON_IMAGENES', '0', 'Mostrar imagenes en tabla y tarjetas de stock', '1');
            END""",
        ]
    },

    {
        'version': 29,
        'description': 'Parametros PAGINACION_GRID y PAGINACION_LIMITE',
        'app_version': 'v1.5.3',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'PAGINACION_GRID' AND empresa_id = '1')
            BEGIN
                INSERT INTO parametros (clave, valor, descripcion, empresa_id)
                VALUES ('PAGINACION_GRID', '1', 'Habilitar paginacion en vista de tabla/grid sin imagenes. 1=Habilitado, 0=Deshabilitado', '1');
            END""",
            """IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'PAGINACION_LIMITE' AND empresa_id = '1')
            BEGIN
                INSERT INTO parametros (clave, valor, descripcion, empresa_id)
                VALUES ('PAGINACION_LIMITE', '50', 'Numero de registros por pagina en vista de tabla/grid. Valores recomendados: 25, 50, 100', '1');
            END""",
        ]
    },

    {
        'version': 30,
        'description': 'Parametro PERMITIR_FIRMA',
        'app_version': 'v1.15.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'PERMITIR_FIRMA' AND empresa_id = '1')
            BEGIN
                INSERT INTO parametros (clave, valor, descripcion, empresa_id)
                VALUES ('PERMITIR_FIRMA', '1', 'Habilita/deshabilita la opcion de firma digital en propuestas (1=habilitado, 0=deshabilitado)', '1');
            END""",
        ]
    },

    {
        'version': 31,
        'description': 'Parametros MODO_ESPEJO y FECHA_ULTIMA_SINCRONIZACION',
        'app_version': 'v1.20.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'MODO_ESPEJO' AND empresa_id = '1')
            BEGIN
                INSERT INTO parametros (clave, valor, descripcion, empresa_id)
                VALUES ('MODO_ESPEJO', '0', 'Indica si la base de datos es un espejo (copia sincronizada de otra BD). 0=Original, 1=Espejo', '1');
            END""",
            """IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'FECHA_ULTIMA_SINCRONIZACION' AND empresa_id = '1')
            BEGIN
                INSERT INTO parametros (clave, valor, descripcion, empresa_id)
                VALUES ('FECHA_ULTIMA_SINCRONIZACION', '', 'Fecha y hora de la ultima sincronizacion de datos desde la BD origen', '1');
            END""",
        ]
    },

    # ================================================================
    # TABLA DOMINIOS
    # ================================================================

    {
        'version': 32,
        'description': 'Crear tabla dominios',
        'app_version': 'v1.22.0',
        'sql': [
            """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dominios')
            BEGIN
                CREATE TABLE dominios (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    dominio VARCHAR(255) NOT NULL,
                    connection_id VARCHAR(10) NOT NULL,
                    descripcion VARCHAR(255) NULL,
                    activo BIT DEFAULT 1,
                    fecha_creacion DATETIME DEFAULT GETDATE(),
                    fecha_modificacion DATETIME DEFAULT GETDATE()
                );
                CREATE UNIQUE INDEX IX_dominios_dominio ON dominios(dominio);
            END""",
        ]
    },

    {
        'version': 33,
        'description': 'Parametro PERMITIR_BUSQUEDA_VOZ',
        'app_version': 'v1.28.0',
        'sql': [
            """IF NOT EXISTS (SELECT 1 FROM parametros WHERE clave = 'PERMITIR_BUSQUEDA_VOZ' AND empresa_id = '1')
            BEGIN
                INSERT INTO parametros (clave, valor, descripcion, empresa_id)
                VALUES ('PERMITIR_BUSQUEDA_VOZ', '1', 'Habilitar busqueda por voz en pagina de stocks (1=habilitado, 0=deshabilitado)', '1');
            END""",
        ]
    },

]
