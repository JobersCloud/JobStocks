-- ============================================================================
-- BASE DE DATOS: Undefasa (ERP - Solo Lectura)
-- Proposito: Base de datos del ERP de gestion ceramica de UNDEFASA.
--            La aplicacion web accede a estas tablas SOLO A TRAVES DE VISTAS
--            en ApiRestStocks. Nunca se conecta directamente.
-- ============================================================================
-- La BD ERP se llama "Undefasa" pero se accede como "cristal" via alias de BD.
-- Las vistas en ApiRestStocks referencian "cristal.dbo.<tabla>".
-- ============================================================================
-- NOTA: Estas tablas son propiedad del ERP. La aplicacion web NO las modifica.
--       Solo se incluyen aqui como referencia de la estructura que consumen
--       las vistas de ApiRestStocks.
-- ============================================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'cristal')
BEGIN
    CREATE DATABASE cristal;
END
GO

USE cristal;
GO

-- ############################################################################
-- TABLAS MAESTRAS
-- ############################################################################

-- ============================================================================
-- TABLA: empresas
-- Catalogo de empresas del grupo.
-- ============================================================================
CREATE TABLE dbo.empresas (
    empresa                     char(5)         NOT NULL,
    nombre                      char(50)        NULL,
    domicilio                   char(50)        NULL,
    ciudad                      char(50)        NULL,
    pais                        char(5)         NULL,
    provincia                   char(5)         NULL,
    codpostal                   char(10)        NULL,
    cif                         char(15)        NULL,
    telefono                    char(30)        NULL,
    fax                         char(30)        NULL,
    abreviado                   char(10)        NULL,
    idioma                      char(5)         NULL,
    cl_domicilio                char(10)        NULL,
    nu_domicilio                char(10)        NULL,
    prefijo_provincia           char(5)         NULL,
    inscripcion                 char(200)       NULL,
    internet                    char(50)        NULL,
    mail                        char(50)        NULL,
    apto_correos                char(50)        NULL,
    cif_norma_58                char(9)         NULL,
    imagen_cabecera             char(255)       NULL,
    imagen_cabecera_legal       char(255)       NULL,
    gestion_contable            char(1)         NULL,
    imprimir_efecto_cobrado     char(1)         NULL,
    gestion_transportes         char(1)         NULL,
    imagen_recibos              char(255)       NULL,
    ins_dev_mensual             char(1)         NULL,
    genter_codigo_cli_autfra    char(15)        NULL,
    genter_codigo_pro_autfra    char(15)        NULL,
    imagen_promocion            char(255)       NULL,
    texto_orden_carga           char(255)       NULL,
    texto_pedido                char(255)       NULL,
    texto_albaran               char(255)       NULL,
    texto_factura               char(255)       NULL,
    libro                       varchar(20)     NULL,
    registro_mercantil          varchar(20)     NULL,
    hoja                        varchar(20)     NULL,
    folio                       varchar(20)     NULL,
    seccion                     varchar(20)     NULL,
    tomo                        varchar(20)     NULL,
    PhysicalGLN                 varchar(15)     NULL,
    LogicalOperationalPoint     varchar(15)     NULL,
    eori                        varchar(20)     NULL,
    CONSTRAINT PK_EMPRESAS PRIMARY KEY NONCLUSTERED (empresa)
);
GO

-- ============================================================================
-- TABLA: unidades
-- Unidades de medida (M2, ML, UD, KG, etc.)
-- ============================================================================
CREATE TABLE dbo.unidades (
    codigo          char(5)     NOT NULL,
    descripcion     char(15)    NULL,
    abreviado       char(5)     NULL,
    decimales       int         NULL,
    unidad_compras  char(5)     NULL,
    CONSTRAINT PK_UNIDADES PRIMARY KEY NONCLUSTERED (codigo)
);
GO

