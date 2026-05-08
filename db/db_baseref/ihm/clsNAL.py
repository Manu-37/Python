from .clsIHM import clsIHM

class clsNAL(clsIHM):
    # 1. IDENTITÉ
    _table = "t_app_lan_nal"
    _pk    = ["app_id", "lan_id"]

    # 2. DICTIONNAIRE DES COLONNES
    APP_ID         = "app_id"
    LAN_ID         = "lan_id"
    NAL_EST_DEFAUT = "nal_est_defaut"
    NAL_CREE_LE    = "nal_cree_le"
    NAL_MODIFIE_LE = "nal_modifie_le"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "app_id": ["app_code", "app_nom"],
        "lan_id": ["lan_code", "lan_nom"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oAPP = None
        self._oLAN = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.app_id is None:
            self.ogLog.error(f"NAL : L'identifiant application est obligatoire.")
            erreurs.append("ERREUR : L'identifiant application est obligatoire.")
            flag_error = True

        if self.lan_id is None:
            self.ogLog.error(f"NAL : L'identifiant langue est obligatoire.")
            erreurs.append("ERREUR : L'identifiant langue est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def app_id(self) -> int:
        return self.get_natural(self.APP_ID)

    @app_id.setter
    def app_id(self, valeur: int):
        self.set_natural(self.APP_ID, valeur)

    @property
    def lan_id(self) -> int:
        return self.get_natural(self.LAN_ID)

    @lan_id.setter
    def lan_id(self, valeur: int):
        self.set_natural(self.LAN_ID, valeur)

    @property
    def nal_est_defaut(self) -> bool:
        return self.get_natural(self.NAL_EST_DEFAUT)

    @nal_est_defaut.setter
    def nal_est_defaut(self, valeur: bool):
        self.set_natural(self.NAL_EST_DEFAUT, valeur)

    @property
    def nal_cree_le(self):
        return self.get_natural(self.NAL_CREE_LE)

    @property
    def nal_modifie_le(self):
        return self.get_natural(self.NAL_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def oAPP(self):
        """Application parente (Lazy Loading)."""
        if self._oAPP is None:
            from .clsAPP import clsAPP
            self._oAPP = clsAPP(app_id=self.app_id)
        return self._oAPP

    @property
    def oLAN(self):
        """Langue parente (Lazy Loading)."""
        if self._oLAN is None:
            from .clsLAN import clsLAN
            self._oLAN = clsLAN(lan_id=self.lan_id)
        return self._oLAN
