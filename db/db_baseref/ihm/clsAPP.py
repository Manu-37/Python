from .clsIHM import clsIHM

class clsAPP(clsIHM):
    # 1. IDENTITÉ
    _table = "t_application_app"
    _pk    = "app_id"

    # 2. DICTIONNAIRE DES COLONNES
    APP_ID          = "app_id"
    APP_CODE        = "app_code"
    APP_NOM         = "app_nom"
    APP_DESCRIPTION = "app_description"
    APP_CREE_LE     = "app_cree_le"
    APP_MODIFIE_LE  = "app_modifie_le"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._tabNAL = None
        self._tabELE = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if not self.app_code:
            self.ogLog.error(f"APP {self.app_id} : Le code application est obligatoire.")
            erreurs.append("ERREUR : Le code application est obligatoire.")
            flag_error = True

        if not self.app_nom:
            self.ogLog.error(f"APP {self.app_id} : Le nom de l'application est obligatoire.")
            erreurs.append("ERREUR : Le nom de l'application est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def app_id(self) -> int:
        return self.get_natural(self.APP_ID)

    @app_id.setter
    def app_id(self, valeur: int):
        self.set_natural(self.APP_ID, valeur)

    @property
    def app_code(self) -> str:
        return self.get_natural(self.APP_CODE)

    @app_code.setter
    def app_code(self, valeur: str):
        self.set_natural(self.APP_CODE, valeur)

    @property
    def app_nom(self) -> str:
        return self.get_natural(self.APP_NOM)

    @app_nom.setter
    def app_nom(self, valeur: str):
        self.set_natural(self.APP_NOM, valeur)

    @property
    def app_description(self) -> str:
        return self.get_natural(self.APP_DESCRIPTION)

    @app_description.setter
    def app_description(self, valeur: str):
        self.set_natural(self.APP_DESCRIPTION, valeur)

    @property
    def app_cree_le(self):
        return self.get_natural(self.APP_CREE_LE)

    @property
    def app_modifie_le(self):
        return self.get_natural(self.APP_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def tabNAL(self):
        """Langues associées à cette application (Lazy Loading)."""
        if self._tabNAL is None:
            from .clsNAL import clsNAL
            sql = (f"SELECT * FROM {clsNAL._schema}.{clsNAL._table} "
                   f"WHERE {clsNAL.APP_ID} = {self.ogEngine.placeholder}")
            self._tabNAL = clsNAL.DepuisResultat(self.ogEngine.execute_select(sql, (self.app_id,)))
        return self._tabNAL

    @property
    def tabELE(self):
        """Éléments UI appartenant à cette application (Lazy Loading)."""
        if self._tabELE is None:
            from .clsELE import clsELE
            sql = (f"SELECT * FROM {clsELE._schema}.{clsELE._table} "
                   f"WHERE {clsELE.APP_ID} = {self.ogEngine.placeholder}")
            self._tabELE = clsELE.DepuisResultat(self.ogEngine.execute_select(sql, (self.app_id,)))
        return self._tabELE
