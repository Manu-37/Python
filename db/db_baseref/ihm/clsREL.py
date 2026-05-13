from .clsIHM import clsIHM

class clsREL(clsIHM):
    # 1. IDENTITÉ
    _table = "t_relation_rel"
    _pk    = "rel_id"

    # 2. DICTIONNAIRE DES COLONNES
    REL_ID         = "rel_id"
    SCH_ID         = "sch_id"
    TRE_ID         = "tre_id"
    REL_NOM        = "rel_nom"
    REL_CREE_LE    = "rel_cree_le"
    REL_MODIFIE_LE = "rel_modifie_le"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "sch_id": ["sch_nom"],
        "tre_id": ["tre_code"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oSCH   = None
        self._oTRE   = None
        self._tabLRE = None
        self._tabCOL = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.sch_id is None:
            self.ogLog.error(f"REL {self.rel_id} : L'identifiant du schéma est obligatoire.")
            erreurs.append("ERREUR : L'identifiant du schéma est obligatoire.")
            flag_error = True

        if self.tre_id is None:
            self.ogLog.error(f"REL {self.rel_id} : L'identifiant du type de relation est obligatoire.")
            erreurs.append("ERREUR : L'identifiant du type de relation est obligatoire.")
            flag_error = True

        if not self.rel_nom:
            self.ogLog.error(f"REL {self.rel_id} : Le nom de la relation est obligatoire.")
            erreurs.append("ERREUR : Le nom de la relation est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def rel_id(self) -> int:
        return self.get_natural(self.REL_ID)

    @rel_id.setter
    def rel_id(self, valeur: int):
        self.set_natural(self.REL_ID, valeur)

    @property
    def sch_id(self) -> int:
        return self.get_natural(self.SCH_ID)

    @sch_id.setter
    def sch_id(self, valeur: int):
        self.set_natural(self.SCH_ID, valeur)

    @property
    def tre_id(self) -> int:
        return self.get_natural(self.TRE_ID)

    @tre_id.setter
    def tre_id(self, valeur: int):
        self.set_natural(self.TRE_ID, valeur)

    @property
    def rel_nom(self) -> str:
        return self.get_natural(self.REL_NOM)

    @rel_nom.setter
    def rel_nom(self, valeur: str):
        self.set_natural(self.REL_NOM, valeur)

    @property
    def rel_cree_le(self):
        return self.get_natural(self.REL_CREE_LE)

    @property
    def rel_modifie_le(self):
        return self.get_natural(self.REL_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def oSCH(self):
        """Schéma parent (Lazy Loading)."""
        if self._oSCH is None:
            from .clsSCH import clsSCH
            self._oSCH = clsSCH(sch_id=self.sch_id)
        return self._oSCH

    @property
    def oTRE(self):
        """Type de relation parent (Lazy Loading)."""
        if self._oTRE is None:
            from .clsTRE import clsTRE
            self._oTRE = clsTRE(tre_id=self.tre_id)
        return self._oTRE

    @property
    def tabLRE(self):
        """Libellés multilingues de cette relation (Lazy Loading)."""
        if self._tabLRE is None:
            from .clsLRE import clsLRE
            sql = (f"SELECT * FROM {clsLRE._schema}.{clsLRE._table} "
                   f"WHERE {clsLRE.REL_ID} = {self.ogEngine.placeholder}")
            self._tabLRE = clsLRE.DepuisResultat(self.ogEngine.execute_select(sql, (self.rel_id,)))
        return self._tabLRE

    @property
    def tabCOL(self):
        """Colonnes de cette relation (Lazy Loading)."""
        if self._tabCOL is None:
            from .clsCOL import clsCOL
            sql = (f"SELECT * FROM {clsCOL._schema}.{clsCOL._table} "
                   f"WHERE {clsCOL.REL_ID} = {self.ogEngine.placeholder}")
            self._tabCOL = clsCOL.DepuisResultat(self.ogEngine.execute_select(sql, (self.rel_id,)))
        return self._tabCOL
