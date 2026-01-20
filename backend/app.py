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
# Fecha : 2026-01-08
# ============================================================

from flask import Flask, jsonify, send_from_directory, request, redirect, url_for, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flasgger import Swagger
from werkzeug.middleware.proxy_fix import ProxyFix
from routes.stock_routes import stock_bp
from routes.carrito_routes import carrito_bp
from routes.api_key_routes import api_key_bp
from routes.register_routes import register_bp
from routes.propuesta_routes import propuesta_bp
from routes.cliente_routes import cliente_bp
from routes.usuario_routes import usuario_bp
from routes.parametros_routes import parametros_bp
from routes.email_config_routes import email_config_bp
from routes.consulta_routes import consulta_bp
from routes.estadisticas_routes import estadisticas_bp
from routes.empresa_logo_routes import empresa_logo_bp
from routes.user_session_routes import user_session_bp
from routes.empresa_routes import empresa_bp
from database.users_db import verify_user, get_user_by_id
from models.user import User
from models.user_session_model import UserSessionModel

import os
import secrets

# Versión de la aplicación
APP_VERSION = 'v1.2.0'

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR)

# ==================== CONFIGURACIÓN DE SEGURIDAD ====================
# SECRET_KEY: usar variable de entorno en producción
# Generar con: python -c "import secrets; print(secrets.token_hex(32))"
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-cambiar-en-produccion-' + str(hash('ApiRestExternos')))

# Configuración de cookies de sesión
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,      # JavaScript no puede leer la cookie (protege XSS)
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',  # Solo HTTPS en producción
    SESSION_COOKIE_SAMESITE='Lax',     # Protección CSRF (Lax permite navegación normal)
)

# Expiración de sesión por rol
SESSION_LIFETIME_USUARIO = timedelta(hours=2)      # Usuarios normales: 2 horas
SESSION_LIFETIME_ADMIN = timedelta(hours=8)        # Administradores: 8 horas
SESSION_LIFETIME_SUPERUSUARIO = timedelta(days=7)  # Superusuarios: 7 días

# ProxyFix para confiar en headers de proxy (Cloudflare Tunnel, nginx, etc.)
# x_for=1: confía en X-Forwarded-For (IP del cliente)
# x_proto=1: confía en X-Forwarded-Proto (http/https)
# x_host=1: confía en X-Forwarded-Host (hostname)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# CORS: En producción, configurar CORS_ORIGINS con dominios permitidos
# Ejemplo: CORS_ORIGINS=https://midominio.com,https://otro.com
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=True)

# ==================== RATE LIMITING ====================
# Protección contra ataques de fuerza bruta
# Usa Redis en producción para compartir límites entre workers de Gunicorn
redis_url = os.environ.get('REDIS_URL', 'memory://')
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],  # Sin límite por defecto, solo en endpoints específicos
    storage_uri=redis_url,
)

# Configurar Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "info": {
        "title": "API Rest Stocks",
        "description": "API para gestión de inventario de azulejos/cerámica.\n\n**Autenticación:**\n- **API Key**: Header `X-API-Key` (crear en POST /api/api-keys)\n- **Sesión**: Usar POST /api/login (para frontend)",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "apiKeyAuth": {
            "type": "apiKey",
            "name": "X-API-Key",
            "in": "header",
            "description": "API Key para autenticación. Crear en POST /api/api-keys"
        }
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

@login_manager.user_loader
def load_user(user_id):
    # Obtener connection y empresa_id de la sesión
    connection = session.get('connection')
    empresa_id = session.get('empresa_id')

    print(f"[DEBUG] load_user - user_id: {user_id}, connection: {connection}, empresa_id: {empresa_id}", flush=True)

    if not connection:
        print(f"[DEBUG] load_user - No connection en sesión, retornando None", flush=True)
        return None

    user_data = get_user_by_id(int(user_id), connection, empresa_id)
    if user_data:
        rol = user_data.get('rol', 'usuario')
        print(f"[DEBUG] load_user - Usuario encontrado: {user_data.get('username')}, rol: {rol}", flush=True)
        return User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data.get('email'),
            full_name=user_data.get('full_name'),
            rol=rol,
            empresa_id=user_data.get('empresa_id', empresa_id),
            cliente_id=user_data.get('cliente_id'),
            debe_cambiar_password=user_data.get('debe_cambiar_password', False)
        )
    print(f"[DEBUG] load_user - Usuario NO encontrado para id: {user_id}", flush=True)
    return None

