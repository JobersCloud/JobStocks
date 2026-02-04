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
# ARCHIVO: routes/register_routes.py
# ============================================
from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash
from models.parametros_model import ParametrosModel
from models.email_config_model import EmailConfigModel
from models.audit_model import AuditModel, AuditAction, AuditResult
from config.database import Database
from datetime import datetime, timedelta
import secrets
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

register_bp = Blueprint('register', __name__, url_prefix='/api')

# Cargar lista de países
PAISES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'paises.json')
with open(PAISES_FILE, 'r', encoding='utf-8') as f:
    PAISES = json.load(f)

def get_connection():
    """Obtiene el connection del request o de la sesión (ID de conexión)"""
    # 1. Buscar en query params
    connection = (request.args.get('connection') or
                  request.args.get('empresa_cli_id') or
                  request.args.get('empresa_id') or
                  request.args.get('empresa'))
    if connection:
        return connection

    # 2. Buscar en el body si es JSON
    if request.is_json:
        data = request.get_json(silent=True)
        if data:
            connection = (data.get('connection') or
                         data.get('empresa_cli_id') or
                         data.get('empresa_id') or
                         data.get('empresa'))
            if connection:
                return connection

    # 3. Buscar en la sesión (si el usuario está logueado)
    if 'connection' in session:
        return session['connection']

    # Sin connection definido - devolver None (el llamador debe manejarlo)
    return None

def get_empresa_id_from_connection(connection):
    """Obtiene el empresa_id desde el connection"""
    from models.empresa_cliente_model import EmpresaClienteModel
    empresa = EmpresaClienteModel.get_by_id(connection)
    if empresa:
        return empresa.get('empresa_erp', '1')
    return '1'


def get_empresa_id():
    """Obtiene el empresa_id (para uso en parámetros y registro)"""
    # Primero intentar obtener empresa_id directamente del body o query
    empresa_id = request.args.get('empresa_id') or request.args.get('empresa')
    if empresa_id:
        return empresa_id

    if request.is_json:
        data = request.get_json(silent=True)
        if data:
            empresa_id = data.get('empresa_id') or data.get('empresa')
            if empresa_id:
                return empresa_id

    # Si no hay empresa_id directo, usar connection y convertir
    connection = get_connection()
    return get_empresa_id_from_connection(connection)

