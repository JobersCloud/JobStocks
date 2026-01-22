"""
Rutas de Auditoria
Endpoints para consultar y gestionar logs de auditoria
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required
from models.audit_model import AuditModel, AuditAction, AuditResult
from utils.auth import administrador_required, csrf_required

audit_bp = Blueprint('audit', __name__)


def get_empresa_id():
    """Obtener empresa_id del request o session"""
    from flask import session
    return request.args.get('empresa_id') or session.get('empresa_id')


def get_connection_id():
    """Obtener connection_id de la session"""
    from flask import session
    conn = session.get('connection')
    return int(conn) if conn else None


@audit_bp.route('/api/audit-logs', methods=['GET'])
@login_required
@administrador_required
def get_audit_logs():
    """
    Obtener logs de auditoria con filtros
    ---
    parameters:
      - name: empresa_id
        in: query
        type: string
        description: Filtrar por empresa
      - name: user_id
        in: query
        type: integer
        description: Filtrar por usuario
      - name: username
        in: query
        type: string
        description: Buscar por nombre de usuario
      - name: accion
        in: query
        type: string
        description: Filtrar por tipo de accion
      - name: fecha_desde
        in: query
        type: string
        description: Fecha inicio (YYYY-MM-DD)
      - name: fecha_hasta
        in: query
        type: string
        description: Fecha fin (YYYY-MM-DD)
      - name: resultado
        in: query
        type: string
        description: Filtrar por resultado (SUCCESS/FAILED/BLOCKED)
      - name: limit
        in: query
        type: integer
        description: Limite de registros (default 50)
      - name: offset
        in: query
        type: integer
        description: Desplazamiento para paginacion
    responses:
      200:
        description: Lista de logs
    """
    empresa_id = get_empresa_id()
    connection_id = get_connection_id()
    user_id = request.args.get('user_id', type=int)
    username = request.args.get('username')
    accion = request.args.get('accion')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    resultado = request.args.get('resultado')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    # Limitar para evitar sobrecarga
    if limit > 200:
        limit = 200

    logs = AuditModel.get_logs(
        empresa_id=empresa_id,
        connection_id=connection_id,
        user_id=user_id,
        username=username,
        accion=accion,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        resultado=resultado,
        limit=limit,
        offset=offset
    )

    total = AuditModel.count_logs(
        empresa_id=empresa_id,
        connection_id=connection_id,
        user_id=user_id,
        username=username,
        accion=accion,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        resultado=resultado
    )

    return jsonify({
        'success': True,
        'logs': logs,
        'total': total,
        'limit': limit,
        'offset': offset
    })


@audit_bp.route('/api/audit-logs/summary', methods=['GET'])
@login_required
@administrador_required
def get_audit_summary():
    """
    Obtener resumen de auditoria para dashboard
    ---
    parameters:
      - name: empresa_id
        in: query
        type: string
      - name: dias
        in: query
        type: integer
        default: 30
    responses:
      200:
        description: Resumen con conteos por accion y resultado
    """
    empresa_id = get_empresa_id()
    connection_id = get_connection_id()
    dias = request.args.get('dias', 30, type=int)

    if dias > 365:
        dias = 365

    actions_summary = AuditModel.get_actions_summary(empresa_id=empresa_id, connection_id=connection_id, dias=dias)
    results_summary = AuditModel.get_results_summary(empresa_id=empresa_id, connection_id=connection_id, dias=dias)

    return jsonify({
        'success': True,
        'por_accion': actions_summary,
        'por_resultado': results_summary,
        'dias': dias
    })


@audit_bp.route('/api/audit-logs/actions', methods=['GET'])
@login_required
@administrador_required
def get_available_actions():
    """
    Obtener lista de tipos de acciones disponibles
    ---
    responses:
      200:
        description: Lista de acciones
    """
    actions = AuditAction.get_all_actions()
    return jsonify({
        'success': True,
        'actions': actions
    })


@audit_bp.route('/api/audit-logs/cleanup', methods=['DELETE'])
@login_required
@administrador_required
@csrf_required
def cleanup_audit_logs():
    """
    Limpiar logs antiguos
    ---
    parameters:
      - name: dias
        in: query
        type: integer
        default: 90
        description: Eliminar logs mas antiguos que X dias
    responses:
      200:
        description: Numero de registros eliminados
    """
    dias = request.args.get('dias', 90, type=int)
    connection_id = get_connection_id()

    # Minimo 30 dias para evitar borrados accidentales
    if dias < 30:
        return jsonify({
            'success': False,
            'message': 'El minimo es 30 dias'
        }), 400

    deleted = AuditModel.cleanup_old_logs(connection_id=connection_id, days=dias)

    return jsonify({
        'success': True,
        'deleted': deleted,
        'message': f'Se eliminaron {deleted} registros con mas de {dias} dias'
    })
