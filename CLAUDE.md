# Notas del Proyecto - Claude

## Instrucciones para Claude
- **IMPORTANTE**: En cada modificación de código, incrementar automáticamente la versión en `backend/app.py` (constante `APP_VERSION`)
- Formato semántico: `vMAJOR.MINOR.PATCH`
  - PATCH: correcciones de bugs, cambios menores de configuración
  - MINOR: nuevas funcionalidades
  - MAJOR: cambios incompatibles con versiones anteriores

## Información General
- **Nombre**: ApiRestExternos
- **Tipo**: Web SPA con backend REST API
- **Repositorio**: https://github.com/JobersCloud/ApiRestExternos (privado)
- **GitHub User**: JobersCloud
- **Fecha de inicio**: 2025-12-22
- **Propósito**: Sistema de gestión de inventario de azulejos/cerámica

## Estructura del Proyecto

```
ApiRestExternos/
├── backend/
│   ├── app.py                # Aplicación principal Flask
│   ├── create_admin.py       # Script crear usuarios admin
│   ├── requirements.txt      # Dependencias Python (incluye gunicorn)
│   ├── Dockerfile            # Imagen Docker producción (gunicorn)
│   ├── Dockerfile.dev        # Imagen Docker desarrollo (hot-reload)
│   ├── .dockerignore         # Exclusiones para Docker
│   │
│   ├── config/
│   │   ├── database.py       # Conexión SQL Server
│   │   └── email_config_model.py
│   │
│   ├── controllers/
│   │   └── stock_controller.py
│   │
│   ├── models/
│   │   ├── user.py           # Modelo usuario (Flask-Login)
│   │   ├── stock_model.py    # Modelo gestión stocks
│   │   ├── email_config_model.py
│   │   ├── api_key_model.py  # Modelo gestión API keys
│   │   ├── parametros_model.py  # Modelo parámetros sistema
│   │   ├── imagen_model.py   # Modelo imágenes artículos
│   │   ├── propuesta_model.py # Modelo propuestas/solicitudes
│   │   ├── consulta_model.py # Modelo consultas sobre productos
│   │   ├── estadisticas_model.py # Modelo estadísticas dashboard
│   │   ├── ficha_tecnica_model.py # Modelo fichas técnicas PDF
│   │   ├── empresa_logo_model.py # Modelo logos/favicons por empresa
│   │   ├── user_session_model.py # Modelo sesiones activas
│   │   └── audit_model.py    # Modelo auditoría de usuarios
│   │
│   ├── routes/
│   │   ├── stock_routes.py   # Rutas consulta stocks + ficha técnica
│   │   ├── carrito_routes.py # Rutas carrito y envío
│   │   ├── email_config_routes.py # Rutas config email + test SMTP
│   │   ├── api_key_routes.py # Rutas gestión API keys
│   │   ├── register_routes.py # Rutas registro usuarios
│   │   ├── propuesta_routes.py # Rutas propuestas (ERP)
│   │   ├── usuario_routes.py # Rutas gestión usuarios (admin)
│   │   ├── parametros_routes.py # Rutas parámetros sistema
│   │   ├── consulta_routes.py # Rutas consultas sobre productos
│   │   ├── estadisticas_routes.py # Rutas estadísticas dashboard (admin)
│   │   ├── empresa_logo_routes.py # Rutas logos/favicons por empresa
│   │   ├── user_session_routes.py # Rutas sesiones activas (admin)
│   │   └── audit_routes.py   # Rutas auditoría de usuarios (admin)
│   │
│   ├── utils/
│   │   └── auth.py           # Decoradores autenticación
│   │
│   ├── data/
│   │   └── paises.json       # Lista países ISO 3166-1
│   │
│   └── database/
│       └── users_db.py       # Funciones autenticación
│
├── frontend/
│   ├── index.html            # Dashboard principal
│   ├── login.html            # Página de autenticación
│   ├── register.html         # Página de registro usuarios
│   ├── verify-email.html     # Página verificación email
│   ├── mis-propuestas.html   # Historial propuestas usuario
│   ├── todas-propuestas.html # Gestión propuestas (admin)
│   ├── usuarios.html         # Gestión usuarios (admin)
│   ├── email-config.html     # Configuración email (admin)
│   ├── parametros.html       # Parámetros sistema (admin)
│   ├── todas-consultas.html  # Gestión consultas (admin)
│   ├── dashboard.html        # Dashboard estadísticas (admin)
│   ├── empresa-logo.html     # Gestión logos por empresa (admin)
│   │
│   ├── js/
│   │   ├── app.js            # JavaScript frontend principal
│   │   ├── login.js          # JavaScript página login
│   │   ├── register.js       # JavaScript página registro
│   │   │
│   │   └── i18n/             # Sistema de internacionalización
│   │       ├── i18n.js       # Core del sistema i18n
│   │       ├── es.json       # Traducciones español
│   │       ├── en.json       # Traducciones inglés
│   │       └── fr.json       # Traducciones francés
│   │
│   ├── css/
│   │   └── styles.css        # Estilos CSS globales
│   │
│   ├── assets/
│   │   ├── logo.svg          # Logo principal (usado en app)
│   │   ├── logo.png          # Logo PNG (guardado en BD)
│   │   ├── logojobers.png    # Logo específico para login
│   │   ├── favicon.ico       # Favicon principal (usado en app)
│   │   └── faviconjobers.ico # Favicon específico para login
│   │
│   └── powerbuilder/         # Cliente PowerBuilder 2022
│       ├── README.md         # Instrucciones de uso
│       ├── n_cst_api_rest.sru # Objeto consumo API
│       └── w_test_api.srw    # Ventana de pruebas
│
├── Scripts SQL/
│   ├── README.md
│   ├── 01_create_table_users.sql
│   ├── 02_create_view_externos_stock.sql
│   ├── 03_create_table_email_config.sql
│   ├── 04_create_table_api_keys.sql
│   ├── 05_create_table_parametros.sql
│   ├── 06_alter_table_users_pais.sql
│   ├── 07_create_view_articulo_imagen.sql
│   ├── 08_create_tables_propuestas.sql
│   ├── 09_alter_table_propuestas_empresa.sql
│   ├── 10_create_view_externos_clientes.sql
│   ├── 11_alter_table_users_rol.sql
│   ├── 12_insert_parametro_propuestas.sql
│   ├── 13_alter_table_email_config_empresa.sql
│   ├── 14_alter_table_parametros_empresa.sql
│   ├── 16_alter_table_users_debe_cambiar_password.sql
│   ├── 18_create_table_consultas.sql
│   ├── 20_create_table_empresa_logo.sql
│   ├── 20_alter_table_empresa_logo_tema.sql
│   ├── 21_create_table_user_sessions.sql
│   └── 24_create_table_audit_log.sql
│
├── deploy/                   # Scripts despliegue Linux
│   ├── INSTALL.sh            # Instalador automático (Debian/RedHat)
│   ├── install-linux.sh      # Instalador simple (Ubuntu/Debian)
│   ├── gunicorn.service      # Servicio systemd
│   └── apache-flask.conf     # Config Apache reverse proxy
│
├── docker-compose.yml        # Docker producción
├── docker-compose.dev.yml    # Docker desarrollo (con debug)
├── claude.md
└── .gitignore
```

## Tecnologías Utilizadas

### Backend (Python)
- **Flask** 3.1.2 - Framework web
- **Flask-Login** - Autenticación y sesiones
- **flask-cors** 6.0.1 - CORS support
- **pyodbc** 5.3.0 - Conexión SQL Server
- **reportlab** - Generación PDFs
- **Werkzeug** - Password hashing
- **Flasgger** 0.9.7.1 - Documentación Swagger

### Frontend
- **JavaScript** Vanilla (sin frameworks)
- **CSS3** con variables personalizadas
- **Fetch API** para comunicación

### Base de Datos
- **Motor**: SQL Server 2008+
- **Servidor**: 192.168.63.25:1433
- **Base de datos**: ApiRestStocks
- **Conexión cifrada**: `Encrypt=yes; TrustServerCertificate=yes;`
  - ⚠️ **IMPORTANTE**: En Linux (Docker) usar `yes`, NO `True` (Windows acepta ambos, Linux solo `yes`)

### Herramientas
- **GitHub CLI**: v2.83.2

## APIs y Endpoints

### Autenticación
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/login` | Iniciar sesión (retorna csrf_token) |
| POST | `/api/logout` | Cerrar sesión |
| GET | `/api/current-user` | Usuario actual |
| GET | `/api/csrf-token` | Obtener/refrescar CSRF token |

### Sistema (público)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/version` | Versión de la aplicación |

**Respuesta GET /version**: `{"version": "v1.0.0"}`

**Gestión de versión**: Editar `APP_VERSION` en `backend/app.py`

### Stocks (protegidos con sesión o API Key)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/stocks` | Todos los productos |
| GET | `/api/stocks/search` | Búsqueda con filtros |
| GET | `/api/stocks/resumen` | Estadísticas |
| GET | `/api/stocks/<codigo>` | Detalle producto |
| GET | `/api/stocks/<codigo>/imagenes` | Imágenes del artículo (base64) |
| GET | `/api/stocks/<codigo>/ficha-tecnica/exists` | Verificar si existe ficha técnica |
| GET | `/api/stocks/<codigo>/ficha-tecnica` | Obtener ficha técnica (PDF base64) |

**Filtros disponibles**: empresa, descripcion, formato, serie, calidad, color, tono, calibre, existencias_min

**Parámetros GET /ficha-tecnica**: `?download=true` para descarga directa del PDF

### API Keys (requiere sesión para gestionar)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/api-keys` | Listar API keys del usuario |
| POST | `/api/api-keys` | Crear nueva API key |
| DELETE | `/api/api-keys/<id>` | Eliminar API key |
| POST | `/api/api-keys/<id>/deactivate` | Desactivar API key |

### Registro de Usuarios (rutas públicas cuando está habilitado)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/registro-habilitado` | Verificar si registro está activo |
| GET | `/api/paises` | Lista de países (ISO 3166-1) |
| POST | `/api/register` | Registrar nuevo usuario |
| GET | `/api/verify-email?token=xxx` | API verificar email con token |
| GET | `/verificar-email?token=xxx` | Página amigable de verificación |

### Documentación Swagger
| Ruta | Descripción |
|------|-------------|
| `/apidocs/` | Swagger UI - Documentación interactiva |
| `/apispec.json` | Especificación OpenAPI en JSON |

