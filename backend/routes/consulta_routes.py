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
# ARCHIVO: routes/consulta_routes.py
# Endpoints para gestión de consultas sobre productos
# ============================================
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from utils.auth import csrf_required
from utils.auth import administrador_required
from models.consulta_model import ConsultaModel
from models.email_config_model import EmailConfigModel
from models.parametros_model import ParametrosModel
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from utils.email_sender import smtp_send_message
from email.utils import formatdate

consulta_bp = Blueprint('consulta', __name__, url_prefix='/api/consultas')


def get_empresa_id():
    """Obtener empresa_id del request o sesión"""
    return request.args.get('empresa_id') or session.get('empresa_id', '1')


@consulta_bp.route('', methods=['POST'])
def crear_consulta():
    """
    Crear una nueva consulta sobre un producto (público o autenticado)
    ---
    tags:
      - Consultas
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - codigo_producto
            - nombre_cliente
            - email_cliente
            - mensaje
          properties:
            codigo_producto:
              type: string
            descripcion_producto:
              type: string
            formato:
              type: string
            calidad:
              type: string
            color:
              type: string
            tono:
              type: string
            calibre:
              type: string
            nombre_cliente:
              type: string
            email_cliente:
              type: string
            telefono_cliente:
              type: string
            mensaje:
              type: string
    responses:
      201:
        description: Consulta creada correctamente
      400:
        description: Datos inválidos
    """
    data = request.json
    empresa_id = get_empresa_id()

    # Validar campos requeridos
    required = ['codigo_producto', 'nombre_cliente', 'email_cliente', 'mensaje']
    for field in required:
        if not data.get(field):
            return jsonify({
                'success': False,
                'error': f'Campo "{field}" es requerido'
            }), 400

    # Añadir empresa_id y user_id si está autenticado
    data['empresa_id'] = empresa_id
    if current_user.is_authenticated:
        data['user_id'] = current_user.id

    # Crear consulta
    consulta_id = ConsultaModel.crear(data)

    if not consulta_id:
        return jsonify({
            'success': False,
            'error': 'Error al crear la consulta'
        }), 500

    # Enviar email de notificación al equipo
    try:
        connection_id = session.get('connection')
        enviar_notificacion_consulta(data, consulta_id, empresa_id, connection_id=connection_id)
    except Exception as e:
        print(f"⚠️ No se pudo enviar notificación: {e}")

    return jsonify({
        'success': True,
        'message': 'Consulta enviada correctamente. Te responderemos pronto.',
        'consulta_id': consulta_id
    }), 201


@consulta_bp.route('', methods=['GET'])
@login_required
@administrador_required
def listar_consultas():
    """
    Listar consultas de la empresa (solo admin)
    ---
    tags:
      - Consultas
    security:
      - cookieAuth: []
    parameters:
      - name: estado
        in: query
        type: string
        enum: [pendiente, respondida, cerrada]
    responses:
      200:
        description: Lista de consultas
    """
    empresa_id = get_empresa_id()
    estado = request.args.get('estado')
    user_id = request.args.get('user_id')

    consultas = ConsultaModel.get_all_by_empresa(empresa_id, estado, user_id=user_id)

    return jsonify({
        'success': True,
        'consultas': consultas,
        'total': len(consultas)
    })


@consulta_bp.route('/mis-consultas', methods=['GET'])
@login_required
def mis_consultas():
    """
    Listar consultas del usuario actual
    ---
    tags:
      - Consultas
    security:
      - cookieAuth: []
    parameters:
      - name: estado
        in: query
        type: string
        enum: [pendiente, respondida, cerrada]
    responses:
      200:
        description: Lista de consultas del usuario
    """
    empresa_id = get_empresa_id()
    estado = request.args.get('estado')

    consultas = ConsultaModel.get_by_user(current_user.id, empresa_id, estado)

    return jsonify({
        'success': True,
        'consultas': consultas,
        'total': len(consultas)
    })


@consulta_bp.route('/pendientes/count', methods=['GET'])
@login_required
@administrador_required
def contar_pendientes():
    """Contar consultas pendientes (para badge en menú)"""
    empresa_id = get_empresa_id()
    count = ConsultaModel.contar_pendientes(empresa_id)

    return jsonify({
        'success': True,
        'count': count
    })


