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
from routes.audit_routes import audit_bp
from routes.pedido_routes import pedido_bp
from routes.db_info_routes import db_info_bp
from routes.almacen_routes import almacen_bp
from routes.notification_routes import notification_bp
from database.users_db import verify_user, get_user_by_id
from models.user import User
from models.user_session_model import UserSessionModel
from models.audit_model import AuditModel, AuditAction, AuditResult
from models.cliente_model import ClienteModel
from models.dominio_model import DominioModel
from utils.password_policy import get_policy_info, PASSWORD_POLICY
from utils.geoip import get_location
from config.database import Database
from utils.db_migrator import run_pending as run_migrations, needs_check as migrations_need_check, mark_checked as migrations_mark_checked
from migrations import MIGRATIONS

import os
import re
import secrets
import logging
import time
import threading
from datetime import datetime


def parse_user_agent(ua_string):
    """
    Parsear User-Agent para extraer navegador, SO y tipo de dispositivo.
    """
    if not ua_string:
        return {'browser': 'Desconocido', 'os': 'Desconocido', 'device_type': 'Desconocido'}

    # Detectar navegador
    browser = 'Otro'
    if 'Edg/' in ua_string:
        m = re.search(r'Edg/([\d.]+)', ua_string)
        browser = f"Edge {m.group(1).split('.')[0]}" if m else 'Edge'
    elif 'OPR/' in ua_string or 'Opera' in ua_string:
        m = re.search(r'OPR/([\d.]+)', ua_string)
        browser = f"Opera {m.group(1).split('.')[0]}" if m else 'Opera'
    elif 'Chrome/' in ua_string and 'Safari/' in ua_string:
        m = re.search(r'Chrome/([\d.]+)', ua_string)
        browser = f"Chrome {m.group(1).split('.')[0]}" if m else 'Chrome'
    elif 'Firefox/' in ua_string:
        m = re.search(r'Firefox/([\d.]+)', ua_string)
        browser = f"Firefox {m.group(1).split('.')[0]}" if m else 'Firefox'
    elif 'Safari/' in ua_string and 'Chrome/' not in ua_string:
        m = re.search(r'Version/([\d.]+)', ua_string)
        browser = f"Safari {m.group(1).split('.')[0]}" if m else 'Safari'

    # Detectar SO
    os_name = 'Otro'
    if 'Windows NT 10.0' in ua_string:
        os_name = 'Windows 11' if 'Windows NT 10.0; Win64' in ua_string and ('rv:' in ua_string or int(re.search(r'Chrome/(\d+)', ua_string).group(1)) >= 108 if re.search(r'Chrome/(\d+)', ua_string) else False) else 'Windows 10'
    elif 'Windows NT 6.3' in ua_string:
        os_name = 'Windows 8.1'
    elif 'Windows NT 6.1' in ua_string:
        os_name = 'Windows 7'
    elif 'Mac OS X' in ua_string:
        m = re.search(r'Mac OS X ([\d_]+)', ua_string)
        ver = m.group(1).replace('_', '.') if m else ''
        os_name = f"macOS {ver}" if ver else 'macOS'
    elif 'Android' in ua_string:
        m = re.search(r'Android ([\d.]+)', ua_string)
        os_name = f"Android {m.group(1)}" if m else 'Android'
    elif 'iPhone OS' in ua_string or 'iPad' in ua_string:
        m = re.search(r'OS ([\d_]+)', ua_string)
        ver = m.group(1).replace('_', '.') if m else ''
        os_name = f"iOS {ver}" if ver else 'iOS'
    elif 'Linux' in ua_string:
        os_name = 'Linux'

    # Detectar tipo de dispositivo
    device_type = 'Desktop'
    ua_lower = ua_string.lower()
    if 'ipad' in ua_lower or 'tablet' in ua_lower:
        device_type = 'Tablet'
    elif 'mobile' in ua_lower or 'iphone' in ua_lower or ('android' in ua_lower and 'mobile' in ua_lower):
        device_type = 'Mobile'
    elif 'android' in ua_lower:
        device_type = 'Tablet'

    return {'browser': browser, 'os': os_name, 'device_type': device_type}


