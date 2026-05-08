# sysclasses/ui/qt/qt_controleur.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt
from sysclasses.clsLOG import clsLOG
from sysclasses.ui.qt.qt_liste_vue import QtListeVue
from sysclasses.ui.qt.qt_fiche_vue import QtFicheVue
from sysclasses.exceptions import (
    ErreurValidationBloquante, AvertissementValidation
)


class QtControleur(QWidget):
    """
    Contrôleur générique pour toute entité CRUD.

    Respecte le pattern MVC :
        - La vue (QtFicheVue) affiche et saisit, émet des signaux
        - Le contrôleur orchestre le CRUD via l'objet entité
        - L'entité porte ses données, sa validation et son chiffrement

    Usage minimal :
        class EnvControleur(QtControleur):
            _classe_entite = clsENV
            _ordre_tri     = clsENV.ENV_CODE

    Variables de classe surchageables :
        _classe_entite  : classe entité (obligatoire)
        _ordre_tri      : colonne de tri pour load_all()
        _afficher_crud  : True par défaut
        _avec_fiche     : True — False si zone basse personnalisée
        _ratio_initial  : 0.5 — proportion liste/zone basse

    Paramètres __init__ :
        afficher_crud   : bool — prioritaire sur variable de classe
        ratio_initial   : float — prioritaire sur variable de classe
        on_ouvrir_fiche : callable(label, widget) — si fourni, la fiche
                          s'ouvre dans un nouvel onglet externe

    Hooks surchageables :
        _creer_liste_vue()
        _creer_zone_basse()
        _creer_fiche_vue()
        _instancier_entite(ligne)
        _avant_enregistrement(entite)
        _apres_enregistrement(entite)
        _on_selection(ligne)
    """

    _classe_entite = None
    _ordre_tri     = None
    _afficher_crud = True
    _avec_fiche    = True
    _ratio_initial = 0.5

    def __init__(self, afficher_crud: bool = None,
                 ratio_initial: float = None,
                 on_ouvrir_fiche=None,
                 parent=None):
        super().__init__(parent)

        if self._classe_entite is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} doit définir _classe_entite."
            )

        if afficher_crud is not None:
            self._afficher_crud = afficher_crud
        if ratio_initial is not None:
            self._ratio_initial = ratio_initial

        self._log             = clsLOG()
        self._on_ouvrir_fiche = on_ouvrir_fiche
        self._entite_courante = None
        self._mode_courant    = None
        self._metadata        = self._classe_entite.get_metadata()

        self._construire_ui()
        self._connecter_signaux()
        self._initialiser()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _construire_ui(self):
        disposition = QVBoxLayout(self)
        disposition.setContentsMargins(0, 0, 0, 0)
        disposition.setSpacing(0)

        self._separateur = QSplitter(Qt.Orientation.Vertical)

        self._vue_liste  = self._creer_liste_vue()
        self._zone_basse = self._creer_zone_basse()

        self._separateur.addWidget(self._vue_liste)
        self._separateur.addWidget(self._zone_basse)
        self._separateur.setStretchFactor(0, 1)
        self._separateur.setStretchFactor(1, 1)

        self._premier_affichage = True
        disposition.addWidget(self._separateur)

    def showEvent(self, event):
        super().showEvent(event)
        if self._premier_affichage:
            self._premier_affichage = False
            hauteur = self._separateur.height()
            if hauteur > 1:
                h_liste = int(hauteur * self._ratio_initial)
                h_basse = hauteur - h_liste
                self._separateur.setSizes([h_liste, h_basse])

    # ------------------------------------------------------------------
    # Hooks création des vues
    # ------------------------------------------------------------------

    def _creer_liste_vue(self) -> QtListeVue:
        return QtListeVue(afficher_crud=self._afficher_crud)

    def _creer_zone_basse(self) -> QWidget:
        """
        Si on_ouvrir_fiche est fourni → pas de zone basse.
        Sinon → QtFicheVue sous la liste.
        """
        if self._on_ouvrir_fiche or not self._avec_fiche:
            self._vue_fiche = None
            contenant = QWidget()
            self._disposition_zone_basse = QVBoxLayout(contenant)
            self._disposition_zone_basse.setContentsMargins(0, 0, 0, 0)
            return contenant
        else:
            self._vue_fiche = self._creer_fiche_vue()
            return self._vue_fiche

    def _creer_fiche_vue(self) -> QtFicheVue:
        """Surcharger pour injecter une QtFicheVue spécialisée."""
        return QtFicheVue()

    # ------------------------------------------------------------------
    # Connexion des signaux
    # ------------------------------------------------------------------

    def _connecter_signaux(self):
        self._vue_liste.demande_ajout.connect(self._on_ajout)
        self._vue_liste.demande_modification.connect(self._on_modification)
        self._vue_liste.demande_suppression.connect(self._on_suppression)
        self._vue_liste.demande_consultation.connect(self._on_consultation)
        self._vue_liste._tableau.itemSelectionChanged.connect(
            lambda: self._on_selection(self._vue_liste.ligne_selectionnee)
        )

        if self._vue_fiche:
            self._vue_fiche.demande_enregistrement.connect(
                self._on_enregistrement
            )
            self._vue_fiche.demande_annulation.connect(
                self._masquer_fiche
            )

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _initialiser(self):
        colonnes       = self._metadata.columns
        colonnes_liste = [
            col for col in colonnes
            if self._metadata.get_column(col)["canonical_type"][0] != "BINARY"
        ]
        libelles_liste = [
            self._metadata.get_col_label(col)
            for col in colonnes_liste
        ]

        if self._vue_fiche:
            cols_meta = [self._metadata.get_column(col) for col in colonnes]
            self._vue_fiche.definir_champs(cols_meta)

            # Objet vide — accès à ogEngine via singleton clsDBAManager
            entite_temp = self._classe_entite()
            for col in cols_meta:
                if col.get("is_fk"):
                    choix = entite_temp.get_list_FK(col["name"])
                    self._vue_fiche.charger_fk(col["name"], choix)

            self._vue_fiche.setVisible(False)

        self._colonnes_liste = colonnes_liste
        self._libelles_liste = libelles_liste
        self._vue_liste.charger(colonnes_liste, libelles_liste, [])
        self._rafraichir_liste()

    def _rafraichir_liste(self):
        lignes = self._classe_entite.load_all(order_by=self._ordre_tri)
        self._vue_liste.charger(
            self._colonnes_liste,
            self._libelles_liste,
            lignes
        )

    # ------------------------------------------------------------------
    # Instanciation de l'entité — hook surchargeable
    # ------------------------------------------------------------------

    def _instancier_entite(self, ligne: dict = None):
        """
        Sans ligne → objet vide pour INSERT.
        Avec ligne → extrait uniquement la PK et relit depuis la DB.
        PK composite supportée — _pk peut être str ou list[str].
        """
        if ligne is None:
            return self._classe_entite()

        # Extrait uniquement la PK depuis la ligne
        pk = self._metadata.primary_keys  # liste de noms de colonnes PK
        criteres = {col: ligne[col] for col in pk}

        # Le constructeur avec la PK relit la ligne complète depuis la DB
        return self._classe_entite(**criteres)

    # ------------------------------------------------------------------
    # Navigation liste / fiche
    # ------------------------------------------------------------------

    def _masquer_fiche(self):
        if self._vue_fiche:
            self._vue_fiche.setVisible(False)

    def _afficher_fiche(self, mode: str, entite):
        """
        Affiche la fiche avec l'entité.
        Si on_ouvrir_fiche fourni → onglet externe.
        Sinon → sous la liste.
        """
        self._entite_courante = entite
        self._mode_courant    = mode

        if self._on_ouvrir_fiche:
            fiche     = self._creer_fiche_vue()
            cols_meta = [
                self._metadata.get_column(col)
                for col in self._metadata.columns
            ]
            fiche.definir_champs(cols_meta)

            entite_temp = self._classe_entite()
            for col in cols_meta:
                if col.get("is_fk"):
                    choix = entite_temp.get_list_FK(col["name"])
                    fiche.charger_fk(col["name"], choix)

            fiche.charger(mode, entite)

            fiche.demande_enregistrement.connect(
                lambda f=fiche: self._on_enregistrement_externe(f)
            )
            fiche.demande_annulation.connect(
                lambda f=fiche: self._fermer_onglet_fiche(f)
            )

            libelle = f"{self._classe_entite.__name__} — {mode}"
            self._on_ouvrir_fiche(libelle, fiche)
        else:
            self._vue_fiche.charger(mode, entite)
            self._vue_fiche.setVisible(True)

    # ------------------------------------------------------------------
    # Actions CRUD
    # ------------------------------------------------------------------

    def _on_ajout(self):
        entite = self._instancier_entite()
        self._afficher_fiche(QtFicheVue.MODE_AJOUT, entite)

    def _on_modification(self, ligne: dict):
        entite = self._instancier_entite(ligne)
        self._afficher_fiche(QtFicheVue.MODE_MODIFICATION, entite)

    def _on_suppression(self, ligne: dict):
        entite = self._instancier_entite(ligne)
        self._afficher_fiche(QtFicheVue.MODE_SUPPRESSION, entite)

    def _on_consultation(self, ligne: dict):
        entite = self._instancier_entite(ligne)
        self._afficher_fiche(QtFicheVue.MODE_CONSULTATION, entite)

    def _on_enregistrement(self):
        """Reçu depuis la fiche sous la liste."""
        self._executer_crud(self._entite_courante, self._mode_courant)

    def _on_enregistrement_externe(self, fiche: QtFicheVue):
        """Reçu depuis une fiche dans un onglet externe."""
        succes = self._executer_crud(fiche._entite, fiche._mode)
        if succes:
            self._fermer_onglet_fiche(fiche)

    def _executer_crud(self, entite, mode: str) -> bool:
        """
        Exécute l'opération CRUD sur l'entité.
        ctrl_valeurs() est appelé par insert()/update() — transparent ici.
        """
        if mode == QtFicheVue.MODE_SUPPRESSION:
            reponse = QMessageBox.question(
                self, "Confirmation",
                "Voulez-vous supprimer cet enregistrement ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reponse != QMessageBox.StandardButton.Yes:
                return False

        try:
            self._avant_enregistrement(entite)

            if mode == QtFicheVue.MODE_AJOUT:
                entite.insert()
            elif mode == QtFicheVue.MODE_MODIFICATION:
                entite.update()
            elif mode == QtFicheVue.MODE_SUPPRESSION:
                entite.delete()

            entite.ogEngine.commit()
            self._apres_enregistrement(entite)

        except ErreurValidationBloquante as e:
            QMessageBox.critical(self, "Erreur de validation", str(e))
            return False

        except AvertissementValidation as e:
            entite.ogEngine.commit()
            QMessageBox.warning(self, "Avertissement", str(e))

        except Exception as e:
            try:
                entite.ogEngine.rollback()
            except Exception:
                pass
            self._log.error(f"Échec opération CRUD : {e}")
            QMessageBox.critical(self, "Erreur", f"Échec :\n{e}")
            return False

        self._rafraichir_liste()
        self._masquer_fiche()
        return True

    # ------------------------------------------------------------------
    # Fermeture onglet fiche externe
    # ------------------------------------------------------------------

    def _fermer_onglet_fiche(self, fiche: QtFicheVue):
        """Remonte l'arbre des parents pour trouver le QTabWidget."""
        from PyQt6.QtWidgets import QTabWidget
        widget = fiche
        while widget is not None:
            parent = widget.parent()
            if isinstance(parent, QTabWidget):
                index = parent.indexOf(widget)
                if index >= 0:
                    parent.removeTab(index)
                return
            widget = parent

    # ------------------------------------------------------------------
    # Hook sélection
    # ------------------------------------------------------------------

    def _on_selection(self, ligne: dict):
        """Surcharger pour réagir à la sélection."""
        pass

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def _avant_enregistrement(self, entite):
        """Avant insert/update/delete."""
        pass

    def _apres_enregistrement(self, entite):
        """Après commit réussi."""
        pass