@consulta_bp.route('/<int:consulta_id>', methods=['GET'])
@login_required
def obtener_consulta(consulta_id):
    """Obtener detalle de una consulta (admin o propietario)"""
    empresa_id = get_empresa_id()
    consulta = ConsultaModel.get_by_id(consulta_id, empresa_id)

    if not consulta:
        return jsonify({
            'success': False,
            'error': 'Consulta no encontrada'
        }), 404

    # Permitir acceso si es admin o si es el propietario de la consulta
    if current_user.rol not in ('administrador', 'superusuario') and consulta.get('user_id') != current_user.id:
        return jsonify({
            'success': False,
            'error': 'No tienes permisos para ver esta consulta'
        }), 403

    return jsonify({
        'success': True,
        'consulta': consulta
    })


@consulta_bp.route('/<int:consulta_id>/responder', methods=['POST'])
@login_required
@csrf_required
@administrador_required
def responder_consulta(consulta_id):
    """
    Responder a una consulta
    ---
    tags:
      - Consultas
    security:
      - cookieAuth: []
    parameters:
      - name: consulta_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - respuesta
          properties:
            respuesta:
              type: string
            enviar_email:
              type: boolean
              default: true
    responses:
      200:
        description: Consulta respondida
    """
    data = request.json
    empresa_id = get_empresa_id()

    if not data or not data.get('respuesta'):
        return jsonify({
            'success': False,
            'error': 'La respuesta es requerida'
        }), 400

    # Obtener consulta para enviar email
    consulta = ConsultaModel.get_by_id(consulta_id, empresa_id)
    if not consulta:
        return jsonify({
            'success': False,
            'error': 'Consulta no encontrada'
        }), 404

    # Guardar respuesta
    result = ConsultaModel.responder(
        consulta_id,
        empresa_id,
        data['respuesta'],
        current_user.id
    )

    if not result:
        return jsonify({
            'success': False,
            'error': 'Error al guardar la respuesta'
        }), 500

    # Enviar email de respuesta al cliente
    if data.get('enviar_email', True):
        try:
            resp_connection_id = session.get('connection')
            enviar_respuesta_consulta(consulta, data['respuesta'], empresa_id, connection_id=resp_connection_id)
        except Exception as e:
            print(f"⚠️ No se pudo enviar email de respuesta: {e}")

    # Notificar al usuario propietario de la consulta
    try:
        from models.notification_model import NotificationModel
        if consulta.get('user_id'):
            connection_id = session.get('connection')
            NotificationModel.create(
                user_id=consulta['user_id'],
                empresa_id=empresa_id,
                tipo='consulta_respondida',
                titulo=f'Respuesta a tu consulta sobre {consulta.get("codigo_producto", "")}',
                mensaje=f'Se ha respondido tu consulta sobre el producto {consulta.get("codigo_producto", "")}.',
                data={'consulta_id': consulta_id, 'codigo_producto': consulta.get('codigo_producto')},
                connection_id=connection_id
            )
    except Exception as e:
        print(f"Warning: No se pudo crear notificación: {e}")

    return jsonify({
        'success': True,
        'message': 'Respuesta enviada correctamente'
    })


