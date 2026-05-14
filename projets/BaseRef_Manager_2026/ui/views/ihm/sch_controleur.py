# ui/views/ihm/sch_controleur.py

from PyQt6.QtWidgets import QPushButton, QMessageBox
from sysclasses.ui import QtControleur
from db.db_baseref.ihm import clsSCH, clsREL, clsCOL
from .rel_controleur import RELControleur


class SCHControleur(QtControleur):
    """
    Contrôleur de la page Schémas.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsSCH
    _ordre_tri     = clsSCH.SCH_NOM

    def _etendre_toolbar_liste(self, barre):
        self._btn_voir_schemas = QPushButton("Voir les relations (tables et vues)")
        self._btn_voir_schemas.setEnabled(False)
        self._btn_voir_schemas.clicked.connect(self._on_voir_relations)
        barre.addWidget(self._btn_voir_schemas)

    def _on_selection(self, ligne):
        self._btn_voir_schemas.setEnabled(ligne is not None)

    def _on_voir_relations(self):
        ligne = self._vue_liste.ligne_selectionnee
        if not ligne:
            return
        sch_id  = ligne.get(clsSCH.SCH_ID)
        libelle = f"Relations (tables et vues) — {ligne.get(clsSCH.SCH_NOM)}"
        self._ouvrir_onglet(libelle, RELControleur(
            where_clause=f"{clsSCH.SCH_ID} = {sch_id}"
        ))

    def _confirmer_suppression(self, entite) -> bool:
        relations = clsREL.load_all(where_clause=f"sch_id = {entite.sch_id}")
        nb_rel    = len(relations)
        if nb_rel == 0:
            return super()._confirmer_suppression(entite)

        nb_col = sum(
            len(clsCOL.load_all(where_clause=f"rel_id = {r[clsREL.REL_ID]}"))
            for r in relations
        )
        msg = (
            f"Supprimer le schéma « {entite.sch_nom} » entraînera la suppression de :\n"
            f"  • {nb_rel} relation(s)\n"
            f"  • {nb_col} colonne(s)\n"
            f"  • tous les libellés associés\n\n"
            f"Cette opération est irréversible. Confirmer ?"
        )
        reponse = QMessageBox.question(
            self, "Suppression en cascade", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reponse == QMessageBox.StandardButton.Yes
