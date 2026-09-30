"""Configuración de la aplicación; conserva ADMIN_CODIGN por compatibilidad."""

import hashlib
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent


def load_config() -> dict:
    """Carga el .env del paquete sin sobrescribir variables del entorno."""
    load_dotenv(BASE_DIR / '.env')
    coding_secret = os.getenv('ADMIN_CODIGN', 'changeme')
    return {
        'SECRET_KEY': os.getenv('FLASK_SECRET') or secrets.token_hex(32),
        'ADMIN_NAME': os.getenv('ADMIN_NAME', 'admin'),
        'ADMIN_PASSWORD': os.getenv('ADMIN_PASSWORD', 'changeme'),
        # Mantener esta derivación permite leer los datos ya existentes.
        'NACL_KEY': hashlib.sha256(coding_secret.encode('utf-8')).digest(),
        'DATA_FILE': os.getenv('DATA_FILE') or str(BASE_DIR / 'Data_P.json'),
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'MAX_CONTENT_LENGTH': 5 * 1024 * 1024,
    }
