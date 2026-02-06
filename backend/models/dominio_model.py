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
# Fecha : 2026-02-05
# ============================================================

# ============================================
# ARCHIVO: models/dominio_model.py
# Modelo para mapeo de dominios a connection_id
# Usa BD Central (jobers_control_usuarios)
# ============================================

from config.database_central import DatabaseCentral


class DominioModel:
    """
    Modelo para gestionar el mapeo de dominios a connection_id.
    Permite que cada subdominio tenga su propia conexión a BD de cliente.
    """

    @staticmethod
    def get_connection_by_domain(dominio):
        """
        Obtiene el connection_id para un dominio dado.

        Args:
            dominio: El dominio o subdominio (ej: 'empresa1.tudominio.com')

        Returns:
            connection_id (str) si existe, None si no se encuentra
        """
        try:
            conn = DatabaseCentral.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT connection_id
                FROM dominios
                WHERE dominio = ? AND activo = 1
            """, (dominio,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return str(row[0])
            return None

        except Exception as e:
            print(f"Error obteniendo connection por dominio: {e}")
            return None

    @staticmethod
    def get_all():
        """
        Obtiene todos los dominios configurados.

        Returns:
            Lista de diccionarios con los dominios
        """
        try:
            conn = DatabaseCentral.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, dominio, connection_id, descripcion, activo,
                       fecha_creacion, fecha_modificacion
                FROM dominios
                ORDER BY dominio
            """)

            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            print(f"Error obteniendo dominios: {e}")
            return []

    @staticmethod
    def create(dominio, connection_id, descripcion=None):
        """
        Crea un nuevo mapeo de dominio.

        Args:
            dominio: El dominio (ej: 'empresa1.tudominio.com')
            connection_id: ID de conexión en empresas_cli
            descripcion: Descripción opcional

        Returns:
            ID del registro creado o None si falla
        """
        try:
            conn = DatabaseCentral.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO dominios (dominio, connection_id, descripcion)
                VALUES (?, ?, ?)
            """, (dominio, connection_id, descripcion))

            cursor.execute("SELECT SCOPE_IDENTITY()")
            new_id = cursor.fetchone()[0]

            conn.commit()
            conn.close()

            return new_id

        except Exception as e:
            print(f"Error creando dominio: {e}")
            return None

    @staticmethod
    def update(id, dominio=None, connection_id=None, descripcion=None, activo=None):
        """
        Actualiza un mapeo de dominio existente.

        Args:
            id: ID del registro a actualizar
            dominio, connection_id, descripcion, activo: Campos a actualizar (opcional)

        Returns:
            True si se actualizó correctamente, False si falla
        """
        try:
            conn = DatabaseCentral.get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if dominio is not None:
                updates.append("dominio = ?")
                params.append(dominio)
            if connection_id is not None:
                updates.append("connection_id = ?")
                params.append(connection_id)
            if descripcion is not None:
                updates.append("descripcion = ?")
                params.append(descripcion)
            if activo is not None:
                updates.append("activo = ?")
                params.append(1 if activo else 0)

            if not updates:
                return False

            updates.append("fecha_modificacion = GETDATE()")
            params.append(id)

            query = f"UPDATE dominios SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Error actualizando dominio: {e}")
            return False

    @staticmethod
    def delete(id):
        """
        Elimina un mapeo de dominio.

        Args:
            id: ID del registro a eliminar

        Returns:
            True si se eliminó correctamente, False si falla
        """
        try:
            conn = DatabaseCentral.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM dominios WHERE id = ?", (id,))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Error eliminando dominio: {e}")
            return False
