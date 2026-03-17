from ..clsTstatAdmin import clsTstatAdmin


class clsTTK(clsTstatAdmin):
    # 1. IDENTITÉ
    _schema = "public"
    _table  = "t_teslatoken_ttk"
    _pk     = "veh_id"

    # 2. DICTIONNAIRE DES COLONNES
    VEH_ID              = "veh_id"
    TTK_CLIENTID        = "ttk_clientid"
    TTK_CLIENTSECRET    = "ttk_clientsecret"
    TTK_REDIRECTURI     = "ttk_redirecturi"
    TTK_FLEETURL        = "ttk_fleeturl"
    TTK_SCOPES          = "ttk_scopes"
    TTK_ACCESSTOKEN     = "ttk_accesstoken"
    TTK_REFRESHTOKEN    = "ttk_refreshtoken"
    TTK_IDTOKEN         = "ttk_idtoken"
    TTK_EXPIRESIN       = "ttk_expiresin"
    TTK_CREATEDAT       = "ttk_createdat"
    TTK_EXPIRESAT       = "ttk_expiresat"
    TTK_LASTREFRESHAT   = "ttk_lastrefreshat"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "veh_id": ["veh_vin", "veh_displayname"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oVEH = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.veh_id is None:
            erreurs.append("ERREUR : Le véhicule est obligatoire.")
            flag_error = True

        if not self.ttk_clientid:
            erreurs.append("ERREUR : Le Client ID est obligatoire.")
            flag_error = True

        if not self.ttk_clientsecret:
            erreurs.append("ERREUR : Le Client Secret est obligatoire.")
            flag_error = True

        if not self.ttk_redirecturi:
            erreurs.append("ERREUR : L'URI de redirection est obligatoire.")
            flag_error = True

        if not self.ttk_fleeturl:
            erreurs.append("ERREUR : L'URL Fleet est obligatoire.")
            flag_error = True

        libelle_erreur = "\n".join(erreurs) if erreurs else ""
        return flag_error, libelle_erreur

    # 5. ACCÈS

    # --- FK (PK) ---

    @property
    def veh_id(self) -> int:
        return self.get_natural(self.VEH_ID)

    @veh_id.setter
    def veh_id(self, valeur: int):
        self.set_natural(self.VEH_ID, valeur)

    # --- Configuration application Tesla ---

    @property
    def ttk_clientid(self) -> str:
        return self.get_decrypted(self.TTK_CLIENTID)

    @ttk_clientid.setter
    def ttk_clientid(self, valeur: str):
        self.set_encrypted(self.TTK_CLIENTID, valeur)

    @property
    def ttk_clientsecret(self) -> str:
        return self.get_decrypted(self.TTK_CLIENTSECRET)

    @ttk_clientsecret.setter
    def ttk_clientsecret(self, valeur: str):
        self.set_encrypted(self.TTK_CLIENTSECRET, valeur)

    @property
    def ttk_redirecturi(self) -> str:
        return self.get_natural(self.TTK_REDIRECTURI)

    @ttk_redirecturi.setter
    def ttk_redirecturi(self, valeur: str):
        self.set_natural(self.TTK_REDIRECTURI, valeur)

    @property
    def ttk_fleeturl(self) -> str:
        return self.get_natural(self.TTK_FLEETURL)

    @ttk_fleeturl.setter
    def ttk_fleeturl(self, valeur: str):
        self.set_natural(self.TTK_FLEETURL, valeur)

    @property
    def ttk_scopes(self) -> str:
        return self.get_natural(self.TTK_SCOPES)

    @ttk_scopes.setter
    def ttk_scopes(self, valeur: str):
        self.set_natural(self.TTK_SCOPES, valeur)

    # --- Tokens OAuth ---

    @property
    def ttk_accesstoken(self) -> str:
        return self.get_decrypted(self.TTK_ACCESSTOKEN)

    @ttk_accesstoken.setter
    def ttk_accesstoken(self, valeur: str):
        self.set_encrypted(self.TTK_ACCESSTOKEN, valeur)

    @property
    def ttk_refreshtoken(self) -> str:
        return self.get_decrypted(self.TTK_REFRESHTOKEN)

    @ttk_refreshtoken.setter
    def ttk_refreshtoken(self, valeur: str):
        self.set_encrypted(self.TTK_REFRESHTOKEN, valeur)

    @property
    def ttk_idtoken(self) -> str:
        return self.get_decrypted(self.TTK_IDTOKEN)

    @ttk_idtoken.setter
    def ttk_idtoken(self, valeur: str):
        self.set_encrypted(self.TTK_IDTOKEN, valeur)

    # --- Gestion expiration ---

    @property
    def ttk_expiresin(self) -> int:
        return self.get_natural(self.TTK_EXPIRESIN)

    @ttk_expiresin.setter
    def ttk_expiresin(self, valeur: int):
        self.set_natural(self.TTK_EXPIRESIN, valeur)

    @property
    def ttk_createdat(self):
        return self.get_natural(self.TTK_CREATEDAT)

    @ttk_createdat.setter
    def ttk_createdat(self, valeur):
        self.set_natural(self.TTK_CREATEDAT, valeur)

    @property
    def ttk_expiresat(self):
        return self.get_natural(self.TTK_EXPIRESAT)

    @ttk_expiresat.setter
    def ttk_expiresat(self, valeur):
        self.set_natural(self.TTK_EXPIRESAT, valeur)

    @property
    def ttk_lastrefreshat(self):
        return self.get_natural(self.TTK_LASTREFRESHAT)

    @ttk_lastrefreshat.setter
    def ttk_lastrefreshat(self, valeur):
        self.set_natural(self.TTK_LASTREFRESHAT, valeur)

    # 6. NAVIGATION

    @property
    def oVEH(self):
        """Retourne le véhicule parent (Lazy Loading)."""
        if self._oVEH is None:
            from .clsVEH import clsVEH
            self._oVEH = clsVEH(veh_id=self.veh_id)
        return self._oVEH