import customtkinter as ctk
from sysclasses.ui.Entity_ListView import Entity_ListView
from sysclasses.ui.MessageDialog import MessageDialog
from db.db_tstat_admin.public.clsVEH import clsVEH as clsVEH_Admin
from .Vehicule_FormView import Vehicule_FormView


class Vehicule_ListView(Entity_ListView):
    """
    Vue liste des véhicules Tesla.

    Extension par rapport à Entity_ListView :
        - Bouton "Synchroniser" dans la toolbar — force la resynchronisation
          de tous les véhicules depuis db_tstat_admin vers db_tstat_data.
          Usage : peuplement initial ou rattrapage d'une désynchronisation.
    """

    def __init__(self, parent, ui_colors=None):
        super().__init__(
            parent,
            entity_class=clsVEH_Admin,
            order_by=clsVEH_Admin.VEH_VIN,
            form_class=Vehicule_FormView,
            ui_colors=ui_colors
        )

    # --------------------------------------------------
    # Hook toolbar
    # --------------------------------------------------

    def _extend_toolbar(self):
        ctk.CTkButton(
            self.toolbar,
            text="Synchroniser",
            command=self._sync_tous
        ).pack(side="left", padx=(20, 5))  # marge gauche pour séparer visuellement des boutons CRUD

    # --------------------------------------------------
    # Synchronisation globale admin → data
    # --------------------------------------------------

    def _sync_tous(self):
        """
        Force la resynchronisation de tous les véhicules
        depuis db_tstat_admin vers db_tstat_data.

        Pour chaque véhicule admin :
            - S'il n'existe pas dans data → INSERT
            - S'il existe déjà            → UPDATE

        Le commit est réalisé ici — c'est cette méthode qui pilote
        l'ensemble de l'opération, elle est donc maître de la transaction.
        """
        from db.db_tstat_data.public.clsVEH import clsVEH as clsVEH_Data

        # Chargement de tous les véhicules admin
        tous_admin = clsVEH_Admin.load_all()

        if not tous_admin:
            MessageDialog.info(self, "Synchronisation", "Aucun véhicule à synchroniser.")
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
            MessageDialog.error(
                self,
                "Synchronisation — Erreurs",
                f"Des erreurs ont empêché la synchronisation complète.\n\n{detail}\n\n"
                "Aucune modification n'a été enregistrée dans db_tstat_data."
            )
        else:
            engine_data.commit()
            MessageDialog.info(
                self,
                "Synchronisation terminée",
                f"Synchronisation effectuée avec succès.\n\n"
                f"Insérés : {nb_inseres}\n"
                f"Mis à jour : {nb_maj}"
            )