@register_bp.route('/registro-habilitado', methods=['GET'])
def registro_habilitado():
    """
    Verificar si el registro está habilitado
    ---
    tags:
      - Registro
    responses:
      200:
        description: Estado del registro
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    habilitado = ParametrosModel.permitir_registro(empresa_id, connection)
    return jsonify({'habilitado': habilitado}), 200

@register_bp.route('/paises', methods=['GET'])
def get_paises():
    """
    Obtener lista de países
    ---
    tags:
      - Registro
    responses:
      200:
        description: Lista de países
        schema:
          type: array
          items:
            type: object
            properties:
              nombre:
                type: string
              alfa2:
                type: string
                description: Código ISO 3166-1 alfa-2
              alfa3:
                type: string
                description: Código ISO 3166-1 alfa-3
    """
    return jsonify(PAISES), 200

@register_bp.route('/register', methods=['POST'])
def register():
    """
    Registrar nuevo usuario
    ---
    tags:
      - Registro
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
            - email
            - pais
            - full_name
          properties:
            username:
              type: string
              example: usuario1
            password:
              type: string
              example: mipassword123
            email:
              type: string
              example: usuario@email.com
            pais:
              type: string
              example: ES
            full_name:
              type: string
              example: Juan García
    responses:
      201:
        description: Usuario registrado, pendiente verificación
      400:
        description: Error en los datos
      403:
        description: Registro no permitido
      409:
        description: Usuario o email ya existe
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)

    # Verificar si el registro está habilitado
    if not ParametrosModel.permitir_registro(empresa_id, connection):
        return jsonify({
            'success': False,
            'message': 'El registro de usuarios no está habilitado'
        }), 403

    data = request.get_json()

    # Validar campos requeridos
    required = ['username', 'password', 'email', 'pais', 'full_name']
    for field in required:
        if not data.get(field):
            return jsonify({
                'success': False,
                'message': f'El campo {field} es requerido'
            }), 400

    username = data['username'].strip().lower()
    password = data['password']
    email = data['email'].strip().lower()
    pais = data['pais']
    full_name = data['full_name'].strip()
    company_name = data.get('company_name', '').strip()  # Campo opcional
    cif_nif = data.get('cif_nif', '').strip()  # Campo opcional

    # Validar longitud de password
    if len(password) < 6:
        return jsonify({
            'success': False,
            'message': 'La contraseña debe tener al menos 6 caracteres'
        }), 400

    # Validar email
    if '@' not in email or '.' not in email:
        return jsonify({
            'success': False,
            'message': 'Email inválido'
        }), 400

    # Validar país (usando código alfa2)
    if not any(p['alfa2'] == pais for p in PAISES):
        return jsonify({
            'success': False,
            'message': 'País inválido'
        }), 400

    conn = Database.get_connection(connection)
    cursor = conn.cursor()

    try:
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'El nombre de usuario ya está en uso'
            }), 409

        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'El email ya está registrado'
            }), 409

        # Generar token de verificación
        token = secrets.token_urlsafe(32)
        token_expiracion = datetime.now() + timedelta(hours=24)

        # Crear usuario (inactivo hasta verificar email)
        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, full_name, company_name, cif_nif, pais, active, email_verificado, token_verificacion, token_expiracion)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
        """, (username, password_hash, email, full_name, company_name, cif_nif, pais, token, token_expiracion))

        user_id = cursor.fetchone()[0]

        # Crear relación con la empresa
        cursor.execute("""
            INSERT INTO users_empresas (user_id, empresa_id, cliente_id, rol)
            VALUES (?, ?, NULL, 'usuario')
        """, (user_id, empresa_id))

        conn.commit()
        print(f"✅ Usuario {username} (id: {user_id}) registrado y asignado a empresa {empresa_id}")

        # Log de auditoría - registro exitoso
        AuditModel.log(
            accion=AuditAction.USER_REGISTER,
            user_id=user_id,
            username=username,
            empresa_id=empresa_id,
            connection_id=connection,
            recurso='user',
            recurso_id=str(user_id),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalles={'email': email, 'full_name': full_name, 'pais': pais},
            resultado=AuditResult.SUCCESS
        )

        # Enviar email de verificación
        try:
            enviar_email_verificacion(email, full_name, token, empresa_id, connection)
        except Exception as e:
            print(f"Error al enviar email de verificación: {e}")
            # No fallar el registro si el email no se envía
            return jsonify({
                'success': True,
                'message': 'Usuario registrado. Error al enviar email de verificación, contacta al administrador.',
                'email_enviado': False
            }), 201

        return jsonify({
            'success': True,
            'message': 'Usuario registrado. Revisa tu email para verificar tu cuenta.',
            'email_enviado': True
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al registrar usuario: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@register_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """
    Reenviar email de verificación
    ---
    tags:
      - Registro
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              example: usuario@email.com
    responses:
      200:
        description: Email reenviado
      400:
        description: Email no encontrado o ya verificado
      429:
        description: Demasiados intentos
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    data = request.get_json()
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({
            'success': False,
            'message': 'Email requerido'
        }), 400

    conn = Database.get_connection(connection)
    cursor = conn.cursor()

    try:
        # Buscar usuario con email no verificado
        cursor.execute("""
            SELECT id, full_name, token_verificacion, token_expiracion FROM users
            WHERE email = ? AND email_verificado = 0
        """, (email,))

        row = cursor.fetchone()

        if not row:
            return jsonify({
                'success': False,
                'message': 'No se encontró una cuenta pendiente de verificación con ese email'
            }), 400

        user_id, full_name, old_token, old_expiracion = row

        # Generar nuevo token (por seguridad)
        new_token = secrets.token_urlsafe(32)
        new_expiracion = datetime.now() + timedelta(hours=24)

        # Actualizar token
        cursor.execute("""
            UPDATE users
            SET token_verificacion = ?, token_expiracion = ?
            WHERE id = ?
        """, (new_token, new_expiracion, user_id))

        conn.commit()

        # Reenviar email
        try:
            enviar_email_verificacion(email, full_name, new_token, empresa_id, connection)

            # Log de auditoría - reenvío exitoso
            AuditModel.log(
                accion=AuditAction.USER_RESEND_VERIFICATION,
                user_id=user_id,
                username=email,
                empresa_id=empresa_id,
                connection_id=connection,
                recurso='user',
                recurso_id=str(user_id),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                detalles={'email': email, 'full_name': full_name},
                resultado=AuditResult.SUCCESS
            )

            return jsonify({
                'success': True,
                'message': 'Email de verificación reenviado. Revisa tu bandeja de entrada.'
            }), 200
        except Exception as e:
            error_msg = str(e)
            print(f"Error al reenviar email: {error_msg}")
            return jsonify({
                'success': False,
                'message': f'Error al enviar el email: {error_msg}'
            }), 500

    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al reenviar verificación: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@register_bp.route('/verify-email', methods=['GET'])
