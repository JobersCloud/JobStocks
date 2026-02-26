# ============================================================
# image_search_routes.py - Rutas para busqueda visual CBIR
# ============================================================

from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from models.image_search_model import ImageSearchModel, extract_features
from models.stock_model import StockModel
from utils.auth import administrador_required, csrf_required
import threading
import base64
import logging

logger = logging.getLogger(__name__)

image_search_bp = Blueprint('image_search', __name__)

# Estado de reindexacion global
_reindex_status = {'running': False, 'progress': 0, 'total': 0}


@image_search_bp.route('/api/image-search/search', methods=['POST'])
@login_required
@csrf_required
def search_by_image():
    """
    Buscar productos similares por imagen
    ---
    tags:
      - Busqueda Visual
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            image:
              type: string
              description: Imagen en base64
            top_k:
              type: integer
              default: 20
    responses:
      200:
        description: Resultados de busqueda
    """
    data = request.get_json()
    if not data or not data.get('image'):
        return jsonify({'success': False, 'error': 'No image provided'}), 400

    try:
        # Decodificar imagen base64
        image_b64 = data['image']
        # Eliminar prefijo data:image/xxx;base64, si existe
        if ',' in image_b64:
            image_b64 = image_b64.split(',')[1]

        image_bytes = base64.b64decode(image_b64)
        top_k = data.get('top_k', 20)

        # Extraer features de la imagen de consulta
        query_vector = extract_features(image_bytes)
        if query_vector is None:
            return jsonify({'success': False, 'error': 'Could not process image'}), 400

        empresa_id = session.get('empresa_id', '1')

        # Buscar similares
        results = ImageSearchModel.search(query_vector, empresa_id=empresa_id, top_k=top_k)

        # Enriquecer resultados con datos de stock
        enrich_error = None
        codigos = []
        if results:
            codigos = [r['codigo'].strip() if isinstance(r['codigo'], str) else r['codigo'] for r in results if r.get('codigo')]
            try:
                from config.database import Database
                conn = Database.get_connection()
                cursor = conn.cursor()
                placeholders = ','.join(['?' for _ in codigos])
                sql = f"""
                    SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                           formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet,
                           existencias, ean13, pesocaja, pesopallet
                    FROM view_externos_stock
                    WHERE codigo IN ({placeholders})
                """
                cursor.execute(sql, codigos)
                rows = cursor.fetchall()

                stocks = {}
                for row in rows:
                    codigo = row[1].strip() if isinstance(row[1], str) else row[1]
                    if codigo not in stocks:
                        stocks[codigo] = {
                            'empresa': row[0], 'codigo': codigo,
                            'descripcion': row[2], 'calidad': row[3],
                            'color': row[4], 'tono': row[5], 'calibre': row[6],
                            'formato': row[7], 'serie': row[8], 'unidad': row[9],
                            'pallet': row[10], 'caja': row[11],
                            'unidadescaja': float(row[12]) if row[12] else 0,
                            'cajaspallet': float(row[13]) if row[13] else 0,
                            'existencias': float(row[14]) if row[14] else 0.0,
                            'ean13': row[15],
                            'pesocaja': float(row[16]) if row[16] else 0,
                            'pesopallet': float(row[17]) if row[17] else 0
                        }
                conn.close()

                for r in results:
                    codigo_key = r.get('codigo', '').strip() if isinstance(r.get('codigo'), str) else r.get('codigo')
                    stock = stocks.get(codigo_key)
                    if stock:
                        for key, val in stock.items():
                            r[key] = val
            except Exception as e:
                enrich_error = str(e)
                logger.error(f'Could not enrich: {e}', exc_info=True)

        resp = {
            'success': True,
            'results': results,
            'total': len(results)
        }
        if enrich_error:
            resp['enrich_error'] = enrich_error
        return jsonify(resp)

    except Exception as e:
        logger.error(f'Error in image search: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@image_search_bp.route('/api/image-search/status', methods=['GET'])
@login_required
def get_index_status():
    """
    Obtener estado de indexacion
    ---
    tags:
      - Busqueda Visual
    responses:
      200:
        description: Estado de la indexacion
    """
    empresa_id = session.get('empresa_id', '1')
    indexed = ImageSearchModel.get_embedding_count(empresa_id)
    total = ImageSearchModel.get_total_images(empresa_id)

    return jsonify({
        'success': True,
        'indexed': indexed,
        'total': total,
        'reindexing': _reindex_status['running'],
        'progress': _reindex_status['progress']
    })


@image_search_bp.route('/api/image-search/reindex', methods=['POST'])
@login_required
@administrador_required
@csrf_required
def reindex_images():
    """
    Iniciar reindexacion de imagenes (background)
    ---
    tags:
      - Busqueda Visual
    responses:
      200:
        description: Reindexacion iniciada
    """
    global _reindex_status

    if _reindex_status['running']:
        return jsonify({'success': False, 'error': 'Reindexing already in progress'}), 409

    empresa_id = session.get('empresa_id', '1')
    connection_id = session.get('connection')

    def _reindex_thread():
        global _reindex_status
        _reindex_status = {'running': True, 'progress': 0, 'total': 0}
        try:
            count = ImageSearchModel.reindex(empresa_id, connection_id=connection_id)
            _reindex_status = {'running': False, 'progress': count, 'total': count}
        except Exception as e:
            logger.error(f'Reindex failed: {e}')
            _reindex_status = {'running': False, 'progress': 0, 'total': 0}

    thread = threading.Thread(target=_reindex_thread, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'message': 'Reindexing started in background'
    })
