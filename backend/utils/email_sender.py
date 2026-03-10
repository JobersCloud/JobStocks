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
# Fecha : 2026-03-10
# ============================================================

"""
Utilidad central de envío de email.

Soporta dos métodos de autenticación:
  - 'basic': SMTP login con usuario/contraseña (comportamiento clásico)
  - 'oauth2': XOAUTH2 con Microsoft OAuth2 (Office 365)

Uso:
    from utils.email_sender import smtp_send_message
    smtp_send_message(email_config, msg)
"""

import smtplib
import base64
import traceback


def _build_xoauth2_string(user, access_token):
    """Construye la cadena XOAUTH2 para autenticación SMTP.

    Formato: user=<user>\\x01auth=Bearer <token>\\x01\\x01
    """
    auth_string = f"user={user}\x01auth=Bearer {access_token}\x01\x01"
    return auth_string


def _get_oauth2_access_token(email_config):
    """Obtiene un access_token usando MSAL con client_credentials (Application permissions).

    Usa el flujo 'acquire_token_for_client' de MSAL ConfidentialClientApplication.
    Este flujo no requiere interacción del usuario ni refresh_token.
    """
    try:
        import msal
    except ImportError:
        raise Exception("El paquete 'msal' es necesario para OAuth2. Instálalo con: pip install msal")

    tenant_id = email_config.get('oauth2_tenant_id')
    client_id = email_config.get('oauth2_client_id')
    client_secret = email_config.get('oauth2_client_secret')

    if not all([tenant_id, client_id, client_secret]):
        raise Exception("Faltan datos OAuth2 en la configuración de email (tenant_id, client_id, client_secret)")

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scopes = ["https://outlook.office365.com/.default"]

    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret
    )

    result = app.acquire_token_for_client(scopes=scopes)

    if "access_token" not in result:
        error_desc = result.get("error_description", result.get("error", "Error desconocido"))
        raise Exception(f"Error al obtener access_token OAuth2: {error_desc}")

    return result["access_token"]


def smtp_send_message(email_config, msg):
    """Envía un email usando la configuración proporcionada.

    Args:
        email_config (dict): Configuración de email con campos:
            - smtp_server, smtp_port, email_from, email_password (para basic)
            - auth_method ('basic' o 'oauth2')
            - oauth2_tenant_id, oauth2_client_id, oauth2_client_secret (para oauth2)
        msg (email.message.Message): Mensaje MIME ya construido.

    Raises:
        Exception: Si hay error de conexión, autenticación o envío.
    """
    auth_method = email_config.get('auth_method', 'basic')
    smtp_server = email_config['smtp_server']
    smtp_port = email_config['smtp_port']
    email_from = email_config['email_from']

    print(f"📧 Conectando a SMTP {smtp_server}:{smtp_port} (auth: {auth_method})")

    # Crear conexión SMTP
    if smtp_port == 465:
        print("   Usando SMTP_SSL (puerto 465)")
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
    else:
        print(f"   Usando SMTP con STARTTLS (puerto {smtp_port})")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()

    try:
        if auth_method == 'oauth2':
            # Autenticación XOAUTH2
            print("   Obteniendo access_token OAuth2...")
            access_token = _get_oauth2_access_token(email_config)
            auth_string = _build_xoauth2_string(email_from, access_token)
            print("   Autenticando con XOAUTH2...")
            server.auth('XOAUTH2', lambda: auth_string)
            print("   ✅ Autenticación XOAUTH2 exitosa")
        else:
            # Autenticación básica
            print("   Autenticando con usuario/contraseña...")
            server.login(email_from, email_config['email_password'])
            print("   ✅ Autenticación básica exitosa")

        # Enviar mensaje
        print("   Enviando mensaje...")
        server.send_message(msg)
        print("   ✅ Mensaje enviado correctamente")

    finally:
        try:
            server.quit()
        except Exception:
            pass


def test_smtp_connection(email_config):
    """Prueba la conexión SMTP sin enviar email.

    Args:
        email_config (dict): Mismos campos que smtp_send_message.

    Returns:
        dict: {'success': True/False, 'message': str, 'error': str (si aplica)}
    """
    auth_method = email_config.get('auth_method', 'basic')
    smtp_server = email_config.get('smtp_server')
    smtp_port = int(email_config.get('smtp_port', 587))
    email_from = email_config.get('email_from')

    try:
        # Crear conexión
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()

        try:
            if auth_method == 'oauth2':
                access_token = _get_oauth2_access_token(email_config)
                auth_string = _build_xoauth2_string(email_from, access_token)
                server.auth('XOAUTH2', lambda: auth_string)
            else:
                server.login(email_from, email_config.get('email_password', ''))
        finally:
            try:
                server.quit()
            except Exception:
                pass

        return {'success': True, 'message': 'Conexión SMTP exitosa'}

    except smtplib.SMTPAuthenticationError as e:
        error_detail = str(e)
        if auth_method == 'oauth2':
            error_msg = f"Error de autenticación OAuth2 SMTP: {error_detail}"
        elif "gmail" in (smtp_server or '').lower():
            error_msg = f"Error de autenticación. Si usas Gmail con verificación en 2 pasos, necesitas una 'Contraseña de aplicación'. Detalle: {error_detail}"
        else:
            error_msg = f"Error de autenticación: {error_detail}"
        return {'success': False, 'error': error_msg}
    except smtplib.SMTPConnectError:
        return {'success': False, 'error': f"No se pudo conectar al servidor SMTP: {smtp_server}:{smtp_port}"}
    except Exception as e:
        error_str = str(e)
        if "getaddrinfo failed" in error_str or "Name or service not known" in error_str:
            return {'success': False, 'error': f"Servidor '{smtp_server}' no encontrado. Verifica el nombre del servidor."}
        if "Connection refused" in error_str:
            return {'success': False, 'error': f"Conexión rechazada en {smtp_server}:{smtp_port}. Verifica el puerto."}
        if "timed out" in error_str.lower() or "timeout" in error_str.lower():
            return {'success': False, 'error': f"Timeout: El servidor {smtp_server}:{smtp_port} no responde."}
        return {'success': False, 'error': error_str}
