from ..clsTstatData import clsTstatData


class clsVEH(clsTstatData):
    """
    Véhicule dans db_tstat_data.
    Copie synchronisée depuis db_tstat_admin.t_vehicle_veh.
    Source de vérité : db_tstat_admin — ne jamais modifier ici directement.
    """
    # 1. IDENTITÉ
    _schema = "public"
    _table  = "t_vehicle_veh"
    _pk     = "veh_id"

    # 2. DICTIONNAIRE DES COLONNES
    VEH_ID              = "veh_id"
    VEH_VIN             = "veh_vin"
    VEH_DISPLAYNAME     = "veh_displayname"
    VEH_POLLINGINTERVAL = "veh_pollinginterval"
    VEH_ISACTIVE        = "veh_isactive"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._tabSNP = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if not self.veh_vin:
            erreurs.append("ERREUR : Le VIN est obligatoire.")
            flag_error = True
        elif len(self.veh_vin) != 17:
            erreurs.append("ERREUR : Le VIN doit contenir exactement 17 caractères.")
            flag_error = True

        if self.veh_pollinginterval is None:
            self.veh_pollinginterval = 300

        if not isinstance(self.veh_pollinginterval, int):
            erreurs.append("ERREUR : L'intervalle de polling doit être un entier.")
            flag_error = True
        elif self.veh_pollinginterval < 60:
            erreurs.append("ERREUR : L'intervalle de polling ne peut pas être inférieur à 60 secondes.")
            flag_error = True

        libelle_erreur = "\n".join(erreurs) if erreurs else ""
        return flag_error, libelle_erreur

    # 5. ACCÈS

    @property
    def veh_id(self) -> int:
        return self.get_natural(self.VEH_ID)

    @veh_id.setter
    def veh_id(self, valeur: int):
        self.set_natural(self.VEH_ID, valeur)

    @property
    def veh_vin(self) -> str:
        return self.get_natural(self.VEH_VIN)

    @veh_vin.setter
    def veh_vin(self, valeur: str):
        self.set_natural(self.VEH_VIN, valeur)

    @property
    def veh_displayname(self) -> str:
        return self.get_natural(self.VEH_DISPLAYNAME)

    @veh_displayname.setter
    def veh_displayname(self, valeur: str):
        self.set_natural(self.VEH_DISPLAYNAME, valeur)

    @property
    def veh_pollinginterval(self) -> int:
        return self.get_natural(self.VEH_POLLINGINTERVAL)

    @veh_pollinginterval.setter
    def veh_pollinginterval(self, valeur: int):
        self.set_natural(self.VEH_POLLINGINTERVAL, valeur)

    @property
    def veh_isactive(self) -> bool:
        return self.get_natural(self.VEH_ISACTIVE)

    @veh_isactive.setter
    def veh_isactive(self, valeur: bool):
        self.set_natural(self.VEH_ISACTIVE, valeur)

    # 6. NAVIGATION

    @property
    def tabSNP(self) -> list:
        """Retourne tous les snapshots de ce véhicule (Lazy Loading)."""
        if self._tabSNP is None:
            from .clsSNP import clsSNP
            sql = (
                f"SELECT * FROM {clsSNP._schema}.{clsSNP._table} "
                f"WHERE {clsSNP.VEH_ID} = {self.ogEngine.placeholder} "
                f"ORDER BY snp_timestamp DESC"
            )
            res = self.ogEngine.execute_select(sql, (self.veh_id,))
            self._tabSNP = clsSNP.DepuisResultat(res)
        return self._tabSNP