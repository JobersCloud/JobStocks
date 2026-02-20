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
# ARCHIVO: models/consulta_model.py
# Modelo para gestión de consultas sobre productos
# ============================================
from config.database import Database
import traceback


class ConsultaModel:
    @staticmethod
    def crear(data):
        """Crear una nueva consulta"""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO consultas (
                    empresa_id, codigo_producto, descripcion_producto,
                    formato, calidad, color, tono, calibre,
                    nombre_cliente, email_cliente, telefono_cliente,
                    mensaje, user_id
                )
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['empresa_id'],
                data['codigo_producto'],
                data.get('descripcion_producto'),
                data.get('formato'),
                data.get('calidad'),
                data.get('color'),
                data.get('tono'),
                data.get('calibre'),
                data['nombre_cliente'],
                data['email_cliente'],
                data.get('telefono_cliente'),
                data['mensaje'],
                data.get('user_id')
            ))

            consulta_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()

            print(f"✅ Consulta {consulta_id} creada correctamente")
            return consulta_id

        except Exception as e:
            print(f"❌ Error al crear consulta: {e}")
            traceback.print_exc()
            return None

    @staticmethod
    def get_by_id(consulta_id, empresa_id):
        """Obtener una consulta por ID"""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id, empresa_id, codigo_producto, descripcion_producto,
                    formato, calidad, color, tono, calibre,
                    nombre_cliente, email_cliente, telefono_cliente,
                    mensaje, user_id, estado, respuesta,
                    fecha_respuesta, respondido_por, fecha_creacion
                FROM consultas
                WHERE id = ? AND empresa_id = ?
            """, (consulta_id, empresa_id))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'empresa_id': row[1],
                    'codigo_producto': row[2],
                    'descripcion_producto': row[3],
                    'formato': row[4],
                    'calidad': row[5],
                    'color': row[6],
                    'tono': row[7],
                    'calibre': row[8],
                    'nombre_cliente': row[9],
                    'email_cliente': row[10],
                    'telefono_cliente': row[11],
                    'mensaje': row[12],
                    'user_id': row[13],
                    'estado': row[14],
                    'respuesta': row[15],
                    'fecha_respuesta': row[16].isoformat() if row[16] else None,
                    'respondido_por': row[17],
                    'fecha_creacion': row[18].isoformat() if row[18] else None
                }

            return None

        except Exception as e:
            print(f"❌ Error al obtener consulta: {e}")
            return None

    @staticmethod
    def get_by_user(user_id, empresa_id, estado=None):
        """Obtener consultas de un usuario específico"""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    c.id, c.empresa_id, c.codigo_producto, c.descripcion_producto,
                    c.formato, c.calidad, c.color, c.tono, c.calibre,
                    c.nombre_cliente, c.email_cliente, c.telefono_cliente,
                    c.mensaje, c.user_id, c.estado, c.respuesta,
                    c.fecha_respuesta, c.respondido_por, c.fecha_creacion,
                    u.username as respondido_por_nombre
                FROM consultas c
                LEFT JOIN users u ON c.respondido_por = u.id
                WHERE c.user_id = ? AND c.empresa_id = ?
            """
            params = [user_id, empresa_id]

            if estado:
                query += " AND c.estado = ?"
                params.append(estado)

            query += " ORDER BY c.fecha_creacion DESC"

            cursor.execute(query, params)

            consultas = []
            for row in cursor.fetchall():
                consultas.append({
                    'id': row[0],
                    'empresa_id': row[1],
                    'codigo_producto': row[2],
                    'descripcion_producto': row[3],
                    'formato': row[4],
                    'calidad': row[5],
                    'color': row[6],
                    'tono': row[7],
                    'calibre': row[8],
                    'nombre_cliente': row[9],
                    'email_cliente': row[10],
                    'telefono_cliente': row[11],
                    'mensaje': row[12],
                    'user_id': row[13],
                    'estado': row[14],
                    'respuesta': row[15],
                    'fecha_respuesta': row[16].isoformat() if row[16] else None,
                    'respondido_por': row[17],
                    'fecha_creacion': row[18].isoformat() if row[18] else None,
                    'respondido_por_nombre': row[19]
                })

            conn.close()
            return consultas

        except Exception as e:
            print(f"❌ Error al obtener consultas del usuario: {e}")
            traceback.print_exc()
            return []

    @staticmethod
    def get_all_by_empresa(empresa_id, estado=None):
        """Obtener todas las consultas de una empresa"""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    c.id, c.empresa_id, c.codigo_producto, c.descripcion_producto,
                    c.formato, c.calidad, c.color, c.tono, c.calibre,
                    c.nombre_cliente, c.email_cliente, c.telefono_cliente,
                    c.mensaje, c.user_id, c.estado, c.respuesta,
                    c.fecha_respuesta, c.respondido_por, c.fecha_creacion,
                    u.username as respondido_por_nombre
                FROM consultas c
                LEFT JOIN users u ON c.respondido_por = u.id
                WHERE c.empresa_id = ?
            """
            params = [empresa_id]

            if estado:
                query += " AND c.estado = ?"
                params.append(estado)

            query += " ORDER BY c.fecha_creacion DESC"

            cursor.execute(query, params)

            consultas = []
            for row in cursor.fetchall():
                consultas.append({
                    'id': row[0],
                    'empresa_id': row[1],
                    'codigo_producto': row[2],
                    'descripcion_producto': row[3],
                    'formato': row[4],
                    'calidad': row[5],
                    'color': row[6],
                    'tono': row[7],
                    'calibre': row[8],
                    'nombre_cliente': row[9],
                    'email_cliente': row[10],
                    'telefono_cliente': row[11],
                    'mensaje': row[12],
                    'user_id': row[13],
                    'estado': row[14],
                    'respuesta': row[15],
                    'fecha_respuesta': row[16].isoformat() if row[16] else None,
                    'respondido_por': row[17],
                    'fecha_creacion': row[18].isoformat() if row[18] else None,
                    'respondido_por_nombre': row[19]
                })

            conn.close()
            return consultas

        except Exception as e:
            print(f"❌ Error al obtener consultas: {e}")
            traceback.print_exc()
            return []

    @staticmethod
    def responder(consulta_id, empresa_id, respuesta, respondido_por):
        """Responder a una consulta"""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE consultas
                SET respuesta = ?, estado = 'respondida',
                    fecha_respuesta = GETDATE(), respondido_por = ?
                WHERE id = ? AND empresa_id = ?
            """, (respuesta, respondido_por, consulta_id, empresa_id))

            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()

            return rows_affected > 0

        except Exception as e:
            print(f"❌ Error al responder consulta: {e}")
            return False

    @staticmethod
    def cambiar_estado(consulta_id, empresa_id, estado):
        """Cambiar el estado de una consulta"""
        if estado not in ['pendiente', 'respondida', 'cerrada']:
            raise ValueError(f"Estado inválido: {estado}")

        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE consultas
                SET estado = ?
                WHERE id = ? AND empresa_id = ?
            """, (estado, consulta_id, empresa_id))

            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()

            return rows_affected > 0

        except Exception as e:
            print(f"❌ Error al cambiar estado: {e}")
            return False

    @staticmethod
    def contar_pendientes(empresa_id):
        """Contar consultas pendientes de una empresa"""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM consultas
                WHERE empresa_id = ? AND estado = 'pendiente'
            """, (empresa_id,))

            count = cursor.fetchone()[0]
            conn.close()

            return count

        except Exception as e:
            print(f"❌ Error al contar consultas: {e}")
            return 0
