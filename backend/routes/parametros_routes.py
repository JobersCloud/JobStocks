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
from utils.auth import csrf_required, api_key_or_login_required
from models.parametros_model import ParametrosModel
from utils.auth import administrador_required, superusuario_required
from datetime import datetime

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


@parametros_bp.route('/firma-habilitada', methods=['GET'])
def firma_habilitada():
    """
    Verificar si la firma de propuestas está habilitada
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
        description: Estado de la firma de propuestas
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    habilitado = ParametrosModel.permitir_firma(empresa_id, connection)
    return jsonify({'habilitado': habilitado}), 200


@parametros_bp.route('/busqueda-voz-habilitada', methods=['GET'])
def busqueda_voz_habilitada():
    """
    Verificar si la búsqueda por voz está habilitada
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
        description: Estado de la búsqueda por voz
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    habilitado = ParametrosModel.permitir_busqueda_voz(empresa_id, connection)
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


@parametros_bp.route('/mostrar-precios', methods=['GET'])
def mostrar_precios():
    """
    Verificar si se deben mostrar precios de artículos.
    Para ver precios, AMBOS deben estar activos: parámetro global de empresa Y flag del usuario.
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
        description: Estado del parámetro mostrar precios
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
            global_habilitado:
              type: boolean
              description: Si el parámetro global de empresa está activo
    """
    from flask_login import current_user as cu
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    global_habilitado = ParametrosModel.mostrar_precios(empresa_id, connection)

    # Si hay usuario logueado, comprobar también su flag mostrar_precios
    habilitado = global_habilitado
    if global_habilitado and cu and cu.is_authenticated:
        habilitado = getattr(cu, 'mostrar_precios', False)

    return jsonify({
        'habilitado': habilitado,
        'global_habilitado': global_habilitado
    }), 200


@parametros_bp.route('/visible-pedidos', methods=['GET'])
def visible_pedidos():
    """
    Verificar si la sección Mis Pedidos es visible.
    Para ver pedidos, AMBOS deben estar activos: parámetro global de empresa Y flag del usuario.
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
        description: Estado del parámetro visible pedidos
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
            global_habilitado:
              type: boolean
              description: Si el parámetro global de empresa está activo
    """
    from flask_login import current_user as cu
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    global_habilitado = ParametrosModel.visible_pedidos(empresa_id, connection)

    # Admins/superusuarios siempre ven si el global está activo; usuarios normales necesitan flag individual
    habilitado = global_habilitado
    if global_habilitado and cu and cu.is_authenticated:
        rol = getattr(cu, 'rol', 'usuario')
        if rol in ('administrador', 'superusuario'):
            habilitado = True
        else:
            habilitado = getattr(cu, 'visible_pedidos', False)

    return jsonify({
        'habilitado': habilitado,
        'global_habilitado': global_habilitado
    }), 200


@parametros_bp.route('/visible-albaranes', methods=['GET'])
def visible_albaranes():
    """
    Verificar si la sección Albaranes es visible.
    Para ver albaranes, AMBOS deben estar activos: parámetro global de empresa Y flag del usuario.
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
        description: Estado del parámetro visible albaranes
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
            global_habilitado:
              type: boolean
              description: Si el parámetro global de empresa está activo
    """
    from flask_login import current_user as cu
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    global_habilitado = ParametrosModel.visible_albaranes(empresa_id, connection)

    # Admins/superusuarios siempre ven si el global está activo; usuarios normales necesitan flag individual
    habilitado = global_habilitado
    if global_habilitado and cu and cu.is_authenticated:
        rol = getattr(cu, 'rol', 'usuario')
        if rol in ('administrador', 'superusuario'):
            habilitado = True
        else:
            habilitado = getattr(cu, 'visible_albaranes', False)

    return jsonify({
        'habilitado': habilitado,
        'global_habilitado': global_habilitado
    }), 200


