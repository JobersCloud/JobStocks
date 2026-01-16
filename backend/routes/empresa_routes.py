# ============================================================
# ARCHIVO: routes/empresa_routes.py
# Rutas para gestión de empresa (inicialización y validación)
# ============================================================

from flask import Blueprint, jsonify, request, session
from models.empresa_cliente_model import EmpresaClienteModel
from utils.empresa import init_empresa_session, get_empresa_cli_id, get_empresa_info

empresa_bp = Blueprint('empresa', __name__, url_prefix='/api/empresa')


@empresa_bp.route('/init', methods=['POST'])
def init_empresa():
    """
    Inicializa la sesión con los datos de una empresa.

    Debe llamarse al cargar la aplicación con ?empresa=X

    Body:
        empresa_cli_id: ID de la empresa (de tabla empresa_cliente)

    Returns:
        200: Empresa inicializada correctamente
        400: Falta empresa_cli_id
        404: Empresa no encontrada
    """
    data = request.get_json() or {}
    empresa_cli_id = data.get('empresa_cli_id') or data.get('empresa')

    # También aceptar de query params
    if not empresa_cli_id:
        empresa_cli_id = request.args.get('empresa') or request.args.get('empresa_id')

    if not empresa_cli_id:
        return jsonify({
            'success': False,
            'error': 'Se requiere empresa_cli_id'
        }), 400

    # Inicializar sesión con datos de empresa
    empresa = init_empresa_session(empresa_cli_id)

    if not empresa:
        return jsonify({
            'success': False,
            'error': f'Empresa con ID {empresa_cli_id} no encontrada'
        }), 404

    return jsonify({
        'success': True,
        'empresa': {
            'empresa_cli_id': empresa.get('empresa_cli_id'),
            'nombre': empresa.get('nombre'),
            'empresa_erp': empresa.get('empresa_erp'),
            'cif': empresa.get('cif')
        }
    }), 200


@empresa_bp.route('/validate/<empresa_cli_id>', methods=['GET'])
def validate_empresa(empresa_cli_id):
    """
    Valida si una empresa existe (sin inicializar sesión).

    Args:
        empresa_cli_id: ID de la empresa

    Returns:
        200: Empresa válida con información básica
        404: Empresa no encontrada
    """
    empresa = EmpresaClienteModel.get_by_id(empresa_cli_id)

    if not empresa:
        return jsonify({
            'valid': False,
            'error': 'Empresa no encontrada'
        }), 404

    return jsonify({
        'valid': True,
        'empresa': {
            'empresa_cli_id': empresa.get('empresa_cli_id'),
            'nombre': empresa.get('nombre'),
            'empresa_erp': empresa.get('empresa_erp')
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
    empresa_cli_id = get_empresa_cli_id()

    if not empresa_cli_id:
        return jsonify({
            'success': False,
            'error': 'No hay empresa en sesión'
        }), 400

    empresa = get_empresa_info()

    if not empresa:
        return jsonify({
            'success': False,
            'error': 'Empresa no encontrada'
        }), 404

    return jsonify({
        'success': True,
        'empresa': {
            'empresa_cli_id': empresa.get('empresa_cli_id'),
            'nombre': empresa.get('nombre'),
            'empresa_erp': empresa.get('empresa_erp'),
            'cif': empresa.get('cif')
        },
        'session': {
            'empresa_cli_id': session.get('empresa_cli_id'),
            'empresa_erp': session.get('empresa_erp'),
            'empresa_nombre': session.get('empresa_nombre')
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
