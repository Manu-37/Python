# sysclasses/ui/qt/qt_libelles_vue.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit
)
from PyQt6.QtCore import Qt
from sysclasses.exceptions import ErreurValidationBloquante, AvertissementValidation


class QtLibellesVue(QWidget):
    """
    Éditeur inline multilingue générique.

    Affiche une ligne par langue active (ordonnée par lan_ordre).
    Les deux premières colonnes (code, nom langue) sont en lecture seule.
    Les colonnes éditables sont définies par le paramètre `colonnes`.

    Paramètres
    ----------
    classe_entite  : classe entité libellé (ex. clsLCO)
    col_fk_parent  : nom de la colonne FK vers le parent (ex. "col_id")
    col_fk_langue  : nom de la colonne FK vers la langue  (ex. "lan_id")
    colonnes       : [(nom_attribut, libelle_en_tete), ...]

    API publique
    ------------
    charger(entite_parente)              — charge les libellés existants
    enregistrer(entite_parente) → (bool, str)  — valide puis persiste
    """

    def __init__(self, classe_entite, col_fk_parent: str, col_fk_langue: str,
                 colonnes: list[tuple[str, str]], parent=None):
        super().__init__(parent)
        self._classe_entite  = classe_entite
        self._col_fk_parent  = col_fk_parent
        self._col_fk_langue  = col_fk_langue
        self._colonnes       = colonnes       # [(nom_col, libelle), ...]
        self._entite_parente = None
        self._lignes: dict[int, object] = {} # lan_id → entité libellé chargée depuis DB

        self._langues = self._charger_langues()
        self._construire_tableau()

    # ─── Initialisation ───────────────────────────────────────────────────────

    def _charger_langues(self) -> list:
        from db.db_baseref.ihm.clsLAN import clsLAN
        rows = clsLAN.load_all(where_clause="lan_actif = TRUE", order_by="lan_ordre")
        return clsLAN.DepuisResultat(rows)

    def _construire_tableau(self):
        nb_cols = 2 + len(self._colonnes)
        self._tableau = QTableWidget(len(self._langues), nb_cols, self)
        self._tableau.setHorizontalHeaderLabels(
            ["Code", "Langue"] + [lib for _, lib in self._colonnes]
        )
        self._tableau.verticalHeader().setVisible(False)
        self._tableau.horizontalHeader().setStretchLastSection(True)
        self._tableau.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        for i, lan in enumerate(self._langues):
            for col_idx, texte in enumerate([lan.lan_code, lan.lan_nom]):
                item = QTableWidgetItem(texte)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._tableau.setItem(i, col_idx, item)
            for j in range(len(self._colonnes)):
                self._tableau.setCellWidget(i, 2 + j, QLineEdit())

        layout = QVBoxLayout(self)
        layout.addWidget(self._tableau)
        layout.setContentsMargins(0, 0, 0, 0)

    # ─── API publique ─────────────────────────────────────────────────────────

    def vider(self):
        self._entite_parente = None
        self._lignes.clear()
        for i in range(len(self._langues)):
            for j in range(len(self._colonnes)):
                edit = self._tableau.cellWidget(i, 2 + j)
                if isinstance(edit, QLineEdit):
                    edit.setText("")

    def charger(self, entite_parente):
        self._entite_parente = entite_parente
        id_parent = getattr(entite_parente, self._col_fk_parent)

        rows = self._classe_entite.load_all(
            where_clause=f"{self._col_fk_parent} = {id_parent}"
        )
        self._lignes = {
            getattr(e, self._col_fk_langue): e
            for e in self._classe_entite.DepuisResultat(rows)
        }

        for i, lan in enumerate(self._langues):
            entite = self._lignes.get(lan.lan_id)
            for j, (nom_col, _) in enumerate(self._colonnes):
                edit = self._tableau.cellWidget(i, 2 + j)
                if isinstance(edit, QLineEdit):
                    valeur = getattr(entite, nom_col, None) if entite else None
                    edit.setText(str(valeur) if valeur is not None else "")

    def enregistrer(self, entite_parente) -> tuple[bool, str]:
        id_parent  = getattr(entite_parente, self._col_fk_parent)
        operations = []  # (entite, action, valeurs) — action ∈ {'insert','update','delete'}
        erreurs    = []

        # ── Passe 1 : lecture + validation ───────────────────────────
        for i, lan in enumerate(self._langues):
            valeurs = {}
            for j, (nom_col, libelle) in enumerate(self._colonnes):
                edit = self._tableau.cellWidget(i, 2 + j)
                valeurs[nom_col] = edit.text().strip() if isinstance(edit, QLineEdit) else ""

            toutes_vides = all(v == "" for v in valeurs.values())
            existante    = self._lignes.get(lan.lan_id)

            if toutes_vides:
                if existante:
                    operations.append((existante, "delete", {}))
                # sinon skip — rien à faire pour cette langue
            elif existante:
                operations.append((existante, "update", valeurs))
            else:
                nouvelle = self._classe_entite()
                setattr(nouvelle, self._col_fk_parent, id_parent)
                setattr(nouvelle, self._col_fk_langue,  lan.lan_id)
                operations.append((nouvelle, "insert", valeurs))

        # ── Passe 2 : persistance ────────────────────────────────────
        for entite, action, valeurs in operations:
            try:
                if action == "delete":
                    entite.delete()
                    self._lignes.pop(getattr(entite, self._col_fk_langue), None)
                else:
                    for nom_col, valeur in valeurs.items():
                        setattr(entite, nom_col, valeur)
                    if action == "insert":
                        entite.insert()
                        self._lignes[getattr(entite, self._col_fk_langue)] = entite
                    else:
                        entite.update()
            except AvertissementValidation:
                pass  # donnée persistée — avertissement non bloquant
            except ErreurValidationBloquante as e:
                erreurs.append(str(e))
            except Exception as e:
                erreurs.append(str(e))

        if erreurs:
            return True, "\n".join(erreurs)
        return False, ""