@parametros_bp.route('/visible-facturas', methods=['GET'])
def visible_facturas():
    """
    Verificar si la sección Facturas es visible.
    Para ver facturas, AMBOS deben estar activos: parámetro global de empresa Y flag del usuario.
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
        description: Estado del parámetro visible facturas
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
            global_habilitado:
              type: boolean
              description: Si el parámetro global de empresa está activo
    """
    from flask_login import current_user as cu
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    global_habilitado = ParametrosModel.visible_facturas(empresa_id, connection)

    # Admins/superusuarios siempre ven si el global está activo; usuarios normales necesitan flag individual
    habilitado = global_habilitado
    if global_habilitado and cu and cu.is_authenticated:
        rol = getattr(cu, 'rol', 'usuario')
        if rol in ('administrador', 'superusuario'):
            habilitado = True
        else:
            habilitado = getattr(cu, 'visible_facturas', False)

    return jsonify({
        'habilitado': habilitado,
        'global_habilitado': global_habilitado
    }), 200


@parametros_bp.route('/visible-propuestas', methods=['GET'])
def visible_propuestas():
    """
    Verificar si la sección Propuestas es visible.
    Para ver propuestas, AMBOS deben estar activos: parámetro global de empresa Y flag del usuario.
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
        description: Estado del parámetro visible propuestas
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
            global_habilitado:
              type: boolean
              description: Si el parámetro global de empresa está activo
    """
    from flask_login import current_user as cu
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    global_habilitado = ParametrosModel.visible_propuestas(empresa_id, connection)

    # Admins/superusuarios siempre ven si el global está activo; usuarios normales necesitan flag individual
    habilitado = global_habilitado
    if global_habilitado and cu and cu.is_authenticated:
        rol = getattr(cu, 'rol', 'usuario')
        if rol in ('administrador', 'superusuario'):
            habilitado = True
        else:
            habilitado = getattr(cu, 'visible_propuestas', True)

    return jsonify({
        'habilitado': habilitado,
        'global_habilitado': global_habilitado
    }), 200


@parametros_bp.route('/visible-stock-anulados', methods=['GET'])
def visible_stock_anulados():
    """
    Verificar si la sección Stocks Anulados es visible.
    Para ver stocks anulados, AMBOS deben estar activos: parámetro global de empresa Y flag del usuario.
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
        description: Estado del parámetro visible stocks anulados
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
            global_habilitado:
              type: boolean
              description: Si el parámetro global de empresa está activo
    """
    from flask_login import current_user as cu
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    global_habilitado = ParametrosModel.visible_stock_anulados(empresa_id, connection)

    # Admins/superusuarios siempre ven si el global está activo; usuarios normales necesitan flag individual
    habilitado = global_habilitado
    if global_habilitado and cu and cu.is_authenticated:
        rol = getattr(cu, 'rol', 'usuario')
        if rol in ('administrador', 'superusuario'):
            habilitado = True
        else:
            habilitado = getattr(cu, 'visible_stock_anulados', False)

    return jsonify({
        'habilitado': habilitado,
        'global_habilitado': global_habilitado
    }), 200


@parametros_bp.route('/visible-busqueda-magica', methods=['GET'])
def visible_busqueda_magica():
    """
    Verificar si la sección Búsqueda Mágica es visible.
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
        description: Estado del parámetro visible búsqueda mágica
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    habilitado = ParametrosModel.visible_busqueda_magica(empresa_id, connection)
    return jsonify({'habilitado': habilitado}), 200


@parametros_bp.route('/visible-consultas', methods=['GET'])
def visible_consultas():
    """
    Verificar si la sección Consultas es visible.
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
        description: Estado del parámetro visible consultas
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    habilitado = ParametrosModel.visible_consultas(empresa_id, connection)
    return jsonify({'habilitado': habilitado}), 200


@parametros_bp.route('/visible-favoritos', methods=['GET'])
def visible_favoritos():
    """
    Verificar si la sección Favoritos es visible.
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
        description: Estado del parámetro visible favoritos
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    habilitado = ParametrosModel.visible_favoritos(empresa_id, connection)
    return jsonify({'habilitado': habilitado}), 200


@parametros_bp.route('/columnas-opcionales', methods=['GET'])
def get_columnas_opcionales():
    """
    Obtener columnas opcionales visibles en grid de stocks
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
        description: Columnas opcionales configuradas
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)
    columnas = ParametrosModel.columnas_opcionales(empresa_id, connection)
    todas = ['formato', 'modelo', 'color', 'tipo_producto', 'calidad', 'busqueda_descripcion', 'existencias_min']
    return jsonify({'columnas': columnas, 'disponibles': todas}), 200


