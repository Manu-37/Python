# BaseRef_UICore.py
from sysclasses.ui.UI_Core import UI_Core
from .views.Environment_ListView import Environment_ListView
from .views.Base_ListView import Base_ListView
from .views.Bas_Env_ListView import Bas_Env_ListView
import customtkinter as ctk

class BaseRef_UICore(UI_Core):
    """
    UI spécifique à BaseRef.
    Définit les tailles de fenêtre par défaut et gère le menu + content_frame.
    """

    def __init__(self):
        # Paramètres de fenêtre par défaut pour BaseRef
        super().__init__(width=1024, height=768, min_width=800, min_height=600)

        self.title("BaseRef Manager")  # Titre explicite pour le projet

        # Dictionnaire des vues disponibles
        self.views = {
            "Environnements": Environment_ListView,
            "Bases de données": Base_ListView,
            "Paramétrages bases par environnement": Bas_Env_ListView,
            # Ajouter d'autres entités si nécessaire
        }

        # Création des boutons dans le menu gauche
        self._build_menu_buttons()

        # Affichage par défaut
        self.current_view = None
        self.show_view("Environnements")

    # -------------------------
    # Boutons du menu
    # -------------------------
    def _build_menu_buttons(self):
        for entity_name in self.views.keys():
            btn = ctk.CTkButton(
                self.menu_frame,
                text=entity_name,
                command=lambda name=entity_name: self.show_view(name),
                corner_radius=0,
                fg_color=self.UIColors.PRIMARY,
                hover_color=self.UIColors.SECONDARY,
            )
            btn.pack(fill="x", padx=5, pady=2)

    # -------------------------
    # Affichage d'une vue
    # -------------------------
    def show_view(self, view_name: str):
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

        view_cls = self.views.get(view_name)
        if view_cls:
            self.current_view = view_cls(self.content_frame, ui_colors=self.UIColors)
            self.current_view.pack(expand=True, fill="both")
        else:
            label = ctk.CTkLabel(self.content_frame, text=f"Vue '{view_name}' non trouvée")
            label.pack(expand=True, fill="both")