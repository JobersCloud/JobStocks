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
# Actualizado: 2026-01-16 - Conexión dinámica multi-empresa
# ============================================================

# ============================================
# ARCHIVO: models/stock_model.py
# ============================================
from config.database import Database


def _s(val):
    """Strip de campos CHAR de SQL Server que vienen con espacios"""
    return val.strip() if isinstance(val, str) else val


def _row_to_stock(row):
    """Convierte una fila SQL a dict de stock, con strip de campos CHAR"""
    return {
        'empresa': _s(row[0]),
        'codigo': _s(row[1]),
        'descripcion': _s(row[2]),
        'calidad': _s(row[3]),
        'color': _s(row[4]),
        'tono': _s(row[5]),
        'calibre': _s(row[6]),
        'formato': _s(row[7]),
        'serie': _s(row[8]),
        'unidad': _s(row[9]),
        'pallet': _s(row[10]),
        'caja': _s(row[11]),
        'unidadescaja': float(row[12]) if row[12] else 0,
        'cajaspallet': float(row[13]) if row[13] else 0,
        'existencias': float(row[14]) if row[14] else 0.0,
        'ean13': _s(row[15]),
        'pesocaja': float(row[16]) if row[16] else 0,
        'pesopallet': float(row[17]) if row[17] else 0,
        'tipo_producto': _s(row[18]) if len(row) > 18 and row[18] else '',
        'piezascaja': float(row[19]) if len(row) > 19 and row[19] else 0
    }


