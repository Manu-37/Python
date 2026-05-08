from .clsIHM import clsIHM

class clsTAF(clsIHM):
    # 1. IDENTITÉ
    _table = "t_type_affichage_taf"
    _pk    = "taf_id"

    # 2. DICTIONNAIRE DES COLONNES
    TAF_ID         = "taf_id"
    TAF_CODE       = "taf_code"
    TAF_NOM        = "taf_nom"
    TAF_CREE_LE    = "taf_cree_le"
    TAF_MODIFIE_LE = "taf_modifie_le"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._tabCOL = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if not self.taf_code:
            self.ogLog.error(f"TAF {self.taf_id} : Le code type affichage est obligatoire.")
            erreurs.append("ERREUR : Le code type affichage est obligatoire.")
            flag_error = True

        if not self.taf_nom:
            self.ogLog.error(f"TAF {self.taf_id} : Le nom du type affichage est obligatoire.")
            erreurs.append("ERREUR : Le nom du type affichage est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def taf_id(self) -> int:
        return self.get_natural(self.TAF_ID)

    @taf_id.setter
    def taf_id(self, valeur: int):
        self.set_natural(self.TAF_ID, valeur)

    @property
    def taf_code(self) -> str:
        return self.get_natural(self.TAF_CODE)

    @taf_code.setter
    def taf_code(self, valeur: str):
        self.set_natural(self.TAF_CODE, valeur)

    @property
    def taf_nom(self) -> str:
        return self.get_natural(self.TAF_NOM)

    @taf_nom.setter
    def taf_nom(self, valeur: str):
        self.set_natural(self.TAF_NOM, valeur)

    @property
    def taf_cree_le(self):
        return self.get_natural(self.TAF_CREE_LE)

    @property
    def taf_modifie_le(self):
        return self.get_natural(self.TAF_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def tabCOL(self):
        """Colonnes ayant ce type d'affichage (Lazy Loading)."""
        if self._tabCOL is None:
            from .clsCOL import clsCOL
            sql = (f"SELECT * FROM {clsCOL._schema}.{clsCOL._table} "
                   f"WHERE {clsCOL.TAF_ID} = {self.ogEngine.placeholder}")
            self._tabCOL = clsCOL.DepuisResultat(self.ogEngine.execute_select(sql, (self.taf_id,)))
        return self._tabCOL
