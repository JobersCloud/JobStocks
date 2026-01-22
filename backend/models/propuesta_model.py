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
# ARCHIVO: models/propuesta_model.py
# Descripcion: Modelo para guardar propuestas/solicitudes en BD
# ============================================
from config.database import Database


class PropuestaModel:
    @staticmethod
    def crear_propuesta(user_id, carrito, comentarios='', empresa_id='1', referencia='', cliente_id=None):
        """
        Crea una propuesta con sus lineas de detalle.

        Args:
            user_id: ID del usuario que envia la propuesta
            carrito: Lista de items del carrito
            comentarios: Comentarios adicionales (opcional)
            empresa_id: ID de la empresa (multi-empresa)
            referencia: Referencia del cliente (opcional)
            cliente_id: ID del cliente asociado a la propuesta

        Returns:
            int: ID de la propuesta creada
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        try:
            # 1. Insertar cabecera de propuesta
            cursor.execute("""
                INSERT INTO propuestas (user_id, empresa_id, comentarios, estado, total_items, referencia, cliente_id)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, 'Enviada', ?, ?, ?)
            """, (user_id, empresa_id, comentarios, len(carrito), referencia or None, cliente_id or None))

            propuesta_id = cursor.fetchone()[0]

            # 2. Insertar lineas de detalle
            for item in carrito:
                cursor.execute("""
                    INSERT INTO propuestas_lineas (
                        propuesta_id, codigo, descripcion, formato, calidad,
                        color, tono, calibre, pallet, caja, unidad,
                        existencias, cantidad_solicitada
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    propuesta_id,
                    item.get('codigo', ''),
                    item.get('descripcion', ''),
                    item.get('formato', ''),
                    item.get('calidad', ''),
                    item.get('color', ''),
                    item.get('tono', ''),
                    item.get('calibre', ''),
                    item.get('pallet', ''),
                    item.get('caja', ''),
                    item.get('unidad', ''),
                    item.get('existencias', 0),
                    item.get('cantidad_solicitada', 0)
                ))

            conn.commit()
            return propuesta_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_by_id(propuesta_id):
        """
        Obtiene una propuesta por ID con sus lineas.

        Args:
            propuesta_id: ID de la propuesta

        Returns:
            dict: Propuesta con sus lineas o None si no existe
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        # Obtener cabecera
        cursor.execute("""
            SELECT p.id, p.user_id, p.empresa_id, p.fecha, p.comentarios, p.estado,
                   p.total_items, p.fecha_modificacion, u.username, u.full_name, p.referencia, p.cliente_id
            FROM propuestas p
            INNER JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        """, (propuesta_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        propuesta = {
            'id': row[0],
            'user_id': row[1],
            'empresa_id': row[2],
            'fecha': row[3].isoformat() if row[3] else None,
            'comentarios': row[4],
            'estado': row[5],
            'total_items': row[6],
            'fecha_modificacion': row[7].isoformat() if row[7] else None,
            'username': row[8],
            'full_name': row[9],
            'referencia': row[10],
            'cliente_id': row[11],
            'lineas': []
        }

        # Obtener lineas
        cursor.execute("""
            SELECT id, codigo, descripcion, formato, calidad, color, tono,
                   calibre, pallet, caja, unidad, existencias, cantidad_solicitada
            FROM propuestas_lineas
            WHERE propuesta_id = ?
        """, (propuesta_id,))

        for row in cursor.fetchall():
            propuesta['lineas'].append({
                'id': row[0],
                'codigo': row[1],
                'descripcion': row[2],
                'formato': row[3],
                'calidad': row[4],
                'color': row[5],
                'tono': row[6],
                'calibre': row[7],
                'pallet': row[8],
                'caja': row[9],
                'unidad': row[10],
                'existencias': float(row[11]) if row[11] else 0,
                'cantidad_solicitada': float(row[12]) if row[12] else 0
            })

        conn.close()
        return propuesta

    @staticmethod
    def get_by_user(user_id, empresa_id=None):
        """
        Obtiene todas las propuestas de un usuario.

        Args:
            user_id: ID del usuario
            empresa_id: Filtrar por empresa (opcional)

        Returns:
            list: Lista de propuestas (solo cabecera)
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, empresa_id, fecha, comentarios, estado, total_items, fecha_modificacion, referencia, cliente_id
            FROM propuestas
            WHERE user_id = ?
        """
        params = [user_id]

        if empresa_id:
            query += " AND empresa_id = ?"
            params.append(empresa_id)

        query += " ORDER BY fecha DESC"

        cursor.execute(query, params)

        propuestas = []
        for row in cursor.fetchall():
            propuestas.append({
                'id': row[0],
                'empresa_id': row[1],
                'fecha': row[2].isoformat() if row[2] else None,
                'comentarios': row[3],
                'estado': row[4],
                'total_items': row[5],
                'fecha_modificacion': row[6].isoformat() if row[6] else None,
                'referencia': row[7],
                'cliente_id': row[8]
            })

        conn.close()
        return propuestas

    @staticmethod
    def get_all(empresa_id=None, estado=None):
        """
        Obtiene todas las propuestas (para administradores).

        Args:
            empresa_id: Filtrar por empresa (opcional)
            estado: Filtrar por estado (opcional)

        Returns:
            list: Lista de propuestas con info del usuario
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT p.id, p.user_id, p.empresa_id, p.fecha, p.comentarios, p.estado,
                   p.total_items, p.fecha_modificacion, u.username, u.full_name, u.email, p.referencia, p.cliente_id
            FROM propuestas p
            INNER JOIN users u ON p.user_id = u.id
            WHERE 1=1
        """
        params = []

        if empresa_id:
            query += " AND p.empresa_id = ?"
            params.append(empresa_id)

        if estado:
            query += " AND p.estado = ?"
            params.append(estado)

        query += " ORDER BY p.fecha DESC"

        cursor.execute(query, params)

        propuestas = []
        for row in cursor.fetchall():
            propuestas.append({
                'id': row[0],
                'user_id': row[1],
                'empresa_id': row[2],
                'fecha': row[3].isoformat() if row[3] else None,
                'comentarios': row[4],
                'estado': row[5],
                'total_items': row[6],
                'fecha_modificacion': row[7].isoformat() if row[7] else None,
                'username': row[8],
                'full_name': row[9],
                'email': row[10],
                'referencia': row[11],
                'cliente_id': row[12]
            })

        conn.close()
        return propuestas

    @staticmethod
    def actualizar_estado(propuesta_id, estado):
        """
        Actualiza el estado de una propuesta.

        Args:
            propuesta_id: ID de la propuesta
            estado: Nuevo estado ('Enviada', 'Procesada', 'Cancelada')

        Returns:
            bool: True si se actualizo correctamente
        """
        if estado not in ['Enviada', 'Procesada', 'Cancelada']:
            raise ValueError(f"Estado invalido: {estado}")

        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE propuestas
            SET estado = ?
            WHERE id = ?
        """, (estado, propuesta_id))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    @staticmethod
    def get_pendientes(incluir_lineas=False, empresa_id=None):
        """
        Obtiene todas las propuestas pendientes de procesar (estado='Enviada').

        Args:
            incluir_lineas: Si True, incluye las lineas de detalle
            empresa_id: Filtrar por empresa (opcional)

        Returns:
            list: Lista de propuestas pendientes con info del usuario
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT p.id, p.user_id, p.empresa_id, p.fecha, p.comentarios, p.estado,
                   p.total_items, p.fecha_modificacion, u.username, u.full_name, u.email, p.referencia, p.cliente_id
            FROM propuestas p
            INNER JOIN users u ON p.user_id = u.id
            WHERE p.estado = 'Enviada'
        """
        params = []

        if empresa_id:
            query += " AND p.empresa_id = ?"
            params.append(empresa_id)

        query += " ORDER BY p.fecha ASC"

        cursor.execute(query, params)

        propuestas = []
        for row in cursor.fetchall():
            propuesta = {
                'id': row[0],
                'user_id': row[1],
                'empresa_id': row[2],
                'fecha': row[3].isoformat() if row[3] else None,
                'comentarios': row[4],
                'estado': row[5],
                'total_items': row[6],
                'fecha_modificacion': row[7].isoformat() if row[7] else None,
                'username': row[8],
                'full_name': row[9],
                'email': row[10],
                'referencia': row[11],
                'cliente_id': row[12]
            }

            if incluir_lineas:
                propuesta['lineas'] = []
                cursor2 = conn.cursor()
                cursor2.execute("""
                    SELECT id, codigo, descripcion, formato, calidad, color, tono,
                           calibre, pallet, caja, unidad, existencias, cantidad_solicitada
                    FROM propuestas_lineas
                    WHERE propuesta_id = ?
                """, (row[0],))

                for linea in cursor2.fetchall():
                    propuesta['lineas'].append({
                        'id': linea[0],
                        'codigo': linea[1],
                        'descripcion': linea[2],
                        'formato': linea[3],
                        'calidad': linea[4],
                        'color': linea[5],
                        'tono': linea[6],
                        'calibre': linea[7],
                        'pallet': linea[8],
                        'caja': linea[9],
                        'unidad': linea[10],
                        'existencias': float(linea[11]) if linea[11] else 0,
                        'cantidad_solicitada': float(linea[12]) if linea[12] else 0
                    })

            propuestas.append(propuesta)

        conn.close()
        return propuestas

    @staticmethod
    def get_lineas(propuesta_id=None):
        """
        Obtiene lineas de propuestas con filtro opcional.

        Args:
            propuesta_id: ID de propuesta para filtrar (opcional)

        Returns:
            list: Lista de lineas con info de la propuesta
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT l.id, l.propuesta_id, l.codigo, l.descripcion, l.formato,
                   l.calidad, l.color, l.tono, l.calibre, l.pallet, l.caja,
                   l.unidad, l.existencias, l.cantidad_solicitada,
                   p.fecha, p.estado, u.username, u.full_name
            FROM propuestas_lineas l
            INNER JOIN propuestas p ON l.propuesta_id = p.id
            INNER JOIN users u ON p.user_id = u.id
        """

        params = []
        if propuesta_id:
            query += " WHERE l.propuesta_id = ?"
            params.append(propuesta_id)

        query += " ORDER BY l.propuesta_id, l.id"

        cursor.execute(query, params)

        lineas = []
        for row in cursor.fetchall():
            lineas.append({
                'id': row[0],
                'propuesta_id': row[1],
                'codigo': row[2],
                'descripcion': row[3],
                'formato': row[4],
                'calidad': row[5],
                'color': row[6],
                'tono': row[7],
                'calibre': row[8],
                'pallet': row[9],
                'caja': row[10],
                'unidad': row[11],
                'existencias': float(row[12]) if row[12] else 0,
                'cantidad_solicitada': float(row[13]) if row[13] else 0,
                'propuesta_fecha': row[14].isoformat() if row[14] else None,
                'propuesta_estado': row[15],
                'username': row[16],
                'full_name': row[17]
            })

        conn.close()
        return lineas
