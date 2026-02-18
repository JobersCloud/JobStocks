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
    COLUMNS_FULL = 'empresa, codigo, razon, domicilio, codpos, poblacion, provincia, pais'
    COLUMNS_BASIC = 'empresa, codigo, razon'

    @staticmethod
    def _get_columns(cursor):
        """Detecta si la vista tiene columnas de dirección (script 32 ejecutado)."""
        try:
            cursor.execute("SELECT COL_LENGTH('view_externos_clientes', 'domicilio')")
            result = cursor.fetchone()
            return ClienteModel.COLUMNS_FULL if result and result[0] is not None else ClienteModel.COLUMNS_BASIC
        except Exception:
            return ClienteModel.COLUMNS_BASIC

    @staticmethod
    def _row_to_dict(row):
        return {
            'empresa': row[0],
            'codigo': row[1],
            'razon': row[2],
            'domicilio': row[3] if len(row) > 3 else None,
            'codpos': row[4] if len(row) > 4 else None,
            'poblacion': row[5] if len(row) > 5 else None,
            'provincia': row[6] if len(row) > 6 else None,
            'pais': row[7] if len(row) > 7 else None
        }

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

        query = f"SELECT {ClienteModel._get_columns(cursor)} FROM view_externos_clientes"
        params = []

        if empresa_id:
            query += " WHERE empresa LIKE ?"
            params.append(f"%{empresa_id}%")

        query += " ORDER BY razon"

        cursor.execute(query, params)
        clientes = [ClienteModel._row_to_dict(row) for row in cursor.fetchall()]
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

        query = f"SELECT {ClienteModel._get_columns(cursor)} FROM view_externos_clientes WHERE codigo = ?"
        params = [codigo]

        if empresa_id:
            query += " AND empresa LIKE ?"
            params.append(f"%{empresa_id}%")

        cursor.execute(query, params)
        row = cursor.fetchone()
        cliente = ClienteModel._row_to_dict(row) if row else None
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

        query = f"SELECT {ClienteModel._get_columns(cursor)} FROM view_externos_clientes WHERE 1=1"
        params = []

        if filtros.get('empresa'):
            query += " AND empresa LIKE ?"
            params.append(f"%{filtros['empresa']}%")

        if filtros.get('razon'):
            query += " AND razon LIKE ?"
            params.append(f"%{filtros['razon']}%")

        query += " ORDER BY razon"

        cursor.execute(query, params)
        clientes = [ClienteModel._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        return clientes