def verify_email():
    """
    Verificar email con token
    ---
    tags:
      - Registro
    parameters:
      - name: token
        in: query
        type: string
        required: true
        description: Token de verificación
      - name: connection
        in: query
        type: string
        required: false
        description: ID de conexión a BD del cliente
    responses:
      200:
        description: Email verificado
      400:
        description: Token inválido o expirado
    """
    token = request.args.get('token')
    connection = request.args.get('connection') or request.args.get('empresa') or request.args.get('empresa_id')

    if not connection:
        return jsonify({
            'success': False,
            'message': 'Connection requerido'
        }), 400

    empresa_id = get_empresa_id_from_connection(connection)

    if not token:
        return jsonify({
            'success': False,
            'message': 'Token requerido'
        }), 400

    conn = Database.get_connection(connection)
    cursor = conn.cursor()

    try:
        # Buscar usuario con el token
        cursor.execute("""
            SELECT id, email, full_name, token_expiracion FROM users
            WHERE token_verificacion = ? AND email_verificado = 0
        """, (token,))

        row = cursor.fetchone()

        if not row:
            return jsonify({
                'success': False,
                'message': 'Token inválido o ya utilizado'
            }), 400

        user_id, email, full_name, token_expiracion = row

        # Verificar si el token ha expirado
        if token_expiracion and datetime.now() > token_expiracion:
            return jsonify({
                'success': False,
                'message': 'El token ha expirado. Solicita un nuevo registro.'
            }), 400

        # Activar usuario
        cursor.execute("""
            UPDATE users
            SET active = 1, email_verificado = 1, token_verificacion = NULL, token_expiracion = NULL
            WHERE id = ?
        """, (user_id,))

        # Crear relación con la empresa en users_empresas
        # Verificar si ya existe la relación (por si acaso)
        cursor.execute("""
            SELECT 1 FROM users_empresas WHERE user_id = ? AND empresa_id = ?
        """, (user_id, empresa_id))

        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users_empresas (user_id, empresa_id, cliente_id, rol)
                VALUES (?, ?, NULL, 'usuario')
            """, (user_id, empresa_id))
            print(f"✅ Usuario {user_id} asignado a empresa {empresa_id}")

        conn.commit()

        # Log de auditoría - verificación exitosa
        AuditModel.log(
            accion=AuditAction.USER_EMAIL_VERIFY,
            user_id=user_id,
            username=email,
            empresa_id=empresa_id,
            connection_id=connection,
            recurso='user',
            recurso_id=str(user_id),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalles={'email': email, 'full_name': full_name},
            resultado=AuditResult.SUCCESS
        )

        # Enviar email de bienvenida
        try:
            enviar_email_bienvenida(email, full_name, empresa_id, connection)
            print(f"✅ Email de bienvenida enviado a {email}")
        except Exception as e:
            print(f"⚠️ Error al enviar email de bienvenida: {e}")
            # No fallar la verificación si el email de bienvenida no se envía

        return jsonify({
            'success': True,
            'message': 'Email verificado correctamente. Ya puedes iniciar sesión.'
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al verificar email: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

def get_base_url():
    """
    Obtiene la URL base correcta detectando automáticamente el protocolo.
    Prioridad:
    1. Variable de entorno BASE_URL (si está configurada)
    2. Headers de proxy X-Forwarded-Proto/Host
    3. request.url_root como fallback
    """
    # 1. Variable de entorno tiene prioridad máxima
    base_url_env = os.environ.get('BASE_URL')
    if base_url_env:
        return base_url_env.rstrip('/')

    # 2. Detectar desde headers de proxy o request
    # X-Forwarded-Proto tiene prioridad sobre request.scheme
    proto = request.headers.get('X-Forwarded-Proto', request.scheme)

    # X-Forwarded-Host tiene prioridad sobre request.host
    host = request.headers.get('X-Forwarded-Host', request.host)

    return f"{proto}://{host}"


def enviar_email_verificacion(email, nombre, token, empresa_id="1", connection=None):
    """Envía el email de verificación"""
    email_config = EmailConfigModel.get_active_config(empresa_id, connection)

    if not email_config:
        raise Exception("No hay configuración de email activa")

    # Construir URL de verificación
    base_url = get_base_url()

    print(f"[DEBUG] Construyendo URL de verificación:")
    print(f"   X-Forwarded-Proto: {request.headers.get('X-Forwarded-Proto', 'N/A')}")
    print(f"   X-Forwarded-Host: {request.headers.get('X-Forwarded-Host', 'N/A')}")
    print(f"   request.scheme: {request.scheme}")
    print(f"   request.host: {request.host}")
    print(f"   Base URL final: {base_url}")
    print(f"   Connection: {connection}")

    # Usar connection en la URL de verificación
    verify_url = f"{base_url}/verificar-email?token={token}&connection={connection}"

    msg = MIMEMultipart()
    msg['From'] = f"Sistema de Stocks <{email_config['email_from']}>"
    msg['To'] = email
    msg['Subject'] = "Verifica tu cuenta - Sistema de Gestión de Stocks"
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = f"<{secrets.token_urlsafe(16)}@jobers.net>"
    msg['Reply-To'] = email_config['email_from']
    msg['X-Priority'] = '1'
    msg['X-Mailer'] = 'Sistema de Gestión de Stocks v1.0'

    body = f"""
    <!DOCTYPE html>
    <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <!-- Logo/Branding superior -->
                        <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width: 600px; margin-bottom: 20px;">
                            <tr>
                                <td align="center" style="padding: 20px;">
                                    <span style="font-size: 32px; font-weight: 700; color: #ffffff; letter-spacing: 2px;">STOCKS</span>
                                    <span style="display: block; font-size: 11px; color: #FF4338; letter-spacing: 4px; margin-top: 5px;">MANAGEMENT SYSTEM</span>
                                </td>
                            </tr>
                        </table>
                        <!-- Tarjeta principal -->
                        <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 24px; overflow: hidden; box-shadow: 0 25px 50px rgba(0,0,0,0.3);">
                            <!-- Header con icono animado -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #FF4338 0%, #FF6B5B 50%, #D32F2F 100%); padding: 60px 40px; text-align: center; position: relative;">
                                    <!-- Circulos decorativos -->
                                    <div style="position: absolute; top: -30px; right: -30px; width: 120px; height: 120px; background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
                                    <div style="position: absolute; bottom: -40px; left: -40px; width: 150px; height: 150px; background: rgba(255,255,255,0.05); border-radius: 50%;"></div>
                                    <!-- Icono principal -->
                                    <div style="width: 100px; height: 100px; background: rgba(255,255,255,0.2); border-radius: 50%; margin: 0 auto 25px; display: inline-block; line-height: 100px; backdrop-filter: blur(10px); border: 2px solid rgba(255,255,255,0.3);">
                                        <span style="font-size: 50px; color: #ffffff;">&#9993;</span>
                                    </div>
                                    <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">Verifica tu Email</h1>
                                    <p style="color: rgba(255,255,255,0.95); margin: 15px 0 0; font-size: 17px; font-weight: 300;">Estas a un solo clic de comenzar</p>
                                </td>
                            </tr>
                            <!-- Contenido principal -->
                            <tr>
                                <td style="padding: 50px 45px;">
                                    <p style="color: #1a1a2e; font-size: 20px; margin: 0 0 25px; line-height: 1.5;">
                                        Hola <strong style="color: #FF4338; background: linear-gradient(90deg, #FF4338, #FF6B5B); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{nombre}</strong> &#128075;
                                    </p>
                                    <p style="color: #4a4a68; font-size: 16px; margin: 0 0 35px; line-height: 1.8;">
                                        Gracias por unirte a nuestro <strong style="color: #1a1a2e;">Sistema de Gestion de Stocks</strong>.
                                        Estamos encantados de tenerte con nosotros. Para activar tu cuenta y comenzar a disfrutar
                                        de todas las funcionalidades, simplemente haz clic en el boton de abajo.
                                    </p>
                                    <!-- Boton CTA con efecto -->
                                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                        <tr>
                                            <td align="center" style="padding: 15px 0 40px;">
                                                <a href="{verify_url}" style="display: inline-block; background-color: #FF4338; color: #ffffff; padding: 20px 60px; text-decoration: none; border-radius: 50px; font-size: 17px; font-weight: 600; letter-spacing: 0.5px; border: none;">
                                                    &#10003; &nbsp; Verificar mi cuenta
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    <!-- Separador decorativo -->
                                    <div style="height: 1px; background: linear-gradient(90deg, transparent, #e5e7eb, transparent); margin: 10px 0 30px;"></div>
                                    <!-- Info adicional -->
                                    <div style="background: linear-gradient(135deg, #f8f9fc 0%, #eef1f5 100%); border-radius: 16px; padding: 25px 30px; border: 1px solid #e5e7eb;">
                                        <p style="color: #6b7280; font-size: 14px; margin: 0 0 15px; line-height: 1.6;">
                                            <strong style="color: #4a4a68;">&#128279; Link alternativo</strong><br>
                                            Si el boton no funciona, copia y pega este enlace:
                                        </p>
                                        <p style="color: #FF4338; font-size: 12px; margin: 0; word-break: break-all; background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px dashed #FF4338; font-family: monospace;">
                                            {verify_url}
                                        </p>
                                    </div>
                                    <!-- Aviso de expiracion con icono -->
                                    <div style="margin-top: 30px; padding: 20px 25px; border-radius: 12px; background: linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%); border-left: 5px solid #FF4338;">
                                        <p style="color: #991b1b; font-size: 14px; margin: 0; font-weight: 500;">
                                            &#9200; <strong>Importante:</strong> Este enlace expira en <strong>24 horas</strong>. Verifica tu cuenta cuanto antes.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                            <!-- Footer con estilo -->
                            <tr>
                                <td style="background: linear-gradient(180deg, #f8f9fc 0%, #eef1f5 100%); padding: 35px 40px; border-top: 1px solid #e5e7eb;">
                                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                        <tr>
                                            <td align="center">
                                                <p style="color: #9ca3af; font-size: 13px; margin: 0 0 15px;">
                                                    &#128274; Si no solicitaste esta cuenta, ignora este mensaje.
                                                </p>
                                                <div style="height: 1px; background: linear-gradient(90deg, transparent, #d1d5db, transparent); margin: 15px 0;"></div>
                                                <p style="color: #b0b0b0; font-size: 11px; margin: 0;">
                                                    &copy; {datetime.now().year} Sistema de Gestion de Stocks &bull; Todos los derechos reservados
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        <!-- Texto legal exterior -->
                        <p style="color: rgba(255,255,255,0.5); font-size: 11px; margin: 30px 0 0; text-align: center; max-width: 450px;">
                            Este es un mensaje automatico generado por el sistema.<br>Por favor, no respondas directamente a este correo.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    # Enviar email con logging mejorado
    try:
        print(f"📧 Intentando enviar email a: {email}")
        print(f"   SMTP Server: {email_config['smtp_server']}:{email_config['smtp_port']}")
        print(f"   Email From: {email_config['email_from']}")
        print(f"   URL de verificación: {verify_url}")

        if email_config['smtp_port'] == 465:
            print("   Usando SMTP_SSL (puerto 465)")
            server = smtplib.SMTP_SSL(email_config['smtp_server'], email_config['smtp_port'])
        else:
            print(f"   Usando SMTP con STARTTLS (puerto {email_config['smtp_port']})")
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()

        print("   Intentando login...")
        server.login(email_config['email_from'], email_config['email_password'])
        print("   Login exitoso, enviando mensaje...")

        # Enviar con debugging completo
        server.set_debuglevel(1)  # Activar debug SMTP
        result = server.send_message(msg)
        print(f"   Respuesta del servidor: {result}")
        print(f"✅ Email enviado exitosamente a {email}")

        server.quit()
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Error de autenticación SMTP: {e}")
        raise Exception(f"Error de autenticación SMTP: {e}")
    except smtplib.SMTPException as e:
        print(f"❌ Error SMTP: {e}")
        raise Exception(f"Error SMTP: {e}")
    except Exception as e:
        print(f"❌ Error general al enviar email: {e}")
        raise


