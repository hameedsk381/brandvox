import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from app.config import get_settings

logger = logging.getLogger(__name__)

# Prefix lets us distinguish encrypted values from legacy plaintext rows.
_ENC_PREFIX = "enc:v1:"

_fernet: Optional[Fernet] = None


def _build_fernet() -> Fernet:
    settings = get_settings()
    if settings.ENCRYPTION_KEY:
        return Fernet(settings.ENCRYPTION_KEY.encode())
    # Development fallback: derive a stable key from JWT_SECRET so local setups
    # work without extra config. Production startup requires ENCRYPTION_KEY.
    derived = hashlib.sha256(settings.JWT_SECRET.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = _build_fernet()
    return _fernet


def encrypt_value(value: str) -> str:
    return _ENC_PREFIX + get_fernet().encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    if not value.startswith(_ENC_PREFIX):
        # Legacy plaintext row written before encryption was introduced.
        # It gets re-encrypted the next time the row is saved.
        return value
    try:
        return get_fernet().decrypt(value[len(_ENC_PREFIX):].encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt stored token: ENCRYPTION_KEY does not match the key used to encrypt it")
        raise ValueError("Stored credential cannot be decrypted with the configured ENCRYPTION_KEY")


class EncryptedToken(TypeDecorator):
    """String column encrypted at rest with Fernet. Reads legacy plaintext as-is."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None or value == "":
            return value
        return encrypt_value(value)

    def process_result_value(self, value, dialect):
        if value is None or value == "":
            return value
        return decrypt_value(value)
