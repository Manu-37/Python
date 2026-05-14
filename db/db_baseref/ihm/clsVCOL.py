from db.clsViewMixin import clsViewMixin
from .clsIHM        import clsIHM

class clsVCOL(clsViewMixin, clsIHM):
    # 1. IDENTITÉ
    _table = "v_col"
    _pk    = ["db_id", "col_nom", "lan_id"]

    # 2. VALIDATION (lecture seule — aucune validation métier)
    def ctrl_valeurs(self) -> tuple[bool, str]:
        return False, ""

    # 3. ACCÈS — getters uniquement, pas de setters

    @property
    def db_id(self) -> int:
        return self.get_natural("db_id")

    @property
    def db_code(self) -> str:
        return self.get_natural("db_code")

    @property
    def rel_nom(self) -> str:
        return self.get_natural("rel_nom")

    @property
    def col_id(self) -> int:
        return self.get_natural("col_id")

    @property
    def col_nom(self) -> str:
        return self.get_natural("col_nom")

    @property
    def col_largeur(self) -> int:
        return self.get_natural("col_largeur")

    @property
    def col_actif(self) -> bool:
        return self.get_natural("col_actif")

    @property
    def taf_code(self) -> str:
        return self.get_natural("taf_code")

    @property
    def lan_id(self) -> int:
        return self.get_natural("lan_id")

    @property
    def lco_label(self) -> str:
        return self.get_natural("lco_label")

    @property
    def lco_label_court(self) -> str:
        return self.get_natural("lco_label_court")

    @property
    def lco_tooltip(self) -> str:
        return self.get_natural("lco_tooltip")
