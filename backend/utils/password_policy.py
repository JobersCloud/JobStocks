"""
Politica de contraseñas - Validacion de complejidad
"""
import re


# Reglas de la politica de contraseñas
PASSWORD_POLICY = {
    'min_length': 8,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_number': True,
    'require_special': True,
    'expiration_days': 90  # 0 = sin expiración
}


def validate_password(password):
    """
    Valida una contraseña contra la politica de complejidad.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
        Cada error es un codigo: 'min_length', 'require_uppercase', etc.
    """
    policy = PASSWORD_POLICY
    errors = []

    if len(password) < policy['min_length']:
        errors.append('min_length')

    if policy['require_uppercase'] and not re.search(r'[A-Z]', password):
        errors.append('require_uppercase')

    if policy['require_lowercase'] and not re.search(r'[a-z]', password):
        errors.append('require_lowercase')

    if policy['require_number'] and not re.search(r'[0-9]', password):
        errors.append('require_number')

    if policy['require_special'] and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?~`]', password):
        errors.append('require_special')

    return len(errors) == 0, errors


def get_policy_info():
    """
    Retorna la politica actual para enviar al frontend.
    """
    return {
        'min_length': PASSWORD_POLICY['min_length'],
        'require_uppercase': PASSWORD_POLICY['require_uppercase'],
        'require_lowercase': PASSWORD_POLICY['require_lowercase'],
        'require_number': PASSWORD_POLICY['require_number'],
        'require_special': PASSWORD_POLICY['require_special'],
        'expiration_days': PASSWORD_POLICY['expiration_days']
    }


def get_password_error_message(errors, lang='es'):
    """
    Genera mensaje de error legible a partir de los codigos de error.
    """
    messages = {
        'es': {
            'min_length': f'Mínimo {PASSWORD_POLICY["min_length"]} caracteres',
            'require_uppercase': 'Al menos una letra mayúscula',
            'require_lowercase': 'Al menos una letra minúscula',
            'require_number': 'Al menos un número',
            'require_special': 'Al menos un carácter especial (!@#$%...)'
        },
        'en': {
            'min_length': f'Minimum {PASSWORD_POLICY["min_length"]} characters',
            'require_uppercase': 'At least one uppercase letter',
            'require_lowercase': 'At least one lowercase letter',
            'require_number': 'At least one number',
            'require_special': 'At least one special character (!@#$%...)'
        },
        'fr': {
            'min_length': f'Minimum {PASSWORD_POLICY["min_length"]} caractères',
            'require_uppercase': 'Au moins une lettre majuscule',
            'require_lowercase': 'Au moins une lettre minuscule',
            'require_number': 'Au moins un chiffre',
            'require_special': 'Au moins un caractère spécial (!@#$%...)'
        }
    }

    msgs = messages.get(lang, messages['es'])
    error_texts = [msgs[e] for e in errors if e in msgs]
    return '. '.join(error_texts)