@consulta_bp.route('/<int:consulta_id>/estado', methods=['PUT'])
@login_required
@csrf_required
@administrador_required
def cambiar_estado(consulta_id):
    """Cambiar estado de una consulta"""
    data = request.json
    empresa_id = get_empresa_id()

    if not data or 'estado' not in data:
        return jsonify({
            'success': False,
            'error': 'Campo "estado" es requerido'
        }), 400

    try:
        result = ConsultaModel.cambiar_estado(consulta_id, empresa_id, data['estado'])
        if not result:
            return jsonify({
                'success': False,
                'error': 'Consulta no encontrada'
            }), 404

        return jsonify({
            'success': True,
            'message': f'Estado cambiado a "{data["estado"]}"'
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@consulta_bp.route('/whatsapp-config', methods=['GET'])
def get_whatsapp_config():
    """Obtener configuración de WhatsApp para la empresa"""
    empresa_id = get_empresa_id()

    numero = ParametrosModel.get('WHATSAPP_NUMERO', empresa_id)

    return jsonify({
        'success': True,
        'numero': numero if numero else None,
        'habilitado': bool(numero and numero.strip())
    })


# ==================== FUNCIONES DE EMAIL ====================

def enviar_notificacion_consulta(data, consulta_id, empresa_id, connection_id=None):
    """Enviar email de notificación al equipo cuando llega una consulta"""
    email_config = EmailConfigModel.get_active_config(empresa_id, connection=connection_id)
    if not email_config:
        raise Exception("No hay configuración de email activa")

    msg = MIMEMultipart()
    msg['From'] = email_config['email_from']
    msg['To'] = email_config['email_to']
    msg['Subject'] = f"Nueva consulta sobre producto: {data['codigo_producto']}"
    msg['Date'] = formatdate(localtime=True)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #FF4338 0%, #C62828 100%); padding: 24px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 22px;">📩 Nueva Consulta Recibida</h1>
            </div>
            <div style="padding: 24px;">
                <div style="background: #f8f9fa; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 12px 0; color: #333;">📦 Producto consultado</h3>
                    <table style="width: 100%; font-size: 14px;">
                        <tr><td style="color: #666; padding: 4px 0;">Código:</td><td style="font-weight: bold;">{data['codigo_producto']}</td></tr>
                        <tr><td style="color: #666; padding: 4px 0;">Descripción:</td><td>{data.get('descripcion_producto', '-')}</td></tr>
                        <tr><td style="color: #666; padding: 4px 0;">Formato:</td><td>{data.get('formato', '-')}</td></tr>
                        <tr><td style="color: #666; padding: 4px 0;">Calidad:</td><td>{data.get('calidad', '-')}</td></tr>
                        <tr><td style="color: #666; padding: 4px 0;">Tono/Calibre:</td><td>{data.get('tono', '-')} / {data.get('calibre', '-')}</td></tr>
                    </table>
                </div>
                <div style="background: #e3f2fd; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 12px 0; color: #333;">👤 Datos del cliente</h3>
                    <p style="margin: 4px 0;"><strong>Nombre:</strong> {data['nombre_cliente']}</p>
                    <p style="margin: 4px 0;"><strong>Email:</strong> <a href="mailto:{data['email_cliente']}">{data['email_cliente']}</a></p>
                    <p style="margin: 4px 0;"><strong>Teléfono:</strong> {data.get('telefono_cliente', 'No proporcionado')}</p>
                </div>
                <div style="background: #fff3e0; border-radius: 8px; padding: 16px;">
                    <h3 style="margin: 0 0 12px 0; color: #333;">💬 Mensaje</h3>
                    <p style="margin: 0; white-space: pre-wrap;">{data['mensaje']}</p>
                </div>
                <div style="text-align: center; margin-top: 24px;">
                    <p style="color: #999; font-size: 12px;">Consulta #{consulta_id} · {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    smtp_send_message(email_config, msg)
    print(f"✅ Notificación de consulta enviada a {email_config['email_to']}")


def enviar_respuesta_consulta(consulta, respuesta, empresa_id, connection_id=None):
    """Enviar email de respuesta al cliente"""
    email_config = EmailConfigModel.get_active_config(empresa_id, connection=connection_id)
    if not email_config:
        raise Exception("No hay configuración de email activa")

    msg = MIMEMultipart()
    msg['From'] = email_config['email_from']
    msg['To'] = consulta['email_cliente']
    msg['Subject'] = f"Respuesta a tu consulta sobre: {consulta['codigo_producto']}"
    msg['Date'] = formatdate(localtime=True)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%); padding: 24px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 22px;">✅ Respuesta a tu consulta</h1>
            </div>
            <div style="padding: 24px;">
                <p style="font-size: 16px; color: #333;">Hola <strong>{consulta['nombre_cliente']}</strong>,</p>
                <p style="color: #555;">Gracias por tu interés. Aquí tienes la respuesta a tu consulta sobre el producto <strong>{consulta['codigo_producto']}</strong>:</p>

                <div style="background: #e8f5e9; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #4CAF50;">
                    <p style="margin: 0; white-space: pre-wrap; line-height: 1.6;">{respuesta}</p>
                </div>

                <div style="background: #f5f5f5; border-radius: 8px; padding: 16px; margin-top: 20px;">
                    <p style="margin: 0 0 8px 0; color: #666; font-size: 13px;"><strong>Tu consulta original:</strong></p>
                    <p style="margin: 0; color: #888; font-size: 13px; font-style: italic;">"{consulta['mensaje'][:200]}{'...' if len(consulta['mensaje']) > 200 else ''}"</p>
                </div>

                <p style="margin-top: 24px; color: #555;">Si tienes más preguntas, no dudes en contactarnos.</p>
                <p style="color: #555;">¡Saludos!</p>
            </div>
            <div style="background: #f8f9fa; padding: 16px; text-align: center; border-top: 1px solid #e0e0e0;">
                <p style="margin: 0; color: #999; font-size: 12px;">© {datetime.now().year} Sistema de Gestión de Stocks</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    smtp_send_message(email_config, msg)
    print(f"✅ Respuesta enviada a {consulta['email_cliente']}")
