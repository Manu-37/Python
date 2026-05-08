# sysclasses/ui/qt/qt_controleur.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt
from sysclasses.ui.qt.qt_liste_vue import QtListeVue
from sysclasses.ui.qt.qt_fiche_vue import QtFicheVue
from sysclasses.exceptions import (
    ErreurValidationBloquante, AvertissementValidation
)


class QtControleur(QWidget):
    """
    Contrôleur générique pour toute entité CRUD.

    Usage minimal — déclarer dans la sous-classe :
        class EnvControleur(QtControleur):
            _classe_entite = clsENV
            _ordre_tri     = clsENV.ENV_CODE

    Variables de classe surchageables :
        _classe_entite : classe entité (obligatoire)
        _ordre_tri     : colonne de tri pour load_all() (défaut None)
        _afficher_crud : True par défaut
        _avec_fiche    : True par défaut — False si la zone basse
                         est une autre liste (ex: Job → Job_run_details)
        _ratio_initial : 0.5 — proportion liste/zone basse

    Paramètres __init__ (prioritaires sur les variables de classe) :
        afficher_crud  : bool
        ratio_initial  : float

    Hooks surchageables :
        _creer_liste_vue()        — injecter une QtListeVue spécialisée
        _creer_zone_basse()       — injecter n'importe quel QWidget
                                    (fiche, autre liste, graphique...)
        _avant_enregistrement()   — avant insert/update/delete
        _apres_enregistrement()   — après commit réussi
        _on_selection(ligne)      — réaction à la sélection d'une ligne
    """

    _classe_entite = None
    _ordre_tri     = None
    _afficher_crud = True
    _avec_fiche    = True
    _ratio_initial = 0.5

    def __init__(self, afficher_crud: bool = None,
                 ratio_initial: float = None, parent=None):
        super().__init__(parent)

        if self._classe_entite is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} doit définir _classe_entite."
            )

        # Paramètres __init__ prioritaires sur variables de classe
        if afficher_crud is not None:
            self._afficher_crud = afficher_crud
        if ratio_initial is not None:
            self._ratio_initial = ratio_initial

        self._valeurs_originales: dict | None = None
        self._metadata = self._classe_entite.get_metadata()

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

        self._vue_liste = self._creer_liste_vue()
        self._zone_basse = self._creer_zone_basse()

        self._separateur.addWidget(self._vue_liste)
        self._separateur.addWidget(self._zone_basse)
        self._separateur.setStretchFactor(0, 1)
        self._separateur.setStretchFactor(1, 1)

        # Ratio appliqué au premier affichage
        self._premier_affichage = True

        disposition.addWidget(self._separateur)

    def showEvent(self, event):
        """Applique le ratio liste/zone basse au premier affichage."""
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
        """Surcharger pour injecter une QtListeVue spécialisée."""
        return QtListeVue(afficher_crud=self._afficher_crud)

    def _creer_zone_basse(self) -> QWidget:
        """
        Retourne le widget affiché sous la liste.

        Par défaut : une QtFicheVue si _avec_fiche=True,
                     un QWidget vide sinon (la sous-classe le peuple
                     dans _on_selection()).

        Surcharger pour mettre une autre liste, un graphique, etc.
        """
        if self._avec_fiche:
            self._vue_fiche = QtFicheVue()
            return self._vue_fiche
        else:
            self._vue_fiche = None
            contenant = QWidget()
            self._disposition_zone_basse = QVBoxLayout(contenant)
            self._disposition_zone_basse.setContentsMargins(0, 0, 0, 0)
            return contenant

    # ------------------------------------------------------------------
    # Connexion des signaux
    # ------------------------------------------------------------------

    def _connecter_signaux(self):
        self._vue_liste.demande_ajout.connect(self._on_ajout)
        self._vue_liste.demande_modification.connect(self._on_modification)
        self._vue_liste.demande_suppression.connect(self._on_suppression)
        self._vue_liste.demande_consultation.connect(self._on_consultation)
        self._vue_liste.itemSelectionChanged = self._on_selection

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
        """
        Charge les métadonnées, initialise la fiche et la liste.
        Appelé une seule fois à la construction.
        """
        colonnes       = self._metadata.columns
        colonnes_liste = [
            col for col in colonnes
            if self._metadata.get_column(col
                )["canonical_type"][0] != "BINARY"
        ]
        libelles_liste = [
            self._metadata.get_col_label(col)
            for col in colonnes_liste
        ]

        # Initialisation de la fiche si elle existe
        if self._vue_fiche:
            cols_meta = [self._metadata.get_column(col) for col in colonnes]
            self._vue_fiche.definir_champs(cols_meta)

            # Alimentation des FK
            entite_temp = self._classe_entite()
            for col in cols_meta:
                if col.get("is_fk"):
                    choix = entite_temp.get_list_FK(col["name"])
                    self._vue_fiche.charger_fk(col["name"], choix)

            self._vue_fiche.setVisible(False)

        self._colonnes_liste  = colonnes_liste
        self._libelles_liste  = libelles_liste

        # Chargement initial de la liste
        self._vue_liste.charger(colonnes_liste, libelles_liste, [])
        self._rafraichir_liste()

    def _rafraichir_liste(self):
        """Recharge les données sans reconstruire le widget."""
        lignes = self._classe_entite.load_all(order_by=self._ordre_tri)
        self._vue_liste.charger(
            self._colonnes_liste,
            self._libelles_liste,
            lignes
        )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _masquer_fiche(self):
        if self._vue_fiche:
            self._vue_fiche.setVisible(False)

    def _afficher_fiche(self, mode: str, valeurs: dict | None = None):
        """
        Charge et affiche la fiche.
        Passe par les getters de l'entité pour le décodage BINARY.
        """
        if not self._vue_fiche:
            return

        if valeurs:
            entite = self._classe_entite(**valeurs)
            valeurs_affichage = {
                col: getattr(entite, col, None)
                for col in self._metadata.columns
            }
        else:
            valeurs_affichage = None

        self._vue_fiche.charger(mode, valeurs_affichage)
        self._vue_fiche.setVisible(True)

    # ------------------------------------------------------------------
    # Hook sélection — à surcharger pour zone basse personnalisée
    # ------------------------------------------------------------------

    def _on_selection(self, ligne: dict):
        """
        Appelé à chaque sélection d'une ligne.
        Par défaut : ne fait rien (la fiche s'ouvre via les boutons).
        Surcharger pour réagir à la sélection — ex: afficher une
        sous-liste dans la zone basse (_avec_fiche=False).
        """
        pass

    # ------------------------------------------------------------------
    # Actions CRUD
    # ------------------------------------------------------------------

    def _on_ajout(self):
        self._valeurs_originales = None
        self._afficher_fiche(QtFicheVue.MODE_AJOUT)

    def _on_modification(self, ligne: dict):
        self._valeurs_originales = ligne
        self._afficher_fiche(QtFicheVue.MODE_MODIFICATION, ligne)

    def _on_suppression(self, ligne: dict):
        self._valeurs_originales = ligne
        self._afficher_fiche(QtFicheVue.MODE_SUPPRESSION, ligne)

    def _on_consultation(self, ligne: dict):
        self._afficher_fiche(QtFicheVue.MODE_CONSULTATION, ligne)

    def _on_enregistrement(self, valeurs: dict):
        mode = self._vue_fiche._mode

        if mode == QtFicheVue.MODE_SUPPRESSION:
            reponse = QMessageBox.question(
                self, "Confirmation",
                "Voulez-vous supprimer cet enregistrement ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reponse != QMessageBox.StandardButton.Yes:
                return

        try:
            if mode == QtFicheVue.MODE_AJOUT:
                entite = self._classe_entite()
                self._peupler_entite(entite, valeurs)
                self._avant_enregistrement(entite)
                entite.insert()

            elif mode == QtFicheVue.MODE_MODIFICATION:
                entite = self._classe_entite(**self._valeurs_originales)
                self._peupler_entite(entite, valeurs)
                self._avant_enregistrement(entite)
                entite.update()

            elif mode == QtFicheVue.MODE_SUPPRESSION:
                entite = self._classe_entite(**self._valeurs_originales)
                self._avant_enregistrement(entite)
                entite.delete()

            entite.ogEngine.commit()
            self._apres_enregistrement(entite)

        except ErreurValidationBloquante as e:
            QMessageBox.critical(self, "Erreur de validation", str(e))
            return

        except AvertissementValidation as e:
            entite.ogEngine.commit()
            QMessageBox.warning(self, "Avertissement", str(e))

        except Exception as e:
            try:
                entite.ogEngine.rollback()
            except Exception:
                pass
            QMessageBox.critical(self, "Erreur", f"Échec :\n{e}")
            return

        self._rafraichir_liste()
        self._masquer_fiche()

    # ------------------------------------------------------------------
    # Peuplement de l'entité
    # ------------------------------------------------------------------

    def _peupler_entite(self, entite, valeurs: dict):
        """
        Affecte les valeurs aux setters de l'entité.
        Les setters gèrent le chiffrement BINARY — transparent ici.
        """
        for nom, valeur in valeurs.items():
            col = self._metadata.get_column(nom)
            if col["is_identity"] or (col["is_pk"] and not col.get("is_fk")):
                continue
            setattr(entite, nom, valeur)

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def _avant_enregistrement(self, entite):
        """Avant insert/update/delete — équivalent _before_save()."""
        pass

    def _apres_enregistrement(self, entite):
        """Après commit réussi — équivalent _after_save()."""
        pass