from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from models.user_session_model import UserSessionModel
from models.audit_model import AuditModel, AuditAction, AuditResult
from utils.auth import administrador_required, csrf_required


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

user_session_bp = Blueprint('user_session', __name__)


@user_session_bp.route('/api/sesiones', methods=['GET'])
@login_required
@administrador_required
def get_sessions():
    """Obtener sesiones activas"""
    empresa_id = request.args.get('empresa_id')
    user_id = request.args.get('user_id')

    # Limpiar sesiones expiradas antes de listar
    UserSessionModel.cleanup_expired()

    sessions = UserSessionModel.get_active_sessions(empresa_id, user_id=user_id)
    count = len(sessions)

    return jsonify({
        'success': True,
        'total': count,
        'sesiones': sessions
    })


@user_session_bp.route('/api/sesiones/<int:session_id>', methods=['DELETE'])
@login_required
@administrador_required
def kill_session(session_id):
    """Terminar una sesion activa"""
    deleted = UserSessionModel.delete_by_id(session_id)

    if deleted:
        # Registrar audit log
        try:
            AuditModel.log(
                accion=AuditAction.SESSION_KILL,
                user_id=current_user.id,
                username=current_user.username,
                empresa_id=session.get('empresa_id'),
                recurso='session',
                recurso_id=str(session_id),
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent'),
                resultado=AuditResult.SUCCESS
            )
        except Exception as e:
            print(f"Warning: No se pudo registrar audit log: {e}")

        return jsonify({
            'success': True,
            'message': 'Sesion terminada correctamente'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Sesion no encontrada'
        }), 404


@user_session_bp.route('/api/sesiones/usuario/<int:user_id>', methods=['DELETE'])
@login_required
@administrador_required
def kill_user_sessions(user_id):
    """Terminar todas las sesiones de un usuario"""
    deleted = UserSessionModel.delete_by_user_id(user_id)

    return jsonify({
        'success': True,
        'message': f'{deleted} sesion(es) terminada(s)',
        'deleted_count': deleted
    })


@user_session_bp.route('/api/sesiones/todas-excepto-actual', methods=['DELETE'])
@login_required
@administrador_required
@csrf_required
def kill_all_except_current():
    """Eliminar todas las sesiones excepto la actual"""
    current_token = session.get('session_token')
    if not current_token:
        return jsonify({
            'success': False,
            'message': 'No hay sesión actual'
        }), 400

    empresa_id = request.args.get('empresa_id')
    deleted = UserSessionModel.delete_all_except(current_token, empresa_id)

    # Registrar audit log
    try:
        AuditModel.log(
            accion=AuditAction.SESSION_KILL_ALL,
            user_id=current_user.id,
            username=current_user.username,
            empresa_id=session.get('empresa_id'),
            recurso='session',
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent'),
            detalles={'sesiones_eliminadas': deleted},
            resultado=AuditResult.SUCCESS
        )
    except Exception as e:
        print(f"Warning: No se pudo registrar audit log: {e}")

    return jsonify({
        'success': True,
        'message': f'{deleted} sesión(es) cerrada(s)',
        'deleted_count': deleted
    })


@user_session_bp.route('/api/sesiones/count', methods=['GET'])
@login_required
@administrador_required
def count_sessions():
    """Contar sesiones activas"""
    empresa_id = request.args.get('empresa_id')
    count = UserSessionModel.count_active_sessions(empresa_id)

    return jsonify({
        'success': True,
        'count': count
    })
