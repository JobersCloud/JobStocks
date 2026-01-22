import secrets
from config.database import Database


class UserSessionModel:
    """Modelo para gestionar sesiones de usuario activas"""

    @staticmethod
    def create(user_id, empresa_id, ip_address=None, connection_id=None):
        """Crear nueva sesion y devolver el token"""
        session_token = secrets.token_hex(32)  # 64 caracteres

        conn = Database.get_connection(connection_id)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO user_sessions (session_token, user_id, empresa_id, ip_address)
                VALUES (?, ?, ?, ?)
            """, (session_token, user_id, empresa_id, ip_address))
            conn.commit()
            return session_token
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(session_token):
        """Eliminar sesion por token"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete_by_id(session_id):
        """Eliminar sesion por ID"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM user_sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete_by_user_id(user_id, connection_id=None):
        """Eliminar todas las sesiones de un usuario"""
        conn = Database.get_connection(connection_id)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            print(f"Error deleting user sessions: {e}")
            return 0
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete_all_except(current_token, empresa_id=None):
        """Eliminar todas las sesiones excepto la actual"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            if empresa_id:
                cursor.execute("""
                    DELETE FROM user_sessions
                    WHERE session_token != ? AND empresa_id = ?
                """, (current_token, empresa_id))
            else:
                cursor.execute("""
                    DELETE FROM user_sessions
                    WHERE session_token != ?
                """, (current_token,))
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            print(f"Error deleting all sessions except current: {e}")
            return 0
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_activity(session_token):
        """Actualizar ultima actividad de la sesion"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE user_sessions
                SET last_activity = GETDATE()
                WHERE session_token = ?
            """, (session_token,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating session activity: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def exists(session_token):
        """Verificar si una sesion existe en BD"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM user_sessions WHERE session_token = ?", (session_token,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking session: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_active_sessions(empresa_id=None):
        """Obtener todas las sesiones activas con info de usuario"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                SELECT
                    s.id,
                    s.user_id,
                    u.username,
                    u.full_name,
                    u.rol,
                    s.empresa_id,
                    s.ip_address,
                    s.created_at,
                    s.last_activity
                FROM user_sessions s
                INNER JOIN users u ON s.user_id = u.id
            """
            params = []

            if empresa_id:
                query += " WHERE s.empresa_id = ?"
                params.append(empresa_id)

            query += " ORDER BY s.last_activity DESC"

            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            sessions = []

            for row in cursor.fetchall():
                session = dict(zip(columns, row))
                # Convertir fechas a string ISO
                if session.get('created_at'):
                    session['created_at'] = session['created_at'].isoformat()
                if session.get('last_activity'):
                    session['last_activity'] = session['last_activity'].isoformat()
                sessions.append(session)

            return sessions
        except Exception as e:
            print(f"Error getting sessions: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def count_active_sessions(empresa_id=None):
        """Contar sesiones activas"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            if empresa_id:
                cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE empresa_id = ?", (empresa_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM user_sessions")
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error counting sessions: {e}")
            return 0
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def cleanup_expired(connection_id=None):
        """Limpiar sesiones expiradas segun el rol del usuario"""
        conn = Database.get_connection(connection_id)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM user_sessions
                WHERE id IN (
                    SELECT s.id
                    FROM user_sessions s
                    INNER JOIN users u ON s.user_id = u.id
                    WHERE (u.rol = 'usuario' AND s.last_activity < DATEADD(HOUR, -2, GETDATE()))
                       OR (u.rol = 'administrador' AND s.last_activity < DATEADD(HOUR, -8, GETDATE()))
                       OR (u.rol = 'superusuario' AND s.last_activity < DATEADD(DAY, -7, GETDATE()))
                )
            """)
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            return 0
        finally:
            cursor.close()
            conn.close()
