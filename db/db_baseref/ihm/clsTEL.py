from .clsIHM import clsIHM

class clsTEL(clsIHM):
    # 1. IDENTITÉ
    _table = "t_type_element_tel"
    _pk    = "tel_id"

    # 2. DICTIONNAIRE DES COLONNES
    TEL_ID         = "tel_id"
    TEL_CODE       = "tel_code"
    TEL_NOM        = "tel_nom"
    TEL_CREE_LE    = "tel_cree_le"
    TEL_MODIFIE_LE = "tel_modifie_le"

    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._tabELE = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if not self.tel_code:
            self.ogLog.error(f"TEL {self.tel_id} : Le code type élément est obligatoire.")
            erreurs.append("ERREUR : Le code type élément est obligatoire.")
            flag_error = True

        if not self.tel_nom:
            self.ogLog.error(f"TEL {self.tel_id} : Le nom du type élément est obligatoire.")
            erreurs.append("ERREUR : Le nom du type élément est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # 5. ACCÈS

    @property
    def tel_id(self) -> int:
        return self.get_natural(self.TEL_ID)

    @tel_id.setter
    def tel_id(self, valeur: int):
        self.set_natural(self.TEL_ID, valeur)

    @property
    def tel_code(self) -> str:
        return self.get_natural(self.TEL_CODE)

    @tel_code.setter
    def tel_code(self, valeur: str):
        self.set_natural(self.TEL_CODE, valeur)

    @property
    def tel_nom(self) -> str:
        return self.get_natural(self.TEL_NOM)

    @tel_nom.setter
    def tel_nom(self, valeur: str):
        self.set_natural(self.TEL_NOM, valeur)

    @property
    def tel_cree_le(self):
        return self.get_natural(self.TEL_CREE_LE)

    @property
    def tel_modifie_le(self):
        return self.get_natural(self.TEL_MODIFIE_LE)

    # 6. NAVIGATION

    @property
    def tabELE(self):
        """Éléments UI de ce type (Lazy Loading)."""
        if self._tabELE is None:
            from .clsELE import clsELE
            sql = (f"SELECT * FROM {clsELE._schema}.{clsELE._table} "
                   f"WHERE {clsELE.TEL_ID} = {self.ogEngine.placeholder}")
            self._tabELE = clsELE.DepuisResultat(self.ogEngine.execute_select(sql, (self.tel_id,)))
        return self._tabELE
