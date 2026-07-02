# ============================================
# ARCHIVO: routes/stock_anulados_routes.py
# Rutas para stocks anulados (artículos descatalogados con existencias)
# ============================================
from flask import Blueprint, jsonify, request
from utils.auth import api_key_or_login_required
from models.stock_anulados_model import StockAnuladosModel
from models.imagen_model import ImagenModel

stock_anulados_bp = Blueprint('stocks_anulados', __name__)


@stock_anulados_bp.route('/api/stocks-anulados', methods=['GET'])
@api_key_or_login_required
def get_all():
    """
    Obtener todos los stocks anulados
    ---
    tags:
      - Stocks Anulados
    responses:
      200:
        description: Lista de stocks anulados
    """
    try:
        stocks = StockAnuladosModel.get_all()
        return jsonify(stocks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_anulados_bp.route('/api/stocks-anulados/search', methods=['GET'])
@api_key_or_login_required
def search():
    """
    Buscar stocks anulados con filtros, paginación y ordenación
    ---
    tags:
      - Stocks Anulados
    responses:
      200:
        description: Stocks anulados filtrados
    """
    try:
        filtros = {}
        for key in request.args:
            if key not in ('page', 'limit', 'order_by', 'order_dir'):
                filtros[key] = request.args.get(key)

        page = request.args.get('page', type=int)
        limit = request.args.get('limit', type=int)
        order_by = request.args.get('order_by', 'codigo')
        order_dir = request.args.get('order_dir', 'ASC')

        result = StockAnuladosModel.search(filtros, page, limit, order_by, order_dir)

        if isinstance(result, dict):
            return jsonify(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_anulados_bp.route('/api/stocks-anulados/<codigo>', methods=['GET'])
@api_key_or_login_required
def get_by_codigo(codigo):
    """
    Obtener stock anulado por código
    ---
    tags:
      - Stocks Anulados
    parameters:
      - name: codigo
        in: path
        type: string
        required: true
    responses:
      200:
        description: Stock anulado encontrado
      404:
        description: No encontrado
    """
    try:
        stock = StockAnuladosModel.get_by_codigo(codigo)
        if stock:
            return jsonify(stock)
        return jsonify({'error': 'Producto no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_anulados_bp.route('/api/stocks-anulados/<codigo>/imagenes', methods=['GET'])
@api_key_or_login_required
def get_imagenes(codigo):
    """
    Obtener imágenes de un artículo anulado
    ---
    tags:
      - Stocks Anulados
    """
    try:
        imagenes = ImagenModel.get_by_codigo(codigo)
        return jsonify(imagenes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
