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
# ARCHIVO: routes/empresa_logo_routes.py
# ============================================
from flask import Blueprint, Response, request, send_from_directory, jsonify, session
from flask_login import login_required, current_user
from utils.auth import csrf_required
from models.empresa_logo_model import EmpresaLogoModel
from utils.auth import administrador_required
import os
import base64

empresa_logo_bp = Blueprint('empresa_logo', __name__, url_prefix='/api/empresa')


def get_connection_from_session():
    """Obtiene el connection de la sesión (después de login)."""
    return session.get('connection')


def get_empresa_id_from_session():
    """Obtiene el empresa_id de la sesión (después de login)."""
    return session.get('empresa_id')


def get_empresa_id_from_connection(connection):
    """Obtiene el empresa_id consultando BD central."""
    from models.empresa_cliente_model import EmpresaClienteModel
    empresa = EmpresaClienteModel.get_by_id(connection)
    if empresa:
        return empresa.get('empresa_erp')
    return '1'

# Directorio de assets como fallback
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend')

@empresa_logo_bp.route('/<empresa_id>/logo', methods=['GET'])
def get_logo(empresa_id):
    """
    Obtiene el logo de una empresa
    ---
    tags:
      - Empresa Logo
    parameters:
      - name: empresa_id
        in: path
        type: string
        required: true
        description: ID de la empresa (connection)
    responses:
      200:
        description: Imagen del logo
      404:
        description: Logo no encontrado
    """
    # empresa_id en URL es connection (para rutas públicas)
    # Obtenemos empresa_id de BD central para filtrar en tabla empresa_logo
    connection = empresa_id
    empresa_id_val = get_empresa_id_from_connection(connection)
    logo = EmpresaLogoModel.get_logo(empresa_id_val, connection)

    if logo:
        # Detectar tipo de imagen por magic bytes
        content_type = 'image/png'
        if logo[:3] == b'\xff\xd8\xff':
            content_type = 'image/jpeg'
        elif logo[:4] == b'\x89PNG':
            content_type = 'image/png'
        elif logo[:4] == b'GIF8':
            content_type = 'image/gif'
        elif logo[:4] == b'RIFF' and logo[8:12] == b'WEBP':
            content_type = 'image/webp'
        elif b'<svg' in logo[:500] or b'<?xml' in logo[:100]:
            content_type = 'image/svg+xml'

        return Response(logo, mimetype=content_type)

    # Fallback: devolver logo por defecto de assets
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), 'logo.svg')


@empresa_logo_bp.route('/<empresa_id>/favicon', methods=['GET'])
def get_favicon(empresa_id):
    """
    Obtiene el favicon de una empresa
    ---
    tags:
      - Empresa Logo
    parameters:
      - name: empresa_id
        in: path
        type: string
        required: true
        description: ID de la empresa (connection)
    responses:
      200:
        description: Favicon
      404:
        description: Favicon no encontrado
    """
    connection = empresa_id
    empresa_id_val = get_empresa_id_from_connection(connection)
    favicon = EmpresaLogoModel.get_favicon(empresa_id_val, connection)

    if favicon:
        # Detectar tipo de imagen
        content_type = 'image/x-icon'
        if favicon[:4] == b'\x89PNG':
            content_type = 'image/png'
        elif favicon[:4] == b'\x00\x00\x01\x00':
            content_type = 'image/x-icon'

        return Response(favicon, mimetype=content_type)

    # Fallback: devolver favicon por defecto
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), 'favicon.ico')


@empresa_logo_bp.route('/<empresa_id>/logo/exists', methods=['GET'])
def logo_exists(empresa_id):
    """
    Verifica si existe logo para una empresa
    ---
    tags:
      - Empresa Logo
    parameters:
      - name: empresa_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Resultado de la verificación
    """
    connection = empresa_id
    empresa_id_val = get_empresa_id_from_connection(connection)
    logo = EmpresaLogoModel.get_logo(empresa_id_val, connection)
    return {"exists": logo is not None}


@empresa_logo_bp.route('/<empresa_id>/config', methods=['GET'])
def get_config(empresa_id):
    """
    Obtiene la configuración de logo de una empresa (incluye invertir_logo)
    ---
    tags:
      - Empresa Logo
    parameters:
      - name: empresa_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Configuración de logo
    """
    connection = empresa_id
    empresa_id_val = get_empresa_id_from_connection(connection)
    config = EmpresaLogoModel.get_config(empresa_id_val, connection)
    if config:
        return jsonify(config)
    return jsonify({
        'empresa_id': empresa_id_val,
        'invertir_logo': False,
        'tiene_logo': False,
        'tiene_favicon': False,
        'tema': 'rubi'
    })


@empresa_logo_bp.route('/<empresa_id>/invertir', methods=['GET'])
def get_invertir(empresa_id):
    """
    Obtiene si el logo debe invertirse
    ---
    tags:
      - Empresa Logo
    """
    connection = empresa_id
    empresa_id_val = get_empresa_id_from_connection(connection)
    invertir = EmpresaLogoModel.get_invertir_logo(empresa_id_val, connection)
    return {"invertir": invertir}


