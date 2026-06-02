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
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from utils.auth import api_key_or_login_required, get_clientes_comercial
from controllers.cliente_controller import ClienteController
from config.database import Database

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


@cliente_bp.route('/api/comercial/mis-clientes', methods=['GET'])
@login_required
def get_mis_clientes():
    """Obtener clientes asignados al comercial del usuario actual."""
    control = getattr(current_user, 'control', None)
    admin_clientes = getattr(current_user, 'administrador_clientes', False)
    if not admin_clientes or not control:
        return jsonify({'success': False, 'message': 'No tiene clientes asignados'}), 403

    empresa_id = session.get('empresa_id', '1')
    clientes_ids = get_clientes_comercial(control, empresa_id)
    if not clientes_ids:
        return jsonify({'success': True, 'clientes': [], 'total': 0})

    try:
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            placeholders = ','.join(['?' for _ in clientes_ids])
            cursor.execute(f"""
                SELECT RTRIM(codigo) as codigo, RTRIM(razon) as razon,
                       RTRIM(ISNULL(domicilio,'')) as domicilio,
                       RTRIM(ISNULL(codpos,'')) as codpos,
                       RTRIM(ISNULL(poblacion,'')) as poblacion,
                       RTRIM(ISNULL(provincia,'')) as provincia,
                       RTRIM(ISNULL(pais,'')) as pais
                FROM view_externos_clientes
                WHERE empresa = ? AND codigo IN ({placeholders})
                ORDER BY razon
            """, [empresa_id] + clientes_ids)
            rows = cursor.fetchall()
            clientes = [{
                'codigo': row[0], 'razon': row[1], 'domicilio': row[2],
                'codpos': row[3], 'poblacion': row[4], 'provincia': row[5], 'pais': row[6]
            } for row in rows]
            return jsonify({'success': True, 'clientes': clientes, 'total': len(clientes)})
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cliente_bp.route('/api/comerciales', methods=['GET'])
@login_required
def get_comerciales():
    """Buscar comerciales disponibles (para autocomplete en usuarios)."""
    q = request.args.get('q', '').strip()
    empresa_id = session.get('empresa_id', '1')
    try:
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            if q:
                cursor.execute("""
                    SELECT DISTINCT RTRIM(control) as control, RTRIM(nombre) as nombre
                    FROM view_comerciales
                    WHERE empresa = ? AND (RTRIM(control) LIKE ? OR RTRIM(nombre) LIKE ?)
                    ORDER BY nombre
                """, (empresa_id, f'%{q}%', f'%{q}%'))
            else:
                cursor.execute("""
                    SELECT DISTINCT RTRIM(control) as control, RTRIM(nombre) as nombre
                    FROM view_comerciales
                    WHERE empresa = ?
                    ORDER BY nombre
                """, (empresa_id,))
            rows = cursor.fetchall()
            return jsonify([{'control': row[0], 'nombre': row[1]} for row in rows])
        finally:
            cursor.close()
            conn.close()
    except Exception:
        return jsonify([])