-- ============================================================================
-- TABLA: formatos
-- Formatos de piezas ceramicas (60x60, 30x90, etc.)
-- ============================================================================
CREATE TABLE dbo.formatos (
    empresa             char(5)         NOT NULL,
    codigo              char(5)         NOT NULL,
    descripcion         char(30)        NULL,
    abreviado           char(10)        NULL,
    piezascaja          int             NULL,
    metroscaja          decimal(16,6)   NULL,
    metroslcaja         decimal(16,6)   NULL,
    pesocaja            decimal(16,6)   NULL,
    preciocoste         decimal(16,6)   NULL,
    pesopieza           decimal(16,6)   NULL,
    largo               decimal(16,6)   NULL,
    ancho               decimal(16,6)   NULL,
    espesor             decimal(16,6)   NULL,
    pesoenvase          decimal(16,6)   NULL,
    equiv_m2_horno      decimal(4,2)    NOT NULL,
    activo              char(1)         NOT NULL,
    kilocaja            decimal(10,3)   NULL,
    tipopanel           char(10)        NULL,
    arrastrapacking     varchar(1)      NULL,
    r_tierra            varchar(20)     NULL,
    gramaje             decimal(19,4)   NULL,
    coste               decimal(19,6)   NULL,
    coste_rect          decimal(19,6)   NULL,
    fabricacion_propia  varchar(1)      NULL,
    abreviado_maestro   varchar(10)     NULL,
    prensas_pzgolpe     numeric(5,0)    NULL,
    especial            varchar(1)      NULL,
    CONSTRAINT formatos_x PRIMARY KEY NONCLUSTERED (empresa, codigo)
);
GO

-- ============================================================================
-- TABLA: almmodelos (Series/Modelos de articulos)
-- ============================================================================
CREATE TABLE dbo.almmodelos (
    empresa             char(5)     NOT NULL,
    modelo              char(5)     NOT NULL,
    descripcion         char(30)    NULL,
    resumido            char(5)     NULL,
    codigo_promocion    int         NULL,
    pasta               varchar(5)  NULL,
    activo              varchar(1)  NULL,
    comercial           varchar(5)  NULL,
    CONSTRAINT PK_ALMMODELOS PRIMARY KEY NONCLUSTERED (empresa, modelo)
);
GO

-- ============================================================================
-- TABLA: calidades
-- Calidades de producto (1a, 2a, 3a, etc.)
-- ============================================================================
CREATE TABLE dbo.calidades (
    empresa         char(5)     NOT NULL,
    codigo          char(5)     NOT NULL,
    descripcion     char(20)    NULL,
    abreviado       char(3)     NULL,
    incremento      char(1)     NULL,
    tono            char(1)     NULL,
    calibre         char(1)     NULL,
    es_calidad_final char(1)    NULL,
    estadistica     char(5)     NULL,
    CONSTRAINT calidades_x PRIMARY KEY NONCLUSTERED (empresa, codigo)
);
GO

-- ============================================================================
-- TABLA: almcolores
-- Colores de articulos
-- ============================================================================
CREATE TABLE dbo.almcolores (
    empresa     char(5)     NOT NULL,
    color       char(5)     NOT NULL,
    descripcion char(30)    NULL,
    resumido    char(5)     NULL,
    CONSTRAINT PK_ALMCOLORES PRIMARY KEY NONCLUSTERED (empresa, color)
);
GO

-- ============================================================================
-- TABLA: pallets
-- Tipos de pallet/embalaje
-- ============================================================================
CREATE TABLE dbo.pallets (
    empresa         char(5)         NOT NULL,
    codigo          char(5)         NOT NULL,
    descripcion     char(30)        NULL,
    resumido        char(10)        NULL,
    largo           decimal(16,6)   NULL,
    ancho           decimal(16,6)   NULL,
    alto            decimal(16,6)   NULL,
    peso            decimal(16,6)   NULL,
    precio_coste    decimal(16,6)   NULL,
    proveedor       char(15)        NULL,
    clase           char(5)         NULL,
    codigo_compras  char(15)        NULL,
    activo          char(1)         NULL,
    CONSTRAINT PK_PALLETS PRIMARY KEY NONCLUSTERED (empresa, codigo)
);
GO

