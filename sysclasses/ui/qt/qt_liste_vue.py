# sysclasses/ui/qt/qt_liste_vue.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction


class QtListeVue(QWidget):
    """
    Vue liste générique pour toute entité.

    Responsabilité unique : afficher une liste et émettre des signaux.
    Ne connaît aucune entité métier.
    Le style visuel est entièrement géré par le QSS global — aucune
    couleur en dur dans ce fichier.

    Signaux émis :
        demande_ajout()
        demande_modification(ligne: dict)
        demande_suppression(ligne: dict)
        demande_consultation(ligne: dict)

    Hook surchargeable :
        _etendre_toolbar(barre) — ajouter des boutons après les boutons CRUD
    """

    demande_ajout        = pyqtSignal()
    demande_modification = pyqtSignal(dict)
    demande_suppression  = pyqtSignal(dict)
    demande_consultation = pyqtSignal(dict)

    def __init__(self, afficher_crud: bool = True,
                 hook_toolbar=None, parent=None):
        super().__init__(parent)
        self._afficher_crud           = afficher_crud
        self._hook_toolbar            = hook_toolbar
        self._ligne_selectionnee: dict | None = None
        self._colonnes: list[str]     = []
        self._actions_etendues: list[tuple[QPushButton, QAction]] = []
        self._construire_ui()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _construire_ui(self):
        disposition = QVBoxLayout(self)
        disposition.setContentsMargins(8, 8, 8, 4)
        disposition.setSpacing(6)
        disposition.addLayout(self._construire_toolbar())
        disposition.addWidget(self._construire_tableau())

    def _construire_toolbar(self) -> QHBoxLayout:
        barre = QHBoxLayout()
        barre.setSpacing(4)

        if self._afficher_crud:
            self._btn_ajouter   = self._creer_bouton(
                "Ajouter",   self.demande_ajout)
            self._btn_modifier  = self._creer_bouton(
                "Modifier",  self._on_modifier)
            self._btn_supprimer = self._creer_bouton(
                "Supprimer", self._on_supprimer)
            self._btn_consulter = self._creer_bouton(
                "Consulter", self._on_consulter)

            for btn in (self._btn_ajouter, self._btn_modifier,
                        self._btn_supprimer, self._btn_consulter):
                barre.addWidget(btn)

        # Hook — boutons spécifiques à droite des boutons CRUD
        nb_avant = barre.count()
        self._etendre_toolbar(barre)
        self._scanner_actions_etendues(barre, nb_avant)
        barre.addStretch()
        return barre

    def _creer_bouton(self, libelle: str, callback) -> QPushButton:
        btn = QPushButton(libelle)
        btn.clicked.connect(callback)
        return btn

    def _construire_tableau(self) -> QTableWidget:
        self._tableau = QTableWidget()
        self._tableau.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._tableau.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._tableau.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._tableau.setAlternatingRowColors(True)
        self._tableau.verticalHeader().setVisible(False)
        self._tableau.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self._tableau.horizontalHeader().setStretchLastSection(True)
        self._tableau.itemSelectionChanged.connect(self._on_selection)
        self._tableau.doubleClicked.connect(lambda: self._on_modifier())
        self._tableau.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._tableau.customContextMenuRequested.connect(
            self._on_menu_contextuel
        )
        return self._tableau

    # ------------------------------------------------------------------
    # Hook toolbar
    # ------------------------------------------------------------------

    def _etendre_toolbar(self, barre: QHBoxLayout):
        """
        Appelé à la fin de _construire_toolbar(), avant le stretch.

        Deux usages possibles, non exclusifs :
          - Surcharger dans une sous-classe de QtListeVue
          - Passer hook_toolbar au constructeur depuis QtControleur
            (évite de sous-classer QtListeVue pour un seul bouton)

        Ajouter des QPushButton directement dans la barre via barre.addWidget() —
        ils sont détectés automatiquement par _scanner_actions_etendues() et
        apparaissent dans le menu contextuel sans aucune action supplémentaire.
        """
        if self._hook_toolbar:
            self._hook_toolbar(barre)

    def _scanner_actions_etendues(self, barre: QHBoxLayout, depuis: int):
        """
        Parcourt les widgets ajoutés après l'index `depuis` dans la barre
        et crée automatiquement une QAction pour chaque QPushButton trouvé.
        L'action délègue à btn.click() — source unique, zéro duplication.
        """
        for i in range(depuis, barre.count()):
            item = barre.itemAt(i)
            if item:
                widget = item.widget()
                if isinstance(widget, QPushButton):
                    action = QAction(widget.text(), self)
                    action.triggered.connect(widget.click)
                    self._actions_etendues.append((widget, action))

    # ------------------------------------------------------------------
    # Menu contextuel
    # ------------------------------------------------------------------

    def _on_menu_contextuel(self, pos):
        menu = QMenu(self)

        if self._afficher_crud:
            a_ajouter = QAction("Ajouter", self)
            a_ajouter.triggered.connect(self.demande_ajout)
            menu.addAction(a_ajouter)

            selection = self._ligne_selectionnee is not None
            for libelle, callback in (
                ("Modifier",  self._on_modifier),
                ("Supprimer", self._on_supprimer),
                ("Consulter", self._on_consulter),
            ):
                a = QAction(libelle, self)
                a.triggered.connect(callback)
                a.setEnabled(selection)
                menu.addAction(a)

        if self._actions_etendues:
            if self._afficher_crud:
                menu.addSeparator()
            for btn, action in self._actions_etendues:
                action.setEnabled(btn.isEnabled())
                menu.addAction(action)

        if not menu.isEmpty():
            menu.exec(self._tableau.viewport().mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Alimentation
    # ------------------------------------------------------------------

    def charger(self, colonnes: list[str], libelles: list[str],
                lignes: list[dict], lignes_data: list[dict] = None):
        """
        Alimente le tableau sans reconstruire le widget.

        colonnes : noms techniques (clés du dict de données)
        libelles : labels d'affichage correspondants
        lignes   : données issues de load_all()
        """
        self._colonnes = colonnes

        self._tableau.blockSignals(True)
        self._tableau.setRowCount(0)
        self._tableau.setColumnCount(len(colonnes))
        self._tableau.setHorizontalHeaderLabels(libelles)

        for numero_ligne, ligne in enumerate(lignes):
            donnee = lignes_data[numero_ligne] if lignes_data else ligne
            self._tableau.insertRow(numero_ligne)
            for numero_col, col in enumerate(colonnes):
                valeur = ligne.get(col, "")
                item   = QTableWidgetItem(
                    "" if valeur is None else str(valeur)
                )
                # Données originales (IDs) stockées sur la colonne 0
                if numero_col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, donnee)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
                self._tableau.setItem(numero_ligne, numero_col, item)

        self._tableau.blockSignals(False)
        self._ligne_selectionnee = None
        self._maj_boutons()

    # ------------------------------------------------------------------
    # Sélection
    # ------------------------------------------------------------------

    def _on_selection(self):
        item_col0 = self._tableau.item(self._tableau.currentRow(), 0)
        if item_col0:
            self._ligne_selectionnee = item_col0.data(
                Qt.ItemDataRole.UserRole
            )
        else:
            self._ligne_selectionnee = None
        self._maj_boutons()

    def _maj_boutons(self):
        """Active les boutons contextuels selon la sélection."""
        if not self._afficher_crud:
            return
        selection = self._ligne_selectionnee is not None
        self._btn_modifier.setEnabled(selection)
        self._btn_supprimer.setEnabled(selection)
        self._btn_consulter.setEnabled(selection)

    # ------------------------------------------------------------------
    # Émission des signaux
    # ------------------------------------------------------------------

    def _on_modifier(self):
        if self._ligne_selectionnee:
            self.demande_modification.emit(self._ligne_selectionnee)

    def _on_supprimer(self):
        if self._ligne_selectionnee:
            self.demande_suppression.emit(self._ligne_selectionnee)

    def _on_consulter(self):
        if self._ligne_selectionnee:
            self.demande_consultation.emit(self._ligne_selectionnee)

    # ------------------------------------------------------------------
    # Accesseur
    # ------------------------------------------------------------------

    @property
    def ligne_selectionnee(self) -> dict | None:
        return self._ligne_selectionnee