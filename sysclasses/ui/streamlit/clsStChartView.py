import streamlit as st
import plotly.graph_objects as go
from sysclasses.ui.streamlit.clsStView import clsStView


class clsStChartView(clsStView):
    """
    Composant graphique générique basé sur Plotly Graph Objects.

    Responsabilités :
        - Fournir une figure Plotly vide prête à l'emploi (_creer_figure)
        - Afficher la figure via st.plotly_chart()
        - Gérer le cas "pas de données" de façon uniforme

    Ce que cette classe ne fait PAS :
        - Pas de connaissance du domaine métier (charge, conduite, etc.)
        - Pas de requête base de données
        - Pas de mise en forme spécifique à un type de graphique

    Sous-classes attendues :
        Les sous-classes reçoivent leurs données via __init__()
        et construisent la figure dans _do_render() en appelant
        _creer_figure() puis en ajoutant leurs traces Plotly.

    Paramètres :
        titre       : titre affiché au-dessus du graphique (optionnel)
        hauteur     : hauteur en pixels (défaut 400)
        width : si 'stretch', occupe toute la largeur (défaut stretch)

    Usage :
        class MonGraphique(clsStChartView):
            def __init__(self, data):
                super().__init__(titre="Mon graphique", hauteur=400)
                self._data = data

            def _do_render(self):
                if not self._data:
                    self._afficher_vide("Aucune donnée disponible.")
                    return
                fig = self._creer_figure()
                fig.add_trace(go.Bar(x=..., y=...))
                self._afficher_figure(fig)
    """

    def __init__(
        self,
        titre   : str  = "",
        hauteur : int  = 400,
        width   : str = 'stretch',
    ):
        super().__init__()
        self._titre               = titre
        self._hauteur             = hauteur
        self._width = width

    # --------------------------------------------------
    # Helpers protégés — à disposition des sous-classes
    # --------------------------------------------------

    def _creer_figure(self) -> go.Figure:
        """
        Retourne une figure Plotly vide avec la mise en forme de base.
        Les sous-classes y ajoutent leurs traces (add_trace, add_bar, etc.).
        """
        fig = go.Figure()
        fig.update_layout(
            title      = self._titre,
            height     = self._hauteur,
            margin     = dict(l=40, r=20, t=40 if self._titre else 20, b=40),
            showlegend = True,
        )
        return fig

    def _afficher_figure(self, fig: go.Figure) -> None:
        """Affiche la figure Plotly dans la page Streamlit."""
        st.plotly_chart(fig, width=self._width)

    def _afficher_vide(self, message: str = "Aucune donnée à afficher.") -> None:
        """
        Affiche un message uniforme quand les données sont absentes.
        Appelé par les sous-classes en lieu et place de _afficher_figure().
        """
        st.info(message)