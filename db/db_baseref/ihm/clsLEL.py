from .clsIHM import clsIHM

class clsLEL(clsIHM):
    # 1. IDENTITÉ
    _table = "t_libelle_element_lel"
    _pk    = ["ele_id", "lan_id"]

    # 2. DICTIONNAIRE DES COLONNES
    ELE_ID         = "ele_id"
    LAN_ID         = "lan_id"
    LEL_LABEL      = "lel_label"
    LEL_TOOLTIP    = "lel_tooltip"
    LEL_CREE_LE    = "lel_cree_le"
    LEL_MODIFIE_LE = "lel_modifie_le"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "ele_id": ["ele_cle", "ele_description"],
        "lan_id": ["lan_code", "lan_nom"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oELE = None
        self._oLAN = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.ele_id is None:
            self.ogLog.error(f"LEL : L'identifiant de l'élément est obligatoire.")
            erreurs.append("ERREUR : L'identifiant de l'élément est obligatoire.")
            flag_error = True

        if self.lan_id is None:
            self.ogLog.error(f"LEL : L'identifiant langue est obligatoire.")
            erreurs.append("ERREUR : L'identifiant langue est obligatoire.")
            flag_error = True

        if not self.lel_label:
            self.ogLog.error(f"LEL {self.ele_id}/{self.lan_id} : Le libellé est obligatoire.")
            erreurs.append("ERREUR : Le libellé est obligatoire.")
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
    def lan_id(self) -> int:
        return self.get_natural(self.LAN_ID)

    @lan_id.setter
    def lan_id(self, valeur: int):
        self.set_natural(self.LAN_ID, valeur)

    @property
    def lel_label(self) -> str:
        return self.get_natural(self.LEL_LABEL)

    @lel_label.setter
    def lel_label(self, valeur: str):
        self.set_natural(self.LEL_LABEL, valeur)

    @property
    def lel_tooltip(self) -> str:
        return self.get_natural(self.LEL_TOOLTIP)

    @lel_tooltip.setter
    def lel_tooltip(self, valeur: str):
        self.set_natural(self.LEL_TOOLTIP, valeur)

    @property
    def lel_cree_le(self):
        return self.get_natural(self.LEL_CREE_LE)

    @property
    def lel_modifie_le(self):
        return self.get_natural(self.LEL_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def oELE(self):
        """Élément parent (Lazy Loading)."""
        if self._oELE is None:
            from .clsELE import clsELE
            self._oELE = clsELE(ele_id=self.ele_id)
        return self._oELE

    @property
    def oLAN(self):
        """Langue parente (Lazy Loading)."""
        if self._oLAN is None:
            from .clsLAN import clsLAN
            self._oLAN = clsLAN(lan_id=self.lan_id)
        return self._oLAN
