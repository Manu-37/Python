import os
from cryptography.fernet import Fernet
from sysclasses.clsINISecurity import clsINISecurity


class clsCrypto:
    """
    Gère le chiffrement et le déchiffrement des données sensibles.
    La clé est stockée physiquement hors de l'application.
    Singleton : une seule instance par processus.

    La clé de chiffrement et security.ini résident sur le même partage réseau.
    Un attaquant disposant des deux peut déchiffrer les credentials.
    Risque accepté — infrastructure domestique, pas de serveur de clés dédié disponible.
    """
    _instance    = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Reconstruction du chemin complet :
        # chemin_base (path du .ini projet) + security_key_file (nom du fichier)
        oSecurity         = clsINISecurity()
        chemin_base       = oSecurity.base_path
        security_key_file = oSecurity.security_params.get('security_key_file')

        if not security_key_file:
            raise ValueError(
                "clsCrypto | 'security_key_file' absent de la section [SECURITY] "
                "dans security.ini."
            )

        self._security_path = chemin_base / security_key_file
        self._cipher        = self._load_or_create_key()

    def _load_or_create_key(self) -> Fernet:
        if not os.path.exists(self._security_path):
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(self._security_path), exist_ok=True)
            with open(self._security_path, "wb") as key_file:
                key_file.write(key)
            try:
                os.chmod(self._security_path, 0o400)
            except Exception:
                pass
        with open(self._security_path, "rb") as key_file:
            key = key_file.read()
        return Fernet(key)

    def encrypt(self, data: str) -> bytes:
        if not data:
            return b""
        return self._cipher.encrypt(data.encode('utf-8'))

    def decrypt(self, encrypted_data: bytes) -> str:
        if not encrypted_data:
            return ""
        return self._cipher.decrypt(bytes(encrypted_data)).decode('utf-8')