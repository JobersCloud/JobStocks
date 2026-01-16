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
# ARCHIVO: models/cliente_model.py
# ============================================
from config.database import Database


class ClienteModel:
    @staticmethod
    def get_all(empresa_id=None):
        """
        Obtiene todos los clientes (con filtro opcional por empresa)

        Args:
            empresa_id: Filtrar por empresa (opcional)

        Returns:
            list: Lista de clientes
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT empresa, codigo, razon
            FROM view_externos_clientes
        """
        params = []

        if empresa_id:
            query += " WHERE empresa LIKE ?"
            params.append(f"%{empresa_id}%")

        query += " ORDER BY razon"

        cursor.execute(query, params)

        clientes = []
        for row in cursor.fetchall():
            clientes.append({
                'empresa': row[0],
                'codigo': row[1],
                'razon': row[2]
            })

        conn.close()
        return clientes

    @staticmethod
    def get_by_codigo(codigo, empresa_id=None):
        """
        Obtiene un cliente por código

        Args:
            codigo: Código del cliente
            empresa_id: Filtrar por empresa (opcional)

        Returns:
            dict: Cliente o None si no existe
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT empresa, codigo, razon
            FROM view_externos_clientes
            WHERE codigo = ?
        """
        params = [codigo]

        if empresa_id:
            query += " AND empresa LIKE ?"
            params.append(f"%{empresa_id}%")

        cursor.execute(query, params)
        row = cursor.fetchone()

        cliente = None
        if row:
            cliente = {
                'empresa': row[0],
                'codigo': row[1],
                'razon': row[2]
            }

        conn.close()
        return cliente

    @staticmethod
    def search(filtros):
        """
        Busca clientes con filtros opcionales

        Args:
            filtros: Dict con filtros (empresa, razon)

        Returns:
            list: Lista de clientes filtrados
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT empresa, codigo, razon
            FROM view_externos_clientes
            WHERE 1=1
        """
        params = []

        if filtros.get('empresa'):
            query += " AND empresa LIKE ?"
            params.append(f"%{filtros['empresa']}%")

        if filtros.get('razon'):
            query += " AND razon LIKE ?"
            params.append(f"%{filtros['razon']}%")

        query += " ORDER BY razon"

        cursor.execute(query, params)

        clientes = []
        for row in cursor.fetchall():
            clientes.append({
                'empresa': row[0],
                'codigo': row[1],
                'razon': row[2]
            })

        conn.close()
        return clientes
