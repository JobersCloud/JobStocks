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
# ARCHIVO: utils/backup_executor.py
# Ejecutor de backups de BD con soporte FTP/SFTP
# ============================================

import os
import time
import ftplib
import logging
import threading
from datetime import datetime
from config.database import Database
from models.backup_model import BackupModel

logger = logging.getLogger(__name__)

# Estado global de backups en curso (por empresa_id)
_backup_status = {}
_backup_lock = threading.Lock()


def get_backup_status(empresa_id):
    """Obtener estado del backup en curso para una empresa"""
    with _backup_lock:
        return _backup_status.get(empresa_id, {}).copy()


def _set_backup_status(empresa_id, status):
    """Establecer estado del backup"""
    with _backup_lock:
        _backup_status[empresa_id] = status


def _clear_backup_status(empresa_id):
    """Limpiar estado del backup"""
    with _backup_lock:
        _backup_status.pop(empresa_id, None)


def get_db_name(tipo_bd, connection=None):
    """Obtener nombre de la base de datos segun tipo"""
    conn = None
    try:
        if tipo_bd == 'central':
            from config.database_central import DatabaseCentral
            conn = DatabaseCentral.get_connection()
        else:
            conn = Database.get_connection(connection)
        cursor = conn.cursor()
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        cursor.close()
        return db_name
    finally:
        if conn:
            conn.close()


