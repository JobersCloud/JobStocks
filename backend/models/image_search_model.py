# ============================================================
# image_search_model.py - Modelo para busqueda visual CBIR
# Extrae features de imagenes y busca productos similares
# v3: Descriptores espaciales (spatial color layout + structural thumbnail)
# ============================================================

import numpy as np
import logging
import threading
from config.database import Database
from scipy.stats import skew as scipy_skew

logger = logging.getLogger(__name__)

# Version de embeddings - cambiar al modificar extract_features()
EMBEDDING_VERSION = 3

# Pesos por grupo de features (suman 1.0)
# Priorizamos descriptores ESPACIALES (donde estan los colores/patrones)
# sobre descriptores estadisticos (histogramas globales)
FEATURE_WEIGHTS = {
    'spatial_color': 0.25,   # Layout espacial de color (pieza entera)
    'structural': 0.25,      # Miniatura estructural (apariencia global)
    'color_hist': 0.10,      # Histograma color global
    'color_moments': 0.05,   # Momentos de color
    'hog': 0.15,             # Orientacion de bordes espacial
    'lbp': 0.10,             # Textura multi-escala
    'glcm': 0.05,            # Textura GLCM
    'edge': 0.05,            # Bordes global
}

# Umbrales de similitud
MIN_SIMILARITY = 35.0        # Umbral absoluto: minimo 35%
RELATIVE_THRESHOLD = 0.50    # Umbral relativo: >= 50% del mejor score

# ==================== FEATURE EXTRACTION ====================

def _normalize_group(vec):
    """Normalizar un grupo de features a norma unitaria."""
    # Reemplazar NaN/Inf por 0 antes de normalizar
    vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
    norm = np.linalg.norm(vec)
    if norm < 1e-7:
        return vec
    return vec / norm


