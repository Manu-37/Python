from sysclasses.clsINI import clsINI
from pathlib import Path


class clsINICommun(clsINI):
    """
    Classe de base commune à tous les projets.

    INSTANCIATION DIRECTE INTERDITE — sauf pour récupérer le singleton existant.
    Chaque projet doit créer sa propre sous-classe, même vide :

        class clsINIMonProjet(clsINICommun):
            pass

    Singleton : une seule instance par processus.
        - Premier appel : via la sous-classe projet avec le chemin du fichier .ini
        - Appels suivants : clsINICommun() sans argument retourne l'instance existante

    Contenu : paramètres communs à tous les projets.
        - [ENVIRONNEMENT] : type d'env, ssh_enabled, path vers db_baseref.ini
        - [LOG]           : configuration du journal
        - [EMAIL_*]       : profils d'envoi email

    Les paramètres sensibles (connexion DB, clé Fernet) sont dans clsINIDBBaseRef.
    """

    _instance    = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls is clsINICommun:
            if clsINICommun._instance is None:
                raise TypeError(
                    "clsINICommun ne peut pas être instanciée directement.\n"
                    "Créez une sous-classe pour votre projet :\n\n"
                    "    class clsINIMonProjet(clsINICommun):\n"
                    "        pass"
                )
            return clsINICommun._instance

        if clsINICommun._instance is None:
            instance = super().__new__(cls)
            clsINICommun._instance = instance
        return clsINICommun._instance

    def __init__(self, filename=None):
        if self._initialized:
            return
        self._initialized = True
        super().__init__(filename)

    @property
    def env_params(self) -> dict:
        """Récupère tout ENVIRONNEMENT et gère le booléen ssh_enabled."""
        return self.get_section("ENVIRONNEMENT")

    @property
    def log_params(self) -> dict:
        """Récupère tout LOG et résout le chemin du dossier."""
        d = self.get_section("LOG")
        if 'folder' in d:
            p = Path(d['folder'])
            if not p.is_absolute():
                d['folder'] = str((Path(self._filename).parent / p).resolve())
        for key in ['level', 'max_bytes', 'backup_count']:
            if key in d:
                d[key] = int(d[key])
        return d

    @property
    def email_profiles(self) -> dict:
        """
        Retourne tous les profils email sous forme de dict de dicts.
        Toute section dont le nom commence par EMAIL_ est un profil.
        Ex : [EMAIL_ALERTES] → {'ALERTES': {smtp_server, smtp_port, sender, password, recipient}}
        """
        profiles = {}
        for section in self._config.sections():
            if section.upper().startswith("EMAIL_"):
                nom_profil = section[6:].upper()
                d = self.get_section(section)
                if 'smtp_port' in d:
                    d['smtp_port'] = int(d['smtp_port'])
                profiles[nom_profil] = d
        return profiles