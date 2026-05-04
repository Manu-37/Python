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

    Convention comment PostgreSQL pour get_col_label() / get_col_tooltip() :
        "Label court|Description longue utilisée comme tooltip"
        ─────────────────────────────────────────────────────
        Si le comment contient '|', la partie gauche est le label d'affichage
        et la partie droite le tooltip.
        Si le comment ne contient pas '|', tout le comment devient le tooltip
        et le label est dérivé du nom de la colonne (fallback).
        Si le comment est absent (None), label et tooltip sont tous deux
        dérivés du nom de colonne.

    Exemple SQL :
        COMMENT ON COLUMN mv_charge_sessions.soc_debut_pct
            IS 'SOC début|% batterie au premier snapshot de la session';
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
            subtype = ctype[1] if isinstance(ctype, tuple) else ""
            if subtype == "SMALLINT":
                return 70          # 5 chiffres max
            if subtype in ("INTEGER", "SERIAL"):
                return 100         # 10 chiffres max
            if subtype in ("BIGINT", "BIGSERIAL"):
                return 140         # 19 chiffres max
            # DECIMAL / NUMERIC → precision est bien en chiffres décimaux
            precision = col["precision"] or 10
            width = precision * 9 + 20
            return max(60, min(width, 160))


        if family == "STRING":
            max_length = col["max_length"] or 30
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

    # --------------------------------------------------
    # Label d'affichage et tooltip
    # --------------------------------------------------

    @staticmethod
    def _col_name_fallback(col_name: str) -> str:
        """Dérive un label lisible depuis un nom de colonne snake_case."""
        return col_name.replace("_", " ").title()

    def get_col_label(self, col_name: str) -> str:
        """
        Retourne le label court d'affichage pour une colonne.

        Priorité :
          1. Partie gauche du comment si celui-ci contient '|'
             ex: comment = "SOC début|% batterie au 1er snapshot"  → "SOC début"
          2. Fallback : nom de colonne humanisé
             ex: "soc_debut_pct" → "Soc Debut Pct"

        Note : si le comment existe mais ne contient pas '|', il est traité
        comme tooltip uniquement (phrase longue) — le fallback nom s'applique
        alors au label.  Cela évite qu'une phrase longue polluée les headers.
        """
        col     = self.get_column(col_name)
        comment = col.get("comment")

        if comment and "|" in comment:
            return comment.split("|", 1)[0].strip()

        return self._col_name_fallback(col_name)

    def get_col_tooltip(self, col_name: str) -> str | None:
        """
        Retourne le texte de tooltip pour une colonne, ou None si absent.

        Priorité :
          1. Partie droite du comment si celui-ci contient '|'
             ex: comment = "SOC début|% batterie au 1er snapshot"
                 → "% batterie au 1er snapshot"
          2. Comment entier s'il n'y a pas de '|'
             (phrase descriptive directement utilisable comme tooltip)
          3. None si pas de comment
        """
        col     = self.get_column(col_name)
        comment = col.get("comment")

        if not comment:
            return None

        if "|" in comment:
            return comment.split("|", 1)[1].strip()

        return comment