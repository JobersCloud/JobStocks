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
# Fecha : 2026-03-13
# ============================================================

# ============================================
# ARCHIVO: models/albaran_model.py
# Descripcion: Modelo para consultar albaranes de venta del ERP
# Vistas: view_externos_venalb, view_externos_venlialb
# ============================================
import math
import time
import logging
from config.database import Database

logger = logging.getLogger(__name__)


class AlbaranModel:
    _has_clientes_dir = None  # Cache: view_externos_clientes tiene pais/provincia

    @classmethod
    def _check_clientes_dir(cls, cursor):
        """Comprueba si view_externos_clientes tiene campos pais/provincia."""
        if cls._has_clientes_dir is None:
            try:
                cursor.execute("SELECT COL_LENGTH('view_externos_clientes', 'pais')")
                result = cursor.fetchone()
                cls._has_clientes_dir = result[0] is not None
            except Exception:
                cls._has_clientes_dir = False
            logger.info(f'[ALBARAN] view_externos_clientes.pais exists: {cls._has_clientes_dir}')
        return cls._has_clientes_dir

    @staticmethod
    def _map_albaran_row(row, offset=1):
        """Mapea una fila de la query paginada a dict. offset=1 para ROW_NUMBER, 0 para get_by_id."""
        o = offset
        pais_idx = 15 + o
        prov_idx = 16 + o

        result = {
            'empresa': row[0 + o],
            'anyo': row[1 + o],
            'albaran': row[2 + o],
            'fecha': row[3 + o].isoformat() if row[3 + o] else None,
            'fecha_entrega': row[4 + o].isoformat() if row[4 + o] else None,
            'cliente': row[5 + o],
            'cliente_nombre': row[6 + o],
            'serie': row[7 + o],
            'bruto': round(float(row[8 + o]), 2) if row[8 + o] else 0,
            'importe_dto': round(float(row[9 + o]), 2) if row[9 + o] else 0,
            'total': round(float(row[10 + o]), 2) if row[10 + o] else 0,
            'peso': round(float(row[11 + o]), 2) if row[11 + o] else 0,
            'divisa': row[12 + o],
            'usuario': row[13 + o],
            'fecha_alta': row[14 + o].isoformat() if row[14 + o] else None,
        }

        # pais/provincia only in paginated queries (offset=1)
        if offset == 1:
            result['pais_nombre'] = row[pais_idx] if row[pais_idx] else ''
            result['provincia_nombre'] = row[prov_idx] if row[prov_idx] else ''

        return result

    @staticmethod
    def get_by_user(cliente_id, empresa_id=None, anyo=None, fecha_desde=None, fecha_hasta=None, page=1, page_size=50):
        """
        Obtiene albaranes de un cliente con paginacion servidor.

        Returns:
            dict: { albaranes, total, page, page_size, total_pages }
        """
        t0 = time.time()
        conn = Database.get_connection()
        t1 = time.time()
        logger.warning(f'[PERF-MODEL] get_connection: {t1-t0:.3f}s')

        try:
            cursor = conn.cursor()
            has_clientes_dir = AlbaranModel._check_clientes_dir(cursor)
            if has_clientes_dir:
                location_sql = "RTRIM(ISNULL(g.pais, '')) AS pais_nombre, RTRIM(ISNULL(g.provincia, '')) AS provincia_nombre"
                join_sql = "OUTER APPLY (SELECT TOP 1 c.pais, c.provincia FROM view_externos_clientes c WHERE c.codigo = v.cliente AND c.empresa = v.empresa) g"
            else:
                location_sql = "'' AS pais_nombre, '' AS provincia_nombre"
                join_sql = ""

            # Build WHERE
            where_parts = ["v.cliente = ?"]
            params = [cliente_id]

            if empresa_id:
                where_parts.append("v.empresa = ?")
                params.append(empresa_id)
            if anyo:
                where_parts.append("v.anyo = ?")
                params.append(anyo)
            if fecha_desde:
                where_parts.append("v.fecha >= CONVERT(datetime, ?, 120)")
                params.append(fecha_desde)
            if fecha_hasta:
                where_parts.append("v.fecha <= CONVERT(datetime, ?, 120)")
                params.append(fecha_hasta)

            where = " AND ".join(where_parts)

            # 1. Count total
            cursor.execute(f"SELECT COUNT(*) FROM view_externos_venalb v WHERE {where}", params)
            total = cursor.fetchone()[0]
            t2 = time.time()
            logger.warning(f'[PERF-MODEL] COUNT: {t2-t1:.3f}s | total={total}')

            # 2. Paginated data with ROW_NUMBER (SQL Server 2008 compatible)
            offset_start = (page - 1) * page_size + 1
            offset_end = page * page_size

            data_query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY v.fecha DESC, v.albaran DESC) AS rn,
                           v.empresa, v.anyo, v.albaran, v.fecha, v.fecha_entrega, v.cliente,
                           v.cliente_nombre, v.serie,
                           CAST(v.bruto AS DECIMAL(18,2)) AS bruto, CAST(v.importe_dto AS DECIMAL(18,2)) AS importe_dto,
                           CAST(v.total AS DECIMAL(18,2)) AS total, CAST(v.peso AS DECIMAL(18,2)) AS peso,
                           v.divisa, v.usuario, v.fecha_alta,
                           {location_sql}
                    FROM view_externos_venalb v
                    {join_sql}
                    WHERE {where}
                ) sub
                WHERE rn BETWEEN ? AND ?
            """
            data_params = params + [offset_start, offset_end]

            t3 = time.time()
            cursor.execute(data_query, data_params)
            t4 = time.time()
            logger.warning(f'[PERF-MODEL] SQL execute: {t4-t3:.3f}s')

            rows = cursor.fetchall()
            t5 = time.time()
            logger.warning(f'[PERF-MODEL] fetchall: {t5-t4:.3f}s | rows={len(rows)}')

            albaranes = [AlbaranModel._map_albaran_row(row, offset=1) for row in rows]

            t6 = time.time()
            logger.warning(f'[PERF-MODEL] Python mapping: {t6-t5:.3f}s | TOTAL model: {t6-t0:.3f}s')

            total_pages = math.ceil(total / page_size) if total > 0 else 1
            return {
                'albaranes': albaranes,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            }
        finally:
            conn.close()

    @staticmethod
    def get_by_id(empresa, anyo, albaran):
        """
        Obtiene un albaran por su clave primaria compuesta con sus lineas.
        """
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT empresa, anyo, albaran, fecha, fecha_entrega, cliente,
                       cliente_nombre, serie,
                       CAST(bruto AS DECIMAL(18,2)) AS bruto, CAST(importe_dto AS DECIMAL(18,2)) AS importe_dto,
                       CAST(total AS DECIMAL(18,2)) AS total, CAST(peso AS DECIMAL(18,2)) AS peso,
                       divisa, usuario, fecha_alta,
                       empresa AS _dummy
                FROM view_externos_venalb
                WHERE empresa = ? AND anyo = ? AND albaran = ?
            """, (empresa, anyo, albaran))

            row = cursor.fetchone()
            if not row:
                return None

            albaran_data = AlbaranModel._map_albaran_row(row, offset=0)
            albaran_data['lineas'] = []

            cursor.execute("""
                SELECT l.linea, l.articulo, l.descripcion, l.formato, l.calidad, l.tono,
                       l.calibre, CAST(l.cantidad AS DECIMAL(18,2)) AS cantidad, CAST(l.precio AS DECIMAL(18,2)) AS precio,
                       CAST(l.importe AS DECIMAL(18,2)) AS importe, l.pallets, l.cajas,
                       l.fecha, l.situacion,
                       f.abreviado
                FROM view_externos_venlialb l
                LEFT JOIN view_externos_formatos f ON f.empresa = l.empresa AND f.codigo = l.formato
                WHERE l.empresa = ? AND l.anyo = ? AND l.albaran = ?
                ORDER BY l.linea
            """, (empresa, anyo, albaran))

            for row in cursor.fetchall():
                albaran_data['lineas'].append({
                    'linea': row[0],
                    'articulo': row[1],
                    'descripcion': row[2],
                    'formato': row[3],
                    'calidad': row[4],
                    'tono': row[5],
                    'calibre': row[6],
                    'cantidad': round(float(row[7]), 2) if row[7] else 0,
                    'precio': round(float(row[8]), 2) if row[8] else 0,
                    'importe': round(float(row[9]), 2) if row[9] else 0,
                    'pallets': int(row[10]) if row[10] else 0,
                    'cajas': int(row[11]) if row[11] else 0,
                    'fecha': row[12].isoformat() if row[12] else None,
                    'situacion': row[13],
                    'formato_abreviado': row[14].strip() if row[14] else None
                })

            return albaran_data
        finally:
            conn.close()

    @staticmethod
    def get_all(empresa_id=None, anyo=None, fecha_desde=None, fecha_hasta=None, cliente=None, pais=None, provincia=None, page=1, page_size=50):
        """
        Obtiene todos los albaranes con paginacion servidor (para administradores).

        Returns:
            dict: { albaranes, total, page, page_size, total_pages }
        """
        t0 = time.time()
        conn = Database.get_connection()
        t1 = time.time()
        logger.warning(f'[PERF-MODEL] get_connection: {t1-t0:.3f}s')

        try:
            cursor = conn.cursor()
            has_clientes_dir = AlbaranModel._check_clientes_dir(cursor)
            if has_clientes_dir:
                location_sql = "RTRIM(ISNULL(g.pais, '')) AS pais_nombre, RTRIM(ISNULL(g.provincia, '')) AS provincia_nombre"
                join_sql = "OUTER APPLY (SELECT TOP 1 c.pais, c.provincia FROM view_externos_clientes c WHERE c.codigo = v.cliente AND c.empresa = v.empresa) g"
            else:
                location_sql = "'' AS pais_nombre, '' AS provincia_nombre"
                join_sql = ""

            # Build WHERE
            where_parts = ["1=1"]
            params = []

            if empresa_id:
                where_parts.append("v.empresa = ?")
                params.append(empresa_id)
            if anyo:
                where_parts.append("v.anyo = ?")
                params.append(anyo)
            if fecha_desde:
                where_parts.append("v.fecha >= CONVERT(datetime, ?, 120)")
                params.append(fecha_desde)
            if fecha_hasta:
                where_parts.append("v.fecha <= CONVERT(datetime, ?, 120)")
                params.append(fecha_hasta)
            if cliente:
                where_parts.append("v.cliente = ?")
                params.append(cliente)
            if pais and has_clientes_dir:
                where_parts.append("v.cliente IN (SELECT codigo FROM view_externos_clientes WHERE RTRIM(ISNULL(pais, '')) = ?)")
                params.append(pais)
            if provincia and has_clientes_dir:
                where_parts.append("v.cliente IN (SELECT codigo FROM view_externos_clientes WHERE RTRIM(ISNULL(provincia, '')) = ?)")
                params.append(provincia)

            where = " AND ".join(where_parts)

            # 1. Count total
            cursor.execute(f"SELECT COUNT(*) FROM view_externos_venalb v WHERE {where}", params)
            total = cursor.fetchone()[0]
            t2 = time.time()
            logger.warning(f'[PERF-MODEL] COUNT: {t2-t1:.3f}s | total={total}')

            # 2. Paginated data with ROW_NUMBER (SQL Server 2008 compatible)
            offset_start = (page - 1) * page_size + 1
            offset_end = page * page_size

            data_query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY v.fecha DESC, v.albaran DESC) AS rn,
                           v.empresa, v.anyo, v.albaran, v.fecha, v.fecha_entrega, v.cliente,
                           v.cliente_nombre, v.serie,
                           CAST(v.bruto AS DECIMAL(18,2)) AS bruto, CAST(v.importe_dto AS DECIMAL(18,2)) AS importe_dto,
                           CAST(v.total AS DECIMAL(18,2)) AS total, CAST(v.peso AS DECIMAL(18,2)) AS peso,
                           v.divisa, v.usuario, v.fecha_alta,
                           {location_sql}
                    FROM view_externos_venalb v
                    {join_sql}
                    WHERE {where}
                ) sub
                WHERE rn BETWEEN ? AND ?
            """
            data_params = params + [offset_start, offset_end]

            t3 = time.time()
            cursor.execute(data_query, data_params)
            t4 = time.time()
            logger.warning(f'[PERF-MODEL] SQL execute: {t4-t3:.3f}s')

            rows = cursor.fetchall()
            t5 = time.time()
            logger.warning(f'[PERF-MODEL] fetchall: {t5-t4:.3f}s | rows={len(rows)}')

            albaranes = [AlbaranModel._map_albaran_row(row, offset=1) for row in rows]

            t6 = time.time()
            logger.warning(f'[PERF-MODEL] Python mapping: {t6-t5:.3f}s | TOTAL model: {t6-t0:.3f}s')

            total_pages = math.ceil(total / page_size) if total > 0 else 1
            return {
                'albaranes': albaranes,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            }
        finally:
            conn.close()

    @staticmethod
    def get_lineas(empresa, anyo, albaran):
        """
        Obtiene las lineas de un albaran.
        """
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT l.linea, l.articulo, l.descripcion, l.formato, l.calidad, l.tono,
                       l.calibre, CAST(l.cantidad AS DECIMAL(18,2)) AS cantidad, CAST(l.precio AS DECIMAL(18,2)) AS precio,
                       CAST(l.importe AS DECIMAL(18,2)) AS importe, l.pallets, l.cajas,
                       l.fecha, l.situacion,
                       f.abreviado
                FROM view_externos_venlialb l
                LEFT JOIN view_externos_formatos f ON f.empresa = l.empresa AND f.codigo = l.formato
                WHERE l.empresa = ? AND l.anyo = ? AND l.albaran = ?
                ORDER BY l.linea
            """, (empresa, anyo, albaran))

            lineas = []
            for row in cursor.fetchall():
                lineas.append({
                    'linea': row[0],
                    'articulo': row[1],
                    'descripcion': row[2],
                    'formato': row[3],
                    'calidad': row[4],
                    'tono': row[5],
                    'calibre': row[6],
                    'cantidad': round(float(row[7]), 2) if row[7] else 0,
                    'precio': round(float(row[8]), 2) if row[8] else 0,
                    'importe': round(float(row[9]), 2) if row[9] else 0,
                    'pallets': int(row[10]) if row[10] else 0,
                    'cajas': int(row[11]) if row[11] else 0,
                    'fecha': row[12].isoformat() if row[12] else None,
                    'situacion': row[13],
                    'formato_abreviado': row[14].strip() if row[14] else None
                })

            return lineas
        finally:
            conn.close()
