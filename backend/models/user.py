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

# models/user.py
from flask_login import UserMixin

# Constantes de roles
ROLES = {
    'usuario': 1,
    'administrador': 2,
    'superusuario': 3
}

class User(UserMixin):
    def __init__(self, id, username, email=None, full_name=None, rol='usuario', empresa_id='1', cliente_id=None, debe_cambiar_password=False, company_name=None):
        self.id = id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.rol = rol
        self.empresa_id = empresa_id
        self.cliente_id = cliente_id
        self.debe_cambiar_password = debe_cambiar_password
        self.company_name = company_name

    def get_id(self):
        return str(self.id)

    def is_usuario(self):
        """Verifica si el usuario tiene rol de usuario (o superior)"""
        return self.rol in ['usuario', 'administrador', 'superusuario']

    def is_administrador(self):
        """Verifica si el usuario tiene rol de administrador (o superior)"""
        return self.rol in ['administrador', 'superusuario']

    def is_superusuario(self):
        """Verifica si el usuario tiene rol de superusuario"""
        return self.rol == 'superusuario'

    def has_role(self, rol_requerido):
        """Verifica si el usuario tiene al menos el rol requerido"""
        nivel_usuario = ROLES.get(self.rol, 0)
        nivel_requerido = ROLES.get(rol_requerido, 0)
        return nivel_usuario >= nivel_requerido

    def to_dict(self):
        """Convierte el usuario a diccionario (para APIs)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'rol': self.rol,
            'empresa_id': self.empresa_id,
            'cliente_id': self.cliente_id,
            'company_name': self.company_name
        }