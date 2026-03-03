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
import io
from PIL import Image


class ImagenModel:
    @staticmethod
    def _resize_image(image_data, max_width=400):
        """Redimensiona una imagen manteniendo proporciones.
        Devuelve bytes JPEG calidad 85. Si ya es menor que max_width, la devuelve tal cual."""
        try:
            img = Image.open(io.BytesIO(image_data))
            if img.width <= max_width:
                return image_data
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            return buffer.getvalue()
        except Exception:
            return image_data

    @staticmethod
    def get_by_codigo(codigo, empresa_id=None):
        """Obtiene todas las imágenes de un artículo por código"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        if empresa_id:
            cursor.execute("""
                SELECT id, codigo, imagen
                FROM view_articulo_imagen
                WHERE codigo = ? AND empresa = ?
            """, (codigo, empresa_id))
        else:
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
    def get_by_id(id, empresa_id=None):
        """Obtiene una imagen por su ID"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        if empresa_id:
            cursor.execute("""
                SELECT id, codigo, imagen
                FROM view_articulo_imagen
                WHERE id = ? AND empresa = ?
            """, (id, empresa_id))
        else:
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
    def get_primera_imagen(codigo, quality='thumb', empresa_id=None):
        """Obtiene el thumbnail de la primera imagen (para grid de tarjetas)
        quality='thumb': usa thumbnail si existe (pequeño, rápido)
        quality='grid': usa imagen original redimensionada a 400px (nítido para grid)"""
        imagen = None
        empresa_filter = " AND empresa = ?" if empresa_id else ""
        params = (codigo, empresa_id) if empresa_id else (codigo,)

        try:
            # Intentar con columna thumbnail (si existe)
            conn = Database.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT TOP 1 id, codigo, thumbnail, imagen
                FROM view_articulo_imagen
                WHERE codigo = ?{empresa_filter}
                ORDER BY id
            """, params)

            row = cursor.fetchone()
            if row:
                if quality == 'grid' and row[3]:
                    img_data = ImagenModel._resize_image(row[3])
                else:
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
                cursor.execute(f"""
                    SELECT TOP 1 id, codigo, imagen
                    FROM view_articulo_imagen
                    WHERE codigo = ?{empresa_filter}
                    ORDER BY id
                """, params)

                row = cursor.fetchone()
                if row and row[2]:
                    img_data = row[2]
                    if quality == 'grid':
                        img_data = ImagenModel._resize_image(img_data)
                    imagen = {
                        'id': row[0],
                        'codigo': row[1],
                        'imagen': base64.b64encode(img_data).decode('utf-8')
                    }
                cursor.close()
                conn.close()
            except Exception:
                pass

        return imagen

    @staticmethod
    def tiene_imagen(codigo, empresa_id=None):
        """Verifica si un artículo tiene al menos una imagen"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        if empresa_id:
            cursor.execute("""
                SELECT TOP 1 1
                FROM view_articulo_imagen
                WHERE codigo = ? AND empresa = ?
            """, (codigo, empresa_id))
        else:
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
    def get_thumbnails_batch(codigos, quality='thumb', empresa_id=None):
        """Obtiene thumbnails de múltiples artículos en una sola consulta (batch loading)
        quality='thumb': usa thumbnail si existe (pequeño, rápido)
        quality='grid': usa imagen original redimensionada a 400px (nítido para grid)
        Retorna un diccionario {codigo: imagen_base64}"""
        if not codigos:
            return {}

        # Limpiar espacios de los códigos
        codigos = [c.strip() if isinstance(c, str) else c for c in codigos]

        # Crear placeholders para IN clause
        placeholders = ','.join(['?' for _ in codigos])
        empresa_filter = " AND empresa = ?" if empresa_id else ""
        params = codigos + [empresa_id] if empresa_id else codigos
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
                    WHERE codigo IN ({placeholders}){empresa_filter}
                )
                SELECT codigo, thumbnail, imagen
                FROM FirstImages
                WHERE rn = 1
            """, params)

            for row in cursor.fetchall():
                codigo = row[0].strip() if row[0] else row[0]
                if quality == 'grid' and row[2]:
                    img_data = ImagenModel._resize_image(row[2])
                else:
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
                        WHERE codigo IN ({placeholders}){empresa_filter}
                    )
                    SELECT codigo, imagen
                    FROM FirstImages
                    WHERE rn = 1
                """, params)

                for row in cursor.fetchall():
                    codigo = row[0].strip() if row[0] else row[0]
                    if row[1]:
                        img_data = row[1]
                        if quality == 'grid':
                            img_data = ImagenModel._resize_image(img_data)
                        thumbnails[codigo] = base64.b64encode(img_data).decode('utf-8')

                cursor.close()
                conn.close()
            except Exception:
                pass

        return thumbnails
