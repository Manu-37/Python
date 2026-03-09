import tkinter as tk
import customtkinter as ctk
from db.clsTableMetadata import clsTableMetadata


class DataGrid(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        titre: str,
        colonnes: list[str],
        metadata: clsTableMetadata,
        ui_colors=None
    ):
        super().__init__(parent)

        self.colonnes        = colonnes
        self.metadata        = metadata
        self.UIColors        = ui_colors
        self._row_index      = 0
        self._rows_widgets   = []
        self._data           = []
        self._selected_index = None

        # Largeurs calculées une fois depuis les métadonnées
        self._col_widths = [metadata.get_col_width(col) for col in colonnes]

        # Callbacks externes
        self.on_row_selected     = None
        self.on_row_double_click = None

        self._build_titre(titre)
        self._build_header()
        self._build_data_area()

    # --------------------------------------------------
    # Couleur de fond CTk courante (suit le thème clair/sombre)
    # --------------------------------------------------

    def _get_bg(self) -> str:
        """
        Récupère la couleur de fond du CTkFrame courant selon le thème actif.
        Nécessaire pour harmoniser les Canvas et Frames Tk natifs avec CTk.
        """
        return self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        )

    # --------------------------------------------------
    # Titre
    # --------------------------------------------------

    def _build_titre(self, titre: str):
        self.lbl_titre = ctk.CTkLabel(
            self,
            text=titre,
            font=("Arial", 16, "bold")
        )
        # columnspan=2 : titre couvre la colonne data ET la colonne scrollbar_v
        self.lbl_titre.grid(row=0, column=0, columnspan=2, pady=(0, 6), sticky="w")

    # --------------------------------------------------
    # Header fixe — ne scroll pas verticalement
    # --------------------------------------------------

    def _build_header(self):
        bg = self._get_bg()

        # Canvas Tk natif — hauteur fixe
        # highlightthickness=0 : supprime le cadre de focus Tk (trait bleu par défaut)
        self.header_canvas = tk.Canvas(self, height=30, highlightthickness=0, bg=bg)
        self.header_canvas.grid(row=1, column=0, sticky="ew")

        # Frame Tk natif posé SUR le canvas
        # (0,0) + anchor="nw" = coin haut-gauche du canvas
        self.header_frame = tk.Frame(self.header_canvas, bg=bg)
        self.header_canvas.create_window((0, 0), window=self.header_frame, anchor="nw")

        # Labels d'en-tête — largeur et cadrage depuis métadonnées
        for col_index, col_name in enumerate(self.colonnes):
            width  = self._col_widths[col_index]
            anchor = self.metadata.get_col_anchor(col_name)

            lbl = ctk.CTkLabel(
                self.header_frame,
                text=col_name,
                font=("Arial", 12, "bold"),
                anchor=anchor,
                width=width
            )
            lbl.grid(row=0, column=col_index, padx=1, pady=2, sticky="ew")

            # Forcer la largeur de colonne dans header_frame
            self.header_frame.grid_columnconfigure(col_index, minsize=width)

    # --------------------------------------------------
    # Zone de données scrollable V + H
    # --------------------------------------------------

    def _build_data_area(self):
        bg = self._get_bg()

        # Canvas Tk natif — zone scrollable dans les deux axes
        self.data_canvas = tk.Canvas(self, highlightthickness=0, bg=bg)
        self.data_canvas.grid(row=2, column=0, sticky="nsew")

        # Frame Tk natif posé SUR le canvas — contiendra toutes les lignes
        self.data_frame = tk.Frame(self.data_canvas, bg=bg)
        self.data_canvas.create_window((0, 0), window=self.data_frame, anchor="nw")

        # Scrollbar verticale — branchée sur data_canvas uniquement
        self.scrollbar_v = ctk.CTkScrollbar(
            self,
            orientation="vertical",
            command=self.data_canvas.yview
        )
        self.scrollbar_v.grid(row=2, column=1, sticky="ns")

        # Scrollbar horizontale — branchée sur LES DEUX canvas via _scroll_horizontal
        self.scrollbar_h = ctk.CTkScrollbar(
            self,
            orientation="horizontal",
            command=self._scroll_horizontal
        )
        self.scrollbar_h.grid(row=3, column=0, sticky="ew")

        # Brancher les canvas sur leurs scrollbars
        self.data_canvas.configure(
            yscrollcommand=self.scrollbar_v.set,
            xscrollcommand=self.scrollbar_h.set
        )

        # Recalcul scrollregions à chaque changement de taille du contenu
        self.data_frame.bind("<Configure>", self._on_data_frame_configure)

        # Réévaluation scrollbars à chaque redimensionnement du canvas (fenêtre)
        self.data_canvas.bind("<Configure>", self._on_canvas_configure)

        # Row 2 et col 0 extensibles — la zone données prend tout l'espace disponible
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # --------------------------------------------------
    # Scroll horizontal synchronisé header + données
    # --------------------------------------------------

    def _scroll_horizontal(self, *args):
        # Les deux canvas bougent ensemble — cœur de la synchronisation
        self.header_canvas.xview(*args)
        self.data_canvas.xview(*args)

    # --------------------------------------------------
    # Recalcul scrollregions quand le contenu change
    # --------------------------------------------------

    def _on_canvas_configure(self, event):
        # Le canvas vient de changer de taille (redimensionnement fenêtre)
        # Le contenu lui est identique — seule la zone visible a changé
        self.after(1, self._update_scrollbars_visibility)

    def _on_data_frame_configure(self, event):
        # scrollregion = taille totale scrollable
        # bbox("all") = bounding box automatique de tous les éléments du canvas
        self.data_canvas.configure(scrollregion=self.data_canvas.bbox("all"))

        # Header : même largeur que data_frame, hauteur fixe
        self.header_canvas.configure(scrollregion=(
            0, 0,
            self.data_frame.winfo_reqwidth(),
            self.header_frame.winfo_reqheight()
        ))

        # after(1) : laisser Tk finaliser le layout avant de mesurer les tailles
        # Le délai est indépendant du volume de données — c'est un cycle de rendu, pas une attente
        self.after(1, self._update_scrollbars_visibility)

    def _update_scrollbars_visibility(self):
        """
        Affiche ou masque les scrollbars selon que le contenu dépasse la zone visible.
        grid_remove() mémorise la config grid — grid() la restaure sans la redéfinir.
        """
        content_w = self.data_frame.winfo_reqwidth()
        content_h = self.data_frame.winfo_reqheight()
        canvas_w  = self.data_canvas.winfo_width()
        canvas_h  = self.data_canvas.winfo_height()

        # Scrollbar verticale
        if content_h > canvas_h:
            self.scrollbar_v.grid()
        else:
            self.scrollbar_v.grid_remove()

        # Scrollbar horizontale
        if content_w > canvas_w:
            self.scrollbar_h.grid()
        else:
            self.scrollbar_h.grid_remove()

    # --------------------------------------------------
    # Couleurs lignes — depuis UIColors ou valeurs par défaut
    # --------------------------------------------------

    def _color_row(self, row_number: int):
        if self.UIColors:
            return self.UIColors.GRID_ROW_EVEN if row_number % 2 == 0 else self.UIColors.GRID_ROW_ODD
        return ("gray95", "gray20") if row_number % 2 == 0 else ("gray90", "gray25")

    def _color_selected(self):
        if self.UIColors:
            return self.UIColors.GRID_ROW_SELECTED
        return ("lightblue", "#1f538d")

    # --------------------------------------------------
    # Vidage de la grille
    # --------------------------------------------------

    def clear(self):
        for widget in self.data_frame.winfo_children():
            widget.destroy()

        self._row_index      = 0
        self._rows_widgets   = []
        self._data           = []
        self._selected_index = None

    # --------------------------------------------------
    # Alimentation de la grille
    # --------------------------------------------------

    def set_data(self, lignes: list[dict]):
        self.clear()
        self._data = lignes

        for ligne in lignes:
            self._add_row(ligne)

    # --------------------------------------------------
    # Ajout d'une ligne
    # --------------------------------------------------

    def _add_row(self, ligne: dict):
        row_widgets = []
        row_number  = len(self._rows_widgets)
        bg_color    = self._color_row(row_number)

        for col_index, col_name in enumerate(self.colonnes):
            value  = ligne.get(col_name, "")
            width  = self._col_widths[col_index]
            anchor = self.metadata.get_col_anchor(col_name)

            lbl = ctk.CTkLabel(
                self.data_frame,        # parent = data_frame (pas self)
                text=str(value),
                anchor=anchor,          # cadrage depuis métadonnées (e=droite, w=gauche)
                fg_color=bg_color,
                corner_radius=0,
                width=width             # largeur depuis métadonnées
            )
            lbl.grid(row=self._row_index, column=col_index, padx=1, pady=1, sticky="ew")

            # Forcer la largeur de colonne dans data_frame — alignement garanti avec header
            self.data_frame.grid_columnconfigure(col_index, minsize=width)

            lbl.bind("<Button-1>",        lambda e, idx=row_number: self._on_row_click(idx))
            lbl.bind("<Double-Button-1>", lambda e, row_data=ligne: self._on_row_double_click(row_data))

            row_widgets.append(lbl)

        self._rows_widgets.append(row_widgets)
        self._row_index += 1

    # --------------------------------------------------
    # Gestion des clics
    # --------------------------------------------------

    def _on_row_click(self, index):
        # Restaurer couleur ancienne sélection
        if self._selected_index is not None:
            self._restore_row_color(self._selected_index)

        # Appliquer couleur sélection
        for widget in self._rows_widgets[index]:
            widget.configure(fg_color=self._color_selected())

        self._selected_index = index

        if self.on_row_selected:
            self.on_row_selected(self._data[index])

    def _on_row_double_click(self, row_data: dict):
        if self.on_row_double_click:
            self.on_row_double_click(row_data)

    def _restore_row_color(self, index):
        for widget in self._rows_widgets[index]:
            widget.configure(fg_color=self._color_row(index))

    # --------------------------------------------------
    # Accesseur sélection
    # --------------------------------------------------

    def get_selected(self):
        if self._selected_index is None:
            return None
        return self._data[self._selected_index]