def generate_backup_filename(db_name):
    """Generar nombre de archivo de backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{db_name}_{timestamp}.bak"


def execute_backup(config, empresa_id, user_id=None, connection=None):
    """
    Ejecutar backup de BD (se ejecuta en un thread separado).
    config: dict con la configuracion de backup
    """
    history_id = None
    start_time = time.time()

    try:
        tipo_bd = config.get('tipo_bd', 'cliente')
        protocolo = config.get('protocolo', 'local')
        config_id = config.get('id')

        # Obtener nombre de la BD
        db_name = get_db_name(tipo_bd, connection)
        backup_filename = generate_backup_filename(db_name)

        # Determinar ruta de destino para mostrar
        if protocolo == 'local':
            ruta_local = config.get('ruta_local', '').strip()
            destino = os.path.join(ruta_local, backup_filename) if ruta_local else backup_filename
        else:
            destino = f"{protocolo}://{config.get('host', '')}:{config.get('puerto', 22)}{config.get('ruta_remota', '')}/{backup_filename}"

        # Crear entrada en historial
        _set_backup_status(empresa_id, {
            'running': True,
            'phase': 'preparing',
            'message': 'Preparando backup...',
            'percent': 0,
            'filename': backup_filename,
        })

        history_id = BackupModel.create_history({
            'config_id': config_id,
            'empresa_id': empresa_id,
            'tipo_bd': tipo_bd,
            'nombre_archivo': backup_filename,
            'protocolo': protocolo,
            'destino': destino,
            'usuario_id': user_id,
        }, connection)

        # Fase 1: Ejecutar BACKUP DATABASE
        _set_backup_status(empresa_id, {
            'running': True,
            'phase': 'backing_up',
            'message': f'Respaldando BD {db_name}...',
            'percent': 20,
            'filename': backup_filename,
        })

        # Determinar la ruta del archivo .bak en el servidor SQL
        # Si es local, usar la ruta destino directamente
        # Si es FTP/SFTP, usar un directorio temporal en el servidor SQL
        if protocolo == 'local':
            ruta_local = config.get('ruta_local', '').strip()
            if not ruta_local:
                raise ValueError("Ruta local no especificada")
            backup_path = os.path.join(ruta_local, backup_filename)
        else:
            # Usar directorio temporal del servidor SQL Server
            backup_path = _get_temp_backup_path(tipo_bd, backup_filename, connection)

        # Ejecutar BACKUP DATABASE con autocommit
        _execute_backup_sql(db_name, backup_path, tipo_bd, connection)

        # Obtener tamano del archivo
        tamano_mb = _get_backup_size_mb(backup_path, tipo_bd, connection)

        # Fase 2: Subir archivo si es FTP/SFTP
        if protocolo in ('ftp', 'sftp'):
            _set_backup_status(empresa_id, {
                'running': True,
                'phase': 'uploading',
                'message': f'Subiendo archivo por {protocolo.upper()}...',
                'percent': 60,
                'filename': backup_filename,
            })

            if protocolo == 'ftp':
                upload_ftp(
                    config.get('host', ''),
                    config.get('puerto', 21),
                    config.get('usuario', ''),
                    config.get('password', ''),
                    config.get('ruta_remota', ''),
                    backup_path,
                    backup_filename
                )
            else:
                upload_sftp(
                    config.get('host', ''),
                    config.get('puerto', 22),
                    config.get('usuario', ''),
                    config.get('password', ''),
                    config.get('ruta_remota', ''),
                    backup_path,
                    backup_filename
                )

            # Limpiar archivo temporal si se subio por FTP/SFTP
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
            except Exception:
                pass

        # Exito
        duracion = int(time.time() - start_time)
        BackupModel.update_history(history_id, {
            'estado': 'success',
            'mensaje': f'Backup completado correctamente',
            'tamano_mb': tamano_mb,
            'duracion_seg': duracion,
            'fecha_fin': True,
        }, connection)

        if config_id:
            BackupModel.mark_executed(config_id, connection)

        _set_backup_status(empresa_id, {
            'running': False,
            'phase': 'completed',
            'message': 'Backup completado correctamente',
            'percent': 100,
            'filename': backup_filename,
            'tamano_mb': tamano_mb,
            'duracion_seg': duracion,
        })

        # Registrar en auditoria
        try:
            from models.audit_model import AuditModel, AuditAction, AuditResult
            AuditModel.log(
                AuditAction.BACKUP_EXECUTE,
                user_id=user_id,
                empresa_id=empresa_id,
                resultado=AuditResult.SUCCESS,
                detalles=f"Backup {tipo_bd} ({protocolo}): {backup_filename} ({tamano_mb:.1f} MB, {duracion}s)",
                connection=connection
            )
        except Exception:
            pass

        logger.info(f"Backup completado: {backup_filename} ({tamano_mb:.1f} MB, {duracion}s)")

    except Exception as e:
        duracion = int(time.time() - start_time)
        error_msg = str(e)
        logger.error(f"Error en backup: {error_msg}")

        if history_id:
            BackupModel.update_history(history_id, {
                'estado': 'failed',
                'mensaje': error_msg[:4000],
                'duracion_seg': duracion,
                'fecha_fin': True,
            }, connection)

        _set_backup_status(empresa_id, {
            'running': False,
            'phase': 'failed',
            'message': error_msg,
            'percent': 0,
        })

        try:
            from models.audit_model import AuditModel, AuditAction, AuditResult
            AuditModel.log(
                AuditAction.BACKUP_EXECUTE,
                user_id=user_id,
                empresa_id=empresa_id,
                resultado=AuditResult.FAILED,
                detalles=f"Error backup: {error_msg[:500]}",
                connection=connection
            )
        except Exception:
            pass


def _get_temp_backup_path(tipo_bd, filename, connection=None):
    """Obtener ruta temporal para el backup en el servidor SQL"""
    conn = None
    try:
        if tipo_bd == 'central':
            from config.database_central import DatabaseCentral
            conn = DatabaseCentral.get_connection()
        else:
            conn = Database.get_connection(connection)

        cursor = conn.cursor()
        # Usar el directorio de datos del SQL Server como temporal
        cursor.execute("""
            SELECT REVERSE(SUBSTRING(REVERSE(physical_name),
                   CHARINDEX('\\', REVERSE(physical_name)),
                   LEN(physical_name)))
            FROM sys.database_files WHERE type = 0
        """)
        row = cursor.fetchone()
        cursor.close()
        if row and row[0]:
            return os.path.join(row[0].strip(), filename)
        # Fallback: directorio temporal de Windows
        return os.path.join('C:\\Temp', filename)
    finally:
        if conn:
            conn.close()


def _execute_backup_sql(db_name, backup_path, tipo_bd, connection=None):
    """Ejecutar sentencia BACKUP DATABASE"""
    conn = None
    try:
        if tipo_bd == 'central':
            from config.database_central import DatabaseCentral
            conn = DatabaseCentral.get_connection()
        else:
            conn = Database.get_connection(connection)

        # BACKUP DATABASE requiere autocommit
        conn.autocommit = True
        cursor = conn.cursor()
        sql = f"BACKUP DATABASE [{db_name}] TO DISK = N'{backup_path}' WITH INIT, COMPRESSION"
        logger.info(f"Ejecutando: {sql}")
        cursor.execute(sql)
        # Consumir todos los resultsets para asegurar que termino
        while cursor.nextset():
            pass
        cursor.close()
    finally:
        if conn:
            conn.close()


def _get_backup_size_mb(backup_path, tipo_bd, connection=None):
    """Obtener tamano del archivo de backup en MB"""
    # Intentar obtener el tamano desde el filesystem local
    try:
        if os.path.exists(backup_path):
            size_bytes = os.path.getsize(backup_path)
            return round(size_bytes / (1024 * 1024), 2)
    except Exception:
        pass

    # Si no es accesible localmente, intentar desde SQL Server
    conn = None
    try:
        if tipo_bd == 'central':
            from config.database_central import DatabaseCentral
            conn = DatabaseCentral.get_connection()
        else:
            conn = Database.get_connection(connection)
        cursor = conn.cursor()
        cursor.execute("""
            EXEC master.dbo.xp_fileexist ?
        """, (backup_path,))
        row = cursor.fetchone()
        cursor.close()
        if row and row[0] == 1:
            # El archivo existe en el servidor SQL, pero no podemos obtener su tamano facilmente
            # desde SQL. Retornar 0 como fallback.
            return 0
    except Exception:
        pass
    finally:
        if conn:
            conn.close()

    return 0


def upload_ftp(host, port, user, password, remote_path, local_file, filename):
    """Subir archivo por FTP"""
    ftp = ftplib.FTP()
    try:
        ftp.connect(host, int(port) if port else 21, timeout=30)
        ftp.login(user, password)

        # Navegar al directorio remoto si se especifica
        if remote_path:
            remote_path = remote_path.strip('/')
            if remote_path:
                try:
                    ftp.cwd(remote_path)
                except ftplib.error_perm:
                    # Intentar crear el directorio
                    _ftp_mkdirs(ftp, remote_path)
                    ftp.cwd(remote_path)

        # Subir archivo
        with open(local_file, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)

        logger.info(f"Archivo subido por FTP: {filename}")
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()


def _ftp_mkdirs(ftp, path):
    """Crear directorios recursivamente en FTP"""
    dirs = path.strip('/').split('/')
    current = ''
    for d in dirs:
        current = f"{current}/{d}"
        try:
            ftp.cwd(current)
        except ftplib.error_perm:
            ftp.mkd(current)
    ftp.cwd('/')


def upload_sftp(host, port, user, password, remote_path, local_file, filename):
    """Subir archivo por SFTP"""
    import paramiko

    transport = paramiko.Transport((host, int(port) if port else 22))
    try:
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # Navegar al directorio remoto
        remote_dir = remote_path.strip('/') if remote_path else ''
        if remote_dir:
            _sftp_mkdirs(sftp, remote_dir)
            remote_file = f"/{remote_dir}/{filename}"
        else:
            remote_file = f"/{filename}"

        sftp.put(local_file, remote_file)
        sftp.close()
        logger.info(f"Archivo subido por SFTP: {filename}")
    finally:
        transport.close()


def _sftp_mkdirs(sftp, path):
    """Crear directorios recursivamente en SFTP"""
    dirs = path.strip('/').split('/')
    current = ''
    for d in dirs:
        current = f"{current}/{d}"
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def test_connection(protocolo, host, port, user, password, remote_path):
    """Probar conexion FTP/SFTP"""
    if protocolo == 'ftp':
        ftp = ftplib.FTP()
        try:
            ftp.connect(host, int(port) if port else 21, timeout=10)
            ftp.login(user, password)
            # Verificar directorio remoto
            if remote_path:
                remote_path = remote_path.strip('/')
                if remote_path:
                    ftp.cwd(remote_path)
            ftp.quit()
            return {'success': True, 'message': 'Conexion FTP exitosa'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            try:
                ftp.close()
            except Exception:
                pass

    elif protocolo == 'sftp':
        import paramiko
        transport = None
        try:
            transport = paramiko.Transport((host, int(port) if port else 22))
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            # Verificar directorio remoto
            if remote_path:
                remote_path = remote_path.strip('/')
                if remote_path:
                    sftp.stat(f"/{remote_path}")
            sftp.close()
            return {'success': True, 'message': 'Conexion SFTP exitosa'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            if transport:
                try:
                    transport.close()
                except Exception:
                    pass

    return {'success': False, 'message': f'Protocolo no soportado: {protocolo}'}
