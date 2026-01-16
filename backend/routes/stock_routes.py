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
# ARCHIVO: routes/stock_routes.py
# ============================================
from flask import Blueprint, jsonify, request, session, Response
from flask_login import current_user
from utils.auth import api_key_or_login_required
from controllers.stock_controller import StockController
from models.imagen_model import ImagenModel
from models.ficha_tecnica_model import FichaTecnicaModel

stock_bp = Blueprint('stocks', __name__)

# Definir las rutas (protegidas con sesión o API key)
@stock_bp.route('/api/stocks', methods=['GET'])
@api_key_or_login_required
def get_all():
    """
    Obtener todos los stocks
    ---
    tags:
      - Stocks
    security:
      - apiKeyAuth: []
    responses:
      200:
        description: Lista de todos los stocks
        schema:
          type: array
          items:
            type: object
            properties:
              empresa:
                type: string
              codigo:
                type: string
              descripcion:
                type: string
              formato:
                type: string
              serie:
                type: string
              calidad:
                type: string
              color:
                type: string
              tono:
                type: string
              calibre:
                type: string
              existencias:
                type: number
              unidad:
                type: string
      401:
        description: No autenticado
      500:
        description: Error del servidor
    """
    return StockController.get_all()

@stock_bp.route('/api/stocks/search', methods=['GET'])
@api_key_or_login_required
def search():
    """
    Buscar stocks con filtros
    ---
    tags:
      - Stocks
    security:
      - apiKeyAuth: []
    parameters:
      - name: formato
        in: query
        type: string
        description: Filtrar por formato
        example: "20x20"
      - name: serie
        in: query
        type: string
        description: Filtrar por serie/modelo
      - name: calidad
        in: query
        type: string
        description: Filtrar por calidad
        example: "Primera"
      - name: color
        in: query
        type: string
        description: Filtrar por color
      - name: existencias_min
        in: query
        type: number
        description: Existencias mínimas
        example: 100
    responses:
      200:
        description: Lista de stocks filtrados
        schema:
          type: array
          items:
            type: object
            properties:
              empresa:
                type: string
              codigo:
                type: string
              descripcion:
                type: string
              formato:
                type: string
              calidad:
                type: string
              color:
                type: string
              existencias:
                type: number
              unidad:
                type: string
      401:
        description: No autenticado
      500:
        description: Error del servidor
    """
    return StockController.search()

@stock_bp.route('/api/stocks/resumen', methods=['GET'])
@api_key_or_login_required
def get_resumen():
    """
    Obtener resumen estadístico de stocks
    ---
    tags:
      - Stocks
    security:
      - apiKeyAuth: []
    responses:
      200:
        description: Estadísticas del inventario
        schema:
          type: object
          properties:
            total_productos:
              type: integer
              example: 5133
            total_existencias:
              type: number
              example: 250000.50
            promedio_existencias:
              type: number
              example: 48.70
            minimo_existencias:
              type: number
              example: 0
            maximo_existencias:
              type: number
              example: 5000
      401:
        description: No autenticado
      500:
        description: Error del servidor
    """
    return StockController.get_resumen()

@stock_bp.route('/api/stocks/<string:codigo>', methods=['GET'])
@api_key_or_login_required
def get_by_codigo(codigo):
    """
    Obtener stock por código
    ---
    tags:
      - Stocks
    security:
      - apiKeyAuth: []
    parameters:
      - name: codigo
        in: path
        type: string
        required: true
        description: Código del producto
    responses:
      200:
        description: Detalle del producto
        schema:
          type: object
          properties:
            empresa:
              type: string
            codigo:
              type: string
            descripcion:
              type: string
            formato:
              type: string
            serie:
              type: string
            calidad:
              type: string
            color:
              type: string
            tono:
              type: string
            calibre:
              type: string
            pallet:
              type: string
            caja:
              type: string
            existencias:
              type: number
            unidad:
              type: string
      401:
        description: No autenticado
      404:
        description: Producto no encontrado
      500:
        description: Error del servidor
    """
    return StockController.get_by_codigo(codigo)


@stock_bp.route('/api/stocks/<string:codigo>/imagenes', methods=['GET'])
@api_key_or_login_required
def get_imagenes(codigo):
    """
    Obtener imágenes de un artículo
    ---
    tags:
      - Stocks
    security:
      - apiKeyAuth: []
    parameters:
      - name: codigo
        in: path
        type: string
        required: true
        description: Código del producto
    responses:
      200:
        description: Lista de imágenes del artículo (base64)
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              codigo:
                type: string
              imagen:
                type: string
                description: Imagen codificada en base64
      401:
        description: No autenticado
      500:
        description: Error del servidor
    """
    try:
        imagenes = ImagenModel.get_by_codigo(codigo)
        return jsonify(imagenes), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/stocks/<string:codigo>/thumbnail', methods=['GET'])
