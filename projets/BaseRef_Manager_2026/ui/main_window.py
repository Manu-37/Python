# ui/main_window.py

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QTabWidget, QLabel, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from ui.theme import AppTheme
from ui.sidebar import Sidebar
from ui.views.gestion_bases import EnvControleur, BasControleur, BasEnvControleur
from ui.views.Tesla import VEHControleur, TTKControleur
from ui.views.Utilitaires import ChiffrementVue
from ui.views.Administration import JobControleur

# ------------------------------------------------------------------
# Définition de la navigation
# ------------------------------------------------------------------
# Format :
#   3-tuple (id, libelle, enfants) → section pliable (niveau N)
#   4-tuple (id, libelle, classe, singleton) → item feuille cliquable
#
# singleton=True  → fiche affichée SOUS la liste (un seul onglet)
# singleton=False → fiche dans un NOUVEL onglet
# classe=None     → placeholder temporaire
# ------------------------------------------------------------------

DEFINITION_MENU = [
    ("catalogue", "Catalogue", [
        ("environnements", "Environnements",         EnvControleur,    True),
        ("bases",          "Bases de données",       BasControleur,    True),
        ("bas_env",        "Paramétrages bases/env", BasEnvControleur, False),
    ]),
    ("tesla", "Tesla", [
        ("vehicules",      "Véhicules",              VEHControleur,    True),
        ("tokens",         "Tokens Tesla",           TTKControleur,    False),
    ]),
    ("utilitaires", "Utilitaires", [
        ("chiffrement",    "Chiffrement",            ChiffrementVue,   True),
    ]),
    ("administration", "Administration", [
        ("cron",           "Tâches planifiées",      JobControleur,    True),
    ]),
]


