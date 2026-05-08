# sysclasses/ui/qt/qt_fiche_vue.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLineEdit, QComboBox, QLabel,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal


class QtFicheVue(QWidget):
    """
    Vue formulaire générique pour toute entité.

    Responsabilité unique : afficher un formulaire et émettre des signaux.
    Ne connaît aucune entité métier.
    Le style visuel est entièrement géré par le QSS global.

    Champs générés depuis clsTableMetadata :
        QLineEdit  : champs standard et BINARY
                     (les valeurs BINARY arrivent déjà décodées)
        QComboBox  : colonnes FK
        Readonly   : identity, PK non-FK

    Signaux émis :
        demande_enregistrement(valeurs: dict)
        demande_annulation()

    Hook surchargeable :
        _etendre_boutons(barre) — ajouter des boutons spécifiques
    """

    demande_enregistrement = pyqtSignal(dict)
    demande_annulation     = pyqtSignal()

    MODE_AJOUT        = "INSERT"
    MODE_MODIFICATION = "UPDATE"
    MODE_SUPPRESSION  = "DELETE"
    MODE_CONSULTATION = "DISPLAY"

    def __init__(self, parent=None):
        super().__init__(parent)

        self._champs:           dict[str, QWidget] = {}
        self._fk_label_vers_id: dict[str, dict]    = {}
        self._fk_id_vers_label: dict[str, dict]    = {}
        self._mode = self.MODE_CONSULTATION

        self._construire_ui()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _construire_ui(self):
        disposition = QVBoxLayout(self)
        disposition.setContentsMargins(8, 8, 8, 8)
        disposition.setSpacing(8)

        self._etiquette_titre = QLabel()
        self._etiquette_titre.setStyleSheet(
            "font-weight: bold; font-size: 12pt;"
        )
        disposition.addWidget(self._etiquette_titre)

        separateur = QFrame()
        separateur.setFrameShape(QFrame.Shape.HLine)
        disposition.addWidget(separateur)

        zone_scroll    = QScrollArea()
        zone_scroll.setWidgetResizable(True)
        zone_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        contenu_scroll = QWidget()
        self._disposition_form = QFormLayout(contenu_scroll)
        self._disposition_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._disposition_form.setSpacing(8)
        self._disposition_form.setContentsMargins(8, 8, 8, 8)
        zone_scroll.setWidget(contenu_scroll)
        disposition.addWidget(zone_scroll, 1)

        disposition.addLayout(self._construire_boutons())

    def _construire_boutons(self) -> QHBoxLayout:
        barre = QHBoxLayout()

        # Hook — boutons spécifiques à gauche
        self._etendre_boutons(barre)

        barre.addStretch()

        self._btn_enregistrer = QPushButton("Enregistrer")
        self._btn_enregistrer.setFixedHeight(28)
        self._btn_enregistrer.clicked.connect(self._on_enregistrer)

        self._btn_annuler = QPushButton("Annuler")
        self._btn_annuler.setFixedHeight(28)
        self._btn_annuler.setObjectName("bouton_secondaire")
        self._btn_annuler.clicked.connect(self.demande_annulation)

        barre.addWidget(self._btn_enregistrer)
        barre.addWidget(self._btn_annuler)
        return barre

    # ------------------------------------------------------------------
    # Hook boutons
    # ------------------------------------------------------------------

    def _etendre_boutons(self, barre: QHBoxLayout):
        """
        Appelé au début de _construire_boutons(), avant le stretch.
        Surcharger pour ajouter des boutons spécifiques à gauche.

        Exemple :
            def _etendre_boutons(self, barre):
                self._btn_tester = QPushButton("Tester la connexion")
                self._btn_tester.clicked.connect(self._tester)
                barre.addWidget(self._btn_tester)
        """
        pass

    # ------------------------------------------------------------------
    # Génération des champs depuis métadonnées
    # ------------------------------------------------------------------

    def definir_champs(self, colonnes: list[dict]):
        """
        Génère les champs depuis la liste des métadonnées.
        Appelé une seule fois par le contrôleur à l'initialisation.

        colonnes : liste de dicts issus de clsTableMetadata
        """
        while self._disposition_form.rowCount():
            self._disposition_form.removeRow(0)
        self._champs.clear()
        self._fk_label_vers_id.clear()
        self._fk_id_vers_label.clear()

        for col in colonnes:
            nom          = col["name"]
            est_identity = col["is_identity"]
            est_pk       = col["is_pk"]
            est_fk       = col.get("is_fk", False)
            libelle      = self._libelle_colonne(col)

            if est_fk:
                champ = QComboBox()
                champ.setFixedHeight(26)
            else:
                champ = QLineEdit()
                champ.setFixedHeight(26)

            # Identity et PK non-FK → toujours readonly
            # Le QSS QLineEdit:read-only grise automatiquement
            if est_identity or (est_pk and not est_fk):
                if isinstance(champ, QLineEdit):
                    champ.setReadOnly(True)
                elif isinstance(champ, QComboBox):
                    champ.setEnabled(False)

            self._disposition_form.addRow(f"{libelle} :", champ)
            self._champs[nom] = champ

    def _libelle_colonne(self, col: dict) -> str:
        """Dérive le libellé depuis le comment PostgreSQL ou le nom."""
        comment = col.get("comment") or ""
        if "|" in comment:
            return comment.split("|", 1)[0].strip()
        if comment:
            return comment
        return col["name"].replace("_", " ").title()

    # ------------------------------------------------------------------
    # Alimentation des ComboBox FK
    # ------------------------------------------------------------------

    def charger_fk(self, nom_colonne: str, choix: list[tuple]):
        """
        Alimente un ComboBox FK.
        choix : liste de tuples (id, label) issus de get_list_FK()
        """
        combo = self._champs.get(nom_colonne)
        if not isinstance(combo, QComboBox):
            return

        self._fk_label_vers_id[nom_colonne] = {
            label: val_id for val_id, label in choix
        }
        self._fk_id_vers_label[nom_colonne] = {
            val_id: label for val_id, label in choix
        }

        combo.blockSignals(True)
        combo.clear()
        combo.addItems([label for _, label in choix])
        combo.blockSignals(False)

    # ------------------------------------------------------------------
    # Chargement des valeurs
    # ------------------------------------------------------------------

    def charger(self, mode: str, valeurs: dict | None = None):
        """
        Affiche le formulaire dans le mode demandé.

        mode    : MODE_AJOUT / MODE_MODIFICATION / MODE_SUPPRESSION
                  / MODE_CONSULTATION
        valeurs : dict des valeurs à afficher — None pour un ajout.
                  Les valeurs BINARY arrivent déjà décodées depuis
                  le contrôleur via les getters de l'entité.
        """
        self._mode = mode

        titres = {
            self.MODE_AJOUT:        "Ajout",
            self.MODE_MODIFICATION: "Modification",
            self.MODE_SUPPRESSION:  "Suppression",
            self.MODE_CONSULTATION: "Consultation",
        }
        self._etiquette_titre.setText(titres.get(mode, ""))

        lecture_seule_totale = mode in (
            self.MODE_CONSULTATION, self.MODE_SUPPRESSION
        )

        for nom, champ in self._champs.items():
            valeur = valeurs.get(nom) if valeurs else None

            if isinstance(champ, QComboBox):
                label = self._fk_id_vers_label.get(nom, {}).get(valeur, "")
                champ.setCurrentText(label)
                champ.setEnabled(not lecture_seule_totale
                                 and champ.isEnabled())
            else:
                champ.setText("" if valeur is None else str(valeur))
                if not champ.isReadOnly():
                    champ.setReadOnly(lecture_seule_totale)

        self._btn_enregistrer.setVisible(
            mode != self.MODE_CONSULTATION
        )
        if mode == self.MODE_SUPPRESSION:
            self._btn_enregistrer.setText("Supprimer")
            self._btn_enregistrer.setObjectName("bouton_suppression")
            self._btn_enregistrer.style().unpolish(self._btn_enregistrer)
            self._btn_enregistrer.style().polish(self._btn_enregistrer)
        else:
            self._btn_enregistrer.setText("Enregistrer")
            self._btn_enregistrer.setObjectName("")
            self._btn_enregistrer.style().unpolish(self._btn_enregistrer)
            self._btn_enregistrer.style().polish(self._btn_enregistrer)

    # ------------------------------------------------------------------
    # Lecture des valeurs saisies
    # ------------------------------------------------------------------

    def _lire_valeurs(self) -> dict:
        """
        Lit les valeurs de tous les champs.
        Pour les FK : retourne l'id (pas le label).
        """
        valeurs = {}
        for nom, champ in self._champs.items():
            if isinstance(champ, QComboBox):
                label_sel    = champ.currentText()
                valeurs[nom] = self._fk_label_vers_id.get(
                    nom, {}
                ).get(label_sel)
            else:
                texte        = champ.text().strip()
                valeurs[nom] = texte if texte else None
        return valeurs

    # ------------------------------------------------------------------
    # Émission
    # ------------------------------------------------------------------

    def _on_enregistrer(self):
        self.demande_enregistrement.emit(self._lire_valeurs())