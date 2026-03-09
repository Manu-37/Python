from ..clsBaseRef import clsBaseRef

class clsBAS_ENV_NBE(clsBaseRef):
    # 1. IDENTITÉ
    _schema = "public"
    _table  = "t_bas_env_nbe"
    _pk     = ["bas_id", "env_id"]

    # 2. DICTIONNAIRE DES COLONNES
    # FK — portent le nom de la colonne dans la table étrangère (convention BDD)
    BAS_ID       = "bas_id"
    ENV_ID       = "env_id"

    # 2b. AFFICHAGE COMBO FK
    # Pour chaque colonne FK : liste ordonnée des colonnes à afficher.
    # Premier élément = colonne de tri dans le combo.
    FK_DISPLAY = {
        "env_id": ["env_code", "env_description"],
        "bas_id": ["bas_nom",  "bas_description"],
    }

    # Connexion de base
    NBE_HOST         = "nbe_host"          # BYTEA (chiffré)
    NBE_PORT         = "nbe_port"
    NBE_DB_NAME      = "nbe_db_name"
    NBE_USER         = "nbe_user"          # BYTEA (chiffré)
    NBE_PWD          = "nbe_pwd"           # BYTEA (chiffré)
    # SSH
    NBE_SSH_ENABLED  = "nbe_ssh_enabled"
    NBE_SSH_HOST     = "nbe_ssh_host"      # BYTEA (chiffré)
    NBE_SSH_USER     = "nbe_ssh_user"      # BYTEA (chiffré)
    NBE_SSH_KEY_PATH = "nbe_ssh_key_path"  # BYTEA (chiffré)
    NBE_SSH_PORT     = "nbe_ssh_port"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oBase = None
        self._oEnv  = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        """Contrôle d'intégrité pour les noeuds de connexion."""
        erreurs        = []
        libelle_erreur = ""
        flag_error     = False

        # --- Bloc 1 : Connexion de base (toujours obligatoire) ---

        if not self.nbe_host:
            self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : L'hôte de connexion est obligatoire.")
            erreurs.append("ERREUR : L'hôte de connexion est obligatoire.")
            flag_error = True

        if self.nbe_port is None:
            self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : Le port de connexion est obligatoire.")
            erreurs.append("ERREUR : Le port de connexion est obligatoire.")
            flag_error = True
        elif not isinstance(self.nbe_port, int):
            self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : Le port de connexion doit être un entier.")
            erreurs.append("ERREUR : Le port de connexion doit être un entier.")
            flag_error = True
        elif not (1 <= self.nbe_port <= 65535):
            self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : Le port '{self.nbe_port}' doit être compris entre 1 et 65535.")
            erreurs.append("ERREUR : Le port de connexion doit être compris entre 1 et 65535.")
            flag_error = True

        if not self.nbe_db_name:
            self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : Le nom de la base de données est obligatoire.")
            erreurs.append("ERREUR : Le nom de la base de données est obligatoire.")
            flag_error = True

        if not self.nbe_user:
            self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : L'utilisateur de connexion est obligatoire.")
            erreurs.append("ERREUR : L'utilisateur de connexion est obligatoire.")
            flag_error = True

        if not self.nbe_pwd:
            self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : Le mot de passe de connexion est obligatoire.")
            erreurs.append("ERREUR : Le mot de passe de connexion est obligatoire.")
            flag_error = True

        # --- Bloc 2 : SSH (conditionnel) ---

        if self.nbe_ssh_enabled:

            if not self.nbe_ssh_host:
                self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : L'hôte SSH est obligatoire si le SSH est activé.")
                erreurs.append("ERREUR : L'hôte SSH est obligatoire si le SSH est activé.")
                flag_error = True

            if self.nbe_ssh_port is None:
                self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : Le port SSH est obligatoire si le SSH est activé.")
                erreurs.append("ERREUR : Le port SSH est obligatoire si le SSH est activé.")
                flag_error = True
            elif not isinstance(self.nbe_ssh_port, int):
                self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : Le port SSH doit être un entier.")
                erreurs.append("ERREUR : Le port SSH doit être un entier.")
                flag_error = True
            elif not (1 <= self.nbe_ssh_port <= 65535):
                self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : Le port SSH '{self.nbe_ssh_port}' doit être compris entre 1 et 65535.")
                erreurs.append("ERREUR : Le port SSH doit être compris entre 1 et 65535.")
                flag_error = True

            if not self.nbe_ssh_user:
                self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : L'utilisateur SSH est obligatoire si le SSH est activé.")
                erreurs.append("ERREUR : L'utilisateur SSH est obligatoire si le SSH est activé.")
                flag_error = True

            if not self.nbe_ssh_key_path:
                self.ogLog.error(f"NBE {self.bas_id}/{self.env_id} : Le chemin de la clé SSH est obligatoire si le SSH est activé.")
                erreurs.append("ERREUR : Le chemin de la clé SSH est obligatoire si le SSH est activé.")
                flag_error = True

        if erreurs:
            libelle_erreur = "\n".join(erreurs)

        return flag_error, libelle_erreur

    # 5. ACCÈS

    # --- FK (PK composite) ---

    @property
    def bas_id(self) -> int:
        return self.get_natural(self.BAS_ID)

    @bas_id.setter
    def bas_id(self, valeur: int):
        self.set_natural(self.BAS_ID, valeur)

    @property
    def env_id(self) -> int:
        return self.get_natural(self.ENV_ID)

    @env_id.setter
    def env_id(self, valeur: int):
        self.set_natural(self.ENV_ID, valeur)

    # --- Connexion de base ---

    @property
    def nbe_host(self) -> str:
        return self.get_decrypted(self.NBE_HOST)

    @nbe_host.setter
    def nbe_host(self, valeur: str):
        self.set_encrypted(self.NBE_HOST, valeur)

    @property
    def nbe_port(self) -> int:
        return self.get_natural(self.NBE_PORT)

    @nbe_port.setter
    def nbe_port(self, valeur: int):
        self.set_natural(self.NBE_PORT, valeur)

    @property
    def nbe_db_name(self) -> str:
        return self.get_natural(self.NBE_DB_NAME)

    @nbe_db_name.setter
    def nbe_db_name(self, valeur: str):
        self.set_natural(self.NBE_DB_NAME, valeur)

    @property
    def nbe_user(self) -> str:
        return self.get_decrypted(self.NBE_USER)

    @nbe_user.setter
    def nbe_user(self, valeur: str):
        self.set_encrypted(self.NBE_USER, valeur)

    @property
    def nbe_pwd(self) -> str:
        return self.get_decrypted(self.NBE_PWD)

    @nbe_pwd.setter
    def nbe_pwd(self, valeur: str):
        self.set_encrypted(self.NBE_PWD, valeur)

    # --- SSH ---

    @property
    def nbe_ssh_enabled(self) -> bool:
        return self.get_natural(self.NBE_SSH_ENABLED)

    @nbe_ssh_enabled.setter
    def nbe_ssh_enabled(self, valeur: bool):
        self.set_natural(self.NBE_SSH_ENABLED, valeur)

    @property
    def nbe_ssh_host(self) -> str:
        return self.get_decrypted(self.NBE_SSH_HOST)

    @nbe_ssh_host.setter
    def nbe_ssh_host(self, valeur: str):
        self.set_encrypted(self.NBE_SSH_HOST, valeur)

    @property
    def nbe_ssh_port(self) -> int:
        return self.get_natural(self.NBE_SSH_PORT)

    @nbe_ssh_port.setter
    def nbe_ssh_port(self, valeur: int):
        self.set_natural(self.NBE_SSH_PORT, valeur)

    @property
    def nbe_ssh_user(self) -> str:
        return self.get_decrypted(self.NBE_SSH_USER)

    @nbe_ssh_user.setter
    def nbe_ssh_user(self, valeur: str):
        self.set_encrypted(self.NBE_SSH_USER, valeur)

    @property
    def nbe_ssh_key_path(self) -> str:
        return self.get_decrypted(self.NBE_SSH_KEY_PATH)

    @nbe_ssh_key_path.setter
    def nbe_ssh_key_path(self, valeur: str):
        self.set_encrypted(self.NBE_SSH_KEY_PATH, valeur)

    # 6. NAVIGATION (Lazy Loading)

    @property
    def oBase(self):
        """Retourne l'objet clsBAS parent (1 seul, logique FK)."""
        if self._oBase is None:
            from .clsBAS import clsBAS
            self._oBase = clsBAS(bas_id=self.bas_id)
        return self._oBase

    @property
    def oEnv(self):
        """Retourne l'objet clsENV parent (1 seul, logique FK)."""
        if self._oEnv is None:
            from .clsENV import clsENV
            self._oEnv = clsENV(env_id=self.env_id)
        return self._oEnv
