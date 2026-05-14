from .clsIHM import clsIHM

class clsDBR(clsIHM):
    # 1. IDENTITÉ
    _table = "t_db_rapport_dbr"
    _pk    = "dbr_id"

    # 2. DICTIONNAIRE DES COLONNES
    DBR_ID         = "dbr_id"
    DB_ID          = "db_id"
    DBR_DATE       = "dbr_date"
    DBR_JSON       = "dbr_json"
    DBR_CREE_LE    = "dbr_cree_le"
    DBR_MODIFIE_LE = "dbr_modifie_le"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oDB = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.db_id is None:
            self.ogLog.error(f"DBR {self.dbr_id} : L'identifiant de la base est obligatoire.")
            erreurs.append("ERREUR : L'identifiant de la base est obligatoire.")
            flag_error = True

        if not self.dbr_json:
            self.ogLog.error(f"DBR {self.dbr_id} : Le contenu JSON du rapport est obligatoire.")
            erreurs.append("ERREUR : Le contenu JSON du rapport est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def dbr_id(self) -> int:
        return self.get_natural(self.DBR_ID)

    @dbr_id.setter
    def dbr_id(self, valeur: int):
        self.set_natural(self.DBR_ID, valeur)

    @property
    def db_id(self) -> int:
        return self.get_natural(self.DB_ID)

    @db_id.setter
    def db_id(self, valeur: int):
        self.set_natural(self.DB_ID, valeur)

    @property
    def dbr_date(self):
        return self.get_natural(self.DBR_DATE)

    @dbr_date.setter
    def dbr_date(self, valeur):
        self.set_natural(self.DBR_DATE, valeur)

    @property
    def dbr_json(self):
        return self.get_natural(self.DBR_JSON)

    @dbr_json.setter
    def dbr_json(self, valeur):
        self.set_natural(self.DBR_JSON, valeur)

    @property
    def dbr_cree_le(self):
        return self.get_natural(self.DBR_CREE_LE)

    @property
    def dbr_modifie_le(self):
        return self.get_natural(self.DBR_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def oDB(self):
        """Base de données parente (Lazy Loading)."""
        if self._oDB is None:
            from .clsDB import clsDB
            self._oDB = clsDB(db_id=self.db_id)
        return self._oDB
