from .clsIHM import clsIHM

class clsLCO(clsIHM):
    # 1. IDENTITÉ
    _table = "t_libelle_colonne_lco"
    _pk    = ["col_id", "lan_id"]

    # 2. DICTIONNAIRE DES COLONNES
    COL_ID         = "col_id"
    LAN_ID         = "lan_id"
    LCO_LABEL       = "lco_label"
    LCO_LABEL_COURT = "lco_label_court"
    LCO_TOOLTIP     = "lco_tooltip"
    LCO_CREE_LE     = "lco_cree_le"
    LCO_MODIFIE_LE = "lco_modifie_le"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "col_id": ["col_nom"],
        "lan_id": ["lan_code"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oCOL = None
        self._oLAN = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.col_id is None:
            self.ogLog.error(f"LCO : L'identifiant de la colonne est obligatoire.")
            erreurs.append("ERREUR : L'identifiant de la colonne est obligatoire.")
            flag_error = True

        if self.lan_id is None:
            self.ogLog.error(f"LCO : L'identifiant langue est obligatoire.")
            erreurs.append("ERREUR : L'identifiant langue est obligatoire.")
            flag_error = True

        if not self.lco_label:
            self.ogLog.error(f"LCO {self.col_id}/{self.lan_id} : Le libellé est obligatoire.")
            erreurs.append("ERREUR : Le libellé est obligatoire.")
            flag_error = True

        if not self.lco_label_court:
            self.ogLog.error(f"LCO {self.col_id}/{self.lan_id} : Le libellé court est obligatoire.")
            erreurs.append("ERREUR : Le libellé court est obligatoire.")
            flag_error = True

        if not self.lco_tooltip:
            self.ogLog.error(f"LCO {self.col_id}/{self.lan_id} : L'info-bulle est obligatoire.")
            erreurs.append("ERREUR : L'info-bulle est fortement conseillée.")
        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def col_id(self) -> int:
        return self.get_natural(self.COL_ID)

    @col_id.setter
    def col_id(self, valeur: int):
        self.set_natural(self.COL_ID, valeur)

    @property
    def lan_id(self) -> int:
        return self.get_natural(self.LAN_ID)

    @lan_id.setter
    def lan_id(self, valeur: int):
        self.set_natural(self.LAN_ID, valeur)

    @property
    def lco_label(self) -> str:
        return self.get_natural(self.LCO_LABEL)

    @lco_label.setter
    def lco_label(self, valeur: str):
        self.set_natural(self.LCO_LABEL, valeur)

    @property
    def lco_label_court(self) -> str:
        return self.get_natural(self.LCO_LABEL_COURT)

    @lco_label_court.setter
    def lco_label_court(self, valeur: str):
        self.set_natural(self.LCO_LABEL_COURT, valeur)

    @property
    def lco_tooltip(self) -> str:
        return self.get_natural(self.LCO_TOOLTIP)

    @lco_tooltip.setter
    def lco_tooltip(self, valeur: str):
        self.set_natural(self.LCO_TOOLTIP, valeur)

    @property
    def lco_cree_le(self):
        return self.get_natural(self.LCO_CREE_LE)

    @property
    def lco_modifie_le(self):
        return self.get_natural(self.LCO_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def oCOL(self):
        """Colonne parente (Lazy Loading)."""
        if self._oCOL is None:
            from .clsCOL import clsCOL
            self._oCOL = clsCOL(col_id=self.col_id)
        return self._oCOL

    @property
    def oLAN(self):
        """Langue parente (Lazy Loading)."""
        if self._oLAN is None:
            from .clsLAN import clsLAN
            self._oLAN = clsLAN(lan_id=self.lan_id)
        return self._oLAN
