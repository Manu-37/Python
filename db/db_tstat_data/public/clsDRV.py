from ..clsTstatData import clsTstatData


class clsDRV(clsTstatData):
    """
    Dernier état de conduite connu au moment du snapshot.
    PK = snp_id — relation 1-1 avec t_snapshot_snp.
    Une ligne existe uniquement si drive_state contient des données significatives
    (shift_state non null — véhicule en mouvement ou récemment conduit).
    """
    # 1. IDENTITÉ
    _schema = "public"
    _table  = "t_drive_drv"
    _pk     = "snp_id"

    # 2. DICTIONNAIRE DES COLONNES
    SNP_ID         = "snp_id"
    DRV_POWER      = "drv_power"
    DRV_SHIFTSTATE = "drv_shiftstate"
    DRV_SPEED      = "drv_speed"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oSNP = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if self.snp_id is None:
            erreurs.append("ERREUR : Le snapshot est obligatoire.")
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
    def drv_power(self) -> int:
        return self.get_natural(self.DRV_POWER)

    @drv_power.setter
    def drv_power(self, valeur: int):
        self.set_natural(self.DRV_POWER, valeur)

    @property
    def drv_shiftstate(self) -> str:
        return self.get_natural(self.DRV_SHIFTSTATE)

    @drv_shiftstate.setter
    def drv_shiftstate(self, valeur: str):
        self.set_natural(self.DRV_SHIFTSTATE, valeur)

    @property
    def drv_speed(self) -> int:
        return self.get_natural(self.DRV_SPEED)

    @drv_speed.setter
    def drv_speed(self, valeur: int):
        self.set_natural(self.DRV_SPEED, valeur)

    # 6. NAVIGATION

    @property
    def oSNP(self):
        """Retourne le snapshot parent (Lazy Loading)."""
        if self._oSNP is None:
            from .clsSNP import clsSNP
            self._oSNP = clsSNP(snp_id=self.snp_id)
        return self._oSNP