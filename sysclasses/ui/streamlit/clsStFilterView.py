import streamlit as st
from sysclasses.ui.streamlit.clsStView import clsStView


class clsStFilterView(clsStView):
    """
    Composant filtres générique destiné à la sidebar Streamlit.

    Responsabilités :
        - Fournir un rendu dans st.sidebar via render()
        - Exposer les valeurs sélectionnées via la propriété valeurs
        - Persister l'état des filtres dans st.session_state

    Ce que cette classe ne fait PAS :
        - Pas de widget spécifique à un domaine métier
        - Pas de connaissance de clsTstatCharge ou de la charge Tesla
        - Pas de requête base de données

    Principe de persistance :
        Streamlit réexécute le script à chaque interaction.
        Les valeurs des widgets sont automatiquement persistées dans
        st.session_state par Streamlit via leur paramètre `key`.
        La propriété `valeurs` lit toujours depuis st.session_state
        pour garantir la cohérence entre réexécutions.

    Sous-classes attendues :
        Les sous-classes déclarent leurs widgets dans _do_render()
        en utilisant st.sidebar.* et en passant un `key` unique
        à chaque widget. Elles surchargent la propriété `valeurs`
        pour retourner un dict des valeurs courantes.

    Usage :
        class MesFiltres(clsStFilterView):
            def _do_render(self):
                st.sidebar.selectbox("Granularité", [...], key="granularite")

            @property
            def valeurs(self) -> dict:
                return {
                    "granularite": st.session_state.get("granularite", "mois"),
                }
    """

    def __init__(self):
        super().__init__()

    # --------------------------------------------------
    # Propriété publique — interface vers la page
    # --------------------------------------------------

    @property
    def valeurs(self) -> dict:
        """
        Retourne les valeurs courantes des filtres.
        DOIT être surchargée par les sous-classes.
        La page appelle cette propriété pour obtenir les paramètres
        à passer au controller.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} doit implémenter la propriété valeurs."
        )

    # --------------------------------------------------
    # Helper — bouton reset uniforme
    # --------------------------------------------------

    def _bouton_reset(self, cles: list[str], label: str = "Réinitialiser") -> None:
        """
        Affiche un bouton de réinitialisation des filtres dans la sidebar.
        Supprime les clés listées de st.session_state et force une réexécution.

        Paramètres :
            cles  : liste des clés session_state à supprimer
            label : texte du bouton
        """
        if st.sidebar.button(label):
            for cle in cles:
                st.session_state.pop(cle, None)
            st.rerun()