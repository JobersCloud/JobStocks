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
# ARCHIVO: routes/usuario_routes.py
# Endpoints para gestión de usuarios (admin)
# ============================================
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from utils.auth import csrf_required
from utils.auth import administrador_required, superusuario_required
from models.audit_model import AuditModel, AuditAction, AuditResult
from database.users_db import (
    get_all_users_by_empresa, get_user_by_id,
    get_user_by_id_and_empresa, update_user, update_user_full,
    update_user_rol, deactivate_user, activate_user, create_user_admin,
    change_password, add_user_to_empresa, get_user_empresas, set_email_verified
)
from models.email_config_model import EmailConfigModel
import smtplib
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


def get_base_url():
    """
    Obtiene la URL base correcta detectando automáticamente el protocolo.
    Prioridad:
    1. Variable de entorno BASE_URL (si está configurada)
    2. Headers de proxy X-Forwarded-Proto/Host
    3. request.scheme/host como fallback
    """
    base_url_env = os.environ.get('BASE_URL')
    if base_url_env:
        return base_url_env.rstrip('/')

    proto = request.headers.get('X-Forwarded-Proto', request.scheme)
    host = request.headers.get('X-Forwarded-Host', request.host)
    return f"{proto}://{host}"


def get_client_ip():
    """Obtener IP real del cliente, considerando proxies"""
    headers_to_check = [
        'X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP',
        'True-Client-IP', 'X-Client-IP'
    ]
    for header in headers_to_check:
        ip = request.headers.get(header)
        if ip:
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            return ip
    return request.remote_addr


usuario_bp = Blueprint('usuario', __name__, url_prefix='/api/usuarios')