-- ============================================================================
-- TABLA: almcajas
-- Tipos de caja
-- ============================================================================
CREATE TABLE dbo.almcajas (
    empresa         char(5)         NOT NULL,
    codigo          char(4)         NOT NULL,
    descripcion     char(50)        NULL,
    pesoenvase      decimal(16,6)   NULL,
    descripcion_abr char(12)        NULL,
    codigo_compras  char(15)        NULL,
    activo          char(1)         NULL,
    CONSTRAINT PK_ALMCAJAS PRIMARY KEY NONCLUSTERED (empresa, codigo)
);
GO

-- ############################################################################
-- TABLAS DE ARTICULOS
-- ############################################################################

-- ============================================================================
-- TABLA: articulos
-- Maestro de articulos/productos ceramicos.
-- Tabla principal con ~80+ campos.
-- ============================================================================
CREATE TABLE dbo.articulos (
    empresa             char(5)         NOT NULL,
    codigo              char(20)        NOT NULL,
    descripcion         char(40)        NULL,
    familia             char(5)         NULL,
    formato             char(5)         NULL,
    modelo              char(5)         NULL,
    unidad              char(5)         NULL,
    precio_coste        float           NULL,
    fecha_alta          datetime        NULL,
    fecha_anulado       datetime        NULL,
    fecha_fin           datetime        NULL,
    cuenta              char(60)        NULL,
    proveedor           char(30)        NULL,
    decorado            char(1)         NULL,
    sector              char(1)         NULL,
    conjunto            int             NULL,
    pesopieza           decimal(16,6)   NULL,
    piezascaja          smallmoney      NULL,
    pesocaja            smallmoney      NULL,
    pesoenvase          smallmoney      NULL,
    metroscaja          smallmoney      NULL,
    metroslcaja         smallmoney      NULL,
    cuenta_contable     char(20)        NULL,
    tono                char(1)         NULL,
    calibre             char(1)         NULL,
    compras             char(1)         NULL,
    activo              char(1)         NULL,
    unidad_est          char(1)         NULL,
    prev_anular         char(1)         NULL,
    empleado            char(5)         NULL,
    molde               char(25)        NULL,
    plato               char(25)        NULL,
    calibre_min         char(25)        NULL,
    calibre_max         char(25)        NULL,
    cliente             char(15)        NULL,
    stock_minimo        decimal(10,2)   NULL,
    base                char(20)        NULL,
    ean13               varchar(14)     NULL,
    nombre_imagen       char(20)        NULL,
    nombre_ambiente     char(20)        NULL,
    color               char(5)         NULL,
    subfamilia          char(5)         NULL,
    activo_pedido       char(1)         NULL,
    imagen              char(255)       NULL,
    nivel_servicio      char(1)         NULL,
    lote_minimo         decimal(16,2)   NULL,
    porc_primera        decimal(4,2)    NULL,
    web                 char(1)         NULL,
    catalogo            char(1)         NULL,
    -- Campos adicionales omitidos por brevedad (~30+ campos de planificacion, web, etc.)
    CONSTRAINT PK_ARTICULOS PRIMARY KEY NONCLUSTERED (empresa, codigo)
);
GO

-- ============================================================================
-- TABLA: almartcajas
-- Configuracion de cajas por articulo (piezas/caja, metros/caja, peso)
-- ============================================================================
CREATE TABLE dbo.almartcajas (
    empresa             char(5)         NOT NULL,
    articulo            char(20)        NOT NULL,
    caja                char(4)         NOT NULL,
    piezascaja          int             NULL,
    metroscaja          decimal(16,6)   NULL,
    metroslcaja         decimal(16,6)   NULL,
    pesocaja            decimal(16,6)   NULL,
    codigo_anterior     char(10)        NULL,
    destacar_en_consultas char(1)       NULL,
    descripcion         char(10)        NULL,
    color               decimal(10,0)   NULL,
    activo              char(1)         NULL,
    ean13               varchar(14)     NULL,
    arrastrapacking     varchar(1)      NULL,
    CONSTRAINT PK_ALMARTCAJAS PRIMARY KEY NONCLUSTERED (empresa, articulo, caja)
);
GO

