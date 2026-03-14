from sysclasses.clsINI import clsINI
from pathlib import Path


class clsINIDBBaseRef(clsINI):
    """
    Singleton dédié à la lecture de db_baseref.ini.

    Ce fichier est physiquement séparé du fichier ini projet pour des raisons
    de sécurité — il contient les données sensibles de cryptographie et de
    connexion à la base de référence centrale.

    Ordre dans AppBootstrap : étape 2, après clsINICommun, avant clsLOG.

    Premier appel : clsINIDBBaseRef(chemin) — depuis AppBootstrap
    Appels suivants : clsINIDBBaseRef() — depuis clsCrypto, clsDBAManager
    """

    _instance    = None
    _initialized = False

    def __new__(cls, chemin=None):
        if cls._instance is None:
            if chemin is None:
                raise RuntimeError(
                    "clsINIDBBaseRef doit être initialisé avec un chemin au premier appel."
                )
            instance = super().__new__(cls)
            cls._instance = instance
        return cls._instance

    def __init__(self, chemin=None):
        if self._initialized:
            return
        self._initialized = True
        super().__init__(chemin)

    @property
    def security_params(self) -> dict:
        """Chemin de la clé Fernet."""
        return self.get_section("SECURITY")

    @property
    def db_params(self) -> dict:
        """Paramètres de connexion à la base registre centrale."""
        d = self.get_section("DB_BASEREF")
        if 'port' in d:
            d['port'] = int(d['port'])
        return d

    @property
    def ssh_params(self) -> dict:
        """Paramètres du tunnel SSH vers la base registre centrale."""
        d = self.get_section("SSH_GATEWAY")
        if 'port' in d:
            d['port'] = int(d['port'])
        return d