def get_client_ip():
    """
    Obtener IP real del cliente, considerando proxies.
    Revisa varios headers en orden de prioridad.
    """
    # Headers comunes de proxies (en orden de prioridad)
    headers_to_check = [
        'X-Forwarded-For',      # Estándar de proxies
        'X-Real-IP',            # Nginx
        'CF-Connecting-IP',     # Cloudflare
        'True-Client-IP',       # Akamai
        'X-Client-IP',          # Otros proxies
    ]

    for header in headers_to_check:
        ip = request.headers.get(header)
        if ip:
            # X-Forwarded-For puede tener múltiples IPs separadas por coma
            # La primera es la IP original del cliente
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            return ip

    # Si no hay headers de proxy, usar remote_addr
    return request.remote_addr


# Versión de la aplicación
APP_VERSION = 'v1.33.1'

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

    if not connection:
        return None

    user_data = get_user_by_id(int(user_id), connection, empresa_id)
    if user_data:
        return User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data.get('email'),
            full_name=user_data.get('full_name'),
            rol=user_data.get('rol', 'usuario'),
            empresa_id=user_data.get('empresa_id', empresa_id),
            cliente_id=user_data.get('cliente_id'),
            debe_cambiar_password=user_data.get('debe_cambiar_password', False),
            company_name=user_data.get('company_name'),
            mostrar_precios=user_data.get('mostrar_precios', False)
        )
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
app.register_blueprint(audit_bp)
app.register_blueprint(pedido_bp)
app.register_blueprint(db_info_bp)
app.register_blueprint(almacen_bp)
app.register_blueprint(notification_bp)

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

@app.route('/reset-password')
def reset_password_page():
    return send_from_directory(FRONTEND_DIR, 'reset-password.html')

# ==================== PÁGINAS DEL MENÚ ====================

@app.route('/mis-propuestas.html')
@login_required
def mis_propuestas_page():
    return send_from_directory(FRONTEND_DIR, 'mis-propuestas.html')

@app.route('/mis-pedidos.html')
@login_required
def mis_pedidos_page():
    return send_from_directory(FRONTEND_DIR, 'mis-pedidos.html')

@app.route('/todas-propuestas.html')
@login_required
def todas_propuestas_page():
    return send_from_directory(FRONTEND_DIR, 'todas-propuestas.html')

@app.route('/todos-pedidos.html')
@login_required
def todos_pedidos_page():
    return send_from_directory(FRONTEND_DIR, 'todos-pedidos.html')

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

@app.route('/api-keys.html')
@login_required
def api_keys_page():
    return send_from_directory(FRONTEND_DIR, 'api-keys.html')

@app.route('/todas-consultas.html')
@login_required
def todas_consultas_page():
    return send_from_directory(FRONTEND_DIR, 'todas-consultas.html')

@app.route('/mis-consultas.html')
@login_required
def mis_consultas_page():
    return send_from_directory(FRONTEND_DIR, 'mis-consultas.html')

@app.route('/dashboard.html')
@login_required
def dashboard_page():
    return send_from_directory(FRONTEND_DIR, 'dashboard.html')

@app.route('/empresa-logo.html')
@login_required
def empresa_logo_page():
    return send_from_directory(FRONTEND_DIR, 'empresa-logo.html')

@app.route('/auditoria.html')
@login_required
def auditoria_page():
    return send_from_directory(FRONTEND_DIR, 'auditoria.html')

@app.route('/control-bd.html')
@login_required
def control_bd_page():
    return send_from_directory(FRONTEND_DIR, 'control-bd.html')

@app.route('/vista-almacen.html')
@login_required
def vista_almacen_page():
    return send_from_directory(FRONTEND_DIR, 'vista-almacen.html')

