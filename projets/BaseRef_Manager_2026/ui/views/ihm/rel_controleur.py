# ui/views/ihm/rel_controleur.py

from PyQt6.QtWidgets import QPushButton, QMessageBox
from sysclasses.ui import QtControleur
from db.db_baseref.ihm import clsREL, clsCOL, clsLRE
from .col_controleur import COLControleur
from .lre_controleur import LREControleur


class RELControleur(QtControleur):
    """
    Contrôleur de la page Relations.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsREL
    _ordre_tri     = clsREL.SCH_ID + "," + clsREL.REL_NOM

    def _etendre_toolbar_liste(self, barre):
        self._btn_voir_colonnes = QPushButton("Voir les colonnes")
        self._btn_voir_colonnes.setEnabled(False)
        self._btn_voir_colonnes.clicked.connect(self._on_voir_colonnes)
        barre.addWidget(self._btn_voir_colonnes)

        self._btn_voir_lre = QPushButton("Voir les libellés de relation par langue")
        self._btn_voir_lre.setEnabled(False)
        self._btn_voir_lre.clicked.connect(self._on_voir_lre)
        barre.addWidget(self._btn_voir_lre)

    def _on_selection(self, ligne):
        self._btn_voir_colonnes.setEnabled(ligne is not None)
        self._btn_voir_lre.setEnabled(ligne is not None)

    def _on_voir_colonnes(self):
        ligne = self._vue_liste.ligne_selectionnee
        if not ligne:
            return
        rel_id  = ligne.get(clsREL.REL_ID)
        libelle = f"Colonnes — {ligne.get(clsREL.REL_NOM)}"
        self._ouvrir_onglet(libelle, COLControleur(
            where_clause=f"{clsCOL.REL_ID} = {rel_id}"
        ))

    def _on_voir_lre(self):
        ligne = self._vue_liste.ligne_selectionnee
        if not ligne:
            return
        rel_id  = ligne.get(clsREL.REL_ID)
        libelle = f"Libellés de relation — {ligne.get(clsREL.REL_NOM)}"
        self._ouvrir_onglet(libelle, LREControleur(
            where_clause=f"{clsLRE.REL_ID} = {rel_id}"
        ))

    def _confirmer_suppression(self, entite) -> bool:
        nb_col = len(clsCOL.load_all(where_clause=f"rel_id = {entite.rel_id}"))
        if nb_col == 0:
            return super()._confirmer_suppression(entite)

        msg = (
            f"Supprimer la relation « {entite.rel_nom} » entraînera la suppression de :\n"
            f"  • {nb_col} colonne(s)\n"
            f"  • tous les libellés associés\n\n"
            f"Cette opération est irréversible. Confirmer ?"
        )
        reponse = QMessageBox.question(
            self, "Suppression en cascade", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reponse == QMessageBox.StandardButton.Yes
