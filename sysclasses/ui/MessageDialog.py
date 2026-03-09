import customtkinter as ctk


class MessageDialog(ctk.CTkToplevel):

    # Dimensions fixes de la boîte — centralisées ici pour le calcul de position
    _DLG_WIDTH  = 420
    _DLG_HEIGHT = 180

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        buttons: list[tuple[str, str]]
    ):
        """
        Boîte de dialogue modale générique, centrée sur la fenêtre parente.
        buttons = [("OK", "ok"), ("Annuler", "cancel")]
        Le second élément est la valeur retournée par dlg.result.
        """
        super().__init__(parent)

        self.result = None
        self.title(title)
        self.resizable(False, False)

        # Modal
        self.transient(parent)
        self.grab_set()

        # Centrage sur la fenêtre principale.
        # winfo_toplevel() remonte l'arbre des widgets jusqu'à la vraie fenêtre
        # (Tk ou Toplevel), quelle que soit la profondeur du widget appelant.
        # Sans ça, on se centrerait sur le frame qui a ouvert la dialog.
        # update_idletasks() force Tkinter à calculer les vraies dimensions
        # avant qu'on lise winfo_width() / winfo_height().
        self.update_idletasks()
        top = parent.winfo_toplevel()
        px = top.winfo_rootx()
        py = top.winfo_rooty()
        pw = top.winfo_width()
        ph = top.winfo_height()
        x = px + (pw - self._DLG_WIDTH)  // 2
        y = py + (ph - self._DLG_HEIGHT) // 2
        self.geometry(f"{self._DLG_WIDTH}x{self._DLG_HEIGHT}+{x}+{y}")

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Message
        lbl_message = ctk.CTkLabel(
            self,
            text=message,
            wraplength=380,
            justify="center"
        )
        lbl_message.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

        # Frame boutons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=(10, 20))

        # Création dynamique des boutons
        for i, (text, value) in enumerate(buttons):
            btn = ctk.CTkButton(
                btn_frame,
                text=text,
                width=100,
                command=lambda v=value: self._on_click(v)
            )
            btn.grid(row=0, column=i, padx=10)

        # Attendre fermeture (modal réel)
        self.wait_window()

    def _on_click(self, value):
        self.result = value
        self.destroy()

    # --------------------------------------------------
    # Méthodes statiques utilitaires
    # --------------------------------------------------

    @staticmethod
    def info(parent, title: str, message: str):
        """Boîte d'information simple — bouton OK."""
        dlg = MessageDialog(
            parent, title, message,
            buttons=[("OK", "ok")]
        )
        return dlg.result

    @staticmethod
    def error(parent, title: str, message: str):
        """
        Boîte d'erreur — bouton OK.
        Identique à info() mais sémantiquement distincte
        (permet une future mise en forme différente : icône rouge, etc.).
        """
        dlg = MessageDialog(
            parent, title, message,
            buttons=[("OK", "ok")]
        )
        return dlg.result

    @staticmethod
    def warning(parent, title: str, message: str):
        """Boîte d'avertissement — bouton OK."""
        dlg = MessageDialog(
            parent, title, message,
            buttons=[("OK", "ok")]
        )
        return dlg.result

    @staticmethod
    def confirm(parent, title: str, message: str, confirm_label: str = "Valider") -> bool:
        """
        Boîte de confirmation — bouton d'action / bouton d'annulation.
        confirm_label : libellé du bouton de confirmation (ex: "Supprimer", "Enregistrer").
        Le bouton d'annulation est construit automatiquement : "Ne pas supprimer", "Ne pas enregistrer"...
        Retourne True si confirmé.
        """
        cancel_label = f"Ne pas {confirm_label.lower()}"
        dlg = MessageDialog(
            parent, title, message,
            buttons=[(confirm_label, "ok"), (cancel_label, "cancel")]
        )
        return dlg.result == "ok"