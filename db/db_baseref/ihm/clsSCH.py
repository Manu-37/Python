from .clsIHM import clsIHM

class clsSCH(clsIHM):
    # 1. IDENTITÉ
    _table = "t_schema_sch"
    _pk    = "sch_id"

    # 2. DICTIONNAIRE DES COLONNES
    SCH_ID         = "sch_id"
    DB_ID          = "db_id"
    SCH_NOM        = "sch_nom"
    SCH_ACTIF      = "sch_actif"
    SCH_CREE_LE    = "sch_cree_le"
    SCH_MODIFIE_LE = "sch_modifie_le"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "db_id": ["db_code"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oDB    = None
        self._tabREL = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.db_id is None:
            self.ogLog.error(f"SCH {self.sch_id} : L'identifiant de la base est obligatoire.")
            erreurs.append("ERREUR : L'identifiant de la base est obligatoire.")
            flag_error = True

        if not self.sch_nom:
            self.ogLog.error(f"SCH {self.sch_id} : Le nom du schéma est obligatoire.")
            erreurs.append("ERREUR : Le nom du schéma est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def sch_id(self) -> int:
        return self.get_natural(self.SCH_ID)

    @sch_id.setter
    def sch_id(self, valeur: int):
        self.set_natural(self.SCH_ID, valeur)

    @property
    def db_id(self) -> int:
        return self.get_natural(self.DB_ID)

    @db_id.setter
    def db_id(self, valeur: int):
        self.set_natural(self.DB_ID, valeur)

    @property
    def sch_nom(self) -> str:
        return self.get_natural(self.SCH_NOM)

    @sch_nom.setter
    def sch_nom(self, valeur: str):
        self.set_natural(self.SCH_NOM, valeur)

    @property
    def sch_actif(self) -> bool:
        return self.get_natural(self.SCH_ACTIF)

    @sch_actif.setter
    def sch_actif(self, valeur: bool):
        self.set_natural(self.SCH_ACTIF, valeur)

    @property
    def sch_cree_le(self):
        return self.get_natural(self.SCH_CREE_LE)

    @property
    def sch_modifie_le(self):
        return self.get_natural(self.SCH_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def oDB(self):
        """Base de données parente (Lazy Loading)."""
        if self._oDB is None:
            from .clsDB import clsDB
            self._oDB = clsDB(db_id=self.db_id)
        return self._oDB

    @property
    def tabREL(self):
        """Relations (tables/vues) de ce schéma (Lazy Loading)."""
        if self._tabREL is None:
            from .clsREL import clsREL
            sql = (f"SELECT * FROM {clsREL._schema}.{clsREL._table} "
                   f"WHERE {clsREL.SCH_ID} = {self.ogEngine.placeholder}")
            self._tabREL = clsREL.DepuisResultat(self.ogEngine.execute_select(sql, (self.sch_id,)))
        return self._tabREL
