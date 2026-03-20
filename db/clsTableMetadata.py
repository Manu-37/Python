class clsTableMetadata:
    """
    Container dynamique des métadonnées d'une table.

    Chaque colonne du dict interne porte les champs suivants :
        name, db_type, canonical_type, max_length, precision, scale,
        nullable, is_pk, is_identity, identity_generation, default,
        is_fk, fk_schema, fk_table, fk_value_col

    Les 4 derniers champs (is_fk, fk_*) valent None si la colonne
    n'est pas une clé étrangère. Ils sont alimentés par clsSQL_Postgre
    via les catalogues système — clsTableMetadata n'y touche pas.
    """

    def __init__(self, table_name: str, canonical_dict: list[dict]):
        self.table_name = table_name
        self._metadata  = canonical_dict

    @property
    def columns(self) -> list[str]:
        return [col["name"] for col in self._metadata]

    @property
    def primary_keys(self) -> list[str]:
        return [col["name"] for col in self._metadata if col["is_pk"]]

    @property
    def insertable_columns(self):
        return [
            col["name"]
            for col in self._metadata
            if not col["is_identity"]
        ]

    @property
    def updatable_columns(self):
        return [
            col["name"]
            for col in self._metadata
            if not col["is_pk"]
            and not col["is_identity"]
        ]

    @property
    def auto_increment_pk(self):
        for col in self._metadata:
            if col["is_pk"] and col["is_identity"]:
                return col["name"]
        return None

    @property
    def fk_columns(self) -> list[str]:
        """Retourne la liste des colonnes qui sont des FK."""
        return [col["name"] for col in self._metadata if col.get("is_fk")]

    @property
    def display_columns(self) -> list[str]:
        """
        Retourne les colonnes à afficher dans une liste standard.
        Exclut :
            - les colonnes identity (PK auto-générées)
            - les colonnes BINARY (BYTEA chiffré — illisible et sensible)
        TODO : prévoir un mécanisme de sélection/masquage/substitution
               de colonnes par entité (ex: FK affichée comme libellé plutôt qu'ID).
        """
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

    # --------------------------------------------------
    # Calcul de largeur pixel pour une colonne
    # --------------------------------------------------

    def get_col_width(self, col_name: str) -> int:
        """
        Calcule la largeur en pixels d'une colonne selon son type canonique.

        Coefficients :
          NUMERIC  → (precision ou 10) * 9 + 20   min=60   max=160
          STRING   → max_length * 8               min=80   max=600
          BOOLEAN  → 60  (fixe)
          TEMPORAL → 180 (fixe)
          UUID     → 280 (fixe)
          JSON     → 600 (fixe)
          BINARY   → 600 (fixe)
          OTHER    → 120 (fixe)
        """
        col  = self.get_column(col_name)
        ctype = col["canonical_type"]
        family = ctype[0] if isinstance(ctype, tuple) else "OTHER"

        if family == "NUMERIC":
            precision = col["precision"] or 10
            width = precision * 9 + 20
            return max(60, min(width, 160))

        if family == "STRING":
            max_length = col["max_length"] or 20
            width = max_length * 8
            return max(80, min(width, 600))

        if family == "BOOLEAN":
            return 60

        if family == "TEMPORAL":
            return 180

        if family == "UUID":
            return 280

        if family in ("JSON", "BINARY"):
            return 600

        # OTHER ou non mappé
        return 120

    # --------------------------------------------------
    # Cadrage horizontal pour une colonne
    # --------------------------------------------------

    def get_col_anchor(self, col_name: str) -> str:
        """
        Retourne l'ancrage horizontal d'une colonne :
          "e" (droite) pour les numériques
          "w" (gauche) pour tout le reste
        """
        col   = self.get_column(col_name)
        ctype = col["canonical_type"]
        family = ctype[0] if isinstance(ctype, tuple) else "OTHER"

        return "e" if family == "NUMERIC" else "w"