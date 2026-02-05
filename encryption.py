"""Encryption utilities for secure storage of sensitive documents."""

import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from logging_config import get_logger

logger = get_logger(__name__)

# Key file location (stored outside output directory)
_KEY_FILE = Path(__file__).parent / ".encryption_key"


def _generate_key() -> bytes:
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key()


def _get_or_create_key() -> bytes:
    """
    Get existing encryption key or create a new one.

    The key is stored in a file with restricted permissions.
    In production, consider using a secrets manager or HSM.
    """
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes()

    # Generate new key
    key = _generate_key()

    # Save with restricted permissions (owner read/write only)
    _KEY_FILE.write_bytes(key)
    try:
        os.chmod(_KEY_FILE, 0o600)
    except OSError:
        # Windows doesn't support chmod the same way
        pass

    logger.info("Generated new encryption key")
    return key


def _derive_key_from_password(password: str, salt: bytes) -> bytes:
    """
    Derive an encryption key from a password using PBKDF2.

    Args:
        password: The password to derive from.
        salt: Random salt for key derivation.

    Returns:
        Derived Fernet-compatible key.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


class DocumentEncryptor:
    """Handles encryption and decryption of sensitive documents."""

    def __init__(self, key: bytes = None):
        """
        Initialize the encryptor.

        Args:
            key: Optional encryption key. If not provided, uses stored key.
        """
        self._key = key or _get_or_create_key()
        self._fernet = Fernet(self._key)

    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt a string document.

        Args:
            plaintext: The document content to encrypt.

        Returns:
            Encrypted bytes.
        """
        return self._fernet.encrypt(plaintext.encode('utf-8'))

    def decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypt an encrypted document.

        Args:
            ciphertext: The encrypted content.

        Returns:
            Decrypted string.
        """
        return self._fernet.decrypt(ciphertext).decode('utf-8')

    def encrypt_to_file(self, content: str, filepath: str) -> str:
        """
        Encrypt content and save to file.

        Args:
            content: Document content to encrypt.
            filepath: Path to save the encrypted file.

        Returns:
            Path to the encrypted file (with .enc extension).
        """
        encrypted_data = self.encrypt(content)

        # Add .enc extension to indicate encrypted file
        if not filepath.endswith('.enc'):
            encrypted_path = filepath + '.enc'
        else:
            encrypted_path = filepath

        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)

        # Set restrictive permissions
        try:
            os.chmod(encrypted_path, 0o600)
        except OSError:
            pass

        logger.debug("Encrypted document saved")
        return encrypted_path

    def decrypt_from_file(self, filepath: str) -> str:
        """
        Read and decrypt content from an encrypted file.

        Args:
            filepath: Path to the encrypted file.

        Returns:
            Decrypted document content.
        """
        with open(filepath, 'rb') as f:
            encrypted_data = f.read()

        return self.decrypt(encrypted_data)


# Global encryptor instance (lazy initialization)
_encryptor: DocumentEncryptor = None


def get_encryptor() -> DocumentEncryptor:
    """Get or create the global encryptor instance."""
    global _encryptor
    if _encryptor is None:
        _encryptor = DocumentEncryptor()
    return _encryptor


def encrypt_document(content: str, filepath: str) -> str:
    """
    Convenience function to encrypt and save a document.

    Args:
        content: Document content.
        filepath: Output file path.

    Returns:
        Path to the encrypted file.
    """
    return get_encryptor().encrypt_to_file(content, filepath)


def decrypt_document(filepath: str) -> str:
    """
    Convenience function to decrypt a document from file.

    Args:
        filepath: Path to encrypted file.

    Returns:
        Decrypted content.
    """
    return get_encryptor().decrypt_from_file(filepath)
