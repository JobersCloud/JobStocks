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
    def get_by_codigo(codigo, empresa_id='1', tono=None):
        """
        Obtiene la ficha tecnica de un articulo.
        Prioridad: 1) por empresa+articulo+tono, 2) genérica por empresa+articulo.

        Args:
            codigo: Codigo del articulo
            empresa_id: ID de la empresa
            tono: Tono del articulo (opcional)

        Returns:
            dict: Ficha tecnica en base64 o None si no existe
        """
        conn = Database.get_connection()
        cursor = conn.cursor()
        ficha = None

        # 1) Buscar ficha específica por tono (requiere view_articulo_ficha_tecnica_tono)
        if tono:
            try:
                cursor.execute("""
                    SELECT empresa, articulo, ficha
                    FROM view_articulo_ficha_tecnica_tono WITH (NOLOCK)
                    WHERE articulo = ? AND empresa = ? AND tono = ?
                """, (codigo, empresa_id, tono))
                row = cursor.fetchone()
                if row and row[2]:
                    ficha = {
                        'empresa': row[0],
                        'articulo': row[1],
                        'ficha': base64.b64encode(row[2]).decode('utf-8')
                    }
            except Exception:
                pass  # Vista no existe en esta instalación

        # 2) Fallback: ficha genérica (sin tono)
        if not ficha:
            cursor.execute("""
                SELECT empresa, articulo, ficha
                FROM view_externos_articulo_ficha_tecnica
                WHERE articulo = ? AND empresa = ?
            """, (codigo, empresa_id))
            row = cursor.fetchone()
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
    def exists(codigo, empresa_id='1', tono=None):
        """
        Verifica si existe una ficha tecnica para el articulo.
        Comprueba primero por tono, luego genérica.

        Args:
            codigo: Codigo del articulo
            empresa_id: ID de la empresa
            tono: Tono del articulo (opcional)

        Returns:
            bool: True si existe, False si no
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        # 1) Buscar ficha específica por tono (requiere view_articulo_ficha_tecnica_tono)
        if tono:
            try:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM view_articulo_ficha_tecnica_tono WITH (NOLOCK)
                    WHERE articulo = ? AND empresa = ? AND tono = ?
                """, (codigo, empresa_id, tono))
                if cursor.fetchone()[0] > 0:
                    cursor.close()
                    conn.close()
                    return True
            except Exception:
                pass  # Vista no existe en esta instalación

        # 2) Fallback: ficha genérica
        cursor.execute("""
            SELECT COUNT(*)
            FROM view_externos_articulo_ficha_tecnica
            WHERE articulo = ? AND empresa = ?
        """, (codigo, empresa_id))

        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0
