# ============================================================
# image_search_model.py - Modelo para busqueda visual CBIR
# Extrae features de imagenes y busca productos similares
# ============================================================

import numpy as np
import logging
import struct
import io
import threading
from config.database import Database

logger = logging.getLogger(__name__)

# ==================== FEATURE EXTRACTION ====================

def extract_features(image_bytes):
    """
    Extrae vector de features de una imagen para busqueda visual.
    Usa histograma HSV + LBP textura + histograma de bordes.
    Retorna vector numpy de ~618 dimensiones.
    """
    try:
        import cv2
        from skimage.feature import local_binary_pattern

        # Decodificar imagen
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logger.error(f'cv2.imdecode returned None (input size: {len(image_bytes)} bytes)')
            return None

        # Redimensionar para consistencia
        img = cv2.resize(img, (256, 256))

        # 1. Histograma de color HSV (8x12x3 = 288 bins -> normalizamos a 512)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180]).flatten()
        hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256]).flatten()
        hist_v = cv2.calcHist([hsv], [2], None, [76], [0, 256]).flatten()
        color_hist = np.concatenate([hist_h, hist_s, hist_v])  # 512 dims
        color_hist = color_hist / (color_hist.sum() + 1e-7)

        # 2. Textura LBP (Local Binary Pattern)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lbp = local_binary_pattern(gray, P=8, R=1, method='uniform')
        lbp_hist, _ = np.histogram(lbp.ravel(), bins=26, range=(0, 26))
        lbp_hist = lbp_hist.astype(float) / (lbp_hist.sum() + 1e-7)  # 26 dims

        # 3. Histograma de bordes (orientacion de gradientes simplificado)
        edges_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        edges_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(edges_x ** 2 + edges_y ** 2)
        angle = np.arctan2(edges_y, edges_x) * 180 / np.pi + 180
        edge_hist, _ = np.histogram(angle.ravel(), bins=80, range=(0, 360),
                                     weights=magnitude.ravel())
        edge_hist = edge_hist / (edge_hist.sum() + 1e-7)  # 80 dims

        # Combinar (512 + 26 + 80 = 618 dimensiones)
        feature_vector = np.concatenate([color_hist, lbp_hist, edge_hist])
        return feature_vector.astype(np.float32)

    except Exception as e:
        logger.error(f'Error extracting features: {e}')
        return None


