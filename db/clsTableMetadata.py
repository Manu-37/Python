class clsTableMetadata:
    """
    Container dynamique des métadonnées d'une table.

    Chaque colonne du dict interne porte les champs suivants :
        name, db_type, canonical_type, max_length, precision, scale,
        nullable, is_pk, is_identity, identity_generation, default,
        comment,
        is_fk, fk_schema, fk_table, fk_value_col

    Les 4 derniers champs (is_fk, fk_*) valent None si la colonne
    n'est pas une clé étrangère. Ils sont alimentés par clsSQL_Postgre
    via les catalogues système — clsTableMetadata n'y touche pas.

    Enrichissement IHM (optionnel) :
        Si clsDBMetadata trouve des données référentiel pour la table,
        les libellés, tooltips et largeurs sont enrichis depuis ihm.v_col.
        Sinon, le comportement pg_catalog reste le fallback.

    Convention comment PostgreSQL pour get_col_label() / get_col_tooltip() :
        "Label|Description longue utilisée comme tooltip"
    """

    _LARGEUR_PX_PAR_CAR = 12

    def __init__(self, table_name: str, canonical_dict: list[dict]):
        self.table_name = table_name
        self._metadata  = canonical_dict
        self._ihm       = None  # initialisé via enrichir_ihm() par clsEntity_ABS

    def enrichir_ihm(self, db_code: str):
        """
        Déclenche l'enrichissement depuis le référentiel IHM.
        Appelé par clsEntity_ABS après construction — jamais dans __init__.
        L'entité connaît son db_code via _DB_SYMBOLIC_NAME.
        Sans appel à cette méthode, comportement pg_catalog inchangé.
        """
        if not db_code:
            return
        from db.clsDBMetadata import clsDBMetadata
        self._ihm = clsDBMetadata(db_code, self.table_name)

    # ------------------------------------------------------------------
    # Colonnes
    # ------------------------------------------------------------------

    @property
    def columns(self) -> list[str]:
        return [col["name"] for col in self._metadata]

    @property
    def primary_keys(self) -> list[str]:
        return [col["name"] for col in self._metadata if col["is_pk"]]

    @property
    def insertable_columns(self):
        return [col["name"] for col in self._metadata if not col["is_identity"]]

    @property
    def updatable_columns(self):
        return [
            col["name"] for col in self._metadata
            if not col["is_pk"] and not col["is_identity"]
        ]

    @property
    def auto_increment_pk(self):
        for col in self._metadata:
            if col["is_pk"] and col["is_identity"]:
                return col["name"]
        return None

    @property
    def fk_columns(self) -> list[str]:
        return [col["name"] for col in self._metadata if col.get("is_fk")]

    @property
    def display_columns(self) -> list[str]:
        return [
            col["name"] for col in self._metadata
            if not col["is_identity"]
            and col["canonical_type"][0] != "BINARY"
        ]

    def get_column(self, col_name: str) -> dict:
        for col in self._metadata:
            if col["name"] == col_name:
                return col
        raise KeyError(f"Colonne '{col_name}' non trouvée")

    # ------------------------------------------------------------------
    # Largeur pixel
    # ------------------------------------------------------------------

    def get_col_width(self, col_name: str) -> int:
        # Priorité 1 : référentiel IHM (col_largeur en nb de caractères)
        if self._ihm and self._ihm.est_disponible:
            ref = self._ihm.colonnes.get(col_name)
            if ref and ref.get("col_largeur"):
                return ref["col_largeur"] * self._LARGEUR_PX_PAR_CAR

        # Fallback : calcul pg_catalog
        col   = self.get_column(col_name)
        ctype = col["canonical_type"]
        family = ctype[0] if isinstance(ctype, tuple) else "OTHER"

        if family == "NUMERIC":
            subtype = ctype[1] if isinstance(ctype, tuple) else ""
            if subtype == "SMALLINT":  return 70
            if subtype in ("INTEGER", "SERIAL"):  return 100
            if subtype in ("BIGINT", "BIGSERIAL"): return 140
            precision = col["precision"] or 10
            return max(60, min(precision * 9 + 20, 160))

        if family == "STRING":
            max_length = col["max_length"] or 30
            return max(80, min(max_length * 8, 600))

        if family == "BOOLEAN": return 60
        if family == "TEMPORAL": return 180
        if family == "UUID": return 280
        if family in ("JSON", "BINARY"): return 600
        return 120

    def get_col_largeur_car(self, col_name: str) -> int | None:
        """Largeur brute en nb de caractères depuis le référentiel IHM, ou None."""
        if self._ihm and self._ihm.est_disponible:
            ref = self._ihm.colonnes.get(col_name)
            if ref:
                return ref.get("col_largeur")
        return None

    # ------------------------------------------------------------------
    # Cadrage horizontal
    # ------------------------------------------------------------------

    def get_col_anchor(self, col_name: str) -> str:
        col    = self.get_column(col_name)
        ctype  = col["canonical_type"]
        family = ctype[0] if isinstance(ctype, tuple) else "OTHER"
        return "e" if family == "NUMERIC" else "w"

    # ------------------------------------------------------------------
    # Libellés et tooltips
    # ------------------------------------------------------------------

    @staticmethod
    def _col_name_fallback(col_name: str) -> str:
        return col_name.replace("_", " ").title()

    def _comment_label(self, col_name: str) -> str | None:
        """Partie gauche du comment pg_catalog si '|' présent."""
        col     = self.get_column(col_name)
        comment = col.get("comment")
        if comment and "|" in comment:
            return comment.split("|", 1)[0].strip()
        return None

    def _comment_tooltip(self, col_name: str) -> str | None:
        """Partie droite du comment pg_catalog si '|', sinon comment entier."""
        col     = self.get_column(col_name)
        comment = col.get("comment")
        if not comment:
            return None
        if "|" in comment:
            return comment.split("|", 1)[1].strip()
        return comment

    def get_col_label(self, col_name: str) -> str:
        """Label long — pour QtFicheVue et anciens écrans."""
        if self._ihm and self._ihm.est_disponible:
            ref = self._ihm.colonnes.get(col_name)
            if ref and ref.get("lco_label"):
                return ref["lco_label"]
        return self._comment_label(col_name) or self._col_name_fallback(col_name)

    def get_col_label_court(self, col_name: str) -> str:
        """Label court — pour QtListeVue, en-têtes de colonnes."""
        if self._ihm and self._ihm.est_disponible:
            ref = self._ihm.colonnes.get(col_name)
            if ref and ref.get("lco_label_court"):
                return ref["lco_label_court"]
        return self._comment_label(col_name) or self._col_name_fallback(col_name)

    def get_col_tooltip(self, col_name: str) -> str | None:
        """Tooltip — commun aux deux vues."""
        if self._ihm and self._ihm.est_disponible:
            ref = self._ihm.colonnes.get(col_name)
            if ref and ref.get("lco_tooltip"):
                return ref["lco_tooltip"]
        return self._comment_tooltip(col_name)

    # ------------------------------------------------------------------
    # Libellés de relation (table/onglet)
    # ------------------------------------------------------------------

    @property
    def rel_label(self) -> str | None:
        if self._ihm and self._ihm.est_disponible and self._ihm.relation:
            return self._ihm.relation.get("lre_label")
        return None

    @property
    def rel_tooltip(self) -> str | None:
        if self._ihm and self._ihm.est_disponible and self._ihm.relation:
            return self._ihm.relation.get("lre_tooltip")
        return None
