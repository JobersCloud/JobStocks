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
# ARCHIVO: models/estadisticas_model.py
# Descripcion: Modelo para estadisticas del dashboard de administracion
# ============================================
from config.database import Database
from datetime import datetime, timedelta
import json


class EstadisticasModel:
    @staticmethod
    def get_resumen(empresa_id='1'):
        """
        Obtiene un resumen general de estadisticas.

        Returns:
            dict: Resumen con totales
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        # Total propuestas
        cursor.execute("""
            SELECT COUNT(*) FROM propuestas WHERE empresa_id = ?
        """, (empresa_id,))
        total_propuestas = cursor.fetchone()[0]

        # Propuestas pendientes (estado = 'Enviada')
        cursor.execute("""
            SELECT COUNT(*) FROM propuestas WHERE empresa_id = ? AND estado = 'Enviada'
        """, (empresa_id,))
        propuestas_pendientes = cursor.fetchone()[0]

        # Total usuarios activos
        cursor.execute("""
            SELECT COUNT(*) FROM users WHERE active = 1
        """)
        usuarios_activos = cursor.fetchone()[0]

        # Total consultas pendientes
        cursor.execute("""
            SELECT COUNT(*) FROM consultas WHERE empresa_id = ? AND estado = 'pendiente'
        """, (empresa_id,))
        consultas_pendientes = cursor.fetchone()[0]

        # Total items solicitados (suma de cantidad_solicitada)
        cursor.execute("""
            SELECT ISNULL(SUM(pl.cantidad_solicitada), 0)
            FROM propuestas_lineas pl
            INNER JOIN propuestas p ON pl.propuesta_id = p.id
            WHERE p.empresa_id = ?
        """, (empresa_id,))
        total_items_solicitados = cursor.fetchone()[0]

        # Totales almacen desglosados por unidad (M2 y Piezas)
        # Probar columna 'unidad' y fallback a 'tipo_unidad'
        almacen_m2 = 0
        almacen_piezas = 0
        for col_name in ('unidad', 'tipo_unidad'):
            try:
                cursor.execute(f"""
                    SELECT
                        ISNULL(SUM(CASE WHEN {col_name} = 1 THEN existencias ELSE 0 END), 0),
                        ISNULL(SUM(CASE WHEN {col_name} = 0 THEN existencias ELSE 0 END), 0)
                    FROM view_externos_almlinubica
                    WHERE empresa = ?
                """, (empresa_id,))
                row_alm = cursor.fetchone()
                if row_alm:
                    almacen_m2 = float(row_alm[0]) if row_alm[0] else 0
                    almacen_piezas = float(row_alm[1]) if row_alm[1] else 0
                break
            except Exception:
                continue

        conn.close()

        return {
            'total_propuestas': total_propuestas,
            'propuestas_pendientes': propuestas_pendientes,
            'usuarios_activos': usuarios_activos,
            'consultas_pendientes': consultas_pendientes,
            'total_items_solicitados': float(total_items_solicitados) if total_items_solicitados else 0,
            'almacen_m2': almacen_m2,
            'almacen_piezas': almacen_piezas
        }

    @staticmethod
    def get_productos_mas_solicitados(empresa_id='1', limit=10):
        """
        Obtiene los productos mas solicitados.

        Args:
            empresa_id: ID de la empresa
            limit: Cantidad de productos a retornar

        Returns:
            list: Lista de productos con cantidad total solicitada
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP (?)
                pl.codigo,
                pl.descripcion,
                pl.formato,
                SUM(pl.cantidad_solicitada) as total_solicitado,
                COUNT(*) as veces_solicitado
            FROM propuestas_lineas pl
            INNER JOIN propuestas p ON pl.propuesta_id = p.id
            WHERE p.empresa_id = ?
            GROUP BY pl.codigo, pl.descripcion, pl.formato
            ORDER BY total_solicitado DESC
        """, (limit, empresa_id))

        productos = []
        for row in cursor.fetchall():
            productos.append({
                'codigo': row[0],
                'descripcion': row[1],
                'formato': row[2],
                'total_solicitado': float(row[3]) if row[3] else 0,
                'veces_solicitado': row[4]
            })

        conn.close()
        return productos

    @staticmethod
    def get_propuestas_por_periodo(empresa_id='1', dias=30):
        """
        Obtiene las propuestas agrupadas por dia.

        Args:
            empresa_id: ID de la empresa
            dias: Cantidad de dias hacia atras

        Returns:
            list: Lista de fechas con cantidad de propuestas
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                CAST(fecha AS DATE) as dia,
                COUNT(*) as cantidad,
                ISNULL(SUM(total_items), 0) as total_items
            FROM propuestas
            WHERE empresa_id = ? AND fecha >= DATEADD(DAY, -?, GETDATE())
            GROUP BY CAST(fecha AS DATE)
            ORDER BY dia ASC
        """, (empresa_id, dias))

        propuestas = []
        for row in cursor.fetchall():
            propuestas.append({
                'fecha': row[0].isoformat() if row[0] else None,
                'cantidad': row[1],
                'total_items': row[2]
            })

        conn.close()
        return propuestas

    @staticmethod
    def get_propuestas_por_estado(empresa_id='1'):
        """
        Obtiene el conteo de propuestas por estado.

        Args:
            empresa_id: ID de la empresa

        Returns:
            dict: Conteo por estado
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM propuestas
            WHERE empresa_id = ?
            GROUP BY estado
        """, (empresa_id,))

        estados = {}
        for row in cursor.fetchall():
            estados[row[0]] = row[1]

        conn.close()
        return estados

    @staticmethod
    def get_usuarios_mas_activos(empresa_id='1', limit=10):
        """
        Obtiene los usuarios con mas propuestas.

        Args:
            empresa_id: ID de la empresa
            limit: Cantidad de usuarios a retornar

        Returns:
            list: Lista de usuarios con cantidad de propuestas
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP (?)
                u.id,
                u.username,
                u.full_name,
                COUNT(p.id) as total_propuestas,
                MAX(p.fecha) as ultima_propuesta
            FROM users u
            INNER JOIN propuestas p ON u.id = p.user_id
            WHERE p.empresa_id = ?
            GROUP BY u.id, u.username, u.full_name
            ORDER BY total_propuestas DESC
        """, (limit, empresa_id))

        usuarios = []
        for row in cursor.fetchall():
            usuarios.append({
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'total_propuestas': row[3],
                'ultima_propuesta': row[4].isoformat() if row[4] else None
            })

        conn.close()
        return usuarios

    @staticmethod
    def get_propuestas_por_mes(empresa_id='1', meses=12):
        """
        Obtiene las propuestas agrupadas por mes.

        Args:
            empresa_id: ID de la empresa
            meses: Cantidad de meses hacia atras

        Returns:
            list: Lista de meses con cantidad de propuestas
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                YEAR(fecha) as anio,
                MONTH(fecha) as mes,
                COUNT(*) as cantidad,
                SUM(total_items) as total_items
            FROM propuestas
            WHERE empresa_id = ?
                AND fecha >= DATEADD(MONTH, -?, GETDATE())
            GROUP BY YEAR(fecha), MONTH(fecha)
            ORDER BY anio ASC, mes ASC
        """, (empresa_id, meses))

        propuestas = []
        for row in cursor.fetchall():
            propuestas.append({
                'anio': row[0],
                'mes': row[1],
                'cantidad': row[2],
                'total_items': row[3]
            })

        conn.close()
        return propuestas

    @staticmethod
    def get_articulos_mas_vistos(empresa_id='1', limit=10, dias=30):
        """
        Obtiene los articulos mas vistos (desde audit_log ARTICLE_VIEW).

        Args:
            empresa_id: ID de la empresa
            limit: Cantidad de articulos a retornar
            dias: Periodo en dias hacia atras

        Returns:
            list: Lista de articulos con cantidad de vistas
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        try:
            # Query solo de audit_log (sin dependencia de vistas externas)
            cursor.execute("""
                SELECT TOP (?)
                    a.recurso_id as codigo,
                    COUNT(*) as vistas,
                    COUNT(DISTINCT a.user_id) as usuarios_unicos,
                    MAX(a.fecha) as ultima_vista
                FROM audit_log a
                WHERE a.accion = 'ARTICLE_VIEW'
                    AND a.empresa_id = ?
                    AND a.fecha >= DATEADD(DAY, ?, GETDATE())
                GROUP BY a.recurso_id
                ORDER BY vistas DESC
            """, (limit, empresa_id, -dias))

            articulos = []
            for row in cursor.fetchall():
                codigo = row[0].strip() if row[0] else row[0]
                articulos.append({
                    'codigo': codigo,
                    'vistas': row[1],
                    'usuarios_unicos': row[2],
                    'ultima_vista': row[3].isoformat() if row[3] else None,
                    'descripcion': codigo
                })

            # Intentar obtener descripciones y formato
            # Primero view_externos_articulos (maestro, no depende de stock),
            # fallback a view_externos_stock
            if articulos:
                codigos = [a['codigo'] for a in articulos]
                placeholders = ','.join(['?' for _ in codigos])
                desc_map = {}

                # Intento 1: view_externos_articulos (tiene todos los articulos)
                try:
                    cursor.execute(f"""
                        SELECT DISTINCT codigo, descripcion, formato FROM view_externos_articulos
                        WHERE codigo IN ({placeholders}) AND empresa = ?
                    """, codigos + [empresa_id])
                    for row in cursor.fetchall():
                        key = row[0].strip() if row[0] else row[0]
                        desc = (row[1].strip() if row[1] else '') or ''
                        fmt = (row[2].strip() if row[2] else '') or ''
                        if key not in desc_map or (desc and desc != key):
                            desc_map[key] = {'descripcion': desc or key, 'formato': fmt}
                except Exception:
                    pass  # Vista no existe, intentar fallback

                # Intento 2: view_externos_stock para codigos que no se encontraron
                codigos_faltantes = [c for c in codigos if c not in desc_map]
                if codigos_faltantes:
                    try:
                        placeholders2 = ','.join(['?' for _ in codigos_faltantes])
                        cursor.execute(f"""
                            SELECT DISTINCT codigo, descripcion, formato FROM view_externos_stock
                            WHERE codigo IN ({placeholders2}) AND empresa = ?
                        """, codigos_faltantes + [empresa_id])
                        for row in cursor.fetchall():
                            key = row[0].strip() if row[0] else row[0]
                            desc = (row[1].strip() if row[1] else '') or ''
                            fmt = (row[2].strip() if row[2] else '') or ''
                            if key not in desc_map or (desc and desc != key and not desc_map[key].get('has_desc')):
                                desc_map[key] = {'descripcion': desc or key, 'formato': fmt}
                    except Exception:
                        pass

                # Intento 3: propuestas_lineas para codigos que siguen sin descripcion
                codigos_faltantes2 = [c for c in codigos if c not in desc_map]
                if codigos_faltantes2:
                    try:
                        placeholders3 = ','.join(['?' for _ in codigos_faltantes2])
                        cursor.execute(f"""
                            SELECT pl.codigo, pl.descripcion, pl.formato
                            FROM (
                                SELECT codigo, descripcion, formato,
                                    ROW_NUMBER() OVER (PARTITION BY RTRIM(codigo) ORDER BY pl2.id DESC) as rn
                                FROM propuestas_lineas pl2
                                INNER JOIN propuestas p ON pl2.propuesta_id = p.id
                                WHERE RTRIM(pl2.codigo) IN ({placeholders3}) AND p.empresa_id = ?
                            ) pl
                            WHERE pl.rn = 1
                        """, codigos_faltantes2 + [empresa_id])
                        for row in cursor.fetchall():
                            key = row[0].strip() if row[0] else row[0]
                            desc = (row[1].strip() if row[1] else '') or ''
                            fmt = (row[2].strip() if row[2] else '') or ''
                            if desc and desc != key:
                                desc_map[key] = {'descripcion': desc, 'formato': fmt}
                    except Exception:
                        pass

                for a in articulos:
                    if a['codigo'] in desc_map:
                        a['descripcion'] = desc_map[a['codigo']]['descripcion']
                        a['formato'] = desc_map[a['codigo']].get('formato', '')

            return articulos
        except Exception as e:
            print(f"Error en get_articulos_mas_vistos: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_actividad_por_dia(empresa_id='1', dias=30):
        """
        Obtiene logins exitosos, fallidos y usuarios unicos por dia.
        Excluye administradores y superusuarios.
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    CAST(a.fecha AS DATE) as dia,
                    SUM(CASE WHEN a.accion='LOGIN' AND a.resultado='SUCCESS' THEN 1 ELSE 0 END) as logins,
                    SUM(CASE WHEN a.accion='LOGIN_FAILED' THEN 1 ELSE 0 END) as logins_fallidos,
                    COUNT(DISTINCT CASE WHEN a.resultado='SUCCESS' THEN a.user_id END) as usuarios_unicos
                FROM audit_log a
                LEFT JOIN users u ON a.user_id = u.id
                LEFT JOIN users_empresas ue ON u.id = ue.user_id AND ue.empresa_id = ?
                WHERE a.empresa_id = ? AND a.fecha >= DATEADD(DAY, ?, GETDATE())
                    AND (u.id IS NULL OR ISNULL(ue.rol, u.rol) NOT IN ('administrador', 'superusuario'))
                GROUP BY CAST(a.fecha AS DATE)
                ORDER BY dia ASC
            """, (empresa_id, empresa_id, -dias))

            resultado = []
            for row in cursor.fetchall():
                resultado.append({
                    'fecha': row[0].isoformat() if row[0] else None,
                    'logins': row[1],
                    'logins_fallidos': row[2],
                    'usuarios_unicos': row[3]
                })
            return resultado
        except Exception as e:
            print(f"Error en get_actividad_por_dia: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_acciones_distribucion(empresa_id='1', dias=30):
        """
        Obtiene la distribucion de acciones (top 10 tipos).
        Excluye administradores y superusuarios.
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT TOP 10 a.accion, COUNT(*) as total
                FROM audit_log a
                LEFT JOIN users u ON a.user_id = u.id
                LEFT JOIN users_empresas ue ON u.id = ue.user_id AND ue.empresa_id = ?
                WHERE a.empresa_id = ? AND a.fecha >= DATEADD(DAY, ?, GETDATE())
                    AND (u.id IS NULL OR ISNULL(ue.rol, u.rol) NOT IN ('administrador', 'superusuario'))
                GROUP BY a.accion
                ORDER BY total DESC
            """, (empresa_id, empresa_id, -dias))

            resultado = []
            for row in cursor.fetchall():
                resultado.append({
                    'accion': row[0],
                    'total': row[1]
                })
            return resultado
        except Exception as e:
            print(f"Error en get_acciones_distribucion: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_actividad_por_hora(empresa_id='1', dias=30):
        """
        Obtiene actividad agrupada por hora del dia (0-23).
        Excluye administradores y superusuarios.
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT DATEPART(HOUR, a.fecha) as hora, COUNT(*) as total
                FROM audit_log a
                LEFT JOIN users u ON a.user_id = u.id
                LEFT JOIN users_empresas ue ON u.id = ue.user_id AND ue.empresa_id = ?
                WHERE a.empresa_id = ? AND a.fecha >= DATEADD(DAY, ?, GETDATE())
                    AND (u.id IS NULL OR ISNULL(ue.rol, u.rol) NOT IN ('administrador', 'superusuario'))
                GROUP BY DATEPART(HOUR, a.fecha)
                ORDER BY hora ASC
            """, (empresa_id, empresa_id, -dias))

            resultado = []
            for row in cursor.fetchall():
                resultado.append({
                    'hora': row[0],
                    'total': row[1]
                })
            return resultado
        except Exception as e:
            print(f"Error en get_actividad_por_hora: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_usuarios_mas_interaccion(empresa_id='1', limit=10, dias=30):
        """
        Obtiene top usuarios por total de acciones.
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT TOP (?)
                    a.username,
                    u.full_name,
                    COUNT(*) as total_acciones,
                    COUNT(DISTINCT CAST(a.fecha AS DATE)) as dias_activo,
                    MAX(a.fecha) as ultima_accion
                FROM audit_log a
                INNER JOIN users u ON a.user_id = u.id
                INNER JOIN users_empresas ue ON u.id = ue.user_id AND ue.empresa_id = ?
                WHERE a.empresa_id = ?
                    AND a.fecha >= DATEADD(DAY, ?, GETDATE())
                    AND ISNULL(ue.rol, u.rol) = 'usuario'
                GROUP BY a.username, u.full_name
                ORDER BY total_acciones DESC
            """, (limit, empresa_id, empresa_id, -dias))

            usuarios = []
            for row in cursor.fetchall():
                usuarios.append({
                    'username': row[0],
                    'full_name': row[1],
                    'total_acciones': row[2],
                    'dias_activo': row[3],
                    'ultima_accion': row[4].isoformat() if row[4] else None
                })
            return usuarios
        except Exception as e:
            print(f"Error en get_usuarios_mas_interaccion: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_logins_por_ubicacion(empresa_id='1', dias=30):
        """
        Obtiene logins agrupados por ubicacion geografica.
        Parsea JSON de detalles en Python (SQL Server 2008 no soporta JSON nativo).
        Filtra IPs locales/privadas (pais_codigo='LO').
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT a.detalles, a.username
                FROM audit_log a
                WHERE a.empresa_id = ?
                    AND a.accion = 'LOGIN'
                    AND a.resultado = 'SUCCESS'
                    AND a.fecha >= DATEADD(DAY, ?, GETDATE())
                    AND a.detalles IS NOT NULL
            """, (empresa_id, -dias))

            # Agrupar por ubicacion redondeada
            ubicaciones = {}
            for row in cursor.fetchall():
                try:
                    detalles = json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    continue

                # La ubicacion esta anidada bajo 'ubicacion' en el JSON de detalles
                ub_data = detalles.get('ubicacion', {})
                if not ub_data:
                    continue

                # Filtrar IPs locales/privadas
                if ub_data.get('pais_codigo') == 'LO':
                    continue

                lat = ub_data.get('lat')
                lon = ub_data.get('lon')
                if lat is None or lon is None:
                    continue

                # Redondear a 2 decimales para agrupar ubicaciones cercanas
                lat_r = round(float(lat), 2)
                lon_r = round(float(lon), 2)
                key = f"{lat_r},{lon_r}"

                username = row[1]

                if key not in ubicaciones:
                    ubicaciones[key] = {
                        'lat': lat_r,
                        'lon': lon_r,
                        'pais': ub_data.get('pais', ''),
                        'ciudad': ub_data.get('ciudad', ''),
                        'total_logins': 0,
                        'usuarios': set()
                    }

                ubicaciones[key]['total_logins'] += 1
                ubicaciones[key]['usuarios'].add(username)

            # Convertir sets a listas para JSON
            resultado = []
            for ub in ubicaciones.values():
                resultado.append({
                    'lat': ub['lat'],
                    'lon': ub['lon'],
                    'pais': ub['pais'],
                    'ciudad': ub['ciudad'],
                    'total_logins': ub['total_logins'],
                    'usuarios': sorted(list(ub['usuarios']))
                })

            return resultado
        except Exception as e:
            print(f"Error en get_logins_por_ubicacion: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_consultas_por_estado(empresa_id='1'):
        """
        Obtiene el conteo de consultas por estado.

        Args:
            empresa_id: ID de la empresa

        Returns:
            dict: Conteo por estado
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM consultas
            WHERE empresa_id = ?
            GROUP BY estado
        """, (empresa_id,))

        estados = {}
        for row in cursor.fetchall():
            estados[row[0]] = row[1]

        conn.close()
        return estados
