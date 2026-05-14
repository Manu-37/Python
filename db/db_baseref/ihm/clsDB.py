from .clsIHM import clsIHM

class clsDB(clsIHM):
    # 1. IDENTITÉ
    _table = "t_db_db"
    _pk    = "db_id"

    # 2. DICTIONNAIRE DES COLONNES
    DB_ID          = "db_id"
    ENV_ID         = "env_id"
    BAS_ID         = "bas_id"
    DB_CODE        = "db_code"
    DB_NOM         = "db_nom"
    DB_DESCRIPTION = "db_description"
    DB_CREE_LE     = "db_cree_le"
    DB_MODIFIE_LE  = "db_modifie_le"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "env_id": ["env_code"],
        "bas_id": ["bas_nom"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._tabSCH = None
        self._oENV   = None
        self._oBAS   = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if not self.db_code:
            self.ogLog.error(f"DB {self.db_id} : Le code de la base est obligatoire.")
            erreurs.append("ERREUR : Le code de la base est obligatoire.")
            flag_error = True

        if not self.db_nom:
            self.ogLog.error(f"DB {self.db_id} : Le nom de la base est obligatoire.")
            erreurs.append("ERREUR : Le nom de la base est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def db_id(self) -> int:
        return self.get_natural(self.DB_ID)

    @db_id.setter
    def db_id(self, valeur: int):
        self.set_natural(self.DB_ID, valeur)

    @property
    def env_id(self) -> int:
        return self.get_natural(self.ENV_ID)

    @env_id.setter
    def env_id(self, valeur: int):
        self.set_natural(self.ENV_ID, valeur)

    @property
    def bas_id(self) -> int:
        return self.get_natural(self.BAS_ID)

    @bas_id.setter
    def bas_id(self, valeur: int):
        self.set_natural(self.BAS_ID, valeur)

    @property
    def db_code(self) -> str:
        return self.get_natural(self.DB_CODE)

    @db_code.setter
    def db_code(self, valeur: str):
        self.set_natural(self.DB_CODE, valeur)

    @property
    def db_nom(self) -> str:
        return self.get_natural(self.DB_NOM)

    @db_nom.setter
    def db_nom(self, valeur: str):
        self.set_natural(self.DB_NOM, valeur)

    @property
    def db_description(self) -> str:
        return self.get_natural(self.DB_DESCRIPTION)

    @db_description.setter
    def db_description(self, valeur: str):
        self.set_natural(self.DB_DESCRIPTION, valeur)

    @property
    def db_cree_le(self):
        return self.get_natural(self.DB_CREE_LE)

    @property
    def db_modifie_le(self):
        return self.get_natural(self.DB_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def oENV(self):
        """Environnement associé (Lazy Loading)."""
        if self._oENV is None and self.env_id is not None:
            from db.db_baseref.public.clsENV import clsENV
            self._oENV = clsENV(env_id=self.env_id)
        return self._oENV

    @property
    def oBAS(self):
        """Base physique associée (Lazy Loading)."""
        if self._oBAS is None and self.bas_id is not None:
            from db.db_baseref.public.clsBAS import clsBAS
            self._oBAS = clsBAS(bas_id=self.bas_id)
        return self._oBAS

    @property
    def tabSCH(self):
        """Schémas de cette base de données (Lazy Loading)."""
        if self._tabSCH is None:
            from .clsSCH import clsSCH
            sql = (f"SELECT * FROM {clsSCH._schema}.{clsSCH._table} "
                   f"WHERE {clsSCH.DB_ID} = {self.ogEngine.placeholder}")
            self._tabSCH = clsSCH.DepuisResultat(self.ogEngine.execute_select(sql, (self.db_id,)))
        return self._tabSCH
