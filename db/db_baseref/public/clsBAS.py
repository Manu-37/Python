from ..clsBaseRef import clsBaseRef

class clsBAS(clsBaseRef):
    # 1. IDENTITÉ
    _schema = "public"
    _table  = "t_base_bas"
    _pk     = "bas_id"

    # 2. DICTIONNAIRE DES COLONNES
    BAS_ID          = "bas_id"
    BAS_NOM         = "bas_nom"
    BAS_DESCRIPTION = "bas_description"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._tabBAS_ENV_NBE = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self):
        """Contrôle d'intégrité pour les bases."""
        erreurs        = []
        libelle_erreur = ""
        flag_error     = False

        # Le nom symbolique est obligatoire
        if not self.bas_nom:
            self.ogLog.error(f"BAS {self.bas_nom} : Le nom symbolique de la base est obligatoire.")
            erreurs.append("ERREUR : Le nom symbolique de la base est obligatoire.")
            flag_error = True

        # Le nom symbolique doit être en majuscules
        if self.bas_nom and not self.bas_nom.isupper():
            self.ogLog.warning(f"BAS {self.bas_nom} : Le nom symbolique '{self.bas_nom}' devrait être en majuscules.")
            erreurs.append("Avertissement : Le nom symbolique de la base devrait être en majuscules.")

        # La description est obligatoire
        if not self.bas_description:
            self.ogLog.error(f"BAS {self.bas_nom} : La description de la base est obligatoire.")
            erreurs.append("ERREUR : La description de la base est obligatoire.")
            flag_error = True

        if erreurs:
            libelle_erreur = "\n".join(erreurs)

        return flag_error, libelle_erreur

    # 5. ACCÈS

    @property
    def bas_id(self) -> int:
        return self.get_natural(self.BAS_ID)

    @bas_id.setter
    def bas_id(self, valeur: int):
        self.set_natural(self.BAS_ID, valeur)

    @property
    def bas_nom(self) -> str:
        return self.get_natural(self.BAS_NOM)

    @bas_nom.setter
    def bas_nom(self, valeur: str):
        self.set_natural(self.BAS_NOM, valeur)

    @property
    def bas_description(self) -> str:
        return self.get_natural(self.BAS_DESCRIPTION)

    @bas_description.setter
    def bas_description(self, valeur: str):
        self.set_natural(self.BAS_DESCRIPTION, valeur)

    # 6. NAVIGATION

    @property
    def tabBAS_ENV_NBE(self):
        """Récupère tous les noeuds de connexion liés à cette base (Lazy Loading)."""
        if self._tabBAS_ENV_NBE is None:
            from .clsBAS_ENV_NBE import clsBAS_ENV_NBE

            sql = f"SELECT * FROM {clsBAS_ENV_NBE._schema}.{clsBAS_ENV_NBE._table} " \
                  f"WHERE {clsBAS_ENV_NBE.BAS_ID} = {self.ogEngine.placeholder}"

            res = self.ogEngine.execute_select(sql, (self.bas_id,))

            self._tabBAS_ENV_NBE = clsBAS_ENV_NBE.DepuisResultat(res)

        return self._tabBAS_ENV_NBE
