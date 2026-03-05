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
# Fecha : 2026-03-04
# ============================================================

# ============================================
# ARCHIVO: routes/favoritos_routes.py
# Endpoints para gestión de productos favoritos
# ============================================
import logging
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from utils.auth import csrf_required
from models.favoritos_model import FavoritosModel

logger = logging.getLogger(__name__)

favoritos_bp = Blueprint('favoritos', __name__, url_prefix='/api/favoritos')


def get_empresa_id():
    """Obtener empresa_id del request (query params, JSON body) o sesión"""
    empresa_id = request.args.get('empresa_id')
    if not empresa_id and request.is_json and request.json:
        empresa_id = request.json.get('empresa_id')
    result = empresa_id or session.get('empresa_id', '1')
    logger.debug(f"[favoritos] empresa_id: args={empresa_id}, session={session.get('empresa_id')}, result={result}")
    return result


@favoritos_bp.route('/toggle', methods=['POST'])
@login_required
@csrf_required
def toggle_favorito():
    """Toggle favorito on/off"""
    data = request.json

    if not data or not data.get('codigo'):
        return jsonify({
            'success': False,
            'error': 'Campo "codigo" es requerido'
        }), 400

    empresa_id = get_empresa_id()
    logger.info(f"[favoritos] TOGGLE user_id={current_user.id}, empresa_id={repr(empresa_id)}, codigo={repr(data['codigo'])}")

    try:
        result = FavoritosModel.toggle(current_user.id, empresa_id, data['codigo'])
        logger.info(f"[favoritos] TOGGLE result: is_favorite={result['is_favorite']}")
        return jsonify({
            'success': True,
            'is_favorite': result['is_favorite']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@favoritos_bp.route('', methods=['GET'])
@login_required
def listar_favoritos():
    """Lista favoritos con datos de stock"""
    empresa_id = get_empresa_id()
    logger.info(f"[favoritos] LIST user_id={current_user.id}, empresa_id={repr(empresa_id)}")

    try:
        favoritos = FavoritosModel.get_favorites_with_stock(current_user.id, empresa_id)
        logger.info(f"[favoritos] LIST result: {len(favoritos)} favoritos")
        return jsonify({
            'success': True,
            'favoritos': favoritos,
            'total': len(favoritos)
        })
    except Exception as e:
        logger.error(f"[favoritos] LIST error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@favoritos_bp.route('/check-batch', methods=['POST'])
@login_required
def check_batch():
    """Comprobar lote de códigos"""
    data = request.json

    if not data or not data.get('codigos'):
        return jsonify({
            'success': True,
            'favoritos': []
        })

    empresa_id = get_empresa_id()

    try:
        favoritos_set = FavoritosModel.check_batch(current_user.id, empresa_id, data['codigos'])
        return jsonify({
            'success': True,
            'favoritos': list(favoritos_set)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@favoritos_bp.route('/frequent', methods=['GET'])
@login_required
def productos_frecuentes():
    """Top 50 productos más pedidos por el usuario"""
    empresa_id = get_empresa_id()

    try:
        productos = FavoritosModel.get_frequent_products(current_user.id, empresa_id)
        return jsonify({
            'success': True,
            'productos': productos,
            'total': len(productos)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
