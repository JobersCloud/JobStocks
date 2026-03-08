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
    def toggle(user_id, empresa_id, codigo, calidad=None, tono=None, calibre=None, pallet=None, caja=None):
        """
        Toggle favorito: si existe lo elimina, si no existe lo crea.
        Usa clave compuesta: codigo+calidad+tono+calibre+pallet+caja.

        Returns:
            dict: {is_favorite: bool}
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        # Normalizar valores
        codigo = codigo.strip() if codigo else ''
        calidad = (calidad or '').strip()
        tono = (tono or '').strip()
        calibre = (calibre or '').strip()
        pallet = (pallet or '').strip()
        caja = (caja or '').strip()

        try:
            # Comprobar si ya existe con clave compuesta
            cursor.execute("""
                SELECT id FROM favoritos
                WHERE user_id = ? AND empresa_id = ? AND RTRIM(codigo) = ?
                  AND ISNULL(RTRIM(calidad), '') = ?
                  AND ISNULL(RTRIM(tono), '') = ?
                  AND ISNULL(RTRIM(calibre), '') = ?
                  AND ISNULL(RTRIM(pallet), '') = ?
                  AND ISNULL(RTRIM(caja), '') = ?
            """, (user_id, empresa_id, codigo, calidad, tono, calibre, pallet, caja))

            row = cursor.fetchone()

            if row:
                # Existe → eliminar
                cursor.execute("DELETE FROM favoritos WHERE id = ?", (row[0],))
                conn.commit()
                return {'is_favorite': False}
            else:
                # No existe → crear
                cursor.execute("""
                    INSERT INTO favoritos (user_id, empresa_id, codigo, calidad, tono, calibre, pallet, caja)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, empresa_id, codigo, calidad or None, tono or None, calibre or None, pallet or None, caja or None))
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
    def _fav_key(codigo, calidad, tono, calibre, pallet, caja):
        """Genera clave serializada para un favorito."""
        return '|'.join([
            (codigo or '').strip(),
            (calidad or '').strip(),
            (tono or '').strip(),
            (calibre or '').strip(),
            (pallet or '').strip(),
            (caja or '').strip()
        ])

    @staticmethod
    def check_batch(user_id, empresa_id, items):
        """
        Comprueba múltiples items de golpe para la grid.
        items: lista de objetos {codigo, calidad, tono, calibre, pallet, caja}
               o lista de strings (códigos simples, retrocompatible).

        Returns:
            set: Set de claves serializadas "codigo|calidad|tono|calibre|pallet|caja"
        """
        if not items:
            return set()

        conn = Database.get_connection()
        cursor = conn.cursor()

        # Extraer códigos únicos para filtro IN
        if isinstance(items[0], str):
            codigos_unicos = list(set(c.strip() for c in items))
        else:
            codigos_unicos = list(set(item.get('codigo', '').strip() for item in items))

        placeholders = ','.join(['?' for _ in codigos_unicos])
        params = [user_id, empresa_id] + codigos_unicos

        cursor.execute(f"""
            SELECT RTRIM(codigo),
                   ISNULL(RTRIM(calidad), ''),
                   ISNULL(RTRIM(tono), ''),
                   ISNULL(RTRIM(calibre), ''),
                   ISNULL(RTRIM(pallet), ''),
                   ISNULL(RTRIM(caja), '')
            FROM favoritos
            WHERE user_id = ? AND empresa_id = ?
            AND RTRIM(codigo) IN ({placeholders})
        """, params)

        result = {FavoritosModel._fav_key(row[0], row[1], row[2], row[3], row[4], row[5])
                  for row in cursor.fetchall()}
        conn.close()
        return result

    @staticmethod
    def get_favorites_with_stock(user_id, empresa_id):
        """
        Obtiene favoritos con datos completos del producto (LEFT JOIN con stock).
        Cada favorito es una variante específica (codigo+calidad+tono+calibre+pallet+caja).

        Returns:
            list: Lista de favoritos con datos de stock
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT f.id, RTRIM(f.codigo) as codigo, f.fecha_creacion,
                   ISNULL(RTRIM(s.descripcion), RTRIM(pl.descripcion)) as descripcion,
                   ISNULL(RTRIM(s.formato), RTRIM(pl.formato)) as formato,
                   RTRIM(s.serie) as serie,
                   ISNULL(RTRIM(f.calidad), '') as calidad,
                   RTRIM(s.color) as color,
                   ISNULL(RTRIM(f.tono), '') as tono,
                   ISNULL(RTRIM(f.calibre), '') as calibre,
                   ISNULL(s.existencias, 0) as existencias,
                   RTRIM(s.unidad) as unidad,
                   ISNULL(RTRIM(f.pallet), '') as pallet,
                   ISNULL(RTRIM(f.caja), '') as caja
            FROM favoritos f
            OUTER APPLY (
                SELECT TOP 1 s.descripcion, s.formato, s.serie, s.color,
                       s.existencias, s.unidad
                FROM view_externos_stock s
                WHERE RTRIM(s.codigo) COLLATE DATABASE_DEFAULT = RTRIM(f.codigo)
                  AND s.empresa COLLATE DATABASE_DEFAULT = f.empresa_id
                  AND ISNULL(RTRIM(s.calidad), '') COLLATE DATABASE_DEFAULT = ISNULL(RTRIM(f.calidad), '')
                  AND ISNULL(RTRIM(s.tono), '') COLLATE DATABASE_DEFAULT = ISNULL(RTRIM(f.tono), '')
                  AND ISNULL(RTRIM(s.calibre), '') COLLATE DATABASE_DEFAULT = ISNULL(RTRIM(f.calibre), '')
                ORDER BY s.existencias DESC
            ) s
            OUTER APPLY (
                SELECT TOP 1 pl.descripcion, pl.formato
                FROM propuestas_lineas pl
                INNER JOIN propuestas p ON pl.propuesta_id = p.id
                WHERE RTRIM(pl.codigo) COLLATE DATABASE_DEFAULT = RTRIM(f.codigo)
                  AND p.user_id = ? AND p.empresa_id = ?
                ORDER BY p.fecha DESC
            ) pl
            WHERE f.user_id = ? AND f.empresa_id = ?
            ORDER BY f.fecha_creacion DESC
        """, (user_id, empresa_id, user_id, empresa_id))

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
                'unidad': _s(row[11]) or '',
                'pallet': _s(row[12]) or '',
                'caja': _s(row[13]) or ''
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
                   ISNULL(RTRIM(pl.calidad), '') as calidad,
                   ISNULL(RTRIM(pl.tono), '') as tono,
                   ISNULL(RTRIM(pl.calibre), '') as calibre,
                   ISNULL(RTRIM(pl.pallet), '') as pallet,
                   ISNULL(RTRIM(pl.caja), '') as caja,
                   COUNT(*) as veces_pedido,
                   SUM(pl.cantidad_solicitada) as total_cantidad,
                   MAX(p.fecha) as ultima_fecha
            FROM propuestas_lineas pl
            INNER JOIN propuestas p ON pl.propuesta_id = p.id
            WHERE p.user_id = ? AND p.empresa_id = ?
            GROUP BY RTRIM(pl.codigo), ISNULL(RTRIM(pl.calidad), ''), ISNULL(RTRIM(pl.tono), ''),
                     ISNULL(RTRIM(pl.calibre), ''), ISNULL(RTRIM(pl.pallet), ''), ISNULL(RTRIM(pl.caja), '')
            ORDER BY COUNT(*) DESC, MAX(p.fecha) DESC
        """, (user_id, empresa_id))

        productos = []
        for row in cursor.fetchall():
            productos.append({
                'codigo': _s(row[0]),
                'descripcion': _s(row[1]) or '',
                'formato': _s(row[2]) or '',
                'calidad': _s(row[3]) or '',
                'tono': _s(row[4]) or '',
                'calibre': _s(row[5]) or '',
                'pallet': _s(row[6]) or '',
                'caja': _s(row[7]) or '',
                'veces_pedido': row[8],
                'total_cantidad': float(row[9]) if row[9] else 0,
                'ultima_fecha': row[10].isoformat() if row[10] else None
            })

        conn.close()
        return productos
