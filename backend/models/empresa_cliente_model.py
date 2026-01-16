# ============================================================
# ARCHIVO: models/empresa_cliente_model.py
# Modelo para obtener datos de conexión por empresa
# ============================================================

from config.database_central import DatabaseCentral

# Caché de conexiones para evitar consultas repetidas
_cache_empresas = {}


class EmpresaClienteModel:
    """Modelo para acceder a la tabla empresa_cliente en BD central"""

    @staticmethod
    def get_by_id(empresa_cli_id):
        """
        Obtiene los datos de conexión de una empresa por su ID.

        Args:
            empresa_cli_id: ID de la empresa (empresa_cli_id)

        Returns:
            dict con datos de conexión o None si no existe
        """
        # Verificar caché primero
        if empresa_cli_id in _cache_empresas:
            return _cache_empresas[empresa_cli_id]

        conn = None
        try:
            conn = DatabaseCentral.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    empresa_cli_id,
                    empresa_cli_nombre,
                    empresa_cli_dbserver,
                    empresa_cli_dbport,
                    empresa_cli_dblogin,
                    empresa_cli_dbpass,
                    empresa_cli_dbname,
                    empresa_cli_correo_id,
                    empresa_cli_key_ws,
                    empresa_cli_cif,
                    empresa_cli_traductor,
                    empresa_cli_tipo,
                    empresa_erp
                FROM empresa_cliente
                WHERE empresa_cli_id = ?
            """
            cursor.execute(query, (empresa_cli_id,))
            row = cursor.fetchone()

            if row:
                empresa = {
                    'empresa_cli_id': int(row.empresa_cli_id) if row.empresa_cli_id else None,
                    'nombre': row.empresa_cli_nombre,
                    'dbserver': row.empresa_cli_dbserver,
                    'dbport': int(row.empresa_cli_dbport) if row.empresa_cli_dbport else 1433,
                    'dblogin': row.empresa_cli_dblogin,
                    'dbpass': row.empresa_cli_dbpass,
                    'dbname': row.empresa_cli_dbname,
                    'correo_id': int(row.empresa_cli_correo_id) if row.empresa_cli_correo_id else None,
                    'key_ws': row.empresa_cli_key_ws,
                    'cif': row.empresa_cli_cif,
                    'traductor': row.empresa_cli_traductor,
                    'tipo': int(row.empresa_cli_tipo) if row.empresa_cli_tipo else None,
                    'empresa_erp': row.empresa_erp
                }
                # Guardar en caché
                _cache_empresas[empresa_cli_id] = empresa
                return empresa

            return None

        except Exception as e:
            print(f"[ERROR] EmpresaClienteModel.get_by_id: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def clear_cache():
        """Limpia la caché de empresas"""
        global _cache_empresas
        _cache_empresas = {}

    @staticmethod
    def get_all():
        """Obtiene todas las empresas (para administración)"""
        conn = None
        try:
            conn = DatabaseCentral.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    empresa_cli_id,
                    empresa_cli_nombre,
                    empresa_cli_dbserver,
                    empresa_cli_dbport,
                    empresa_cli_dbname,
                    empresa_cli_cif,
                    empresa_cli_tipo,
                    empresa_erp
                FROM empresa_cliente
                ORDER BY empresa_cli_nombre
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            empresas = []
            for row in rows:
                empresas.append({
                    'empresa_cli_id': int(row.empresa_cli_id) if row.empresa_cli_id else None,
                    'nombre': row.empresa_cli_nombre,
                    'dbserver': row.empresa_cli_dbserver,
                    'dbport': int(row.empresa_cli_dbport) if row.empresa_cli_dbport else 1433,
                    'dbname': row.empresa_cli_dbname,
                    'cif': row.empresa_cli_cif,
                    'tipo': int(row.empresa_cli_tipo) if row.empresa_cli_tipo else None,
                    'empresa_erp': row.empresa_erp
                })
            return empresas

        except Exception as e:
            print(f"[ERROR] EmpresaClienteModel.get_all: {e}")
            return []
        finally:
            if conn:
                conn.close()
