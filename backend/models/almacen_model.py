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
# Fecha : 2026-02-12
# ============================================================

# ============================================
# ARCHIVO: models/almacen_model.py
# Descripcion: Modelo para vista almacen (ubicaciones 3D)
# ============================================
from config.database import Database


class AlmacenModel:
    @staticmethod
    def get_almacenes(empresa_id='1'):
        """
        Obtiene la lista de almacenes con codigo y descripcion.
        Fuente: view_externos_almalmacen (cristal.dbo.almalmacen)

        Returns:
            list: Lista de dicts {codigo, descripcion}
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT codigo, descripcion
            FROM view_externos_almalmacen
            WHERE empresa = ?
            ORDER BY codigo
        """, (empresa_id,))

        almacenes = []
        for row in cursor.fetchall():
            almacenes.append({
                'codigo': row[0].strip() if row[0] else '',
                'descripcion': row[1].strip() if row[1] else ''
            })
        conn.close()
        return almacenes

    @staticmethod
    def get_ubicaciones(empresa_id='1', almacen=None):
        """
        Obtiene todas las ubicaciones con sus datos para el 3D.

        Args:
            empresa_id: ID de la empresa
            almacen: Codigo de almacen

        Returns:
            list: Lista de ubicaciones con datos del articulo
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        # Detectar si la vista tiene columna 'unidad' o 'tipo_unidad'
        unidad_col = None
        for col_name in ('unidad', 'tipo_unidad'):
            try:
                cursor.execute(f"""
                    SELECT TOP 1 {col_name} FROM view_externos_almlinubica
                    WHERE empresa = ? AND almacen = ?
                """, (empresa_id, almacen))
                cursor.fetchone()
                unidad_col = col_name
                break
            except Exception:
                pass

        cols = """zona, fila, altura, codigo, descripcion, formato, serie,
                  calidad, tono, tonochar, calibre, existencias, ubicacion,
                  pallet, caja, sector"""
        if unidad_col:
            cols += f", {unidad_col}"

        cursor.execute(f"""
            SELECT {cols}
            FROM view_externos_almlinubica
            WHERE empresa = ? AND almacen = ?
            ORDER BY zona, fila, altura
        """, (empresa_id, almacen))

        ubicaciones = []
        for row in cursor.fetchall():
            item = {
                'zona': row[0].strip() if row[0] else '',
                'fila': row[1] if row[1] is not None else 0,
                'altura': row[2] if row[2] is not None else 0,
                'codigo': row[3].strip() if row[3] else '',
                'descripcion': row[4].strip() if row[4] else '',
                'formato': row[5].strip() if row[5] else '',
                'serie': row[6].strip() if row[6] else '',
                'calidad': row[7].strip() if row[7] else '',
                'tono': row[8].strip() if row[8] else '',
                'tonochar': row[9].strip() if row[9] else '',
                'calibre': row[10].strip() if isinstance(row[10], str) else (row[10] if row[10] is not None else ''),
                'existencias': float(row[11]) if row[11] else 0,
                'ubicacion': row[12].strip() if row[12] else '',
                'pallet': row[13].strip() if row[13] else '',
                'caja': float(row[14]) if row[14] else 0,
                'sector': row[15].strip() if row[15] else ''
            }
            if unidad_col:
                item['unidad'] = int(row[16]) if row[16] is not None else 0
            else:
                item['unidad'] = 0
            ubicaciones.append(item)

        conn.close()
        return ubicaciones

    @staticmethod
    def get_estructura(empresa_id='1', almacen=None):
        """
        Obtiene las dimensiones de cada zona (max fila, max altura).

        Args:
            empresa_id: ID de la empresa
            almacen: Codigo de almacen

        Returns:
            list: Lista de zonas con sus dimensiones
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                zona,
                MAX(fila) as max_fila,
                MAX(altura) as max_altura,
                COUNT(*) as total_celdas
            FROM view_externos_almlinubica
            WHERE empresa = ? AND almacen = ?
            GROUP BY zona
            ORDER BY zona
        """, (empresa_id, almacen))

        estructura = []
        for row in cursor.fetchall():
            estructura.append({
                'zona': row[0].strip() if row[0] else '',
                'max_fila': row[1] if row[1] is not None else 0,
                'max_altura': row[2] if row[2] is not None else 0,
                'total_celdas': row[3]
            })

        conn.close()
        return estructura

    @staticmethod
    def get_resumen(empresa_id='1', almacen=None):
        """
        Obtiene estadisticas resumen del almacen.

        Args:
            empresa_id: ID de la empresa
            almacen: Codigo de almacen

        Returns:
            dict: Resumen con totales
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(DISTINCT zona) as total_zonas,
                COUNT(*) as total_ubicaciones,
                COUNT(DISTINCT codigo) as total_articulos,
                ISNULL(SUM(existencias), 0) as total_existencias
            FROM view_externos_almlinubica
            WHERE empresa = ? AND almacen = ?
        """, (empresa_id, almacen))

        row = cursor.fetchone()

        result = {
            'total_zonas': row[0] if row[0] else 0,
            'total_ubicaciones': row[1] if row[1] else 0,
            'total_articulos': row[2] if row[2] else 0,
            'total_existencias': float(row[3]) if row[3] else 0,
            'total_m2': 0,
            'total_piezas': 0
        }

        # Desglose M2/Piezas (probar columna 'unidad' y fallback a 'tipo_unidad')
        for col_name in ('unidad', 'tipo_unidad'):
            try:
                cursor.execute(f"""
                    SELECT
                        ISNULL(SUM(CASE WHEN {col_name} = 1 THEN existencias ELSE 0 END), 0),
                        ISNULL(SUM(CASE WHEN {col_name} = 0 THEN existencias ELSE 0 END), 0)
                    FROM view_externos_almlinubica
                    WHERE empresa = ? AND almacen = ?
                """, (empresa_id, almacen))
                row2 = cursor.fetchone()
                if row2:
                    result['total_m2'] = float(row2[0]) if row2[0] else 0
                    result['total_piezas'] = float(row2[1]) if row2[1] else 0
                break
            except Exception:
                continue

        conn.close()
        return result

    @staticmethod
    def get_mapa(empresa_id='1', almacen=None):
        """
        Obtiene la definicion del mapa de ubicaciones (todos los huecos).
        Fuente: view_externos_almubimapa (cristal.dbo.almubimapa)

        Args:
            empresa_id: ID de la empresa
            almacen: Codigo de almacen

        Returns:
            list: Lista de zonas con rangos de filas y alturas
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                zona,
                fila_desde,
                fila_hasta,
                altura_desde,
                altura_hasta,
                largo
            FROM view_externos_almubimapa
            WHERE empresa = ? AND almacen = ?
            ORDER BY zona, fila_desde, altura_desde
        """, (empresa_id, almacen))

        mapa = []
        for row in cursor.fetchall():
            mapa.append({
                'zona': row[0].strip() if row[0] else '',
                'fila_desde': row[1] if row[1] is not None else 0,
                'fila_hasta': row[2] if row[2] is not None else 0,
                'altura_desde': row[3] if row[3] is not None else 0,
                'altura_hasta': row[4] if row[4] is not None else 0,
                'largo': float(row[5]) if row[5] is not None else 1.0
            })

        conn.close()
        return mapa
