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

# database/users_db.py
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import Database


def verify_user(username, password, empresa_cli_id, empresa_erp=None):
    """
    Verificar credenciales de usuario.

    Args:
        username: Nombre de usuario
        password: Contraseña
        empresa_cli_id: ID para conexión a BD
        empresa_erp: Código para filtrar (opcional, se obtiene de sesión si no se pasa)
    """
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        # Obtener usuario básico
        cursor.execute("""
            SELECT id, username, password_hash, email, full_name, active, debe_cambiar_password, company_name
            FROM users
            WHERE username = ? AND active = 1
        """, (username,))

        row = cursor.fetchone()

        if not row:
            return None

        user = {
            'id': row[0],
            'username': row[1],
            'password_hash': row[2],
            'email': row[3],
            'full_name': row[4],
            'active': row[5],
            'debe_cambiar_password': bool(row[6]) if row[6] is not None else False,
            'company_name': row[7],
            'rol': 'usuario',
            'empresa_cli_id': empresa_cli_id,
            'empresa_erp': empresa_erp,
            'cliente_id': None
        }

        # Verificar contraseña
        if not check_password_hash(user['password_hash'], password):
            return None

        # Obtener fecha_ultimo_cambio_password (puede no existir la columna)
        try:
            cursor.execute("SELECT fecha_ultimo_cambio_password FROM users WHERE id = ?", (user['id'],))
            pwd_row = cursor.fetchone()
            user['fecha_ultimo_cambio_password'] = pwd_row[0] if pwd_row else None
        except Exception:
            user['fecha_ultimo_cambio_password'] = None

        # Obtener datos de empresa si se proporciona empresa_erp
        if empresa_erp:
            cursor.execute("""
                SELECT empresa_id, cliente_id, rol
                FROM users_empresas
                WHERE user_id = ? AND empresa_id = ?
            """, (user['id'], empresa_erp))

            emp_row = cursor.fetchone()
            if emp_row:
                user['empresa_erp'] = emp_row[0]
                user['cliente_id'] = emp_row[1]
                user['rol'] = emp_row[2] or 'usuario'

        return user
    except Exception as e:
        print(f"[ERROR] verify_user: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_user_by_id(user_id, empresa_cli_id, empresa_erp=None):
    """
    Obtener usuario por ID.

    Args:
        user_id: ID del usuario
        empresa_cli_id: ID para conexión a BD
        empresa_erp: Código para filtrar (opcional)
    """
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, email, full_name, active, debe_cambiar_password, company_name
            FROM users
            WHERE id = ? AND active = 1
        """, (user_id,))

        row = cursor.fetchone()

        if not row:
            return None

        user = {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'full_name': row[3],
            'active': row[4],
            'debe_cambiar_password': bool(row[5]) if row[5] is not None else False,
            'company_name': row[6],
            'rol': 'usuario',
            'empresa_cli_id': empresa_cli_id,
            'empresa_erp': empresa_erp,
            'cliente_id': None
        }

        # Obtener datos de empresa si se proporciona empresa_erp
        if empresa_erp:
            cursor.execute("""
                SELECT empresa_id, cliente_id, rol
                FROM users_empresas
                WHERE user_id = ? AND empresa_id = ?
            """, (user_id, empresa_erp))

            emp_row = cursor.fetchone()
            if emp_row:
                user['empresa_erp'] = emp_row[0]
                user['cliente_id'] = emp_row[1]
                user['rol'] = emp_row[2] or 'usuario'

        return user
    except Exception as e:
        print(f"[ERROR] get_user_by_id: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_user_by_username(username, empresa_cli_id):
    """Obtener usuario por nombre de usuario"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, email, full_name
            FROM users
            WHERE username = ? AND active = 1
        """, (username,))

        row = cursor.fetchone()

        if row:
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3]
            }

        return None
    except Exception as e:
        print(f"[ERROR] get_user_by_username: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_all_users_by_empresa(empresa_erp, empresa_cli_id):
    """Obtener todos los usuarios de una empresa"""
    print(f"[DEBUG] get_all_users_by_empresa - empresa_erp: {empresa_erp}, empresa_cli_id: {empresa_cli_id}")
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)  # Usar connection explícita
        print(f"[DEBUG] get_all_users_by_empresa - Conexión obtenida")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                u.id, u.username, u.email, u.full_name, u.pais,
                ue.rol, u.active, u.email_verificado,
                u.created_at, u.updated_at,
                ue.empresa_id, ue.cliente_id, u.company_name
            FROM users u
            INNER JOIN users_empresas ue ON u.id = ue.user_id
            WHERE ue.empresa_id = ?
            ORDER BY u.created_at DESC
        """, (empresa_erp,))

        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3],
                'pais': row[4],
                'rol': row[5] or 'usuario',
                'active': row[6],
                'email_verificado': row[7],
                'created_at': row[8].isoformat() if row[8] else None,
                'updated_at': row[9].isoformat() if row[9] else None,
                'empresa_id': row[10],
                'cliente_id': row[11],
                'company_name': row[12]
            })

        return users
    except Exception as e:
        print(f"[ERROR] get_all_users_by_empresa: {e}")
        return []
    finally:
        if conn:
            conn.close()


