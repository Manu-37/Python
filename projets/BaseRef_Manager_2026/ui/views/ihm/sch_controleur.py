# ui/views/ihm/sch_controleur.py

from PyQt6.QtWidgets import QPushButton
from sysclasses.ui import QtControleur
from db.db_baseref.ihm import clsSCH
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
        sch_id   = ligne.get(clsSCH.SCH_ID)
        libelle = f"Relations (tables et vues) — {ligne.get(clsSCH.SCH_NOM)}"
        self._ouvrir_onglet(libelle, RELControleur(
            where_clause=f"{clsSCH.SCH_ID} = {sch_id}"
        ))