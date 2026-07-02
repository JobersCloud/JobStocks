# ============================================
# ARCHIVO: routes/factura_pdf_routes.py
# Rutas para gestión de PDFs de facturas
# ============================================
from flask import Blueprint, jsonify, request, session, send_file
from flask_login import login_required
from utils.auth import administrador_required, csrf_required
from models.factura_pdf_model import FacturaPdfModel

factura_pdf_bp = Blueprint('factura_pdf', __name__)


def _get_connection():
    return session.get('connection')


def _get_empresa_id():
    return session.get('empresa_id', '1')


@factura_pdf_bp.route('/api/facturas/<empresa>/<int:anyo>/<int:factura>/pdfs', methods=['GET'])
@login_required
def get_pdfs(empresa, anyo, factura):
    """
    Listar PDFs vinculados a una factura
    ---
    tags:
      - Facturas PDF
    """
    try:
        pdfs = FacturaPdfModel.get_pdfs(empresa, anyo, factura, _get_connection())
        return jsonify(pdfs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@factura_pdf_bp.route('/api/facturas-pdf/download/<int:pdf_id>', methods=['GET'])
@login_required
def download_pdf(pdf_id):
    """
    Descargar un PDF de factura
    ---
    tags:
      - Facturas PDF
    """
    try:
        empresa_id = _get_empresa_id()
        path = FacturaPdfModel.get_pdf_path(pdf_id, empresa_id, _get_connection())
        if not path:
            return jsonify({'error': 'PDF no encontrado'}), 404
        return send_file(path, mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@factura_pdf_bp.route('/api/facturas-pdf/scan', methods=['GET'])
@login_required
@administrador_required
def scan_directory():
    """
    Escanear directorio de PDFs (solo admin)
    ---
    tags:
      - Facturas PDF
    """
    try:
        empresa_id = _get_empresa_id()
        files = FacturaPdfModel.scan_directory(empresa_id, _get_connection())
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@factura_pdf_bp.route('/api/facturas-pdf/link', methods=['POST'])
@login_required
@csrf_required
@administrador_required
def link_pdf():
    """
    Vincular un PDF a una factura (solo admin)
    ---
    tags:
      - Facturas PDF
    """
    data = request.json
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400

    required = ['empresa', 'anyo', 'factura', 'filename']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Campo "{field}" es requerido'}), 400

    try:
        pdf_id = FacturaPdfModel.link_pdf(
            data['empresa'], data['anyo'], data['factura'],
            data['filename'], _get_connection()
        )
        return jsonify({'success': True, 'id': pdf_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@factura_pdf_bp.route('/api/facturas-pdf/<int:pdf_id>', methods=['DELETE'])
@login_required
@csrf_required
@administrador_required
def unlink_pdf(pdf_id):
    """
    Desvincular un PDF de una factura (solo admin)
    ---
    tags:
      - Facturas PDF
    """
    try:
        success = FacturaPdfModel.unlink_pdf(pdf_id, _get_connection())
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'PDF no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@factura_pdf_bp.route('/api/facturas-pdf/batch-check', methods=['POST'])
@login_required
def batch_check():
    """
    Check masivo: qué facturas tienen PDFs
    ---
    tags:
      - Facturas PDF
    """
    try:
        existing = FacturaPdfModel.has_pdfs_batch([], _get_connection())
        result = [{'empresa': e, 'anyo': a, 'factura': f} for e, a, f in existing]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