def create_user_admin(data, empresa_cli_id):
    """Crear usuario manualmente por admin (sin verificación de email)"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        password_hash = generate_password_hash(data['password'])
        debe_cambiar = 1 if data.get('debe_cambiar_password', False) else 0

        # 1. Insertar en tabla users
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, full_name, pais,
                              active, email_verificado, debe_cambiar_password, company_name)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)
        """, (
            data['username'],
            password_hash,
            data.get('email'),
            data.get('full_name'),
            data.get('pais'),
            debe_cambiar,
            data.get('company_name')
        ))

        user_id = cursor.fetchone()[0]

        # 2. Insertar en tabla users_empresas (usa empresa_erp)
        cursor.execute("""
            INSERT INTO users_empresas (user_id, empresa_id, cliente_id, rol)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            data['empresa_erp'],  # empresa_erp para el filtro interno
            data.get('cliente_id'),
            data.get('rol', 'usuario')
        ))

        conn.commit()
        return int(user_id)
    except Exception as e:
        print(f"[ERROR] create_user_admin: {e}")
        if '2627' in str(e):
            raise ValueError(f"El usuario '{data['username']}' ya existe")
        raise
    finally:
        if conn:
            conn.close()


def add_user_to_empresa(user_id, empresa_cli_id, empresa_erp, cliente_id=None, rol='usuario'):
    """Añadir un usuario existente a una empresa"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users_empresas (user_id, empresa_id, cliente_id, rol)
            VALUES (?, ?, ?, ?)
        """, (user_id, empresa_erp, cliente_id, rol))

        conn.commit()
        return True
    except Exception as e:
        print(f"[ERROR] add_user_to_empresa: {e}")
        return False
    finally:
        if conn:
            conn.close()


def update_user_empresa(user_id, empresa_cli_id, empresa_erp, cliente_id=None, rol=None):
    """Actualizar datos de un usuario en una empresa específica"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        updates = []
        params = []

        if cliente_id is not None:
            updates.append("cliente_id = ?")
            params.append(cliente_id if cliente_id else None)

        if rol is not None:
            updates.append("rol = ?")
            params.append(rol)

        if not updates:
            return False

        params.extend([user_id, empresa_erp])
        query = f"UPDATE users_empresas SET {', '.join(updates)} WHERE user_id = ? AND empresa_id = ?"

        cursor.execute(query, params)
        rows_affected = cursor.rowcount
        conn.commit()

        return rows_affected > 0
    except Exception as e:
        print(f"[ERROR] update_user_empresa: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_user_empresas(user_id, empresa_cli_id):
    """Obtener todas las empresas de un usuario"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT empresa_id, cliente_id, rol, fecha_creacion
            FROM users_empresas
            WHERE user_id = ?
        """, (user_id,))

        empresas = []
        for row in cursor.fetchall():
            empresas.append({
                'empresa_id': row[0],
                'cliente_id': row[1],
                'rol': row[2],
                'fecha_creacion': row[3].isoformat() if row[3] else None
            })

        return empresas
    except Exception as e:
        print(f"[ERROR] get_user_empresas: {e}")
        return []
    finally:
        if conn:
            conn.close()


def update_user_full(user_id, data, empresa_cli_id, empresa_erp):
    """Actualización completa de usuario (solo admin)"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        # Verificar que el usuario pertenece a la empresa
        cursor.execute("""
            SELECT 1 FROM users_empresas
            WHERE user_id = ? AND empresa_id = ?
        """, (user_id, empresa_erp))

        if not cursor.fetchone():
            return False

        # Actualizar tabla users
        user_updates = []
        user_params = []

        if 'full_name' in data:
            user_updates.append("full_name = ?")
            user_params.append(data['full_name'])

        if 'email' in data:
            user_updates.append("email = ?")
            user_params.append(data['email'])

        if 'pais' in data:
            user_updates.append("pais = ?")
            user_params.append(data['pais'])

        if 'active' in data:
            user_updates.append("active = ?")
            user_params.append(1 if data['active'] else 0)

        if 'password' in data and data['password']:
            user_updates.append("password_hash = ?")
            user_params.append(generate_password_hash(data['password']))

        if 'company_name' in data:
            user_updates.append("company_name = ?")
            user_params.append(data['company_name'])

        if user_updates:
            user_params.append(user_id)
            query = f"UPDATE users SET {', '.join(user_updates)} WHERE id = ?"
            cursor.execute(query, user_params)

        # Actualizar tabla users_empresas
        emp_updates = []
        emp_params = []

        if 'cliente_id' in data:
            emp_updates.append("cliente_id = ?")
            emp_params.append(data['cliente_id'] if data['cliente_id'] else None)

        if 'rol' in data:
            emp_updates.append("rol = ?")
            emp_params.append(data['rol'])

        if emp_updates:
            emp_params.extend([user_id, empresa_erp])
            query = f"UPDATE users_empresas SET {', '.join(emp_updates)} WHERE user_id = ? AND empresa_id = ?"
            cursor.execute(query, emp_params)

        conn.commit()
        return True
    except Exception as e:
        print(f"[ERROR] update_user_full: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_user_by_id_and_empresa(user_id, empresa_cli_id, empresa_erp):
    """Obtener usuario por ID verificando empresa"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                u.id, u.username, u.email, u.full_name, u.pais,
                ue.rol, u.active, u.email_verificado,
                ue.empresa_id, ue.cliente_id, u.company_name
            FROM users u
            INNER JOIN users_empresas ue ON u.id = ue.user_id
            WHERE u.id = ? AND ue.empresa_id = ?
        """, (user_id, empresa_erp))

        row = cursor.fetchone()

        if row:
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3],
                'pais': row[4],
                'rol': row[5] or 'usuario',
                'active': row[6],
                'email_verificado': row[7],
                'empresa_id': row[8],
                'cliente_id': row[9],
                'company_name': row[10]
            }

        return None
    except Exception as e:
        print(f"[ERROR] get_user_by_id_and_empresa: {e}")
        return None
    finally:
        if conn:
            conn.close()


def update_user(user_id, data, empresa_cli_id):
    """Actualizar datos básicos de un usuario"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        updates = []
        params = []

        if 'full_name' in data:
            updates.append("full_name = ?")
            params.append(data['full_name'])

        if 'email' in data:
            updates.append("email = ?")
            params.append(data['email'])

        if 'pais' in data:
            updates.append("pais = ?")
            params.append(data['pais'])

        if 'active' in data:
            updates.append("active = ?")
            params.append(1 if data['active'] else 0)

        if not updates:
            return False

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(query, params)
        rows_affected = cursor.rowcount
        conn.commit()

        return rows_affected > 0
    except Exception as e:
        print(f"[ERROR] update_user: {e}")
        return False
    finally:
        if conn:
            conn.close()


def update_user_rol(user_id, rol, empresa_cli_id, empresa_erp):
    """Actualizar el rol de un usuario en una empresa específica"""
    if rol not in ['usuario', 'administrador', 'superusuario']:
        raise ValueError(f"Rol inválido: {rol}")

    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users_empresas
            SET rol = ?
            WHERE user_id = ? AND empresa_id = ?
        """, (rol, user_id, empresa_erp))

        rows_affected = cursor.rowcount
        conn.commit()

        return rows_affected > 0
    except Exception as e:
        print(f"[ERROR] update_user_rol: {e}")
        return False
    finally:
        if conn:
            conn.close()


def deactivate_user(user_id, empresa_cli_id):
    """Desactivar un usuario"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET active = 0 WHERE id = ?", (user_id,))
        rows_affected = cursor.rowcount
        conn.commit()

        return rows_affected > 0
    except Exception as e:
        print(f"[ERROR] deactivate_user: {e}")
        return False
    finally:
        if conn:
            conn.close()


