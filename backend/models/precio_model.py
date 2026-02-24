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
# Fecha : 2026-02-23
# ============================================================

# ============================================
# ARCHIVO: models/precio_model.py
# ============================================
from config.database import Database
import logging

logger = logging.getLogger(__name__)


class PrecioModel:
    @staticmethod
    def get_precio(empresa_id, codigo, calidad, connection=None):
        """Obtiene el precio de un artículo por código y calidad.

        Args:
            empresa_id: ID empresa ERP
            codigo: Código del artículo
            calidad: Calidad del artículo
            connection: ID para conexión (opcional)

        Returns:
            float o None si no existe precio
        """
        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT precio
                FROM view_externos_articulos_precios
                WHERE empresa = ? AND codigo = ? AND calidad = ?
            """, (empresa_id, codigo, calidad))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return float(row[0]) if row else None
        except Exception:
            # La vista puede no existir en algunas instalaciones
            return None

    @staticmethod
    def get_precios_batch(empresa_id, stocks, connection=None):
        """Obtiene precios para un lote de artículos.

        Args:
            empresa_id: ID empresa ERP
            stocks: Lista de dicts con 'codigo' y 'calidad'
            connection: ID para conexión (opcional)

        Returns:
            dict keyed by (codigo, calidad) → precio (float)
        """
        if not stocks:
            return {}

        try:
            conn = Database.get_connection(connection)
            cursor = conn.cursor()

            # Obtener todos los precios de la empresa de una vez
            cursor.execute("""
                SELECT codigo, calidad, precio
                FROM view_externos_articulos_precios
                WHERE empresa = ?
            """, (empresa_id,))

            precios = {}
            for row in cursor.fetchall():
                key = (row[0], row[1])
                precios[key] = float(row[2]) if row[2] else None

            cursor.close()
            conn.close()
            return precios
        except Exception as e:
            # La vista puede no existir en algunas instalaciones
            return {}

    @staticmethod
    def inyectar_precios(empresa_id, stocks, connection=None):
        """Inyecta precios en una lista de stocks.

        Modifica los dicts in-place añadiendo el campo 'precio'.

        Args:
            empresa_id: ID empresa ERP
            stocks: Lista de dicts de stock
            connection: ID para conexión (opcional)
        """
        precios = PrecioModel.get_precios_batch(empresa_id, stocks, connection)
        if not precios:
            return

        for stock in stocks:
            key = (stock.get('codigo'), stock.get('calidad'))
            precio = precios.get(key)
            if precio is not None:
                stock['precio'] = precio