### Carrito
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/carrito` | Ver carrito |
| POST | `/api/carrito/add` | Agregar producto |
| DELETE | `/api/carrito/remove/<index>` | Eliminar producto por índice |
| DELETE | `/api/carrito/clear` | Vaciar carrito |
| POST | `/api/carrito/enviar` | Generar PDF, enviar email y guardar en BD |

**Notas**:
- El carrito detecta duplicados por clave compuesta: codigo + calidad + tono + calibre + pallet + caja
- Al enviar, se guarda la propuesta en tablas `propuestas` y `propuestas_lineas`
- Retorna `propuesta_id` en la respuesta

### Propuestas (para integración ERP)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/propuestas/pendientes` | Propuestas pendientes de procesar |
| GET | `/api/propuestas/<id>` | Detalle de una propuesta con líneas |
| GET | `/api/propuestas/<id>/lineas` | Solo las líneas de una propuesta |
| GET | `/api/propuestas/lineas` | Líneas con filtro por propuesta_id |
| PUT | `/api/propuestas/<id>/estado` | Cambiar estado de propuesta |

**Parámetros GET /pendientes**: `?incluir_lineas=true` para incluir detalle de productos

**Parámetros GET /lineas**: `?propuesta_id=123` para filtrar por propuesta

**Body PUT /estado**: `{"estado": "Procesada"}` - Estados válidos: Enviada, Procesada, Cancelada

**Autenticación**: Sesión o API Key (header `X-API-Key` o query `?apikey=`)

### Configuración Email (requiere admin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/email-config` | Listar configs |
| GET | `/api/email-config/active` | Config activa |
| POST | `/api/email-config` | Crear nueva config |
| PUT | `/api/email-config/<id>` | Actualizar |
| POST | `/api/email-config/<id>/activate` | Activar config |
| POST | `/api/email-config/test` | Probar conexión SMTP |

### Gestión de Usuarios (requiere admin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/usuarios` | Listar todos los usuarios |
| PUT | `/api/usuarios/<id>/activar` | Activar usuario |
| PUT | `/api/usuarios/<id>/desactivar` | Desactivar usuario |
| PUT | `/api/usuarios/<id>/rol` | Cambiar rol del usuario |

**Body PUT /rol**: `{"rol": "administrador"}` - Roles válidos: usuario, administrador, superusuario

### Parámetros del Sistema (requiere admin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/parametros` | Listar todos los parámetros |
| PUT | `/api/parametros/<clave>` | Actualizar valor de parámetro |

**Body PUT**: `{"valor": "true"}`

### Consultas sobre Productos (requiere sesión)
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/consultas` | Enviar consulta sobre producto |
| GET | `/api/consultas/whatsapp-config` | Obtener número WhatsApp configurado |

**Body POST /consultas**:
```json
{
  "codigo": "ABC123",
  "descripcion": "Producto ejemplo",
  "formato": "60x60",
  "calidad": "A",
  "tono": "01",
  "calibre": "9",
  "nombre": "Juan Pérez",
  "email": "juan@email.com",
  "telefono": "123456789",
  "mensaje": "Consulta sobre disponibilidad"
}
```

**Respuesta GET /whatsapp-config**: `{"numero": "+34612345678"}` o `{"numero": null}`

### Estadísticas Dashboard (requiere admin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/estadisticas/resumen` | Resumen general (totales) |
| GET | `/api/estadisticas/productos-mas-solicitados` | Top productos solicitados |
| GET | `/api/estadisticas/propuestas-por-dia` | Propuestas últimos N días |
| GET | `/api/estadisticas/propuestas-por-estado` | Distribución por estado |
| GET | `/api/estadisticas/propuestas-por-mes` | Propuestas por mes (últimos 6) |
| GET | `/api/estadisticas/usuarios-mas-activos` | Top usuarios con propuestas |
| GET | `/api/estadisticas/consultas-por-estado` | Distribución consultas por estado |

**Parámetros GET /propuestas-por-dia**: `?dias=7` (por defecto 7, máximo 90)

**Parámetros GET /productos-mas-solicitados y /usuarios-mas-activos**: `?limite=10` (por defecto 10)

### Logo de Empresa (público GET, admin POST/DELETE)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/empresa/<id>/logo` | Obtener logo de empresa (imagen binaria) |
| GET | `/api/empresa/<id>/favicon` | Obtener favicon de empresa |
| GET | `/api/empresa/<id>/logo/exists` | Verificar si existe logo |
| GET | `/api/empresa/<id>/config` | Obtener configuración (tema, invertir_logo) |
| POST | `/api/empresa/<id>/logo` | Subir/actualizar logo (base64) |
| POST | `/api/empresa/<id>/favicon` | Subir/actualizar favicon (base64) |
| PUT | `/api/empresa/<id>/tema` | Cambiar tema de color |
| PUT | `/api/empresa/<id>/invertir-logo` | Cambiar flag invertir logo |
| DELETE | `/api/empresa/<id>/logo` | Eliminar logo |
| DELETE | `/api/empresa/<id>/favicon` | Eliminar favicon |

**Notas**:
- GET es público (sin autenticación) para cargar logos en login
- POST, PUT y DELETE requieren rol administrador
- Las imágenes se detectan automáticamente por magic bytes (PNG, JPEG, GIF, WebP, SVG, ICO)
- **Temas disponibles**: rubí, zafiro, esmeralda, amatista, ámbar, grafito

## Tablas de Base de Datos

### `view_externos_stock` (Vista)
Campos: empresa, codigo, descripcion, formato, serie, calidad, color, tono, calibre, unidad, pallet, caja, unidadescaja, cajaspallet, existencias, ean13, pesocaja, pesopallet, tipo_producto

### `view_articulo_imagen` (Vista)
Campos: id, codigo, imagen
- **Origen**: `cristal.dbo.ps_articulo_imagen`
- Múltiples imágenes por código de artículo
- Imágenes en formato binario (IMAGE), convertidas a base64 en la API

### `view_externos_articulo_ficha_tecnica` (Vista)
Campos: empresa, articulo, ficha
- **Origen**: `cristal.dbo.ps_articulo_ficha_tecnica`
- Ficha técnica en formato PDF binario (VARBINARY), convertida a base64 en la API
- Un PDF por artículo (puede no existir)

### `users`
Campos: id, username, password_hash, email, full_name, pais, active, email_verificado, token_verificacion, token_expiracion, rol
- **Roles**: 'usuario' (por defecto), 'administrador', 'superusuario'

### `parametros`
Campos: id, clave, valor, descripcion, fecha_modificacion, empresa_id
- **empresa_id**: VARCHAR(5) - Permite configuración independiente por empresa
- **Restricción única**: (clave, empresa_id) - Mismo parámetro puede existir en diferentes empresas
- **PERMITIR_REGISTRO**: Flag para habilitar/deshabilitar registro público de usuarios
- **PERMITIR_PROPUESTAS**: Flag para habilitar/deshabilitar funcionalidad de propuestas

### `email_config`
Campos: id, nombre_configuracion, smtp_server, smtp_port, email_from, email_password, email_to, activo, fecha_creacion, fecha_modificacion, empresa_id
- **empresa_id**: VARCHAR(5) - Permite configuración SMTP independiente por empresa

### `api_keys`
Campos: id, user_id, api_key, nombre, activo, fecha_creacion, fecha_ultimo_uso

### `propuestas` (Cabecera de solicitudes)
Campos: id, user_id, fecha, comentarios, estado, total_items, fecha_modificacion
- **Estados**: 'Enviada', 'Procesada', 'Cancelada'
- FK a `users`

### `propuestas_lineas` (Detalle de solicitudes)
Campos: id, propuesta_id, codigo, descripcion, formato, calidad, color, tono, calibre, pallet, caja, unidad, existencias, cantidad_solicitada
- FK a `propuestas` con ON DELETE CASCADE

### `consultas` (Consultas sobre productos)
Campos: id, user_id, empresa_id, codigo, descripcion, formato, calidad, tono, calibre, nombre, email, telefono, mensaje, fecha
- FK a `users`
- Almacena consultas enviadas desde modal de detalle de producto
- Se envía email al destinatario configurado en `email_config`

### `empresa_logo` (Logos, favicons y temas por empresa)
Campos: codigo, logo, favicon, tema, invertir_logo, fecha_creacion, fecha_modificacion
- **codigo**: VARCHAR(5) PRIMARY KEY - ID de la empresa
- **logo**: VARBINARY(MAX) - Logo en formato binario
- **favicon**: VARBINARY(MAX) - Favicon en formato binario
- **tema**: VARCHAR(20) DEFAULT 'rubi' - Tema de color (rubí, zafiro, esmeralda, amatista, ámbar, grafito)
- **invertir_logo**: BIT DEFAULT 0 - Flag para invertir colores del logo en header
- Permite personalizar apariencia visual por cada empresa
- Scripts SQL: `20_create_table_empresa_logo.sql`, `20_alter_table_empresa_logo_tema.sql`

## Funcionalidades Principales

1. **Autenticación**: Login/logout con Flask-Login y password hashing
2. **Registro de Usuarios**: Sistema de registro público con verificación por email
   - Flag configurable para habilitar/deshabilitar registro (`PERMITIR_REGISTRO`)
   - Verificación obligatoria de email antes de activar cuenta
   - Lista de 196 países con códigos ISO 3166-1 (alfa-2 y alfa-3)
   - Token de verificación con expiración de 24 horas
3. **API Keys**: Autenticación por API Key para integraciones externas
4. **Consulta de Stocks**: Tabla con filtros avanzados y vista detallada
5. **Galería de Imágenes**: Imágenes de artículos en vista detalle
   - Múltiples imágenes por artículo
   - Carga asíncrona con indicador de loading
   - Clic para ampliar imagen en modal
   - Responsive en móvil
6. **Carrito de Solicitudes**: Agregar productos, validar cantidades (clave compuesta)
7. **Envío por Email**: Genera PDF, envía email y guarda propuesta en BD
   - Las propuestas se guardan con estado 'Enviada' tras enviar email exitosamente
   - Historial de solicitudes en tablas `propuestas` y `propuestas_lineas`
8. **Gestión Config Email**: Múltiples configuraciones activables
   - Crear, editar, activar configuraciones SMTP
   - Botón de test para probar conexión SMTP antes de guardar
9. **Sistema de Roles**: Control de acceso basado en roles
   - **usuario**: Acceso a stocks, carrito, mis propuestas
   - **administrador**: + gestión usuarios, propuestas, email, parámetros
   - **superusuario**: Acceso total (reservado para desarrollo)
   - Menú hamburguesa con opciones según rol
10. **Panel de Administración**: Páginas exclusivas para admins
    - Gestión de usuarios (activar/desactivar, cambiar rol)
    - Todas las propuestas (ver, cambiar estado)
    - Configuración de email SMTP
    - Parámetros del sistema
