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
                    email_to
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

                config = {
                    'id': row[0],
                    'nombre_configuracion': row[1],
                    'smtp_server': row[2],
                    'smtp_port': row[3],
                    'email_from': row[4],
                    'email_password': row[5],
                    'email_to': row[6]
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
        """Obtiene una configuración de email por ID y empresa (incluye contraseña)"""
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
                    activo
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
                    'activo': bool(row[7])
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
                    fecha_modificacion
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
                    'fecha_modificacion': row[8].strftime('%Y-%m-%d %H:%M:%S') if row[8] else None
                })

            conn.close()
            print(f"✅ Se encontraron {len(configs)} configuraciones")
            return configs

        except Exception as e:
            print(f"❌ Error al obtener todas las configuraciones: {str(e)}")
            traceback.print_exc()
            return []

    @staticmethod
    def update_config(id, nombre_configuracion, smtp_server, smtp_port, email_from, email_password, email_to, empresa_id):
        """Actualiza una configuración de email"""
        try:
            print(f"\n🔧 Actualizando configuración ID: {id} (Empresa: {empresa_id})...")
            conn = Database.get_connection()
            cursor = conn.cursor()

            # Si email_password está vacío o es None, no actualizamos la contraseña
            if email_password and email_password.strip() and email_password != '********':
                cursor.execute("""
                    UPDATE email_config
                    SET
                        nombre_configuracion = ?,
                        smtp_server = ?,
                        smtp_port = ?,
                        email_from = ?,
                        email_password = ?,
                        email_to = ?,
                        fecha_modificacion = GETDATE()
                    WHERE id = ? AND empresa_id = ?
                """, (nombre_configuracion, smtp_server, smtp_port, email_from, email_password, email_to, id, empresa_id))
            else:
                # Actualizar sin cambiar la contraseña
                cursor.execute("""
                    UPDATE email_config
                    SET
                        nombre_configuracion = ?,
                        smtp_server = ?,
                        smtp_port = ?,
                        email_from = ?,
                        email_to = ?,
                        fecha_modificacion = GETDATE()
                    WHERE id = ? AND empresa_id = ?
                """, (nombre_configuracion, smtp_server, smtp_port, email_from, email_to, id, empresa_id))

            conn.commit()
            conn.close()
            print(f"✅ Configuración ID {id} actualizada correctamente")
            return True

        except Exception as e:
            print(f"❌ Error al actualizar configuración: {str(e)}")
            traceback.print_exc()
            return False

    @staticmethod
    def create_config(nombre_configuracion, smtp_server, smtp_port, email_from, email_password, email_to, empresa_id):
        """Crea una nueva configuración de email para una empresa"""
        try:
            print(f"\n➕ Creando nueva configuración: {nombre_configuracion} (Empresa: {empresa_id})...")
            conn = Database.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO email_config
                    (nombre_configuracion, smtp_server, smtp_port, email_from, email_password, email_to, activo, empresa_id, fecha_creacion)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, GETDATE())
            """, (nombre_configuracion, smtp_server, smtp_port, email_from, email_password, email_to, empresa_id))

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
