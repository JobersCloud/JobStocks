"""
Modelo de Auditoria para registrar acciones de usuarios
Almacena logs en BD del cliente (misma conexión que user_sessions)
"""
import json
from config.database import Database


class AuditAction:
    """Constantes para tipos de acciones auditables"""
    # Autenticacion
    LOGIN = 'LOGIN'
    LOGIN_FAILED = 'LOGIN_FAILED'
    LOGOUT = 'LOGOUT'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE'
    PASSWORD_RESET_REQUEST = 'PASSWORD_RESET_REQUEST'

    # Sesiones
    SESSION_KILL = 'SESSION_KILL'
    SESSION_KILL_ALL = 'SESSION_KILL_ALL'

    # Usuarios
    USER_CREATE = 'USER_CREATE'
    USER_ACTIVATE = 'USER_ACTIVATE'
    USER_DEACTIVATE = 'USER_DEACTIVATE'
    USER_ROLE_CHANGE = 'USER_ROLE_CHANGE'
    USER_DELETE = 'USER_DELETE'

    # Registro público
    USER_REGISTER = 'USER_REGISTER'
    USER_EMAIL_VERIFY = 'USER_EMAIL_VERIFY'
    USER_RESEND_VERIFICATION = 'USER_RESEND_VERIFICATION'

    # API Keys
    API_KEY_CREATE = 'API_KEY_CREATE'
    API_KEY_DELETE = 'API_KEY_DELETE'

    # Configuracion
    CONFIG_CHANGE = 'CONFIG_CHANGE'
    EMAIL_CONFIG_CHANGE = 'EMAIL_CONFIG_CHANGE'

    # Propuestas
    PROPUESTA_SEND = 'PROPUESTA_SEND'
    PROPUESTA_STATUS_CHANGE = 'PROPUESTA_STATUS_CHANGE'

    # Consultas
    CONSULTA_SEND = 'CONSULTA_SEND'
    CONSULTA_RESPOND = 'CONSULTA_RESPOND'

    # Articulos
    ARTICLE_VIEW = 'ARTICLE_VIEW'

    @classmethod
    def get_all_actions(cls):
        """Retorna lista de todas las acciones disponibles"""
        return [
            cls.LOGIN, cls.LOGIN_FAILED, cls.LOGOUT, cls.PASSWORD_CHANGE, cls.PASSWORD_RESET_REQUEST,
            cls.SESSION_KILL, cls.SESSION_KILL_ALL,
            cls.USER_CREATE, cls.USER_ACTIVATE, cls.USER_DEACTIVATE, cls.USER_ROLE_CHANGE,
            cls.USER_REGISTER, cls.USER_EMAIL_VERIFY, cls.USER_RESEND_VERIFICATION,
            cls.API_KEY_CREATE, cls.API_KEY_DELETE,
            cls.CONFIG_CHANGE, cls.EMAIL_CONFIG_CHANGE,
            cls.PROPUESTA_SEND, cls.PROPUESTA_STATUS_CHANGE,
            cls.CONSULTA_SEND, cls.CONSULTA_RESPOND,
            cls.ARTICLE_VIEW
        ]


class AuditResult:
    """Constantes para resultados de acciones"""
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    BLOCKED = 'BLOCKED'


