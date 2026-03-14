from sysclasses.clsINI import clsINI
from pathlib import Path


class clsINISecurity(clsINI):
    """
    Singleton dédié à la lecture de security.ini.

    Ce fichier est physiquement séparé du fichier ini projet pour des raisons
    de sécurité — il contient les données sensibles de chiffrement et de
    connexion à la base de référence centrale.

    NOTE SÉCURITÉ : la clé de chiffrement et ce fichier résident sur le même
    partage réseau. Un attaquant disposant des deux peut déchiffrer les
    credentials. Risque accepté — infrastructure domestique, pas de serveur
    de clés dédié disponible.

    Ordre dans AppBootstrap : étape 2, après clsINICommun, avant clsLOG.

    Premier appel : clsINISecurity(chemin)  — depuis AppBootstrap
    Appels suivants : clsINISecurity()      — depuis clsCrypto, clsDBAManager
    """

    _instance    = None
    _initialized = False

    def __new__(cls, chemin=None):
        if cls._instance is None:
            if chemin is None:
                raise RuntimeError(
                    "clsINISecurity doit être initialisé avec un chemin au premier appel."
                )
            instance = super().__new__(cls)
            cls._instance = instance
        return cls._instance

    def __init__(self, chemin=None):
        if self._initialized:
            return
        self._initialized = True
        super().__init__(chemin)
        # Mémorise le dossier contenant security.ini
        # Utilisé par clsCrypto pour reconstruire les chemins complets
        self._base_path = Path(chemin).parent

    @property
    def base_path(self) -> Path:
        """
        Dossier contenant security.ini — correspond au 'path' du .ini projet.
        Utilisé par clsCrypto pour reconstruire le chemin complet des fichiers clés.
        """
        return self._base_path

    @property
    def security_params(self) -> dict:
        """Nom du fichier de clé de chiffrement."""
        return self.get_section("SECURITY")

    @property
    def db_params(self) -> dict:
        """
        Paramètres de connexion à la base registre centrale.
        user et pwd sont chiffrés dans le fichier — déchiffrés ici à la lecture.
        """
        from sysclasses.clsCrypto import clsCrypto
        d = self.get_section("DB_BASEREF")
        if 'port' in d:
            d['port'] = int(d['port'])
        crypto = clsCrypto()
        if 'user' in d:
            d['user'] = crypto.decrypt(d['user'].encode('utf-8'))
        if 'pwd' in d:
            d['pwd'] = crypto.decrypt(d['pwd'].encode('utf-8'))
        return d

    @property
    def ssh_params(self) -> dict:
        """
        Paramètres du tunnel SSH vers la base registre centrale.
        ssh_enabled est géré ici — retiré de clsINICommun.
        ssh_key_file est un nom de fichier — chemin complet reconstruit via base_path.
        """
        d = self.get_section("SSH_GATEWAY")
        if 'port' in d:
            d['port'] = int(d['port'])
        if 'ssh_enabled' in d:
            d['ssh_enabled'] = d['ssh_enabled'].upper() == 'TRUE'
        if 'ssh_key_file' in d:
            d['ssh_key_path'] = self._base_path / d.pop('ssh_key_file')
        return d