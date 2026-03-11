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
# ARCHIVO: routes/email_config_routes.py
# ============================================
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from utils.auth import csrf_required
from models.email_config_model import EmailConfigModel
from utils.email_sender import test_smtp_connection

email_config_bp = Blueprint('email_config', __name__, url_prefix='/api/email-config')

def get_empresa_id():
    """Obtiene el empresa_id de la sesión o del request"""
    # Primero intentar obtener de la sesión
    empresa_id = session.get('empresa_id')
    if empresa_id:
        return empresa_id

    # Si no está en sesión, buscar en query params o body
    empresa_id = request.args.get('empresa_id') or request.args.get('empresa')
    if empresa_id:
        return empresa_id

    # Buscar en el body si es JSON
    if request.is_json:
        data = request.get_json(silent=True)
        if data:
            empresa_id = data.get('empresa_id') or data.get('empresa')
            if empresa_id:
                return empresa_id

    # Default
    return '1'

@email_config_bp.route('', methods=['GET'])
@login_required
def get_configs():
    """
    Obtener todas las configuraciones de email
    ---
    tags:
      - Configuración Email
    parameters:
      - name: empresa_id
        in: query
        type: string
        required: false
        description: ID de la empresa
    responses:
      200:
        description: Lista de configuraciones
    """
    try:
        empresa_id = get_empresa_id()
        configs = EmailConfigModel.get_all_configs(empresa_id)
        # Ocultar secretos en la respuesta
        for config in configs:
            config['email_password'] = '********'
        return jsonify(configs), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@email_config_bp.route('/active', methods=['GET'])
