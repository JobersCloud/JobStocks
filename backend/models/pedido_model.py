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
from config.database import Database


class PedidoModel:
    @staticmethod
    def get_by_user(cliente_id, empresa_id=None, anyo=None, fecha_desde=None, fecha_hasta=None):
        """
        Obtiene todos los pedidos de un cliente.

        Args:
            cliente_id: Codigo del cliente en el ERP
            empresa_id: Filtrar por empresa (opcional)
            anyo: Filtrar por año (opcional)
            fecha_desde: Filtrar desde fecha (opcional)
            fecha_hasta: Filtrar hasta fecha (opcional)

        Returns:
            list: Lista de pedidos (solo cabecera)
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT empresa, anyo, pedido, fecha, fecha_entrega, cliente,
                   cliente_nombre, pedido_cliente, serie, bruto, importe_dto,
                   total, peso, divisa, usuario, fecha_alta
            FROM view_externos_venped
            WHERE cliente = ?
        """
        params = [cliente_id]

        if empresa_id:
            query += " AND empresa = ?"
            params.append(empresa_id)

        if anyo:
            query += " AND anyo = ?"
            params.append(anyo)

        if fecha_desde:
            query += " AND fecha >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND fecha <= ?"
            params.append(fecha_hasta)

        query += " ORDER BY fecha DESC, pedido DESC"

        cursor.execute(query, params)

        pedidos = []
        for row in cursor.fetchall():
            pedidos.append({
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
                'fecha_alta': row[15].isoformat() if row[15] else None
            })

        conn.close()
        return pedidos

    @staticmethod
    def get_by_id(empresa, anyo, pedido):
        """
        Obtiene un pedido por su clave primaria compuesta con sus lineas.

        Args:
            empresa: Codigo de empresa
            anyo: Año del pedido
            pedido: Numero de pedido

        Returns:
            dict: Pedido con sus lineas o None si no existe
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        # Obtener cabecera
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

        # Obtener lineas
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
    def get_all(empresa_id=None, anyo=None, fecha_desde=None, fecha_hasta=None, cliente=None):
        """
        Obtiene todos los pedidos (para administradores).

        Args:
            empresa_id: Filtrar por empresa (opcional)
            anyo: Filtrar por año (opcional)
            fecha_desde: Filtrar desde fecha (opcional)
            fecha_hasta: Filtrar hasta fecha (opcional)
            cliente: Filtrar por codigo de cliente (opcional)

        Returns:
            list: Lista de pedidos con info del cliente
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT empresa, anyo, pedido, fecha, fecha_entrega, cliente,
                   cliente_nombre, pedido_cliente, serie, bruto, importe_dto,
                   total, peso, divisa, usuario, fecha_alta
            FROM view_externos_venped
            WHERE 1=1
        """
        params = []

        if empresa_id:
            query += " AND empresa = ?"
            params.append(empresa_id)

        if anyo:
            query += " AND anyo = ?"
            params.append(anyo)

        if fecha_desde:
            query += " AND fecha >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND fecha <= ?"
            params.append(fecha_hasta)

        if cliente:
            query += " AND cliente = ?"
            params.append(cliente)

        query += " ORDER BY fecha DESC, pedido DESC"

        cursor.execute(query, params)

        pedidos = []
        for row in cursor.fetchall():
            pedidos.append({
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
                'fecha_alta': row[15].isoformat() if row[15] else None
            })

        conn.close()
        return pedidos

    @staticmethod
    def get_lineas(empresa, anyo, pedido):
        """
        Obtiene las lineas de un pedido.

        Args:
            empresa: Codigo de empresa
            anyo: Año del pedido
            pedido: Numero de pedido

        Returns:
            list: Lista de lineas del pedido
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