# Registrar blueprints
app.register_blueprint(stock_bp)
app.register_blueprint(carrito_bp)
app.register_blueprint(api_key_bp)
app.register_blueprint(register_bp)
app.register_blueprint(propuesta_bp)
app.register_blueprint(cliente_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(parametros_bp, url_prefix='/api/parametros')
app.register_blueprint(email_config_bp)
app.register_blueprint(empresa_logo_bp)
app.register_blueprint(consulta_bp)
app.register_blueprint(estadisticas_bp)
app.register_blueprint(user_session_bp)
app.register_blueprint(empresa_bp)

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route('/')
@app.route('/index.html')
def home():
    if current_user.is_authenticated:
        return send_from_directory(FRONTEND_DIR, 'index.html')
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return send_from_directory(FRONTEND_DIR, 'login.html')

@app.route('/register')
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return send_from_directory(FRONTEND_DIR, 'register.html')

@app.route('/verificar-email')
def verify_email_page():
    return send_from_directory(FRONTEND_DIR, 'verify-email.html')

# ==================== PÁGINAS DEL MENÚ ====================

@app.route('/mis-propuestas.html')
@login_required
def mis_propuestas_page():
    return send_from_directory(FRONTEND_DIR, 'mis-propuestas.html')

@app.route('/todas-propuestas.html')
@login_required
def todas_propuestas_page():
    return send_from_directory(FRONTEND_DIR, 'todas-propuestas.html')

@app.route('/usuarios.html')
@login_required
def usuarios_page():
    return send_from_directory(FRONTEND_DIR, 'usuarios.html')

@app.route('/email-config.html')
@login_required
def email_config_page():
    return send_from_directory(FRONTEND_DIR, 'email-config.html')

@app.route('/parametros.html')
@login_required
def parametros_page():
    return send_from_directory(FRONTEND_DIR, 'parametros.html')

@app.route('/todas-consultas.html')
@login_required
def todas_consultas_page():
    return send_from_directory(FRONTEND_DIR, 'todas-consultas.html')

@app.route('/dashboard.html')
@login_required
def dashboard_page():
    return send_from_directory(FRONTEND_DIR, 'dashboard.html')

@app.route('/empresa-logo.html')
@login_required
def empresa_logo_page():
    return send_from_directory(FRONTEND_DIR, 'empresa-logo.html')

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")  # Máximo 5 intentos por minuto por IP
def login():
    """
    Iniciar sesión
    ---
    tags:
      - Autenticación
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: admin
            password:
              type: string
              example: mipassword
    responses:
      200:
        description: Login exitoso
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Login exitoso
            user:
              type: object
              properties:
                username:
                  type: string
                full_name:
                  type: string
      400:
        description: Faltan credenciales
      401:
        description: Credenciales inválidas
    """
    from models.empresa_cliente_model import EmpresaClienteModel

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    # Aceptar 'connection' o 'empresa_cli_id' para compatibilidad
    connection = data.get('connection') or data.get('empresa_cli_id') or data.get('empresa_id') or data.get('empresa')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuario y contraseña requeridos'}), 400

    if not connection:
        return jsonify({'success': False, 'message': 'Se requiere connection'}), 400

    # Limpiar caché para asegurar datos frescos de BD central
    EmpresaClienteModel.clear_cache()

    # Obtener datos de empresa de BD central
    empresa_info = EmpresaClienteModel.get_by_id(connection)
    if not empresa_info:
        return jsonify({'success': False, 'message': f'Empresa {connection} no encontrada'}), 404

    empresa_id = empresa_info.get('empresa_erp')

    # Verificar usuario con conexión dinámica
    user_data = verify_user(username, password, connection, empresa_id)

    if user_data:
        user = User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data.get('email'),
            full_name=user_data.get('full_name'),
            rol=user_data.get('rol', 'usuario'),
            empresa_id=empresa_id,
            cliente_id=user_data.get('cliente_id')
        )
        login_user(user)

        # Configurar expiración de sesión según rol
        session.permanent = True
        if user.rol == 'superusuario':
            app.permanent_session_lifetime = SESSION_LIFETIME_SUPERUSUARIO
        elif user.rol == 'administrador':
            app.permanent_session_lifetime = SESSION_LIFETIME_ADMIN
        else:
            app.permanent_session_lifetime = SESSION_LIFETIME_USUARIO

        # ⭐ Guardar connection, empresa_id y carrito en sesión
        session['connection'] = connection
        session['empresa_id'] = empresa_id
        session['empresa_nombre'] = empresa_info.get('nombre')
        session['carrito'] = []
        session['user_id'] = user_data['id']

        # Crear sesion en BD para tracking
        try:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            session_token = UserSessionModel.create(user_data['id'], empresa_id, ip_address)
            if session_token:
                session['session_token'] = session_token
        except Exception as e:
            print(f"Warning: No se pudo crear sesion en BD: {e}")

        # Verificar si debe cambiar la contraseña
        debe_cambiar = user_data.get('debe_cambiar_password', False)

        # Generar CSRF token
        csrf_token = secrets.token_hex(32)
        session['csrf_token'] = csrf_token

        return jsonify({
            'success': True,
            'message': 'Login exitoso',
            'debe_cambiar_password': debe_cambiar,
            'csrf_token': csrf_token,
            'user': {
                'username': user.username,
                'full_name': user.full_name,
                'rol': user.rol,
                'connection': connection,
                'empresa_id': empresa_id,
                'empresa_nombre': empresa_info.get('nombre'),
                'cliente_id': user.cliente_id
            }
        })

    return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """
    Cerrar sesión
    ---
    tags:
      - Autenticación
    security:
      - cookieAuth: []
    responses:
      200:
        description: Logout exitoso
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Logout exitoso
      401:
        description: No autenticado
    """
    # Eliminar sesion de BD
    try:
        session_token = session.get('session_token')
        if session_token:
            UserSessionModel.delete(session_token)
    except Exception as e:
        print(f"Warning: No se pudo eliminar sesion de BD: {e}")

    # ⭐ Limpiar carrito y CSRF token al cerrar sesión
    session.pop('carrito', None)
    session.pop('session_token', None)
    session.pop('csrf_token', None)
    logout_user()
    return jsonify({'success': True, 'message': 'Logout exitoso'})