@empresa_logo_bp.route('/<empresa_id>/invertir', methods=['POST'])
@login_required
@csrf_required
@administrador_required
def set_invertir(empresa_id):
    """
    Establece si el logo debe invertirse
    ---
    tags:
      - Empresa Logo
    """
    try:
        # Usar sesión (usuario logueado)
        connection = get_connection_from_session()
        empresa_id_val = get_empresa_id_from_session()
        data = request.json
        invertir = data.get('invertir', False)

        if EmpresaLogoModel.set_invertir_logo(empresa_id_val, invertir, connection):
            return jsonify({"message": "Configuración actualizada"}), 200
        else:
            return jsonify({"error": "Error al guardar configuración"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@empresa_logo_bp.route('/<empresa_id>/logo', methods=['POST'])
@login_required
@csrf_required
@administrador_required
def upload_logo(empresa_id):
    """
    Sube o actualiza el logo de una empresa
    ---
    tags:
      - Empresa Logo
    parameters:
      - name: empresa_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            logo:
              type: string
              description: Logo en base64
    responses:
      200:
        description: Logo actualizado correctamente
      400:
        description: Error en la solicitud
    """
    try:
        # Usar sesión (usuario logueado)
        connection = get_connection_from_session()
        empresa_id_val = get_empresa_id_from_session()
        data = request.json
        logo_base64 = data.get('logo')

        if not logo_base64:
            return jsonify({"error": "No se proporcionó logo"}), 400

        # Eliminar prefijo data:image/xxx;base64, si existe
        if ',' in logo_base64:
            logo_base64 = logo_base64.split(',')[1]

        logo_bytes = base64.b64decode(logo_base64)

        if EmpresaLogoModel.save_logo(empresa_id_val, logo_bytes, connection):
            return jsonify({"message": "Logo actualizado correctamente"}), 200
        else:
            return jsonify({"error": "Error al guardar logo"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@empresa_logo_bp.route('/<empresa_id>/favicon', methods=['POST'])
@login_required
@csrf_required
@administrador_required
def upload_favicon(empresa_id):
    """
    Sube o actualiza el favicon de una empresa
    ---
    tags:
      - Empresa Logo
    parameters:
      - name: empresa_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            favicon:
              type: string
              description: Favicon en base64
    responses:
      200:
        description: Favicon actualizado correctamente
      400:
        description: Error en la solicitud
    """
    try:
        # Usar sesión (usuario logueado)
        connection = get_connection_from_session()
        empresa_id_val = get_empresa_id_from_session()
        data = request.json
        favicon_base64 = data.get('favicon')

        if not favicon_base64:
            return jsonify({"error": "No se proporcionó favicon"}), 400

        # Eliminar prefijo data:image/xxx;base64, si existe
        if ',' in favicon_base64:
            favicon_base64 = favicon_base64.split(',')[1]

        favicon_bytes = base64.b64decode(favicon_base64)

        if EmpresaLogoModel.save_favicon(empresa_id_val, favicon_bytes, connection):
            return jsonify({"message": "Favicon actualizado correctamente"}), 200
        else:
            return jsonify({"error": "Error al guardar favicon"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@empresa_logo_bp.route('/<empresa_id>/logo', methods=['DELETE'])
@login_required
@csrf_required
@administrador_required
def delete_logo(empresa_id):
    """
    Elimina el logo de una empresa
    """
    try:
        # Usar sesión (usuario logueado)
        connection = get_connection_from_session()
        empresa_id_val = get_empresa_id_from_session()
        if EmpresaLogoModel.delete_logo(empresa_id_val, connection):
            return jsonify({"message": "Logo eliminado correctamente"}), 200
        else:
            return jsonify({"error": "Error al eliminar logo"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@empresa_logo_bp.route('/<empresa_id>/favicon', methods=['DELETE'])
@login_required
@csrf_required
@administrador_required
def delete_favicon(empresa_id):
    """
    Elimina el favicon de una empresa
    """
    try:
        # Usar sesión (usuario logueado)
        connection = get_connection_from_session()
        empresa_id_val = get_empresa_id_from_session()
        if EmpresaLogoModel.delete_favicon(empresa_id_val, connection):
            return jsonify({"message": "Favicon eliminado correctamente"}), 200
        else:
            return jsonify({"error": "Error al eliminar favicon"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@empresa_logo_bp.route('/<empresa_id>/tema', methods=['GET'])
def get_tema(empresa_id):
    """
    Obtiene el tema de colores de una empresa
    ---
    tags:
      - Empresa Logo
    parameters:
      - name: empresa_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Tema de colores
    """
    # Público: usar connection de la URL
    connection = empresa_id
    empresa_id_val = get_empresa_id_from_connection(connection)
    tema = EmpresaLogoModel.get_tema(empresa_id_val, connection)
    return jsonify({"tema": tema})


@empresa_logo_bp.route('/<empresa_id>/tema', methods=['PUT'])
@login_required
@csrf_required
@administrador_required
def set_tema(empresa_id):
    """
    Establece el tema de colores de una empresa
    ---
    tags:
      - Empresa Logo
    parameters:
      - name: empresa_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            tema:
              type: string
              enum: [rubi, zafiro, esmeralda, amatista, ambar, grafito]
    responses:
      200:
        description: Tema actualizado correctamente
      400:
        description: Tema no válido
    """
    try:
        # Usar sesión (usuario logueado)
        connection = get_connection_from_session()
        empresa_id_val = get_empresa_id_from_session()
        data = request.json
        tema = data.get('tema', 'rubi')

        if EmpresaLogoModel.set_tema(empresa_id_val, tema, connection):
            return jsonify({"message": "Tema actualizado correctamente"}), 200
        else:
            return jsonify({"error": "Tema no válido. Valores permitidos: rubi, zafiro, esmeralda, amatista, ambar, grafito"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
