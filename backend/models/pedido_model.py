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
# Fecha : 2026-02-03
# ============================================================

# ============================================
# ARCHIVO: models/pedido_model.py
# Descripcion: Modelo para consultar pedidos de venta del ERP
# Vistas: view_externos_venped, view_externos_venliped
# ============================================
import math
import time
import logging
from config.database import Database

logger = logging.getLogger(__name__)


class PedidoModel:
    @staticmethod
    def get_by_user(cliente_id, empresa_id=None, anyo=None, fecha_desde=None, fecha_hasta=None, page=1, page_size=50):
        """
        Obtiene pedidos de un cliente con paginacion servidor.

        Returns:
            dict: { pedidos, total, page, page_size, total_pages }
        """
        t0 = time.time()
        conn = Database.get_connection()
        t1 = time.time()
        logger.warning(f'[PERF-MODEL] get_connection: {t1-t0:.3f}s')

        cursor = conn.cursor()

        # Build WHERE
        where_parts = ["cliente = ?"]
        params = [cliente_id]

        if empresa_id:
            where_parts.append("empresa = ?")
            params.append(empresa_id)
        if anyo:
            where_parts.append("anyo = ?")
            params.append(anyo)
        if fecha_desde:
            where_parts.append("fecha >= ?")
            params.append(fecha_desde)
        if fecha_hasta:
            where_parts.append("fecha <= ?")
            params.append(fecha_hasta)

        where = " AND ".join(where_parts)

        # 1. Count total
        cursor.execute(f"SELECT COUNT(*) FROM view_externos_venped WHERE {where}", params)
        total = cursor.fetchone()[0]
        t2 = time.time()
        logger.warning(f'[PERF-MODEL] COUNT: {t2-t1:.3f}s | total={total}')

        # 2. Paginated data with ROW_NUMBER (SQL Server 2008 compatible)
        offset_start = (page - 1) * page_size + 1
        offset_end = page * page_size

        data_query = f"""
            SELECT * FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY fecha DESC, pedido DESC) AS rn,
                       empresa, anyo, pedido, fecha, fecha_entrega, cliente,
                       cliente_nombre, pedido_cliente, serie, bruto, importe_dto,
                       total, peso, divisa, usuario, fecha_alta
                FROM view_externos_venped
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

        pedidos = []
        for row in rows:
            pedidos.append({
                'empresa': row[1],
                'anyo': row[2],
                'pedido': row[3],
                'fecha': row[4].isoformat() if row[4] else None,
                'fecha_entrega': row[5].isoformat() if row[5] else None,
                'cliente': row[6],
                'cliente_nombre': row[7],
                'pedido_cliente': row[8],
                'serie': row[9],
                'bruto': float(row[10]) if row[10] else 0,
                'importe_dto': float(row[11]) if row[11] else 0,
                'total': float(row[12]) if row[12] else 0,
                'peso': float(row[13]) if row[13] else 0,
                'divisa': row[14],
                'usuario': row[15],
                'fecha_alta': row[16].isoformat() if row[16] else None
            })

        t6 = time.time()
        logger.warning(f'[PERF-MODEL] Python mapping: {t6-t5:.3f}s | TOTAL model: {t6-t0:.3f}s')

        conn.close()

        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return {
            'pedidos': pedidos,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }

    @staticmethod
    def get_by_id(empresa, anyo, pedido):
        """
        Obtiene un pedido por su clave primaria compuesta con sus lineas.
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT empresa, anyo, pedido, fecha, fecha_entrega, cliente,
                   cliente_nombre, pedido_cliente, serie, bruto, importe_dto,
                   total, peso, divisa, usuario, fecha_alta
            FROM view_externos_venped
            WHERE empresa = ? AND anyo = ? AND pedido = ?
        """, (empresa, anyo, pedido))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        pedido_data = {
            'empresa': row[0],
            'anyo': row[1],
            'pedido': row[2],
            'fecha': row[3].isoformat() if row[3] else None,
            'fecha_entrega': row[4].isoformat() if row[4] else None,
            'cliente': row[5],
            'cliente_nombre': row[6],
            'pedido_cliente': row[7],
            'serie': row[8],
            'bruto': float(row[9]) if row[9] else 0,
            'importe_dto': float(row[10]) if row[10] else 0,
            'total': float(row[11]) if row[11] else 0,
            'peso': float(row[12]) if row[12] else 0,
            'divisa': row[13],
            'usuario': row[14],
            'fecha_alta': row[15].isoformat() if row[15] else None,
            'lineas': []
        }

        cursor.execute("""
            SELECT linea, articulo, descripcion, formato, calidad, tono,
                   calibre, cantidad, precio, importe, pallets, cajas,
                   fecha_pedido, fecha_entrega, situacion
            FROM view_externos_venliped
            WHERE empresa = ? AND anyo = ? AND pedido = ?
            ORDER BY linea
        """, (empresa, anyo, pedido))

        for row in cursor.fetchall():
            pedido_data['lineas'].append({
                'linea': row[0],
                'articulo': row[1],
                'descripcion': row[2],
                'formato': row[3],
                'calidad': row[4],
                'tono': row[5],
                'calibre': row[6],
                'cantidad': float(row[7]) if row[7] else 0,
                'precio': float(row[8]) if row[8] else 0,
                'importe': float(row[9]) if row[9] else 0,
                'pallets': float(row[10]) if row[10] else 0,
                'cajas': float(row[11]) if row[11] else 0,
                'fecha_pedido': row[12].isoformat() if row[12] else None,
                'fecha_entrega': row[13].isoformat() if row[13] else None,
                'situacion': row[14]
            })

        conn.close()
        return pedido_data

    @staticmethod
    def get_all(empresa_id=None, anyo=None, fecha_desde=None, fecha_hasta=None, cliente=None, page=1, page_size=50):
        """
        Obtiene todos los pedidos con paginacion servidor (para administradores).

        Returns:
            dict: { pedidos, total, page, page_size, total_pages }
        """
        t0 = time.time()
        conn = Database.get_connection()
        t1 = time.time()
        logger.warning(f'[PERF-MODEL] get_connection: {t1-t0:.3f}s')

        cursor = conn.cursor()

        # Build WHERE
        where_parts = ["1=1"]
        params = []

        if empresa_id:
            where_parts.append("empresa = ?")
            params.append(empresa_id)
        if anyo:
            where_parts.append("anyo = ?")
            params.append(anyo)
        if fecha_desde:
            where_parts.append("fecha >= ?")
            params.append(fecha_desde)
        if fecha_hasta:
            where_parts.append("fecha <= ?")
            params.append(fecha_hasta)
        if cliente:
            where_parts.append("(cliente_nombre LIKE ? OR cliente LIKE ?)")
            params.append(f'%{cliente}%')
            params.append(f'%{cliente}%')

        where = " AND ".join(where_parts)

        # 1. Count total
        cursor.execute(f"SELECT COUNT(*) FROM view_externos_venped WHERE {where}", params)
        total = cursor.fetchone()[0]
        t2 = time.time()
        logger.warning(f'[PERF-MODEL] COUNT: {t2-t1:.3f}s | total={total}')

        # 2. Paginated data with ROW_NUMBER (SQL Server 2008 compatible)
        offset_start = (page - 1) * page_size + 1
        offset_end = page * page_size

        data_query = f"""
            SELECT * FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY fecha DESC, pedido DESC) AS rn,
                       empresa, anyo, pedido, fecha, fecha_entrega, cliente,
                       cliente_nombre, pedido_cliente, serie, bruto, importe_dto,
                       total, peso, divisa, usuario, fecha_alta
                FROM view_externos_venped
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

        pedidos = []
        for row in rows:
            pedidos.append({
                'empresa': row[1],
                'anyo': row[2],
                'pedido': row[3],
                'fecha': row[4].isoformat() if row[4] else None,
                'fecha_entrega': row[5].isoformat() if row[5] else None,
                'cliente': row[6],
                'cliente_nombre': row[7],
                'pedido_cliente': row[8],
                'serie': row[9],
                'bruto': float(row[10]) if row[10] else 0,
                'importe_dto': float(row[11]) if row[11] else 0,
                'total': float(row[12]) if row[12] else 0,
                'peso': float(row[13]) if row[13] else 0,
                'divisa': row[14],
                'usuario': row[15],
                'fecha_alta': row[16].isoformat() if row[16] else None
            })

        t6 = time.time()
        logger.warning(f'[PERF-MODEL] Python mapping: {t6-t5:.3f}s | TOTAL model: {t6-t0:.3f}s')

        conn.close()

        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return {
            'pedidos': pedidos,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }

    @staticmethod
    def get_lineas(empresa, anyo, pedido):
        """
        Obtiene las lineas de un pedido.
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT linea, articulo, descripcion, formato, calidad, tono,
                   calibre, cantidad, precio, importe, pallets, cajas,
                   fecha_pedido, fecha_entrega, situacion
            FROM view_externos_venliped
            WHERE empresa = ? AND anyo = ? AND pedido = ?
            ORDER BY linea
        """, (empresa, anyo, pedido))

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
                'cantidad': float(row[7]) if row[7] else 0,
                'precio': float(row[8]) if row[8] else 0,
                'importe': float(row[9]) if row[9] else 0,
                'pallets': float(row[10]) if row[10] else 0,
                'cajas': float(row[11]) if row[11] else 0,
                'fecha_pedido': row[12].isoformat() if row[12] else None,
                'fecha_entrega': row[13].isoformat() if row[13] else None,
                'situacion': row[14]
            })

        conn.close()
        return lineas