def extract_features(image_bytes):
    """
    Extrae vector de features de una imagen para busqueda visual.
    Usa 8 grupos de descriptores priorizando apariencia espacial.
    Retorna vector numpy normalizado.
    """
    try:
        import cv2
        from skimage.feature import local_binary_pattern, graycomatrix, graycoprops

        # Decodificar imagen
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logger.error(f'cv2.imdecode returned None (input size: {len(image_bytes)} bytes)')
            return None

        # Redimensionar para consistencia
        img = cv2.resize(img, (256, 256))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # ---- 1. SPATIAL COLOR LAYOUT (48 dims) ----
        # Divide el azulejo en cuadricula 4x4, captura color medio por zona
        # Esto detecta DONDE estan los colores (vetas, dibujos, bordes)
        spatial_colors = []
        cell = 64  # 256/4
        for cy in range(4):
            for cx in range(4):
                region = hsv[cy*cell:(cy+1)*cell, cx*cell:(cx+1)*cell]
                spatial_colors.append(np.mean(region[:, :, 0]) / 180.0)  # H normalizado
                spatial_colors.append(np.mean(region[:, :, 1]) / 255.0)  # S normalizado
                spatial_colors.append(np.mean(region[:, :, 2]) / 255.0)  # V normalizado
        spatial_color = np.array(spatial_colors)  # 4*4*3 = 48 dims
        spatial_color = _normalize_group(spatial_color) * FEATURE_WEIGHTS['spatial_color']

        # ---- 2. STRUCTURAL THUMBNAIL (256 dims) ----
        # Miniatura 16x16 en escala de grises = "como se ve de lejos"
        # Captura la apariencia GLOBAL del azulejo
        thumb = cv2.resize(gray, (16, 16), interpolation=cv2.INTER_AREA)
        structural = thumb.astype(np.float64).ravel() / 255.0  # 256 dims
        structural = _normalize_group(structural) * FEATURE_WEIGHTS['structural']

        # ---- 3. Histograma de color HSV reducido (128 bins) ----
        hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180]).flatten()
        hist_s = cv2.calcHist([hsv], [1], None, [48], [0, 256]).flatten()
        hist_v = cv2.calcHist([hsv], [2], None, [48], [0, 256]).flatten()
        color_hist = np.concatenate([hist_h, hist_s, hist_v])  # 128 dims
        color_hist = color_hist / (color_hist.sum() + 1e-7)
        color_hist = _normalize_group(color_hist) * FEATURE_WEIGHTS['color_hist']

        # ---- 4. Color Moments (9 dims) ----
        color_moments = []
        for ch in range(3):
            channel = hsv[:, :, ch].astype(np.float64).ravel()
            color_moments.append(np.mean(channel) / 255.0)
            color_moments.append(np.var(channel) / (255.0 ** 2))
            color_moments.append(scipy_skew(channel) / 10.0)
        color_moments = np.array(color_moments, dtype=np.float64)  # 9 dims
        color_moments = _normalize_group(color_moments) * FEATURE_WEIGHTS['color_moments']

        # ---- 5. HOG espacial (144 dims) ----
        edges_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        edges_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(edges_x ** 2 + edges_y ** 2)
        angle = np.arctan2(edges_y, edges_x) * 180 / np.pi + 180

        n_bins_hog = 9
        cell_size_hog = 64
        n_cells_hog = 4
        hog_features = []
        for cy in range(n_cells_hog):
            for cx in range(n_cells_hog):
                y0, y1 = cy * cell_size_hog, (cy + 1) * cell_size_hog
                x0, x1 = cx * cell_size_hog, (cx + 1) * cell_size_hog
                cell_mag = magnitude[y0:y1, x0:x1].ravel()
                cell_ang = angle[y0:y1, x0:x1].ravel()
                cell_hist, _ = np.histogram(cell_ang, bins=n_bins_hog,
                                            range=(0, 360), weights=cell_mag)
                cell_hist = cell_hist / (cell_hist.sum() + 1e-7)
                hog_features.extend(cell_hist)
        hog_features = np.array(hog_features)  # 144 dims
        hog_features = _normalize_group(hog_features) * FEATURE_WEIGHTS['hog']

        # ---- 6. Multi-scale LBP (54 dims) ----
        lbp_all = []
        for radius in [1, 2, 3]:
            n_points = 8 * radius
            lbp = local_binary_pattern(gray, P=n_points, R=radius, method='uniform')
            n_bins = n_points + 2
            lbp_hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins))
            lbp_hist = lbp_hist.astype(np.float64) / (lbp_hist.sum() + 1e-7)
            lbp_all.append(lbp_hist)
        lbp_features = np.concatenate(lbp_all)  # 54 dims
        lbp_features = _normalize_group(lbp_features) * FEATURE_WEIGHTS['lbp']

        # ---- 7. GLCM Texture (4 dims) ----
        gray_q = (gray // 4).astype(np.uint8)
        glcm = graycomatrix(gray_q, distances=[1], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4],
                            levels=64, symmetric=True, normed=True)
        glcm_features = np.array([
            graycoprops(glcm, 'contrast').mean(),
            graycoprops(glcm, 'homogeneity').mean(),
            graycoprops(glcm, 'correlation').mean(),
            graycoprops(glcm, 'dissimilarity').mean()
        ])  # 4 dims
        glcm_features = _normalize_group(glcm_features) * FEATURE_WEIGHTS['glcm']

        # ---- 8. Histograma de bordes global (80 dims) ----
        edge_hist, _ = np.histogram(angle.ravel(), bins=80, range=(0, 360),
                                     weights=magnitude.ravel())
        edge_hist = edge_hist / (edge_hist.sum() + 1e-7)
        edge_hist = _normalize_group(edge_hist) * FEATURE_WEIGHTS['edge']

        # Combinar (48+256+128+9+144+54+4+80 = 723 dims)
        feature_vector = np.concatenate([
            spatial_color, structural, color_hist, color_moments,
            hog_features, lbp_features, glcm_features, edge_hist
        ])
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
    result = float(dot / (norm_a * norm_b))
    if np.isnan(result) or np.isinf(result):
        return 0.0
    return result


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
    def check_version_mismatch(empresa_id=None, connection_id=None):
        """Verificar si los embeddings en BD son de una version anterior."""
        try:
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()
            if empresa_id:
                cursor.execute("SELECT TOP 1 embedding FROM image_embeddings WHERE empresa_id = ?", [empresa_id])
            else:
                cursor.execute("SELECT TOP 1 embedding FROM image_embeddings")
            row = cursor.fetchone()
            conn.close()
            if row is None:
                return False  # No hay embeddings, no hay mismatch
            vec = bytes_to_vector(row[0])
            # Generar un vector de prueba para comparar dimensiones
            expected_dims = None
            try:
                # Crear imagen dummy 1x1 para saber dims esperadas
                import cv2
                dummy = np.zeros((10, 10, 3), dtype=np.uint8)
                _, buf = cv2.imencode('.png', dummy)
                test_vec = extract_features(buf.tobytes())
                if test_vec is not None:
                    expected_dims = len(test_vec)
            except Exception:
                pass
            if expected_dims and len(vec) != expected_dims:
                logger.warning(f'Embedding version mismatch: stored={len(vec)} dims, expected={expected_dims} dims. Reindex needed.')
                return True
            return False
        except Exception as e:
            logger.error(f'Error checking version: {e}')
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
            expected_dims = None
            skipped = 0
            for row in cursor.fetchall():
                vec = bytes_to_vector(row[2])
                # Verificar dimension compatible (primera vez se establece referencia)
                if expected_dims is None:
                    expected_dims = len(vec)
                if len(vec) != expected_dims:
                    skipped += 1
                    continue
                embeddings.append((row[0], row[1], vec))
            conn.close()

            if skipped > 0:
                logger.warning(f'Skipped {skipped} embeddings with mismatched dimensions')

            cache_key = empresa_id or '_all'
            with ImageSearchModel._cache_lock:
                ImageSearchModel._cache[cache_key] = embeddings

            logger.info(f'Loaded {len(embeddings)} embeddings into cache')
            return embeddings
        except Exception as e:
            logger.error(f'Error loading embeddings: {e}')
            return []

    @staticmethod
    def search(query_vector, empresa_id=None, top_k=20,
               min_similarity=MIN_SIMILARITY, relative_threshold=RELATIVE_THRESHOLD):
        """
        Buscar imagenes similares por vector de features.
        Aplica umbral absoluto y relativo para filtrar resultados debiles.
        Retorna lista de (codigo, imagen_id, similarity_score).
        """
        cache_key = empresa_id or '_all'

        with ImageSearchModel._cache_lock:
            embeddings = ImageSearchModel._cache.get(cache_key)

        if embeddings is None:
            embeddings = ImageSearchModel.load_all_embeddings(empresa_id)

        if not embeddings:
            return []

        # Verificar compatibilidad de dimensiones
        stored_dims = len(embeddings[0][2])
        query_dims = len(query_vector)
        if stored_dims != query_dims:
            # Cache obsoleta - forzar recarga desde BD por si ya se reindexo
            logger.warning(f'Dimension mismatch (cache={stored_dims}, query={query_dims}), reloading from DB...')
            with ImageSearchModel._cache_lock:
                ImageSearchModel._cache.pop(cache_key, None)
            embeddings = ImageSearchModel.load_all_embeddings(empresa_id)

            if not embeddings:
                return []

            # Comprobar de nuevo tras recarga
            stored_dims = len(embeddings[0][2])
            if stored_dims != query_dims:
                raise ValueError(
                    f'REINDEX_NEEDED: Los embeddings almacenados ({stored_dims} dims) '
                    f'son incompatibles con la version actual ({query_dims} dims). '
                    f'Es necesario reindexar las imagenes desde Control BD.'
                )

        # Calcular similitud con todos los embeddings
        scores = []
        for codigo, imagen_id, vec in embeddings:
            sim = cosine_similarity(query_vector, vec)
            scores.append((codigo, imagen_id, sim))

        # Ordenar por similitud descendente
        scores.sort(key=lambda x: x[2], reverse=True)

        # Deduplicar por codigo (mantener mejor score)
        seen = set()
        deduped = []
        for codigo, imagen_id, sim in scores:
            if codigo not in seen:
                seen.add(codigo)
                deduped.append((codigo, imagen_id, sim))

        if not deduped:
            return []

        # Determinar umbral relativo basado en el mejor score
        best_score = deduped[0][2] * 100  # Convertir a porcentaje
        relative_min = best_score * relative_threshold

        results = []
        for codigo, imagen_id, sim in deduped:
            sim_pct = round(sim * 100, 1)

            # Filtro absoluto: descartar si < min_similarity%
            if sim_pct < min_similarity:
                break  # Ya estan ordenados, no habra mejores

            # Filtro relativo: descartar si < 50% del mejor score
            if sim_pct < relative_min:
                continue

            results.append({
                'codigo': codigo,
                'imagen_id': imagen_id,
                'similarity': sim_pct
            })
            if len(results) >= top_k:
                break

        return results

    @staticmethod
    def reindex(empresa_id=None, connection_id=None, progress_callback=None):
        """
        Reindexar todas las imagenes. Se ejecuta en background.
        connection_id es necesario porque el thread no tiene contexto Flask.
        progress_callback(indexed, total, errors) se llama periodicamente.
        Retorna tupla (count, errors).
        """
        try:
            # 1. Limpiar embeddings PRIMERO (antes de cargar imagenes)
            logger.info(f'Reindex: clearing old embeddings (empresa={empresa_id})')
            ImageSearchModel.clear_embeddings(empresa_id, connection_id=connection_id)
            logger.info('Old embeddings cleared from DB')

            # Limpiar cache inmediatamente
            cache_key = empresa_id or '_all'
            with ImageSearchModel._cache_lock:
                ImageSearchModel._cache.pop(cache_key, None)
            logger.info('Cache invalidated')

            # 2. Contar total de imagenes primero (query ligera)
            logger.info('Counting images...')
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM view_articulo_imagen")
            total_images = cursor.fetchone()[0]
            conn.close()

            if total_images == 0:
                logger.info('No images to index')
                return (0, 0)

            logger.info(f'Total images: {total_images}, starting feature extraction one by one')

            if progress_callback:
                progress_callback(0, total_images, 0)

            # 3. Procesar imagen por imagen (no fetchall con 150MB)
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()
            cursor.execute("SELECT id, codigo, imagen FROM view_articulo_imagen")

            count = 0
            errors = 0
            first_error_logged = False
            row = cursor.fetchone()
            while row is not None:
                imagen_id = row[0]
                codigo = row[1]
                image_data = row[2]

                if image_data:
                    # Extraer features
                    try:
                        vec = extract_features(bytes(image_data))
                    except Exception as ex:
                        if not first_error_logged:
                            logger.error(f'extract_features exception on imagen_id={imagen_id}, codigo={codigo}: {ex}', exc_info=True)
                            first_error_logged = True
                        vec = None

                    if vec is not None:
                        emp = empresa_id or '1'
                        ImageSearchModel.save_embedding(imagen_id, codigo, emp, vec, connection_id=connection_id)
                        count += 1
                    else:
                        errors += 1
                        if not first_error_logged:
                            logger.warning(f'extract_features returned None for imagen_id={imagen_id}, codigo={codigo}')
                            first_error_logged = True

                # Siguiente fila
                row = cursor.fetchone()

                # Actualizar progreso cada 10 imagenes
                if progress_callback and (count + errors) % 10 == 0:
                    progress_callback(count, total_images, errors)

                if (count + errors) % 100 == 0:
                    logger.info(f'Indexed {count}/{total_images} images ({errors} errors)')

            conn.close()

            logger.info(f'Reindex complete: {count} images indexed, {errors} errors')

            # Recargar cache
            ImageSearchModel.load_all_embeddings(empresa_id, connection_id=connection_id)

            return (count, errors)
        except Exception as e:
            logger.error(f'Error reindexing: {e}', exc_info=True)
            raise  # Propagar al thread para que se guarde en _reindex_status

    @staticmethod
    def index_new_images(empresa_id=None, connection_id=None, progress_callback=None):
        """
        Indexar solo imagenes nuevas (que no tienen embedding).
        Retorna tupla (count, errors).
        """
        try:
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()

            # Contar imagenes sin embedding
            cursor.execute("""
                SELECT COUNT(*) FROM view_articulo_imagen v
                WHERE NOT EXISTS (
                    SELECT 1 FROM image_embeddings e
                    WHERE e.imagen_id = v.id AND e.empresa_id = ?
                )
            """, [empresa_id or '1'])
            total_new = cursor.fetchone()[0]
            conn.close()

            if total_new == 0:
                logger.info('No new images to index')
                return (0, 0)

            logger.info(f'{total_new} new images to index')

            if progress_callback:
                progress_callback(0, total_new, 0)

            # Procesar una por una
            conn = ImageSearchModel._get_conn(connection_id)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.id, v.codigo, v.imagen FROM view_articulo_imagen v
                WHERE NOT EXISTS (
                    SELECT 1 FROM image_embeddings e
                    WHERE e.imagen_id = v.id AND e.empresa_id = ?
                )
            """, [empresa_id or '1'])

            count = 0
            errors = 0
            row = cursor.fetchone()
            while row is not None:
                imagen_id = row[0]
                codigo = row[1]
                image_data = row[2]

                if image_data:
                    try:
                        vec = extract_features(bytes(image_data))
                    except Exception:
                        vec = None

                    if vec is not None:
                        emp = empresa_id or '1'
                        ImageSearchModel.save_embedding(imagen_id, codigo, emp, vec, connection_id=connection_id)
                        count += 1
                    else:
                        errors += 1

                row = cursor.fetchone()

                if progress_callback and (count + errors) % 10 == 0:
                    progress_callback(count, total_new, errors)

            conn.close()
            logger.info(f'Incremental index: {count} new images indexed, {errors} errors')

            # Recargar cache
            ImageSearchModel.load_all_embeddings(empresa_id, connection_id=connection_id)

            return (count, errors)
        except Exception as e:
            logger.error(f'Error indexing new images: {e}', exc_info=True)
            raise
