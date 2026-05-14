# ui/views/ihm/db_controleur.py

from PyQt6.QtWidgets import QPushButton, QMessageBox
from sysclasses.ui import QtControleur
from db.db_baseref.ihm import clsDB, clsSCH
from .sch_controleur      import SCHControleur
from .db_explorateur      import DbExplorateur
from .ihm_maintenance_vue import IhmMaintenanceVue


class DBControleur(QtControleur):
    _classe_entite = clsDB
    _ordre_tri     = clsDB.DB_CODE

    def _etendre_toolbar_liste(self, barre):
        self._btn_voir_schemas = QPushButton("Voir les schémas")
        self._btn_voir_schemas.setEnabled(False)
        self._btn_voir_schemas.clicked.connect(self._on_voir_schemas)
        barre.addWidget(self._btn_voir_schemas)

        self._btn_explorer = QPushButton("Explorer la base")
        self._btn_explorer.setEnabled(False)
        self._btn_explorer.clicked.connect(self._on_explorer)
        barre.addWidget(self._btn_explorer)

        self._btn_maintenance = QPushButton("Maintenir les libellés IHM")
        self._btn_maintenance.setEnabled(False)
        self._btn_maintenance.clicked.connect(self._on_maintenance)
        barre.addWidget(self._btn_maintenance)

    def _on_selection(self, ligne):
        has = ligne is not None
        self._btn_voir_schemas.setEnabled(has)
        self._btn_maintenance.setEnabled(has)
        if has:
            bas_id = ligne.get(clsDB.BAS_ID)
            self._btn_explorer.setEnabled(bool(bas_id))
        else:
            self._btn_explorer.setEnabled(False)

    def _on_voir_schemas(self):
        ligne = self._vue_liste.ligne_selectionnee
        if not ligne:
            return
        db_id   = ligne.get(clsDB.DB_ID)
        libelle = f"Schémas — {ligne.get(clsDB.DB_NOM)}"
        self._ouvrir_onglet(libelle, SCHControleur(
            where_clause=f"{clsSCH.DB_ID} = {db_id}"
        ))

    def _on_explorer(self):
        ligne = self._vue_liste.ligne_selectionnee
        if not ligne:
            return
        db_id = ligne.get(clsDB.DB_ID)
        oDb   = clsDB(db_id=db_id)
        if not oDb.bas_id:
            QMessageBox.warning(
                self, "Connexion manquante",
                "Cette base n'a pas de base physique configurée (bas_id).\n"
                "Renseignez bas_id dans la fiche avant d'explorer."
            )
            return
        libelle = f"Explorateur — {ligne.get(clsDB.DB_NOM)}"
        self._ouvrir_onglet(libelle, DbExplorateur(oDb))

    def _on_maintenance(self):
        ligne = self._vue_liste.ligne_selectionnee
        if not ligne:
            return
        db_id   = ligne.get(clsDB.DB_ID)
        oDb     = clsDB(db_id=db_id)
        libelle = f"IHM — {ligne.get(clsDB.DB_NOM)}"
        self._ouvrir_onglet(libelle, IhmMaintenanceVue(oDb))

    def _confirmer_suppression(self, entite) -> bool:
        nb = len(clsSCH.load_all(where_clause=f"db_id = {entite.db_id}"))
        if nb > 0:
            QMessageBox.warning(
                self, "Suppression impossible",
                f"Cette base contient {nb} schéma(s).\n"
                f"Supprimez d'abord tous les schémas avant de supprimer la base."
            )
            return False
        return super()._confirmer_suppression(entite)
