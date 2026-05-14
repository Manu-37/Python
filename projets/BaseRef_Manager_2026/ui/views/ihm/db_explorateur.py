# ui/views/ihm/db_explorateur.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QTextEdit, QMessageBox, QLabel,
    QApplication,
)
from PyQt6.QtGui  import QColor, QCursor
from PyQt6.QtCore import Qt

from sysclasses.clsLOG        import clsLOG
from db.db_baseref.ihm.clsDB  import clsDB
from projets.BaseRef_Manager_2026.services.explorateur_db import ExplorateurDB


class DbExplorateur(QWidget):
    """
    Explorateur différentiel d'une base de données.

    Structure :
        ┌─ toolbar ───────────────────────────────────┐
        │ [Scanner]  [Valider]  [Fermer]              │
        ├─ QSplitter (horizontal) ────────────────────┤
        │ QTreeWidget (structure réelle)              │
        │   └─ schéma → relation [TYPE] → colonne     │
        │                                             │
        │ QTabWidget (rapport diff)                   │
        │   Nouveautés | Disparitions | Inchangés     │
        └─────────────────────────────────────────────┘

    Vert  = nouvel élément (absent du catalogue)
    Gris  = éléments inchangés
    """

    def __init__(self, oDb: clsDB, parent=None):
        super().__init__(parent)
        self._oDb      = oDb
        self._log      = clsLOG()
        self._service  = ExplorateurDB(oDb)
        self._diff     = None

        self._construire_ui()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _construire_ui(self):
        disposition = QVBoxLayout(self)
        disposition.setContentsMargins(4, 4, 4, 4)
        disposition.setSpacing(4)

        disposition.addLayout(self._creer_toolbar())

        separateur = QSplitter(Qt.Orientation.Horizontal)

        self._arbre  = self._creer_arbre()
        self._onglets = self._creer_onglets_rapport()

        separateur.addWidget(self._arbre)
        separateur.addWidget(self._onglets)
        separateur.setStretchFactor(0, 2)
        separateur.setStretchFactor(1, 3)

        disposition.addWidget(separateur)

    def _creer_toolbar(self) -> QHBoxLayout:
        barre = QHBoxLayout()
        barre.setContentsMargins(0, 0, 0, 0)

        self._btn_scanner = QPushButton("Scanner la base")
        self._btn_valider = QPushButton("Valider et importer")
        self._btn_valider.setEnabled(False)

        self._btn_scanner.clicked.connect(self._on_scanner)
        self._btn_valider.clicked.connect(self._on_valider)

        barre.addWidget(self._btn_scanner)
        barre.addWidget(self._btn_valider)
        barre.addStretch()
        return barre

    def _creer_arbre(self) -> QTreeWidget:
        arbre = QTreeWidget()
        arbre.setHeaderLabel("Structure réelle de la base")
        arbre.setColumnCount(1)
        arbre.setAlternatingRowColors(True)
        arbre.setIndentation(16)
        label = QLabel(
            "Cliquez sur « Scanner la base » pour explorer la structure réelle.",
            arbre
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: gray; font-style: italic;")
        self._label_arbre_vide = label
        return arbre

    def _creer_onglets_rapport(self) -> QTabWidget:
        onglets = QTabWidget()
        self._txt_nouveautes   = QTextEdit(); self._txt_nouveautes.setReadOnly(True)
        self._txt_disparitions = QTextEdit(); self._txt_disparitions.setReadOnly(True)
        self._txt_inchanges    = QTextEdit(); self._txt_inchanges.setReadOnly(True)
        onglets.addTab(self._txt_nouveautes,   "Nouveautés")
        onglets.addTab(self._txt_disparitions, "Disparitions")
        onglets.addTab(self._txt_inchanges,    "Inchangés")
        return onglets

    def showEvent(self, event):
        super().showEvent(event)
        if self._label_arbre_vide:
            self._label_arbre_vide.resize(self._arbre.size())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._label_arbre_vide:
            self._label_arbre_vide.resize(self._arbre.size())

    # ------------------------------------------------------------------
    # Scan
    # ------------------------------------------------------------------

    def _on_scanner(self):
        self._btn_scanner.setEnabled(False)
        self._btn_scanner.setText("Scan en cours…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._diff = self._service.scanner()
            self._peupler_arbre(self._diff)
            self._peupler_rapport(self._diff)
            self._btn_valider.setEnabled(self._diff_a_appliquer())
            if self._label_arbre_vide:
                self._label_arbre_vide.hide()
                self._label_arbre_vide = None
        except Exception as e:
            self._log.error(f"DbExplorateur.scanner : {e}")
            QMessageBox.critical(
                self, "Erreur de scan",
                f"Impossible d'explorer la base :\n{e}"
            )
        finally:
            QApplication.restoreOverrideCursor()
            self._btn_scanner.setEnabled(True)
            self._btn_scanner.setText("Scanner la base")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _on_valider(self):
        if not self._diff:
            return
        n = self._diff["nouveautes"]
        d = self._diff["disparitions"]
        nb_n = len(n["schemas"]) + len(n["relations"]) + len(n["colonnes"])
        nb_d = len(d["schemas"]) + len(d["relations"]) + len(d["colonnes"])
        msg = (
            f"Appliquer les modifications au catalogue ?\n\n"
            f"  Nouveautés  : {nb_n} élément(s) à importer\n"
            f"  Disparitions : {nb_d} élément(s) à désactiver\n\n"
            f"Cette opération est irréversible."
        )
        if QMessageBox.question(
            self, "Confirmer la validation", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._service.valider(self._diff)
            self._btn_valider.setEnabled(False)
            QMessageBox.information(
                self, "Validation terminée",
                "Le catalogue a été mis à jour avec succès."
            )
        except Exception as e:
            self._log.error(f"DbExplorateur.valider : {e}")
            QMessageBox.critical(self, "Erreur de validation", f"Échec :\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    # ------------------------------------------------------------------
    # Population de l'arbre
    # ------------------------------------------------------------------

    def _peupler_arbre(self, diff: dict):
        self._arbre.clear()

        # Ensembles pour le marquage visuel "nouveau"
        sch_nouveaux = {n["sch_nom"] for n in diff["nouveautes"]["schemas"]}
        rel_nouveaux = {
            (n["sch_nom"], n["rel_nom"]) for n in diff["nouveautes"]["relations"]
        }
        col_nouveaux = {
            (n["sch_nom"], n["rel_nom"], n["col_nom"])
            for n in diff["nouveautes"]["colonnes"]
        }

        # L'arbre montre la structure réelle — on la reconstitue depuis le diff
        # (inchangés + nouveautés) pour éviter de rescanner la base
        sch_presents = {
            s["sch_nom"] for s in diff["inchanges"]["schemas"]
        } | sch_nouveaux

        rel_presents: dict[str, list] = {}
        for r in diff["inchanges"]["relations"] + diff["nouveautes"]["relations"]:
            rel_presents.setdefault(r["sch_nom"], []).append(r)

        col_presents: dict[tuple, list] = {}
        for c in diff["inchanges"]["colonnes"] + diff["nouveautes"]["colonnes"]:
            key = (c["sch_nom"], c["rel_nom"])
            col_presents.setdefault(key, []).append(c)

        couleur_nouveau = QColor("#4caf50")

        for sch_nom in sorted(sch_presents):
            item_sch = QTreeWidgetItem([sch_nom])
            if sch_nom in sch_nouveaux:
                item_sch.setForeground(0, couleur_nouveau)
            self._arbre.addTopLevelItem(item_sch)

            for rel in sorted(rel_presents.get(sch_nom, []), key=lambda r: r["rel_nom"]):
                rel_nom  = rel["rel_nom"]
                rel_type = rel.get("rel_type", "")
                label    = f"{rel_nom}  [{rel_type}]" if rel_type else rel_nom
                item_rel = QTreeWidgetItem([label])
                if (sch_nom, rel_nom) in rel_nouveaux:
                    item_rel.setForeground(0, couleur_nouveau)
                item_sch.addChild(item_rel)

                for col in sorted(
                    col_presents.get((sch_nom, rel_nom), []),
                    key=lambda c: c["col_nom"]
                ):
                    col_nom  = col["col_nom"]
                    col_type = col.get("col_type", "")
                    label    = f"{col_nom}  {col_type}" if col_type else col_nom
                    item_col = QTreeWidgetItem([label])
                    if (sch_nom, rel_nom, col_nom) in col_nouveaux:
                        item_col.setForeground(0, couleur_nouveau)
                    item_rel.addChild(item_col)

        self._arbre.expandToDepth(1)

    # ------------------------------------------------------------------
    # Population du rapport
    # ------------------------------------------------------------------

    def _peupler_rapport(self, diff: dict):
        self._txt_nouveautes.setHtml(
            self._html_nouveautes(diff["nouveautes"])
        )
        self._txt_disparitions.setHtml(
            self._html_disparitions(diff["disparitions"])
        )
        self._txt_inchanges.setHtml(
            self._html_inchanges(diff["inchanges"])
        )

    def _html_nouveautes(self, n: dict) -> str:
        lignes = ["<h3 style='color:#2e7d32'>Nouveautés</h3>"]

        if n["schemas"]:
            lignes.append(f"<b>Schémas ({len(n['schemas'])})</b><ul>")
            for s in n["schemas"]:
                lignes.append(f"<li>{s['sch_nom']}</li>")
            lignes.append("</ul>")

        if n["relations"]:
            lignes.append(f"<b>Relations ({len(n['relations'])})</b><ul>")
            for r in n["relations"]:
                nb     = len(r.get("colonnes", []))
                nb_fk  = r.get("nb_fk_ignorees", 0)
                detail = f"{nb} colonne(s)"
                if nb_fk:
                    detail += f" <span style='color:#e57373'>+{nb_fk} FK ignorée(s)</span>"
                lignes.append(
                    f"<li>{r['sch_nom']}.{r['rel_nom']} "
                    f"<span style='color:gray'>[{r['rel_type']}] — {detail}</span></li>"
                )
            lignes.append("</ul>")

        if n["colonnes"]:
            lignes.append(f"<b>Colonnes ({len(n['colonnes'])})</b><ul>")
            for c in n["colonnes"]:
                comment = (
                    f" <span style='color:gray;font-style:italic'>— {c['commentaire']}</span>"
                    if c.get("commentaire") else ""
                )
                lignes.append(
                    f"<li>{c['sch_nom']}.{c['rel_nom']}.<b>{c['col_nom']}</b> "
                    f"<span style='color:gray'>{c.get('col_type','')}</span>{comment}</li>"
                )
            lignes.append("</ul>")

        if not (n["schemas"] or n["relations"] or n["colonnes"]):
            lignes.append("<p style='color:gray;font-style:italic'>Aucune nouveauté.</p>")

        return "".join(lignes)

    def _html_disparitions(self, d: dict) -> str:
        lignes = ["<h3 style='color:#c62828'>Disparitions</h3>"]

        if d["schemas"]:
            lignes.append(f"<b>Schémas ({len(d['schemas'])})</b><ul>")
            for s in d["schemas"]:
                lignes.append(
                    f"<li>{s['sch_nom']} "
                    f"<span style='color:gray'>→ sera désactivé avec toutes ses relations</span></li>"
                )
            lignes.append("</ul>")

        if d["relations"]:
            lignes.append(f"<b>Relations ({len(d['relations'])})</b><ul>")
            for r in d["relations"]:
                lignes.append(
                    f"<li>{r['sch_nom']}.{r['rel_nom']} "
                    f"<span style='color:gray'>→ sera désactivée avec ses colonnes</span></li>"
                )
            lignes.append("</ul>")

        if d["colonnes"]:
            lignes.append(f"<b>Colonnes ({len(d['colonnes'])})</b><ul>")
            for c in d["colonnes"]:
                lignes.append(
                    f"<li>{c['sch_nom']}.{c['rel_nom']}.<b>{c['col_nom']}</b> "
                    f"<span style='color:gray'>→ sera désactivée</span></li>"
                )
            lignes.append("</ul>")

        if not (d["schemas"] or d["relations"] or d["colonnes"]):
            lignes.append("<p style='color:gray;font-style:italic'>Aucune disparition.</p>")

        return "".join(lignes)

    def _html_inchanges(self, i: dict) -> str:
        return (
            "<h3>Inchangés</h3>"
            f"<p>Schémas &nbsp;&nbsp;: <b>{len(i['schemas'])}</b><br>"
            f"Relations : <b>{len(i['relations'])}</b><br>"
            f"Colonnes &nbsp;: <b>{len(i['colonnes'])}</b></p>"
        )

    # ------------------------------------------------------------------
    # Utilitaire
    # ------------------------------------------------------------------

    def _diff_a_appliquer(self) -> bool:
        if not self._diff:
            return False
        n = self._diff["nouveautes"]
        d = self._diff["disparitions"]
        return any([
            n["schemas"], n["relations"], n["colonnes"],
            d["schemas"], d["relations"], d["colonnes"],
        ])
