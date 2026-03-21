from ..clsTstatData import clsTstatData


class clsSNP(clsTstatData):
    """
    Snapshot — enveloppe de chaque appel API réussi.
    Une instance = un instant T = une ligne dans t_snapshot_snp.
    Les tables filles (CHG, DRV) utilisent snp_id comme PK.
    """
    # 1. IDENTITÉ
    _schema = "public"
    _table  = "t_snapshot_snp"
    _pk     = "snp_id"

    # 2. DICTIONNAIRE DES COLONNES
    SNP_ID          = "snp_id"
    VEH_ID          = "veh_id"
    SNP_TIMESTAMP   = "snp_timestamp"
    SNP_COLLECTEDAT = "snp_collectedat"
    SNP_STATE       = "snp_state"
    SNP_ODOMETER    = "snp_odometer"
    SNP_FIRMWARE    = "snp_firmware"

    # 2b. AFFICHAGE COMBO FK
    FK_DISPLAY = {
        "veh_id": ["veh_vin", "veh_displayname"],
    }

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oVEH = None
        self._oCHG = None
        self._oDRV = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.veh_id is None:
            erreurs.append("ERREUR : Le véhicule est obligatoire.")
            flag_error = True

        if self.snp_timestamp is None:
            erreurs.append("ERREUR : L'horodatage Tesla est obligatoire.")
            flag_error = True

        if self.snp_collectedat is None:
            erreurs.append("ERREUR : L'horodatage collecteur est obligatoire.")
            flag_error = True

        if not self.snp_state:
            erreurs.append("ERREUR : L'état du véhicule est obligatoire.")
            flag_error = True

        libelle_erreur = "\n".join(erreurs) if erreurs else ""
        return flag_error, libelle_erreur

    # 5. ACCÈS

    @property
    def snp_id(self) -> int:
        return self.get_natural(self.SNP_ID)

    @snp_id.setter
    def snp_id(self, valeur: int):
        self.set_natural(self.SNP_ID, valeur)

    @property
    def veh_id(self) -> int:
        return self.get_natural(self.VEH_ID)

    @veh_id.setter
    def veh_id(self, valeur: int):
        self.set_natural(self.VEH_ID, valeur)

    @property
    def snp_timestamp(self):
        return self.get_natural(self.SNP_TIMESTAMP)

    @snp_timestamp.setter
    def snp_timestamp(self, valeur):
        self.set_natural(self.SNP_TIMESTAMP, valeur)

    @property
    def snp_collectedat(self):
        return self.get_natural(self.SNP_COLLECTEDAT)

    @snp_collectedat.setter
    def snp_collectedat(self, valeur):
        self.set_natural(self.SNP_COLLECTEDAT, valeur)

    @property
    def snp_state(self) -> str:
        return self.get_natural(self.SNP_STATE)

    @snp_state.setter
    def snp_state(self, valeur: str):
        self.set_natural(self.SNP_STATE, valeur)

    @property
    def snp_odometer(self):
        return self.get_natural(self.SNP_ODOMETER)

    @snp_odometer.setter
    def snp_odometer(self, valeur):
        self.set_natural(self.SNP_ODOMETER, valeur)

    @property
    def snp_firmware(self) -> str:
        return self.get_natural(self.SNP_FIRMWARE)

    @snp_firmware.setter
    def snp_firmware(self, valeur: str):
        self.set_natural(self.SNP_FIRMWARE, valeur)

    # 6. NAVIGATION

    @property
    def oVEH(self):
        """Retourne le véhicule parent (Lazy Loading)."""
        if self._oVEH is None:
            from .clsVEH import clsVEH
            self._oVEH = clsVEH(veh_id=self.veh_id)
        return self._oVEH

    @property
    def oCHG(self):
        """Retourne les données de charge liées à ce snapshot (Lazy Loading — peut être None)."""
        if self._oCHG is None:
            from .clsCHG import clsCHG
            sql = (
                f"SELECT * FROM {clsCHG._schema}.{clsCHG._table} "
                f"WHERE {clsCHG.SNP_ID} = {self.ogEngine.placeholder}"
            )
            res = self.ogEngine.execute_select(sql, (self.snp_id,))
            if res:
                self._oCHG = clsCHG.DepuisResultat(res)[0]
        return self._oCHG

    @property
    def oDRV(self):
        """Retourne les données de conduite liées à ce snapshot (Lazy Loading — peut être None)."""
        if self._oDRV is None:
            from .clsDRV import clsDRV
            sql = (
                f"SELECT * FROM {clsDRV._schema}.{clsDRV._table} "
                f"WHERE {clsDRV.SNP_ID} = {self.ogEngine.placeholder}"
            )
            res = self.ogEngine.execute_select(sql, (self.snp_id,))
            if res:
                self._oDRV = clsDRV.DepuisResultat(res)[0]
        return self._oDRV