from .clsIHM import clsIHM

class clsCOL(clsIHM):
    # 1. IDENTITÉ
    _table = "t_colonne_col"
    _pk    = "col_id"

    # 2. DICTIONNAIRE DES COLONNES
    COL_ID         = "col_id"
    REL_ID         = "rel_id"
    TAF_ID         = "taf_id"
    COL_NOM        = "col_nom"
    COL_LARGEUR    = "col_largeur"
    COL_ACTIF      = "col_actif"
    COL_CREE_LE    = "col_cree_le"
    COL_MODIFIE_LE = "col_modifie_le"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "rel_id": ["rel_nom"],
        "taf_id": ["taf_code"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oREL   = None
        self._oTAF   = None
        self._tabLCO = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.rel_id is None:
            self.ogLog.error(f"COL {self.col_id} : L'identifiant de la relation est obligatoire.")
            erreurs.append("ERREUR : L'identifiant de la relation est obligatoire.")
            flag_error = True

        if self.taf_id is None:
            self.ogLog.error(f"COL {self.col_id} : L'identifiant du type d'affichage est obligatoire.")
            erreurs.append("ERREUR : L'identifiant du type d'affichage est obligatoire.")
            flag_error = True

        if not self.col_nom:
            self.ogLog.error(f"COL {self.col_id} : Le nom de la colonne est obligatoire.")
            erreurs.append("ERREUR : Le nom de la colonne est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def col_id(self) -> int:
        return self.get_natural(self.COL_ID)

    @col_id.setter
    def col_id(self, valeur: int):
        self.set_natural(self.COL_ID, valeur)

    @property
    def rel_id(self) -> int:
        return self.get_natural(self.REL_ID)

    @rel_id.setter
    def rel_id(self, valeur: int):
        self.set_natural(self.REL_ID, valeur)

    @property
    def taf_id(self) -> int:
        return self.get_natural(self.TAF_ID)

    @taf_id.setter
    def taf_id(self, valeur: int):
        self.set_natural(self.TAF_ID, valeur)

    @property
    def col_nom(self) -> str:
        return self.get_natural(self.COL_NOM)

    @col_nom.setter
    def col_nom(self, valeur: str):
        self.set_natural(self.COL_NOM, valeur)

    @property
    def col_largeur(self) -> int:
        return self.get_natural(self.COL_LARGEUR)

    @col_largeur.setter
    def col_largeur(self, valeur: int):
        self.set_natural(self.COL_LARGEUR, valeur)

    @property
    def col_actif(self) -> bool:
        return self.get_natural(self.COL_ACTIF)

    @col_actif.setter
    def col_actif(self, valeur: bool):
        self.set_natural(self.COL_ACTIF, valeur)

    @property
    def col_cree_le(self):
        return self.get_natural(self.COL_CREE_LE)

    @property
    def col_modifie_le(self):
        return self.get_natural(self.COL_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def oREL(self):
        """Relation parente (Lazy Loading)."""
        if self._oREL is None:
            from .clsREL import clsREL
            self._oREL = clsREL(rel_id=self.rel_id)
        return self._oREL

    @property
    def oTAF(self):
        """Type d'affichage parent (Lazy Loading)."""
        if self._oTAF is None:
            from .clsTAF import clsTAF
            self._oTAF = clsTAF(taf_id=self.taf_id)
        return self._oTAF

    @property
    def tabLCO(self):
        """Libellés multilingues de cette colonne (Lazy Loading)."""
        if self._tabLCO is None:
            from .clsLCO import clsLCO
            sql = (f"SELECT * FROM {clsLCO._schema}.{clsLCO._table} "
                   f"WHERE {clsLCO.COL_ID} = {self.ogEngine.placeholder}")
            self._tabLCO = clsLCO.DepuisResultat(self.ogEngine.execute_select(sql, (self.col_id,)))
        return self._tabLCO
