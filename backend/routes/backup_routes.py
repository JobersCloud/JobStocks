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
# Fecha : 2026-03-27
# ============================================================

# ============================================
# ARCHIVO: routes/backup_routes.py
# ============================================
import threading
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from utils.auth import superusuario_required, csrf_required
from models.backup_model import BackupModel
from utils.backup_executor import execute_backup, test_connection, get_backup_status

backup_bp = Blueprint('backup', __name__)


def get_empresa_id():
    """Obtener empresa_id del contexto de sesion"""
    return session.get('empresa_id', session.get('connection', '1'))


@backup_bp.route('/api/backup/configs', methods=['GET'])
@login_required
@superusuario_required
def list_configs():
    """Listar configuraciones de backup"""
    try:
        empresa_id = get_empresa_id()
        configs = BackupModel.get_configs(empresa_id)
        return jsonify(configs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backup_bp.route('/api/backup/configs', methods=['POST'])
@login_required
@superusuario_required
@csrf_required
def create_config():
    """Crear configuracion de backup"""
    try:
        empresa_id = get_empresa_id()
        data = request.get_json()
        if not data or not data.get('nombre'):
            return jsonify({'error': 'Nombre es requerido'}), 400

        new_id = BackupModel.create_config(data, empresa_id)
        return jsonify({'success': True, 'id': new_id})
    except Exception as e:
        error_msg = str(e)
        if 'UQ_backup_config_nombre' in error_msg:
            return jsonify({'error': 'Ya existe una configuracion con ese nombre'}), 400
        return jsonify({'error': error_msg}), 500


@backup_bp.route('/api/backup/configs/<int:id>', methods=['PUT'])
@login_required
@superusuario_required
@csrf_required
def update_config(id):
    """Actualizar configuracion de backup"""
    try:
        empresa_id = get_empresa_id()
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos requeridos'}), 400

        updated = BackupModel.update_config(id, data, empresa_id)
        if not updated:
            return jsonify({'error': 'Configuracion no encontrada'}), 404
        return jsonify({'success': True})
    except Exception as e:
        error_msg = str(e)
        if 'UQ_backup_config_nombre' in error_msg:
            return jsonify({'error': 'Ya existe una configuracion con ese nombre'}), 400
        return jsonify({'error': error_msg}), 500


@backup_bp.route('/api/backup/configs/<int:id>', methods=['DELETE'])
@login_required
@superusuario_required
@csrf_required
def delete_config(id):
    """Eliminar configuracion de backup"""
    try:
        empresa_id = get_empresa_id()
        deleted = BackupModel.delete_config(id, empresa_id)
        if not deleted:
            return jsonify({'error': 'Configuracion no encontrada'}), 404
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backup_bp.route('/api/backup/execute/<int:id>', methods=['POST'])
@login_required
@superusuario_required
@csrf_required
def execute_config_backup(id):
    """Ejecutar backup desde una configuracion guardada"""
    try:
        empresa_id = get_empresa_id()

        # Verificar que no hay backup en curso
        status = get_backup_status(empresa_id)
        if status.get('running'):
            return jsonify({'error': 'Ya hay un backup en curso'}), 409

        config = BackupModel.get_config(id, empresa_id)
        if not config:
            return jsonify({'error': 'Configuracion no encontrada'}), 404

        connection = session.get('connection')
        user_id = current_user.id if current_user else None

        # Ejecutar en thread separado
        thread = threading.Thread(
            target=execute_backup,
            args=(config, empresa_id, user_id, connection),
            daemon=True,
            name=f'Backup-{id}'
        )
        thread.start()

        return jsonify({'success': True, 'message': 'Backup iniciado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backup_bp.route('/api/backup/execute-now', methods=['POST'])
@login_required
@superusuario_required
@csrf_required
def execute_now():
    """Ejecutar backup rapido sin configuracion guardada"""
    try:
        empresa_id = get_empresa_id()

        # Verificar que no hay backup en curso
        status = get_backup_status(empresa_id)
        if status.get('running'):
            return jsonify({'error': 'Ya hay un backup en curso'}), 409

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos requeridos'}), 400

        config = {
            'id': None,
            'tipo_bd': data.get('tipo_bd', 'cliente'),
            'protocolo': data.get('protocolo', 'local'),
            'ruta_local': data.get('ruta_local', ''),
            'host': data.get('host', ''),
            'puerto': data.get('puerto', 22),
            'usuario': data.get('usuario', ''),
            'password': data.get('password', ''),
            'ruta_remota': data.get('ruta_remota', ''),
        }

        connection = session.get('connection')
        user_id = current_user.id if current_user else None

        thread = threading.Thread(
            target=execute_backup,
            args=(config, empresa_id, user_id, connection),
            daemon=True,
            name='Backup-quick'
        )
        thread.start()

        return jsonify({'success': True, 'message': 'Backup iniciado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backup_bp.route('/api/backup/status', methods=['GET'])
@login_required
@superusuario_required
def backup_status():
    """Obtener estado del backup en curso"""
    try:
        empresa_id = get_empresa_id()
        status = get_backup_status(empresa_id)
        return jsonify(status if status else {'running': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backup_bp.route('/api/backup/history', methods=['GET'])
@login_required
@superusuario_required
def list_history():
    """Listar historial de backups"""
    try:
        empresa_id = get_empresa_id()
        limit = request.args.get('limit', 50, type=int)
        history = BackupModel.get_history(empresa_id, limit)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backup_bp.route('/api/backup/history/<int:id>', methods=['DELETE'])
@login_required
@superusuario_required
@csrf_required
def delete_history_entry(id):
    """Eliminar entrada del historial"""
    try:
        empresa_id = get_empresa_id()
        deleted = BackupModel.delete_history(id, empresa_id)
        if not deleted:
            return jsonify({'error': 'Entrada no encontrada'}), 404
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backup_bp.route('/api/backup/history/cleanup', methods=['POST'])
@login_required
@superusuario_required
@csrf_required
def cleanup_history():
    """Limpiar historial antiguo"""
    try:
        empresa_id = get_empresa_id()
        data = request.get_json() or {}
        dias = data.get('dias', 90)
        deleted = BackupModel.cleanup_history(empresa_id, dias)
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backup_bp.route('/api/backup/test-connection', methods=['POST'])
@login_required
@superusuario_required
@csrf_required
def test_backup_connection():
    """Probar conexion FTP/SFTP"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos requeridos'}), 400

        protocolo = data.get('protocolo', '')
        if protocolo not in ('ftp', 'sftp'):
            return jsonify({'error': 'Protocolo debe ser ftp o sftp'}), 400

        result = test_connection(
            protocolo,
            data.get('host', ''),
            data.get('puerto', 22 if protocolo == 'sftp' else 21),
            data.get('usuario', ''),
            data.get('password', ''),
            data.get('ruta_remota', '')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
