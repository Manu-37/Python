# ui/views/ihm/db_controleur.py

from PyQt6.QtWidgets import QPushButton
from sysclasses.ui import QtControleur
from db.db_baseref.ihm import clsDB, clsSCH
from .sch_controleur import SCHControleur


class DBControleur(QtControleur):
    _classe_entite = clsDB
    _ordre_tri     = clsDB.DB_CODE

    def _etendre_toolbar_liste(self, barre):
        self._btn_voir_schemas = QPushButton("Voir les schémas")
        self._btn_voir_schemas.setEnabled(False)
        self._btn_voir_schemas.clicked.connect(self._on_voir_schemas)
        barre.addWidget(self._btn_voir_schemas)

    def _on_selection(self, ligne):
        self._btn_voir_schemas.setEnabled(ligne is not None)

    def _on_voir_schemas(self):
        ligne = self._vue_liste.ligne_selectionnee
        if not ligne:
            return
        db_id   = ligne.get(clsDB.DB_ID)
        libelle = f"Schémas — {ligne.get(clsDB.DB_NOM)}"
        self._ouvrir_onglet(libelle, SCHControleur(
            where_clause=f"{clsSCH.DB_ID} = {db_id}"
        ))