@app.route('/api/current-user')
@login_required
def get_current_user():
    """
    Obtener usuario actual
    ---
    tags:
      - Autenticación
    security:
      - cookieAuth: []
    responses:
      200:
        description: Información del usuario autenticado
        schema:
          type: object
          properties:
            username:
              type: string
              example: admin
            full_name:
              type: string
              example: Administrador
            email:
              type: string
              example: admin@empresa.com
            rol:
              type: string
              example: usuario
              enum: [usuario, administrador, superusuario]
      401:
        description: No autenticado
    """
    return jsonify({
        'username': current_user.username,
        'full_name': current_user.full_name,
        'email': current_user.email,
        'rol': current_user.rol,
        'debe_cambiar_password': getattr(current_user, 'debe_cambiar_password', False),
        'empresa_id': session.get('empresa_id'),
        'connection': session.get('connection'),
        'empresa_nombre': session.get('empresa_nombre')
    })

@app.route('/api/version')
def get_version():
    """
    Obtener versión de la aplicación
    ---
    tags:
      - Sistema
    responses:
      200:
        description: Versión actual de la aplicación
        schema:
          type: object
          properties:
            version:
              type: string
              example: v1.0.0
    """
    return jsonify({'version': APP_VERSION})

@app.route('/api/csrf-token')
@login_required
def get_csrf_token():
    """
    Obtener CSRF token
    ---
    tags:
      - Autenticación
    security:
      - cookieAuth: []
    responses:
      200:
        description: CSRF token actual
        schema:
          type: object
          properties:
            csrf_token:
              type: string
              example: "abc123..."
      401:
        description: No autenticado
    """
    # Si no existe, generar uno nuevo
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return jsonify({'csrf_token': session['csrf_token']})

