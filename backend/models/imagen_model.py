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
# ARCHIVO: models/imagen_model.py
# ============================================
from config.database import Database
import base64


class ImagenModel:
    @staticmethod
    def get_by_codigo(codigo):
        """Obtiene todas las imágenes de un artículo por código"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, codigo, imagen
            FROM view_articulo_imagen
            WHERE codigo = ?
        """, (codigo,))

        imagenes = []
        for row in cursor.fetchall():
            # Convertir imagen binaria a base64 para enviar al frontend
            imagen_base64 = None
            if row[2]:
                imagen_base64 = base64.b64encode(row[2]).decode('utf-8')

            imagenes.append({
                'id': row[0],
                'codigo': row[1],
                'imagen': imagen_base64
            })

        cursor.close()
        conn.close()
        return imagenes

    @staticmethod
    def get_by_id(id):
        """Obtiene una imagen por su ID"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, codigo, imagen
            FROM view_articulo_imagen
            WHERE id = ?
        """, (id,))

        row = cursor.fetchone()
        imagen = None

        if row:
            imagen_base64 = None
            if row[2]:
                imagen_base64 = base64.b64encode(row[2]).decode('utf-8')

            imagen = {
                'id': row[0],
                'codigo': row[1],
                'imagen': imagen_base64
            }

        cursor.close()
        conn.close()
        return imagen

    @staticmethod
    def get_primera_imagen(codigo):
        """Obtiene el thumbnail de la primera imagen (para grid de tarjetas)
        Usa el campo thumbnail si existe, sino usa la imagen original"""
        imagen = None

        try:
            # Intentar con columna thumbnail (si existe)
            conn = Database.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 id, codigo, thumbnail, imagen
                FROM view_articulo_imagen
                WHERE codigo = ?
                ORDER BY id
            """, (codigo,))

            row = cursor.fetchone()
            if row:
                # Preferir thumbnail si existe, sino usar imagen completa
                img_data = row[2] if row[2] else row[3]
                if img_data:
                    imagen = {
                        'id': row[0],
                        'codigo': row[1],
                        'imagen': base64.b64encode(img_data).decode('utf-8')
                    }
            cursor.close()
            conn.close()

        except Exception:
            # Fallback: si no existe columna thumbnail, usar solo imagen
            try:
                conn = Database.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT TOP 1 id, codigo, imagen
                    FROM view_articulo_imagen
                    WHERE codigo = ?
                    ORDER BY id
                """, (codigo,))

                row = cursor.fetchone()
                if row and row[2]:
                    imagen = {
                        'id': row[0],
                        'codigo': row[1],
                        'imagen': base64.b64encode(row[2]).decode('utf-8')
                    }
                cursor.close()
                conn.close()
            except Exception:
                pass

        return imagen

    @staticmethod
    def tiene_imagen(codigo):
        """Verifica si un artículo tiene al menos una imagen"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 1 1
            FROM view_articulo_imagen
            WHERE codigo = ?
        """, (codigo,))

        tiene = cursor.fetchone() is not None

        cursor.close()
        conn.close()
        return tiene

    @staticmethod
    def get_thumbnails_batch(codigos):
        """Obtiene thumbnails de múltiples artículos en una sola consulta (batch loading)
        Retorna un diccionario {codigo: imagen_base64}"""
        if not codigos:
            return {}

        # Limpiar espacios de los códigos
        codigos = [c.strip() if isinstance(c, str) else c for c in codigos]

        # Crear placeholders para IN clause
        placeholders = ','.join(['?' for _ in codigos])
        thumbnails = {}

        try:
            # Intentar con columna thumbnail (si existe)
            conn = Database.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"""
                WITH FirstImages AS (
                    SELECT codigo, thumbnail, imagen,
                           ROW_NUMBER() OVER (PARTITION BY codigo ORDER BY id) as rn
                    FROM view_articulo_imagen
                    WHERE codigo IN ({placeholders})
                )
                SELECT codigo, thumbnail, imagen
                FROM FirstImages
                WHERE rn = 1
            """, codigos)

            for row in cursor.fetchall():
                codigo = row[0].strip() if row[0] else row[0]
                img_data = row[1] if row[1] else row[2]
                if img_data:
                    thumbnails[codigo] = base64.b64encode(img_data).decode('utf-8')

            cursor.close()
            conn.close()

        except Exception:
            # Fallback: si no existe columna thumbnail, usar solo imagen
            try:
                conn = Database.get_connection()
                cursor = conn.cursor()
                cursor.execute(f"""
                    WITH FirstImages AS (
                        SELECT codigo, imagen,
                               ROW_NUMBER() OVER (PARTITION BY codigo ORDER BY id) as rn
                        FROM view_articulo_imagen
                        WHERE codigo IN ({placeholders})
                    )
                    SELECT codigo, imagen
                    FROM FirstImages
                    WHERE rn = 1
                """, codigos)

                for row in cursor.fetchall():
                    codigo = row[0].strip() if row[0] else row[0]
                    if row[1]:
                        thumbnails[codigo] = base64.b64encode(row[1]).decode('utf-8')

                cursor.close()
                conn.close()
            except Exception:
                pass

        return thumbnails
