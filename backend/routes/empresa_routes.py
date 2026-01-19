# ============================================================
# ARCHIVO: routes/empresa_routes.py
# Rutas para gestión de empresa (inicialización y validación)
# ============================================================

from flask import Blueprint, jsonify, request, session
from models.empresa_cliente_model import EmpresaClienteModel
from models.empresa_model import EmpresaModel
from utils.empresa import init_empresa_session, get_connection, get_empresa_info

empresa_bp = Blueprint('empresa', __name__, url_prefix='/api/empresa')


@empresa_bp.route('/init', methods=['POST'])
def init_empresa():
    """
    Inicializa la sesión con los datos de una empresa.

    Debe llamarse al cargar la aplicación con ?empresa=X

    Body:
        connection: ID de la empresa (de tabla empresa_cliente)

    Returns:
        200: Empresa inicializada correctamente
        400: Falta connection
        404: Empresa no encontrada
    """
    data = request.get_json() or {}
    connection = data.get('connection') or data.get('empresa_cli_id') or data.get('empresa')

    # También aceptar de query params
    if not connection:
        connection = request.args.get('empresa') or request.args.get('connection')

    if not connection:
        return jsonify({
            'success': False,
            'error': 'Se requiere connection (empresa_cli_id)'
        }), 400

    # Inicializar sesión con datos de empresa
    empresa = init_empresa_session(connection)

    if not empresa:
        return jsonify({
            'success': False,
            'error': f'Empresa con ID {connection} no encontrada'
        }), 404

    return jsonify({
        'success': True,
        'empresa': {
            'connection': empresa.get('empresa_cli_id'),
            'nombre': empresa.get('nombre'),
            'empresa_id': empresa.get('empresa_erp'),
            'cif': empresa.get('cif')
        }
    }), 200


@empresa_bp.route('/validate/<connection>', methods=['GET'])
def validate_empresa(connection):
    """
    Valida si una empresa existe (sin inicializar sesión).

    Args:
        connection: ID de la empresa

    Returns:
        200: Empresa válida con información básica
        404: Empresa no encontrada
    """
    empresa = EmpresaClienteModel.get_by_id(connection)

    if not empresa:
        return jsonify({
            'valid': False,
            'error': 'Empresa no encontrada'
        }), 404

    return jsonify({
        'valid': True,
        'empresa': {
            'connection': empresa.get('empresa_cli_id'),
            'nombre': empresa.get('nombre'),
            'empresa_id': empresa.get('empresa_erp')
        }
    }), 200


@empresa_bp.route('/current', methods=['GET'])
def current_empresa():
    """
    Obtiene la información de la empresa actual en sesión.

    Returns:
        200: Información de la empresa
        400: No hay empresa en sesión
    """
    connection = get_connection()

    if not connection:
        return jsonify({
            'success': False,
            'error': 'No hay empresa en sesión'
        }), 400

    # Obtener info básica (conn string, etc)
    empresa = get_empresa_info()
    
    # Obtener info detallada de la vista (nombre real)
    empresa_id = empresa.get('empresa_erp')
    empresa_nombre = empresa.get('nombre') # default del registro maestro
    
    if empresa_id:
        print(f"[DEBUG] Buscando detalle empresa para id: {empresa_id} en connection: {connection}")
        empresa_detalle = EmpresaModel.get_by_id(empresa_id, connection)
        if empresa_detalle and empresa_detalle.get('nombre'):
            print(f"[DEBUG] Nombre encontrado en vista: {empresa_detalle.get('nombre')}")
            empresa_nombre = empresa_detalle.get('nombre')

    if not empresa:
        return jsonify({
            'success': False,
            'error': 'Empresa no encontrada'
        }), 404

    return jsonify({
        'success': True,
        'empresa': {
            'connection': empresa.get('empresa_cli_id'),
            'nombre': empresa_nombre,
            'empresa_id': empresa.get('empresa_erp'),
            'cif': empresa.get('cif')
        },
        'session': {
            'connection': session.get('connection'),
            'empresa_id': session.get('empresa_id'),
            'empresa_nombre': session.get('empresa_nombre')
        },
        'debug_info': {
            'empresa_erp_central': empresa.get('empresa_erp'),
            'origen_nombre': 'vista_cliente' if empresa_nombre != empresa.get('nombre') else 'central_db'
        }
    }), 200


@empresa_bp.route('/list', methods=['GET'])
def list_empresas():
    """
    Lista todas las empresas disponibles (para administración).

    Returns:
        200: Lista de empresas
    """
    empresas = EmpresaClienteModel.get_all()

    return jsonify({
        'success': True,
        'empresas': empresas
    }), 200
