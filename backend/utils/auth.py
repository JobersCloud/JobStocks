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

# ============================================
# ARCHIVO: utils/auth.py
# Decoradores de autenticación y autorización
# ============================================
from functools import wraps
from flask import request, jsonify, g, session
from flask_login import current_user
from models.api_key_model import ApiKeyModel

# Niveles de rol para comparación
ROLES_NIVEL = {
    'usuario': 1,
    'administrador': 2,
    'superusuario': 3
}


def api_key_or_login_required(f):
    """
    Decorador que permite autenticación por:
    1. Sesión (cookie) - para el frontend
    2. API Key (header X-API-Key) - para integraciones externas
    3. API Key (query param ?apikey=) - para pruebas en navegador
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Opción 1: Verificar si hay sesión activa (frontend)
        if current_user.is_authenticated:
            g.auth_method = 'session'
            g.auth_user = {
                'user_id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'email': current_user.email,
                'rol': getattr(current_user, 'rol', 'usuario')
            }
            return f(*args, **kwargs)

        # Opción 2: Verificar API Key en header o query param
        api_key = request.headers.get('X-API-Key') or request.args.get('apikey')
        if api_key:
            # Configurar conexión ANTES de validar (validate necesita acceso a BD)
            connection_id = request.args.get('connection')
            if connection_id and not session.get('db_config'):
                try:
                    from models.empresa_cliente_model import EmpresaClienteModel
                    empresa_info = EmpresaClienteModel.get_by_id(connection_id)
                    if empresa_info:
                        session['connection'] = connection_id
                        session['empresa_id'] = empresa_info.get('empresa_erp', '1')
                        session['empresa_nombre'] = empresa_info.get('nombre')
                        session['db_config'] = {
                            'dbserver': empresa_info.get('dbserver'),
                            'dbport': empresa_info.get('dbport'),
                            'dbname': empresa_info.get('dbname'),
                            'dblogin': empresa_info.get('dblogin'),
                            'dbpass': empresa_info.get('dbpass')
                        }
                except Exception:
                    pass

            user_data = ApiKeyModel.validate(api_key)
            if user_data:
                g.auth_method = 'api_key'
                g.auth_user = user_data

                # Si no se pasó ?connection pero la API Key tiene connection guardada
                if not session.get('db_config') and user_data.get('connection'):
                    try:
                        from models.empresa_cliente_model import EmpresaClienteModel
                        empresa_info = EmpresaClienteModel.get_by_id(user_data['connection'])
                        if empresa_info:
                            session['connection'] = user_data['connection']
                            session['empresa_id'] = empresa_info.get('empresa_erp', '1')
                            session['empresa_nombre'] = empresa_info.get('nombre')
                            session['db_config'] = {
                                'dbserver': empresa_info.get('dbserver'),
                                'dbport': empresa_info.get('dbport'),
                                'dbname': empresa_info.get('dbname'),
                                'dblogin': empresa_info.get('dblogin'),
                                'dbpass': empresa_info.get('dbpass')
                            }
                    except Exception:
                        pass

                return f(*args, **kwargs)
            else:
                return jsonify({
                    'success': False,
                    'message': 'API Key inválida o inactiva'
                }), 401

        # No autenticado
        return jsonify({
            'success': False,
            'message': 'No autenticado. Use sesión o API Key (header X-API-Key o ?apikey=)'
        }), 401

    return decorated_function


def rol_required(rol_minimo):
    """
    Decorador que requiere un rol mínimo.
    Uso: @rol_required('administrador')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar autenticación primero
            if not current_user.is_authenticated:
                return jsonify({
                    'success': False,
                    'message': 'No autenticado'
                }), 401

            # Obtener rol del usuario
            rol_usuario = getattr(current_user, 'rol', 'usuario')
            nivel_usuario = ROLES_NIVEL.get(rol_usuario, 0)
            nivel_requerido = ROLES_NIVEL.get(rol_minimo, 0)

            if nivel_usuario < nivel_requerido:
                return jsonify({
                    'success': False,
                    'message': f'Acceso denegado. Se requiere rol: {rol_minimo}'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def administrador_required(f):
    """
    Decorador que requiere rol administrador o superior.
    Uso: @administrador_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'No autenticado'
            }), 401

        rol_usuario = getattr(current_user, 'rol', 'usuario')
        if rol_usuario not in ['administrador', 'superusuario']:
            return jsonify({
                'success': False,
                'message': 'Acceso denegado. Se requiere rol de administrador'
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def superusuario_required(f):
    """
    Decorador que requiere rol superusuario.
    Uso: @superusuario_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'No autenticado'
            }), 401

        rol_usuario = getattr(current_user, 'rol', 'usuario')
        if rol_usuario != 'superusuario':
            return jsonify({
                'success': False,
                'message': 'Acceso denegado. Se requiere rol de superusuario'
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def csrf_required(f):
    """
    Decorador que verifica el CSRF token en peticiones POST/PUT/DELETE.
    El token debe enviarse en el header X-CSRF-Token.
    Solo verifica si el usuario está autenticado por sesión (no por API Key).
    Uso: @csrf_required (después de @login_required o @api_key_or_login_required)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Solo verificar en métodos que modifican datos
        if request.method in ['POST', 'PUT', 'DELETE']:
            # Si se autenticó con API Key, no verificar CSRF (integraciones externas)
            api_key = request.headers.get('X-API-Key') or request.args.get('apikey')
            if api_key:
                return f(*args, **kwargs)

            # Verificar CSRF solo para usuarios con sesión
            csrf_token = request.headers.get('X-CSRF-Token')
            session_token = session.get('csrf_token')

            if not csrf_token or not session_token or csrf_token != session_token:
                return jsonify({
                    'success': False,
                    'message': 'CSRF token inválido o ausente'
                }), 403

        return f(*args, **kwargs)
    return decorated_function


def get_clientes_comercial(control, empresa_id, connection=None):
    """
    Obtiene la lista de clientes asignados a un comercial desde view_comercial_clientes.
    Returns: lista de códigos de cliente, o lista vacía si no hay resultados o la vista no existe.
    """
    from config.database import Database
    try:
        conn = Database.get_connection(connection)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT RTRIM(cliente) FROM view_comercial_clientes
                WHERE RTRIM(control) = ? AND RTRIM(empresa) = ?
            """, (control.strip(), empresa_id.strip() if empresa_id else empresa_id))
            rows = cursor.fetchall()
            return [row[0].strip() for row in rows if row[0]]
        finally:
            cursor.close()
            conn.close()
    except Exception:
        return []
