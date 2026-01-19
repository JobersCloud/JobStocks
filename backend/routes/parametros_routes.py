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
from models.parametros_model import ParametrosModel
from utils.auth import administrador_required

parametros_bp = Blueprint('parametros', __name__)


def get_empresa_cli_id():
    """Obtiene el empresa_cli_id del request o sesión (ID para conexión)"""
    # Primero de la sesión
    empresa_cli_id = session.get('empresa_cli_id')
    if empresa_cli_id:
        return empresa_cli_id

    # Del query param
    empresa_cli_id = request.args.get('empresa_id') or request.args.get('empresa')
    if empresa_cli_id:
        return empresa_cli_id

    # Del body JSON
    if request.is_json:
        data = request.get_json(silent=True)
        if data:
            empresa_cli_id = data.get('empresa_id') or data.get('empresa')
            if empresa_cli_id:
                return empresa_cli_id

    return None


def get_empresa_erp(empresa_cli_id):
    """Obtiene el empresa_erp desde el empresa_cli_id"""
    # Primero de la sesión
    empresa_erp = session.get('empresa_erp')
    if empresa_erp:
        return empresa_erp

    # Sino, de la BD central
    if empresa_cli_id:
        from models.empresa_cliente_model import EmpresaClienteModel
        empresa = EmpresaClienteModel.get_by_id(empresa_cli_id)
        if empresa:
            return empresa.get('empresa_erp')

    return None


def get_empresa_id():
    """Obtiene el empresa_id de la sesión o del request (para compatibilidad)"""
    empresa_cli_id = get_empresa_cli_id()
    empresa_erp = get_empresa_erp(empresa_cli_id)
    return empresa_erp or empresa_cli_id or '1'

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
    empresa_cli_id = get_empresa_cli_id()
    empresa_erp = get_empresa_erp(empresa_cli_id)
    habilitado = ParametrosModel.permitir_propuestas(empresa_erp, empresa_cli_id)
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
    empresa_cli_id = get_empresa_cli_id()
    empresa_erp = get_empresa_erp(empresa_cli_id)
    habilitado = ParametrosModel.grid_con_imagenes(empresa_erp, empresa_cli_id)
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
    parametros = ParametrosModel.get_all(empresa_id)
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
    valor = ParametrosModel.get(clave, empresa_id)
    if valor is None:
        return jsonify({'error': 'Parámetro no encontrado'}), 404

    return jsonify({
        'clave': clave,
        'valor': valor
    })

@parametros_bp.route('/<clave>', methods=['PUT'])
@login_required
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
    valor_actual = ParametrosModel.get(clave, empresa_id)
    if valor_actual is None:
        return jsonify({'error': 'Parámetro no encontrado'}), 404

    success = ParametrosModel.set(clave, nuevo_valor, empresa_id)

    if success:
        return jsonify({
            'message': 'Parámetro actualizado correctamente',
            'clave': clave,
            'valor': nuevo_valor
        })
    else:
        return jsonify({'error': 'Error al actualizar el parámetro'}), 500
