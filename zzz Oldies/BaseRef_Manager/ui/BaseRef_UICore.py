# BaseRef_UICore.py
from sysclasses.ui.UI_Core import UI_Core, MK_SEP, MK_BLANK, MK_BLANK_HEIGHT
from .views.Environment_ListView import Environment_ListView
from .views.Base_ListView import Base_ListView
from .views.Bas_Env_ListView import Bas_Env_ListView
from .views.Vehicule_ListView import Vehicule_ListView
from .views.Token_ListView import Token_ListView
from .views.Crypto_View import Crypto_View
from .views.Job_ListView import Job_ListView
import customtkinter as ctk


class BaseRef_UICore(UI_Core):
    """
    UI spécifique à BaseRef.
    Définit les tailles de fenêtre par défaut et gère le menu + content_frame.

    Structure du menu (_menu_definition) :
        Toutes les entrées sont des tuples (marqueur_ou_nom, classe_ou_None).
        - (nom,     classe) → bouton de navigation
        - (MK_SEP,  None)   → séparateur horizontal (ligne fine)
        - (MK_BLANK,None)   → espace blanc (~80% hauteur bouton)
    """

    def __init__(self):
        super().__init__(width=1024, height=768, min_width=800, min_height=600)
        self.title("BaseRef Manager")

        self._menu_definition = [
            # --- Groupe db_baseref ---
            ("Environnements",           Environment_ListView),
            ("Bases de données",         Base_ListView),
            ("Paramétrages bases / env", Bas_Env_ListView),
            (MK_SEP,   None),
            # --- Groupe Tesla ---
            ("Véhicules",                Vehicule_ListView),
            ("Tokens Tesla",             Token_ListView),
            (MK_BLANK, None),
            (MK_SEP,   None),
            # --- Groupe Utilitaires ---
            ("Chiffrement",              Crypto_View),
            #(MK_BLANK, None)
            (MK_SEP,   None),
            # --- Groupe Cron ---
            ("Tâches planifiées",        Job_ListView),
        ]

        self.views = {
            nom: cls
            for nom, cls in self._menu_definition
            if not nom.startswith("MK_")
        }

        self._build_menu_buttons()

        self.current_view = None
        self.show_view("Environnements")

    # -------------------------
    # Construction du menu
    # -------------------------
    def _build_menu_buttons(self):
        """
        Parcourt _menu_definition et crée le widget correspondant à chaque entrée.
        Toutes les entrées sont des tuples (nom, cls) — dépaquetage uniforme garanti.
            - MK_SEP   → CTkFrame fin (ligne horizontale)
            - MK_BLANK → CTkFrame transparent (espace vide)
            - autre    → CTkButton de navigation
        """
        for nom, cls in self._menu_definition:

            if nom == MK_SEP:
                ctk.CTkFrame(
                    self.menu_frame,
                    height=2,
                    fg_color=(self.UIColors.SEPARATOR_LIGHT, self.UIColors.SEPARATOR_DARK)
                ).pack(fill="x", padx=8, pady=6)

            elif nom == MK_BLANK:
                ctk.CTkFrame(
                    self.menu_frame,
                    height=MK_BLANK_HEIGHT,
                    fg_color="transparent"
                ).pack(fill="x")

            else:
                ctk.CTkButton(
                    self.menu_frame,
                    text=nom,
                    command=lambda name=nom: self.show_view(name),
                    corner_radius=0,
                    fg_color=self.UIColors.PRIMARY,
                    hover_color=self.UIColors.SECONDARY,
                ).pack(fill="x", padx=5, pady=2)

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
            ctk.CTkLabel(
                self.content_frame,
                text=f"Vue '{view_name}' non trouvée"
            ).pack(expand=True, fill="both")