-- ============================================================================
-- TABLA: palarticulo
-- Configuracion de pallets por articulo (cajas/pallet, planos, alturas)
-- ============================================================================
CREATE TABLE dbo.palarticulo (
    empresa         char(5)         NOT NULL,
    articulo        char(20)        NOT NULL,
    codigo          char(5)         NOT NULL,
    caja            char(4)         NOT NULL,
    cajaspallet     int             NULL,
    planospallet    int             NULL,
    alturas         decimal(16,6)   NULL,
    activo          char(1)         NULL,
    CONSTRAINT PK_PALARTICULO PRIMARY KEY NONCLUSTERED (empresa, articulo, codigo, caja)
);
GO

-- ============================================================================
-- TABLA: almartcal
-- Precios y stock por articulo+calidad
-- ============================================================================
CREATE TABLE dbo.almartcal (
    empresa             char(5)         NOT NULL,
    articulo            char(20)        NOT NULL,
    calidad             char(5)         NOT NULL,
    precio              decimal(16,6)   NULL,
    fecha_alta          datetime        NULL,
    stockmin            decimal(16,6)   NULL,
    stockmax            decimal(16,6)   NULL,
    puntopedido         decimal(16,6)   NULL,
    ean13               varchar(14)     NULL,
    precio_coste_total  decimal(16,6)   NULL,
    CONSTRAINT PK_ALMARTCAL PRIMARY KEY NONCLUSTERED (empresa, articulo, calidad)
);
GO

-- ============================================================================
-- TABLA: almarttonopeso
-- Peso por articulo+tono
-- ============================================================================
CREATE TABLE dbo.almarttonopeso (
    empresa     varchar(5)      NOT NULL,
    articulo    varchar(20)     NOT NULL,
    tono        varchar(4)      NOT NULL,
    peso        numeric(18,4)   NOT NULL,
    CONSTRAINT pk_almarttonopeso PRIMARY KEY CLUSTERED (empresa, articulo, tono)
);
GO

-- ============================================================================
-- TABLA: articulo_ficha_tecnica
-- PDFs de fichas tecnicas de articulos (binario)
-- ============================================================================
CREATE TABLE dbo.articulo_ficha_tecnica (
    empresa     varchar(5)      NOT NULL,
    articulo    varchar(20)     NOT NULL,
    ficha       image           NULL,
    CONSTRAINT pk_articulo_ficha_tecnica PRIMARY KEY CLUSTERED (empresa, articulo)
);
GO

-- ============================================================================
-- TABLA: ps_articulo_imagen
-- Fotos de articulos (binario) con thumbnails
-- ============================================================================
CREATE TABLE dbo.ps_articulo_imagen (
    id                  numeric(18,0)   NOT NULL,
    empresa             varchar(5)      NOT NULL,
    articulo            varchar(20)     NOT NULL,
    foto                image           NULL,
    predeterminada      int             NOT NULL,
    width_thumbnail     int             NULL,
    height_thumbnail    int             NULL,
    thumbnail           image           NULL,
    nombre              varchar(100)    NULL,
    web_id              numeric(18,0)   NULL,
    CONSTRAINT PK_ps_articulo_imagen PRIMARY KEY CLUSTERED (id)
);
GO

-- ############################################################################
-- TABLAS DE ALMACEN / STOCK
-- ############################################################################

-- ============================================================================
-- TABLA: almlinubica
-- Stock fisico por ubicacion. Tabla principal de existencias.
-- Cada fila = 1 linea de stock en una ubicacion concreta.
-- ============================================================================
CREATE TABLE dbo.almlinubica (
    empresa             char(5)         NOT NULL,
    almacen             char(5)         NULL,
    zona                char(1)         NULL,
    fila                int             NULL,
    altura              int             NULL,
    linea               decimal(16,0)   NOT NULL,
    articulo            char(20)        NULL,
    familia             char(5)         NULL,
    formato             char(5)         NULL,
    modelo              char(5)         NULL,
    calidad             char(5)         NULL,
    tono                int             NULL,
    calibre             int             NULL,
    existencias         decimal(16,6)   NULL,
    anyo                int             NULL,
    pedido              decimal(16,0)   NULL,
    linped              int             NULL,
    cliente             char(15)        NULL,
    ubicacion           char(20)        NOT NULL,
    tipo_unidad         char(5)         NULL,
    referencia          varchar(20)     NULL,
    f_alta              datetime        NULL,
    observaciones       text            NULL,
    tipo_pallet         char(5)         NULL,
    sector              char(1)         NULL,
    externo             char(1)         NULL,
    caja                char(5)         NULL,
    tonochar            char(4)         NULL,
    preferencia_carga   decimal(5,0)    NULL,
    CONSTRAINT PK_ALMLINUBICA PRIMARY KEY NONCLUSTERED (empresa, ubicacion, linea)
);
GO

