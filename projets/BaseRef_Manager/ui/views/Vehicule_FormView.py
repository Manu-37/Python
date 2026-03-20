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
        - Bouton "Récupérer les données" présent dans tous les modes,
          grisé en INSERT (pas de token associé à un véhicule non encore créé).
        - _check() : délègue entièrement à clsTeslaVehicle.save_snapshot(),
          affiche le résultat via une fenêtre dédiée avec lien cliquable.
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
    # Action — délègue tout à la couche métier
    # --------------------------------------------------

    def _check(self):
        """
        Déclenche la récupération et la sauvegarde du snapshot Tesla.
        Toute la logique métier est dans clsTeslaVehicle.save_snapshot().
        Cette méthode ne fait que piloter l'UI : appel → résultat → affichage.
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
        """
        Affiche une fenêtre modale avec le nom du fichier créé.
        Le lien est cliquable — ouvre le fichier dans l'explorateur Windows.
        """
        dlg = ctk.CTkToplevel(self)
        dlg.title("Données récupérées")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        # Centrage sur la fenêtre parente
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

        # Lien cliquable — underline simulé via la couleur et le curseur
        lbl_lien = ctk.CTkLabel(
            dlg,
            text=chemin.name,
            font=ctk.CTkFont(size=12, underline=True),
            text_color="#1F6AA5",
            cursor="hand2"
        )
        lbl_lien.grid(row=1, column=0, padx=20, pady=(0, 6))

        # Clic → ouvre l'explorateur Windows positionné sur le fichier
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