class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application.

    Structure :
        QMenuBar                    — Fichier, ?
        QSplitter horizontal
            Sidebar                 — accordion piloté par DEFINITION_MENU
            QTabWidget central      — onglets de contenu

    Logique des onglets :
        Clic sidebar       → toujours singleton (un seul onglet liste par item)
        Fiche depuis liste → sous la liste si singleton=True
                          → nouvel onglet si singleton=False
    """

    def __init__(self):
        super().__init__()

        # Registre des onglets liste ouverts : identifiant → index onglet
        self._onglets_liste: dict[str, int] = {}

        self._construire_fenetre()
        self._construire_menu()
        self._construire_zone_centrale()
        self._construire_sidebar()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _construire_fenetre(self):
        self.setWindowTitle("BaseRef Manager 2026")
        self.resize(1280, 960)
        self.setMinimumSize(1024, 768)

    def _construire_menu(self):
        barre_menu = self.menuBar()
        self._ajouter_menu(barre_menu, "Fichier", [
            ("Quitter", "Ctrl+Q", self.close),
        ])
        self._ajouter_menu(barre_menu, "?", [
            ("À propos", None, self._on_apropos),
        ])

    def _ajouter_menu(self, barre_menu, titre: str, items: list):
        """
        Factorisation de la construction d'un menu.
        items : liste de tuples (libelle, raccourci_ou_None, callback)
        """
        menu = barre_menu.addMenu(titre)
        for libelle, raccourci, callback in items:
            action = QAction(libelle, self)
            if raccourci:
                action.setShortcut(raccourci)
            action.triggered.connect(callback)
            menu.addAction(action)

    def _construire_zone_centrale(self):
        """
        Construit le layout central : sidebar (gauche) + onglets (droite).
        Un QWidget neutre occupe provisoirement la place de la sidebar —
        il sera remplacé par la vraie sidebar dans _construire_sidebar().
        """
        widget_racine  = QWidget()
        disposition    = QHBoxLayout(widget_racine)
        disposition.setContentsMargins(0, 0, 0, 0)
        disposition.setSpacing(0)

        self._separateur = QSplitter(Qt.Orientation.Horizontal)

        # Placeholder sidebar — remplacé dans _construire_sidebar()
        emplacement_sidebar = QWidget()
        self._separateur.addWidget(emplacement_sidebar)

        # Zone à onglets
        self._boite_onglets = QTabWidget()
        self._boite_onglets.setTabsClosable(True)
        self._boite_onglets.tabCloseRequested.connect(self._on_fermeture_onglet)
        self._separateur.addWidget(self._boite_onglets)

        # Sidebar fixe, zone onglets extensible
        self._separateur.setStretchFactor(0, 0)
        self._separateur.setStretchFactor(1, 1)

        disposition.addWidget(self._separateur)
        self.setCentralWidget(widget_racine)

    def _construire_sidebar(self):
        """
        Construit la sidebar depuis DEFINITION_MENU et remplace le placeholder.
        Séparé de _construire_zone_centrale() car la boite_onglets
        doit exister avant la connexion du signal item_clicked.
        """
        barre_laterale = Sidebar()
        barre_laterale.item_clicked.connect(self._on_navigation)

        for entree in DEFINITION_MENU:
            self._ajouter_noeud_sidebar(barre_laterale, entree)

        self._separateur.replaceWidget(0, barre_laterale)
        self._barre_laterale = barre_laterale

    def _ajouter_noeud_sidebar(self, parent, entree: tuple):
        """
        Ajoute récursivement un nœud dans la sidebar.
        3-tuple (id, libelle, enfants) → section pliable
        4-tuple (id, libelle, classe, singleton) → item feuille
        """
        if len(entree) == 3:
            id_, libelle, enfants = entree
            theme = parent.add_theme(id_, libelle)
            for enfant in enfants:
                self._ajouter_noeud_sidebar(theme, enfant)
        else:
            id_, libelle, _classe, singleton = entree
            parent.add_item(id_, libelle, singleton)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _on_navigation(self, identifiant: str, libelle: str, singleton: bool):
        """
        Clic sur un item sidebar.
        L'onglet liste est toujours singleton — un seul par identifiant.
        """
        if identifiant in self._onglets_liste:
            self._boite_onglets.setCurrentIndex(
                self._onglets_liste[identifiant]
            )
            return

        page  = self._creer_page_liste(identifiant, libelle, singleton)
        index = self._boite_onglets.addTab(page, libelle)
        self._boite_onglets.setCurrentIndex(index)
        self._onglets_liste[identifiant] = index

    def _creer_page_liste(
        self, identifiant: str, libelle: str, singleton: bool
    ) -> QWidget:
        """
        Crée la page liste pour un item.
        Cherche la classe dans DEFINITION_MENU.
        classe=None → placeholder temporaire.
        """
        classe = self._get_classe(identifiant)

        if classe is None:
            return self._placeholder(libelle)

        if singleton:
            return classe()
        else:
            return classe(
                on_ouvrir_fiche=self._ouvrir_fiche_onglet
            )

    def _ouvrir_fiche_onglet(self, libelle: str, widget: QWidget):
        """
        Ouvre une fiche dans un nouvel onglet indépendant.
        Appelé par les pages non-singleton via callback.
        """
        index = self._boite_onglets.addTab(widget, libelle)
        self._boite_onglets.setCurrentIndex(index)

    # ------------------------------------------------------------------
    # Fermeture d'onglet
    # ------------------------------------------------------------------

    def _on_fermeture_onglet(self, index: int):
        """
        Fermeture d'un onglet.
        Nettoie le registre des listes singleton.
        Décale les index supérieurs au fermé.
        """
        self._onglets_liste = {
            k: v for k, v in self._onglets_liste.items()
            if v != index
        }
        self._onglets_liste = {
            k: (v - 1 if v > index else v)
            for k, v in self._onglets_liste.items()
        }
        self._boite_onglets.removeTab(index)

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def _get_classe(self, identifiant: str):
        """Retrouve récursivement la classe associée à un identifiant."""
        return self._chercher_classe(identifiant, DEFINITION_MENU)

    def _chercher_classe(self, identifiant: str, noeuds: list):
        for entree in noeuds:
            if len(entree) == 3:
                resultat = self._chercher_classe(identifiant, entree[2])
                if resultat is not None:
                    return resultat
            else:
                iid, _libelle, classe, _singleton = entree
                if iid == identifiant:
                    return classe
        return None

    def _placeholder(self, libelle: str) -> QWidget:
        """Page temporaire pour les items non encore implémentés."""
        page       = QWidget()
        disposition = QHBoxLayout(page)
        etiquette  = QLabel(f"[ {libelle} ]")
        etiquette.setAlignment(Qt.AlignmentFlag.AlignCenter)
        etiquette.setStyleSheet(
            f"color: {AppTheme.CLR_TEXT_SECONDARY}; font-size: 18pt;"
        )
        disposition.addWidget(etiquette)
        return page

    def _on_apropos(self):
        QMessageBox.information(self, "À propos", "BaseRef Manager 2026")