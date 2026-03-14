import customtkinter as ctk

# --------------------------------------------------
# Mots-clés de structure de menu
# Utilisés dans _menu_definition des UI_Core filles.
# Toujours une constante explicite — jamais None.
# --------------------------------------------------
MK_SEP   = "MK_SEP"    # Séparateur horizontal (ligne fine)
MK_BLANK = "MK_BLANK"  # Espace blanc (~80% hauteur d'un bouton)

# Hauteur en pixels du MK_BLANK — ajustable ici sans chercher dans le code
MK_BLANK_HEIGHT = 26


class UI_Core(ctk.CTk):
    """
    Coeur UI générique commun à toutes les applications.
    Ne contient aucune logique métier.
    """

    class UIColors:
        # -----------------------------
        # Thème entreprise unifié
        # -----------------------------
        PRIMARY          = "#1F6AA5"
        SECONDARY        = "#144870"
        BACKGROUND       = "#F2F2F2"
        SEPARATOR_LIGHT  = "#c0c0c0"
        SEPARATOR_DARK   = "#505050"
        GRISE_BG         = "#e4e4e4"
        GRISE_FG         = "#7A7A7A"
        FONT_DEFAULT     = ("Segoe UI", 12)

        # --- DataGrid ---
        GRID_ROW_EVEN     = ("gray95", "gray20")
        GRID_ROW_ODD      = ("gray90", "gray25")
        GRID_ROW_SELECTED = ("lightblue", "#1f538d")

    def __init__(self, *, width: int, height: int, min_width: int, min_height: int):
        super().__init__()
        self._configure_window(width, height, min_width, min_height)
        self._configure_theme()
        self._build_root_layout()

    def _configure_window(self, width, height, min_width, min_height):
        self.geometry(f"{width}x{height}")
        self.minsize(min_width, min_height)
        self.title("UI_Core - Title not set")

    def _configure_theme(self):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.UIColors = self.UIColors
        self.configure(bg=self.UIColors.BACKGROUND)

    def _build_root_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.menu_frame = ctk.CTkFrame(self, width=200)
        self.menu_frame.grid(row=0, column=0, sticky="ns")
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=0, column=1, sticky="nsew")

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()