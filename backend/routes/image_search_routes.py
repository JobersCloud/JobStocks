# ============================================================
# image_search_routes.py - Rutas para busqueda visual CBIR
# ============================================================

from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from models.image_search_model import ImageSearchModel, extract_features, EMBEDDING_VERSION
from models.stock_model import StockModel
from utils.auth import administrador_required, csrf_required
import threading
import base64
import logging
import numpy as np

logger = logging.getLogger(__name__)

image_search_bp = Blueprint('image_search', __name__)

# Estado de reindexacion global
_reindex_status = {'running': False, 'progress': 0, 'total': 0, 'error': None, 'errors_count': 0}


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
        connection_id = session.get('connection')

        # Auto-indexar imagenes nuevas antes de buscar (si hay pocas)
        try:
            indexed = ImageSearchModel.get_embedding_count(empresa_id)
            total_img = ImageSearchModel.get_total_images(empresa_id)
            new_count = total_img - indexed
            if new_count > 0 and new_count <= 50:
                # Pocas nuevas: indexar sincrono (rapido)
                logger.info(f'Auto-indexing {new_count} new images before search')
                ImageSearchModel.index_new_images(empresa_id, connection_id=connection_id)
            elif new_count > 50:
                logger.info(f'{new_count} new images pending, skipping auto-index (use Control BD)')
        except Exception as e:
            logger.warning(f'Auto-index check failed: {e}')

        # Buscar similares
        try:
            results = ImageSearchModel.search(query_vector, empresa_id=empresa_id, top_k=top_k)
        except ValueError as ve:
            error_msg = str(ve)
            if 'REINDEX_NEEDED' in error_msg:
                return jsonify({
                    'success': False,
                    'error': 'Es necesario reindexar las imagenes. Ve a Control BD y pulsa "Reindexar".',
                    'needs_reindex': True
                }), 409
            raise

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

    # Verificar si los embeddings necesitan reindexarse
    version_mismatch = False
    if indexed > 0:
        version_mismatch = ImageSearchModel.check_version_mismatch(empresa_id)

    resp = {
        'success': True,
        'indexed': indexed,
        'total': total,
        'reindexing': _reindex_status['running'],
        'progress': _reindex_status.get('progress', 0),
        'reindex_total': _reindex_status.get('total', 0),
        'embedding_version': EMBEDDING_VERSION,
        'needs_reindex': version_mismatch,
        'last_reindex_error': _reindex_status.get('error'),
        'last_reindex_errors_count': _reindex_status.get('errors_count', 0)
    }
    return jsonify(resp)


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

    # Invalidar cache inmediatamente para evitar usar embeddings viejos
    cache_key = empresa_id or '_all'
    with ImageSearchModel._cache_lock:
        ImageSearchModel._cache.pop(cache_key, None)
    logger.info(f'Cache invalidated for empresa_id={empresa_id} before reindex')

    # Marcar running=True ANTES de lanzar el thread (evitar race condition con poll)
    _reindex_status = {'running': True, 'progress': 0, 'total': 0, 'error': None, 'errors_count': 0}

    def _progress_callback(indexed, total_images, errors_count):
        """Actualizar progreso en tiempo real para que el poll lo vea."""
        global _reindex_status
        _reindex_status = {
            'running': True, 'progress': indexed, 'total': total_images,
            'error': None, 'errors_count': errors_count
        }

    def _reindex_thread():
        global _reindex_status
        try:
            logger.info(f'Reindex thread started: empresa_id={empresa_id}, connection_id={connection_id}')

            count, errors_count = ImageSearchModel.reindex(
                empresa_id, connection_id=connection_id,
                progress_callback=_progress_callback
            )
            logger.info(f'Reindex complete: {count} indexed, {errors_count} errors')
            _reindex_status = {'running': False, 'progress': count, 'total': count, 'error': None, 'errors_count': errors_count}
        except Exception as e:
            logger.error(f'Reindex failed: {e}', exc_info=True)
            _reindex_status = {'running': False, 'progress': 0, 'total': 0, 'error': str(e), 'errors_count': 0}

    thread = threading.Thread(target=_reindex_thread, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'message': 'Reindexing started in background'
    })


