"""
Modelo de Notificaciones para usuarios
Almacena notificaciones en BD del cliente
"""
import json
from config.database import Database


class NotificationModel:
    """Modelo para gestionar notificaciones de usuarios"""

    @staticmethod
    def create(user_id, empresa_id, tipo, titulo, mensaje=None, data=None, connection_id=None):
        """
        Crear una notificación para un usuario.

        Args:
            user_id: ID del usuario destinatario
            empresa_id: ID de la empresa
            tipo: Tipo de notificación (propuesta_cambio_estado, consulta_respondida, nueva_propuesta)
            titulo: Título de la notificación
            mensaje: Mensaje descriptivo (opcional)
            data: Datos adicionales en formato dict (se convierte a JSON)
            connection_id: ID de conexión a BD

        Returns:
            int: ID de la notificación creada, o None si falla
        """
        conn = None
        try:
            if connection_id is None:
                from flask import session, has_request_context
                if has_request_context():
                    connection_id = session.get('connection')

            conn = Database.get_connection(connection_id)
            cursor = conn.cursor()

            data_json = json.dumps(data) if data else None

            cursor.execute("""
                INSERT INTO notifications (user_id, empresa_id, tipo, titulo, mensaje, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, empresa_id, tipo, titulo, mensaje, data_json))

            conn.commit()

            cursor.execute("SELECT @@IDENTITY")
            row = cursor.fetchone()
            notification_id = int(row[0]) if row and row[0] is not None else None

            cursor.close()
            return notification_id
        except Exception as e:
            print(f"Error creating notification: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_unread_count(user_id, empresa_id, connection_id=None):
        """
        Obtener conteo de notificaciones no leídas (endpoint ligero para polling).

        Returns:
            int: Número de notificaciones no leídas
        """
        conn = None
        try:
            if connection_id is None:
                from flask import session, has_request_context
                if has_request_context():
                    connection_id = session.get('connection')

            conn = Database.get_connection(connection_id)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM notifications
                WHERE user_id = ? AND empresa_id = ? AND leida = 0
            """, (user_id, empresa_id))

            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_unread(user_id, empresa_id, connection_id=None):
        """
        Obtener lista de notificaciones no leídas.

        Returns:
            list: Lista de notificaciones como diccionarios
        """
        conn = None
        try:
            if connection_id is None:
                from flask import session, has_request_context
                if has_request_context():
                    connection_id = session.get('connection')

            conn = Database.get_connection(connection_id)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT TOP 50 id, tipo, titulo, mensaje, data, fecha_creacion
                FROM notifications
                WHERE user_id = ? AND empresa_id = ? AND leida = 0
                ORDER BY fecha_creacion DESC
            """, (user_id, empresa_id))

            notifications = []
            for row in cursor.fetchall():
                notif = {
                    'id': row[0],
                    'tipo': row[1],
                    'titulo': row[2],
                    'mensaje': row[3],
                    'data': None,
                    'fecha_creacion': row[5].isoformat() if row[5] else None
                }
                if row[4]:
                    try:
                        notif['data'] = json.loads(row[4])
                    except (json.JSONDecodeError, TypeError):
                        notif['data'] = row[4]
                notifications.append(notif)

            cursor.close()
            return notifications
        except Exception as e:
            print(f"Error getting unread notifications: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mark_read(notification_id, user_id, connection_id=None):
        """
        Marcar una notificación como leída.

        Returns:
            bool: True si se actualizó correctamente
        """
        conn = None
        try:
            if connection_id is None:
                from flask import session, has_request_context
                if has_request_context():
                    connection_id = session.get('connection')

            conn = Database.get_connection(connection_id)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE notifications SET leida = 1
                WHERE id = ? AND user_id = ?
            """, (notification_id, user_id))

            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            return affected > 0
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def mark_all_read(user_id, empresa_id, connection_id=None):
        """
        Marcar todas las notificaciones como leídas.

        Returns:
            int: Número de notificaciones marcadas
        """
        conn = None
        try:
            if connection_id is None:
                from flask import session, has_request_context
                if has_request_context():
                    connection_id = session.get('connection')

            conn = Database.get_connection(connection_id)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE notifications SET leida = 1
                WHERE user_id = ? AND empresa_id = ? AND leida = 0
            """, (user_id, empresa_id))

            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            return affected
        except Exception as e:
            print(f"Error marking all notifications as read: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_admin_user_ids(empresa_id, connection_id=None):
        """
        Obtener IDs de usuarios administradores y superusuarios de una empresa.

        Returns:
            list: Lista de user_ids
        """
        conn = None
        try:
            if connection_id is None:
                from flask import session, has_request_context
                if has_request_context():
                    connection_id = session.get('connection')

            conn = Database.get_connection(connection_id)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id FROM users_empresas
                WHERE empresa_id = ? AND rol IN ('administrador', 'superusuario')
            """, (empresa_id,))

            ids = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return ids
        except Exception as e:
            print(f"Error getting admin user IDs: {e}")
            return []
        finally:
            if conn:
                conn.close()