11. **Internacionalización (i18n)**: Soporte multi-idioma
   - Idiomas soportados: Español (es), Inglés (en), Francés (fr)
   - Selector de idioma en menú de usuario (sección Apariencia)
   - Cambio de idioma sin recargar página
   - Preferencia guardada en localStorage
   - Detección automática del idioma del navegador
12. **Consultas sobre Productos**: Sistema de consultas desde detalle
   - Formulario modal para enviar consulta por email
   - Botón WhatsApp con mensaje prellenado con datos del producto
   - Número WhatsApp configurable en parámetros (`WHATSAPP_NUMERO`)
   - Historial de consultas en tabla `consultas`
13. **Modo Oscuro**: Tema oscuro configurable
   - Toggle en menú de usuario (sección Apariencia)
   - Variables CSS para colores dinámicos
   - Persistencia en localStorage
   - Afecta a toda la interfaz: tablas, modales, tarjetas, menús
14. **Dashboard de Estadísticas**: Panel para administradores
   - Tarjetas de resumen: total propuestas, pendientes, usuarios activos, consultas
   - Gráfico de línea: propuestas por día (últimos 7 días)
   - Gráfico doughnut: distribución por estado
   - Gráfico de barras: propuestas por mes (últimos 6 meses)
   - Tabla: productos más solicitados
   - Lista: usuarios más activos
   - Integración con Chart.js
   - Soporte modo oscuro
15. **Ficha Técnica PDF**: Descarga de fichas técnicas de productos
   - Vista `view_externos_articulo_ficha_tecnica` para acceso a PDFs
   - Botón solo visible si el producto tiene ficha técnica
   - Descarga directa del PDF desde el modal de detalle
   - Bloque visual en detalle con botón de descarga
16. **Logos Dinámicos por Empresa**: Personalización visual por empresa
   - Tabla `empresa_logo` para almacenar logo y favicon por empresa
   - Subida de imágenes en base64 desde panel de administración
   - Carga dinámica en header y favicon de la aplicación
   - Página login usa archivos estáticos (`logojobers.png`, `faviconjobers.ico`)
   - Resto de la app carga logo/favicon de base de datos según empresa_id
   - Endpoints públicos GET, protegidos POST/DELETE (admin)
17. **Temas de Color por Empresa**: Personalización de colores de la interfaz
   - 6 temas disponibles: rubí (rojo), zafiro (azul), esmeralda (verde), amatista (morado), ámbar (naranja), grafito (gris)
   - Variables CSS dinámicas: `--primary`, `--primary-dark`, `--primary-light`, `--accent`
   - Página de configuración con vista previa de cada tema
   - Persistencia en localStorage para carga instantánea (sin flash)
   - Script inline en `<head>` de todas las páginas para evitar parpadeo
   - Colores de Chart.js en dashboard se adaptan al tema activo

## Patrones de Diseño

- **MVC**: Models, Controllers, Routes separados
- **Blueprint Pattern**: Rutas modulares en Flask
- **Static Methods**: Operaciones de BD en modelos
- **Session Storage**: Carrito en sesión del servidor

## Sistema de Internacionalización (i18n)

### Uso en JavaScript
```javascript
// Inicializar (automático al cargar)
await I18n.init();

// Obtener traducción simple
t('auth.login')  // "Iniciar Sesión"

// Traducción con variables
t('auth.welcomeUser', { name: 'Juan' })  // "Bienvenido, Juan"

// Cambiar idioma (sin recargar)
I18n.setLanguage('en');
```

### Uso en HTML
```html
<!-- Texto del elemento -->
<h1 data-i18n="header.title">Gestión de Stocks</h1>

<!-- Placeholder de input -->
<input data-i18n-placeholder="authPlaceholders.username" placeholder="...">
```

### Estructura de traducciones
Los archivos JSON están en `frontend/js/i18n/` organizados por namespaces:
- `common`: Textos genéricos (cargar, error, buscar...)
- `auth`: Autenticación (login, logout, registro...)
- `header`: Cabecera de la app
- `filters`: Filtros de búsqueda
- `table`: Columnas de tabla
- `detail`: Vista detalle del producto
- `cart`: Carrito de solicitudes
- `shipping`: Formulario de envío
- `errors`: Mensajes de error
- `cards`: Vista de tarjetas móvil

### Añadir nuevo idioma
1. Crear archivo `frontend/js/i18n/XX.json` (ej: `de.json` para alemán)
2. Añadir opción en selectores de idioma en todos los HTML
3. Agregar código al array `SUPPORTED_LANGS` en `i18n.js`

## Configuración

### Entorno Virtual Python
- **Ruta**: `C:\Users\jobers\virtualenv`
- **Activar**: `C:\Users\jobers\virtualenv\Scripts\activate`
- **Gestión**: direnv (carga automática de entorno al entrar al directorio)

### Flask (app.py)
- Host: 0.0.0.0
- Puerto: 5000
- Debug: True (desarrollo)

### Base de Datos (config/database.py)
- Driver: ODBC Driver 18 for SQL Server
- TrustServerCertificate: yes

## Notas de Seguridad

### Implementado
- Hash de contraseñas con Werkzeug
- **Autenticación dual**:
  - Sesión (cookies) para frontend
  - API Key para integraciones externas
- **Cookies de sesión seguras**:
  - `SESSION_COOKIE_HTTPONLY=True` - Protección XSS
  - `SESSION_COOKIE_SECURE=True` en producción - Solo HTTPS
  - `SESSION_COOKIE_SAMESITE='Lax'` - Protección CSRF
- **Todas las rutas API protegidas**:
  - Rutas de stocks (`/api/stocks/*`) - sesión o API Key
  - Rutas de carrito (`/api/carrito/*`) - solo sesión
  - Rutas de config email (`/api/email-config/*`) - solo sesión
  - Rutas de API keys (`/api/api-keys/*`) - solo sesión
- API Key soportada en header (`X-API-Key`) o query param (`?apikey=`)
- **Configuración via variables de entorno**:
  - `SECRET_KEY` - Clave secreta de Flask
  - `CORS_ORIGINS` - Orígenes permitidos para CORS
  - `FLASK_ENV` - production/development
- CORS controlado (configurable por entorno)
- Contraseñas email ocultas en API
- Swagger UI accesible sin autenticación para documentación
- **Rate limiting**: 5 intentos/minuto en login (Flask-Limiter)
- **Protección CSRF**: Token en sesión para peticiones POST/PUT/DELETE
  - Token generado en login, guardado en `session['csrf_token']`
  - Frontend envía en header `X-CSRF-Token`
  - Decorador `@csrf_required` en rutas mutantes
  - No aplica a autenticación por API Key (integraciones externas)
  - Endpoint `GET /api/csrf-token` para obtener/refrescar token

### Por mejorar
- (Todas las mejoras de seguridad principales implementadas)

## Tareas Pendientes

### Prioridad Baja (Futuro)
- [x] **Dockerizar la aplicación**: Crear `Dockerfile` y `docker-compose.yml` para facilitar despliegue *(Completado 2025-12-23)*

## Scripts Útiles

### Ejecución con Python (desarrollo)
```bash
# El entorno se activa automáticamente con direnv al entrar al directorio

# Ir al backend
cd backend

# Crear usuario admin
python create_admin.py

# Ejecutar aplicación
python app.py
```

### Ejecución con Docker (Producción)
```bash
# Construir y ejecutar
docker-compose up --build

# Ejecutar en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

### Ejecución con Docker (Desarrollo)
```bash
# Con debug y hot-reload
docker-compose -f docker-compose.dev.yml up --build

# Detener
docker-compose -f docker-compose.dev.yml down
```

### Despliegue en Linux (Producción)

Scripts en la carpeta `deploy/` para instalar en servidores Linux:

**Instalación automática (recomendado):**
```bash
# Copiar proyecto al servidor y ejecutar:
cd /ruta/al/proyecto
sudo bash deploy/INSTALL.sh
```

El script `INSTALL.sh`:
- Detecta el sistema operativo (Debian/Ubuntu o RedHat/CentOS)
- Instala dependencias: Python 3, Apache, ODBC Driver 18
- Copia la aplicación a `/opt/ApiRestExternos`
- Crea entorno virtual e instala requirements
- Configura servicio systemd (Gunicorn con 4 workers)
- Configura Apache como reverse proxy
- Inicia todo y verifica funcionamiento

**Comandos útiles post-instalación:**
```bash
# Ver logs en tiempo real
journalctl -u apirest -f

# Reiniciar servicio
systemctl restart apirest

# Ver estado
systemctl status apirest
```

**Para HTTPS**, usar certbot:
```bash
sudo certbot --apache -d tu-dominio.com
```

### Túneles para Acceso Externo (Desarrollo)

Para exponer el servidor local a internet (útil para probar desde móviles, compartir demos, etc.):

**ngrok** (recomendado - mejor compatibilidad con Gmail para emails):
```bash
# Ejecutar túnel (servidor Flask debe estar corriendo en puerto 5000)
ngrok http 5000

# La URL será algo como: https://xxx-xxx-xxx.ngrok-free.app
```

**Cloudflare Tunnel** (alternativa gratuita, pero Gmail puede bloquear emails con URLs de trycloudflare.com):
```bash
cloudflared tunnel --url http://localhost:5000

# La URL será algo como: https://xxx-xxx-xxx.trycloudflare.com
```

**Notas importantes:**
- El frontend detecta automáticamente si está en localhost o detrás de un túnel
- Los emails de verificación usan la URL correcta del túnel gracias a `ProxyFix`
- Gmail puede bloquear emails con URLs de `trycloudflare.com` (usar ngrok si hay problemas)
- Para acceso con empresa: `https://tu-tunel.ngrok-free.app/login?empresa=1`

## Historial de Cambios

### 2026-03-08
- **Columnas Opcionales en Grid de Stocks**: Configuración por empresa
  - Parámetro `STOCK_COLUMNAS_OPCIONALES` (JSON array) en tabla `parametros`
  - Columnas opcionales: `color`, `tipo_producto` (configurables en Parámetros)
  - Columnas fijas (siempre visibles): codigo, descripcion, formato, serie, calidad, tono, calibre, existencias
  - Sección de checkboxes en página Parámetros para gestionar columnas visibles
  - Endpoints: `GET /api/parametros/columnas-opcionales`, `PUT /api/parametros/columnas-opcionales`
  - Filtros del sidebar y filtros de columna se ocultan/muestran según configuración
  - Panel de filtros oculto con `visibility:hidden` hasta carga completa (evita flash)
  - Migraciones v48 y v49 en `migrations.py`
- **Campo tipo_producto en Stocks**: Nueva columna para tipo de producto
  - Campo `tipo_producto` añadido a `view_externos_stock`
  - Incluido en todos los SELECT de `stock_model.py` y en `stock_controller.py`
  - Filtro en sidebar (entre Formato y Modelo), grid y tarjetas móvil
  - Orden en sidebar: Formato > Tipo Producto > Modelo > Color > Calidad > Existencias
  - Orden en grid/tarjetas: formato > tipo_producto > serie > color > calidad > tono > calibre
