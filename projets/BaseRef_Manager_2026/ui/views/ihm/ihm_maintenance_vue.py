# ui/views/ihm/ihm_maintenance_vue.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QStyledItemDelegate, QAbstractItemDelegate, QLineEdit,
    QMessageBox, QApplication,
)
from PyQt6.QtCore  import Qt, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui   import QKeyEvent, QIntValidator

from sysclasses.clsLOG         import clsLOG
from db.db_baseref.ihm.clsDB   import clsDB
from db.db_baseref.ihm.clsSCH  import clsSCH
from db.db_baseref.ihm.clsREL  import clsREL
from db.db_baseref.ihm.clsCOL  import clsCOL
from db.db_baseref.ihm.clsLAN  import clsLAN
from db.db_baseref.ihm.clsLRE  import clsLRE
from db.db_baseref.ihm.clsLCO  import clsLCO
from db.db_baseref.ihm.clsTAF  import clsTAF


# ── Indices de colonnes ────────────────────────────────────────────────────
_C_NOM   = 0   # Nom (non éditable)
_C_TYPE  = 1   # Type TAF  — éditable COL seulement
_C_LARG  = 2   # Largeur   — éditable COL seulement
_C_LABEL = 3   # Libellé   — éditable REL et COL
_C_COURT = 4   # Court     — éditable COL seulement
_C_BULLE = 5   # Infobulle — éditable COL seulement

_COLS_REL = (_C_LABEL,)
_COLS_COL = (_C_TYPE, _C_LARG, _C_LABEL, _C_COURT, _C_BULLE)

_ROLE_META = Qt.ItemDataRole.UserRole        # dict métadonnées (col 0)
_ROLE_TAF  = Qt.ItemDataRole.UserRole + 1   # taf_id courant (col 1)
_ROLE_ORIG = Qt.ItemDataRole.UserRole + 2   # valeur originale (toutes colonnes)


# ═══════════════════════════════════════════════════════════════════════════
# Delegates
# ═══════════════════════════════════════════════════════════════════════════

class _DelegateBase(QStyledItemDelegate):
    """
    Base commune : auto-sélection du contenu + interception Tab / Entrée.
    Chaque instance track sa colonne courante pour émettre le bon signal.
    """
    tab_presse     = pyqtSignal(int, bool)  # (col, retour)
    entree_pressee = pyqtSignal(int)        # (col,)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._col_courante = -1

    def _editable(self, index) -> bool:
        data  = index.model().index(index.row(), 0, index.parent()).data(_ROLE_META) or {}
        ntype = data.get("type")
        col   = index.column()
        if ntype == "rel":
            return col in _COLS_REL
        if ntype == "col":
            return col in _COLS_COL
        return False

    def createEditor(self, parent, option, index):
        if not self._editable(index):
            return None
        self._col_courante = index.column()
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            QTimer.singleShot(0, editor.selectAll)
        return editor

    def eventFilter(self, editor, event):
        if isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress:
            col = self._col_courante
            if event.key() == Qt.Key.Key_Tab:
                self.commitData.emit(editor)
                self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)
                self.tab_presse.emit(col, False)
                return True
            if event.key() == Qt.Key.Key_Backtab:
                self.commitData.emit(editor)
                self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)
                self.tab_presse.emit(col, True)
                return True
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.commitData.emit(editor)
                self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)
                self.entree_pressee.emit(col)
                return True
        return super().eventFilter(editor, event)


class _DelegateEntier(_DelegateBase):
    """Delegate entier positif pour col_largeur."""

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            editor.setValidator(QIntValidator(0, 9999, editor))
        return editor


class _DelegateTAF(_DelegateBase):
    """Delegate ComboBox pour taf_id."""

    def __init__(self, choix: list[tuple], parent=None):
        super().__init__(parent)
        self._choix = choix  # [(taf_id, taf_code), ...]

    def createEditor(self, parent, option, index):
        if not self._editable(index):
            return None
        self._col_courante = index.column()
        combo = QComboBox(parent)
        for taf_id, taf_code in self._choix:
            combo.addItem(taf_code, taf_id)
        QTimer.singleShot(0, combo.showPopup)
        return combo

    def setEditorData(self, editor, index):
        taf_id = index.data(_ROLE_TAF)
        for i, (tid, _) in enumerate(self._choix):
            if tid == taf_id:
                editor.setCurrentIndex(i)
                return
        editor.setCurrentIndex(0)

    def setModelData(self, editor, model, index):
        taf_id   = editor.currentData()
        taf_code = editor.currentText()
        model.setData(index, taf_code, Qt.ItemDataRole.DisplayRole)
        model.setData(index, taf_id,   _ROLE_TAF)


