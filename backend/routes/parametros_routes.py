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
# ARCHIVO: routes/parametros_routes.py
# ============================================
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from utils.auth import csrf_required
from models.parametros_model import ParametrosModel
from utils.auth import administrador_required

parametros_bp = Blueprint('parametros', __name__)


def get_connection():
    """Obtiene el connection del request o sesión (ID para conexión)"""
    # Primero de la sesión
    connection = session.get('connection')
    if connection:
        return connection

    # Del query param
    connection = request.args.get('connection') or request.args.get('empresa')
    if connection:
        return connection

    # Del body JSON
    if request.is_json:
        data = request.get_json(silent=True)
        if data:
            connection = data.get('connection') or data.get('empresa')
            if connection:
                return connection

    return None


def get_empresa_id_from_connection(connection):
    """Obtiene el empresa_id desde el connection"""
    # Primero de la sesión
    empresa_id = session.get('empresa_id')
    if empresa_id:
        return empresa_id

    # Sino, de la BD central
    if connection:
        from models.empresa_cliente_model import EmpresaClienteModel
        empresa = EmpresaClienteModel.get_by_id(connection)
        if empresa:
            return empresa.get('empresa_erp')

    return None


def get_empresa_id():
    """Obtiene el empresa_id de la sesión o del request (para compatibilidad)"""
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    return empresa_id or connection or '1'

# ============================================
# ENDPOINTS PÚBLICOS (sin autenticación)
# ============================================

@parametros_bp.route('/propuestas-habilitadas', methods=['GET'])
def propuestas_habilitadas():
    """
    Verificar si las propuestas están habilitadas
    ---
    tags:
      - Parámetros
    parameters:
      - name: empresa_id
        in: query
        type: string
        required: false
    responses:
      200:
        description: Estado de las propuestas
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    habilitado = ParametrosModel.permitir_propuestas(empresa_id, connection)
    return jsonify({'habilitado': habilitado}), 200

@parametros_bp.route('/grid-con-imagenes', methods=['GET'])
def grid_con_imagenes():
    """
    Verificar si se deben mostrar imágenes en la tabla/tarjetas de stock
    ---
    tags:
      - Parámetros
    parameters:
      - name: empresa_id
        in: query
        type: string
        required: false
    responses:
      200:
        description: Estado del parámetro grid con imágenes
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    habilitado = ParametrosModel.grid_con_imagenes(empresa_id, connection)
    return jsonify({'habilitado': habilitado}), 200

# ============================================
# ENDPOINTS PROTEGIDOS (requieren admin)
# ============================================

@parametros_bp.route('', methods=['GET'])
@login_required
@administrador_required
def get_all_parametros():
    """
    Obtiene todos los parámetros del sistema
    ---
    tags:
      - Parámetros
    security:
      - session: []
    parameters:
      - name: empresa_id
        in: query
        type: string
        required: false
    responses:
      200:
        description: Lista de parámetros
        schema:
          type: object
          properties:
            parametros:
              type: array
              items:
                type: object
                properties:
                  clave:
                    type: string
                  valor:
                    type: string
                  descripcion:
                    type: string
                  fecha_modificacion:
                    type: string
    """
    empresa_id = get_empresa_id()
    connection = get_connection()
    parametros = ParametrosModel.get_all(empresa_id, connection)
    return jsonify({'parametros': parametros})

@parametros_bp.route('/<clave>', methods=['GET'])
@login_required
@administrador_required
def get_parametro(clave):
    """
    Obtiene un parámetro específico
    ---
    tags:
      - Parámetros
    security:
      - session: []
    parameters:
      - name: clave
        in: path
        type: string
        required: true
      - name: empresa_id
        in: query
        type: string
        required: false
    responses:
      200:
        description: Parámetro encontrado
      404:
        description: Parámetro no encontrado
    """
    empresa_id = get_empresa_id()
    connection = get_connection()
    valor = ParametrosModel.get(clave, empresa_id, connection)
    if valor is None:
        return jsonify({'error': 'Parámetro no encontrado'}), 404

    return jsonify({
        'clave': clave,
        'valor': valor
    })

@parametros_bp.route('/<clave>', methods=['PUT'])
@login_required
@csrf_required
@administrador_required
def update_parametro(clave):
    """
    Actualiza el valor de un parámetro
    ---
    tags:
      - Parámetros
    security:
      - session: []
    parameters:
      - name: clave
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            valor:
              type: string
              description: Nuevo valor del parámetro
            empresa_id:
              type: string
    responses:
      200:
        description: Parámetro actualizado
      400:
        description: Valor no proporcionado
      404:
        description: Parámetro no encontrado
    """
    data = request.get_json()

    if 'valor' not in data:
        return jsonify({'error': 'El campo valor es requerido'}), 400

    nuevo_valor = data['valor']
    empresa_id = data.get('empresa_id') or get_empresa_id()

    # Verificar que el parámetro existe
    connection = get_connection()
    valor_actual = ParametrosModel.get(clave, empresa_id, connection)
    if valor_actual is None:
        return jsonify({'error': 'Parámetro no encontrado'}), 404

    success = ParametrosModel.set(clave, nuevo_valor, empresa_id, connection)

    if success:
        return jsonify({
            'message': 'Parámetro actualizado correctamente',
            'clave': clave,
            'valor': nuevo_valor
        })
    else:
        return jsonify({'error': 'Error al actualizar el parámetro'}), 500
