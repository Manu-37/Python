from .clsIHM import clsIHM

class clsTRE(clsIHM):
    # 1. IDENTITÉ
    _table = "t_type_relation_tre"
    _pk    = "tre_id"

    # 2. DICTIONNAIRE DES COLONNES
    TRE_ID         = "tre_id"
    TRE_CODE       = "tre_code"
    TRE_NOM        = "tre_nom"
    TRE_CREE_LE    = "tre_cree_le"
    TRE_MODIFIE_LE = "tre_modifie_le"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._tabREL = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if not self.tre_code:
            self.ogLog.error(f"TRE {self.tre_id} : Le code type relation est obligatoire.")
            erreurs.append("ERREUR : Le code type relation est obligatoire.")
            flag_error = True

        if not self.tre_nom:
            self.ogLog.error(f"TRE {self.tre_id} : Le nom du type relation est obligatoire.")
            erreurs.append("ERREUR : Le nom du type relation est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def tre_id(self) -> int:
        return self.get_natural(self.TRE_ID)

    @tre_id.setter
    def tre_id(self, valeur: int):
        self.set_natural(self.TRE_ID, valeur)

    @property
    def tre_code(self) -> str:
        return self.get_natural(self.TRE_CODE)

    @tre_code.setter
    def tre_code(self, valeur: str):
        self.set_natural(self.TRE_CODE, valeur)

    @property
    def tre_nom(self) -> str:
        return self.get_natural(self.TRE_NOM)

    @tre_nom.setter
    def tre_nom(self, valeur: str):
        self.set_natural(self.TRE_NOM, valeur)

    @property
    def tre_cree_le(self):
        return self.get_natural(self.TRE_CREE_LE)

    @property
    def tre_modifie_le(self):
        return self.get_natural(self.TRE_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def tabREL(self):
        """Relations de ce type (Lazy Loading)."""
        if self._tabREL is None:
            from .clsREL import clsREL
            sql = (f"SELECT * FROM {clsREL._schema}.{clsREL._table} "
                   f"WHERE {clsREL.TRE_ID} = {self.ogEngine.placeholder}")
            self._tabREL = clsREL.DepuisResultat(self.ogEngine.execute_select(sql, (self.tre_id,)))
        return self._tabREL