- **Mejora Favoritos**: OUTER APPLY + fallback a propuestas_lineas
  - Favoritos de productos sin stock muestran descripción del último pedido
  - Resuelto conflicto COLLATE DATABASE_DEFAULT en consultas
  - Versión: v1.40.0 → v1.40.7

### 2026-01-08
- **Logos Dinámicos por Empresa**: Sistema de logos y favicons personalizables
  - Nueva tabla `empresa_logo` con campos: codigo (empresa_id), logo, favicon (VARBINARY)
  - Script SQL: `20_create_table_empresa_logo.sql`
  - Nuevo modelo `empresa_logo_model.py` con métodos CRUD
  - Nuevas rutas `empresa_logo_routes.py`:
    - `GET /api/empresa-logo/logo` - Obtener logo (público)
    - `GET /api/empresa-logo/favicon` - Obtener favicon (público)
    - `GET /api/empresa-logo/exists` - Verificar si existe logo
    - `POST /api/empresa-logo/logo` - Subir logo (admin)
    - `POST /api/empresa-logo/favicon` - Subir favicon (admin)
    - `DELETE /api/empresa-logo/logo` - Eliminar logo (admin)
    - `DELETE /api/empresa-logo/favicon` - Eliminar favicon (admin)
  - Nueva página `empresa-logo.html` para gestión de logos
  - Opción "Logo de Empresa" en menú de administración
  - Traducciones i18n completas (namespace `empresaLogo`)
- **Separación Login vs App**: Archivos estáticos para login
  - Login usa `logojobers.png` y `faviconjobers.ico` (estáticos, no de BD)
  - Resto de la app carga logo/favicon desde base de datos
  - Generado `faviconjobers.ico` desde `logojobers.png` con fondo transparente
- **Fix: Menú con Scroll**: Menú desplegable scrollable
  - Añadido `max-height: calc(100vh - 100px)` y `overflow-y: auto`
  - Soluciona problema cuando hay muchas opciones de menú en pantallas pequeñas
- **Scripts de Despliegue Linux**: Nueva carpeta `deploy/`
  - `INSTALL.sh`: Instalador automático (detecta Debian/RedHat)
  - `install-linux.sh`: Instalador simple (Ubuntu/Debian)
  - `gunicorn.service`: Servicio systemd para Gunicorn
  - `apache-flask.conf`: Configuración Apache como reverse proxy
  - Instala ODBC Driver 18, Python, Apache automáticamente
- **Sistema de Temas de Color**: Personalización visual por empresa
  - 6 temas disponibles: rubí, zafiro, esmeralda, amatista, ámbar, grafito
  - Campo `tema` añadido a tabla `empresa_logo` (Script: `20_alter_table_empresa_logo_tema.sql`)
  - Variables CSS dinámicas: `--primary`, `--primary-dark`, `--primary-light`, `--accent`
  - Selector `[data-color-theme="xxx"]` con paletas de colores predefinidas
  - Página de configuración con vista previa en tiempo real de cada tema
  - Endpoints: `GET /api/empresa/<id>/config`, `PUT /api/empresa/<id>/tema`
- **Fix: Flash de Tema al Cargar Páginas**: Eliminado parpadeo de colores
  - Script inline en `<head>` de todas las páginas para cargar tema desde localStorage
  - El tema se aplica antes de renderizar el DOM, evitando el flash del tema rojo por defecto
  - Patrón similar al usado para modo oscuro (dark mode)
  - Todas las funciones `applyColorTheme()` ahora guardan en localStorage
- **Eliminación de Colores Hardcodeados**: Migración a variables CSS
  - Reemplazados valores #FF4338 y #D32F2F por `var(--primary)` y `var(--primary-dark)`
  - Afecta headers, botones, badges y elementos de acento en todas las páginas
  - Gráficos de Chart.js en dashboard obtienen colores dinámicamente de CSS

### 2026-01-23
- **Grid Avanzada en Páginas de Administración**: Sistema de filtros y ordenación en tablas admin
  - Filtros por columna en `todas-propuestas.html`, `mis-propuestas.html`, `todas-consultas.html`
  - Cabeceras sticky que permanecen visibles al hacer scroll
  - Iconos de ordenación ASC/DESC por columna clicables
  - Popup de filtro con operadores (contiene, no contiene, igual, empieza por, termina en)
  - Chips de filtros activos con opción de eliminar individualmente
  - Cierre de popup con: clic fuera, tecla Escape, scroll de tabla
  - Soporte completo para modo oscuro en todos los componentes
  - Versión: v1.7.23
- **Grid Avanzada en Usuarios**: Aplicada misma funcionalidad a `usuarios.html`
  - Filtros por columna con popup profesional
  - Ordenación ASC/DESC clicando en cabeceras
  - Chips de filtros activos debajo de la tabla
  - Estilos unificados con resto de páginas admin
  - Versión: v1.7.24
- **Unificación de Headers de Tablas**: Gradiente consistente en todas las tablas admin
  - `.users-table th`, `.proposals-table th`, `.inquiries-table th` con mismo gradiente
  - `background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)`
  - Texto blanco y sticky positioning
- **Selector de Idioma Movido al Menú**: Reestructuración del menú de usuario
  - Eliminado selector de idioma del header en páginas admin
  - Añadido dentro de sección "Apariencia" junto con modo oscuro
  - Nueva traducción `menu.language` en ES/EN/FR
  - Clase `.lang-selector-menu` para estilos específicos
- **Operadores Negativos en Backend**: Soporte para filtros de exclusión
  - Nuevos operadores: `not_contains`, `not_starts`, `not_ends`
  - Operadores de rango: `between`, `not_between`
  - `stock_model.py`: VALID_OPERATORS actualizado con NOT LIKE y BETWEEN
  - Estilos diferenciados para opciones negativas en popup de filtro
- **Operadores Negativos Añadidos en Frontend**: Completado en todas las páginas
  - Operadores `not_starts` y `not_ends` añadidos a usuarios, propuestas, consultas
  - Versión: v1.7.25
- **Fix: Chips de Filtros Más Visibles**: Mejora de visibilidad
  - Contenedor con fondo gradiente, borde y sombra interior
  - Chips con borde y sombra para destacar sobre fondo
  - `.column-filters-chips` con estilos profesionales
- **Fix: Scroll Doble Eliminado**: Evitar scroll del browser + scroll de tabla
  - `body:has(.users-container) { overflow: hidden; height: 100vh; }`
  - `body:has(.proposals-container) { overflow: hidden; height: 100vh; }`
  - `body:has(.inquiries-container) { overflow: hidden; height: 100vh; }`
- **Fix: Columnas No Solapan Filas**: Mejora de responsive
  - `min-width: 800px` a `900px` en tablas para evitar superposición
  - `white-space: nowrap` en celdas de tabla
- **Área de Tablas Ampliada**: Reducido espacio vacío
  - Padding reducido de 30px a 15px 20px en contenedores
  - `max-height: calc(100vh - 200px)` a `calc(100vh - 250px)` para más espacio
  - Versión: v1.7.26
- **Modo Oscuro Mejorado**: Correcciones de estilos dark mode
  - Modal detalle de propuestas con estilos dark mode completos
  - Botón agregar al carrito (icono SVG) visible en modo oscuro móvil
  - Opciones negativas de filtro con colores suaves (no rojo intenso)
- **Fix: Scroll Móvil en Páginas Admin**: Corregido scroll bloqueado en móvil
  - `overflow: hidden` solo aplica en desktop (min-width: 769px)
  - En móvil el body permite scroll normal para ver tarjetas
  - Versión: v1.7.27
- **Fix: Chips de Filtros Visibles Sin Resultados**: Siempre visibles para poder quitar filtros
  - Chips movidos ANTES del empty state en HTML
  - Nuevo mensaje "No se encontraron resultados" cuando filtros producen 0 resultados
  - Distinción entre "sin datos" y "sin resultados por filtro"
  - Estilos CSS `.users-no-results`, `.proposals-no-results`, `.inquiries-no-results`
  - Soporte modo oscuro para mensajes de sin resultados
  - Versión: v1.7.28
- **Fix: Operadores not_starts/not_ends en Switch de Filtros**: Corregido bug crítico
  - Los operadores estaban en `operadoresTexto` pero faltaban en el `switch` de filtrado
  - Ahora "No empieza por" y "No termina en" funcionan correctamente
  - Aplicado a: usuarios, mis-propuestas, todas-propuestas, todas-consultas
  - Versión: v1.7.29
- **Fix: Icono Filtro Junto al Título**: Alineación correcta en headers de tabla
  - Quitar `justify-content: space-between` en `.column-header-wrapper`
  - Título, icono ordenación y filtro quedan juntos (no separados)
  - Aplicado a: users-table, proposals-table, inquiries-table
  - Versión: v1.7.30
- **Fix: Paginación Abajo y Compacta**: Corregido posicionamiento en split-screen
  - Paginación insertada DENTRO del `table-container` (antes era `.after()`)
  - Evita que aparezca a la derecha en layout flex
  - Paginación más pequeña: botones 32px, padding 10px, fuente 0.8rem
  - Layout horizontal (row) en una línea
  - Versión: v1.7.31

### 2026-01-22
- **Filtros por Columna Estilo WorkWithPlus**: Sistema de filtros avanzados en tabla
  - Icono de filtro (embudo SVG) en cada cabecera de columna filtrable
  - Popup profesional al hacer clic con:
    - Header con gradiente y botón cerrar
    - Radio buttons personalizados para operadores
    - Input de valor con estilos modernos
    - Botones Aplicar y Limpiar con iconos
  - **Operadores de texto**: Contiene, Igual a, Empieza por, Termina en
  - **Operadores numéricos**: Igual a, Mayor que, Mayor o igual, Menor que, Menor o igual, Diferente de
  - Filtros acumulativos mostrados como chips debajo de la tabla
  - Compatible con paginación backend (formato `columna__operador=valor`)
  - Iconos SVG de ordenación profesionales (flechas arriba/abajo)
  - Popup se cierra al: clic fuera, Escape, scroll
  - Soporte completo modo oscuro
  - **Backend**: `stock_model.py` con métodos `_parse_filter_key()` y `_build_filter_condition()`
  - **Frontend**: Variables `filtrosColumna`, `operadoresTexto`, `operadoresNumero`
  - Versión: v1.5.3
