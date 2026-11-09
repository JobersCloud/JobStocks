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
# ARCHIVO: models/parametros_model.py
# ============================================
from config.database import Database

class ParametrosModel:
    @staticmethod
    def get(clave, empresa_id, connection=None):
        """Obtiene el valor de un parámetro por su clave y empresa

        Args:
            clave: Nombre del parámetro
            empresa_id: ID empresa_erp para filtrar en BD
            connection: ID para conexión (opcional, si no se pasa obtiene de sesión)
        """
        conn = Database.get_connection(connection)
        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT valor FROM parametros WHERE clave = ? AND empresa_id = ?
            """, (clave, empresa_id))

            row = cursor.fetchone()
            cursor.close()

            return row[0] if row else None
        finally:
            conn.close()

    @staticmethod
    def get_bool(clave, empresa_id, connection=None, default=False):
        """Obtiene un parámetro como booleano (1=True, 0=False)

        Args:
            default: Valor devuelto si el parámetro no existe en la empresa.
                     Útil para parámetros añadidos a posteriori sobre
                     funcionalidades que ya estaban visibles.
        """
        valor = ParametrosModel.get(clave, empresa_id, connection)
        if valor is None:
            return default
        return valor == '1'

    @staticmethod
    def set(clave, valor, empresa_id, connection=None):
        """Actualiza el valor de un parámetro para una empresa"""
        conn = Database.get_connection(connection)
        try:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE parametros
                SET valor = ?, fecha_modificacion = GETDATE()
                WHERE clave = ? AND empresa_id = ?
            """, (valor, clave, empresa_id))

            affected = cursor.rowcount
            conn.commit()
            cursor.close()

            return affected > 0
        finally:
            conn.close()

    @staticmethod
    def get_all(empresa_id, connection=None):
        """Obtiene todos los parámetros de una empresa"""
        conn = Database.get_connection(connection)
        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT clave, valor, descripcion, fecha_modificacion
                FROM parametros
                WHERE empresa_id = ?
                ORDER BY clave
            """, (empresa_id,))

            parametros = []
            for row in cursor.fetchall():
                parametros.append({
                    'clave': row[0],
                    'valor': row[1],
                    'descripcion': row[2],
                    'fecha_modificacion': row[3].isoformat() if row[3] else None
                })

            cursor.close()

            return parametros
        finally:
            conn.close()

    @staticmethod
    def permitir_registro(empresa_id, connection=None):
        """Verifica si el registro público está permitido para una empresa"""
        return ParametrosModel.get_bool('PERMITIR_REGISTRO', empresa_id, connection)

    @staticmethod
    def permitir_propuestas(empresa_id, connection=None):
        """Verifica si las propuestas/solicitudes están permitidas para una empresa"""
        return ParametrosModel.get_bool('PERMITIR_PROPUESTAS', empresa_id, connection)

    @staticmethod
    def grid_con_imagenes(empresa_id, connection=None):
        """Verifica si se deben mostrar imágenes en la tabla/tarjetas de stock"""
        return ParametrosModel.get_bool('GRID_CON_IMAGENES', empresa_id, connection)

    @staticmethod
    def permitir_firma(empresa_id, connection=None):
        """Verifica si la firma de propuestas está habilitada para una empresa"""
        return ParametrosModel.get_bool('PERMITIR_FIRMA', empresa_id, connection)

    @staticmethod
    def permitir_busqueda_voz(empresa_id, connection=None):
        """Verifica si la búsqueda por voz está habilitada para una empresa"""
        return ParametrosModel.get_bool('PERMITIR_BUSQUEDA_VOZ', empresa_id, connection)

    @staticmethod
    def mostrar_precios(empresa_id, connection=None):
        """Verifica si se deben mostrar precios de artículos para una empresa"""
        return ParametrosModel.get_bool('MOSTRAR_PRECIOS', empresa_id, connection)

    @staticmethod
    def visible_pedidos(empresa_id, connection=None):
        """Verifica si la sección Mis Pedidos es visible para una empresa"""
        return ParametrosModel.get_bool('VISIBLE_PEDIDOS', empresa_id, connection)

    @staticmethod
    def visible_albaranes(empresa_id, connection=None):
        """Verifica si la sección Albaranes es visible para una empresa"""
        return ParametrosModel.get_bool('VISIBLE_ALBARANES', empresa_id, connection)

    @staticmethod
    def visible_facturas(empresa_id, connection=None):
        """Verifica si la sección Facturas es visible para una empresa"""
        return ParametrosModel.get_bool('VISIBLE_FACTURAS', empresa_id, connection)

    @staticmethod
    def visible_propuestas(empresa_id, connection=None):
        """Verifica si la sección Propuestas es visible para una empresa"""
        return ParametrosModel.get_bool('VISIBLE_PROPUESTAS', empresa_id, connection)

    @staticmethod
    def visible_stock_anulados(empresa_id, connection=None):
        """Verifica si la sección Stocks Anulados es visible para una empresa"""
        return ParametrosModel.get_bool('VISIBLE_STOCK_ANULADOS', empresa_id, connection)

    @staticmethod
    def visible_busqueda_magica(empresa_id, connection=None):
        """Verifica si la sección Búsqueda Mágica es visible para una empresa"""
        return ParametrosModel.get_bool('VISIBLE_BUSQUEDA_MAGICA', empresa_id, connection)

    @staticmethod
    def visible_consultas(empresa_id, connection=None):
        """Verifica si la sección Consultas es visible para una empresa

        Por defecto visible: la funcionalidad existía antes que el parámetro,
        así que una empresa sin el registro no debe perder el menú.
        """
        return ParametrosModel.get_bool('VISIBLE_CONSULTAS', empresa_id, connection, default=True)

    @staticmethod
    def visible_favoritos(empresa_id, connection=None):
        """Verifica si la sección Favoritos es visible para una empresa

        Por defecto visible, igual que Consultas.
        """
        return ParametrosModel.get_bool('VISIBLE_FAVORITOS', empresa_id, connection, default=True)

    @staticmethod
    def columnas_opcionales(empresa_id, connection=None):
        """Devuelve lista de columnas opcionales visibles para la empresa."""
        import json
        valor = ParametrosModel.get('STOCK_COLUMNAS_OPCIONALES', empresa_id, connection)
        if valor:
            try:
                return json.loads(valor)
            except (json.JSONDecodeError, TypeError):
                pass
        return ['color', 'calidad', 'tono', 'calibre']

    @staticmethod
    def create_if_not_exists(clave, valor, descripcion, empresa_id, connection=None):
        """Crea un parámetro si no existe para la empresa"""
        conn = Database.get_connection(connection)
        try:
            cursor = conn.cursor()

            # Verificar si existe
            cursor.execute("""
                SELECT 1 FROM parametros WHERE clave = ? AND empresa_id = ?
            """, (clave, empresa_id))

            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO parametros (clave, valor, descripcion, empresa_id, fecha_modificacion)
                    VALUES (?, ?, ?, ?, GETDATE())
                """, (clave, valor, descripcion, empresa_id))
                conn.commit()
                cursor.close()
                return True

            cursor.close()
            return False
        finally:
            conn.close()
