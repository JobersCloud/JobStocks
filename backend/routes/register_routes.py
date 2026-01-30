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
            INSERT INTO users (username, password_hash, email, full_name, pais, active, email_verificado, token_verificacion, token_expiracion)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)
        """, (username, password_hash, email, full_name, pais, token, token_expiracion))

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
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;
                          margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>¡Bienvenido!</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre}</strong>,</p>
                    <p>Gracias por registrarte en el Sistema de Gestión de Stocks.</p>
                    <p>Para completar tu registro y activar tu cuenta, haz clic en el siguiente botón:</p>
                    <p style="text-align: center;">
                        <a href="{verify_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff !important; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold;">Verificar mi cuenta</a>
                    </p>
                    <p>O copia y pega este enlace en tu navegador:</p>
                    <p style="word-break: break-all; background-color: #eee; padding: 10px; border-radius: 5px;">
                        {verify_url}
                    </p>
                    <p><strong>Este enlace expira en 24 horas.</strong></p>
                </div>
                <div class="footer">
                    <p>Si no solicitaste este registro, ignora este mensaje.</p>
                    <p>© {datetime.now().year} - Sistema de Gestión de Stocks</p>
                </div>
            </div>
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
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
                          padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .check-icon {{ font-size: 48px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="check-icon">✓</div>
                    <h1>¡Cuenta Activada!</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre}</strong>,</p>
                    <p>Tu cuenta ha sido verificada y activada correctamente.</p>
                    <p>Ya puedes acceder al Sistema de Gestión de Stocks con tus credenciales.</p>
                    <p style="text-align: center;">
                        <a href="{login_url}" style="display: inline-block; background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%); color: #ffffff !important; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold;">Iniciar Sesión</a>
                    </p>
                    <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} - Sistema de Gestión de Stocks</p>
                </div>
            </div>
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