- **Paginación Backend para Grid sin Imágenes**: Mejora de rendimiento
  - Parámetros `PAGINACION_GRID` y `PAGINACION_LIMITE` en tabla `parametros`
  - Script SQL: `26_insert_parametro_paginacion.sql`
  - Endpoint `/api/parametros/paginacion-config` para obtener configuración
  - Paginación con `ROW_NUMBER()` compatible SQL Server 2008
  - Ordenación por columnas en backend

### 2026-01-20
- **Conexión cifrada a SQL Server**: SSL/TLS habilitado en conexiones a BD
  - `Encrypt=yes;` activa cifrado de conexión
  - `TrustServerCertificate=yes;` acepta certificados autofirmados
  - Aplicado en `database.py` (conexión dinámica) y `database_central.py` (conexión central)
  - ⚠️ En Linux (Docker) usar `yes`, NO `True` (driver ODBC 18 en Linux no acepta `True`)
  - Script de despliegue: `deploy/deploy-docker.sh`
  - Versión: v1.1.3
- **Protección CSRF**: Token en sesión para peticiones POST/PUT/DELETE
  - Token generado en login con `secrets.token_hex(32)`
  - Guardado en `session['csrf_token']` (backend) y `localStorage` (frontend)
  - Frontend envía en header `X-CSRF-Token` via función `fetchWithCsrf()`
  - Decorador `@csrf_required` en `utils/auth.py`
  - **Rutas protegidas**:
    - `carrito_routes.py`: add, remove, clear, enviar
    - `usuario_routes.py`: crear, activar, desactivar, rol, cambiar-password
    - `email_config_routes.py`: crear, actualizar, activar, test
    - `api_key_routes.py`: crear, eliminar, desactivar
    - `parametros_routes.py`: actualizar
    - `consulta_routes.py`: crear, responder
    - `empresa_logo_routes.py`: logo, favicon, tema, invertir-logo
    - `propuesta_routes.py`: cambiar estado
  - No verifica CSRF cuando se usa API Key (integraciones externas como PowerBuilder)
  - Endpoint `GET /api/csrf-token` para obtener/refrescar token
  - Versión: v1.2.0
- **Botón "Cerrar Todas las Sesiones"**: En dashboard de administración
  - Nuevo endpoint `DELETE /api/sesiones/todas-excepto-actual`
  - Nuevo método `UserSessionModel.delete_all_except(current_token, empresa_id)`
  - Botón "Cerrar Todas" junto a "Actualizar" en sección de sesiones activas
  - Confirmación antes de ejecutar con mensaje de advertencia
  - Protegido con `@csrf_required` y `@administrador_required`
  - No elimina la sesión del usuario actual
- **Fix: Toggle Modo Oscuro en Login**: Alineación responsive mejorada
  - Aumentado padding base de 5px 10px a 6px 12px
  - Switch más pequeño en móvil (36px × 20px)
  - Nuevo breakpoint para tablets (769px-1024px)
  - Nuevo breakpoint para pantallas grandes (≥1440px)
  - Versión: v1.2.1
- **Sistema de Auditoría de Usuarios**: Registro de acciones de usuarios
  - Nueva tabla `audit_log` en BD Central (Script: `24_create_table_audit_log.sql`)
  - Nuevo modelo `audit_model.py` con clases `AuditAction`, `AuditResult`, `AuditModel`
  - Nuevas rutas `audit_routes.py`:
    - `GET /api/audit-logs` - Listar logs con filtros (fecha, usuario, acción, resultado)
    - `GET /api/audit-logs/summary` - Resumen por acción y resultado
    - `GET /api/audit-logs/actions` - Lista de tipos de acción disponibles
    - `DELETE /api/audit-logs/cleanup` - Limpiar logs antiguos (mínimo 30 días)
  - **Acciones auditadas**:
    - Autenticación: LOGIN, LOGIN_FAILED, LOGOUT, PASSWORD_CHANGE
    - Sesiones: SESSION_KILL, SESSION_KILL_ALL
    - Usuarios: USER_CREATE, USER_ACTIVATE, USER_DEACTIVATE, USER_ROLE_CHANGE
    - API Keys: API_KEY_CREATE, API_KEY_DELETE
    - Configuración: CONFIG_CHANGE, EMAIL_CONFIG_CHANGE
    - Propuestas: PROPUESTA_SEND, PROPUESTA_STATUS_CHANGE
    - Consultas: CONSULTA_SEND, CONSULTA_RESPOND
  - **Frontend**: Nueva sección en dashboard.html
    - Filtros avanzados: fecha desde/hasta, acción, resultado, usuario
    - Tabla para desktop, tarjetas para móvil
    - Paginación con límite de 20 registros por página
    - Badges de colores por tipo de acción y resultado
    - **Filtros inline en columnas**: Inputs de texto/select en cada columna del header
    - **Ordenación por columnas**: Clic en título ordena ASC/DESC con iconos visuales
    - Filtrado y ordenación en cliente para mejor rendimiento
  - **Archivos modificados**:
    - `app.py`: Logging de login/logout
    - `usuario_routes.py`: Logging de gestión usuarios
    - `user_session_routes.py`: Logging de sesiones
    - `styles.css`: Estilos para filtros inline y ordenación
  - Versión: v1.2.3
- **Fix: Conexión BD en Auditoría**: Corregido para usar BD del cliente
  - `audit_model.py` ahora usa `Database.get_connection()` (conexión cliente)
  - Obtiene `connection_id` automáticamente de `session['connection']` si no se pasa
  - Paginación con `ROW_NUMBER()` para compatibilidad con SQL Server 2008
  - Commit antes de obtener IDENTITY (soporta tablas sin IDENTITY)
  - La tabla `audit_log` debe estar en la misma BD que `user_sessions`
  - Versión: v1.2.7

### 2026-01-19
- **Toggle Modo Oscuro en Login**: Selector de tema en página de login
  - Toggle con switch en esquina superior derecha (junto al selector de idioma)
  - Tema oscuro por defecto (`localStorage.getItem('theme') || 'dark'`)
  - Estilos dark mode completos para login (wrapper, sidebar, box, inputs, links)
  - Funciones `loadTheme()`, `applyTheme()`, `toggleTheme()` en `login.js`
  - Persistencia en localStorage compartida con la aplicación principal
  - Nuevos estilos CSS: `.login-top-controls`, `.theme-toggle-login`
- **Spinner de Envío en Carrito**: Indicador visual mientras se envía email
  - Overlay oscuro con spinner giratorio durante el envío
  - Función `mostrarEnviando(mostrar)` en `app.js`
  - Traducción `shipping.sending` en ES/EN/FR
  - Estilos CSS con soporte para modo oscuro
- **Imágenes CID en Email y PDF**: Thumbnails de productos embebidos
  - Imágenes en cuerpo del email HTML usando Content-ID (CID)
  - Thumbnails en tabla del PDF generado
  - `MIMEMultipart('mixed')` + `MIMEMultipart('related')` para estructura correcta
  - Función `ImagenModel.get_thumbnails_batch()` para obtener imágenes

### 2026-01-12 - Release v1.1.0
- **Release v1.1.0**: Mejoras de seguridad y rendimiento
  - Tag Git: `v1.1.0`
  - **Seguridad de Cookies**: HttpOnly, Secure (HTTPS), SameSite='Lax'
  - **Variables de Entorno**: SECRET_KEY, CORS_ORIGINS, credenciales BD
  - **Rate Limiting**: 5 intentos/minuto en login con Redis
  - **Redis**: Contenedor para almacenamiento compartido entre workers
  - **Dashboard Móvil**: Tarjetas para rankings (productos/usuarios)
  - **Pesos en Stock**: Campos pesocaja y pesopallet en detalle
  - Todos los items de "Por mejorar" de seguridad completados

### 2026-01-10
- **Refactorización CSS**: Consolidación de estilos inline en `styles.css`
  - Extraídos estilos de 12 archivos HTML a un único archivo CSS centralizado
  - Eliminadas ~5.400 líneas de código CSS inline duplicado
  - `styles.css` creció de ~1.500 a ~6.580 líneas organizadas por secciones
  - Archivos procesados:
    - `login.html`, `register.html`, `verify-email.html` (autenticación)
    - `index.html`, `usuarios.html` (páginas principales)
    - `mis-propuestas.html`, `todas-propuestas.html` (propuestas)
    - `todas-consultas.html`, `dashboard.html` (administración)
    - `email-config.html`, `parametros.html`, `empresa-logo.html` (configuración)
  - Secciones CSS organizadas con comentarios:
    - `/* ==================== SECCIÓN ==================== */`
  - Beneficios:
    - Separación clara de capas (HTML=estructura, CSS=presentación, JS=lógica)
    - Más fácil de mantener y escalar
    - Menos código duplicado
    - Carga más eficiente (CSS cacheado)
  - Preservado soporte completo para modo oscuro y responsive design
- **Indicador de Versión**: Versión visible en página de login
  - Constante `APP_VERSION` centralizada en `backend/app.py`
  - Endpoint público `GET /api/version` devuelve `{"version": "v1.0.0"}`
  - Formato semántico: `vMAJOR.MINOR.PATCH`
  - Login obtiene versión dinámicamente desde API
  - Indicador discreto en esquina inferior derecha
  - Estilos con soporte para modo oscuro
  - Para actualizar: editar `APP_VERSION` en `backend/app.py`
- **Gestión de Sesiones Activas**: Panel para administradores en dashboard
  - Nueva tabla `user_sessions` para tracking de sesiones activas
  - Script SQL: `21_create_table_user_sessions.sql`
  - Nuevo modelo `user_session_model.py` con métodos CRUD
  - Nuevas rutas `user_session_routes.py`:
    - `GET /api/sesiones` - Listar sesiones activas
    - `DELETE /api/sesiones/<id>` - Matar sesión por ID
    - `DELETE /api/sesiones/usuario/<user_id>` - Matar todas las sesiones de un usuario
    - `DELETE /api/sesiones/todas-excepto-actual` - Matar todas las sesiones excepto la actual
    - `GET /api/sesiones/count` - Contar sesiones activas
  - Panel en `dashboard.html` con tabla de sesiones
  - Vista responsiva: tabla en desktop, tarjetas en móvil
  - Botón "Cerrar Sesión" para expulsar usuarios
  - Expiración automática por rol: usuario (2h), admin (8h), superusuario (7d)
  - Validación en `before_request`: si sesión no existe en BD, se cierra
- **Pesos de Caja y Pallet en Detalle de Stock**: Información de peso en empaquetado
  - Campos `pesocaja` y `pesopallet` añadidos a `view_externos_stock`
  - `stock_model.py`: Campos incluidos en todas las consultas SQL
  - `app.js`: Muestra peso por caja (⚖️) y peso por pallet (🏋️) en sección empaquetado
  - Valores directos de BD (sin cálculos en frontend)
  - Traducciones i18n: `detail.weightPerBox`, `detail.weightPerPallet` en ES/EN/FR
