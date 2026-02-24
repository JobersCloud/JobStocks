"""
Rutas de Notificaciones
Endpoints para gestión de notificaciones de usuarios
"""
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from utils.auth import csrf_required
from models.notification_model import NotificationModel

notification_bp = Blueprint('notification', __name__, url_prefix='/api/notifications')


@notification_bp.route('/unread-count', methods=['GET'])
@login_required
def unread_count():
    """
    Obtener conteo de notificaciones no leídas (endpoint ligero para polling)
    ---
    tags:
      - Notificaciones
    security:
      - cookieAuth: []
    responses:
      200:
        description: Conteo de notificaciones no leídas
    """
    empresa_id = session.get('empresa_id')
    connection_id = session.get('connection')

    count = NotificationModel.get_unread_count(
        current_user.id, empresa_id, connection_id
    )

    return jsonify({
        'success': True,
        'count': count
    })


@notification_bp.route('', methods=['GET'])
@login_required
def get_notifications():
    """
    Obtener lista de notificaciones no leídas
    ---
    tags:
      - Notificaciones
    security:
      - cookieAuth: []
    responses:
      200:
        description: Lista de notificaciones no leídas
    """
    empresa_id = session.get('empresa_id')
    connection_id = session.get('connection')

    notifications = NotificationModel.get_unread(
        current_user.id, empresa_id, connection_id
    )

    return jsonify({
        'success': True,
        'notifications': notifications,
        'total': len(notifications)
    })


@notification_bp.route('/<int:notification_id>/read', methods=['PUT'])
@login_required
@csrf_required
def mark_as_read(notification_id):
    """
    Marcar una notificación como leída
    ---
    tags:
      - Notificaciones
    security:
      - cookieAuth: []
    parameters:
      - name: notification_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Notificación marcada como leída
    """
    connection_id = session.get('connection')

    result = NotificationModel.mark_read(
        notification_id, current_user.id, connection_id
    )

    if result:
        return jsonify({
            'success': True,
            'message': 'Notificación marcada como leída'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Notificación no encontrada'
        }), 404


@notification_bp.route('/read-all', methods=['PUT'])
@login_required
@csrf_required
def mark_all_as_read():
    """
    Marcar todas las notificaciones como leídas
    ---
    tags:
      - Notificaciones
    security:
      - cookieAuth: []
    responses:
      200:
        description: Todas las notificaciones marcadas como leídas
    """
    empresa_id = session.get('empresa_id')
    connection_id = session.get('connection')

    count = NotificationModel.mark_all_read(
        current_user.id, empresa_id, connection_id
    )

    return jsonify({
        'success': True,
        'message': f'{count} notificaciones marcadas como leídas',
        'count': count
    })
