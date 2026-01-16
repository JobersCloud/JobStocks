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
# ARCHIVO: models/ficha_tecnica_model.py
# Descripcion: Modelo para fichas tecnicas de articulos (PDF)
# ============================================
from config.database import Database
import base64


class FichaTecnicaModel:
    @staticmethod
    def get_by_codigo(codigo, empresa_id='1'):
        """
        Obtiene la ficha tecnica de un articulo por codigo.

        Args:
            codigo: Codigo del articulo
            empresa_id: ID de la empresa

        Returns:
            dict: Ficha tecnica en base64 o None si no existe
        """
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT empresa, articulo, ficha
            FROM view_externos_articulo_ficha_tecnica
            WHERE articulo = ? AND empresa = ?
        """, (codigo, empresa_id))

        row = cursor.fetchone()
        ficha = None

        if row and row[2]:
            ficha = {
                'empresa': row[0],
                'articulo': row[1],
                'ficha': base64.b64encode(row[2]).decode('utf-8')
            }

        cursor.close()
        conn.close()
        return ficha

    @staticmethod
    def exists(codigo, empresa_id='1'):
        """
        Verifica si existe una ficha tecnica para el articulo.

        Args:
            codigo: Codigo del articulo
            empresa_id: ID de la empresa

        Returns:
            bool: True si existe, False si no
        """
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM view_externos_articulo_ficha_tecnica
            WHERE articulo = ? AND empresa = ?
        """, (codigo, empresa_id))

        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0
