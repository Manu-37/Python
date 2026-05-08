from .clsIHM import clsIHM

class clsLAN(clsIHM):
    # 1. IDENTITÉ
    _table = "t_langue_lan"
    _pk    = "lan_id"

    # 2. DICTIONNAIRE DES COLONNES
    LAN_ID         = "lan_id"
    LAN_CODE       = "lan_code"
    LAN_NOM        = "lan_nom"
    LAN_RTL        = "lan_rtl"
    LAN_ACTIF      = "lan_actif"
    LAN_CREE_LE    = "lan_cree_le"
    LAN_MODIFIE_LE = "lan_modifie_le"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._tabNAL = None
        self._tabLEL = None
        self._tabLRE = None
        self._tabLCO = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if not self.lan_code:
            self.ogLog.error(f"LAN {self.lan_id} : Le code langue est obligatoire.")
            erreurs.append("ERREUR : Le code langue est obligatoire.")
            flag_error = True

        if not self.lan_nom:
            self.ogLog.error(f"LAN {self.lan_id} : Le nom de la langue est obligatoire.")
            erreurs.append("ERREUR : Le nom de la langue est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def lan_id(self) -> int:
        return self.get_natural(self.LAN_ID)

    @lan_id.setter
    def lan_id(self, valeur: int):
        self.set_natural(self.LAN_ID, valeur)

    @property
    def lan_code(self) -> str:
        return self.get_natural(self.LAN_CODE)

    @lan_code.setter
    def lan_code(self, valeur: str):
        self.set_natural(self.LAN_CODE, valeur)

    @property
    def lan_nom(self) -> str:
        return self.get_natural(self.LAN_NOM)

    @lan_nom.setter
    def lan_nom(self, valeur: str):
        self.set_natural(self.LAN_NOM, valeur)

    @property
    def lan_rtl(self) -> bool:
        return self.get_natural(self.LAN_RTL)

    @lan_rtl.setter
    def lan_rtl(self, valeur: bool):
        self.set_natural(self.LAN_RTL, valeur)

    @property
    def lan_actif(self) -> bool:
        return self.get_natural(self.LAN_ACTIF)

    @lan_actif.setter
    def lan_actif(self, valeur: bool):
        self.set_natural(self.LAN_ACTIF, valeur)

    @property
    def lan_cree_le(self):
        return self.get_natural(self.LAN_CREE_LE)

    @property
    def lan_modifie_le(self):
        return self.get_natural(self.LAN_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def tabNAL(self):
        """Associations application/langue pour cette langue (Lazy Loading)."""
        if self._tabNAL is None:
            from .clsNAL import clsNAL
            sql = (f"SELECT * FROM {clsNAL._schema}.{clsNAL._table} "
                   f"WHERE {clsNAL.LAN_ID} = {self.ogEngine.placeholder}")
            self._tabNAL = clsNAL.DepuisResultat(self.ogEngine.execute_select(sql, (self.lan_id,)))
        return self._tabNAL

    @property
    def tabLEL(self):
        """Libellés d'éléments pour cette langue (Lazy Loading)."""
        if self._tabLEL is None:
            from .clsLEL import clsLEL
            sql = (f"SELECT * FROM {clsLEL._schema}.{clsLEL._table} "
                   f"WHERE {clsLEL.LAN_ID} = {self.ogEngine.placeholder}")
            self._tabLEL = clsLEL.DepuisResultat(self.ogEngine.execute_select(sql, (self.lan_id,)))
        return self._tabLEL

    @property
    def tabLRE(self):
        """Libellés de relations pour cette langue (Lazy Loading)."""
        if self._tabLRE is None:
            from .clsLRE import clsLRE
            sql = (f"SELECT * FROM {clsLRE._schema}.{clsLRE._table} "
                   f"WHERE {clsLRE.LAN_ID} = {self.ogEngine.placeholder}")
            self._tabLRE = clsLRE.DepuisResultat(self.ogEngine.execute_select(sql, (self.lan_id,)))
        return self._tabLRE

    @property
    def tabLCO(self):
        """Libellés de colonnes pour cette langue (Lazy Loading)."""
        if self._tabLCO is None:
            from .clsLCO import clsLCO
            sql = (f"SELECT * FROM {clsLCO._schema}.{clsLCO._table} "
                   f"WHERE {clsLCO.LAN_ID} = {self.ogEngine.placeholder}")
            self._tabLCO = clsLCO.DepuisResultat(self.ogEngine.execute_select(sql, (self.lan_id,)))
        return self._tabLCO