-- Indices de almlinubica (criticos para rendimiento de consultas de stock)
CREATE NONCLUSTERED INDEX [idx2]  ON dbo.almlinubica (empresa, articulo, tipo_pallet, pedido);
CREATE NONCLUSTERED INDEX [idx3]  ON dbo.almlinubica (empresa, referencia, pedido);
CREATE NONCLUSTERED INDEX [idx4]  ON dbo.almlinubica (empresa, referencia, tipo_pallet, pedido);
CREATE NONCLUSTERED INDEX [idx5]  ON dbo.almlinubica (empresa, referencia, tipo_pallet, pedido, externo);
CREATE NONCLUSTERED INDEX [idx6]  ON dbo.almlinubica (empresa, anyo, pedido, linped);
CREATE NONCLUSTERED INDEX [idx7]  ON dbo.almlinubica (empresa, articulo);
CREATE NONCLUSTERED INDEX [idx8]  ON dbo.almlinubica (empresa, ubicacion, referencia, tipo_pallet, pedido);
CREATE NONCLUSTERED INDEX [idx9]  ON dbo.almlinubica (empresa, ubicacion);
CREATE NONCLUSTERED INDEX [idx10] ON dbo.almlinubica (empresa, referencia, tipo_pallet);
CREATE NONCLUSTERED INDEX [idx11] ON dbo.almlinubica (empresa, articulo, calidad, pedido);
GO

-- ============================================================================
-- TABLA: almubimapa
-- Mapa fisico de ubicaciones del almacen (filas, alturas, largo)
-- ============================================================================
CREATE TABLE dbo.almubimapa (
    empresa         char(5)     NOT NULL,
    almacen         char(5)     NOT NULL,
    zona            char(1)     NOT NULL,
    fila_desde      int         NULL,
    fila_hasta      int         NULL,
    altura_desde    int         NULL,
    altura_hasta    int         NULL,
    largo           int         NULL
);
GO

-- ============================================================================
-- TABLA: almalmacen (Catalogo de almacenes)
-- ============================================================================
-- CREATE TABLE dbo.almalmacen (
--     empresa     char(5)     NOT NULL,
--     codigo      char(5)     NOT NULL PRIMARY KEY,
--     descripcion char(30)    NULL
-- );
-- NOTA: No hay DDL exportado. Estructura inferida del modelo.

-- ############################################################################
-- TABLAS COMERCIALES (Ventas)
-- ############################################################################

-- ============================================================================
-- TABLA: genter
-- Terceros: clientes (tipoter='C'), proveedores, agentes, etc.
-- ============================================================================
CREATE TABLE dbo.genter (
    empresa             char(5)     NOT NULL,
    tipoter             char(1)     NOT NULL,       -- C=Cliente, P=Proveedor, A=Agente...
    codigo              char(15)    NOT NULL,
    nombre              char(50)    NULL,
    razon               char(50)    NULL,
    cif                 char(30)    NULL,
    pais                char(5)     NULL,
    provincia           char(5)     NULL,
    cod_postal          char(10)    NULL,
    localidad           char(50)    NULL,
    domicilio           char(255)   NULL,
    telefono            char(30)    NULL,
    fax                 char(30)    NULL,
    moneda              char(5)     NULL,
    riesgo              int         NULL,
    falta               datetime    NULL,
    apellidos           char(40)    NULL,
    sexo                char(1)     NULL,
    fecha_nacimiento    datetime    NULL,
    idioma              char(5)     NULL,
    activo              char(1)     NULL,
    tipopais            char(1)     NULL,
    cl_domicilio        char(10)    NULL,
    nu_domicilio        char(10)    NULL,
    prefijo_provincia   char(5)     NULL,
    distribuidor        char(1)     NULL,
    codigo_cliente      char(15)    NULL,
    genter              char(20)    NULL,
    cuenta              char(20)    NULL,
    textoactivo         char(255)   NULL,
    activo_mailing      char(1)     NULL,
    tel_movil           char(20)    NULL,
    e_mail              char(255)   NULL,
    acreedor            char(1)     NULL,
    cta_portes          char(20)    NULL,
    usuario             char(20)    NULL,
    email_firma         char(200)   NULL,
    email2_firma        char(200)   NULL,
    email_ar            varchar(200) NULL,
    eori                varchar(50)  NULL,
    nombre_comercial    varchar(50)  NULL,
    web                 varchar(100) NULL,
    poblacion           char(50)    NULL,
    CONSTRAINT genter_x PRIMARY KEY NONCLUSTERED (empresa, tipoter, codigo)
);
GO

