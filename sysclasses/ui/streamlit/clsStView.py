from sysclasses.clsLOG import clsLOG


class clsStView:
    """
    Classe de base commune à tous les composants Streamlit.

    Responsabilités :
        - Fournir self.log (clsLOG singleton, déjà initialisé par AppBootstrap)
        - Implémenter le patron Template Method via render()

    Ce que cette classe ne fait PAS :
        - Pas d'accès base de données
        - Pas de connaissance de clsDBAManager ou clsTstatCharge
        - Pas de gestion du cache Streamlit (c'est le rôle de cache.py)

    Patron Template Method :
        render() orchestre la séquence en trois temps.
        Les sous-classes surchargent _do_render() obligatoirement,
        et peuvent surcharger _before_render() / _after_render() si besoin.

    Usage :
        class MonComposant(clsStView):
            def _do_render(self):
                st.write("Mon contenu")

        composant = MonComposant()
        composant.render()
    """

    def __init__(self):
        # clsLOG() sans argument retourne le singleton existant.
        # AppBootstrap l'a déjà initialisé — aucun risque de re-initialisation.
        self.log = clsLOG()

    # --------------------------------------------------
    # Template Method — séquence publique
    # --------------------------------------------------

    def render(self) -> None:
        """
        Point d'entrée public appelé par la page Streamlit.
        Orchestre la séquence : before → do → after.
        Ne pas surcharger dans les sous-classes.
        """
        self._before_render()
        self._do_render()
        self._after_render()

    # --------------------------------------------------
    # Hooks — surchargeable selon besoin
    # --------------------------------------------------

    def _before_render(self) -> None:
        """
        Hook exécuté avant le rendu principal.
        Par défaut : rien. Surchargeable pour préparer l'état,
        valider les données, afficher un spinner, etc.
        """
        pass

    def _after_render(self) -> None:
        """
        Hook exécuté après le rendu principal.
        Par défaut : rien. Surchargeable pour afficher un footer,
        logger une métrique, nettoyer l'état, etc.
        """
        pass

    # --------------------------------------------------
    # Méthode abstraite — obligatoire dans les sous-classes
    # --------------------------------------------------

    def _do_render(self) -> None:
        """
        Contenu principal du composant. DOIT être surchargée.
        Lève NotImplementedError si appelée directement sur clsStView
        ou sur une sous-classe qui oublie de l'implémenter.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} doit implémenter _do_render()."
        )