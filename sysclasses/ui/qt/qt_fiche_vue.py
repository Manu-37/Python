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
    Ne connaît aucune entité métier — ne connaît pas insert/update/ctrl_valeurs.

    L'entité est passée par le contrôleur via charger().
    La vue lit via getattr() — déchiffrement inclus via les getters.
    La vue écrit via setattr() — chiffrement inclus via les setters.
    Le contrôleur est responsable du CRUD et du commit.

    Signaux émis :
        demande_enregistrement() — sans données, le contrôleur possède l'entité
        demande_annulation()

    Hooks surchageables :
        _etendre_boutons(barre) — ajouter des boutons spécifiques
    """

    demande_enregistrement = pyqtSignal()
    demande_annulation     = pyqtSignal()

    MODE_AJOUT        = "INSERT"
    MODE_MODIFICATION = "UPDATE"
    MODE_SUPPRESSION  = "DELETE"
    MODE_CONSULTATION = "DISPLAY"

    def __init__(self, parent=None):
        super().__init__(parent)

        self._entite       = None   # objet entité courant — peuplé par charger()
        self._mode         = self.MODE_CONSULTATION
        self._champs:           dict[str, QWidget] = {}
        self._fk_label_vers_id: dict[str, dict]    = {}
        self._fk_id_vers_label: dict[str, dict]    = {}

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
        """
        pass

    # ------------------------------------------------------------------
    # Génération des champs depuis métadonnées
    # ------------------------------------------------------------------

    def definir_champs(self, colonnes: list[dict]):
        """
        Génère les champs depuis la liste des métadonnées.
        Appelé une seule fois par le contrôleur à l'initialisation.
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

            if est_identity or (est_pk and not est_fk):
                if isinstance(champ, QLineEdit):
                    champ.setReadOnly(True)
                elif isinstance(champ, QComboBox):
                    champ.setEnabled(False)

            self._disposition_form.addRow(f"{libelle} :", champ)
            self._champs[nom] = champ

    def _libelle_colonne(self, col: dict) -> str:
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
    # Chargement depuis l'entité
    # ------------------------------------------------------------------

    def charger(self, mode: str, entite):
        """
        Affiche le formulaire depuis l'objet entité.

        mode   : MODE_AJOUT / MODE_MODIFICATION / MODE_SUPPRESSION / MODE_CONSULTATION
        entite : objet clsEntity_ABS instancié par le contrôleur.
                 Lecture via getattr() — déchiffrement BINARY inclus via les getters.
        """
        self._mode   = mode
        self._entite = entite

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
            # Lecture via le getter de l'entité — déchiffrement inclus
            valeur = getattr(entite, nom, None)

            if isinstance(champ, QComboBox):
                label = self._fk_id_vers_label.get(nom, {}).get(valeur, "")
                champ.setCurrentText(label)
                champ.setEnabled(not lecture_seule_totale
                                 and champ.isEnabled())
            else:
                champ.setText("" if valeur is None else str(valeur))
                if not champ.isReadOnly():
                    champ.setReadOnly(lecture_seule_totale)

        self._btn_enregistrer.setVisible(mode != self.MODE_CONSULTATION)
        if mode == self.MODE_SUPPRESSION:
            self._btn_enregistrer.setText("Supprimer")
        else:
            self._btn_enregistrer.setText("Enregistrer")

    # ------------------------------------------------------------------
    # Écriture dans l'entité depuis les champs
    # ------------------------------------------------------------------

    def _ecrire_dans_entite(self):
        """
        Écrit les valeurs saisies dans l'entité via les setters.
        Chiffrement BINARY inclus — transparent ici.
        PK et identity ignorées — jamais modifiables.
        """
        from db.clsTableMetadata import clsTableMetadata
        metadata = self._entite.TableMetadata

        for nom, champ in self._champs.items():
            col      = metadata.get_column(nom)
            est_pk   = col["is_pk"]
            est_fk   = col.get("is_fk", False)
            est_iden = col["is_identity"]

            # Ne jamais toucher aux identity et PK non-FK
            if est_iden or (est_pk and not est_fk):
                continue

            if isinstance(champ, QComboBox):
                label_sel = champ.currentText()
                valeur    = self._fk_label_vers_id.get(nom, {}).get(label_sel)
            else:
                texte  = champ.text().strip()
                valeur = texte if texte else None

            # Écriture via le setter — chiffrement inclus
            setattr(self._entite, nom, valeur)

    # ------------------------------------------------------------------
    # Émission
    # ------------------------------------------------------------------

    def _on_enregistrer(self):
        """
        Écrit les valeurs dans l'entité puis signale au contrôleur.
        Le contrôleur appelle insert() ou update() — ctrl_valeurs() inclus.
        """
        self._ecrire_dans_entite()
        self.demande_enregistrement.emit()