-- ============================================================================
-- TABLA: venped (Pedidos de venta - cabecera)
-- ============================================================================
CREATE TABLE dbo.venped (
    empresa         char(5)         NOT NULL,
    anyo            int             NOT NULL,
    pedido          decimal(16,0)   NOT NULL,
    fpedido         datetime        NULL,
    fentrega        datetime        NULL,
    falta           datetime        NULL,
    cliente         char(15)        NOT NULL,
    flistado        datetime        NULL,
    observaciones   text            NULL,
    codpago         char(5)         NULL,
    numpedcli       char(20)        NULL,       -- Numero pedido del cliente
    serie           char(5)         NULL,
    bruto           decimal(16,6)   NULL,
    importe_dto     decimal(16,6)   NULL,
    total_neto      decimal(16,6)   NULL,
    peso            decimal(16,6)   NULL,
    divisa          char(5)         NULL,
    usuario         char(20)        NULL
    -- ~30+ campos adicionales omitidos (agentes, descuentos, direcciones, etc.)
);
GO

-- ============================================================================
-- TABLA: venliped (Pedidos de venta - lineas)
-- ============================================================================
CREATE TABLE dbo.venliped (
    empresa         char(5)         NOT NULL,
    anyo            int             NOT NULL,
    pedido          decimal(16,0)   NOT NULL,
    linea           int             NOT NULL,
    serie           char(5)         NULL,
    fpedido         datetime        NULL,
    fentrega        datetime        NULL,
    cliente         char(15)        NULL,
    tipo_unidad     char(5)         NULL,
    articulo        char(20)        NULL,
    familia         char(5)         NULL,
    formato         char(5)         NULL,
    modelo          char(5)         NULL,
    calidad         char(5)         NULL,
    tono            int             NULL,
    calibre         int             NULL,
    precio          decimal(17,6)   NULL,
    precio_estand   decimal(17,6)   NULL,
    cantidad        decimal(16,6)   NULL,
    pallets         int             NULL,
    total_cajas     decimal(16,6)   NULL,
    cajas           int             NULL,
    descripcion     char(40)        NULL,
    importe         decimal(16,6)   NULL,
    referencia      varchar(20)     NULL,
    situacion       char(1)         NULL,       -- C=Confirmado, P=Pendiente, F=Facturado...
    tipo_pallet     char(5)         NULL,
    caja            char(5)         NULL,
    tonochar        char(4)         NULL,
    -- ~60+ campos adicionales omitidos
    CONSTRAINT PK_VENLIPED PRIMARY KEY NONCLUSTERED (empresa, anyo, pedido, linea)
);
GO

-- ============================================================================
-- TABLA: venalb (Albaranes de venta - cabecera)
-- ============================================================================
CREATE TABLE dbo.venalb (
    empresa         char(5)         NOT NULL,
    anyo            int             NOT NULL,
    albaran         decimal(16,0)   NOT NULL,
    falbaran        datetime        NULL,
    fentrega        datetime        NULL,
    falta           datetime        NULL,
    cliente         char(15)        NULL,
    serie           char(5)         NULL,
    bruto           decimal(16,6)   NULL,
    importe_dto     decimal(16,6)   NULL,
    total_neto      decimal(16,6)   NULL,
    peso            decimal(16,6)   NULL,
    divisa          char(5)         NULL,
    usuario         char(20)        NULL,
    deposito        char(5)         NULL
    -- Campos adicionales omitidos
);
GO

