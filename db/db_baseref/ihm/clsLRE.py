from .clsIHM import clsIHM

class clsLRE(clsIHM):
    # 1. IDENTITÉ
    _table = "t_libelle_relation_lre"
    _pk    = ["rel_id", "lan_id"]

    # 2. DICTIONNAIRE DES COLONNES
    REL_ID         = "rel_id"
    LAN_ID         = "lan_id"
    LRE_LABEL      = "lre_label"
    LRE_TOOLTIP    = "lre_tooltip"
    LRE_CREE_LE    = "lre_cree_le"
    LRE_MODIFIE_LE = "lre_modifie_le"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "rel_id": ["rel_nom"],
        "lan_id": ["lan_code"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oREL = None
        self._oLAN = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.rel_id is None:
            self.ogLog.error(f"LRE : L'identifiant de la relation est obligatoire.")
            erreurs.append("ERREUR : L'identifiant de la relation est obligatoire.")
            flag_error = True

        if self.lan_id is None:
            self.ogLog.error(f"LRE : L'identifiant langue est obligatoire.")
            erreurs.append("ERREUR : L'identifiant langue est obligatoire.")
            flag_error = True

        if not self.lre_label:
            self.ogLog.error(f"LRE {self.rel_id}/{self.lan_id} : Le libellé est obligatoire.")
            erreurs.append("ERREUR : Le libellé est obligatoire.")
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
    def lan_id(self) -> int:
        return self.get_natural(self.LAN_ID)

    @lan_id.setter
    def lan_id(self, valeur: int):
        self.set_natural(self.LAN_ID, valeur)

    @property
    def lre_label(self) -> str:
        return self.get_natural(self.LRE_LABEL)

    @lre_label.setter
    def lre_label(self, valeur: str):
        self.set_natural(self.LRE_LABEL, valeur)

    @property
    def lre_tooltip(self) -> str:
        return self.get_natural(self.LRE_TOOLTIP)

    @lre_tooltip.setter
    def lre_tooltip(self, valeur: str):
        self.set_natural(self.LRE_TOOLTIP, valeur)

    @property
    def lre_cree_le(self):
        return self.get_natural(self.LRE_CREE_LE)

    @property
    def lre_modifie_le(self):
        return self.get_natural(self.LRE_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def oREL(self):
        """Relation parente (Lazy Loading)."""
        if self._oREL is None:
            from .clsREL import clsREL
            self._oREL = clsREL(rel_id=self.rel_id)
        return self._oREL

    @property
    def oLAN(self):
        """Langue parente (Lazy Loading)."""
        if self._oLAN is None:
            from .clsLAN import clsLAN
            self._oLAN = clsLAN(lan_id=self.lan_id)
        return self._oLAN