class AuditModel:
    """Modelo para gestionar logs de auditoria en BD Central"""

    @staticmethod
    def log(accion, user_id=None, username=None, empresa_id=None,
            connection_id=None, recurso=None, recurso_id=None,
            ip_address=None, user_agent=None, detalles=None,
            resultado='SUCCESS'):
        """
        Registrar evento de auditoria en BD Central

        Args:
            accion: Tipo de accion (usar constantes AuditAction)
            user_id: ID del usuario que realiza la accion
            username: Nombre de usuario (util si user_id es None)
            empresa_id: ID de la empresa (ej: '1', '2')
            connection_id: ID de conexion dinamica (empresa_cli_id)
            recurso: Tipo de recurso afectado (ej: 'user', 'propuesta')
            recurso_id: ID del recurso afectado
            ip_address: Direccion IP del cliente
            user_agent: User-Agent del navegador/cliente
            detalles: Diccionario con detalles adicionales (se convierte a JSON)
            resultado: Resultado de la accion (usar constantes AuditResult)

        Returns:
            int: ID del registro creado, o None si falla
        """
        try:
            # Obtener connection de la sesión si no se pasa
            from flask import session, has_request_context
            if connection_id is None and has_request_context():
                connection_id = session.get('connection')

            conn = Database.get_connection(connection_id)
        except Exception as e:
            print(f"Error en audit log (conexión): {e}")
            return None

        cursor = conn.cursor()
        try:
            # Convertir detalles a JSON si es un diccionario
            detalles_json = json.dumps(detalles) if detalles else None

            # Truncar campos para evitar error de longitud
            username = str(username)[:100] if username else None
            empresa_id = str(empresa_id)[:5] if empresa_id else None
            accion = str(accion)[:50] if accion else None
            recurso = str(recurso)[:100] if recurso else None
            recurso_id = str(recurso_id)[:100] if recurso_id else None
            ip_address = str(ip_address)[:45] if ip_address else None
            user_agent = str(user_agent)[:1000] if user_agent else None
            resultado = str(resultado)[:20] if resultado else 'SUCCESS'

            cursor.execute("""
                INSERT INTO audit_log
                (user_id, username, empresa_id, accion,
                 recurso, recurso_id, ip_address, user_agent, detalles, resultado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, empresa_id, accion,
                  recurso, recurso_id, ip_address, user_agent, detalles_json, resultado))

            conn.commit()

            # Obtener ID insertado
            cursor.execute("SELECT @@IDENTITY")
            row = cursor.fetchone()
            log_id = int(row[0]) if row and row[0] is not None else None

            return log_id
        except Exception as e:
            print(f"Error en audit log (INSERT): {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_logs(empresa_id=None, connection_id=None, user_id=None,
                 username=None, accion=None, fecha_desde=None, fecha_hasta=None,
                 resultado=None, limit=50, offset=0):
        """
        Obtener logs de auditoria con filtros multiples

        Args:
            empresa_id: Filtrar por empresa
            connection_id: ID conexion para obtener BD (no para filtrar)
            user_id: Filtrar por usuario (ID)
            username: Filtrar por nombre de usuario (parcial)
            accion: Filtrar por tipo de accion
            fecha_desde: Fecha inicio (formato YYYY-MM-DD)
            fecha_hasta: Fecha fin (formato YYYY-MM-DD)
            resultado: Filtrar por resultado
            limit: Limite de registros
            offset: Desplazamiento para paginacion

        Returns:
            list: Lista de logs como diccionarios
        """
        conn = Database.get_connection(connection_id)
        cursor = conn.cursor()
        try:
            # Construir WHERE clause
            where_conditions = ["1=1"]
            params = []

            if empresa_id:
                where_conditions.append("empresa_id = ?")
                params.append(empresa_id)

            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)

            if username:
                where_conditions.append("username LIKE ?")
                params.append(f"%{username}%")

            if accion:
                where_conditions.append("accion = ?")
                params.append(accion)

            if fecha_desde:
                where_conditions.append("fecha >= ?")
                params.append(f"{fecha_desde} 00:00:00")

            if fecha_hasta:
                where_conditions.append("fecha <= ?")
                params.append(f"{fecha_hasta} 23:59:59")

            if resultado:
                where_conditions.append("resultado = ?")
                params.append(resultado)

            where_clause = " AND ".join(where_conditions)

            # Usar ROW_NUMBER para paginación (compatible SQL Server 2008)
            query = f"""
                SELECT * FROM (
                    SELECT
                        id, fecha, user_id, username, empresa_id,
                        accion, recurso, recurso_id, ip_address, user_agent,
                        detalles, resultado,
                        ROW_NUMBER() OVER (ORDER BY fecha DESC) AS row_num
                    FROM audit_log
                    WHERE {where_clause}
                ) AS numbered
                WHERE row_num > ? AND row_num <= ?
                ORDER BY row_num
            """
            params.append(offset)
            params.append(offset + limit)

            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            logs = []

            for row in cursor.fetchall():
                log = dict(zip(columns, row))
                # Quitar row_num del resultado
                log.pop('row_num', None)
                # Convertir fecha a ISO
                if log.get('fecha'):
                    log['fecha'] = log['fecha'].isoformat()
                # Parsear detalles JSON
                if log.get('detalles'):
                    try:
                        log['detalles'] = json.loads(log['detalles'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                logs.append(log)

            return logs
        except Exception as e:
            print(f"Error getting audit logs: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def count_logs(empresa_id=None, connection_id=None, user_id=None,
                   username=None, accion=None, fecha_desde=None, fecha_hasta=None,
                   resultado=None):
        """
        Contar logs para paginacion

        Returns:
            int: Numero total de logs que coinciden con los filtros
        """
        conn = Database.get_connection(connection_id)
        cursor = conn.cursor()
        try:
            query = "SELECT COUNT(*) FROM audit_log WHERE 1=1"
            params = []

            if empresa_id:
                query += " AND empresa_id = ?"
                params.append(empresa_id)

            # connection_id solo se usa para la conexión, no para filtrar
            # (la columna no existe en la tabla)

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if username:
                query += " AND username LIKE ?"
                params.append(f"%{username}%")

            if accion:
                query += " AND accion = ?"
                params.append(accion)

            if fecha_desde:
                query += " AND fecha >= ?"
                params.append(f"{fecha_desde} 00:00:00")

            if fecha_hasta:
                query += " AND fecha <= ?"
                params.append(f"{fecha_hasta} 23:59:59")

            if resultado:
                query += " AND resultado = ?"
                params.append(resultado)

            cursor.execute(query, params)
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error counting audit logs: {e}")
            return 0
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_actions_summary(empresa_id=None, connection_id=None, dias=30):
        """
        Obtener resumen de acciones por tipo (para graficos)

        Args:
            empresa_id: Filtrar por empresa
            connection_id: ID de conexion para obtener BD
            dias: Numero de dias hacia atras

        Returns:
            list: Lista de {accion, count}
        """
        conn = Database.get_connection(connection_id)
        cursor = conn.cursor()
        try:
            query = """
                SELECT accion, COUNT(*) as count
                FROM audit_log
                WHERE fecha >= DATEADD(DAY, ?, GETDATE())
            """
            params = [-dias]

            if empresa_id:
                query += " AND empresa_id = ?"
                params.append(empresa_id)

            query += " GROUP BY accion ORDER BY count DESC"

            cursor.execute(query, params)
            return [{'accion': row[0], 'count': row[1]} for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting actions summary: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_results_summary(empresa_id=None, connection_id=None, dias=30):
        """
        Obtener resumen de resultados (SUCCESS/FAILED/BLOCKED)

        Args:
            empresa_id: Filtrar por empresa
            connection_id: ID de conexion para obtener BD
            dias: Numero de dias hacia atras

        Returns:
            list: Lista de {resultado, count}
        """
        conn = Database.get_connection(connection_id)
        cursor = conn.cursor()
        try:
            query = """
                SELECT resultado, COUNT(*) as count
                FROM audit_log
                WHERE fecha >= DATEADD(DAY, ?, GETDATE())
            """
            params = [-dias]

            if empresa_id:
                query += " AND empresa_id = ?"
                params.append(empresa_id)

            query += " GROUP BY resultado"

            cursor.execute(query, params)
            return [{'resultado': row[0], 'count': row[1]} for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting results summary: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def cleanup_old_logs(connection_id=None, days=90):
        """
        Eliminar logs antiguos

        Args:
            connection_id: ID de conexion para obtener BD
            days: Eliminar logs mas antiguos que este numero de dias

        Returns:
            int: Numero de registros eliminados
        """
        conn = Database.get_connection(connection_id)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM audit_log
                WHERE fecha < DATEADD(DAY, ?, GETDATE())
            """, (-days,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        except Exception as e:
            print(f"Error cleaning up audit logs: {e}")
            return 0
        finally:
            cursor.close()
            conn.close()
