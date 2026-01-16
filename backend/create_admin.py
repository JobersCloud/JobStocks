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

# create_admin.py
from database.users_db import create_user, init_users_db

# Inicializar base de datos
init_users_db()

# Crear usuario administrador
print("=" * 60)
print("CREAR USUARIO ADMINISTRADOR")
print("=" * 60)

username = input("Usuario: ")
password = input("Contraseña: ")
full_name = input("Nombre completo: ")
email = input("Email (opcional): ")

success = create_user(
    username=username,
    password=password,
    email=email if email else None,
    full_name=full_name if full_name else None
)

if success:
    print("\n✅ Usuario creado exitosamente!")
    print(f"   Usuario: {username}")
    print(f"   Nombre: {full_name}")
else:
    print("\n❌ Error al crear usuario")