- **Dashboard Móvil - Tarjetas para Rankings**: Vista responsiva mejorada
  - "Productos Más Solicitados": Tarjetas con código, descripción, veces y cantidad
  - "Usuarios Más Activos": Tarjetas con nombre de usuario y número de propuestas
  - Tabla en desktop, tarjetas en móvil (breakpoint 768px)
  - Estilos en `styles.css` (no inline) con soporte modo oscuro
  - Funciones `renderTopProducts()` y `renderTopUsers()` renderizan ambas vistas
- **Seguridad de Cookies y Sesiones**: Mejoras de seguridad en autenticación
  - `SESSION_COOKIE_HTTPONLY=True` - JavaScript no puede leer cookies (protege XSS)
  - `SESSION_COOKIE_SECURE=True` en producción - Solo se envían por HTTPS
  - `SESSION_COOKIE_SAMESITE='Lax'` - Protección CSRF (cookie no se envía cross-site)
  - `SECRET_KEY` configurable via variable de entorno `SECRET_KEY`
  - `CORS_ORIGINS` configurable via variable de entorno (antes era `*` fijo)
  - `docker-compose.yml` actualizado con variables de seguridad
  - Tag de restauración: `git checkout pre-security-fix`
- **Credenciales BD via Variables de Entorno**: Seguridad en conexión a base de datos
  - `database.py` usa `os.environ.get()` con fallback para desarrollo
  - Variables: `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_DRIVER`
  - Archivo `.env.example` como plantilla (incluido en Git, sin credenciales)
  - Archivo `.env` con credenciales reales (excluido de Git via `.gitignore`)
  - `docker-compose.yml` lee variables desde `.env` automáticamente
  - Tag de restauración: `git checkout pre-db-env-vars`
- **Rate Limiting en Login**: Protección contra ataques de fuerza bruta
  - Flask-Limiter 3.9.0 + redis 5.2.1 añadidos a dependencias
  - Límite: 5 intentos por minuto por IP en `/api/login`
  - Error handler 429 con mensaje amigable en español
  - Contenedor Redis 7-alpine para almacenamiento compartido entre workers Gunicorn
  - Variable de entorno `REDIS_URL` para configurar conexión
  - Fallback a memoria para desarrollo local (sin Redis)
  - Tag de restauración: `git checkout pre-rate-limiting`

### 2026-01-09
- **Fix: Eliminar Flash del Favicon**: Carga instantánea sin parpadeo
  - Eliminado favicon estático del HTML en todas las páginas (excepto login.html)
  - `app.js` guarda URL del favicon en `localStorage.faviconUrl` al cargar config de empresa
  - Script inline en `<head>` de cada página crea el link del favicon dinámicamente desde localStorage
  - Primera visita: favicon aparece cuando app.js carga la configuración
  - Visitas posteriores: favicon se carga instantáneamente desde localStorage
  - `login.html` mantiene `faviconjobers.ico` estático (sin cambios)

### 2025-12-30
- **Sistema de Roles y Permisos**: Implementado control de acceso basado en roles
  - Tres roles: `usuario`, `administrador`, `superusuario`
  - Campo `rol` añadido a tabla `users` (Script: `11_alter_table_users_rol.sql`)
  - Decoradores `@administrador_required` y `@superusuario_required` en `auth.py`
  - Menú hamburguesa en header con opciones según rol del usuario
- **Páginas de Administración**: Nuevas páginas para gestión del sistema
  - `mis-propuestas.html` - Historial de propuestas del usuario
  - `todas-propuestas.html` - Gestión de todas las propuestas (admin)
  - `usuarios.html` - Gestión de usuarios (activar/desactivar, cambiar rol)
  - `email-config.html` - Configuración de cuentas email SMTP
  - `parametros.html` - Parámetros del sistema
- **API de Gestión de Usuarios**: Nuevos endpoints para administradores
  - `GET /api/usuarios` - Listar todos los usuarios
  - `PUT /api/usuarios/<id>/activar` - Activar usuario
  - `PUT /api/usuarios/<id>/desactivar` - Desactivar usuario
  - `PUT /api/usuarios/<id>/rol` - Cambiar rol
  - Nueva ruta: `usuario_routes.py`
- **API de Parámetros**: Endpoints para gestión de configuración
  - `GET /api/parametros` - Listar parámetros
  - `PUT /api/parametros/<clave>` - Actualizar parámetro
  - Nueva ruta: `parametros_routes.py`
- **Test de Conexión SMTP**: Botón para probar configuración email
  - Nuevo endpoint `POST /api/email-config/test`
  - Prueba conexión SMTP antes de guardar
  - Usa contraseña guardada si no se introduce nueva
