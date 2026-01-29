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
# ARCHIVO: models/empresa_logo_model.py
# ============================================
from config.database import Database
import base64

class EmpresaLogoModel:
    """Modelo para gestionar logos y favicons por empresa"""

    @staticmethod
    def get_logo(empresa_id, connection=None):
        """Obtiene el logo de una empresa en formato binario"""
        conn = Database.get_connection(connection)
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT logo FROM empresa_logo WHERE codigo = ?
            """, (empresa_id,))

            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
            return None
        except Exception as e:
            print(f"Error al obtener logo: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_logo_base64(empresa_id):
        """Obtiene el logo de una empresa en formato base64"""
        logo = EmpresaLogoModel.get_logo(empresa_id)
        if logo:
            return base64.b64encode(logo).decode('utf-8')
        return None

    @staticmethod
    def get_favicon(empresa_id, connection=None):
        """Obtiene el favicon de una empresa en formato binario"""
        conn = Database.get_connection(connection)
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT favicon FROM empresa_logo WHERE codigo = ?
            """, (empresa_id,))

            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
            return None
        except Exception as e:
            print(f"Error al obtener favicon: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_favicon_base64(empresa_id):
        """Obtiene el favicon de una empresa en formato base64"""
        favicon = EmpresaLogoModel.get_favicon(empresa_id)
        if favicon:
            return base64.b64encode(favicon).decode('utf-8')
        return None

    @staticmethod
    def exists(empresa_id, connection=None):
        """Verifica si existe configuración de logo para una empresa"""
        conn = Database.get_connection(connection)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM empresa_logo WHERE codigo = ?
            """, (empresa_id,))

            row = cursor.fetchone()
            return row[0] > 0 if row else False
        except Exception as e:
            print(f"Error al verificar empresa_logo: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def save_logo(empresa_id, logo_bytes, connection=None):
        """Guarda o actualiza el logo de una empresa"""
        conn = Database.get_connection(connection)
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Verificar si existe
            if EmpresaLogoModel.exists(empresa_id, connection):
                cursor.execute("""
                    UPDATE empresa_logo
                    SET logo = ?, fecha_modificacion = GETDATE()
                    WHERE codigo = ?
                """, (logo_bytes, empresa_id))
            else:
                cursor.execute("""
                    INSERT INTO empresa_logo (codigo, logo)
                    VALUES (?, ?)
                """, (empresa_id, logo_bytes))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar logo: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def save_favicon(empresa_id, favicon_bytes, connection=None):
        """Guarda o actualiza el favicon de una empresa"""
        conn = Database.get_connection(connection)
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Verificar si existe
            if EmpresaLogoModel.exists(empresa_id, connection):
                cursor.execute("""
                    UPDATE empresa_logo
                    SET favicon = ?, fecha_modificacion = GETDATE()
                    WHERE codigo = ?
                """, (favicon_bytes, empresa_id))
            else:
                cursor.execute("""
                    INSERT INTO empresa_logo (codigo, favicon)
                    VALUES (?, ?)
                """, (empresa_id, favicon_bytes))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar favicon: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_logo(empresa_id, connection=None):
        """Elimina el logo de una empresa (pone NULL)"""
        conn = Database.get_connection(connection)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE empresa_logo
                SET logo = NULL, fecha_modificacion = GETDATE()
                WHERE codigo = ?
            """, (empresa_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar logo: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_favicon(empresa_id, connection=None):
        """Elimina el favicon de una empresa (pone NULL)"""
        conn = Database.get_connection(connection)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE empresa_logo
                SET favicon = NULL, fecha_modificacion = GETDATE()
                WHERE codigo = ?
            """, (empresa_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar favicon: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_invertir_logo(empresa_id, connection=None):
        """Obtiene si el logo debe invertirse para una empresa"""
        conn = Database.get_connection(connection)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT invertir_logo FROM empresa_logo WHERE codigo = ?
            """, (empresa_id,))

            row = cursor.fetchone()
            if row and row[0]:
                return bool(row[0])
            return False
        except Exception as e:
            print(f"Error al obtener invertir_logo: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def set_invertir_logo(empresa_id, invertir, connection=None):
        """Establece si el logo debe invertirse"""
        conn = Database.get_connection(connection)
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Verificar si existe
            if EmpresaLogoModel.exists(empresa_id, connection):
                cursor.execute("""
                    UPDATE empresa_logo
                    SET invertir_logo = ?, fecha_modificacion = GETDATE()
                    WHERE codigo = ?
                """, (1 if invertir else 0, empresa_id))
            else:
                cursor.execute("""
                    INSERT INTO empresa_logo (codigo, invertir_logo)
                    VALUES (?, ?)
                """, (empresa_id, 1 if invertir else 0))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar invertir_logo: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_config(empresa_id, connection=None):
        """Obtiene toda la configuración de logo de una empresa"""
        conn = Database.get_connection(connection)
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT codigo, invertir_logo,
                       CASE WHEN logo IS NOT NULL THEN 1 ELSE 0 END as tiene_logo,
                       CASE WHEN favicon IS NOT NULL THEN 1 ELSE 0 END as tiene_favicon,
                       ISNULL(tema, 'rubi') as tema
                FROM empresa_logo WHERE codigo = ?
            """, (empresa_id,))

            row = cursor.fetchone()
            if row:
                return {
                    'empresa_id': row[0],
                    'invertir_logo': bool(row[1]) if row[1] else False,
                    'tiene_logo': bool(row[2]),
                    'tiene_favicon': bool(row[3]),
                    'tema': row[4] or 'rubi'
                }
            return None
        except Exception as e:
            print(f"Error al obtener config: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_tema(empresa_id, connection=None):
        """Obtiene el tema de colores de una empresa"""
        conn = Database.get_connection(connection)
        if not conn:
            return 'rubi'

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ISNULL(tema, 'rubi') FROM empresa_logo WHERE codigo = ?
            """, (empresa_id,))

            row = cursor.fetchone()
            if row:
                return row[0] or 'rubi'
            return 'rubi'
        except Exception as e:
            print(f"Error al obtener tema: {e}")
            return 'rubi'
        finally:
            conn.close()

    @staticmethod
    def set_tema(empresa_id, tema, connection=None):
        """Establece el tema de colores de una empresa"""
        # Validar que el tema sea válido
        temas_validos = ['rubi', 'zafiro', 'esmeralda', 'amatista', 'ambar', 'grafito',
                         'corporativo', 'ejecutivo', 'oceano', 'bosque', 'vino',
                         'medianoche', 'titanio', 'bronce']
        if tema not in temas_validos:
            return False

        conn = Database.get_connection(connection)
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Verificar si existe
            if EmpresaLogoModel.exists(empresa_id, connection):
                cursor.execute("""
                    UPDATE empresa_logo
                    SET tema = ?, fecha_modificacion = GETDATE()
                    WHERE codigo = ?
                """, (tema, empresa_id))
            else:
                cursor.execute("""
                    INSERT INTO empresa_logo (codigo, tema)
                    VALUES (?, ?)
                """, (empresa_id, tema))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar tema: {e}")
            return False
        finally:
            conn.close()
