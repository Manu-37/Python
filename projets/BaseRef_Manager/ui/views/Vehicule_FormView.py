import os
import customtkinter as ctk
from pathlib import Path

from sysclasses.ui.AutoFormView import AutoFormView
from sysclasses.ui.MessageDialog import MessageDialog
from sysclasses.clsLOG import clsLOG


class Vehicule_FormView(AutoFormView):
    """
    Formulaire spécifique pour la table Véhicules Tesla.

    Extension par rapport à AutoFormView :
        - Bouton "Récupérer les données" — grisé en INSERT.
        - _after_save() : après chaque enregistrement réussi en admin,
          le véhicule est immédiatement répercuté dans db_tstat_data.
          En cas d'échec de la partie data, un message explicite est affiché
          mais l'opération admin reste commitée (risque accepté — même serveur).
        - _check() : délègue à clsTeslaVehicle.save_snapshot().
    """

    def __init__(self, parent, entity_instance, mode, ui_colors=None):
        self._log = clsLOG()
        super().__init__(parent, entity_instance, mode, ui_colors=ui_colors)

    # --------------------------------------------------
    # Hook boutons
    # --------------------------------------------------

    def _extend_buttons(self):
        """
        Ajoute le bouton "Récupérer les données" après les boutons standards.
        Grisé en INSERT — l'entité n'a pas encore de veh_id ni de token associé.
        """
        self._btn_recuperer = ctk.CTkButton(
            self._frame_btn,
            text="Récupérer les données",
            command=self._check
        )
        self._btn_recuperer.pack(side="left", padx=5)

        if self.mode == "INSERT":
            self._btn_recuperer.configure(state="disabled")

    # --------------------------------------------------
    # Hook après sauvegarde — synchronisation automatique
    # --------------------------------------------------

    def _after_save(self):
        """
        Appelé automatiquement par AutoFormView._save() après chaque
        opération CRUD réussie et commitée en admin.

        Répercute le véhicule concerné dans db_tstat_data :
            - INSERT si le véhicule est nouveau dans data
            - UPDATE si le véhicule existe déjà dans data
            - En cas de DELETE en admin → veh_isactive = False dans data
              (jamais de DELETE réel — l'historique des snapshots est préservé)

        Le commit data est réalisé ici.
        En cas d'échec, un message explicite est affiché — l'admin reste intact.
        """
        self._sync_un(self.entity)

    def _sync_un(self, oAdmin):
        """
        Synchronise un véhicule depuis db_tstat_admin vers db_tstat_data.

        Paramètre :
            oAdmin : instance clsVEH (admin) avec veh_id valide.

        Comportement selon le mode :
            INSERT / UPDATE : INSERT ou UPDATE dans data selon existence
            DELETE          : passe veh_isactive = False dans data
        """
        from db.db_tstat_data.public.clsVEH import clsVEH as clsVEH_Data

        try:
            oData = clsVEH_Data(veh_id=oAdmin.veh_id)

            if self.mode == "DELETE":
                # Suppression admin → désactivation dans data (historique préservé)
                if oData.veh_id is not None:
                    oData.veh_isactive = False
                    oData.update()
                # Si absent de data, rien à faire
            else:
                if oData.veh_id is None:
                    # Nouveau véhicule → INSERT dans data
                    oData.veh_id              = oAdmin.veh_id
                    oData.veh_vin             = oAdmin.veh_vin
                    oData.veh_displayname     = oAdmin.veh_displayname
                    oData.veh_pollinginterval = oAdmin.veh_pollinginterval
                    oData.veh_isactive        = oAdmin.veh_isactive
                    oData.insert()
                else:
                    # Véhicule existant → UPDATE dans data
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
            self._log.error(f"Vehicule_FormView._sync_un | {msg}")
            MessageDialog.error(self, "Synchronisation data", msg)

    # --------------------------------------------------
    # Action — délègue tout à la couche métier
    # --------------------------------------------------

    def _check(self):
        """
        Déclenche la récupération et la sauvegarde du snapshot Tesla.
        Toute la logique métier est dans clsTeslaVehicle.save_snapshot().
        """
        veh_vin = self.entity.veh_vin

        if not veh_vin:
            MessageDialog.error(self, "Données manquantes", "Le VIN du véhicule est absent.")
            return

        try:
            from projets.shared.tesla.clsTeslaAuth import clsTeslaAuth
            from projets.shared.tesla.clsTeslaVehicle import clsTeslaVehicle

            auth    = clsTeslaAuth(veh_id=self.entity.veh_id)
            vehicle = clsTeslaVehicle(auth)

        except ValueError as e:
            msg = f"Configuration Tesla absente pour ce véhicule.\n\nDétail : {e}"
            self._log.error(f"Vehicule_FormView._check | {msg}")
            MessageDialog.error(self, "Erreur d'authentification", msg)
            return

        except Exception as e:
            msg = f"Impossible d'initialiser l'authentification Tesla.\n\nDétail : {e}"
            self._log.error(f"Vehicule_FormView._check | {msg}")
            MessageDialog.error(self, "Erreur d'authentification", msg)
            return

        resultat = vehicle.save_snapshot(veh_vin)

        if resultat["erreur"]:
            self._log.error(f"Vehicule_FormView._check | {resultat['erreur']}")
            MessageDialog.error(self, "Erreur API Tesla", resultat["erreur"])
            return

        self._afficher_succes(resultat["chemin"])

    # --------------------------------------------------
    # Fenêtre de succès avec lien cliquable
    # --------------------------------------------------

    def _afficher_succes(self, chemin: Path):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Données récupérées")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        dlg.update_idletasks()
        top = self.winfo_toplevel()
        x = top.winfo_rootx() + (top.winfo_width()  - 480) // 2
        y = top.winfo_rooty() + (top.winfo_height() - 160) // 2
        dlg.geometry(f"480x160+{x}+{y}")

        dlg.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dlg,
            text="Snapshot Tesla enregistré avec succès.",
            font=ctk.CTkFont(size=13)
        ).grid(row=0, column=0, padx=20, pady=(20, 6))

        lbl_lien = ctk.CTkLabel(
            dlg,
            text=chemin.name,
            font=ctk.CTkFont(size=12, underline=True),
            text_color="#1F6AA5",
            cursor="hand2"
        )
        lbl_lien.grid(row=1, column=0, padx=20, pady=(0, 6))

        lbl_lien.bind(
            "<Button-1>",
            lambda e: os.startfile(chemin.parent)
        )

        ctk.CTkButton(
            dlg,
            text="OK",
            width=100,
            command=dlg.destroy
        ).grid(row=2, column=0, pady=(6, 20))

        dlg.wait_window()