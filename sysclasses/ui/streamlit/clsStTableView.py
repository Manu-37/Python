import streamlit as st
import pandas as pd
from sysclasses.ui.streamlit.clsStView import clsStView


class clsStTableView(clsStView):
    """
    Composant tableau générique basé sur st.dataframe().

    Responsabilités :
        - Convertir list[dict] en DataFrame pandas
        - Appliquer la configuration des colonnes (labels, largeurs, alignements)
        - Afficher le tableau via st.dataframe()
        - Gérer le cas "pas de données" de façon uniforme

    Ce que cette classe ne fait PAS :
        - Pas de connaissance du domaine métier
        - Pas de requête base de données
        - Pas de logique de filtrage

    La configuration des colonnes suit le format des dicts UI_* de clsTstatCharge :
        { nom_colonne: {"label": str, "width": int, "anchor": "w"|"e"} }

    "anchor" contrôle l'alignement :
        "w" (west)  → aligné à gauche  (texte, libellés)
        "e" (east)  → aligné à droite  (nombres)

    Paramètres :
        col_config  : dict de configuration des colonnes (format UI_* de clsTstatCharge)
                      Si None, toutes les colonnes sont affichées sans mise en forme.
        hauteur     : hauteur du tableau en pixels (défaut 400)
        cles        : liste des colonnes à afficher (et leur ordre).
                      Si None, toutes les colonnes du dict col_config sont affichées.

    Usage :
        class MonTableau(clsStTableView):
            def __init__(self, data):
                super().__init__(
                    col_config = MaClasse.UI_MON_DICT,
                    hauteur    = 300,
                )
                self._data = data

            def _do_render(self):
                self._afficher_tableau(self._data)
    """

    def __init__(
        self,
        col_config : dict | None = None,
        hauteur    : int         = 400,
        cles       : list | None = None,
    ):
        super().__init__()
        self._col_config = col_config or {}
        self._hauteur    = hauteur
        self._cles       = cles  # ordre et sélection des colonnes

    # --------------------------------------------------
    # Helpers protégés — à disposition des sous-classes
    # --------------------------------------------------

    def _afficher_tableau(self, data: list[dict]) -> None:
        """
        Convertit data en DataFrame et l'affiche avec st.dataframe().
        Gère le cas données vides de façon uniforme.
        """
        if not data:
            self._afficher_vide()
            return

        df = pd.DataFrame(data)

        # Sélection et ordre des colonnes
        colonnes_a_afficher = self._colonnes_a_afficher(df)
        df = df[colonnes_a_afficher]

        # Construction de la configuration Streamlit des colonnes
        st_col_config = self._build_st_col_config(colonnes_a_afficher)

        st.dataframe(
            df,
            height          = self._hauteur,
            use_container_width = True,
            column_config   = st_col_config if st_col_config else None,
            hide_index      = True,
        )

    def _colonnes_a_afficher(self, df: pd.DataFrame) -> list[str]:
        """
        Retourne la liste ordonnée des colonnes à afficher.

        Priorité :
            1. self._cles si fourni
            2. Colonnes du col_config présentes dans le DataFrame
            3. Toutes les colonnes du DataFrame si pas de config
        """
        if self._cles:
            return [c for c in self._cles if c in df.columns]
        if self._col_config:
            return [c for c in self._col_config if c in df.columns]
        return list(df.columns)

    def _build_st_col_config(self, colonnes: list[str]) -> dict:
        """
        Construit le dict column_config attendu par st.dataframe()
        depuis le format UI_* de clsTstatCharge.

        Format UI_* : { nom_col: {"label": str, "width": int, "anchor": "w"|"e"} }
        Format st   : { nom_col: st.column_config.Column(label, width) }

        L'alignement ("anchor") est transmis via le paramètre TextColumn/NumberColumn.
        Une colonne numérique (anchor "e") devient NumberColumn.
        Une colonne texte   (anchor "w") devient TextColumn.
        """
        if not self._col_config:
            return {}

        config = {}
        for col in colonnes:
            meta = self._col_config.get(col)
            if not meta:
                continue

            label  = meta.get("label", col)
            width  = meta.get("width", None)
            anchor = meta.get("anchor", "w")

            if anchor == "e":
                config[col] = st.column_config.NumberColumn(
                    label = label,
                    width = width,
                )
            else:
                config[col] = st.column_config.TextColumn(
                    label = label,
                    width = width,
                )
        return config

    def _afficher_vide(self, message: str = "Aucune donnée à afficher.") -> None:
        """Affiche un message uniforme quand les données sont absentes."""
        st.info(message)