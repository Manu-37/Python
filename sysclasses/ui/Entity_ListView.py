import tkinter as tk
import customtkinter as ctk
from sysclasses.ui.DataGrid import DataGrid
from sysclasses.ui.MessageDialog import MessageDialog
from sysclasses.ui.AutoFormView import AutoFormView


class Entity_ListView(ctk.CTkFrame):
    """
    Composant générique liste + formulaire pour toute entité CRUD.

    Paramètres
    ----------
    parent       : widget parent CustomTkinter
    entity_class : classe entité (ex: clsENV) — doit hériter de clsEntity_ABS
    order_by     : colonne de tri pour load_all() — None = pas de tri
    form_class   : classe formulaire à instancier (défaut : AutoFormView)
    ui_colors    : objet UIColors transmis depuis UI_Core
    """

    def __init__(
        self,
        parent,
        entity_class,
        order_by: str = None,
        form_class=None,
        ui_colors=None
    ):
        super().__init__(parent)

        self.entity_class  = entity_class
        self.order_by      = order_by
        self.form_class    = form_class or AutoFormView
        self.UIColors      = ui_colors
        self.selected_row  = None

        self._build_layout()
        self._build_toolbar()
        self._build_grid()
        self._build_form_container()
        self._load_data()

        self.after(100, self._set_initial_sash)

    # --------------------------
    # Layout principal
    # --------------------------
    def _build_layout(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.paned = tk.PanedWindow(
            self,
            orient=tk.VERTICAL,
            sashrelief=tk.RAISED,
            sashwidth=6,
            sashpad=2
        )
        self.paned.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.frame_liste = tk.Frame(self.paned)
        self.paned.add(self.frame_liste, stretch="always")

        self.frame_fiche = tk.Frame(self.paned)
        self.paned.add(self.frame_fiche, stretch="always")

    # --------------------------
    # Position initiale du splitter
    # --------------------------
    def _set_initial_sash(self):
        hauteur_totale = self.paned.winfo_height()
        if hauteur_totale > 1:
            self.paned.sash_place(0, 0, int(hauteur_totale * 0.40))

    # --------------------------
    # Toolbar CRUD
    # --------------------------
    def _build_toolbar(self):
        self.toolbar = ctk.CTkFrame(self)
        self.toolbar.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        ctk.CTkButton(self.toolbar, text="Ajouter",   command=self._ajouter).pack(side="left", padx=5)
        ctk.CTkButton(self.toolbar, text="Modifier",  command=self._modifier).pack(side="left", padx=5)
        ctk.CTkButton(self.toolbar, text="Supprimer", command=self._supprimer).pack(side="left", padx=5)
        ctk.CTkButton(self.toolbar, text="Consulter", command=self._consulter).pack(side="left", padx=5)

        # Hook — point d'extension pour boutons spécifiques
        self._extend_toolbar()

    def _extend_toolbar(self):
        """
        Hook pour ajouter des boutons personnalisés à la suite des boutons standards.
        Appelé à la fin de _build_toolbar().
        À implémenter dans les sous-classes qui en ont besoin.
        Par défaut, ne fait rien.
        """
        pass

    # --------------------------
    # DataGrid
    # --------------------------
    def _build_grid(self):
        self.frame_liste.grid_rowconfigure(0, weight=1)
        self.frame_liste.grid_columnconfigure(0, weight=1)

        metadata = self.entity_class.get_metadata()

        self.data_grid = DataGrid(
            self.frame_liste,
            titre=f"Liste des {self.entity_class.__name__}",
            colonnes=metadata.display_columns,
            metadata=metadata,
            ui_colors=self.UIColors
        )
        self.data_grid.on_row_selected     = self._on_row_selected
        self.data_grid.on_row_double_click = self._on_row_double_click
        self.data_grid.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

    # --------------------------
    # Zone formulaire
    # --------------------------
    def _build_form_container(self):
        self.frame_fiche.grid_rowconfigure(0, weight=1)
        self.frame_fiche.grid_columnconfigure(0, weight=1)

        self.form_container = ctk.CTkFrame(self.frame_fiche)
        self.form_container.grid(row=0, column=0, sticky="nsew")

    # --------------------------
    # Chargement des données
    # --------------------------
    def _load_data(self):
        data = self.entity_class.load_all(order_by=self.order_by)
        self.data_grid.set_data(data)
        self.selected_row = None

    # --------------------------
    # Sélection / double clic
    # --------------------------
    def _on_row_selected(self, ligne: dict):
        self.selected_row = ligne

    def _on_row_double_click(self, ligne: dict):
        self._modifier()

    # --------------------------
    # Ouverture du formulaire
    # --------------------------
    def _ouvrir_form(self, entity_instance, mode: str):
        for widget in self.form_container.winfo_children():
            widget.destroy()

        form = self.form_class(
            self.form_container,
            entity_instance,
            mode,
            ui_colors=self.UIColors
        )
        form.on_done = self._load_data
        form.pack(expand=True, fill="both")

    # --------------------------
    # Actions CRUD
    # --------------------------
    def _ajouter(self):
        entity = self.entity_class()
        self._ouvrir_form(entity, mode="INSERT")

    def _modifier(self):
        if not self.selected_row:
            MessageDialog.info(self, "Information", "Vous devez sélectionner une ligne.")
            return
        entity = self.entity_class(**self.selected_row)
        self._ouvrir_form(entity, mode="UPDATE")

    def _supprimer(self):
        if not self.selected_row:
            MessageDialog.info(self, "Information", "Vous devez sélectionner une ligne.")
            return
        entity = self.entity_class(**self.selected_row)
        self._ouvrir_form(entity, mode="DELETE")

    def _consulter(self):
        if not self.selected_row:
            MessageDialog.info(self, "Information", "Vous devez sélectionner une ligne.")
            return
        entity = self.entity_class(**self.selected_row)
        self._ouvrir_form(entity, mode="DISPLAY")