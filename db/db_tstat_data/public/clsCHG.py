from ..clsTstatData import clsTstatData


class clsCHG(clsTstatData):
    """
    Données de charge extraites d'un snapshot.
    PK = snp_id — relation 1-1 avec t_snapshot_snp.
    Une ligne existe uniquement si le véhicule était branché au moment du snapshot.
    """
    # 1. IDENTITÉ
    _schema = "public"
    _table  = "t_charge_chg"
    _pk     = "snp_id"

    # 2. DICTIONNAIRE DES COLONNES
    SNP_ID            = "snp_id"
    CHG_STATE         = "chg_state"
    CHG_BATTERYLEVEL  = "chg_batterylevel"
    CHG_USABLELEVEL   = "chg_usablelevel"
    CHG_RANGE         = "chg_range"
    CHG_LIMITSOC      = "chg_limitsoc"
    CHG_POWER         = "chg_power"
    CHG_VOLTAGE       = "chg_voltage"
    CHG_CURRENT       = "chg_current"
    CHG_RATE          = "chg_rate"
    CHG_ENERGYADDED   = "chg_energyadded"
    CHG_MINUTESTOFULL = "chg_minutestofull"
    CHG_FASTCHARGER   = "chg_fastcharger"
    CHG_CABLETYPE     = "chg_cabletype"

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

        if not self.chg_state:
            erreurs.append("ERREUR : L'état de charge est obligatoire.")
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
    def chg_state(self) -> str:
        return self.get_natural(self.CHG_STATE)

    @chg_state.setter
    def chg_state(self, valeur: str):
        self.set_natural(self.CHG_STATE, valeur)

    @property
    def chg_batterylevel(self) -> int:
        return self.get_natural(self.CHG_BATTERYLEVEL)

    @chg_batterylevel.setter
    def chg_batterylevel(self, valeur: int):
        self.set_natural(self.CHG_BATTERYLEVEL, valeur)

    @property
    def chg_usablelevel(self) -> int:
        return self.get_natural(self.CHG_USABLELEVEL)

    @chg_usablelevel.setter
    def chg_usablelevel(self, valeur: int):
        self.set_natural(self.CHG_USABLELEVEL, valeur)

    @property
    def chg_range(self):
        return self.get_natural(self.CHG_RANGE)

    @chg_range.setter
    def chg_range(self, valeur):
        self.set_natural(self.CHG_RANGE, valeur)

    @property
    def chg_limitsoc(self) -> int:
        return self.get_natural(self.CHG_LIMITSOC)

    @chg_limitsoc.setter
    def chg_limitsoc(self, valeur: int):
        self.set_natural(self.CHG_LIMITSOC, valeur)

    @property
    def chg_power(self) -> int:
        return self.get_natural(self.CHG_POWER)

    @chg_power.setter
    def chg_power(self, valeur: int):
        self.set_natural(self.CHG_POWER, valeur)

    @property
    def chg_voltage(self) -> int:
        return self.get_natural(self.CHG_VOLTAGE)

    @chg_voltage.setter
    def chg_voltage(self, valeur: int):
        self.set_natural(self.CHG_VOLTAGE, valeur)

    @property
    def chg_current(self) -> int:
        return self.get_natural(self.CHG_CURRENT)

    @chg_current.setter
    def chg_current(self, valeur: int):
        self.set_natural(self.CHG_CURRENT, valeur)

    @property
    def chg_rate(self):
        return self.get_natural(self.CHG_RATE)

    @chg_rate.setter
    def chg_rate(self, valeur):
        self.set_natural(self.CHG_RATE, valeur)

    @property
    def chg_energyadded(self):
        return self.get_natural(self.CHG_ENERGYADDED)

    @chg_energyadded.setter
    def chg_energyadded(self, valeur):
        self.set_natural(self.CHG_ENERGYADDED, valeur)

    @property
    def chg_minutestofull(self) -> int:
        return self.get_natural(self.CHG_MINUTESTOFULL)

    @chg_minutestofull.setter
    def chg_minutestofull(self, valeur: int):
        self.set_natural(self.CHG_MINUTESTOFULL, valeur)

    @property
    def chg_fastcharger(self) -> bool:
        return self.get_natural(self.CHG_FASTCHARGER)

    @chg_fastcharger.setter
    def chg_fastcharger(self, valeur: bool):
        self.set_natural(self.CHG_FASTCHARGER, valeur)

    @property
    def chg_cabletype(self) -> str:
        return self.get_natural(self.CHG_CABLETYPE)

    @chg_cabletype.setter
    def chg_cabletype(self, valeur: str):
        self.set_natural(self.CHG_CABLETYPE, valeur)

    # 6. NAVIGATION

    @property
    def oSNP(self):
        """Retourne le snapshot parent (Lazy Loading)."""
        if self._oSNP is None:
            from .clsSNP import clsSNP
            self._oSNP = clsSNP(snp_id=self.snp_id)
        return self._oSNP