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
import time
import logging
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from utils.auth import api_key_or_login_required, administrador_required
from models.pedido_model import PedidoModel

logger = logging.getLogger(__name__)

pedido_bp = Blueprint('pedido', __name__, url_prefix='/api/pedidos')


@pedido_bp.route('/mis-pedidos', methods=['GET'])
@login_required
def get_mis_pedidos():
    """
    Obtener los pedidos del usuario actual con paginacion.
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
      - name: fecha_desde
        in: query
        type: string
        format: date
        required: false
      - name: fecha_hasta
        in: query
        type: string
        format: date
        required: false
      - name: page
        in: query
        type: integer
        required: false
        default: 1
      - name: page_size
        in: query
        type: integer
        required: false
        default: 50
    responses:
      200:
        description: Lista paginada de pedidos del usuario
    """
    t0 = time.time()
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
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 50, type=int), 200)

    logger.warning(f'[PERF] GET /api/pedidos/mis-pedidos cliente={cliente_id} anyo={anyo} page={page}')

    try:
        t1 = time.time()
        result = PedidoModel.get_by_user(
            cliente_id=cliente_id,
            empresa_id=empresa_id,
            anyo=anyo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            page=page,
            page_size=page_size
        )
        t2 = time.time()
        logger.warning(f'[PERF] DB query + fetch: {t2-t1:.3f}s | rows={len(result["pedidos"])}')

        response = jsonify({
            'success': True,
            'total': result['total'],
            'page': result['page'],
            'page_size': result['page_size'],
            'total_pages': result['total_pages'],
            'pedidos': result['pedidos']
        })
        t3 = time.time()
        logger.warning(f'[PERF] JSON serialize: {t3-t2:.3f}s | TOTAL: {t3-t0:.3f}s')

        return response, 200
    except Exception as e:
        logger.error(f'[PERF] ERROR after {time.time()-t0:.3f}s: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pedido_bp.route('', methods=['GET'])
@login_required
@administrador_required
def get_todos_pedidos():
    """
    Obtener todos los pedidos con paginacion (solo administradores).
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
      - name: fecha_desde
        in: query
        type: string
        format: date
        required: false
      - name: fecha_hasta
        in: query
        type: string
        format: date
        required: false
      - name: cliente
        in: query
        type: string
        required: false
      - name: page
        in: query
        type: integer
        required: false
        default: 1
      - name: page_size
        in: query
        type: integer
        required: false
        default: 50
    responses:
      200:
        description: Lista paginada de todos los pedidos
    """
    t0 = time.time()
    empresa_id = session.get('empresa_id', '1')
    anyo = request.args.get('anyo', type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    cliente = request.args.get('cliente')
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 50, type=int), 200)

    logger.warning(f'[PERF] GET /api/pedidos empresa={empresa_id} anyo={anyo} cliente={cliente} page={page}')

    try:
        t1 = time.time()
        result = PedidoModel.get_all(
            empresa_id=empresa_id,
            anyo=anyo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            cliente=cliente,
            page=page,
            page_size=page_size
        )
        t2 = time.time()
        logger.warning(f'[PERF] DB query + fetch: {t2-t1:.3f}s | rows={len(result["pedidos"])}')

        response = jsonify({
            'success': True,
            'total': result['total'],
            'page': result['page'],
            'page_size': result['page_size'],
            'total_pages': result['total_pages'],
            'pedidos': result['pedidos']
        })
        t3 = time.time()
        logger.warning(f'[PERF] JSON serialize: {t3-t2:.3f}s | TOTAL: {t3-t0:.3f}s')

        return response, 200
    except Exception as e:
        logger.error(f'[PERF] ERROR after {time.time()-t0:.3f}s: {e}')
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
