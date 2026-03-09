import os
from pathlib import Path
from cryptography.fernet import Fernet
from .clsINICommun import clsINICommun


class clsCrypto:
    """
    Gère le chiffrement et le déchiffrement des données sensibles.
    La clé est stockée physiquement hors de l'application.
    """
    _instance = None

    # --------------------------------------------------
    # Singleton via __new__
    # --------------------------------------------------
    def __new__(cls, key_path: str = None):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instance = instance
        return cls._instance

    def __init__(self, key_path: str = None):
        # Garde : si déjà initialisé, on ne fait rien
        if self._initialized:
            return
        self._initialized = True

        self._key_path = Path(key_path) / 'db_baseref.ini'
        self._baserefini = clsINICommun(self._key_path)
        self._security_path = self._baserefini.db_baseref_security.get('key_path')
        self._cipher = self._load_or_create_key()

    def _load_or_create_key(self) -> Fernet:
        if not os.path.exists(self._security_path):
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(self._key_path), exist_ok=True)
            with open(self._key_path, "wb") as key_file:
                key_file.write(key)
            try:
                os.chmod(self._security_path, 0o400)
            except:
                pass 
        with open(self._security_path, "rb") as key_file:
            key = key_file.read()
        return Fernet(key)

    def encrypt(self, data: str) -> bytes:
        if not data: return b""
        return self._cipher.encrypt(data.encode('utf-8'))

    def decrypt(self, encrypted_data: bytes) -> str:
        if not encrypted_data: return ""
        return self._cipher.decrypt(bytes(encrypted_data)).decode('utf-8')
