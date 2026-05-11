# ui/views/gestion_bases/veh_controleur.py

import os

from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QMessageBox
from sysclasses.ui.qt import QtControleur
from sysclasses.ui.qt import QtFicheVue

from db.db_tstat_admin.public.clsVEH import clsVEH as clsVEH_Admin
from db.db_tstat_data.public.clsVEH import clsVEH as clsVEH_Data



class VEHControleur(QtControleur):
    """
    Contrôleur de la page Véhicules.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsVEH_Admin
    _ordre_tri     = clsVEH_Admin.VEH_DISPLAYNAME

    def _etendre_toolbar_liste(self, barre: QHBoxLayout):
        """
        Ajoute un bouton de synchronisation entre db_tstat_admin et db_tstat_data.
        """
        btn_sync = QPushButton("Synchroniser")
        btn_sync.clicked.connect(self._on_sync_tous)
        barre.addWidget(btn_sync)


    def _on_sync_tous(self):       
        """
        Force la resynchronisation de tous les véhicules
        depuis db_tstat_admin vers db_tstat_data.

        Pour chaque véhicule admin :
            - S'il n'existe pas dans data → INSERT
            - S'il existe déjà            → UPDATE

        Le commit est réalisé ici — c'est cette méthode qui pilote
        l'ensemble de l'opération, elle est donc maître de la transaction.
        """
        
        # Chargement de tous les véhicules admin
        tous_admin = clsVEH_Admin.load_all()

        if not tous_admin:
            QMessageBox.information(self, "Synchronisation", "Aucun véhicule à synchroniser.")
            return

        engine_data = clsVEH_Data().ogEngine
        nb_inseres  = 0
        nb_maj      = 0
        erreurs     = []

        for ligne in tous_admin:
            veh_id = ligne.get(clsVEH_Admin.VEH_ID)
            try:
                # Recherche dans data par veh_id
                oData = clsVEH_Data(veh_id=veh_id)

                if oData.veh_id is None:
                    # Véhicule absent de data → INSERT
                    oData.veh_id              = ligne.get(clsVEH_Admin.VEH_ID)
                    oData.veh_vin             = ligne.get(clsVEH_Admin.VEH_VIN)
                    oData.veh_displayname     = ligne.get(clsVEH_Admin.VEH_DISPLAYNAME)
                    oData.veh_pollinginterval = ligne.get(clsVEH_Admin.VEH_POLLINGINTERVAL)
                    oData.veh_isactive        = ligne.get(clsVEH_Admin.VEH_ISACTIVE)
                    oData.insert()
                    nb_inseres += 1
                else:
                    # Véhicule présent → UPDATE
                    oData.veh_vin             = ligne.get(clsVEH_Admin.VEH_VIN)
                    oData.veh_displayname     = ligne.get(clsVEH_Admin.VEH_DISPLAYNAME)
                    oData.veh_pollinginterval = ligne.get(clsVEH_Admin.VEH_POLLINGINTERVAL)
                    oData.veh_isactive        = ligne.get(clsVEH_Admin.VEH_ISACTIVE)
                    oData.update()
                    nb_maj += 1

            except Exception as e:
                erreurs.append(f"veh_id={veh_id} : {e}")

        # Commit ou rollback selon le résultat global
        if erreurs:
            engine_data.rollback()
            detail = "\n".join(erreurs)
            QMessageBox.critical(
                self,
                "Synchronisation — Erreurs",
                f"Des erreurs ont empêché la synchronisation complète.\n\n{detail}\n\n"
                "Aucune modification n'a été enregistrée dans db_tstat_data."
            )
        else:
            engine_data.commit()
            QMessageBox.information(
                self,
                "Synchronisation terminée",
                f"Synchronisation effectuée avec succès.\n\n"
                f"Insérés : {nb_inseres}\n"
                f"Mis à jour : {nb_maj}"
            )

    def _etendre_boutons_fiche(self, fiche, barre):
        """
        Ajoute un bouton de regénération du token d'accès Tesla dans les fiches de véhicule.
        """
        fiche._btn_GetTeslaData = QPushButton("Récupérer données Tesla en fichier")
        fiche._btn_GetTeslaData.clicked.connect(lambda: self._on_get_tesla_data(fiche._entite))
        barre.addWidget(fiche._btn_GetTeslaData)
    
    def _on_get_tesla_data (self, oVEH: clsVEH_Admin):
        if not oVEH.veh_vin:
            QMessageBox.critical(self, "Données manquantes", "Le VIN du véhicule est absent.")
            return

        try:
            from projets.shared.tesla.clsTeslaAuth import clsTeslaAuth
            from projets.shared.tesla.clsTeslaVehicle import clsTeslaVehicle

            auth    = clsTeslaAuth(veh_id=oVEH.veh_id)
            vehicle = clsTeslaVehicle(auth)

        except ValueError as e:
            msg = f"Configuration Tesla absente pour ce véhicule.\n\nDétail : {e}"
            self._log.error(f"VEHControleur._on_regenerer_token | {msg}")
            QMessageBox.critical(self, "Erreur d'authentification", msg)
            return

        except Exception as e:
            msg = f"Impossible d'initialiser l'authentification Tesla.\n\nDétail : {e}"
            self._log.error(f"VEHControleur._on_regenerer_token | {msg}")
            QMessageBox.critical(self, "Erreur d'authentification", msg)
            return

        resultat = vehicle.save_snapshot(oVEH.veh_vin)

        if resultat["erreur"]:
            self._log.error(f"VEHControleur._on_regenerer_token | {resultat['erreur']}")
            QMessageBox.critical(self, "Erreur API Tesla", resultat["erreur"])
            return

        self._afficher_succes(resultat["chemin"])

    def _afficher_succes(self, chemin):
        boite = QMessageBox(self)
        boite.setWindowTitle("Données récupérées")
        boite.setText("Snapshot Tesla enregistré avec succès.")
        boite.setInformativeText(str(chemin.name))
        btn_ouvrir = boite.addButton("Ouvrir le dossier", QMessageBox.ButtonRole.ActionRole)
        boite.addButton(QMessageBox.StandardButton.Ok)
        boite.exec()
        if boite.clickedButton() == btn_ouvrir:
            os.startfile(chemin.parent)

    def _apres_enregistrement(self, entite):
        self._sync_un(entite, self._mode_courant)

    def _sync_un(self, oAdmin, mode: str):
        try:
            oData = clsVEH_Data(veh_id=oAdmin.veh_id)

            if mode == QtFicheVue.MODE_SUPPRESSION:
                if oData.veh_id is not None:
                    oData.veh_isactive = False
                    oData.update()
            else:
                if oData.veh_id is None:
                    oData.veh_id              = oAdmin.veh_id
                    oData.veh_vin             = oAdmin.veh_vin
                    oData.veh_displayname     = oAdmin.veh_displayname
                    oData.veh_pollinginterval = oAdmin.veh_pollinginterval
                    oData.veh_isactive        = oAdmin.veh_isactive
                    oData.insert()
                else:
                    oData.veh_vin             = oAdmin.veh_vin
                    oData.veh_displayname     = oAdmin.veh_displayname
                    oData.veh_pollinginterval = oAdmin.veh_pollinginterval
                    oData.veh_isactive        = oAdmin.veh_isactive
                    oData.update()

            oData.ogEngine.commit()

        except Exception as e:
            msg = (
                f"Le véhicule a été enregistré dans db_tstat_admin "
                f"mais la synchronisation vers db_tstat_data a échoué.\n\n"
                f"Utilisez le bouton 'Synchroniser' depuis la liste pour corriger.\n\n"
                f"Détail : {e}"
            )
            self._log.error(f"VEHControleur._sync_un | {msg}")
            QMessageBox.warning(self, "Synchronisation data", msg)

    def _apres_chargement_fiche(self, fiche, mode: str, entite):
        if hasattr(fiche, '_btn_GetTeslaData'):
            fiche._btn_GetTeslaData.setEnabled(mode != QtFicheVue.MODE_AJOUT)
