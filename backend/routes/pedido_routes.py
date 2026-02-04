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
# Fecha : 2026-02-03
# ============================================================

# ============================================
# ARCHIVO: routes/pedido_routes.py
# Endpoints para consulta de pedidos de venta (ERP)
# ============================================
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from utils.auth import api_key_or_login_required, administrador_required
from models.pedido_model import PedidoModel

pedido_bp = Blueprint('pedido', __name__, url_prefix='/api/pedidos')


@pedido_bp.route('/mis-pedidos', methods=['GET'])
@login_required
def get_mis_pedidos():
    """
    Obtener los pedidos del usuario actual (usando cliente_id).
    Usa empresa de sesion.
    ---
    tags:
      - Pedidos
    security:
      - cookieAuth: []
    parameters:
      - name: anyo
        in: query
        type: integer
        required: false
        description: Filtrar por año
      - name: fecha_desde
        in: query
        type: string
        format: date
        required: false
        description: Filtrar desde fecha (YYYY-MM-DD)
      - name: fecha_hasta
        in: query
        type: string
        format: date
        required: false
        description: Filtrar hasta fecha (YYYY-MM-DD)
    responses:
      200:
        description: Lista de pedidos del usuario
      400:
        description: El usuario no tiene cliente_id asignado
      401:
        description: No autenticado
    """
    # Verificar que el usuario tiene cliente_id asignado
    cliente_id = current_user.cliente_id
    if not cliente_id:
        return jsonify({
            'success': False,
            'error': 'No tienes un cliente asociado en el sistema'
        }), 400

    empresa_id = session.get('empresa_id', '1')
    anyo = request.args.get('anyo', type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    try:
        pedidos = PedidoModel.get_by_user(
            cliente_id=cliente_id,
            empresa_id=empresa_id,
            anyo=anyo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )
        return jsonify({
            'success': True,
            'total': len(pedidos),
            'pedidos': pedidos
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pedido_bp.route('', methods=['GET'])
@login_required
@administrador_required
def get_todos_pedidos():
    """
    Obtener todos los pedidos (solo administradores).
    Usa empresa de sesion.
    ---
    tags:
      - Pedidos
    security:
      - cookieAuth: []
    parameters:
      - name: anyo
        in: query
        type: integer
        required: false
        description: Filtrar por año
      - name: fecha_desde
        in: query
        type: string
        format: date
        required: false
        description: Filtrar desde fecha (YYYY-MM-DD)
      - name: fecha_hasta
        in: query
        type: string
        format: date
        required: false
        description: Filtrar hasta fecha (YYYY-MM-DD)
      - name: cliente
        in: query
        type: string
        required: false
        description: Filtrar por codigo de cliente
    responses:
      200:
        description: Lista de todos los pedidos
      401:
        description: No autenticado
      403:
        description: No autorizado (requiere rol administrador)
    """
    empresa_id = session.get('empresa_id', '1')
    anyo = request.args.get('anyo', type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    cliente = request.args.get('cliente')

    try:
        pedidos = PedidoModel.get_all(
            empresa_id=empresa_id,
            anyo=anyo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            cliente=cliente
        )
        return jsonify({
            'success': True,
            'total': len(pedidos),
            'pedidos': pedidos
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pedido_bp.route('/<int:empresa>/<int:anyo>/<int:pedido>', methods=['GET'])
@api_key_or_login_required
def get_pedido(empresa, anyo, pedido):
    """
    Obtener un pedido por su clave primaria compuesta.
    ---
    tags:
      - Pedidos
    security:
      - cookieAuth: []
      - apiKeyHeader: []
      - apiKeyQuery: []
    parameters:
      - name: empresa
        in: path
        type: integer
        required: true
        description: Codigo de empresa
      - name: anyo
        in: path
        type: integer
        required: true
        description: Año del pedido
      - name: pedido
        in: path
        type: integer
        required: true
        description: Numero de pedido
    responses:
      200:
        description: Detalle del pedido con sus lineas
      401:
        description: No autenticado
      404:
        description: Pedido no encontrado
    """
    try:
        pedido_data = PedidoModel.get_by_id(empresa, anyo, pedido)
        if not pedido_data:
            return jsonify({
                'success': False,
                'error': 'Pedido no encontrado'
            }), 404

        return jsonify({
            'success': True,
            'pedido': pedido_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pedido_bp.route('/<int:empresa>/<int:anyo>/<int:pedido>/lineas', methods=['GET'])
@api_key_or_login_required
def get_lineas_pedido(empresa, anyo, pedido):
    """
    Obtener las lineas de un pedido.
    ---
    tags:
      - Pedidos
    security:
      - cookieAuth: []
      - apiKeyHeader: []
      - apiKeyQuery: []
    parameters:
      - name: empresa
        in: path
        type: integer
        required: true
        description: Codigo de empresa
      - name: anyo
        in: path
        type: integer
        required: true
        description: Año del pedido
      - name: pedido
        in: path
        type: integer
        required: true
        description: Numero de pedido
    responses:
      200:
        description: Lista de lineas del pedido
      401:
        description: No autenticado
    """
    try:
        lineas = PedidoModel.get_lineas(empresa, anyo, pedido)
        return jsonify({
            'success': True,
            'total': len(lineas),
            'lineas': lineas
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
