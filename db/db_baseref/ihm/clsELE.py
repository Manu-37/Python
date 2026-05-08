from .clsIHM import clsIHM

class clsELE(clsIHM):
    # 1. IDENTITÉ
    _table = "t_element_ele"
    _pk    = "ele_id"

    # 2. DICTIONNAIRE DES COLONNES
    ELE_ID          = "ele_id"
    APP_ID          = "app_id"
    TEL_ID          = "tel_id"
    ELE_CLE         = "ele_cle"
    ELE_DESCRIPTION = "ele_description"
    ELE_CREE_LE     = "ele_cree_le"
    ELE_MODIFIE_LE  = "ele_modifie_le"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "app_id": ["app_code", "app_nom"],
        "tel_id": ["tel_code", "tel_nom"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oAPP   = None
        self._oTEL   = None
        self._tabLEL = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.app_id is None:
            self.ogLog.error(f"ELE {self.ele_id} : L'identifiant application est obligatoire.")
            erreurs.append("ERREUR : L'identifiant application est obligatoire.")
            flag_error = True

        if self.tel_id is None:
            self.ogLog.error(f"ELE {self.ele_id} : L'identifiant type élément est obligatoire.")
            erreurs.append("ERREUR : L'identifiant type élément est obligatoire.")
            flag_error = True

        if not self.ele_cle:
            self.ogLog.error(f"ELE {self.ele_id} : La clé de l'élément est obligatoire.")
            erreurs.append("ERREUR : La clé de l'élément est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def ele_id(self) -> int:
        return self.get_natural(self.ELE_ID)

    @ele_id.setter
    def ele_id(self, valeur: int):
        self.set_natural(self.ELE_ID, valeur)

    @property
    def app_id(self) -> int:
        return self.get_natural(self.APP_ID)

    @app_id.setter
    def app_id(self, valeur: int):
        self.set_natural(self.APP_ID, valeur)

    @property
    def tel_id(self) -> int:
        return self.get_natural(self.TEL_ID)

    @tel_id.setter
    def tel_id(self, valeur: int):
        self.set_natural(self.TEL_ID, valeur)

    @property
    def ele_cle(self) -> str:
        return self.get_natural(self.ELE_CLE)

    @ele_cle.setter
    def ele_cle(self, valeur: str):
        self.set_natural(self.ELE_CLE, valeur)

    @property
    def ele_description(self) -> str:
        return self.get_natural(self.ELE_DESCRIPTION)

    @ele_description.setter
    def ele_description(self, valeur: str):
        self.set_natural(self.ELE_DESCRIPTION, valeur)

    @property
    def ele_cree_le(self):
        return self.get_natural(self.ELE_CREE_LE)

    @property
    def ele_modifie_le(self):
        return self.get_natural(self.ELE_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def oAPP(self):
        """Application parente (Lazy Loading)."""
        if self._oAPP is None:
            from .clsAPP import clsAPP
            self._oAPP = clsAPP(app_id=self.app_id)
        return self._oAPP

    @property
    def oTEL(self):
        """Type d'élément parent (Lazy Loading)."""
        if self._oTEL is None:
            from .clsTEL import clsTEL
            self._oTEL = clsTEL(tel_id=self.tel_id)
        return self._oTEL

    @property
    def tabLEL(self):
        """Libellés multilingues de cet élément (Lazy Loading)."""
        if self._tabLEL is None:
            from .clsLEL import clsLEL
            sql = (f"SELECT * FROM {clsLEL._schema}.{clsLEL._table} "
                   f"WHERE {clsLEL.ELE_ID} = {self.ogEngine.placeholder}")
            self._tabLEL = clsLEL.DepuisResultat(self.ogEngine.execute_select(sql, (self.ele_id,)))
        return self._tabLEL