@login_required
def get_active():
    """
    Obtener configuración activa
    ---
    tags:
      - Configuración Email
    parameters:
      - name: empresa_id
        in: query
        type: string
        required: false
    responses:
      200:
        description: Configuración activa
    """
    try:
        empresa_id = get_empresa_id()
        config = EmailConfigModel.get_active_config(empresa_id)
        if config:
            config['email_password'] = '********'  # Ocultar contraseña
            config['oauth2_client_secret'] = '********' if config.get('oauth2_client_secret') else None
            return jsonify(config), 200
        else:
            return jsonify({"error": "No hay configuración activa"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@email_config_bp.route('/<int:id>', methods=['PUT'])
@login_required
@csrf_required
def update_config(id):
    """
    Actualizar configuración de email
    ---
    tags:
      - Configuración Email
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre_configuracion:
              type: string
            smtp_server:
              type: string
            smtp_port:
              type: integer
            email_from:
              type: string
            email_password:
              type: string
            email_to:
              type: string
            empresa_id:
              type: string
            auth_method:
              type: string
            oauth2_tenant_id:
              type: string
            oauth2_client_id:
              type: string
            oauth2_client_secret:
              type: string
    """
    try:
        data = request.json
        empresa_id = data.get('empresa_id') or get_empresa_id()

        EmailConfigModel.update_config(
            id=id,
            nombre_configuracion=data.get('nombre_configuracion'),
            smtp_server=data.get('smtp_server'),
            smtp_port=data.get('smtp_port'),
            email_from=data.get('email_from'),
            email_password=data.get('email_password'),  # Puede ser None
            email_to=data.get('email_to'),
            empresa_id=empresa_id,
            auth_method=data.get('auth_method'),
            oauth2_tenant_id=data.get('oauth2_tenant_id'),
            oauth2_client_id=data.get('oauth2_client_id'),
            oauth2_client_secret=data.get('oauth2_client_secret')
        )

        return jsonify({"message": "Configuración actualizada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@email_config_bp.route('', methods=['POST'])
@login_required
@csrf_required
def create_config():
    """
    Crear nueva configuración de email
    ---
    tags:
      - Configuración Email
    """
    try:
        data = request.json
        empresa_id = data.get('empresa_id') or get_empresa_id()

        config_id = EmailConfigModel.create_config(
            nombre_configuracion=data.get('nombre_configuracion', 'Nueva Configuración'),
            smtp_server=data.get('smtp_server'),
            smtp_port=data.get('smtp_port', 587),
            email_from=data.get('email_from'),
            email_password=data.get('email_password'),
            email_to=data.get('email_to'),
            empresa_id=empresa_id,
            auth_method=data.get('auth_method', 'basic'),
            oauth2_tenant_id=data.get('oauth2_tenant_id'),
            oauth2_client_id=data.get('oauth2_client_id'),
            oauth2_client_secret=data.get('oauth2_client_secret')
        )

        return jsonify({"message": "Configuración creada correctamente", "id": config_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@email_config_bp.route('/test', methods=['POST'])
@login_required
@csrf_required
def test_config():
    """
    Probar conexión SMTP con los datos proporcionados
    ---
    tags:
      - Configuración Email
    """
    try:
        data = request.json
        smtp_server = data.get('smtp_server')
        smtp_port = int(data.get('smtp_port', 587))
        email_from = data.get('email_from')
        email_password = data.get('email_password')
        empresa_id = data.get('empresa_id') or get_empresa_id()
        auth_method = data.get('auth_method', 'basic')
        config_id = data.get('config_id')

        if not all([smtp_server, smtp_port, email_from]):
            return jsonify({"success": False, "error": "Faltan datos de conexión"}), 400

        # Construir config para test
        test_email_config = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'email_from': email_from,
            'auth_method': auth_method
        }

        if auth_method == 'oauth2':
            # Usar datos del formulario primero, fallback a BD
            test_email_config['oauth2_tenant_id'] = data.get('oauth2_tenant_id')
            test_email_config['oauth2_client_id'] = data.get('oauth2_client_id')
            form_secret = data.get('oauth2_client_secret')

            if form_secret:
                test_email_config['oauth2_client_secret'] = form_secret
            elif config_id:
                # Secret no proporcionado en form - obtener de BD
                existing = EmailConfigModel.get_config_by_id(config_id, empresa_id)
                if existing:
                    test_email_config['oauth2_client_secret'] = existing.get('oauth2_client_secret')

            if not all([test_email_config.get('oauth2_tenant_id'), test_email_config.get('oauth2_client_id'), test_email_config.get('oauth2_client_secret')]):
                return jsonify({"success": False, "error": "Faltan datos OAuth2 (Tenant ID, Client ID, Client Secret)"}), 400
        else:
            # Basic auth
            if not email_password:
                return jsonify({"success": False, "error": "Faltan datos de conexión"}), 400

            # Si la contraseña es asteriscos, obtener la real de la BD
            if email_password == '********':
                if config_id:
                    existing = EmailConfigModel.get_config_by_id(config_id, empresa_id)
                    if existing:
                        email_password = existing.get('email_password')
                    else:
                        return jsonify({"success": False, "error": "No se encontró la configuración para obtener la contraseña"}), 400
                else:
                    return jsonify({"success": False, "error": "Debe introducir la contraseña para probar la conexión"}), 400

            test_email_config['email_password'] = email_password

        # Usar la utilidad central de test
        print(f"🔧 Probando conexión SMTP: {smtp_server}:{smtp_port} (auth: {auth_method})")
        result = test_smtp_connection(test_email_config)

        status_code = 200
        print(f"{'✅' if result['success'] else '❌'} Resultado test: {result}")
        return jsonify(result), status_code

    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


@email_config_bp.route('/<int:id>', methods=['DELETE'])
@login_required
@csrf_required
def delete_config(id):
    """
    Eliminar una configuración de email (no puede ser la activa)
    ---
    tags:
      - Configuración Email
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    """
    try:
        empresa_id = get_empresa_id()
        EmailConfigModel.delete_config(id, empresa_id)
        return jsonify({"message": "Configuración eliminada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@email_config_bp.route('/<int:id>/activate', methods=['POST'])
@login_required
@csrf_required
def activate_config(id):
    """
    Activar una configuración específica
    ---
    tags:
      - Configuración Email
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    """
    try:
        empresa_id = get_empresa_id()
        EmailConfigModel.set_active(id, empresa_id)
        return jsonify({"message": "Configuración activada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

