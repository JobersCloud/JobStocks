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
from models.email_config_model import EmailConfigModel

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
        # Ocultar contraseñas en la respuesta
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
            return jsonify(config), 200
        else:
            return jsonify({"error": "No hay configuración activa"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@email_config_bp.route('/<int:id>', methods=['PUT'])
@login_required
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
            empresa_id=empresa_id
        )

        return jsonify({"message": "Configuración actualizada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@email_config_bp.route('', methods=['POST'])
@login_required
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
            empresa_id=empresa_id
        )

        return jsonify({"message": "Configuración creada correctamente", "id": config_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@email_config_bp.route('/test', methods=['POST'])
@login_required
def test_config():
    """
    Probar conexión SMTP con los datos proporcionados
    ---
    tags:
      - Configuración Email
    """
    try:
        import smtplib
        from email.mime.text import MIMEText

        data = request.json
        smtp_server = data.get('smtp_server')
        smtp_port = int(data.get('smtp_port', 587))
        email_from = data.get('email_from')
        email_password = data.get('email_password')
        empresa_id = data.get('empresa_id') or get_empresa_id()

        if not all([smtp_server, smtp_port, email_from, email_password]):
            return jsonify({"success": False, "error": "Faltan datos de conexión"}), 400

        # Si la contraseña es asteriscos, obtener la real de la BD
        if email_password == '********':
            config_id = data.get('config_id')
            if config_id:
                existing = EmailConfigModel.get_config_by_id(config_id, empresa_id)
                if existing:
                    email_password = existing.get('email_password')
                else:
                    return jsonify({"success": False, "error": "No se encontró la configuración para obtener la contraseña"}), 400
            else:
                return jsonify({"success": False, "error": "Debe introducir la contraseña para probar la conexión"}), 400

        # Intentar conexión SMTP
        print(f"🔧 Probando conexión SMTP: {smtp_server}:{smtp_port}")

        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.set_debuglevel(0)
        server.starttls()
        server.login(email_from, email_password)
        server.quit()

        print(f"✅ Conexión SMTP exitosa")
        return jsonify({"success": True, "message": "Conexión SMTP exitosa"}), 200

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Error de autenticación SMTP: {str(e)}")
        return jsonify({"success": False, "error": "Error de autenticación. Verifica el email y contraseña."}), 200
    except smtplib.SMTPConnectError as e:
        print(f"❌ Error de conexión SMTP: {str(e)}")
        return jsonify({"success": False, "error": f"No se pudo conectar al servidor SMTP: {smtp_server}:{smtp_port}"}), 200
    except Exception as e:
        print(f"❌ Error SMTP: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 200


@email_config_bp.route('/<int:id>/activate', methods=['POST'])
@login_required
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
