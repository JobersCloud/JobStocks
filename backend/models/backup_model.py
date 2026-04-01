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
# ARCHIVO: models/backup_model.py
# ============================================
from config.database import Database


class BackupModel:

    @staticmethod
    def get_configs(empresa_id, connection=None):
        """Listar configuraciones de backup de una empresa"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, empresa_id, nombre, tipo_bd, protocolo,
                       ruta_local, host, puerto, usuario, password, ruta_remota,
                       frecuencia, hora, dia_semana, dia_mes,
                       activo, fecha_creacion, fecha_modificacion, ultima_ejecucion
                FROM backup_config
                WHERE empresa_id = ?
                ORDER BY nombre
            """, (empresa_id,))
            rows = cursor.fetchall()
            configs = []
            for row in rows:
                configs.append({
                    'id': row[0],
                    'empresa_id': row[1].strip() if row[1] else '',
                    'nombre': row[2].strip() if row[2] else '',
                    'tipo_bd': row[3].strip() if row[3] else 'cliente',
                    'protocolo': row[4].strip() if row[4] else 'local',
                    'ruta_local': row[5].strip() if row[5] else '',
                    'host': row[6].strip() if row[6] else '',
                    'puerto': row[7] or 22,
                    'usuario': row[8].strip() if row[8] else '',
                    'password': '********' if row[9] else '',
                    'ruta_remota': row[10].strip() if row[10] else '',
                    'frecuencia': row[11].strip() if row[11] else 'manual',
                    'hora': row[12] if row[12] is not None else 3,
                    'dia_semana': row[13] if row[13] is not None else 1,
                    'dia_mes': row[14] if row[14] is not None else 1,
                    'activo': bool(row[15]),
                    'fecha_creacion': row[16].isoformat() if row[16] else None,
                    'fecha_modificacion': row[17].isoformat() if row[17] else None,
                    'ultima_ejecucion': row[18].isoformat() if row[18] else None,
                })
            cursor.close()
            return configs
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_config(id, empresa_id, connection=None):
        """Obtener una configuracion de backup por ID"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, empresa_id, nombre, tipo_bd, protocolo,
                       ruta_local, host, puerto, usuario, password, ruta_remota,
                       frecuencia, hora, dia_semana, dia_mes,
                       activo, fecha_creacion, fecha_modificacion, ultima_ejecucion
                FROM backup_config
                WHERE id = ? AND empresa_id = ?
            """, (id, empresa_id))
            row = cursor.fetchone()
            cursor.close()
            if not row:
                return None
            return {
                'id': row[0],
                'empresa_id': row[1].strip() if row[1] else '',
                'nombre': row[2].strip() if row[2] else '',
                'tipo_bd': row[3].strip() if row[3] else 'cliente',
                'protocolo': row[4].strip() if row[4] else 'local',
                'ruta_local': row[5].strip() if row[5] else '',
                'host': row[6].strip() if row[6] else '',
                'puerto': row[7] or 22,
                'usuario': row[8].strip() if row[8] else '',
                'password': row[9] or '',
                'ruta_remota': row[10].strip() if row[10] else '',
                'frecuencia': row[11].strip() if row[11] else 'manual',
                'hora': row[12] if row[12] is not None else 3,
                'dia_semana': row[13] if row[13] is not None else 1,
                'dia_mes': row[14] if row[14] is not None else 1,
                'activo': bool(row[15]),
                'fecha_creacion': row[16].isoformat() if row[16] else None,
                'fecha_modificacion': row[17].isoformat() if row[17] else None,
                'ultima_ejecucion': row[18].isoformat() if row[18] else None,
            }
        finally:
            if conn:
                conn.close()

    @staticmethod
    def create_config(data, empresa_id, connection=None):
        """Crear nueva configuracion de backup"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backup_config
                    (empresa_id, nombre, tipo_bd, protocolo, ruta_local,
                     host, puerto, usuario, password, ruta_remota,
                     frecuencia, hora, dia_semana, dia_mes, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                empresa_id,
                data.get('nombre', ''),
                data.get('tipo_bd', 'cliente'),
                data.get('protocolo', 'local'),
                data.get('ruta_local', ''),
                data.get('host', ''),
                data.get('puerto', 22),
                data.get('usuario', ''),
                data.get('password', ''),
                data.get('ruta_remota', ''),
                data.get('frecuencia', 'manual'),
                data.get('hora', 3),
                data.get('dia_semana', 1),
                data.get('dia_mes', 1),
                1 if data.get('activo', True) else 0,
            ))
            conn.commit()
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
            cursor.close()
            return new_id
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_config(id, data, empresa_id, connection=None):
        """Actualizar configuracion de backup"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()

            fields = []
            params = []

            field_map = {
                'nombre': 'nombre',
                'tipo_bd': 'tipo_bd',
                'protocolo': 'protocolo',
                'ruta_local': 'ruta_local',
                'host': 'host',
                'puerto': 'puerto',
                'usuario': 'usuario',
                'ruta_remota': 'ruta_remota',
                'frecuencia': 'frecuencia',
                'hora': 'hora',
                'dia_semana': 'dia_semana',
                'dia_mes': 'dia_mes',
                'activo': 'activo',
            }

            for key, col in field_map.items():
                if key in data:
                    val = data[key]
                    if key == 'activo':
                        val = 1 if val else 0
                    fields.append(f"{col} = ?")
                    params.append(val)

            # Solo actualizar password si no es el placeholder
            if 'password' in data and data['password'] != '********':
                fields.append("password = ?")
                params.append(data['password'])

            if not fields:
                return False

            fields.append("fecha_modificacion = GETDATE()")
            params.extend([id, empresa_id])

            sql = f"UPDATE backup_config SET {', '.join(fields)} WHERE id = ? AND empresa_id = ?"
            cursor.execute(sql, params)
            conn.commit()
            updated = cursor.rowcount > 0
            cursor.close()
            return updated
        finally:
            if conn:
                conn.close()

    @staticmethod
    def delete_config(id, empresa_id, connection=None):
        """Eliminar configuracion de backup"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM backup_config WHERE id = ? AND empresa_id = ?", (id, empresa_id))
            conn.commit()
            deleted = cursor.rowcount > 0
            cursor.close()
            return deleted
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_history(empresa_id, limit=50, connection=None):
        """Listar historial de backups"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP (?) id, config_id, empresa_id, tipo_bd, nombre_archivo,
                       tamano_mb, estado, mensaje, protocolo, destino,
                       fecha_inicio, fecha_fin, duracion_seg, usuario_id
                FROM backup_history
                WHERE empresa_id = ?
                ORDER BY fecha_inicio DESC
            """, (limit, empresa_id))
            rows = cursor.fetchall()
            history = []
            for row in rows:
                history.append({
                    'id': row[0],
                    'config_id': row[1],
                    'empresa_id': row[2].strip() if row[2] else '',
                    'tipo_bd': row[3].strip() if row[3] else '',
                    'nombre_archivo': row[4].strip() if row[4] else '',
                    'tamano_mb': float(row[5]) if row[5] is not None else None,
                    'estado': row[6].strip() if row[6] else '',
                    'mensaje': row[7] or '',
                    'protocolo': row[8].strip() if row[8] else '',
                    'destino': row[9].strip() if row[9] else '',
                    'fecha_inicio': row[10].isoformat() if row[10] else None,
                    'fecha_fin': row[11].isoformat() if row[11] else None,
                    'duracion_seg': row[12],
                    'usuario_id': row[13],
                })
            cursor.close()
            return history
        finally:
            if conn:
                conn.close()

    @staticmethod
    def create_history(data, connection=None):
        """Crear entrada en historial de backup"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backup_history
                    (config_id, empresa_id, tipo_bd, nombre_archivo, estado, protocolo, destino, usuario_id)
                VALUES (?, ?, ?, ?, 'running', ?, ?, ?)
            """, (
                data.get('config_id'),
                data.get('empresa_id', ''),
                data.get('tipo_bd', 'cliente'),
                data.get('nombre_archivo', ''),
                data.get('protocolo', 'local'),
                data.get('destino', ''),
                data.get('usuario_id'),
            ))
            conn.commit()
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
            cursor.close()
            return new_id
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_history(id, data, connection=None):
        """Actualizar entrada de historial (estado, tamano, fin)"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()

            fields = []
            params = []

            for key in ['estado', 'mensaje', 'tamano_mb', 'duracion_seg', 'nombre_archivo']:
                if key in data:
                    fields.append(f"{key} = ?")
                    params.append(data[key])

            if 'fecha_fin' in data:
                fields.append("fecha_fin = GETDATE()")

            if not fields:
                return False

            params.append(id)
            sql = f"UPDATE backup_history SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(sql, params)
            conn.commit()
            updated = cursor.rowcount > 0
            cursor.close()
            return updated
        finally:
            if conn:
                conn.close()

    @staticmethod
    def delete_history(id, empresa_id, connection=None):
        """Eliminar entrada del historial"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM backup_history WHERE id = ? AND empresa_id = ?", (id, empresa_id))
            conn.commit()
            deleted = cursor.rowcount > 0
            cursor.close()
            return deleted
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cleanup_history(empresa_id, dias=90, connection=None):
        """Limpiar historial antiguo"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM backup_history
                WHERE empresa_id = ? AND fecha_inicio < DATEADD(day, -?, GETDATE())
            """, (empresa_id, dias))
            conn.commit()
            deleted = cursor.rowcount
            cursor.close()
            return deleted
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_scheduled_configs(connection=None):
        """Obtener todas las configs activas con programacion (para scheduler)"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, empresa_id, nombre, tipo_bd, protocolo,
                       ruta_local, host, puerto, usuario, password, ruta_remota,
                       frecuencia, hora, dia_semana, dia_mes,
                       activo, ultima_ejecucion
                FROM backup_config
                WHERE activo = 1 AND frecuencia != 'manual'
            """)
            rows = cursor.fetchall()
            configs = []
            for row in rows:
                configs.append({
                    'id': row[0],
                    'empresa_id': row[1].strip() if row[1] else '',
                    'nombre': row[2].strip() if row[2] else '',
                    'tipo_bd': row[3].strip() if row[3] else 'cliente',
                    'protocolo': row[4].strip() if row[4] else 'local',
                    'ruta_local': row[5].strip() if row[5] else '',
                    'host': row[6].strip() if row[6] else '',
                    'puerto': row[7] or 22,
                    'usuario': row[8].strip() if row[8] else '',
                    'password': row[9] or '',
                    'ruta_remota': row[10].strip() if row[10] else '',
                    'frecuencia': row[11].strip() if row[11] else 'manual',
                    'hora': row[12] if row[12] is not None else 3,
                    'dia_semana': row[13] if row[13] is not None else 1,
                    'dia_mes': row[14] if row[14] is not None else 1,
                    'activo': bool(row[15]),
                    'ultima_ejecucion': row[16],
                })
            cursor.close()
            return configs
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mark_executed(config_id, connection=None):
        """Marcar config como ejecutada (actualizar ultima_ejecucion)"""
        conn = None
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE backup_config SET ultima_ejecucion = GETDATE(), fecha_modificacion = GETDATE()
                WHERE id = ?
            """, (config_id,))
            conn.commit()
            cursor.close()
        finally:
            if conn:
                conn.close()