@app.route('/informe-almacen.html')
@login_required
def informe_almacen_page():
    return send_from_directory(FRONTEND_DIR, 'informe-almacen.html')

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
    ip_address = get_client_ip()
    ua_string = request.headers.get('User-Agent', '')

    # ==================== LOCKOUT CHECK (1 sola conexión reutilizada) ====================
    lockout_user_id = None
    login_conn = None
    try:
        login_conn = Database.get_connection(connection)
        cursor = login_conn.cursor()

        # Limpiar sesiones expiradas (reusar conexión)
        try:
            cursor.execute("""
                DELETE FROM user_sessions
                WHERE last_activity < DATEADD(HOUR, -24, GETDATE())
            """)
            login_conn.commit()
        except Exception:
            pass

        # Verificar lockout
        cursor.execute("""
            SELECT id, login_attempts, locked_until
            FROM users WHERE username = ?
        """, (username,))
        lockout_row = cursor.fetchone()
        if lockout_row:
            lockout_user_id = lockout_row[0]
            locked_until = lockout_row[2]

            if locked_until and locked_until > datetime.now():
                remaining_seconds = (locked_until - datetime.now()).total_seconds()
                remaining_minutes = max(1, int(remaining_seconds / 60) + 1)
                cursor.close()
                login_conn.close()
                return jsonify({
                    'success': False,
                    'message': f'Cuenta bloqueada. Intenta de nuevo en {remaining_minutes} minutos.',
                    'error': 'account_locked',
                    'remaining_minutes': remaining_minutes
                }), 423
        cursor.close()
    except Exception as e:
        logging.getLogger(__name__).debug(f"Lockout check: {e}")
    finally:
        if login_conn:
            try:
                login_conn.close()
            except Exception:
                pass

    # Verificar usuario con conexión dinámica
    user_data = verify_user(username, password, connection, empresa_id)

    if user_data:
        # ==================== LOGIN EXITOSO (1 sola conexión para todo) ====================
        post_conn = None
        session_token = None
        try:
            post_conn = Database.get_connection(connection)
            cursor = post_conn.cursor()

            # Resetear lockout
            cursor.execute("""
                UPDATE users SET login_attempts = 0, locked_until = NULL
                WHERE id = ?
            """, (user_data['id'],))

            # Eliminar sesiones anteriores del usuario
            try:
                cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_data['id'],))
            except Exception:
                pass

            # Crear nueva sesión
            try:
                import secrets as _secrets
                session_token = _secrets.token_hex(32)
                cursor.execute("""
                    INSERT INTO user_sessions (session_token, user_id, empresa_id, ip_address)
                    VALUES (?, ?, ?, ?)
                """, (session_token, user_data['id'], empresa_id, ip_address))
            except Exception:
                session_token = None

            post_conn.commit()
            cursor.close()
        except Exception as e:
            logging.getLogger(__name__).warning(f"Post-login operations: {e}")
        finally:
            if post_conn:
                try:
                    post_conn.close()
                except Exception:
                    pass

        user = User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data.get('email'),
            full_name=user_data.get('full_name'),
            rol=user_data.get('rol', 'usuario'),
            empresa_id=empresa_id,
            cliente_id=user_data.get('cliente_id'),
            company_name=user_data.get('company_name')
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

        # Guardar datos en sesión
        session['connection'] = connection
        session['empresa_id'] = empresa_id
        session['empresa_nombre'] = empresa_info.get('nombre')
        session['carrito'] = []
        session['user_id'] = user_data['id']
        if session_token:
            session['session_token'] = session_token
        session['_session_check_ts'] = time.time()

        session['db_config'] = {
            'dbserver': empresa_info.get('dbserver'),
            'dbport': empresa_info.get('dbport'),
            'dbname': empresa_info.get('dbname'),
            'dblogin': empresa_info.get('dblogin'),
            'dbpass': empresa_info.get('dbpass')
        }

        # Ejecutar migraciones de BD pendientes (solo si no se verificó ya en esta sesión del servidor)
        if migrations_need_check(connection, MIGRATIONS):
            try:
                mig_conn = Database.get_connection(connection)
                try:
                    mig_result = run_migrations(mig_conn, MIGRATIONS)
                    if mig_result['applied']:
                        logging.getLogger(__name__).info(
                            f"Migraciones BD aplicadas para empresa {connection}: {mig_result['applied']}"
                        )
                    if mig_result['failed']:
                        logging.getLogger(__name__).warning(
                            f"Migración fallida para empresa {connection}: v{mig_result['failed']['version']} - {mig_result['failed']['error']}"
                        )
                    else:
                        migrations_mark_checked(connection, MIGRATIONS)
                finally:
                    mig_conn.close()
            except Exception as e:
                logging.getLogger(__name__).warning(f"Migraciones: {e}")

        # Verificar si debe cambiar la contraseña
        debe_cambiar = user_data.get('debe_cambiar_password', False)
        if not debe_cambiar and PASSWORD_POLICY['expiration_days'] > 0:
            fecha_pwd = user_data.get('fecha_ultimo_cambio_password')
            if fecha_pwd:
                dias_desde_cambio = (datetime.now() - fecha_pwd).days
                if dias_desde_cambio > PASSWORD_POLICY['expiration_days']:
                    debe_cambiar = True

        # Generar CSRF token
        csrf_token = secrets.token_hex(32)
        session['csrf_token'] = csrf_token

        # Audit log en background (no bloquea la respuesta al usuario)
        _audit_user_id = user_data['id']
        _audit_username = user.username
        _audit_session_token = session_token
        _audit_device_info = data.get('device_info', {})
        def _log_login_audit():
            try:
                ua_parsed = parse_user_agent(ua_string)
                detalles_login = {
                    'metodo': 'password',
                    'dispositivo': {
                        'tipo': ua_parsed['device_type'],
                        'navegador': ua_parsed['browser'],
                        'sistema_operativo': ua_parsed['os'],
                        'user_agent': ua_string,
                        'pantalla': _audit_device_info.get('screen'),
                        'viewport': _audit_device_info.get('viewport'),
                        'zona_horaria': _audit_device_info.get('timezone'),
                        'idioma': _audit_device_info.get('language'),
                        'plataforma': _audit_device_info.get('platform'),
                        'cookies': _audit_device_info.get('cookiesEnabled'),
                        'tactil': _audit_device_info.get('touchscreen'),
                        'memoria_gb': _audit_device_info.get('deviceMemory'),
                        'nucleos_cpu': _audit_device_info.get('hardwareConcurrency')
                    }
                }
                ubicacion = get_location(ip_address)
                if ubicacion:
                    detalles_login['ubicacion'] = ubicacion
                AuditModel.log(
                    accion=AuditAction.LOGIN,
                    user_id=_audit_user_id,
                    username=_audit_username,
                    empresa_id=empresa_id,
                    recurso='session',
                    recurso_id=_audit_session_token,
                    ip_address=ip_address,
                    user_agent=ua_string,
                    detalles=detalles_login,
                    resultado=AuditResult.SUCCESS
                )
            except Exception:
                pass
        threading.Thread(target=_log_login_audit, daemon=True).start()

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

    # ==================== LOGIN FALLIDO (1 sola conexión para lockout + audit en background) ====================
    attempts_remaining = None
    try:
        if lockout_user_id:
            inc_conn = Database.get_connection(connection)
            inc_cursor = inc_conn.cursor()
            inc_cursor.execute("""
                UPDATE users SET login_attempts = ISNULL(login_attempts, 0) + 1
                WHERE id = ?
            """, (lockout_user_id,))
            inc_cursor.execute("SELECT login_attempts FROM users WHERE id = ?", (lockout_user_id,))
            row = inc_cursor.fetchone()
            current_attempts = row[0] if row else 0

            if current_attempts >= 5:
                inc_cursor.execute("""
                    UPDATE users SET locked_until = DATEADD(MINUTE, 15, GETDATE())
                    WHERE id = ?
                """, (lockout_user_id,))

            inc_conn.commit()
            inc_cursor.close()
            inc_conn.close()

            if current_attempts >= 5:
                # Audit de bloqueo en background
                _lock_user_id = lockout_user_id
                _lock_attempts = current_attempts
                def _log_lockout_audit():
                    try:
                        AuditModel.log(
                            accion=AuditAction.ACCOUNT_LOCKED,
                            user_id=_lock_user_id,
                            username=username,
                            empresa_id=empresa_id,
                            recurso='user',
                            recurso_id=str(_lock_user_id),
                            ip_address=ip_address,
                            user_agent=ua_string,
                            detalles={'intentos': _lock_attempts, 'duracion_minutos': 15},
                            resultado=AuditResult.BLOCKED
                        )
                    except Exception:
                        pass
                threading.Thread(target=_log_lockout_audit, daemon=True).start()
            else:
                attempts_remaining = 5 - current_attempts
    except Exception as e:
        logging.getLogger(__name__).debug(f"Lockout increment: {e}")

    # Audit de login fallido en background
    def _log_failed_audit():
        try:
            failed_detalles = {'motivo': 'credenciales_invalidas'}
            ubicacion_failed = get_location(ip_address)
            if ubicacion_failed:
                failed_detalles['ubicacion'] = ubicacion_failed
            AuditModel.log(
                accion=AuditAction.LOGIN_FAILED,
                username=username,
                empresa_id=empresa_id,
                recurso='session',
                ip_address=ip_address,
                user_agent=ua_string,
                detalles=failed_detalles,
                resultado=AuditResult.FAILED
            )
        except Exception:
            pass
    threading.Thread(target=_log_failed_audit, daemon=True).start()

    response_data = {'success': False, 'message': 'Credenciales inválidas'}
    if attempts_remaining is not None:
        response_data['attempts_remaining'] = attempts_remaining
    elif lockout_user_id:
        response_data['message'] = 'Cuenta bloqueada por demasiados intentos fallidos. Intenta de nuevo en 15 minutos.'
        response_data['error'] = 'account_locked'
        return jsonify(response_data), 423

    return jsonify(response_data), 401

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
    # Capturar datos antes de limpiar sesión
    logout_ip = get_client_ip()
    logout_ua = request.headers.get('User-Agent', '')
    logout_user_id = current_user.id
    logout_username = current_user.username
    logout_empresa_id = session.get('empresa_id')
    logout_session_token = session.get('session_token')

    # Eliminar sesion de BD
    try:
        if logout_session_token:
            UserSessionModel.delete(logout_session_token)
    except Exception:
        pass

    # Limpiar sesión
    session.pop('carrito', None)
    session.pop('session_token', None)
    session.pop('csrf_token', None)
    session.pop('_session_check_ts', None)
    logout_user()

    # Audit en background (no bloquea la respuesta)
    def _log_logout_audit():
        try:
            logout_detalles = {'metodo': 'manual'}
            ubicacion_logout = get_location(logout_ip)
            if ubicacion_logout:
                logout_detalles['ubicacion'] = ubicacion_logout
            AuditModel.log(
                accion=AuditAction.LOGOUT,
                user_id=logout_user_id,
                username=logout_username,
                empresa_id=logout_empresa_id,
                recurso='session',
                recurso_id=logout_session_token,
                ip_address=logout_ip,
                user_agent=logout_ua,
                detalles=logout_detalles,
                resultado=AuditResult.SUCCESS
            )
        except Exception:
            pass
    threading.Thread(target=_log_logout_audit, daemon=True).start()

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
    # Obtener nombre del cliente si el usuario tiene cliente_id
    cliente_id = getattr(current_user, 'cliente_id', None)
    cliente_razon = None
    if cliente_id:
        try:
            cliente = ClienteModel.get_by_codigo(cliente_id, session.get('empresa_id'))
            if cliente:
                cliente_razon = cliente.get('razon')
        except Exception:
            pass  # Si falla, simplemente no incluimos el nombre

    return jsonify({
        'username': current_user.username,
        'full_name': current_user.full_name,
        'email': current_user.email,
        'rol': current_user.rol,
        'debe_cambiar_password': getattr(current_user, 'debe_cambiar_password', False),
        'empresa_id': session.get('empresa_id'),
        'connection': session.get('connection'),
        'empresa_nombre': session.get('empresa_nombre'),
        'cliente_id': cliente_id,
        'cliente_razon': cliente_razon,
        'company_name': getattr(current_user, 'company_name', None)
    })

