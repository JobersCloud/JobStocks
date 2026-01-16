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

class EmailConfigModel:
    @staticmethod
    def get_active_config():
        """Obtiene la configuración de email activa"""
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
                email_to
            FROM email_config
            WHERE activo = 1
        """)
        
        row = cursor.fetchone()
        config = None
        
        if row:
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
        return config
    
    @staticmethod
    def get_all_configs():
        """Obtiene todas las configuraciones de email"""
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
            ORDER BY id
        """)
        
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
        return configs
    
    @staticmethod
    def update_config(id, smtp_server, smtp_port, email_from, email_password, email_to):
        """Actualiza una configuración de email"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE email_config
            SET 
                smtp_server = ?,
                smtp_port = ?,
                email_from = ?,
                email_password = ?,
                email_to = ?,
                fecha_modificacion = GETDATE()
            WHERE id = ?
        """, smtp_server, smtp_port, email_from, email_password, email_to, id)
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def set_active(id):
        """Establece una configuración como activa (desactiva las demás)"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        # Desactivar todas
        cursor.execute("UPDATE email_config SET activo = 0")
        
        # Activar la seleccionada
        cursor.execute("UPDATE email_config SET activo = 1 WHERE id = ?", id)
        
        conn.commit()
        conn.close()
        return True