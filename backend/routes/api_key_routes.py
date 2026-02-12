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
# ARCHIVO: routes/api_key_routes.py
# ============================================
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from utils.auth import csrf_required
from models.api_key_model import ApiKeyModel

api_key_bp = Blueprint('api_keys', __name__, url_prefix='/api/api-keys')

@api_key_bp.route('', methods=['GET'])
@login_required
def get_api_keys():
    """
    Listar API keys del usuario
    ---
    tags:
      - API Keys
    security:
      - cookieAuth: []
    responses:
      200:
        description: Lista de API keys del usuario
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              api_key:
                type: string
                description: API key parcialmente oculta
              nombre:
                type: string
              activo:
                type: boolean
              fecha_creacion:
                type: string
              fecha_ultimo_uso:
                type: string
      401:
        description: No autenticado
    """
    keys = ApiKeyModel.get_by_user(current_user.id)
    return jsonify(keys), 200

@api_key_bp.route('', methods=['POST'])
@login_required
@csrf_required
def create_api_key():
    """
    Crear nueva API key
    ---
    tags:
      - API Keys
    security:
      - cookieAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nombre
          properties:
            nombre:
              type: string
              example: "Integración ERP"
              description: Nombre descriptivo para identificar la API key
    responses:
      201:
        description: API key creada
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            api_key:
              type: string
              description: API key completa (solo se muestra una vez)
      400:
        description: Nombre requerido
      401:
        description: No autenticado
    """
    data = request.get_json()
    nombre = data.get('nombre')

    if not nombre:
        return jsonify({
            'success': False,
            'message': 'El nombre es requerido'
        }), 400

    # Guardar la conexión actual para que la API Key herede el contexto de empresa
    connection = session.get('connection')
    api_key = ApiKeyModel.create(current_user.id, nombre, connection=connection)

    return jsonify({
        'success': True,
        'message': 'API key creada. Guárdala, no se mostrará de nuevo.',
        'api_key': api_key
    }), 201

@api_key_bp.route('/<int:key_id>', methods=['DELETE'])
@login_required
@csrf_required
def delete_api_key(key_id):
    """
    Eliminar API key
    ---
    tags:
      - API Keys
    security:
      - cookieAuth: []
    parameters:
      - name: key_id
        in: path
        type: integer
        required: true
        description: ID de la API key a eliminar
    responses:
      200:
        description: API key eliminada
      404:
        description: API key no encontrada
      401:
        description: No autenticado
    """
    deleted = ApiKeyModel.delete(key_id, current_user.id)

    if deleted:
        return jsonify({
            'success': True,
            'message': 'API key eliminada'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'API key no encontrada'
        }), 404

@api_key_bp.route('/<int:key_id>/deactivate', methods=['POST'])
@login_required
@csrf_required
def deactivate_api_key(key_id):
    """
    Desactivar API key
    ---
    tags:
      - API Keys
    security:
      - cookieAuth: []
    parameters:
      - name: key_id
        in: path
        type: integer
        required: true
        description: ID de la API key a desactivar
    responses:
      200:
        description: API key desactivada
      404:
        description: API key no encontrada
      401:
        description: No autenticado
    """
    deactivated = ApiKeyModel.deactivate(key_id, current_user.id)

    if deactivated:
        return jsonify({
            'success': True,
            'message': 'API key desactivada'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'API key no encontrada'
        }), 404
