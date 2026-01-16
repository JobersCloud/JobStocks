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
# ARCHIVO: routes/estadisticas_routes.py
# Descripcion: Rutas para estadisticas del dashboard
# ============================================
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from models.estadisticas_model import EstadisticasModel
from utils.auth import administrador_required

estadisticas_bp = Blueprint('estadisticas', __name__)


def get_empresa_id():
    """Obtiene el empresa_id del contexto actual."""
    # Primero intenta del usuario actual
    if hasattr(current_user, 'empresa_id') and current_user.empresa_id:
        return current_user.empresa_id
    # Luego de la sesion
    if 'empresa_id' in session:
        return session['empresa_id']
    # Por defecto
    return request.args.get('empresa_id', '1')


@estadisticas_bp.route('/api/estadisticas/resumen', methods=['GET'])
@login_required
@administrador_required
def get_resumen():
    """
    Obtener resumen de estadisticas
    ---
    tags:
      - Estadisticas
    security:
      - cookieAuth: []
    responses:
      200:
        description: Resumen de estadisticas
        schema:
          type: object
          properties:
            total_propuestas:
              type: integer
            propuestas_pendientes:
              type: integer
            usuarios_activos:
              type: integer
            consultas_pendientes:
              type: integer
            total_items_solicitados:
              type: number
      401:
        description: No autorizado
    """
    empresa_id = get_empresa_id()
    resumen = EstadisticasModel.get_resumen(empresa_id)
    return jsonify(resumen)


@estadisticas_bp.route('/api/estadisticas/productos-mas-solicitados', methods=['GET'])
@login_required
@administrador_required
def get_productos_mas_solicitados():
    """
    Obtener productos mas solicitados
    ---
    tags:
      - Estadisticas
    security:
      - cookieAuth: []
    parameters:
      - name: limit
        in: query
        type: integer
        default: 10
        description: Cantidad de productos a retornar
    responses:
      200:
        description: Lista de productos mas solicitados
        schema:
          type: array
          items:
            type: object
            properties:
              codigo:
                type: string
              descripcion:
                type: string
              formato:
                type: string
              total_solicitado:
                type: number
              veces_solicitado:
                type: integer
    """
    empresa_id = get_empresa_id()
    limit = request.args.get('limit', 10, type=int)
    productos = EstadisticasModel.get_productos_mas_solicitados(empresa_id, limit)
    return jsonify(productos)


@estadisticas_bp.route('/api/estadisticas/propuestas-por-dia', methods=['GET'])
@login_required
@administrador_required
def get_propuestas_por_dia():
    """
    Obtener propuestas agrupadas por dia
    ---
    tags:
      - Estadisticas
    security:
      - cookieAuth: []
    parameters:
      - name: dias
        in: query
        type: integer
        default: 30
        description: Cantidad de dias hacia atras
    responses:
      200:
        description: Lista de propuestas por dia
        schema:
          type: array
          items:
            type: object
            properties:
              fecha:
                type: string
                format: date
              cantidad:
                type: integer
              total_items:
                type: integer
    """
    empresa_id = get_empresa_id()
    dias = request.args.get('dias', 30, type=int)
    propuestas = EstadisticasModel.get_propuestas_por_periodo(empresa_id, dias)
    return jsonify(propuestas)


@estadisticas_bp.route('/api/estadisticas/propuestas-por-estado', methods=['GET'])
@login_required
@administrador_required
def get_propuestas_por_estado():
    """
    Obtener conteo de propuestas por estado
    ---
    tags:
      - Estadisticas
    security:
      - cookieAuth: []
    responses:
      200:
        description: Conteo de propuestas por estado
        schema:
          type: object
          additionalProperties:
            type: integer
    """
    empresa_id = get_empresa_id()
    estados = EstadisticasModel.get_propuestas_por_estado(empresa_id)
    return jsonify(estados)


@estadisticas_bp.route('/api/estadisticas/usuarios-mas-activos', methods=['GET'])
@login_required
@administrador_required
def get_usuarios_mas_activos():
    """
    Obtener usuarios con mas propuestas
    ---
    tags:
      - Estadisticas
    security:
      - cookieAuth: []
    parameters:
      - name: limit
        in: query
        type: integer
        default: 10
        description: Cantidad de usuarios a retornar
    responses:
      200:
        description: Lista de usuarios mas activos
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              username:
                type: string
              full_name:
                type: string
              total_propuestas:
                type: integer
              ultima_propuesta:
                type: string
                format: date-time
    """
    empresa_id = get_empresa_id()
    limit = request.args.get('limit', 10, type=int)
    usuarios = EstadisticasModel.get_usuarios_mas_activos(empresa_id, limit)
    return jsonify(usuarios)


@estadisticas_bp.route('/api/estadisticas/propuestas-por-mes', methods=['GET'])
@login_required
@administrador_required
def get_propuestas_por_mes():
    """
    Obtener propuestas agrupadas por mes
    ---
    tags:
      - Estadisticas
    security:
      - cookieAuth: []
    parameters:
      - name: meses
        in: query
        type: integer
        default: 12
        description: Cantidad de meses hacia atras
    responses:
      200:
        description: Lista de propuestas por mes
        schema:
          type: array
          items:
            type: object
            properties:
              anio:
                type: integer
              mes:
                type: integer
              cantidad:
                type: integer
              total_items:
                type: integer
    """
    empresa_id = get_empresa_id()
    meses = request.args.get('meses', 12, type=int)
    propuestas = EstadisticasModel.get_propuestas_por_mes(empresa_id, meses)
    return jsonify(propuestas)


@estadisticas_bp.route('/api/estadisticas/consultas-por-estado', methods=['GET'])
@login_required
@administrador_required
def get_consultas_por_estado():
    """
    Obtener conteo de consultas por estado
    ---
    tags:
      - Estadisticas
    security:
      - cookieAuth: []
    responses:
      200:
        description: Conteo de consultas por estado
        schema:
          type: object
          additionalProperties:
            type: integer
    """
    empresa_id = get_empresa_id()
    estados = EstadisticasModel.get_consultas_por_estado(empresa_id)
    return jsonify(estados)
