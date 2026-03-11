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
# ARCHIVO: models/email_config_model.py
# ============================================
from config.database import Database
import traceback

class EmailConfigModel:
    @staticmethod
    def get_active_config(empresa_id, connection=None):
        """Obtiene la configuración de email activa para una empresa"""
        try:
            print("\n" + "=" * 60)
            print(f"🔍 OBTENIENDO CONFIGURACIÓN DE EMAIL (Empresa: {empresa_id}, Connection: {connection})")
            print("=" * 60)

            # Establecer conexión
            print("📡 Conectando a la base de datos...")
            conn = Database.get_connection(connection)
            print("✅ Conexión establecida correctamente")

            cursor = conn.cursor()

            # Ejecutar consulta
            print("📊 Ejecutando consulta SQL...")
            sql = """
                SELECT
                    id,
                    nombre_configuracion,
                    smtp_server,
                    smtp_port,
                    email_from,
                    email_password,
                    email_to,
                    ISNULL(auth_method, 'basic'),
                    oauth2_tenant_id,
                    oauth2_client_id,
                    oauth2_client_secret
                FROM email_config
                WHERE activo = 1 AND empresa_id = ?
            """
            cursor.execute(sql, (empresa_id,))
            print("✅ Consulta ejecutada")

            # Obtener resultado
            row = cursor.fetchone()

            if row:
                print(f"✅ Registro encontrado:")
                print(f"   - ID: {row[0]}")
                print(f"   - Nombre: {row[1]}")
                print(f"   - SMTP Server: {row[2]}")
                print(f"   - SMTP Port: {row[3]}")
                print(f"   - Email From: {row[4]}")
                print(f"   - Email To: {row[6]}")
                print(f"   - Auth Method: {row[7]}")

                config = {
                    'id': row[0],
                    'nombre_configuracion': row[1],
                    'smtp_server': row[2],
                    'smtp_port': row[3],
                    'email_from': row[4],
                    'email_password': row[5],
                    'email_to': row[6],
                    'auth_method': row[7],
                    'oauth2_tenant_id': row[8],
                    'oauth2_client_id': row[9],
                    'oauth2_client_secret': row[10]
                }

                conn.close()
                print("✅ Configuración cargada exitosamente")
                print("=" * 60 + "\n")
                return config
            else:
                print("❌ NO SE ENCONTRÓ NINGUNA CONFIGURACIÓN ACTIVA")
                print(f"   Verifica que exista un registro con activo = 1 para empresa_id = {empresa_id}")
                conn.close()
                print("=" * 60 + "\n")
                return None

        except Exception as e:
            print("\n" + "=" * 60)
            print("❌ ERROR AL OBTENER CONFIGURACIÓN DE EMAIL")
            print("=" * 60)
            print(f"Error: {str(e)}")
            print("\nTraceback completo:")
            traceback.print_exc()
            print("=" * 60 + "\n")
            return None

    @staticmethod
    def get_config_by_id(config_id, empresa_id):
        """Obtiene una configuración de email por ID y empresa (incluye contraseña y OAuth2)"""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    nombre_configuracion,
                    smtp_server,
                    smtp_port,
                    email_from,
                    email_password,
                    email_to,
                    activo,
                    ISNULL(auth_method, 'basic'),
                    oauth2_tenant_id,
                    oauth2_client_id,
                    oauth2_client_secret
                FROM email_config
                WHERE id = ? AND empresa_id = ?
            """, (config_id, empresa_id))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'nombre_configuracion': row[1],
                    'smtp_server': row[2],
                    'smtp_port': row[3],
                    'email_from': row[4],
                    'email_password': row[5],
                    'email_to': row[6],
                    'activo': bool(row[7]),
                    'auth_method': row[8],
                    'oauth2_tenant_id': row[9],
                    'oauth2_client_id': row[10],
                    'oauth2_client_secret': row[11]
                }
            return None

        except Exception as e:
            print(f"❌ Error al obtener configuración por ID: {str(e)}")
            traceback.print_exc()
            return None

    @staticmethod
    def get_all_configs(empresa_id):
        """Obtiene todas las configuraciones de email de una empresa"""
        try:
            print(f"\n🔍 Obteniendo configuraciones de email (Empresa: {empresa_id})...")
            conn = Database.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    nombre_configuracion,
                    smtp_server,
                    smtp_port,
                    email_from,
                    email_to,
                    activo,
                    fecha_creacion,
                    fecha_modificacion,
                    ISNULL(auth_method, 'basic'),
                    oauth2_tenant_id,
                    oauth2_client_id
                FROM email_config
                WHERE empresa_id = ?
                ORDER BY id
            """, (empresa_id,))

            configs = []
            for row in cursor.fetchall():
                configs.append({
                    'id': row[0],
                    'nombre_configuracion': row[1],
                    'smtp_server': row[2],
                    'smtp_port': row[3],
                    'email_from': row[4],
                    'email_to': row[5],
                    'activo': bool(row[6]),
                    'fecha_creacion': row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
                    'fecha_modificacion': row[8].strftime('%Y-%m-%d %H:%M:%S') if row[8] else None,
                    'auth_method': row[9],
                    'oauth2_tenant_id': row[10],
                    'oauth2_client_id': row[11]
                })

            conn.close()
            print(f"✅ Se encontraron {len(configs)} configuraciones")
            return configs

        except Exception as e:
            print(f"❌ Error al obtener todas las configuraciones: {str(e)}")
            traceback.print_exc()
            return []

    @staticmethod
    def update_config(id, nombre_configuracion, smtp_server, smtp_port, email_from, email_password, email_to, empresa_id, auth_method=None, oauth2_tenant_id=None, oauth2_client_id=None, oauth2_client_secret=None):
        """Actualiza una configuración de email"""
        try:
            print(f"\n🔧 Actualizando configuración ID: {id} (Empresa: {empresa_id})...")
            conn = Database.get_connection()
            cursor = conn.cursor()

            # Construir SET dinámico
            set_parts = [
                "nombre_configuracion = ?",
                "smtp_server = ?",
                "smtp_port = ?",
                "email_from = ?",
                "email_to = ?",
                "fecha_modificacion = GETDATE()"
            ]
            params = [nombre_configuracion, smtp_server, smtp_port, email_from, email_to]

            # Contraseña solo si se proporciona
            if email_password and email_password.strip() and email_password != '********':
                set_parts.insert(4, "email_password = ?")
                params.insert(4, email_password)

            # auth_method
            if auth_method is not None:
                set_parts.append("auth_method = ?")
                params.append(auth_method)

            # Campos OAuth2
            if oauth2_tenant_id is not None:
                set_parts.append("oauth2_tenant_id = ?")
                params.append(oauth2_tenant_id if oauth2_tenant_id else None)

            if oauth2_client_id is not None:
                set_parts.append("oauth2_client_id = ?")
                params.append(oauth2_client_id if oauth2_client_id else None)

            if oauth2_client_secret is not None and oauth2_client_secret != '********':
                set_parts.append("oauth2_client_secret = ?")
                params.append(oauth2_client_secret if oauth2_client_secret else None)

            params.extend([id, empresa_id])

            sql = f"UPDATE email_config SET {', '.join(set_parts)} WHERE id = ? AND empresa_id = ?"
            cursor.execute(sql, tuple(params))

            conn.commit()
            conn.close()
            print(f"✅ Configuración ID {id} actualizada correctamente")
            return True

        except Exception as e:
            print(f"❌ Error al actualizar configuración: {str(e)}")
            traceback.print_exc()
            return False

    @staticmethod
    def create_config(nombre_configuracion, smtp_server, smtp_port, email_from, email_password, email_to, empresa_id, auth_method='basic', oauth2_tenant_id=None, oauth2_client_id=None, oauth2_client_secret=None):
        """Crea una nueva configuración de email para una empresa"""
        try:
            print(f"\n➕ Creando nueva configuración: {nombre_configuracion} (Empresa: {empresa_id})...")
            conn = Database.get_connection()
            cursor = conn.cursor()

            # email_password no puede ser NULL en BD - usar string vacío para OAuth2
            if not email_password:
                email_password = ''

            cursor.execute("""
                INSERT INTO email_config
                    (nombre_configuracion, smtp_server, smtp_port, email_from, email_password, email_to, activo, empresa_id, fecha_creacion, auth_method, oauth2_tenant_id, oauth2_client_id, oauth2_client_secret)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, GETDATE(), ?, ?, ?, ?)
            """, (nombre_configuracion, smtp_server, smtp_port, email_from, email_password, email_to, empresa_id, auth_method, oauth2_tenant_id, oauth2_client_id, oauth2_client_secret))

            row = cursor.fetchone()
            new_id = row[0] if row else None

            conn.commit()
            conn.close()
            print(f"✅ Configuración creada con ID: {new_id}")
            return new_id

        except Exception as e:
            print(f"❌ Error al crear configuración: {str(e)}")
            traceback.print_exc()
            return None

    @staticmethod
    def delete_config(id, empresa_id):
        """Elimina una configuración de email (solo si no está activa)"""
        try:
            print(f"\n🗑️ Eliminando configuración ID: {id} (Empresa: {empresa_id})...")
            conn = Database.get_connection()
            cursor = conn.cursor()

            # Verificar que no esté activa
            cursor.execute("SELECT activo FROM email_config WHERE id = ? AND empresa_id = ?", (id, empresa_id))
            row = cursor.fetchone()
            if not row:
                conn.close()
                raise Exception("Configuración no encontrada")
            if bool(row[0]):
                conn.close()
                raise Exception("No se puede eliminar la configuración activa")

            cursor.execute("DELETE FROM email_config WHERE id = ? AND empresa_id = ?", (id, empresa_id))
            conn.commit()
            conn.close()
            print(f"✅ Configuración ID {id} eliminada correctamente")
            return True

        except Exception as e:
            print(f"❌ Error al eliminar configuración: {str(e)}")
            traceback.print_exc()
            raise

    @staticmethod
    def set_active(id, empresa_id):
        """Establece una configuración como activa (desactiva las demás de la misma empresa)"""
        try:
            print(f"\n🔄 Activando configuración ID: {id} (Empresa: {empresa_id})...")
            conn = Database.get_connection()
            cursor = conn.cursor()

            # Desactivar todas las de la misma empresa
            cursor.execute("UPDATE email_config SET activo = 0 WHERE empresa_id = ?", (empresa_id,))
            print(f"  - Todas las configuraciones de empresa {empresa_id} desactivadas")

            # Activar la seleccionada
            cursor.execute("UPDATE email_config SET activo = 1 WHERE id = ? AND empresa_id = ?", (id, empresa_id))
            print(f"  - Configuración ID {id} activada")

            conn.commit()
            conn.close()
            print(f"✅ Configuración ID {id} establecida como activa")
            return True

        except Exception as e:
            print(f"❌ Error al activar configuración: {str(e)}")
            traceback.print_exc()
            return False