def activate_user(user_id, empresa_cli_id):
    """Activar un usuario"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET active = 1 WHERE id = ?", (user_id,))
        rows_affected = cursor.rowcount
        conn.commit()

        return rows_affected > 0
    except Exception as e:
        print(f"[ERROR] activate_user: {e}")
        return False
    finally:
        if conn:
            conn.close()


def set_email_verified(user_id, verified, empresa_cli_id):
    """Cambiar el estado de verificación de email de un usuario"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET email_verificado = ? WHERE id = ?",
            (1 if verified else 0, user_id)
        )
        rows_affected = cursor.rowcount
        conn.commit()

        return rows_affected > 0
    except Exception as e:
        print(f"[ERROR] set_email_verified: {e}")
        return False
    finally:
        if conn:
            conn.close()


def change_password(user_id, new_password, empresa_cli_id):
    """Cambiar contraseña de un usuario y resetear flag debe_cambiar_password"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        password_hash = generate_password_hash(new_password)

        cursor.execute("""
            UPDATE users
            SET password_hash = ?, debe_cambiar_password = 0
            WHERE id = ?
        """, (password_hash, user_id))

        # Actualizar fecha_ultimo_cambio_password (puede no existir la columna)
        try:
            cursor.execute("""
                UPDATE users SET fecha_ultimo_cambio_password = GETDATE() WHERE id = ?
            """, (user_id,))
        except Exception:
            pass  # Columna no existe aún

        rows_affected = cursor.rowcount
        conn.commit()

        return rows_affected > 0
    except Exception as e:
        print(f"[ERROR] change_password: {e}")
        return False
    finally:
        if conn:
            conn.close()


def remove_user_from_empresa(user_id, empresa_cli_id, empresa_erp):
    """Eliminar un usuario de una empresa"""
    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM users_empresas
            WHERE user_id = ? AND empresa_id = ?
        """, (user_id, empresa_erp))

        rows_affected = cursor.rowcount
        conn.commit()

        return rows_affected > 0
    except Exception as e:
        print(f"[ERROR] remove_user_from_empresa: {e}")
        return False
    finally:
        if conn:
            conn.close()


def create_user(username, password, email=None, full_name=None, empresa_cli_id=None):
    """Crear un nuevo usuario (básico, sin empresa)"""
    if not empresa_cli_id:
        raise ValueError("Se requiere empresa_cli_id para crear usuario")

    conn = None
    try:
        conn = Database.get_connection(empresa_cli_id)
        cursor = conn.cursor()

        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users (username, password_hash, email, full_name)
            VALUES (?, ?, ?, ?)
        """, (username, password_hash, email, full_name))

        conn.commit()
        print(f"[OK] Usuario '{username}' creado exitosamente")
        return True
    except Exception as e:
        if '2627' in str(e):
            print(f"[ERROR] El usuario '{username}' ya existe")
        else:
            print(f"[ERROR] Error al crear usuario: {e}")
        return False
    finally:
        if conn:
            conn.close()