def cosine_similarity(a, b):
    """Similitud coseno entre dos vectores."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def vector_to_bytes(vec):
    """Convertir vector numpy a bytes para almacenar en BD."""
    return vec.tobytes()


def bytes_to_vector(raw):
    """Convertir bytes de BD a vector numpy."""
    return np.frombuffer(raw, dtype=np.float32)


# ==================== MODEL ====================

class ImageSearchModel:

    # Cache en memoria de embeddings {empresa_id: [(codigo, imagen_id, vector), ...]}
    _cache = {}
    _cache_lock = threading.Lock()

    @staticmethod
    def _get_conn(connection_id=None):
        """Obtener conexion BD, con soporte para threads sin contexto Flask."""
        return Database.get_connection(connection_id)

    @staticmethod
    def get_embedding_count(empresa_id=None, connection_id=None):
        """Contar embeddings indexados."""
        try:
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()
            if empresa_id:
                cursor.execute("SELECT COUNT(*) FROM image_embeddings WHERE empresa_id = ?", [empresa_id])
            else:
                cursor.execute("SELECT COUNT(*) FROM image_embeddings")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f'Error counting embeddings: {e}')
            return 0

    @staticmethod
    def get_total_images(empresa_id=None, connection_id=None):
        """Contar total de imagenes en la BD."""
        try:
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM view_articulo_imagen")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f'Error counting images: {e}')
            return 0

    @staticmethod
    def save_embedding(imagen_id, codigo, empresa_id, embedding_vector, connection_id=None):
        """Guardar embedding en BD."""
        try:
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()
            raw = vector_to_bytes(embedding_vector)
            cursor.execute("""
                INSERT INTO image_embeddings (imagen_id, codigo, empresa_id, embedding)
                VALUES (?, ?, ?, ?)
            """, [imagen_id, codigo, empresa_id, raw])
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f'Error saving embedding: {e}')
            return False

    @staticmethod
    def clear_embeddings(empresa_id=None, connection_id=None):
        """Eliminar todos los embeddings (para reindexar)."""
        try:
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()
            if empresa_id:
                cursor.execute("DELETE FROM image_embeddings WHERE empresa_id = ?", [empresa_id])
            else:
                cursor.execute("DELETE FROM image_embeddings")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f'Error clearing embeddings: {e}')
            return False

    @staticmethod
    def load_all_embeddings(empresa_id=None, connection_id=None):
        """Cargar todos los embeddings desde BD a cache en memoria."""
        try:
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()
            if empresa_id:
                cursor.execute("SELECT codigo, imagen_id, embedding FROM image_embeddings WHERE empresa_id = ?", [empresa_id])
            else:
                cursor.execute("SELECT codigo, imagen_id, embedding FROM image_embeddings")

            embeddings = []
            for row in cursor.fetchall():
                vec = bytes_to_vector(row[2])
                embeddings.append((row[0], row[1], vec))
            conn.close()

            cache_key = empresa_id or '_all'
            with ImageSearchModel._cache_lock:
                ImageSearchModel._cache[cache_key] = embeddings

            logger.info(f'Loaded {len(embeddings)} embeddings into cache')
            return embeddings
        except Exception as e:
            logger.error(f'Error loading embeddings: {e}')
            return []

    @staticmethod
    def search(query_vector, empresa_id=None, top_k=20):
        """
        Buscar imagenes similares por vector de features.
        Retorna lista de (codigo, imagen_id, similarity_score).
        """
        cache_key = empresa_id or '_all'

        with ImageSearchModel._cache_lock:
            embeddings = ImageSearchModel._cache.get(cache_key)

        if embeddings is None:
            embeddings = ImageSearchModel.load_all_embeddings(empresa_id)

        if not embeddings:
            return []

        # Calcular similitud con todos los embeddings
        scores = []
        for codigo, imagen_id, vec in embeddings:
            sim = cosine_similarity(query_vector, vec)
            scores.append((codigo, imagen_id, sim))

        # Ordenar por similitud descendente
        scores.sort(key=lambda x: x[2], reverse=True)

        # Deduplicar por codigo (mantener mejor score)
        seen = set()
        results = []
        for codigo, imagen_id, sim in scores:
            if codigo not in seen:
                seen.add(codigo)
                results.append({
                    'codigo': codigo,
                    'imagen_id': imagen_id,
                    'similarity': round(sim * 100, 1)
                })
            if len(results) >= top_k:
                break

        return results

    @staticmethod
    def reindex(empresa_id=None, connection_id=None):
        """
        Reindexar todas las imagenes. Se ejecuta en background.
        connection_id es necesario porque el thread no tiene contexto Flask.
        """
        try:
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()

            # Obtener todas las imagenes
            cursor.execute("SELECT id, codigo, imagen FROM view_articulo_imagen")
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                logger.info('No images to index')
                return 0

            logger.info(f'Starting reindex of {len(rows)} images')

            # Limpiar embeddings existentes
            ImageSearchModel.clear_embeddings(empresa_id, connection_id=connection_id)

            count = 0
            errors = 0
            for row in rows:
                imagen_id = row[0]
                codigo = row[1]
                image_data = row[2]

                if not image_data:
                    continue

                # Extraer features
                vec = extract_features(bytes(image_data))
                if vec is not None:
                    emp = empresa_id or '1'
                    ImageSearchModel.save_embedding(imagen_id, codigo, emp, vec, connection_id=connection_id)
                    count += 1
                else:
                    errors += 1

                if (count + errors) % 100 == 0:
                    logger.info(f'Indexed {count}/{len(rows)} images ({errors} errors)')

            logger.info(f'Reindex complete: {count} images indexed, {errors} errors')

            # Recargar cache
            ImageSearchModel.load_all_embeddings(empresa_id, connection_id=connection_id)

            return count
        except Exception as e:
            logger.error(f'Error reindexing: {e}', exc_info=True)
            return 0
