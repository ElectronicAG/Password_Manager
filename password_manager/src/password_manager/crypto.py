"""Cifrado compatible con los registros SecretBox existentes."""

import base64
import binascii

from nacl.exceptions import CryptoError
from nacl.secret import SecretBox


class DecryptionError(ValueError):
    """El contenido está dañado o fue cifrado con otra clave."""


class PasswordCipher:
    def __init__(self, key: bytes) -> None:
        self._box = SecretBox(key)

    def encrypt(self, plaintext: str) -> str:
        encrypted = self._box.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted).decode('ascii')

    def decrypt(self, ciphertext: str) -> str:
        try:
            encrypted = base64.b64decode(ciphertext, validate=True)
            return self._box.decrypt(encrypted).decode('utf-8')
        except (CryptoError, binascii.Error, UnicodeError, ValueError) as exc:
            raise DecryptionError('No se pudo descifrar la contraseña.') from exc