- **Cambio de Esquema de Colores**: Actualizado a rojo del logo (#FF4338)
  - Cabeceras, botones, badges y elementos de acento
  - Gradiente: #FF4338 → #D32F2F
  - Aplicado en todas las páginas
- **Fix: Diseño Responsive Móvil**: Corregido en páginas de administración
  - Solo se muestran tarjetas en móvil (no tabla + tarjetas)
  - Header centrado con logo más pequeño
  - Botón "Volver" ocupa ancho completo
- **Fix: Blueprint email_config no registrado**: Corregido en app.py
- **Soporte para Túneles Proxy (ngrok/Cloudflare)**: Implementado soporte completo para túneles
  - `ProxyFix` middleware en `app.py` para confiar en headers de proxy
  - Frontend detecta automáticamente localhost vs túnel (sin hardcodear puertos)
  - URLs de verificación de email se construyen correctamente con la URL del túnel
  - Probado con ngrok (recomendado) y Cloudflare Tunnel
  - Fix: Gmail bloquea emails con URLs de `trycloudflare.com`, usar ngrok como alternativa
- **Mejora Email de Verificación**: Estilo del botón con color blanco inline para compatibilidad

### 2025-12-29
- **Sistema Multi-Empresa**: Implementado soporte para múltiples empresas
  - Parámetro `?empresa=X` en URL es **OBLIGATORIO** en el primer acceso
  - Validación estricta: muestra error crítico si falta el parámetro y no hay valor en localStorage
  - Persistencia en `localStorage` para mantener contexto entre sesiones
  - Permite abrir múltiples navegadores con empresas diferentes simultáneamente
  - Todos los endpoints filtran datos por empresa_id
  - Documentación completa en `MULTI-EMPRESA.md`
- **Tabla `propuestas` extendida**: Añadido campo `empresa_id`
  - Tipo: VARCHAR(5) NOT NULL DEFAULT '1'
  - Índice creado para optimizar consultas por empresa
  - Script SQL: `09_alter_table_propuestas_empresa.sql`
- **API de Clientes**: Nuevos endpoints para gestión de clientes
  - Vista `view_externos_clientes` desde `cristal.dbo.genter` (tipoter='C')
  - `GET /api/clientes` - Listar todos los clientes
  - `GET /api/clientes/search` - Buscar con filtros (empresa, razon)
  - `GET /api/clientes/<codigo>` - Obtener cliente por código
  - Modelo `cliente_model.py`, controlador `cliente_controller.py`, rutas `cliente_routes.py`
  - Script SQL: `10_create_view_externos_clientes.sql`
- **Validación de Parámetro Empresa Obligatorio**: Implementado en frontend
  - `frontend/js/login.js` - Valida empresa en login, muestra error si falta
  - `frontend/js/app.js` - Valida empresa al cargar app principal
  - Pantalla de error crítico con diseño profesional y mensaje claro
  - Detiene inicialización si no hay empresa_id válido

### 2025-12-23
- **Cliente PowerBuilder 2022**: Objetos para consumir la API desde PowerBuilder
  - `n_cst_api_rest.sru` - Non-visual object con métodos para todos los endpoints
  - `w_test_api.srw` - Ventana de pruebas interactiva
  - Soporte HTTPClient y autenticación por API Key
  - README con instrucciones de importación y uso
- **API Propuestas para ERP**: Endpoints para integración con sistemas externos
  - `GET /api/propuestas/pendientes` - Lista propuestas con estado 'Enviada'
  - `GET /api/propuestas/<id>` - Detalle completo con líneas
  - `PUT /api/propuestas/<id>/estado` - Cambiar estado (Enviada/Procesada/Cancelada)
  - Autenticación: Sesión o API Key
  - Nueva ruta: `propuesta_routes.py`
- **Persistencia de Propuestas en BD**: Las solicitudes ahora se guardan en SQL Server
  - Nueva tabla `propuestas` (cabecera): id, user_id, fecha, comentarios, estado, total_items
  - Nueva tabla `propuestas_lineas` (detalle): todos los campos del producto solicitado
  - Nuevo modelo `propuesta_model.py` con métodos CRUD
  - Al enviar email exitosamente, se guarda automáticamente con estado 'Enviada'
  - Script SQL: `08_create_tables_propuestas.sql`
- **Sistema Multi-idioma (i18n)**: Implementada internacionalización completa
  - Idiomas: Español (es), Inglés (en), Francés (fr)
  - Sistema vanilla JS sin dependencias externas
  - `frontend/js/i18n/i18n.js` - Core con funciones `t()`, `I18n.init()`, `I18n.setLanguage()`
  - Archivos de traducción JSON con ~195 textos cada uno
  - Selector de idioma en header de todas las páginas
  - Atributos `data-i18n` y `data-i18n-placeholder` para HTML
  - Cambio de idioma sin recargar página
  - Persistencia en localStorage
  - Detección automática del idioma del navegador
- **Dockerización de la aplicación**: Añadida configuración Docker para despliegue
  - `backend/Dockerfile` con Python 3.11 y ODBC Driver 18
  - `docker-compose.yml` para producción (sin debug)
  - `docker-compose.dev.yml` para desarrollo (con debug y hot-reload)
  - `.dockerignore` para optimizar build
  - No afecta ejecución actual con Python directo
- **Botón carrito en detalle**: Añadido botón "Agregar al Carrito" en modal de detalle del producto

### 2025-12-22
- **Página de Verificación de Email**: Nueva página amigable para verificar cuenta
  - Ruta `/verificar-email?token=xxx` con mismo estilo que login/register
  - Estados de carga, éxito y error
  - Botón para ir al login tras verificación exitosa
- **Galería de Imágenes de Artículos**: Visualización de imágenes en vista detalle
  - Nueva vista `view_articulo_imagen` desde `cristal.dbo.ps_articulo_imagen`
  - Nuevo modelo `imagen_model.py` para obtener imágenes en base64
  - Endpoint `GET /api/stocks/{codigo}/imagenes`
  - Galería con miniaturas y modal para ampliar
  - Estilos responsive para móvil
- **Mejora Carrito**: Detección de duplicados por clave compuesta
  - Verifica: codigo + calidad + tono + calibre + pallet + caja
  - Eliminación por índice en lugar de código
  - Muestra pallet y caja en el modal del carrito
- **Sistema de Registro de Usuarios**: Implementado registro público con verificación por email
  - Nueva tabla `parametros` con flag `PERMITIR_REGISTRO` para habilitar/deshabilitar
  - Campos añadidos a `users`: pais, email_verificado, token_verificacion, token_expiracion
  - Endpoints: `/api/registro-habilitado`, `/api/paises`, `/api/register`, `/api/verify-email`
  - Lista de 196 países con códigos ISO 3166-1 (alfa-2 y alfa-3) en `backend/data/paises.json`
  - Verificación obligatoria de email antes de activar cuenta
  - Frontend: `register.html` y `register.js` para formulario de registro
  - Login muestra enlace a registro solo si está habilitado
- **Autenticación por API Key**: Implementada autenticación dual para integraciones externas
  - Nueva tabla `api_keys` para almacenar claves
  - Endpoints CRUD en `/api/api-keys`
  - Decorador `api_key_or_login_required` en `utils/auth.py`
  - Soporte en header `X-API-Key` o query param `?apikey=`
  - Rutas de stocks aceptan sesión o API Key
- **Seguridad API**: Protegidas todas las rutas de stocks
  - Antes: `/api/stocks/*` era accesible sin autenticación
  - Ahora: Requieren sesión activa o API Key válida
- **Swagger UI configurado**: Documentación interactiva en `/apidocs/`
  - Configurado Flasgger con OpenAPI specs
  - Documentados todos los endpoints con parámetros y respuestas
  - Accesible sin autenticación para consulta de documentación
- **Reorganización del proyecto**: Separado backend y frontend en carpetas independientes
  - `backend/`: app.py, config/, controllers/, models/, routes/, database/, utils/
  - `frontend/`: index.html, login.html, js/, css/, assets/
- Añadido header `Date` en emails (`backend/routes/carrito_routes.py:356`) - los emails llegaban sin fecha y se perdían en el correo
- Organizada carpeta Scripts SQL con archivos individuales y README
- Fix: Logo visible en pantalla de login en resolución móvil

### 2026-01-02
- **Header Rojo Unificado**: Todas las páginas ahora usan el mismo estilo de header
  - Página principal (index.html) migrada a clase `.page-header`
  - Fondo con gradiente rojo (#FF4338 → #D32F2F)
  - Logo en blanco (filtro invertido)
  - Título y subtítulo en blanco
- **Fix: Selector de Idioma en Headers Oscuros**: Nueva clase `.lang-selector-header`
  - Estilos específicos para selectores sobre fondo rojo
  - Color de texto blanco con `!important` para override
  - Aplicado en todas las páginas de administración e index.html
- **Fix: Título h1 en Headers**: Corregido problema de visibilidad
  - El h1 global usaba `-webkit-text-fill-color: transparent` para efecto gradiente
  - Añadido override en `.page-header h1` para forzar texto blanco
- **Fix: Selector de Idioma No Mostraba Valor Actual**:
  - Expuesto `I18n.currentLang` como getter en la API pública de i18n.js
  - Antes: `I18n.currentLang` era `undefined` y sobrescribía el valor correcto
- **Login: Enlace Reenvío Verificación Condicional**:
  - El enlace "¿No recibiste el email de verificación?" ahora respeta `PERMITIR_REGISTRO`
  - Oculto por defecto, solo visible si el registro está habilitado
  - Nuevo ID `resend-link-container` para control de visibilidad
- **Fix: Botón Atrás No Vuelve a Login**:
  - Nueva función `verificarSesionActiva()` al cargar login.js
  - Si ya hay sesión activa, redirige automáticamente a página principal
  - Usa `window.location.replace()` en lugar de `href` para no añadir al historial
- **Icono Menú Usuario**: Cambiado emoji 👤 por SVG blanco
  - Icono vectorial que hereda color del botón
  - Se ve correctamente sobre el fondo rojo del header
- **Modal Agregar Cantidad**: Añadido tono y calibre
  - Ahora muestra: código, formato, calidad, tono, calibre
  - Información más completa antes de agregar al carrito
- **Botones +/− Cantidad Mejorados**:
  - Cambiado de SVG a texto "−" y "+" grande (1.5rem)
  - Botón + con fondo rojo, botón − con fondo blanco y borde
  - Más visibles y fáciles de usar en móvil
- **Header Modal Cantidad Rojo**: Estilo unificado con resto de la app
  - Fondo con gradiente rojo (#FF4338 → #D32F2F)
  - Título y botón cerrar en blanco
- **Parámetro PERMITIR_PROPUESTAS**: Control de funcionalidad de propuestas
  - Nuevo parámetro en tabla `parametros` (Script: `12_insert_parametro_propuestas.sql`)
  - Endpoint público `GET /api/parametros/propuestas-habilitadas`
  - Método `ParametrosModel.permitir_propuestas()`
  - Si está desactivado (valor `0`):
    - Oculta botones "Agregar al carrito" en tabla, tarjetas y detalle
    - Oculta botón flotante del carrito
    - Oculta opciones del menú relacionadas con propuestas
  - Por defecto habilitado (valor `1`)

### 2026-01-04
- **Filtros en Páginas de Propuestas**: Añadidos filtros avanzados
  - Filtro por estado (Todos/Enviada/Procesada/Cancelada)
  - Filtro por rango de fechas (desde/hasta)
  - Botones "Buscar" y "Limpiar"
  - Aplicado en `mis-propuestas.html` y `todas-propuestas.html`
  - Traducciones i18n en español, inglés y francés
  - Nuevas claves: `proposals.filterStatus`, `filterDateFrom`, `filterDateTo`, `allStatuses`
- **Auto-cierre Modal Detalle**: El modal de detalle se cierra automáticamente
  - Al agregar un artículo al carrito desde el detalle, el modal se cierra tras confirmar
  - Flag `window.agregandoDesdeDetalle` para controlar comportamiento
  - Mejora UX evitando tener que cerrar manualmente
- **Fix: Campo 'caja' en Modelo de Stock**: Corregido mapeo del campo
  - El campo `caja` existía en la vista SQL pero no estaba en el SELECT
  - Añadido a todas las funciones: `get_all()`, `get_by_codigo()`, `get_by_codigo_and_empresa()`, `search()`
  - Ahora el detalle muestra correctamente el valor de caja (antes mostraba guión)
- **Multi-Empresa en Parámetros y Email Config**: Soporte completo para configuración por empresa
  - **Tabla `email_config`**: Añadido campo `empresa_id` VARCHAR(5)
    - Script SQL: `13_alter_table_email_config_empresa.sql`
    - Cada empresa puede tener sus propias configuraciones SMTP
  - **Tabla `parametros`**: Añadido campo `empresa_id` VARCHAR(5)
    - Script SQL: `14_alter_table_parametros_empresa.sql`
    - Restricción única compuesta: (clave, empresa_id)
    - Eliminada restricción única antigua solo sobre `clave`
  - **Backend actualizado**:
    - `email_config_model.py` - Todas las funciones reciben `empresa_id`
    - `parametros_model.py` - Todas las funciones reciben `empresa_id`
    - `email_config_routes.py` - Helper `get_empresa_id()` para obtener del contexto
    - `parametros_routes.py` - Helper `get_empresa_id()` para obtener del contexto
    - `carrito_routes.py` - Pasa `empresa_id` al enviar email
    - `register_routes.py` - Pasa `empresa_id` para verificación de registro
  - **Frontend actualizado** para pasar `empresa_id` en todas las llamadas API:
    - `parametros.html` - `loadParams()`, `toggleParam()`, `saveTextParam()`
    - `email-config.html` - `loadConfigs()`, `activateConfig()`, `saveConfig()`, `testConnection()`
    - `login.js` - `verificarRegistroHabilitado()`, `reenviarVerificacion()`
    - `register.js` - `verificarRegistroHabilitado()`, formulario de registro, redirect
    - `app.js` - `verificarPropuestasHabilitadas()`
    - `mis-propuestas.html` y `todas-propuestas.html` - Ya tenían soporte
- **Fix: Parámetros no cargaban por empresa**: Corregido
  - El frontend no pasaba `empresa_id` en las llamadas API
  - Ahora cada empresa tiene sus propios parámetros independientes
- **Cambio de Contraseña Obligatorio**: Para usuarios creados por admin
  - Nuevo campo `debe_cambiar_password` en tabla `users`
  - Script SQL: `16_alter_table_users_debe_cambiar_password.sql`
  - Modal de cambio de contraseña en login (`login.html`, `login.js`)
  - Endpoint `POST /api/usuarios/cambiar-password`
  - Modelo `User` actualizado con atributo `debe_cambiar_password`
  - `app.js` verifica flag y redirige al login si debe cambiar
  - `login.js` muestra modal en lugar de redirigir si hay sesión con cambio pendiente
- **Email de Bienvenida Mejorado**: Para usuarios creados por admin
  - Botón "Acceder al Sistema" con enlace al login incluyendo `?empresa=X`
  - Mensaje de advertencia sobre cambio de contraseña obligatorio
  - Credenciales de acceso (usuario y contraseña temporal)
- **CRUD Completo de Usuarios**: Creación desde panel de administración
  - Formulario en `usuarios.html` con campos: usuario, email, nombre, contraseña, empresa_id, cliente_id
  - Endpoint `POST /api/usuarios` para crear usuarios
  - Envío automático de email de bienvenida con credenciales
  - Validaciones de campos requeridos y duplicados
- **Fix: EmailConfigModel.get_active**: Corregido nombre del método
  - El método correcto es `get_active_config()`, no `get_active()`
  - Afectaba al envío de email de bienvenida

### 2026-01-05
- **Sistema de Consultas sobre Productos**: Formulario de contacto y WhatsApp
  - Nueva tabla `consultas` para almacenar consultas (Script: `18_create_table_consultas.sql`)
  - Nuevo modelo `consulta_model.py` con métodos CRUD
  - Nuevas rutas `consulta_routes.py`:
    - `POST /api/consultas` - Enviar consulta por email
    - `GET /api/consultas/whatsapp-config` - Obtener número WhatsApp
  - Modal de consulta en detalle de producto con formulario
  - Botón WhatsApp con icono SVG y mensaje prellenado
  - Parámetro `WHATSAPP_NUMERO` para configurar número de contacto
  - Traducciones i18n en español, inglés y francés (namespace `inquiry`)
- **Modo Oscuro**: Tema oscuro configurable en la interfaz
  - Toggle en menú de usuario bajo sección "Apariencia"
  - Variables CSS para colores dinámicos (`--text-primary`, `--bg-primary`, etc.)
  - Selector `[data-theme="dark"]` con override de todos los elementos
  - Estilos específicos para: tablas (thead, tbody, tr), modales, tarjetas, menús, inputs
  - Persistencia en localStorage
  - Icono de luna/sol que cambia según el tema
  - Funciones `loadTheme()`, `applyTheme()`, `toggleTheme()` en `app.js`
- **Modo Oscuro en Menú de Perfil**: El dropdown del usuario ahora respeta el tema
  - Estilos dark mode para `.menu-dropdown` en `styles.css`
  - Fondo, bordes, textos y hover adaptativos
  - El menú cambia inmediatamente al activar modo oscuro
- **Modo Oscuro en Páginas de Administración**: Soporte completo en todas las páginas
  - Estilos para contenedores: `.proposals-container`, `.users-container`, etc.
  - Estilos para tablas: `.proposals-table`, `.users-table`
  - Estilos para tarjetas móviles: `.proposal-card`, `.user-card`
  - Estilos para formularios y modales de administración
  - Script de carga de tema en: `mis-propuestas.html`, `todas-propuestas.html`, `usuarios.html`, `email-config.html`, `parametros.html`
- **Fix: empresa_id en URL de verificación de email**
  - El enlace de verificación ahora incluye `?empresa=X`
  - `verify-email.html` captura el parámetro y lo guarda en localStorage
  - Los botones "Ir al Login" incluyen el parámetro empresa
- **Fix: Funciones onclick no accesibles en HTML dinámico**
  - Funciones de consulta expuestas a `window` para onclick en HTML generado
  - `window.abrirModalConsulta`, `window.abrirWhatsApp`, etc.
- **Fix: WhatsApp no mostraba botón con número configurado**
  - Corregido llamada a `ParametrosModel.get()` (antes `get_valor()`)
- **Página de Administración de Consultas**: Nueva página para gestionar consultas
  - `todas-consultas.html` - Página completa para administradores/superusuarios
  - Ruta `/todas-consultas.html` añadida en `app.py`
  - Opción "Todas las Consultas" en menú de administración (`index.html`)
  - Navegación añadida en `app.js` (función `navigateTo`)
  - Filtros por estado (Pendiente/Respondida/Cerrada) y rango de fechas
  - Vista tabla (desktop) y tarjetas (móvil)
  - Modal de detalle con información completa del producto y cliente
  - Formulario de respuesta integrado en el modal
  - Endpoints utilizados: `GET /api/consultas`, `GET /api/consultas/<id>`, `POST /api/consultas/<id>/responder`, `PUT /api/consultas/<id>/estado`
  - Traducciones i18n completas (namespace `inquiries` con ~40 claves)
  - Modo oscuro completo con estilos en `styles.css`
- **Logo Clicable en Páginas Admin**: Navegación rápida a stocks
  - El logo en el header ahora es clicable en todas las páginas de administración
  - Redirige a `index.html` manteniendo el parámetro `empresa_id`
  - Aplicado en: `mis-propuestas.html`, `todas-propuestas.html`, `todas-consultas.html`, `usuarios.html`, `email-config.html`, `parametros.html`
- **Favicon**: Añadido icono de pestaña del navegador
  - Archivo `favicon.ico` en `frontend/assets/`
  - Añadido `<link rel="icon">` en todas las páginas HTML (10 archivos)
- **Campo EAN13 en Detalle de Stock**: Nuevo campo para código de barras
  - Campo `ean13` (VARCHAR(20)) añadido a la vista `view_externos_stock`
  - `stock_model.py`: Campo incluido en todas las consultas SQL
  - `app.js`: Muestra EAN-13 en modal de detalle (condicional, solo si tiene valor)
  - Traducciones i18n: `detail.ean13` en ES/EN/FR
- **Actualización Docker para Producción**: Configuración mejorada
  - `Dockerfile`: Usuario no-root, gunicorn (4 workers, 2 threads), healthcheck
  - `Dockerfile.dev`: Nuevo archivo para desarrollo con Flask dev server y hot-reload
  - `docker-compose.yml`: Healthcheck, logging rotativo (10MB, 3 archivos), network dedicada
  - `docker-compose.dev.yml`: Usa Dockerfile.dev con volumen para hot-reload
  - `requirements.txt`: Añadido gunicorn==23.0.0, organizado por categorías
  - `.dockerignore`: Ampliado con más exclusiones
- **Modo Oscuro en Detalle de Propuestas**: Estilos dark mode completos
  - `mis-propuestas.html`: Estilos para modal de detalle, tablas, tarjetas, filtros
  - `todas-propuestas.html`: Estilos para modal de detalle, tablas, tarjetas, filtros, user-badge
  - Elementos cubiertos: `.proposal-info`, `.proposal-lines-table`, `.line-card`, `.proposal-comments`, `.filters-container`
- **Modo Oscuro en Modal de Cantidad**: Estilos dark mode para agregar al carrito
  - `.quantity-detail-item`: Tags de código, formato, calidad con fondo oscuro
  - `.quantity-btn`: Botones +/- con colores adaptativos
  - `.quantity-input`: Input con fondo y texto correctos
  - `.quantity-package-label`, `.quantity-package-btn`: Etiquetas y botones de caja/pallet
  - `.quantity-btn-cancel`: Botón cancelar con estilo oscuro
- **Modo Oscuro en Status Badges**: Colores más vibrantes
  - `.status-enviada`: Amarillo brillante (#ffc107) con fondo semitransparente
  - `.status-procesada`: Verde brillante (#4caf50) con fondo semitransparente
  - `.status-cancelada`: Rojo brillante (#f44336) con fondo semitransparente
- **UX Modal de Detalle**: Mejoras de usabilidad
  - Botón "Cerrar" gris añadido abajo del modal
  - Clic fuera del contenido cierra el modal
  - Tecla Escape cierra el modal
  - Ahora hay 4 formas de cerrar: X, botón Cerrar, clic fuera, Escape
- **Modo Oscuro en Textarea Comentarios**: Fix para formulario de envío
  - `.envio-form textarea`: Fondo y texto adaptativos en dark mode
  - Eliminados estilos inline del HTML para que CSS tenga efecto
  - Corregido `background: white` hardcodeado en `:focus`

### 2026-01-06
- **Dashboard de Estadísticas para Administradores**: Panel completo con métricas
  - Nueva página `dashboard.html` con diseño responsive
  - 5 tarjetas de resumen: total propuestas, pendientes, usuarios activos, consultas pendientes, items solicitados
  - Gráfico de línea: propuestas por día (últimos 7 días) con Chart.js
  - Gráfico doughnut: distribución de propuestas por estado
  - Gráfico de barras: propuestas por mes (últimos 6 meses)
  - Tabla: top 10 productos más solicitados
  - Lista: top 10 usuarios más activos
  - Selectores de período: 7, 30, 90 días
  - Soporte completo para modo oscuro
  - Nuevo modelo `estadisticas_model.py` con consultas SQL optimizadas
  - Nuevas rutas `estadisticas_routes.py` con 7 endpoints protegidos por rol admin
  - Opción "Dashboard" añadida al menú de administración
  - Traducciones i18n completas (namespace `dashboard` con ~20 claves)
- **Checkbox Copia de Email**: Opción para recibir copia del pedido
  - Checkbox en formulario de envío de propuestas
  - Si está marcado, el usuario recibe copia del email con el PDF
  - Campo `send_copy` en la petición POST al enviar carrito
  - Traducción: `shipping.sendCopy` en ES/EN/FR
- **Ficha Técnica PDF**: Descarga de fichas técnicas de productos
  - Nueva vista SQL `view_externos_articulo_ficha_tecnica` (creada por usuario)
  - Nuevo modelo `ficha_tecnica_model.py` con métodos:
    - `get_by_codigo(codigo, empresa_id)` - Obtiene PDF en base64
    - `exists(codigo, empresa_id)` - Verifica si existe ficha
  - Nuevos endpoints en `stock_routes.py`:
    - `GET /api/stocks/<codigo>/ficha-tecnica/exists` - Verificación
    - `GET /api/stocks/<codigo>/ficha-tecnica` - Descarga (base64 o archivo)
  - Botón de descarga solo visible si el producto tiene ficha técnica
  - Bloque visual en modal de detalle con borde y botón "Descargar PDF"
  - Traducciones: `detail.technicalSheet`, `detail.downloadPdf`
- **Reorganización Modal de Detalle**: Bloques visuales mejorados
  - Nuevo bloque "Ficha Técnica" con borde y botón de descarga
  - Nuevo bloque "Contacto" con botones "Consultar" y "WhatsApp"
  - Ambos bloques con estilo consistente (borde, padding, border-radius)
  - Traducción: `detail.contact` para etiqueta del bloque
  - Mejor organización visual de la información del producto

---
## Servidores de Despliegue

### Servidor Cristal (Desarrollo/Producción)
- **IP**: 10.1.99.4
- **Usuario**: administrador
- **Contraseña**: crijob15
- **Ruta**: /opt/ApiRestExternos
- **Método**: Docker (docker-compose)
- **Estado**: Funcionando

### Servidor Cloud (Producción) - OVH
- **IP**: 51.68.44.136
- **Usuario**: ubuntu
- **Contraseña**: Desa2012Job
- **Ruta**: /opt/ApiRestExternos
- **Método**: Docker (docker-compose)
- **Estado**: Docker instalado, contenedores corriendo, **PENDIENTE: conexión a BD**
- **Problema actual**: El servidor cloud no puede conectar a la BD local (192.168.63.25) porque están en redes diferentes
- **Soluciones posibles**:
  1. Exponer SQL Server a internet (abrir puerto 1433 en firewall/router, usar IP pública)
  2. Configurar VPN entre servidor cloud y red local
  3. Usar otra instancia de SQL Server accesible desde internet

### Comandos útiles para servidores

```bash
# Conectar al servidor local
ssh root@192.168.63.51

# Conectar al servidor cloud
ssh ubuntu@51.68.44.136

# Ver estado de contenedores
sudo docker ps -a

# Ver logs del backend
sudo docker logs apirest-backend -f

# Reiniciar contenedores
cd /opt/ApiRestExternos && sudo docker-compose down && sudo docker-compose up -d

# Actualizar código (desde local)
scp -r backend frontend docker-compose.yml ubuntu@51.68.44.136:/opt/ApiRestExternos/
```

### Base de Datos
- **Servidor BD**: 192.168.63.25\SQL2008,1433
- **Base de datos**: ApiRestStocks
- **Usuario**: sa
- **Contraseña**: Desa1
- **Nota**: Solo accesible desde red local (192.168.63.x)

---
*Última actualización: 2026-03-08*