class StockModel:
    @staticmethod
    def get_all():
        """Obtiene todos los stocks de la empresa actual (de sesión)"""
        conn = Database.get_connection()  # Obtiene empresa_cli_id de sesión
        empresa_erp = Database.get_empresa_erp()  # Obtiene de sesión
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                       formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet, existencias, ean13, pesocaja, pesopallet, tipo_producto, piezascaja
                FROM view_externos_stock
                WHERE empresa = ?
            """, (empresa_erp,))

            stocks = [_row_to_stock(row) for row in cursor.fetchall()]
            return stocks
        finally:
            conn.close()

    @staticmethod
    def get_by_codigo(codigo):
        """Obtiene un stock por código"""
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                       formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet, existencias, ean13, pesocaja, pesopallet, tipo_producto, piezascaja
                FROM view_externos_stock
                WHERE codigo = ? AND empresa = ?
            """, (codigo, empresa_erp))
            row = cursor.fetchone()

            stock = _row_to_stock(row) if row else None
            return stock
        finally:
            conn.close()

    @staticmethod
    def get_by_codigo_and_empresa(codigo, empresa):
        """Obtiene un stock por código y empresa (compatibilidad)"""
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                       formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet, existencias, ean13, pesocaja, pesopallet, tipo_producto, piezascaja
                FROM view_externos_stock
                WHERE codigo = ? AND empresa LIKE ?
            """, (codigo, f"%{empresa}%"))
            row = cursor.fetchone()

            stock = _row_to_stock(row) if row else None
            return stock
        finally:
            conn.close()

    @staticmethod
    def get_by_codigos(codigos):
        """Obtiene stocks por una lista de códigos. Retorna dict {codigo: stock_dict}"""
        if not codigos:
            return {}
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        try:
            cursor = conn.cursor()

            placeholders = ','.join(['?' for _ in codigos])
            params = list(codigos) + [empresa_erp]
            cursor.execute(f"""
                SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                       formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet, existencias, ean13, pesocaja, pesopallet, tipo_producto, piezascaja
                FROM view_externos_stock
                WHERE codigo IN ({placeholders}) AND empresa = ?
            """, params)

            result = {}
            for row in cursor.fetchall():
                stock = _row_to_stock(row)
                result[stock['codigo']] = stock

            return result
        finally:
            conn.close()

    # Columnas válidas para ordenación (seguridad contra SQL injection)
    VALID_ORDER_COLUMNS = ['codigo', 'descripcion', 'calidad', 'color', 'tono',
                           'calibre', 'formato', 'serie', 'existencias', 'tipo_producto']

    # Columnas válidas para filtros (seguridad contra SQL injection)
    VALID_FILTER_COLUMNS = ['codigo', 'descripcion', 'calidad', 'color', 'tono',
                            'calibre', 'formato', 'serie', 'existencias', 'tipo_producto']

    # Operadores válidos y su traducción SQL
    VALID_OPERATORS = {
        'eq': '=',               # Igual a
        'neq': '<>',             # Diferente de
        'contains': 'LIKE',      # Contiene
        'not_contains': 'NOT LIKE',  # No contiene
        'starts': 'LIKE',        # Empieza por
        'not_starts': 'NOT LIKE',    # No empieza por
        'ends': 'LIKE',          # Termina en
        'not_ends': 'NOT LIKE',      # No termina en
        'gt': '>',               # Mayor que
        'gte': '>=',             # Mayor o igual
        'lt': '<',               # Menor que
        'lte': '<=',             # Menor o igual
        'between': 'BETWEEN',    # Entre (rango)
        'not_between': 'NOT BETWEEN'  # No entre (rango)
    }

    @staticmethod
    def _parse_filter_key(key):
        """
        Parsea una clave de filtro que puede tener formato columna__operador.
        Retorna tupla (columna, operador) o None si no es válido.
        """
        if '__' in key:
            parts = key.split('__', 1)
            if len(parts) == 2:
                columna, operador = parts
                if columna in StockModel.VALID_FILTER_COLUMNS and operador in StockModel.VALID_OPERATORS:
                    return (columna, operador)
        return None

    @staticmethod
    def _build_filter_condition(columna, operador, valor):
        """
        Construye la condición SQL y el parámetro para un filtro.
        Retorna tupla (condición_sql, valor_parametro) o (condición_sql, [param1, param2]) para rangos.
        """
        sql_op = StockModel.VALID_OPERATORS.get(operador, '=')

        # Operadores de texto con LIKE
        if operador == 'contains':
            return (f"{columna} LIKE ?", f"%{valor}%")
        elif operador == 'not_contains':
            return (f"{columna} NOT LIKE ?", f"%{valor}%")
        elif operador == 'starts':
            return (f"{columna} LIKE ?", f"{valor}%")
        elif operador == 'not_starts':
            return (f"{columna} NOT LIKE ?", f"{valor}%")
        elif operador == 'ends':
            return (f"{columna} LIKE ?", f"%{valor}")
        elif operador == 'not_ends':
            return (f"{columna} NOT LIKE ?", f"%{valor}")
        # Operadores de rango (valor viene como "desde,hasta")
        elif operador in ('between', 'not_between'):
            partes = valor.split(',') if ',' in valor else [valor, valor]
            desde = partes[0] if partes[0] else None
            hasta = partes[1] if len(partes) > 1 and partes[1] else None

            if desde and hasta:
                if operador == 'between':
                    return (f"{columna} BETWEEN ? AND ?", [desde, hasta])
                else:
                    return (f"({columna} < ? OR {columna} > ?)", [desde, hasta])
            elif desde:
                op = '>=' if operador == 'between' else '<'
                return (f"{columna} {op} ?", desde)
            elif hasta:
                op = '<=' if operador == 'between' else '>'
                return (f"{columna} {op} ?", hasta)
            else:
                return (None, None)  # Sin valores, no aplicar filtro
        else:
            # Operadores de comparación directa (eq, neq, gt, gte, lt, lte)
            return (f"{columna} {sql_op} ?", valor)

    @staticmethod
    def search(filtros, page=None, limit=None, order_by='codigo', order_dir='ASC'):
        """
        Busca stocks con filtros opcionales, paginación y ordenación.

        Args:
            filtros: dict con filtros de búsqueda
            page: número de página (1-based), None para sin paginación
            limit: registros por página, None para sin paginación
            order_by: columna para ordenar (default: codigo)
            order_dir: dirección de ordenación ASC o DESC (default: ASC)

        Returns:
            Si hay paginación: dict con 'data', 'total', 'page', 'limit', 'pages'
            Si no hay paginación: lista de stocks (comportamiento original)
        """
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        try:
            cursor = conn.cursor()

            # Validar columna de ordenación (prevenir SQL injection)
            if order_by not in StockModel.VALID_ORDER_COLUMNS:
                order_by = 'codigo'

            # Validar dirección de ordenación
            order_dir = 'DESC' if order_dir.upper() == 'DESC' else 'ASC'

            # Construir WHERE clause
            where_conditions = ["empresa = ?"]
            params = [empresa_erp]

            # Procesar filtros - soporta tanto formato simple como con operador
            for key, valor in filtros.items():
                if not valor:  # Ignorar valores vacíos
                    continue

                # Intentar parsear como filtro con operador (columna__operador)
                parsed = StockModel._parse_filter_key(key)
                if parsed:
                    columna, operador = parsed
                    condition, param = StockModel._build_filter_condition(columna, operador, valor)
                    if condition:  # Solo añadir si hay condición válida
                        where_conditions.append(condition)
                        # param puede ser un valor simple o una lista (para BETWEEN)
                        if isinstance(param, list):
                            params.extend(param)
                        else:
                            params.append(param)
                # Compatibilidad con filtros simples (sin operador)
                elif key in StockModel.VALID_FILTER_COLUMNS:
                    # Por defecto usa LIKE %valor% para texto
                    if key == 'existencias':
                        # Para existencias, usar >= si viene como filtro simple
                        where_conditions.append("existencias >= ?")
                        params.append(float(valor))
                    else:
                        where_conditions.append(f"{key} LIKE ?")
                        params.append(f"%{valor}%")
                # Filtro especial existencias_min (compatibilidad)
                elif key == 'existencias_min':
                    where_conditions.append("existencias >= ?")
                    params.append(float(valor))

            where_clause = " AND ".join(where_conditions)

            # Si hay paginación, usar ROW_NUMBER() (compatible con SQL Server 2008)
            if page is not None and limit is not None:
                page = max(1, int(page))
                limit = max(1, min(500, int(limit)))  # Máximo 500 registros por página
                offset = (page - 1) * limit

                # Primero obtener el total de registros
                count_query = f"SELECT COUNT(*) FROM view_externos_stock WHERE {where_clause}"
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]

                # Query con paginación usando ROW_NUMBER()
                query = f"""
                    SELECT * FROM (
                        SELECT
                            empresa, codigo, descripcion, calidad, color, tono, calibre,
                            formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet,
                            existencias, ean13, pesocaja, pesopallet, tipo_producto, piezascaja,
                            ROW_NUMBER() OVER (ORDER BY {order_by} {order_dir}) AS row_num
                        FROM view_externos_stock
                        WHERE {where_clause}
                    ) AS numbered
                    WHERE row_num > ? AND row_num <= ?
                """
                params.extend([offset, offset + limit])
            else:
                # Sin paginación - comportamiento original con ordenación
                query = f"""
                    SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                           formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet,
                           existencias, ean13, pesocaja, pesopallet, tipo_producto, piezascaja
                    FROM view_externos_stock
                    WHERE {where_clause}
                    ORDER BY {order_by} {order_dir}
                """

            cursor.execute(query, params)

            stocks = [_row_to_stock(row) for row in cursor.fetchall()]

            # Devolver con metadatos de paginación si aplica
            if page is not None and limit is not None:
                total_pages = (total + limit - 1) // limit  # Redondeo hacia arriba
                return {
                    'data': stocks,
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': total_pages
                }

            return stocks
        finally:
            conn.close()

    @staticmethod
    def get_valores_unicos(columna, limite=100):
        """
        Obtiene los valores únicos de una columna para filtros estilo Excel.

        Args:
            columna: nombre de la columna (debe estar en VALID_FILTER_COLUMNS)
            limite: máximo de valores a devolver (default 100)

        Returns:
            Lista de valores únicos ordenados
        """
        # Validar columna (seguridad contra SQL injection)
        if columna not in StockModel.VALID_FILTER_COLUMNS:
            return []

        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        try:
            cursor = conn.cursor()

            # Query para obtener valores únicos
            query = f"""
                SELECT DISTINCT TOP {min(limite, 500)} {columna}
                FROM view_externos_stock
                WHERE empresa = ? AND {columna} IS NOT NULL AND {columna} <> ''
                ORDER BY {columna}
            """
            cursor.execute(query, (empresa_erp,))

            valores = [_s(row[0]) for row in cursor.fetchall()]

            return valores
        finally:
            conn.close()

    @staticmethod
    def get_resumen():
        """Obtiene un resumen de estadísticas del stock"""
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) as total_productos,
                    SUM(existencias) as total_existencias,
                    AVG(existencias) as promedio_existencias,
                    MIN(existencias) as minimo_existencias,
                    MAX(existencias) as maximo_existencias
                FROM view_externos_stock
                WHERE empresa = ?
            """, (empresa_erp,))
            row = cursor.fetchone()

            resumen = {
                'total_productos': row[0],
                'total_existencias': float(row[1]) if row[1] else 0.0,
                'promedio_existencias': float(row[2]) if row[2] else 0.0,
                'minimo_existencias': float(row[3]) if row[3] else 0.0,
                'maximo_existencias': float(row[4]) if row[4] else 0.0
            }

            return resumen
        finally:
            conn.close()