@image_search_bp.route('/api/image-search/debug', methods=['GET'])
@login_required
@administrador_required
def debug_embeddings():
    """Diagnostico de embeddings para debug."""
    empresa_id = session.get('empresa_id', '1')
    connection_id = session.get('connection')
    result = {'empresa_id': empresa_id, 'connection_id': connection_id}

    # 1. Test extract_features con imagen REAL de la BD
    try:
        conn = ImageSearchModel._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 id, codigo, DATALENGTH(imagen) as img_size, imagen FROM view_articulo_imagen")
        row = cursor.fetchone()
        conn.close()

        if row:
            result['test_image_id'] = row[0]
            result['test_image_codigo'] = row[1]
            result['test_image_bytes'] = row[2]

            if row[3]:
                vec = extract_features(bytes(row[3]))
                result['extract_features_ok'] = vec is not None
                result['expected_dims'] = len(vec) if vec is not None else None
            else:
                result['extract_features_ok'] = False
                result['extract_features_error'] = 'Image data is NULL'
        else:
            result['extract_features_ok'] = False
            result['extract_features_error'] = 'No images in view_articulo_imagen'
    except Exception as e:
        result['extract_features_ok'] = False
        result['extract_features_error'] = str(e)
        import traceback
        result['extract_features_traceback'] = traceback.format_exc()

    # 2. Check stored embeddings
    try:
        conn = ImageSearchModel._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM image_embeddings WHERE empresa_id = ?", [empresa_id])
        result['stored_count'] = cursor.fetchone()[0]

        cursor.execute("SELECT TOP 1 DATALENGTH(embedding) FROM image_embeddings WHERE empresa_id = ?", [empresa_id])
        row = cursor.fetchone()
        if row:
            byte_len = row[0]
            result['stored_dims'] = byte_len // 4
            result['stored_bytes'] = byte_len
        else:
            result['stored_dims'] = None

        conn.close()
    except Exception as e:
        result['db_error'] = str(e)

    # 3. Cache state
    cache_key = empresa_id or '_all'
    with ImageSearchModel._cache_lock:
        cached = ImageSearchModel._cache.get(cache_key)
    if cached:
        result['cache_count'] = len(cached)
        result['cache_dims'] = len(cached[0][2]) if cached else None
    else:
        result['cache_count'] = 0
        result['cache_dims'] = None

    # 4. Reindex status
    result['reindex_status'] = _reindex_status

    # 5. Test conexion con connection_id (la que usa el thread de reindex)
    try:
        conn = ImageSearchModel._get_conn(connection_id)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM view_articulo_imagen")
        count_via_connid = cursor.fetchone()[0]
        result['connection_id_works'] = True
        result['connection_id_image_count'] = count_via_connid
        conn.close()
    except Exception as e:
        result['connection_id_works'] = False
        result['connection_id_error'] = str(e)
        import traceback
        result['connection_id_traceback'] = traceback.format_exc()

    return jsonify(result)


@image_search_bp.route('/api/image-search/clear', methods=['POST'])
@login_required
@administrador_required
@csrf_required
def clear_embeddings():
    """Limpiar todos los embeddings y resetear estado."""
    global _reindex_status

    empresa_id = session.get('empresa_id', '1')

    # Forzar reset del estado de reindex (por si está atascado)
    _reindex_status = {'running': False, 'progress': 0, 'total': 0, 'error': None, 'errors_count': 0}

    # Limpiar BD
    ImageSearchModel.clear_embeddings(empresa_id)

    # Limpiar cache
    cache_key = empresa_id or '_all'
    with ImageSearchModel._cache_lock:
        ImageSearchModel._cache.pop(cache_key, None)

    logger.info(f'Embeddings cleared manually for empresa_id={empresa_id}')

    return jsonify({
        'success': True,
        'message': 'Embeddings eliminados. Ahora puedes reindexar.'
    })