@api_key_or_login_required
def get_thumbnail(codigo):
    """
    Obtener la primera imagen de un artículo (thumbnail para grid)
    ---
    tags:
      - Stocks
    security:
      - apiKeyAuth: []
    parameters:
      - name: codigo
        in: path
        type: string
        required: true
        description: Código del producto
    responses:
      200:
        description: Primera imagen del artículo (base64)
        schema:
          type: object
          properties:
            id:
              type: integer
            codigo:
              type: string
            imagen:
              type: string
              description: Imagen codificada en base64
      404:
        description: No hay imagen para este artículo
      401:
        description: No autenticado
      500:
        description: Error del servidor
    """
    try:
        imagen = ImagenModel.get_primera_imagen(codigo)
        if imagen:
            return jsonify(imagen), 200
        else:
            return jsonify({'error': 'No hay imagen disponible'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/stocks/thumbnails', methods=['POST'])
@api_key_or_login_required
def get_thumbnails_batch():
    """
    Obtener thumbnails de múltiples artículos en una sola petición (batch loading)
    ---
    tags:
      - Stocks
    security:
      - apiKeyAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            codigos:
              type: array
              items:
                type: string
              description: Lista de códigos de productos
    responses:
      200:
        description: Diccionario con thumbnails {codigo: imagen_base64}
        schema:
          type: object
          additionalProperties:
            type: string
      400:
        description: Parámetros inválidos
      401:
        description: No autenticado
      500:
        description: Error del servidor
    """
    try:
        data = request.get_json()
        if not data or 'codigos' not in data:
            return jsonify({'error': 'Se requiere el campo "codigos" con un array de códigos'}), 400

        codigos = data['codigos']
        if not isinstance(codigos, list):
            return jsonify({'error': 'El campo "codigos" debe ser un array'}), 400

        # Limitar a 50 códigos por petición para evitar sobrecarga
        if len(codigos) > 50:
            codigos = codigos[:50]

        thumbnails = ImagenModel.get_thumbnails_batch(codigos)
        return jsonify(thumbnails), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_empresa_id():
    """Obtiene el empresa_id del contexto actual."""
    if hasattr(current_user, 'empresa_id') and current_user.empresa_id:
        return current_user.empresa_id
    if 'empresa_id' in session:
        return session['empresa_id']
    return request.args.get('empresa_id', '1')


@stock_bp.route('/api/stocks/<string:codigo>/ficha-tecnica/exists', methods=['GET'])
@api_key_or_login_required
def check_ficha_tecnica(codigo):
    """
    Verificar si existe ficha tecnica para un articulo
    ---
    tags:
      - Stocks
    security:
      - apiKeyAuth: []
      - cookieAuth: []
    parameters:
      - name: codigo
        in: path
        type: string
        required: true
        description: Codigo del articulo
    responses:
      200:
        description: Resultado de la verificacion
        schema:
          type: object
          properties:
            exists:
              type: boolean
              description: True si existe ficha tecnica
      401:
        description: No autenticado
      500:
        description: Error del servidor
    """
    try:
        empresa_id = get_empresa_id()
        exists = FichaTecnicaModel.exists(codigo, empresa_id)
        return jsonify({'exists': exists}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/stocks/<string:codigo>/ficha-tecnica', methods=['GET'])
@api_key_or_login_required
def get_ficha_tecnica(codigo):
    """
    Obtener ficha tecnica de un articulo (PDF)
    ---
    tags:
      - Stocks
    security:
      - apiKeyAuth: []
      - cookieAuth: []
    parameters:
      - name: codigo
        in: path
        type: string
        required: true
        description: Codigo del articulo
      - name: download
        in: query
        type: boolean
        default: false
        description: Si es true, descarga el PDF directamente
    responses:
      200:
        description: Ficha tecnica del articulo
        schema:
          type: object
          properties:
            empresa:
              type: string
            articulo:
              type: string
            ficha:
              type: string
              description: PDF codificado en base64
      404:
        description: Ficha tecnica no encontrada
      401:
        description: No autenticado
      500:
        description: Error del servidor
    """
    try:
        empresa_id = get_empresa_id()
        ficha = FichaTecnicaModel.get_by_codigo(codigo, empresa_id)

        if not ficha:
            return jsonify({'error': 'Ficha tecnica no encontrada'}), 404

        # Si se solicita descarga directa, devolver el PDF como archivo
        download = request.args.get('download', 'false').lower() == 'true'
        if download:
            import base64
            pdf_data = base64.b64decode(ficha['ficha'])
            return Response(
                pdf_data,
                mimetype='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename=ficha_tecnica_{codigo}.pdf'
                }
            )

        return jsonify(ficha), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
