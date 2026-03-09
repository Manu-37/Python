from ..clsBaseRef import clsBaseRef

class clsENV(clsBaseRef):
    """
    Entité représentant un Environnement (PROD, TEST, DEV, etc.).
    """
    # 1. IDENTITÉ
    _schema = "public"
    _table  = "t_environnement_env"
    _pk     = "env_id"

    # 2. DICTIONNAIRE DES COLONNES
    ENV_ID          = "env_id"
    ENV_CODE        = "env_code"
    ENV_DESCRIPTION = "env_description"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._tabBAS_ENV_NBE = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self):
        """Contrôle d'intégrité pour l'environnement."""
        erreurs        = []
        libelle_erreur = ""
        flag_error     = False

        # Le code ne peut être vide
        if not self.env_code:
            self.ogLog.error(f"ENV {self.env_code} : Le code de l'environnement est obligatoire.")
            erreurs.append("ERREUR : Le code de l'environnement est obligatoire.")
            flag_error = True

        # Le code doit être en majuscules
        if self.env_code and not self.env_code.isupper():
            self.ogLog.warning(f"ENV {self.env_code} : Le code '{self.env_code}' devrait être en majuscules.")
            erreurs.append("Avertissement : Le code de l'environnement devrait être en majuscules.")

        # La description est obligatoire
        if not self.env_description:
            self.ogLog.error(f"ENV {self.env_code} : Le nom de l'environnement est obligatoire.")
            erreurs.append("ERREUR : Le nom de l'environnement est obligatoire.")
            flag_error = True

        if erreurs:
            libelle_erreur = "\n".join(erreurs)

        return flag_error, libelle_erreur

    # 5. ACCÈS

    @property
    def env_id(self) -> int:
        return self.get_natural(self.ENV_ID)

    @env_id.setter
    def env_id(self, valeur: int):
        self.set_natural(self.ENV_ID, valeur)

    @property
    def env_code(self) -> str:
        return self.get_natural(self.ENV_CODE)

    @env_code.setter
    def env_code(self, valeur: str):
        self.set_natural(self.ENV_CODE, valeur)

    @property
    def env_description(self) -> str:
        return self.get_natural(self.ENV_DESCRIPTION)

    @env_description.setter
    def env_description(self, valeur: str):
        self.set_natural(self.ENV_DESCRIPTION, valeur)

    # 6. NAVIGATION

    @property
    def tabBAS_ENV_NBE(self):
        """Récupère tous les noeuds de connexion liés à cet environnement (Lazy Loading)."""
        if self._tabBAS_ENV_NBE is None:
            from .clsBAS_ENV_NBE import clsBAS_ENV_NBE

            sql = f"SELECT * FROM {clsBAS_ENV_NBE._schema}.{clsBAS_ENV_NBE._table} " \
                  f"WHERE {clsBAS_ENV_NBE.ENV_ID} = {self.ogEngine.placeholder}"

            res = self.ogEngine.execute_select(sql, (self.env_id,))

            self._tabBAS_ENV_NBE = clsBAS_ENV_NBE.DepuisResultat(res)

        return self._tabBAS_ENV_NBE