@app.route('/api/context-info')
@login_required
def get_context_info():
    """
    Obtener información de contexto/debug
    ---
    tags:
      - Debug
    security:
      - cookieAuth: []
    responses:
      200:
        description: Variables de contexto de la sesión
    """
    db_config = session.get('db_config', {})
    # Ocultar password por seguridad
    db_config_safe = {k: ('***' if k == 'dbpass' else v) for k, v in db_config.items()} if db_config else {}

    return jsonify({
        'user': {
            'id': getattr(current_user, 'id', None),
            'username': current_user.username,
            'full_name': current_user.full_name,
            'email': current_user.email,
            'rol': current_user.rol,
            'cliente_id': getattr(current_user, 'cliente_id', None)
        },
        'session': {
            'connection': session.get('connection'),
            'empresa_id': session.get('empresa_id'),
            'empresa_nombre': session.get('empresa_nombre'),
            'user_id': session.get('user_id'),
            'session_token': session.get('session_token', '')[:20] + '...' if session.get('session_token') else None
        },
        'db_config': db_config_safe,
        'has_db_config': bool(db_config and db_config.get('dbserver'))
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

@app.route('/api/password-policy')
def password_policy():
    """
    Obtener política de contraseñas actual
    ---
    tags:
      - Sistema
    responses:
      200:
        description: Reglas de la política de contraseñas
    """
    return jsonify(get_policy_info())

@app.route('/api/default-connection')
def get_default_connection():
    """
    Obtener connection por defecto segun el dominio
    ---
    tags:
      - Sistema
    description: |
      Busca en la tabla 'dominios' de la BD Central el connection_id
      correspondiente al dominio de la peticion. Si no encuentra,
      usa la variable de entorno DEFAULT_CONNECTION como fallback.
    responses:
      200:
        description: Connection para este dominio
        schema:
          type: object
          properties:
            connection:
              type: string
              example: "1"
            source:
              type: string
              example: "database"
    """
    # Obtener el dominio de la peticion (Host header)
    host = request.host.split(':')[0]  # Quitar puerto si existe

    # Buscar en BD Central
    connection = DominioModel.get_connection_by_domain(host)

    if connection:
        print(f"🌐 Dominio '{host}' -> connection '{connection}' (desde BD)")
        return jsonify({'connection': connection, 'source': 'database'})

    # Fallback a variable de entorno
    default_conn = os.environ.get('DEFAULT_CONNECTION', '1')
    print(f"🌐 Dominio '{host}' no encontrado, usando DEFAULT_CONNECTION='{default_conn}'")
    return jsonify({'connection': default_conn, 'source': 'environment'})

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

@app.route('/js/reset-password.js')
def serve_reset_password_js():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'reset-password.js', mimetype='application/javascript')

@app.route('/js/sidebar.js')
@login_required
def serve_sidebar_js():
    response = send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'sidebar.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/js/grid-filters.js')
