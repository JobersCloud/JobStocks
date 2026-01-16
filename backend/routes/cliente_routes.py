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
# ARCHIVO: routes/cliente_routes.py
# ============================================
from flask import Blueprint
from utils.auth import api_key_or_login_required
from controllers.cliente_controller import ClienteController

cliente_bp = Blueprint('clientes', __name__)


@cliente_bp.route('/api/clientes', methods=['GET'])
@api_key_or_login_required
def get_all():
    """
    Obtener todos los clientes
    ---
    tags:
      - Clientes
    security:
      - apiKeyAuth: []
    parameters:
      - name: empresa
        in: query
        type: string
        description: Filtrar por empresa
        example: "1"
    responses:
      200:
        description: Lista de clientes
        schema:
          type: array
          items:
            type: object
            properties:
              empresa:
                type: string
                example: "1"
              codigo:
                type: string
                example: "CLI001"
              razon:
                type: string
                example: "Cliente Ejemplo S.L."
      401:
        description: No autenticado
      500:
        description: Error del servidor
    """
    return ClienteController.get_all()


@cliente_bp.route('/api/clientes/search', methods=['GET'])
@api_key_or_login_required
def search():
    """
    Buscar clientes con filtros
    ---
    tags:
      - Clientes
    security:
      - apiKeyAuth: []
    parameters:
      - name: empresa
        in: query
        type: string
        description: Filtrar por empresa
        example: "1"
      - name: razon
        in: query
        type: string
        description: Buscar por razón social (LIKE)
        example: "ejemplo"
    responses:
      200:
        description: Lista de clientes filtrados
        schema:
          type: array
          items:
            type: object
            properties:
              empresa:
                type: string
              codigo:
                type: string
              razon:
                type: string
      401:
        description: No autenticado
      500:
        description: Error del servidor
    """
    return ClienteController.search()


@cliente_bp.route('/api/clientes/<string:codigo>', methods=['GET'])
@api_key_or_login_required
def get_by_codigo(codigo):
    """
    Obtener cliente por código
    ---
    tags:
      - Clientes
    security:
      - apiKeyAuth: []
    parameters:
      - name: codigo
        in: path
        type: string
        required: true
        description: Código del cliente
        example: "CLI001"
      - name: empresa
        in: query
        type: string
        description: Filtrar por empresa
        example: "1"
    responses:
      200:
        description: Detalle del cliente
        schema:
          type: object
          properties:
            empresa:
              type: string
            codigo:
              type: string
            razon:
              type: string
      401:
        description: No autenticado
      404:
        description: Cliente no encontrado
      500:
        description: Error del servidor
    """
    return ClienteController.get_by_codigo(codigo)