def enviar_email_bienvenida(email, nombre, empresa_id="1", connection=None):
    """Envía el email de bienvenida tras verificar la cuenta"""
    email_config = EmailConfigModel.get_active_config(empresa_id, connection)

    if not email_config:
        raise Exception("No hay configuración de email activa")

    # Construir URL del login
    base_url = get_base_url()
    login_url = f"{base_url}/login?connection={connection}"

    msg = MIMEMultipart()
    msg['From'] = f"Sistema de Stocks <{email_config['email_from']}>"
    msg['To'] = email
    msg['Subject'] = "¡Cuenta activada! - Sistema de Gestión de Stocks"
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = f"<{secrets.token_urlsafe(16)}@jobers.net>"
    msg['Reply-To'] = email_config['email_from']
    msg['X-Mailer'] = 'Sistema de Gestión de Stocks v1.0'

    body = f"""
    <!DOCTYPE html>
    <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); min-height: 100vh;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <!-- Logo/Branding superior -->
                        <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width: 600px; margin-bottom: 20px;">
                            <tr>
                                <td align="center" style="padding: 20px;">
                                    <span style="font-size: 32px; font-weight: 700; color: #ffffff; letter-spacing: 2px;">STOCKS</span>
                                    <span style="display: block; font-size: 11px; color: #10B981; letter-spacing: 4px; margin-top: 5px;">MANAGEMENT SYSTEM</span>
                                </td>
                            </tr>
                        </table>
                        <!-- Tarjeta principal -->
                        <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 24px; overflow: hidden; box-shadow: 0 25px 50px rgba(0,0,0,0.3);">
                            <!-- Header con celebracion -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #10B981 0%, #34D399 50%, #059669 100%); padding: 60px 40px; text-align: center; position: relative;">
                                    <!-- Confetti decorativo -->
                                    <div style="position: absolute; top: 20px; left: 30px; font-size: 24px;">&#127881;</div>
                                    <div style="position: absolute; top: 40px; right: 40px; font-size: 20px;">&#10024;</div>
                                    <div style="position: absolute; bottom: 30px; left: 50px; font-size: 18px;">&#127882;</div>
                                    <div style="position: absolute; bottom: 25px; right: 60px; font-size: 22px;">&#127880;</div>
                                    <!-- Icono principal con check -->
                                    <div style="width: 100px; height: 100px; background: rgba(255,255,255,0.25); border-radius: 50%; margin: 0 auto 25px; display: inline-block; line-height: 100px; backdrop-filter: blur(10px); border: 3px solid rgba(255,255,255,0.4);">
                                        <span style="font-size: 55px; color: #ffffff;">&#10003;</span>
                                    </div>
                                    <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px; text-shadow: 0 2px 10px rgba(0,0,0,0.15);">&#127881; Cuenta Activada!</h1>
                                    <p style="color: rgba(255,255,255,0.95); margin: 15px 0 0; font-size: 17px; font-weight: 300;">Tu verificacion se ha completado con exito</p>
                                </td>
                            </tr>
                            <!-- Contenido principal -->
                            <tr>
                                <td style="padding: 50px 45px;">
                                    <p style="color: #1a1a2e; font-size: 20px; margin: 0 0 25px; line-height: 1.5;">
                                        Hola <strong style="color: #10B981;">{nombre}</strong> &#128079;
                                    </p>
                                    <p style="color: #4a4a68; font-size: 16px; margin: 0 0 15px; line-height: 1.8;">
                                        <strong style="color: #1a1a2e;">&#127881; Enhorabuena!</strong> Tu cuenta ha sido verificada y activada correctamente.
                                        Ya formas parte de nuestra comunidad.
                                    </p>
                                    <p style="color: #4a4a68; font-size: 16px; margin: 0 0 35px; line-height: 1.8;">
                                        Ahora puedes acceder al <strong style="color: #1a1a2e;">Sistema de Gestion de Stocks</strong> con tus credenciales
                                        y comenzar a explorar todas las funcionalidades que tenemos para ti.
                                    </p>
                                    <!-- Boton CTA con efecto -->
                                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                        <tr>
                                            <td align="center" style="padding: 15px 0 40px;">
                                                <a href="{login_url}" style="display: inline-block; background-color: #10B981; color: #ffffff; padding: 20px 60px; text-decoration: none; border-radius: 50px; font-size: 17px; font-weight: 600; letter-spacing: 0.5px;">
                                                    &#128640; &nbsp; Acceder al Sistema
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    <!-- Separador decorativo -->
                                    <div style="height: 1px; background: linear-gradient(90deg, transparent, #e5e7eb, transparent); margin: 10px 0 30px;"></div>
                                    <!-- Que puedes hacer - Cards -->
                                    <p style="color: #1a1a2e; font-size: 16px; font-weight: 600; margin: 0 0 20px; text-align: center;">
                                        &#128161; Que puedes hacer ahora
                                    </p>
                                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                        <tr>
                                            <td width="50%" style="padding: 8px;">
                                                <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #bbf7d0;">
                                                    <span style="font-size: 28px; display: block; margin-bottom: 10px;">&#128230;</span>
                                                    <span style="color: #166534; font-size: 13px; font-weight: 600;">Consultar Inventario</span>
                                                </div>
                                            </td>
                                            <td width="50%" style="padding: 8px;">
                                                <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #bfdbfe;">
                                                    <span style="font-size: 28px; display: block; margin-bottom: 10px;">&#128203;</span>
                                                    <span style="color: #1e40af; font-size: 13px; font-weight: 600;">Crear Solicitudes</span>
                                                </div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td width="50%" style="padding: 8px;">
                                                <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #fcd34d;">
                                                    <span style="font-size: 28px; display: block; margin-bottom: 10px;">&#128196;</span>
                                                    <span style="color: #92400e; font-size: 13px; font-weight: 600;">Fichas Tecnicas</span>
                                                </div>
                                            </td>
                                            <td width="50%" style="padding: 8px;">
                                                <div style="background: linear-gradient(135deg, #fae8ff 0%, #f5d0fe 100%); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #e9d5ff;">
                                                    <span style="font-size: 28px; display: block; margin-bottom: 10px;">&#128100;</span>
                                                    <span style="color: #7c3aed; font-size: 13px; font-weight: 600;">Gestionar Perfil</span>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <!-- Footer con estilo -->
                            <tr>
                                <td style="background: linear-gradient(180deg, #f8f9fc 0%, #eef1f5 100%); padding: 35px 40px; border-top: 1px solid #e5e7eb;">
                                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                        <tr>
                                            <td align="center">
                                                <p style="color: #6b7280; font-size: 14px; margin: 0 0 15px;">
                                                    &#128172; Tienes alguna pregunta? No dudes en contactarnos.
                                                </p>
                                                <div style="height: 1px; background: linear-gradient(90deg, transparent, #d1d5db, transparent); margin: 15px 0;"></div>
                                                <p style="color: #b0b0b0; font-size: 11px; margin: 0;">
                                                    &copy; {datetime.now().year} Sistema de Gestion de Stocks &bull; Todos los derechos reservados
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        <!-- Texto legal exterior -->
                        <p style="color: rgba(255,255,255,0.5); font-size: 11px; margin: 30px 0 0; text-align: center; max-width: 450px;">
                            Este es un mensaje automatico generado por el sistema.<br>Por favor, no respondas directamente a este correo.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    # Enviar email
    try:
        print(f"📧 Enviando email de bienvenida a: {email}")

        if email_config['smtp_port'] == 465:
            server = smtplib.SMTP_SSL(email_config['smtp_server'], email_config['smtp_port'])
        else:
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()

        server.login(email_config['email_from'], email_config['email_password'])
        server.send_message(msg)
        print(f"✅ Email de bienvenida enviado a {email}")
        server.quit()
    except Exception as e:
        print(f"❌ Error al enviar email de bienvenida: {e}")
        raise
