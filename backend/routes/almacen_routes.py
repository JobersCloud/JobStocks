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
# Fecha : 2026-02-12
# ============================================================

# ============================================
# ARCHIVO: routes/almacen_routes.py
# Descripcion: Rutas para vista almacen (ubicaciones 3D)
# ============================================
from flask import Blueprint, jsonify, request, session
from flask_login import login_required
from models.almacen_model import AlmacenModel
from utils.auth import administrador_required

almacen_bp = Blueprint('almacen', __name__)


def get_empresa_id():
    """Obtiene el empresa_id de la sesion."""
    return session.get('empresa_id', '1')


@almacen_bp.route('/api/almacen/almacenes', methods=['GET'])
@login_required
@administrador_required
def get_almacenes():
    """
    Obtener lista de almacenes disponibles
    ---
    tags:
      - Almacen
    security:
      - cookieAuth: []
    responses:
      200:
        description: Lista de almacenes
        schema:
          type: array
          items:
            type: string
    """
    empresa_id = get_empresa_id()
    try:
        almacenes = AlmacenModel.get_almacenes(empresa_id)
        return jsonify(almacenes)
    except Exception as e:
        print(f"Error en get_almacenes: {e}")
        return jsonify({'error': str(e)}), 500


@almacen_bp.route('/api/almacen/ubicaciones', methods=['GET'])
@login_required
@administrador_required
def get_ubicaciones():
    """
    Obtener ubicaciones de un almacen con estructura
    ---
    tags:
      - Almacen
    security:
      - cookieAuth: []
    parameters:
      - name: almacen
        in: query
        type: string
        required: true
        description: Codigo del almacen
    responses:
      200:
        description: Ubicaciones y estructura del almacen
    """
    empresa_id = get_empresa_id()
    almacen = request.args.get('almacen')

    if not almacen:
        return jsonify({'error': 'Se requiere parametro almacen'}), 400

    try:
        ubicaciones = AlmacenModel.get_ubicaciones(empresa_id, almacen)
        estructura = AlmacenModel.get_estructura(empresa_id, almacen)
        return jsonify({
            'ubicaciones': ubicaciones,
            'estructura': estructura
        })
    except Exception as e:
        print(f"Error en get_ubicaciones: {e}")
        return jsonify({'error': str(e)}), 500


@almacen_bp.route('/api/almacen/mapa', methods=['GET'])
@login_required
@administrador_required
def get_mapa():
    """
    Obtener mapa de ubicaciones del almacen (todos los huecos)
    ---
    tags:
      - Almacen
    security:
      - cookieAuth: []
    parameters:
      - name: almacen
        in: query
        type: string
        required: true
    responses:
      200:
        description: Mapa de ubicaciones con rangos de filas y alturas
    """
    empresa_id = get_empresa_id()
    almacen = request.args.get('almacen')

    if not almacen:
        return jsonify({'error': 'Se requiere parametro almacen'}), 400

    try:
        mapa = AlmacenModel.get_mapa(empresa_id, almacen)
        return jsonify(mapa)
    except Exception as e:
        print(f"Error en get_mapa: {e}")
        return jsonify({'error': str(e)}), 500


@almacen_bp.route('/api/almacen/resumen', methods=['GET'])
@login_required
@administrador_required
def get_resumen():
    """
    Obtener resumen estadistico de un almacen
    ---
    tags:
      - Almacen
    security:
      - cookieAuth: []
    parameters:
      - name: almacen
        in: query
        type: string
        required: true
        description: Codigo del almacen
    responses:
      200:
        description: Resumen del almacen
    """
    empresa_id = get_empresa_id()
    almacen = request.args.get('almacen')

    if not almacen:
        return jsonify({'error': 'Se requiere parametro almacen'}), 400

    try:
        resumen = AlmacenModel.get_resumen(empresa_id, almacen)
        return jsonify(resumen)
    except Exception as e:
        print(f"Error en get_resumen: {e}")
        return jsonify({'error': str(e)}), 500