-- ============================================================================
-- TABLA: venlialb (Albaranes de venta - lineas)
-- ============================================================================
CREATE TABLE dbo.venlialb (
    empresa         char(5)         NOT NULL,
    anyo            int             NOT NULL,
    albaran         decimal(16,0)   NOT NULL,
    linea           int             NOT NULL,
    articulo        char(20)        NULL,
    descripcion     char(40)        NULL,
    formato         char(5)         NULL,
    calidad         char(5)         NULL,
    tono            int             NULL,
    calibre         int             NULL,
    cantidad        decimal(16,6)   NULL,
    precio          decimal(17,6)   NULL,
    importe         decimal(16,6)   NULL,
    pallets         int             NULL,
    total_cajas     decimal(16,6)   NULL,
    falbaran        datetime        NULL,
    situacion       char(1)         NULL
    -- Campos adicionales omitidos
);
GO

-- ============================================================================
-- TABLA: venfac (Facturas de venta - cabecera)
-- ============================================================================
CREATE TABLE dbo.venfac (
    empresa         char(5)         NOT NULL,
    anyo            int             NOT NULL,
    factura         decimal(16,0)   NOT NULL,
    ffactura        datetime        NULL,
    falta           datetime        NULL,
    cliente         char(15)        NULL,
    serie           char(5)         NULL,
    total_neto      decimal(16,6)   NULL,
    importe_dto     decimal(16,6)   NULL,
    iva             decimal(16,6)   NULL,
    total_fac       decimal(16,6)   NULL,
    divisa          char(5)         NULL,
    usuario         char(20)        NULL
    -- Campos adicionales omitidos
);
GO

-- ============================================================================
-- TABLA: venlifac (Facturas de venta - lineas)
-- ============================================================================
CREATE TABLE dbo.venlifac (
    empresa         char(5)         NOT NULL,
    anyo            int             NOT NULL,
    factura         decimal(16,0)   NOT NULL,
    linea           int             NOT NULL,
    articulo        char(20)        NULL,
    descripcion     char(40)        NULL,
    formato         char(5)         NULL,
    calidad         char(5)         NULL,
    tono            int             NULL,
    calibre         int             NULL,
    cantidad        decimal(16,6)   NULL,
    precio          decimal(17,6)   NULL,
    neto            decimal(16,6)   NULL,       -- Importe neto
    pallets         int             NULL,
    total_cajas     decimal(16,6)   NULL,
    ffactura        datetime        NULL,
    situacion       char(1)         NULL
    -- Campos adicionales omitidos
);
GO

-- ############################################################################
-- DIAGRAMA DE RELACIONES (Simplificado)
-- ############################################################################
--
-- articulos ──┬── formato ──> formatos
--             ├── modelo  ──> almmodelos
--             ├── color   ──> almcolores
--             └── unidad  ──> unidades
--
-- almlinubica ──┬── articulo    ──> articulos
--               ├── calidad     ──> calidades
--               ├── tipo_pallet ──> pallets
--               └── caja        ──> almcajas (via almartcajas)
--
-- almartcajas ──┬── articulo ──> articulos
--               └── caja     ──> almcajas
--
-- palarticulo ──┬── articulo ──> articulos
--               └── codigo   ──> pallets
--
-- venped ──── cliente ──> genter (tipoter='C')
-- venliped ── (empresa, anyo, pedido) ──> venped
--
-- venalb ──── cliente ──> genter (tipoter='C')
-- venlialb ── (empresa, anyo, albaran) ──> venalb
--
-- venfac ──── cliente ──> genter (tipoter='C')
-- venlifac ── (empresa, anyo, factura) ──> venfac
--
-- ps_articulo_imagen ── articulo ──> articulos
-- articulo_ficha_tecnica ── articulo ──> articulos
--
-- ############################################################################