@login_required
def serve_grid_filters_js():
    response = send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'grid-filters.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/js/data-grid.js')
@login_required
def serve_data_grid_js():
    response = send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'data-grid.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/js/page-common.js')
@login_required
def serve_page_common_js():
    response = send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'page-common.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/js/map-component.js')
@login_required
def serve_map_component_js():
    response = send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'map-component.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/js/datepicker.js')
@login_required
def serve_datepicker_js():
    response = send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'datepicker.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/js/notifications.js')
@login_required
def serve_notifications_js():
    response = send_from_directory(os.path.join(FRONTEND_DIR, 'js'), 'notifications.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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
    allowed_routes = ['login_page', 'login', 'register_page', 'verify_email_page', 'reset_password_page', 'serve_css', 'serve_login_js', 'serve_register_js', 'serve_reset_password_js', 'serve_i18n_js', 'serve_i18n_lang', 'logo', 'logo_png', 'logo_jobers', 'favicon', 'favicon_jobers', 'favicon_root', 'static', 'flasgger.static', 'flasgger.apispec', 'empresa_logo.get_logo', 'empresa_logo.get_favicon', 'empresa_logo.logo_exists', 'empresa_logo.get_config', 'empresa_logo.get_tema', 'empresa_logo.get_invertir', 'get_version']
    # Permitir acceso a Swagger UI
    if request.path.startswith('/apidocs') or request.path.startswith('/flasgger_static') or request.path.startswith('/apispec'):
        return None

    # Permitir rutas de registro, empresa y consultas sin autenticación
    public_api_routes = ['/api/register', '/api/verify-email', '/api/resend-verification', '/api/paises', '/api/registro-habilitado', '/api/parametros/propuestas-habilitadas', '/api/parametros/busqueda-voz-habilitada', '/api/parametros/mostrar-precios', '/api/consultas/whatsapp-config', '/api/empresa/validate', '/api/empresa/init', '/api/empresa/list', '/api/default-connection', '/api/version', '/api/password-policy', '/api/forgot-password', '/api/reset-password']
    if any(request.path.startswith(route) for route in public_api_routes):
        return None

    # Verificar autenticación por sesión o API Key
    api_key = request.headers.get('X-API-Key') or request.args.get('apikey')
    is_authenticated = current_user.is_authenticated or api_key

    # Verificar si la sesion fue eliminada de BD (matar sesion desde dashboard)
    # Optimización: solo consultar BD cada 60 segundos, no en cada request
    if current_user.is_authenticated:
        try:
            session_token = session.get('session_token')
            if session_token:
                now = time.time()
                last_check = session.get('_session_check_ts', 0)
                if now - last_check > 60:
                    if not UserSessionModel.exists(session_token):
                        session.pop('carrito', None)
                        session.pop('session_token', None)
                        session.pop('_session_check_ts', None)
                        logout_user()
                        is_authenticated = False
                    else:
                        UserSessionModel.update_activity(session_token)
                        session['_session_check_ts'] = now
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