@usuario_bp.route('', methods=['GET'])
@login_required
@administrador_required
def listar_usuarios():
    """
    Listar usuarios por empresa (solo administradores).
    Usa connection y empresa_id de la sesión.
    ---
    tags:
      - Usuarios
    security:
      - cookieAuth: []
    responses:
      200:
        description: Lista de usuarios
      401:
        description: No autenticado
      403:
        description: No autorizado (requiere rol administrador)
    """
    # Obtener empresa_id de sesión para filtrar
    empresa_id = session.get('empresa_id', '1')
    connection = session.get('connection')

    print(f"[DEBUG] listar_usuarios - connection: {connection}, empresa_id: {empresa_id}", flush=True)

    try:
        usuarios = get_all_users_by_empresa(empresa_id, connection)
        print(f"[DEBUG] listar_usuarios - Total usuarios: {len(usuarios)}")
        return jsonify({
            'success': True,
            'total': len(usuarios),
            'usuarios': usuarios
        }), 200
    except Exception as e:
        import traceback
        print(f"[ERROR] listar_usuarios - Error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@usuario_bp.route('', methods=['POST'])
@login_required
@csrf_required
@administrador_required
def crear_usuario():
    """
    Crear un nuevo usuario (solo administradores)
    ---
    tags:
      - Usuarios
    security:
      - cookieAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
            - empresa_id
          properties:
            username:
              type: string
            password:
              type: string
            email:
              type: string
            full_name:
              type: string
            pais:
              type: string
            cliente_id:
              type: string
            rol:
              type: string
              enum: [usuario, administrador, superusuario]
              default: usuario
            empresa_id:
              type: string
    responses:
      201:
        description: Usuario creado
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            user_id:
              type: integer
      400:
        description: Datos inválidos o usuario ya existe
      401:
        description: No autenticado
      403:
        description: No autorizado
    """
    data = request.json

    if not data:
        return jsonify({
            'success': False,
            'error': 'No se proporcionaron datos'
        }), 400

    # Validar campos requeridos
    required_fields = ['username', 'password', 'empresa_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'success': False,
                'error': f'Campo "{field}" es requerido'
            }), 400

    # Validar longitud de contraseña
    if len(data['password']) < 6:
        return jsonify({
            'success': False,
            'error': 'La contraseña debe tener al menos 6 caracteres'
        }), 400

    # Validar que solo superusuario puede crear admin/superusuario
    if data.get('rol') in ['administrador', 'superusuario']:
        if not current_user.is_superusuario():
            return jsonify({
                'success': False,
                'error': 'Solo un superusuario puede crear usuarios con rol administrador o superusuario'
            }), 403

    # Si se solicita enviar email, verificar que el usuario tenga email
    enviar_email = data.get('enviar_email', False)
    if enviar_email and not data.get('email'):
        return jsonify({
            'success': False,
            'error': 'Para enviar email de bienvenida, el usuario debe tener un email'
        }), 400

    # Si se envía email, marcar que debe cambiar contraseña
    if enviar_email:
        data['debe_cambiar_password'] = True

    # Preparar datos para crear usuario
    connection = session.get('connection')
    data['empresa_erp'] = data.get('empresa_id')  # Mapear empresa_id a empresa_erp

    try:
        user_id = create_user_admin(data, connection)

        # Registrar audit log de usuario creado
        try:
            AuditModel.log(
                accion=AuditAction.USER_CREATE,
                user_id=current_user.id,
                username=current_user.username,
                empresa_id=session.get('empresa_id'),
                recurso='user',
                recurso_id=str(user_id),
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent'),
                detalles={'nuevo_usuario': data['username'], 'rol': data.get('rol', 'usuario')},
                resultado=AuditResult.SUCCESS
            )
        except Exception as e:
            print(f"Warning: No se pudo registrar audit log: {e}")

        email_enviado = False
        email_error = None

        # Enviar email de bienvenida si se solicitó
        if enviar_email:
            try:
                enviar_email_bienvenida(
                    email=data['email'],
                    username=data['username'],
                    password=data['password'],
                    full_name=data.get('full_name', ''),
                    empresa_id=data['empresa_id']
                )
                email_enviado = True
            except Exception as e:
                email_error = str(e)
                print(f"❌ Error al enviar email de bienvenida: {e}")

        response = {
            'success': True,
            'message': 'Usuario creado correctamente',
            'user_id': user_id
        }

        if enviar_email:
            response['email_enviado'] = email_enviado
            if email_error:
                response['email_error'] = email_error

        return jsonify(response), 201
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def enviar_email_bienvenida(email, username, password, full_name, empresa_id):
    """Enviar email de bienvenida con credenciales al nuevo usuario"""
    # Obtener configuración de email activa
    email_config = EmailConfigModel.get_active_config(empresa_id)
    if not email_config:
        raise Exception("No hay configuración de email activa")

    # Crear mensaje
    msg = MIMEMultipart()
    msg['From'] = email_config['email_from']
    msg['To'] = email
    msg['Subject'] = "Bienvenido - Tu cuenta ha sido creada"
    msg['Date'] = formatdate(localtime=True)

    # Cuerpo del email HTML
    nombre = full_name if full_name else username

    # Construir URL de login con empresa
    login_url = f"{get_base_url()}/login?empresa={empresa_id}"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 40px 20px;">
                    <table role="presentation" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.1);">
                        <!-- Header con gradiente -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #FF4338 0%, #C62828 100%); padding: 40px 30px; text-align: center;">
                                <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>
                                <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">
                                    ¡Bienvenido al equipo!
                                </h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 12px 0 0 0; font-size: 16px;">
                                    Tu cuenta ha sido creada exitosamente
                                </p>
                            </td>
                        </tr>

                        <!-- Contenido principal -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <p style="font-size: 18px; color: #333; margin: 0 0 24px 0;">
                                    Hola <strong style="color: #FF4338;">{nombre}</strong>,
                                </p>
                                <p style="font-size: 15px; color: #555; margin: 0 0 32px 0; line-height: 1.7;">
                                    Se ha creado una cuenta para ti en el <strong>Sistema de Gestión de Stocks</strong>.
                                    A continuación encontrarás tus credenciales de acceso.
                                </p>

                                <!-- Tarjeta de credenciales -->
                                <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
                                    <tr>
                                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 24px;">
                                            <p style="color: rgba(255,255,255,0.8); font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 16px 0;">
                                                🔐 Credenciales de acceso
                                            </p>
                                            <table role="presentation" style="width: 100%;">
                                                <tr>
                                                    <td style="padding: 12px 16px; background: rgba(255,255,255,0.15); border-radius: 8px; margin-bottom: 8px;">
                                                        <span style="color: rgba(255,255,255,0.7); font-size: 12px; display: block;">Usuario</span>
                                                        <span style="color: white; font-size: 18px; font-weight: 600;">{username}</span>
                                                    </td>
                                                </tr>
                                                <tr><td style="height: 8px;"></td></tr>
                                                <tr>
                                                    <td style="padding: 12px 16px; background: rgba(255,255,255,0.15); border-radius: 8px;">
                                                        <span style="color: rgba(255,255,255,0.7); font-size: 12px; display: block;">Contraseña temporal</span>
                                                        <span style="color: white; font-size: 18px; font-weight: 600; font-family: monospace;">{password}</span>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Aviso importante -->
                                <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 32px;">
                                    <tr>
                                        <td style="background: #FFF8E1; border-radius: 12px; padding: 20px; border-left: 4px solid #FFB300;">
                                            <table role="presentation">
                                                <tr>
                                                    <td style="vertical-align: top; padding-right: 12px;">
                                                        <span style="font-size: 24px;">⚠️</span>
                                                    </td>
                                                    <td>
                                                        <p style="margin: 0; color: #F57C00; font-weight: 600; font-size: 14px;">
                                                            Cambio de contraseña requerido
                                                        </p>
                                                        <p style="margin: 6px 0 0 0; color: #795548; font-size: 13px; line-height: 1.5;">
                                                            Por seguridad, deberás cambiar tu contraseña la primera vez que inicies sesión.
                                                        </p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Botón de acceso -->
                                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="text-align: center; padding: 8px 0 32px 0;">
                                            <a href="{login_url}" style="display: inline-block; background-color: #FF4338; color: white !important; text-decoration: none; padding: 16px 48px; border-radius: 50px; font-size: 16px; font-weight: 600;">
                                                🚀 Acceder al Sistema
                                            </a>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Pasos -->
                                <table role="presentation" style="width: 100%; border-collapse: collapse; background: #F8F9FA; border-radius: 12px; padding: 20px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <p style="margin: 0 0 16px 0; color: #333; font-weight: 600; font-size: 14px;">
                                                📋 Pasos para comenzar:
                                            </p>
                                            <table role="presentation" style="width: 100%;">
                                                <tr>
                                                    <td style="padding: 8px 0; color: #555; font-size: 14px;">
                                                        <span style="display: inline-block; width: 24px; height: 24px; background: #FF4338; color: white; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; font-weight: bold; margin-right: 12px;">1</span>
                                                        Haz clic en "Acceder al Sistema"
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 8px 0; color: #555; font-size: 14px;">
                                                        <span style="display: inline-block; width: 24px; height: 24px; background: #FF4338; color: white; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; font-weight: bold; margin-right: 12px;">2</span>
                                                        Ingresa tus credenciales
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 8px 0; color: #555; font-size: 14px;">
                                                        <span style="display: inline-block; width: 24px; height: 24px; background: #FF4338; color: white; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; font-weight: bold; margin-right: 12px;">3</span>
                                                        Cambia tu contraseña por una segura
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 8px 0; color: #555; font-size: 14px;">
                                                        <span style="display: inline-block; width: 24px; height: 24px; background: #4CAF50; color: white; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; font-weight: bold; margin-right: 12px;">✓</span>
                                                        ¡Listo! Ya puedes usar el sistema
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background: #F8F9FA; padding: 24px 30px; text-align: center; border-top: 1px solid #E0E0E0;">
                                <p style="margin: 0 0 8px 0; color: #999; font-size: 12px;">
                                    Este es un mensaje automático, por favor no respondas a este email.
                                </p>
                                <p style="margin: 0; color: #BBB; font-size: 11px;">
                                    © {datetime.now().year} Sistema de Gestión de Stocks
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    # Enviar email
    if email_config['smtp_port'] == 465:
        server = smtplib.SMTP_SSL(email_config['smtp_server'], email_config['smtp_port'])
    else:
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()

    server.login(email_config['email_from'], email_config['email_password'])
    server.send_message(msg)
    server.quit()

    print(f"✅ Email de bienvenida enviado a {email}")


