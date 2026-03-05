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
# Fecha : 2026-03-04
# ============================================================

# ============================================
# ARCHIVO: models/favoritos_model.py
# Descripcion: Modelo para gestión de productos favoritos
# ============================================
from config.database import Database


def _s(val):
    """Strip whitespace from CHAR fields returned by SQL Server."""
    return val.strip() if isinstance(val, str) else val


class FavoritosModel:
    @staticmethod
    def toggle(user_id, empresa_id, codigo):
        """
        Toggle favorito: si existe lo elimina, si no existe lo crea.

        Returns:
            dict: {is_favorite: bool}
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        try:
            # Comprobar si ya existe
            cursor.execute("""
                SELECT id FROM favoritos
                WHERE user_id = ? AND empresa_id = ? AND RTRIM(codigo) = ?
            """, (user_id, empresa_id, codigo.strip()))

            row = cursor.fetchone()

            if row:
                # Existe → eliminar
                cursor.execute("DELETE FROM favoritos WHERE id = ?", (row[0],))
                conn.commit()
                return {'is_favorite': False}
            else:
                # No existe → crear
                cursor.execute("""
                    INSERT INTO favoritos (user_id, empresa_id, codigo)
                    VALUES (?, ?, ?)
                """, (user_id, empresa_id, codigo.strip()))
                conn.commit()
                return {'is_favorite': True}
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_by_user(user_id, empresa_id):
        """
        Lista códigos favoritos del usuario.

        Returns:
            list: Lista de códigos favoritos
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT RTRIM(codigo) FROM favoritos
            WHERE user_id = ? AND empresa_id = ?
            ORDER BY fecha_creacion DESC
        """, (user_id, empresa_id))

        codigos = [row[0] for row in cursor.fetchall()]
        conn.close()
        return codigos

    @staticmethod
    def check_batch(user_id, empresa_id, codigos):
        """
        Comprueba múltiples códigos de golpe para la grid.

        Returns:
            set: Set de códigos que son favoritos
        """
        if not codigos:
            return set()

        conn = Database.get_connection()
        cursor = conn.cursor()

        # Usar IN con parámetros
        placeholders = ','.join(['?' for _ in codigos])
        params = [user_id, empresa_id] + [c.strip() for c in codigos]

        cursor.execute(f"""
            SELECT RTRIM(codigo) FROM favoritos
            WHERE user_id = ? AND empresa_id = ?
            AND RTRIM(codigo) IN ({placeholders})
        """, params)

        result = {row[0] for row in cursor.fetchall()}
        conn.close()
        return result

    @staticmethod
    def get_favorites_with_stock(user_id, empresa_id):
        """
        Obtiene favoritos con datos completos del producto (LEFT JOIN con stock).
        Usa subquery con ROW_NUMBER para evitar duplicados cuando un producto
        tiene múltiples filas en stock (distintas calidades/tonos/calibres).

        Returns:
            list: Lista de favoritos con datos de stock
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT f.id, RTRIM(f.codigo) as codigo, f.fecha_creacion,
                   RTRIM(s.descripcion) as descripcion,
                   RTRIM(s.formato) as formato,
                   RTRIM(s.serie) as serie,
                   RTRIM(s.calidad) as calidad,
                   RTRIM(s.color) as color,
                   RTRIM(s.tono) as tono,
                   RTRIM(s.calibre) as calibre,
                   s.total_existencias,
                   RTRIM(s.unidad) as unidad
            FROM favoritos f
            LEFT JOIN (
                SELECT codigo, empresa,
                       MAX(descripcion) as descripcion,
                       MAX(formato) as formato,
                       MAX(serie) as serie,
                       MAX(calidad) as calidad,
                       MAX(color) as color,
                       MAX(tono) as tono,
                       MAX(calibre) as calibre,
                       SUM(existencias) as total_existencias,
                       MAX(unidad) as unidad
                FROM view_externos_stock
                GROUP BY codigo, empresa
            ) s ON RTRIM(f.codigo) = RTRIM(s.codigo) AND f.empresa_id = s.empresa
            WHERE f.user_id = ? AND f.empresa_id = ?
            ORDER BY f.fecha_creacion DESC
        """, (user_id, empresa_id))

        favoritos = []
        for row in cursor.fetchall():
            favoritos.append({
                'id': row[0],
                'codigo': _s(row[1]),
                'fecha_creacion': row[2].isoformat() if row[2] else None,
                'descripcion': _s(row[3]) or '',
                'formato': _s(row[4]) or '',
                'serie': _s(row[5]) or '',
                'calidad': _s(row[6]) or '',
                'color': _s(row[7]) or '',
                'tono': _s(row[8]) or '',
                'calibre': _s(row[9]) or '',
                'existencias': float(row[10]) if row[10] else 0,
                'unidad': _s(row[11]) or ''
            })

        conn.close()
        return favoritos

    @staticmethod
    def get_frequent_products(user_id, empresa_id):
        """
        Obtiene productos más pedidos por el usuario desde propuestas_lineas.

        Returns:
            list: Top 50 productos con veces_pedido, total_cantidad, ultima_fecha
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP 50
                   RTRIM(pl.codigo) as codigo,
                   RTRIM(MAX(pl.descripcion)) as descripcion,
                   RTRIM(MAX(pl.formato)) as formato,
                   COUNT(*) as veces_pedido,
                   SUM(pl.cantidad_solicitada) as total_cantidad,
                   MAX(p.fecha) as ultima_fecha
            FROM propuestas_lineas pl
            INNER JOIN propuestas p ON pl.propuesta_id = p.id
            WHERE p.user_id = ? AND p.empresa_id = ?
            GROUP BY RTRIM(pl.codigo)
            ORDER BY COUNT(*) DESC, MAX(p.fecha) DESC
        """, (user_id, empresa_id))

        productos = []
        for row in cursor.fetchall():
            productos.append({
                'codigo': _s(row[0]),
                'descripcion': _s(row[1]) or '',
                'formato': _s(row[2]) or '',
                'veces_pedido': row[3],
                'total_cantidad': float(row[4]) if row[4] else 0,
                'ultima_fecha': row[5].isoformat() if row[5] else None
            })

        conn.close()
        return productos