# ═══════════════════════════════════════════════════════════════════════════
# Vue principale
# ═══════════════════════════════════════════════════════════════════════════

class IhmMaintenanceVue(QWidget):
    """
    Vue de maintenance des libellés IHM pour une base de données.

    Arborescence SCH → REL → COL avec édition inline pour la langue choisie.
    Sauvegarde ligne par ligne à la sortie (currentItemChanged).
    """

    def __init__(self, oDb: clsDB, parent=None):
        super().__init__(parent)
        self._oDb     = oDb
        self._log     = clsLOG()
        self._langues: list[dict] = []
        self._item_sale: QTreeWidgetItem | None = None

        self._charger_langues()
        self._construire_ui()
        self._connecter_signaux()
        self._charger_arbre()

    # ──────────────────────────────────────────────────────────────────────
    # Construction
    # ──────────────────────────────────────────────────────────────────────

    def _charger_langues(self):
        self._langues = clsLAN.load_all(
            where_clause="lan_actif = TRUE", order_by=clsLAN.LAN_ORDRE
        )

    def _construire_ui(self):
        disp = QVBoxLayout(self)
        disp.setContentsMargins(4, 4, 4, 4)
        disp.setSpacing(4)
        disp.addLayout(self._creer_toolbar())
        disp.addWidget(self._creer_arbre())

    def _creer_toolbar(self) -> QHBoxLayout:
        barre = QHBoxLayout()
        barre.setSpacing(8)

        barre.addWidget(QLabel("Langue :"))
        self._combo_langue = QComboBox()
        for lan in self._langues:
            self._combo_langue.addItem(lan[clsLAN.LAN_CODE], lan[clsLAN.LAN_ID])
        barre.addWidget(self._combo_langue)

        btn = QPushButton("Actualiser")
        btn.clicked.connect(self._on_actualiser)
        barre.addWidget(btn)
        barre.addStretch()
        return barre

    def _creer_arbre(self) -> QTreeWidget:
        self._arbre = QTreeWidget()
        self._arbre.setColumnCount(6)
        self._arbre.setHeaderLabels(
            ["Nom", "Type", "Larg.", "Libellé", "Court", "Infobulle"]
        )

        h = self._arbre.header()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h.resizeSection(_C_NOM,   200)
        h.resizeSection(_C_TYPE,  150)
        h.resizeSection(_C_LARG,   60)
        h.resizeSection(_C_LABEL, 280)
        h.resizeSection(_C_COURT, 100)
        h.setStretchLastSection(True)

        self._arbre.setAlternatingRowColors(True)
        self._arbre.setIndentation(16)

        # Delegates
        choix_taf = [
            (r[clsTAF.TAF_ID], r[clsTAF.TAF_CODE])
            for r in clsTAF.load_all(order_by=clsTAF.TAF_CODE)
        ]
        self._del_taf    = _DelegateTAF(choix_taf, self._arbre)
        self._del_entier = _DelegateEntier(self._arbre)
        self._del_texte  = _DelegateBase(self._arbre)

        self._arbre.setItemDelegateForColumn(_C_TYPE,  self._del_taf)
        self._arbre.setItemDelegateForColumn(_C_LARG,  self._del_entier)
        self._arbre.setItemDelegateForColumn(_C_LABEL, self._del_texte)
        self._arbre.setItemDelegateForColumn(_C_COURT, self._del_texte)
        self._arbre.setItemDelegateForColumn(_C_BULLE, self._del_texte)

        return self._arbre

    def _connecter_signaux(self):
        self._arbre.currentItemChanged.connect(self._on_item_change)
        self._arbre.itemChanged.connect(self._on_cellule_modifiee)
        self._combo_langue.currentIndexChanged.connect(self._on_actualiser)

        for d in (self._del_taf, self._del_entier, self._del_texte):
            d.tab_presse.connect(self._on_tab)
            d.entree_pressee.connect(lambda col: self._on_tab(col, False))

    # ──────────────────────────────────────────────────────────────────────
    # Chargement de l'arbre
    # ──────────────────────────────────────────────────────────────────────

    def _lan_id(self) -> int | None:
        return self._combo_langue.currentData()

    def _on_actualiser(self):
        if self._item_sale:
            self._sauver_item(self._item_sale)
        self._charger_arbre()

    def _charger_arbre(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._arbre.blockSignals(True)
            self._arbre.clear()
            self._item_sale = None
            lan_id = self._lan_id()

            schemas = clsSCH.load_all(
                where_clause=f"db_id = {self._oDb.db_id} AND sch_actif = TRUE",
                order_by=clsSCH.SCH_NOM
            )
            for sch_row in schemas:
                self._arbre.addTopLevelItem(
                    self._creer_item_sch(sch_row, lan_id)
                )
            self._arbre.expandToDepth(0)
        finally:
            self._arbre.blockSignals(False)
            QApplication.restoreOverrideCursor()

    def _creer_item_sch(self, sch_row: dict, lan_id: int | None) -> QTreeWidgetItem:
        item = QTreeWidgetItem([sch_row[clsSCH.SCH_NOM]])
        item.setData(_C_NOM, _ROLE_META, {"type": "sch", "sch_id": sch_row[clsSCH.SCH_ID]})
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        rels = clsREL.load_all(
            where_clause=f"sch_id = {sch_row[clsSCH.SCH_ID]} AND rel_actif = TRUE",
            order_by=clsREL.REL_NOM
        )
        for rel_row in rels:
            item.addChild(self._creer_item_rel(rel_row, lan_id))
        return item

    def _creer_item_rel(self, rel_row: dict, lan_id: int | None) -> QTreeWidgetItem:
        rel_id  = rel_row[clsREL.REL_ID]
        rel_nom = rel_row[clsREL.REL_NOM]

        oLRE      = clsLRE(rel_id=rel_id, lan_id=lan_id) if lan_id else None
        lre_existe = bool(oLRE and oLRE.rel_id)
        lre_label  = (oLRE.lre_label or "") if lre_existe else ""

        item = QTreeWidgetItem([""] * 6)
        item.setText(_C_NOM,   rel_nom)
        item.setText(_C_LABEL, lre_label)
        item.setData(_C_NOM,   _ROLE_META, {
            "type": "rel", "rel_id": rel_id, "lan_id": lan_id,
            "lre_existe": lre_existe,
        })
        item.setData(_C_LABEL, _ROLE_ORIG, lre_label)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

        cols = clsCOL.load_all(
            where_clause=f"rel_id = {rel_id} AND col_actif = TRUE",
            order_by=clsCOL.COL_NOM
        )
        for col_row in cols:
            item.addChild(self._creer_item_col(col_row, lan_id))
        return item

    def _creer_item_col(self, col_row: dict, lan_id: int | None) -> QTreeWidgetItem:
        col_id  = col_row[clsCOL.COL_ID]
        taf_id  = col_row.get(clsCOL.TAF_ID)
        largeur = col_row.get(clsCOL.COL_LARGEUR)

        oTAF     = clsTAF(taf_id=taf_id) if taf_id else None
        taf_code = (oTAF.taf_code or "") if (oTAF and oTAF.taf_id) else ""

        oLCO      = clsLCO(col_id=col_id, lan_id=lan_id) if lan_id else None
        lco_existe = bool(oLCO and oLCO.col_id)
        lco_label  = (oLCO.lco_label       or "") if lco_existe else ""
        lco_court  = (oLCO.lco_label_court or "") if lco_existe else ""
        lco_bulle  = (oLCO.lco_tooltip     or "") if lco_existe else ""
        larg_txt   = str(largeur) if largeur is not None else ""

        item = QTreeWidgetItem([""] * 6)
        item.setText(_C_NOM,   col_row[clsCOL.COL_NOM])
        item.setText(_C_TYPE,  taf_code)
        item.setText(_C_LARG,  larg_txt)
        item.setText(_C_LABEL, lco_label)
        item.setText(_C_COURT, lco_court)
        item.setText(_C_BULLE, lco_bulle)

        item.setData(_C_NOM,  _ROLE_META, {
            "type": "col", "col_id": col_id, "lan_id": lan_id,
            "taf_id_orig": taf_id, "lco_existe": lco_existe,
        })
        item.setData(_C_TYPE,  _ROLE_TAF,  taf_id)
        item.setData(_C_TYPE,  _ROLE_ORIG, taf_code)
        item.setData(_C_LARG,  _ROLE_ORIG, larg_txt)
        item.setData(_C_LABEL, _ROLE_ORIG, lco_label)
        item.setData(_C_COURT, _ROLE_ORIG, lco_court)
        item.setData(_C_BULLE, _ROLE_ORIG, lco_bulle)

        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        return item

    # ──────────────────────────────────────────────────────────────────────
    # Détection des modifications
    # ──────────────────────────────────────────────────────────────────────

    def _on_cellule_modifiee(self, item: QTreeWidgetItem, col: int):
        data  = item.data(_C_NOM, _ROLE_META) or {}
        ntype = data.get("type")
        if ntype not in ("rel", "col"):
            return
        orig = item.data(col, _ROLE_ORIG)
        if item.text(col) != (orig or ""):
            self._item_sale = item

    def _on_item_change(self, courant: QTreeWidgetItem, precedent: QTreeWidgetItem):
        if precedent and precedent is self._item_sale:
            self._sauver_item(precedent)

    # ──────────────────────────────────────────────────────────────────────
    # Sauvegarde
    # ──────────────────────────────────────────────────────────────────────

    def _sauver_item(self, item: QTreeWidgetItem):
        if item is None:
            return
        data  = item.data(_C_NOM, _ROLE_META) or {}
        ntype = data.get("type")
        try:
            if ntype == "rel":
                ok = self._sauver_rel(item, data)
            elif ntype == "col":
                ok = self._sauver_col(item, data)
            else:
                return
            if ok:
                self._item_sale = None
        except Exception as e:
            self._log.error(f"IhmMaintenanceVue._sauver_item : {e}")
            QMessageBox.critical(self, "Erreur de sauvegarde", str(e))

    def _sauver_rel(self, item: QTreeWidgetItem, data: dict) -> bool:
        rel_id = data["rel_id"]
        lan_id = data["lan_id"]
        label  = item.text(_C_LABEL).strip()

        if not label:
            QMessageBox.warning(self, "Libellé manquant",
                                "Le libellé de la relation est obligatoire.")
            QTimer.singleShot(0, lambda: self._arbre.editItem(item, _C_LABEL))
            return False

        if data.get("lre_existe"):
            oLRE           = clsLRE(rel_id=rel_id, lan_id=lan_id)
            oLRE.lre_label = label
            oLRE.update()
        else:
            oLRE           = clsLRE()
            oLRE.rel_id    = rel_id
            oLRE.lan_id    = lan_id
            oLRE.lre_label = label
            oLRE.insert()
            data["lre_existe"] = True

        oLRE.ogEngine.commit()
        self._arbre.blockSignals(True)
        item.setData(_C_NOM,   _ROLE_META,  data)
        item.setData(_C_LABEL, _ROLE_ORIG,  label)
        self._arbre.blockSignals(False)
        return True

    def _sauver_col(self, item: QTreeWidgetItem, data: dict) -> bool:
        col_id = data["col_id"]
        lan_id = data["lan_id"]
        label  = item.text(_C_LABEL).strip()

        if not label:
            QMessageBox.warning(self, "Libellé manquant",
                                "Le libellé long de la colonne est obligatoire.")
            QTimer.singleShot(0, lambda: self._arbre.editItem(item, _C_LABEL))
            return False

        # ── COL : taf_id + largeur ──
        nouveau_taf = item.data(_C_TYPE, _ROLE_TAF)
        larg_txt    = item.text(_C_LARG).strip()
        nouveau_larg = int(larg_txt) if larg_txt.isdigit() else None

        oCOL = clsCOL(col_id=col_id)
        modifie_col = False
        if nouveau_taf is not None and nouveau_taf != oCOL.taf_id:
            oCOL.taf_id = nouveau_taf
            modifie_col = True
        if nouveau_larg != oCOL.col_largeur:
            oCOL.col_largeur = nouveau_larg
            modifie_col = True
        if modifie_col:
            oCOL.update()
            oCOL.ogEngine.commit()

        # ── LCO : libellés ──
        court = item.text(_C_COURT).strip()[:15] or label[:15]
        bulle = item.text(_C_BULLE).strip() or None

        if data.get("lco_existe"):
            oLCO                 = clsLCO(col_id=col_id, lan_id=lan_id)
            oLCO.lco_label       = label
            oLCO.lco_label_court = court
            oLCO.lco_tooltip     = bulle
            oLCO.update()
        else:
            oLCO                 = clsLCO()
            oLCO.col_id          = col_id
            oLCO.lan_id          = lan_id
            oLCO.lco_label       = label
            oLCO.lco_label_court = court
            oLCO.lco_tooltip     = bulle
            oLCO.insert()
            data["lco_existe"] = True

        oLCO.ogEngine.commit()

        self._arbre.blockSignals(True)
        item.setData(_C_NOM,   _ROLE_META,  data)
        item.setData(_C_TYPE,  _ROLE_ORIG,  item.text(_C_TYPE))
        item.setData(_C_LARG,  _ROLE_ORIG,  larg_txt)
        item.setData(_C_LABEL, _ROLE_ORIG,  label)
        item.setData(_C_COURT, _ROLE_ORIG,  court)
        item.setData(_C_BULLE, _ROLE_ORIG,  bulle or "")
        self._arbre.blockSignals(False)
        return True

    # ──────────────────────────────────────────────────────────────────────
    # Navigation Tab
    # ──────────────────────────────────────────────────────────────────────

    def _on_tab(self, col: int, retour: bool):
        item  = self._arbre.currentItem()
        if not item:
            return
        data  = item.data(_C_NOM, _ROLE_META) or {}
        ntype = data.get("type")
        cols  = _COLS_REL if ntype == "rel" else (_COLS_COL if ntype == "col" else ())
        if not cols:
            return

        try:
            idx = cols.index(col)
        except ValueError:
            idx = -1

        if not retour:
            if idx < len(cols) - 1:
                cible = cols[idx + 1]
                QTimer.singleShot(0, lambda c=cible: self._arbre.editItem(item, c))
            else:
                prochain = self._prochain_editable(item)
                if prochain:
                    self._arbre.setCurrentItem(prochain)
                    d = prochain.data(_C_NOM, _ROLE_META) or {}
                    premiere = _COLS_REL[0] if d.get("type") == "rel" else _COLS_COL[0]
                    QTimer.singleShot(0, lambda p=prochain, c=premiere: self._arbre.editItem(p, c))
        else:
            if idx > 0:
                cible = cols[idx - 1]
                QTimer.singleShot(0, lambda c=cible: self._arbre.editItem(item, c))
            else:
                prec = self._precedent_editable(item)
                if prec:
                    self._arbre.setCurrentItem(prec)
                    d = prec.data(_C_NOM, _ROLE_META) or {}
                    derniere = _COLS_REL[-1] if d.get("type") == "rel" else _COLS_COL[-1]
                    QTimer.singleShot(0, lambda p=prec, c=derniere: self._arbre.editItem(p, c))

    def _prochain_editable(self, item: QTreeWidgetItem) -> QTreeWidgetItem | None:
        it = self._arbre.itemBelow(item)
        while it:
            ntype = (it.data(_C_NOM, _ROLE_META) or {}).get("type")
            if ntype in ("rel", "col"):
                return it
            it = self._arbre.itemBelow(it)
        return None

    def _precedent_editable(self, item: QTreeWidgetItem) -> QTreeWidgetItem | None:
        it = self._arbre.itemAbove(item)
        while it:
            ntype = (it.data(_C_NOM, _ROLE_META) or {}).get("type")
            if ntype in ("rel", "col"):
                return it
            it = self._arbre.itemAbove(it)
        return None