@usuario_bp.route('/<int:user_id>', methods=['GET'])
@login_required
@administrador_required
def obtener_usuario(user_id):
    """
    Obtener un usuario por ID (solo administradores).
    Usa empresa de sesión.
    ---
    tags:
      - Usuarios
    security:
      - cookieAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Datos del usuario
      404:
        description: Usuario no encontrado
    """
    connection = session.get('connection')
    empresa_id = session.get('empresa_id', '1')

    try:
        usuario = get_user_by_id_and_empresa(user_id, connection, empresa_id)
        if not usuario:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado'
            }), 404

        return jsonify({
            'success': True,
            'usuario': usuario
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@usuario_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
@csrf_required
@administrador_required
def actualizar_usuario(user_id):
    """
    Actualizar datos de un usuario (solo administradores).
    Usa empresa de sesión.
    ---
    tags:
      - Usuarios
    security:
      - cookieAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Usuario actualizado
      400:
        description: Datos inválidos
      404:
        description: Usuario no encontrado
    """
    data = request.json

    if not data:
        return jsonify({
            'success': False,
            'error': 'No se proporcionaron datos para actualizar'
        }), 400

    connection = session.get('connection')
    empresa_id = session.get('empresa_id', '1')

    # Validar que solo superusuario puede cambiar rol a admin/superusuario
    if 'rol' in data and data['rol'] in ['administrador', 'superusuario']:
        if not current_user.is_superusuario():
            return jsonify({
                'success': False,
                'error': 'Solo un superusuario puede asignar roles de administrador o superusuario'
            }), 403

    try:
        actualizado = update_user_full(user_id, data, connection, empresa_id)
        if not actualizado:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado o sin cambios'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Usuario actualizado correctamente'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@usuario_bp.route('/<int:user_id>/rol', methods=['PUT'])
@login_required
@csrf_required
@superusuario_required
def cambiar_rol(user_id):
    """
    Cambiar el rol de un usuario (solo superusuarios)
    ---
    tags:
      - Usuarios
    security:
      - cookieAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID del usuario
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - rol
          properties:
            rol:
              type: string
              enum: [usuario, administrador, superusuario]
    responses:
      200:
        description: Rol actualizado
      400:
        description: Rol inválido
      404:
        description: Usuario no encontrado
      401:
        description: No autenticado
      403:
        description: No autorizado (requiere rol superusuario)
    """
    data = request.json

    if not data or 'rol' not in data:
        return jsonify({
            'success': False,
            'error': 'Campo "rol" es requerido'
        }), 400

    # Evitar que el superusuario se quite su propio rol
    if user_id == current_user.id and data['rol'] != 'superusuario':
        return jsonify({
            'success': False,
            'error': 'No puedes cambiar tu propio rol de superusuario'
        }), 400

    try:
        connection = session.get('connection')
        empresa_id = session.get('empresa_id', '1')

        actualizado = update_user_rol(user_id, data['rol'], connection, empresa_id)
        if not actualizado:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado en esta empresa'
            }), 404

        # Registrar audit log
        try:
            AuditModel.log(
                accion=AuditAction.USER_ROLE_CHANGE,
                user_id=current_user.id,
                username=current_user.username,
                empresa_id=empresa_id,
                recurso='user',
                recurso_id=str(user_id),
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent'),
                detalles={'nuevo_rol': data['rol']},
                resultado=AuditResult.SUCCESS
            )
        except Exception as e:
            print(f"Warning: No se pudo registrar audit log: {e}")

        return jsonify({
            'success': True,
            'message': f'Rol actualizado a "{data["rol"]}"'
        }), 200
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@usuario_bp.route('/<int:user_id>/desactivar', methods=['POST'])
@login_required
@csrf_required
@administrador_required
def desactivar_usuario(user_id):
    """
    Desactivar un usuario (solo administradores)
    ---
    tags:
      - Usuarios
    security:
      - cookieAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID del usuario
    responses:
      200:
        description: Usuario desactivado
      400:
        description: No se puede desactivar al propio usuario
      404:
        description: Usuario no encontrado
      401:
        description: No autenticado
      403:
        description: No autorizado
    """
    # Evitar que el usuario se desactive a sí mismo
    if user_id == current_user.id:
        return jsonify({
            'success': False,
            'error': 'No puedes desactivarte a ti mismo'
        }), 400

    try:
        connection = session.get('connection')
        desactivado = deactivate_user(user_id, connection)
        if not desactivado:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado'
            }), 404

        # Registrar audit log
        try:
            AuditModel.log(
                accion=AuditAction.USER_DEACTIVATE,
                user_id=current_user.id,
                username=current_user.username,
                empresa_id=session.get('empresa_id'),
                recurso='user',
                recurso_id=str(user_id),
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent'),
                resultado=AuditResult.SUCCESS
            )
        except Exception as e:
            print(f"Warning: No se pudo registrar audit log: {e}")

        return jsonify({
            'success': True,
            'message': 'Usuario desactivado correctamente'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@usuario_bp.route('/<int:user_id>/activar', methods=['POST'])
@login_required
@csrf_required
@administrador_required
def activar_usuario(user_id):
    """
    Activar un usuario (solo administradores)
    ---
    tags:
      - Usuarios
    security:
      - cookieAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID del usuario
    responses:
      200:
        description: Usuario activado
      404:
        description: Usuario no encontrado
      401:
        description: No autenticado
      403:
        description: No autorizado
    """
    try:
        connection = session.get('connection')
        activado = activate_user(user_id, connection)
        if not activado:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado'
            }), 404

        # Registrar audit log
        try:
            AuditModel.log(
                accion=AuditAction.USER_ACTIVATE,
                user_id=current_user.id,
                username=current_user.username,
                empresa_id=session.get('empresa_id'),
                recurso='user',
                recurso_id=str(user_id),
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent'),
                resultado=AuditResult.SUCCESS
            )
        except Exception as e:
            print(f"Warning: No se pudo registrar audit log: {e}")

        return jsonify({
            'success': True,
            'message': 'Usuario activado correctamente'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@usuario_bp.route('/<int:user_id>/verificacion-email', methods=['POST'])
@login_required
@csrf_required
@administrador_required
def cambiar_verificacion_email(user_id):
    """
    Cambiar estado de verificación de email de un usuario (solo administradores)
    ---
    tags:
      - Usuarios
    security:
      - cookieAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID del usuario
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - verificado
          properties:
            verificado:
              type: boolean
              description: true para marcar como verificado, false para no verificado
    responses:
      200:
        description: Estado de verificación actualizado
      400:
        description: Parámetro inválido
      404:
        description: Usuario no encontrado
      401:
        description: No autenticado
      403:
        description: No autorizado
    """
    data = request.json

    if not data or 'verificado' not in data:
        return jsonify({
            'success': False,
            'error': 'Campo "verificado" es requerido'
        }), 400

    try:
        connection = session.get('connection')
        actualizado = set_email_verified(user_id, data['verificado'], connection)
        if not actualizado:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado'
            }), 404

        estado = 'verificado' if data['verificado'] else 'no verificado'
        return jsonify({
            'success': True,
            'message': f'Email marcado como {estado}'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@usuario_bp.route('/cambiar-password', methods=['POST'])
@login_required
@csrf_required
def cambiar_password():
    """
    Cambiar contraseña del usuario actual (obligatorio si debe_cambiar_password=True)
    ---
    tags:
      - Usuarios
    security:
      - cookieAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - new_password
          properties:
            new_password:
              type: string
              description: Nueva contraseña (mínimo 6 caracteres)
    responses:
      200:
        description: Contraseña cambiada correctamente
      400:
        description: Contraseña inválida
      401:
        description: No autenticado
    """
    data = request.json

    if not data or not data.get('new_password'):
        return jsonify({
            'success': False,
            'error': 'La nueva contraseña es requerida'
        }), 400

    new_password = data['new_password']

    if len(new_password) < 6:
        return jsonify({
            'success': False,
            'error': 'La contraseña debe tener al menos 6 caracteres'
        }), 400

    # Si se envía current_password, verificar antes de cambiar (cambio voluntario)
    if data.get('current_password'):
        from werkzeug.security import check_password_hash
        connection = session.get('connection')
        conn = None
        try:
            from config.database import Database
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (current_user.id,))
            row = cursor.fetchone()
            if not row or not check_password_hash(row[0], data['current_password']):
                return jsonify({
                    'success': False,
                    'error': 'La contraseña actual es incorrecta'
                }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Error al verificar la contraseña actual'
            }), 500
        finally:
            if conn:
                conn.close()

    try:
        connection = session.get('connection')
        result = change_password(current_user.id, new_password, connection)
        if result:
            # Registrar audit log
            try:
                AuditModel.log(
                    accion=AuditAction.PASSWORD_CHANGE,
                    user_id=current_user.id,
                    username=current_user.username,
                    empresa_id=session.get('empresa_id'),
                    recurso='user',
                    recurso_id=str(current_user.id),
                    ip_address=get_client_ip(),
                    user_agent=request.headers.get('User-Agent'),
                    resultado=AuditResult.SUCCESS
                )
            except Exception as e:
                print(f"Warning: No se pudo registrar audit log: {e}")

            return jsonify({
                'success': True,
                'message': 'Contraseña cambiada correctamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo cambiar la contraseña'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@usuario_bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
@csrf_required
@superusuario_required
def eliminar_usuario_cascada(user_id):
    """
    Eliminar un usuario y todas sus dependencias en cascada (solo superusuarios)
    Elimina: propuestas (y lineas), consultas, api_keys, user_sessions, audit_log
    ---
    tags:
      - Usuarios
    security:
      - cookieAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID del usuario a eliminar
    responses:
      200:
        description: Usuario eliminado correctamente
      400:
        description: No se puede eliminar al propio usuario
      404:
        description: Usuario no encontrado
      401:
        description: No autenticado
      403:
        description: No autorizado (requiere rol superusuario)
    """
    from config.database import Database

    # Evitar que el usuario se elimine a sí mismo
    if user_id == current_user.id:
        return jsonify({
            'success': False,
            'error': 'No puedes eliminarte a ti mismo'
        }), 400

    try:
        connection = session.get('connection')
        empresa_id = session.get('empresa_id', '1')

        # Verificar que el usuario existe
        usuario = get_user_by_id_and_empresa(user_id, connection, empresa_id)
        if not usuario:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado en esta empresa'
            }), 404

        username_eliminado = usuario.get('username', 'desconocido')

        conn = Database.get_connection(connection)
        cursor = conn.cursor()

        eliminados = {
            'propuestas_lineas': 0,
            'propuestas': 0,
            'consultas': 0,
            'api_keys': 0,
            'user_sessions': 0,
            'audit_log': 0
        }

        try:
            # 1. Eliminar líneas de propuestas (las propuestas del usuario)
            cursor.execute("""
                DELETE FROM propuestas_lineas
                WHERE propuesta_id IN (SELECT id FROM propuestas WHERE user_id = ?)
            """, (user_id,))
            eliminados['propuestas_lineas'] = cursor.rowcount

            # 2. Eliminar propuestas del usuario
            cursor.execute("DELETE FROM propuestas WHERE user_id = ?", (user_id,))
            eliminados['propuestas'] = cursor.rowcount

            # 3. Eliminar consultas del usuario
            cursor.execute("DELETE FROM consultas WHERE user_id = ?", (user_id,))
            eliminados['consultas'] = cursor.rowcount

            # 4. Eliminar API keys del usuario
            cursor.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))
            eliminados['api_keys'] = cursor.rowcount

            # 5. Eliminar sesiones activas del usuario
            cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
            eliminados['user_sessions'] = cursor.rowcount

            # 6. Eliminar registros de auditoría del usuario
            cursor.execute("DELETE FROM audit_log WHERE user_id = ?", (user_id,))
            eliminados['audit_log'] = cursor.rowcount

            # 7. Finalmente, eliminar el usuario
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

            conn.commit()

            # Registrar audit log de la eliminación (con el usuario actual, no el eliminado)
            try:
                AuditModel.log(
                    accion=AuditAction.USER_DELETE,
                    user_id=current_user.id,
                    username=current_user.username,
                    empresa_id=empresa_id,
                    recurso='user',
                    recurso_id=str(user_id),
                    ip_address=get_client_ip(),
                    user_agent=request.headers.get('User-Agent'),
                    detalles={
                        'usuario_eliminado': username_eliminado,
                        'registros_eliminados': eliminados
                    },
                    resultado=AuditResult.SUCCESS
                )
            except Exception as e:
                print(f"Warning: No se pudo registrar audit log: {e}")

            return jsonify({
                'success': True,
                'message': f'Usuario "{username_eliminado}" eliminado correctamente junto con todas sus dependencias',
                'eliminados': eliminados
            }), 200

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        import traceback
        print(f"[ERROR] eliminar_usuario_cascada: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