# ==================== ARCHIVOS ESTÁTICOS ====================

@app.route('/js/app.js')
@login_required
def serve_js():
    response = send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'app.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/css/styles.css')
def serve_css():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'css'), 'styles.css', mimetype='text/css')

@app.route('/js/login.js')
def serve_login_js():
    response = send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'login.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/js/register.js')
def serve_register_js():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'register.js', mimetype='application/javascript')

@app.route('/js/i18n/i18n.js')
def serve_i18n_js():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'js', 'i18n'), 'i18n.js', mimetype='application/javascript')

@app.route('/js/i18n/<lang>.json')
def serve_i18n_lang(lang):
    # Solo permitir idiomas válidos
    if lang not in ['es', 'en', 'fr']:
        return jsonify({'error': 'Invalid language'}), 404
    return send_from_directory(os.path.join(FRONTEND_DIR, 'js', 'i18n'), f'{lang}.json', mimetype='application/json')

@app.route('/assets/logo.svg')
def logo():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), 'logo.svg')

@app.route('/assets/logo.png')
def logo_png():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), 'logo.png')

@app.route('/assets/logojobers.png')
def logo_jobers():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), 'logojobers.png')

@app.route('/assets/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), 'favicon.ico')

@app.route('/assets/faviconjobers.ico')
def favicon_jobers():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), 'faviconjobers.ico')

@app.route('/favicon.ico')
def favicon_root():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), 'favicon.ico')

# ==================== PROTEGER RUTAS API ====================

@app.before_request
def require_login():
    allowed_routes = ['login_page', 'login', 'register_page', 'verify_email_page', 'serve_css', 'serve_login_js', 'serve_register_js', 'serve_i18n_js', 'serve_i18n_lang', 'logo', 'logo_png', 'logo_jobers', 'favicon', 'favicon_jobers', 'favicon_root', 'static', 'flasgger.static', 'flasgger.apispec', 'empresa_logo.get_logo', 'empresa_logo.get_favicon', 'empresa_logo.logo_exists', 'empresa_logo.get_config', 'empresa_logo.get_tema', 'empresa_logo.get_invertir', 'get_version']
    # Permitir acceso a Swagger UI
    if request.path.startswith('/apidocs') or request.path.startswith('/flasgger_static') or request.path.startswith('/apispec'):
        return None

    # Permitir rutas de registro, empresa y consultas sin autenticación
    public_api_routes = ['/api/register', '/api/verify-email', '/api/resend-verification', '/api/paises', '/api/registro-habilitado', '/api/parametros/propuestas-habilitadas', '/api/consultas/whatsapp-config', '/api/empresa/validate', '/api/empresa/init', '/api/empresa/list']
    if any(request.path.startswith(route) for route in public_api_routes):
        return None

    # Verificar autenticación por sesión o API Key
    api_key = request.headers.get('X-API-Key') or request.args.get('apikey')
    is_authenticated = current_user.is_authenticated or api_key

    # Verificar si la sesion fue eliminada de BD (matar sesion desde dashboard)
    if current_user.is_authenticated:
        try:
            session_token = session.get('session_token')
            if session_token:
                if not UserSessionModel.exists(session_token):
                    # Sesion eliminada de BD, cerrar sesion de Flask
                    session.pop('carrito', None)
                    session.pop('session_token', None)
                    logout_user()
                    is_authenticated = False
                else:
                    # Actualizar ultima actividad
                    UserSessionModel.update_activity(session_token)
        except Exception:
            pass

    if request.endpoint not in allowed_routes and not is_authenticated:
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': 'No autenticado'}), 401
        return redirect(url_for('login_page'))

# ==================== ERROR HANDLERS ====================

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handler para cuando se excede el límite de peticiones"""
    return jsonify({
        'success': False,
        'message': 'Demasiados intentos. Por favor, espera un momento antes de intentarlo de nuevo.',
        'error': 'rate_limit_exceeded'
    }), 429

if __name__ == '__main__':
    print("=" * 60)
    print("Servidor Flask iniciado con autenticacion y carrito")
    print("=" * 60)
    print(f"Acceso local:    http://localhost:5000")
    print(f"Acceso en red:   http://192.168.10.161:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)