@parametros_bp.route('/columnas-opcionales', methods=['PUT'])
@login_required
@csrf_required
@superusuario_required
def set_columnas_opcionales():
    """
    Guardar columnas opcionales visibles en grid de stocks
    ---
    tags:
      - Parámetros
    security:
      - session: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            columnas:
              type: array
              items:
                type: string
    responses:
      200:
        description: Columnas actualizadas
    """
    import json
    data = request.get_json()
    columnas = data.get('columnas', [])
    todas_validas = ['formato', 'modelo', 'color', 'tipo_producto', 'calidad', 'busqueda_descripcion', 'existencias_min']
    columnas = [c for c in columnas if c in todas_validas]
    empresa_id = get_empresa_id()
    connection = get_connection()
    ParametrosModel.set('STOCK_COLUMNAS_OPCIONALES', json.dumps(columnas), empresa_id, connection)
    return jsonify({'success': True, 'columnas': columnas}), 200


@parametros_bp.route('/paginacion-config', methods=['GET'])
def paginacion_config():
    """
    Obtener configuración de paginación para el grid sin imágenes
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
        description: Configuración de paginación
        schema:
          type: object
          properties:
            habilitado:
              type: boolean
              description: Si la paginación está habilitada
            limite:
              type: integer
              description: Número de registros por página
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)

    # Obtener parámetros de paginación
    paginacion_habilitada = ParametrosModel.get('PAGINACION_GRID', empresa_id, connection)
    paginacion_limite = ParametrosModel.get('PAGINACION_LIMITE', empresa_id, connection)

    # Valores por defecto si no existen
    habilitado = paginacion_habilitada == '1' if paginacion_habilitada else False
    limite = int(paginacion_limite) if paginacion_limite else 50

    return jsonify({
        'habilitado': habilitado,
        'limite': limite
    }), 200

# ============================================
# ENDPOINTS PROTEGIDOS (requieren admin)
# ============================================

@parametros_bp.route('', methods=['GET'])
@login_required
@superusuario_required
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
@superusuario_required
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
@superusuario_required
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


# ============================================
# ENDPOINTS MODO ESPEJO
# ============================================

@parametros_bp.route('/modo-espejo', methods=['GET'])
def get_modo_espejo():
    """
    Obtener configuración de modo espejo y fecha de sincronización
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
        description: Configuración de modo espejo
        schema:
          type: object
          properties:
            modo_espejo:
              type: boolean
              description: Si la BD trabaja en modo espejo
            fecha_sincronizacion:
              type: string
              description: Fecha de la última sincronización (formato YYYY-MM-DD HH:MM:SS)
    """
    connection = get_connection()
    empresa_id = get_empresa_id_from_connection(connection)

    modo_espejo = ParametrosModel.get('MODO_ESPEJO', empresa_id, connection)
    fecha_sync = ParametrosModel.get('FECHA_ULTIMA_SINCRONIZACION', empresa_id, connection)

    return jsonify({
        'modo_espejo': modo_espejo == '1' if modo_espejo else False,
        'fecha_sincronizacion': fecha_sync or None
    }), 200


@parametros_bp.route('/sincronizacion', methods=['POST'])
@api_key_or_login_required
def actualizar_sincronizacion():
    """
    Actualizar fecha de última sincronización (para scripts externos)
    ---
    tags:
      - Parámetros
    security:
      - api_key: []
      - session: []
    parameters:
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            fecha:
              type: string
              description: Fecha de sincronización (formato YYYY-MM-DD HH:MM:SS). Si no se proporciona, usa la fecha actual.
            empresa_id:
              type: string
    responses:
      200:
        description: Fecha actualizada correctamente
      500:
        description: Error al actualizar
    """
    data = request.get_json() or {}
    connection = get_connection()
    empresa_id = data.get('empresa_id') or get_empresa_id_from_connection(connection) or '1'

    # Si no se proporciona fecha, usar la actual
    fecha = data.get('fecha')
    if not fecha:
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    success = ParametrosModel.set('FECHA_ULTIMA_SINCRONIZACION', fecha, empresa_id, connection)

    if success:
        return jsonify({
            'success': True,
            'message': 'Fecha de sincronización actualizada',
            'fecha': fecha
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'Error al actualizar la fecha de sincronización'
        }), 500
