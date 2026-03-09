import customtkinter as ctk
from sysclasses.ui.MessageDialog import MessageDialog


class AutoFormView(ctk.CTkFrame):

    def __init__(self, parent, entity_instance, mode: str, ui_colors=None):
        super().__init__(parent)

        self.UIColors = ui_colors
        self.entity   = entity_instance
        self.mode     = mode.upper()
        self.on_done  = None
        self._fields_widgets  = {}
        # Pour chaque colonne FK : {col_name: {label: id}}  → utilisé dans _save
        self._fk_maps         = {}
        # Inverse  : {col_name: {id: label}}                → utilisé dans _load_values
        self._fk_maps_reverse = {}

        self.grid_rowconfigure(0, weight=0)   # titre
        self.grid_rowconfigure(1, weight=1)   # zone scrollable
        self.grid_rowconfigure(2, weight=0)   # boutons
        self.grid_columnconfigure(0, weight=1)

        self._build_title()
        self._build_scroll_zone()
        self._build_form()
        self._build_buttons()
        self._load_values()

        if self.mode in ("DISPLAY", "DELETE"):
            self._set_readonly()

    # --------------------------------------------------
    # Titre
    # --------------------------------------------------
    def _build_title(self):
        title_map = {
            "INSERT":  "Ajout",
            "UPDATE":  "Modification",
            "DELETE":  "Suppression",
            "DISPLAY": "Consultation"
        }
        lbl = ctk.CTkLabel(
            self,
            text=title_map.get(self.mode, "Formulaire"),
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="center"
        )
        lbl.grid(row=0, column=0, pady=(10, 5), sticky="ew")

    # --------------------------------------------------
    # Zone scrollable — contient le formulaire
    # --------------------------------------------------
    def _build_scroll_zone(self):
        """
        CTkScrollableFrame : fournit un ascenseur vertical automatique
        quand le nombre de champs dépasse la hauteur disponible.
        Le formulaire est construit à l'intérieur de ce frame.
        """
        self._scroll_frame = ctk.CTkScrollableFrame(self)
        self._scroll_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self._scroll_frame.grid_columnconfigure(0, weight=0)
        self._scroll_frame.grid_columnconfigure(1, weight=0)

    # --------------------------------------------------
    # Construction du formulaire (dans le scroll frame)
    # --------------------------------------------------
    def _build_form(self):
        metadata = self.entity.TableMetadata
        row = 0

        for column in metadata.columns:
            col_meta = metadata.get_column(column)

            lbl = ctk.CTkLabel(
                self._scroll_frame,
                text=column.replace("_", " ").title(),
                anchor="w"
            )
            lbl.grid(row=row, column=0, padx=10, pady=5, sticky="w")

            # FK → ComboBox, sinon widget standard
            if col_meta.get("is_fk"):
                widget = self._create_combo_fk(column)
            else:
                widget = self._create_widget(col_meta)

            widget.grid(row=row, column=1, padx=10, pady=5, sticky="w")

            # Règle de grisage :
            # - is_identity              → toujours grisé (valeur générée par la DB)
            # - is_pk sans is_fk         → toujours grisé (PK technique pure)
            # - is_pk ET is_fk           → actif en INSERT et UPDATE, grisé en DELETE/DISPLAY
            is_pk       = col_meta["is_pk"]
            is_fk       = col_meta.get("is_fk", False)
            is_identity = col_meta["is_identity"]

            doit_griser = (
                is_identity
                or (is_pk and not is_fk)
                or (is_pk and is_fk and self.mode in ("DELETE", "DISPLAY"))
            )

            if doit_griser:
                self._make_readonly(widget)

            self._fields_widgets[column] = widget
            row += 1

    # --------------------------------------------------
    # Lecture seule visuelle (grisé)
    # --------------------------------------------------
    def _make_readonly(self, widget):
        if isinstance(widget, ctk.CTkComboBox):
            widget.configure(state="disabled")
            return
        widget.configure(
            fg_color=self.UIColors.GRISE_BG,
            text_color=self.UIColors.GRISE_FG
        )
        widget.bind("<Key>",      lambda e: "break")
        widget.bind("<Button-1>", lambda e: "break")
        widget.bind("<B1-Motion>",lambda e: "break")

    # --------------------------------------------------
    # ComboBox FK
    # --------------------------------------------------
    def _create_combo_fk(self, col_name: str) -> ctk.CTkComboBox:
        """
        Crée un CTkComboBox alimenté depuis la table liée.
        Appelle entity.get_list_FK() → [(id, "label"), ...]
        """
        choix  = self.entity.get_list_FK(col_name)
        labels = [label for _, label in choix]

        self._fk_maps[col_name]         = {label: val_id for val_id, label in choix}
        self._fk_maps_reverse[col_name] = {val_id: label for val_id, label in choix}

        width = self.entity.TableMetadata.get_col_width(col_name)
        combo = ctk.CTkComboBox(
            self._scroll_frame,
            values=labels,
            width=max(width, 200),
            state="readonly"
        )
        combo.set("")
        return combo

    # --------------------------------------------------
    # Widget standard
    # --------------------------------------------------
    def _create_widget(self, col_meta):
        canonical  = col_meta["canonical_type"]
        family     = canonical[0] if isinstance(canonical, tuple) else "STRING"
        col_name   = col_meta["name"]
        metadata   = self.entity.TableMetadata
        width      = metadata.get_col_width(col_name)
        anchor     = metadata.get_col_anchor(col_name)
        max_length = col_meta["max_length"]
        justify    = "right" if anchor == "e" else "left"

        if family == "BOOLEAN":
            # text="" pour ne pas afficher le nom du widget par défaut
            return ctk.CTkCheckBox(self._scroll_frame, text="")

        if family == "STRING":
            entry = ctk.CTkEntry(self._scroll_frame, width=width, justify=justify)
            if max_length:
                self._set_max_length(entry, max_length)
            return entry

        return ctk.CTkEntry(self._scroll_frame, width=width, justify=justify)

    # --------------------------------------------------
    # Limitation longueur saisie
    # --------------------------------------------------
    def _set_max_length(self, entry: ctk.CTkEntry, max_length: int):
        tk_entry = entry._entry
        vcmd = tk_entry.register(lambda new_val: len(new_val) <= max_length)
        tk_entry.configure(validate="key", validatecommand=(vcmd, "%P"))

    # --------------------------------------------------
    # Chargement des valeurs
    # --------------------------------------------------
    def _load_values(self):
        metadata = self.entity.TableMetadata

        for column, widget in self._fields_widgets.items():
            value    = getattr(self.entity, column, None)
            col_meta = metadata.get_column(column)
            canonical= col_meta["canonical_type"]
            family   = canonical[0] if isinstance(canonical, tuple) else "STRING"

            # --- FK : traduire l'id stocké en label affiché ---
            if col_meta.get("is_fk"):
                label = self._fk_maps_reverse.get(column, {}).get(value, "")
                widget.set(label)
                continue

            if value is None:
                value = ""

            if family == "BOOLEAN":
                widget.select() if value else widget.deselect()
            else:
                widget.insert(0, str(value))

    # --------------------------------------------------
    # Lecture seule totale (DISPLAY / DELETE)
    # --------------------------------------------------
    def _set_readonly(self):
        for widget in self._fields_widgets.values():
            widget.configure(state="disabled")

    # --------------------------------------------------
    # Sauvegarde
    # --------------------------------------------------
    def _save(self):
        metadata = self.entity.TableMetadata

        for column, widget in self._fields_widgets.items():

            col_meta  = metadata.get_column(column)
            is_pk     = col_meta["is_pk"]
            is_fk     = col_meta.get("is_fk", False)

            # PK pure (non FK) → jamais écrite, la DB la gère
            # PK+FK en DELETE/DISPLAY → la ligne est identifiée, on ne retouche pas
            if is_pk and not is_fk:
                continue
            if is_pk and is_fk and self.mode in ("DELETE", "DISPLAY"):
                continue

            canonical = col_meta["canonical_type"]
            family    = canonical[0] if isinstance(canonical, tuple) else "STRING"

            # --- FK : traduire le label sélectionné en id ---
            if is_fk:
                label_sel = widget.get()
                if not label_sel:
                    if not col_meta["nullable"]:
                        MessageDialog.error(self, "Erreur", f"{column} est obligatoire.")
                        return
                    setattr(self.entity, column, None)
                else:
                    setattr(self.entity, column,
                            self._fk_maps.get(column, {}).get(label_sel))
                continue

            if family == "BOOLEAN":
                value = widget.get() == 1
            else:
                value = widget.get()

            if not col_meta["nullable"] and value == "":
                MessageDialog.error(self, "Erreur", f"{column} est obligatoire.")
                return

            # Conversion de type selon la famille canonique
            if value != "" and value is not None:
                if family == "NUMERIC":
                    sub_type = col_meta["canonical_type"][1] if isinstance(col_meta["canonical_type"], tuple) else ""
                    try:
                        if sub_type in ("FLOAT", "DOUBLE", "DECIMAL"):
                            value = float(value)
                        else:
                            value = int(value)
                    except (ValueError, TypeError):
                        MessageDialog.error(self, "Erreur", f"{column} : valeur numérique invalide.")
                        return

            setattr(self.entity, column, value)

        # Validation métier
        if hasattr(self.entity, "ctrl_valeurs"):
            flag_erreur, libelle_erreur = self.entity.ctrl_valeurs()
            if libelle_erreur:
                MessageDialog.error(self, "Erreur", libelle_erreur)
                if flag_erreur:
                    return

        # Exécution CRUD
        try:
            if self.mode == "INSERT" and hasattr(self.entity, "insert"):
                self.entity.insert()
            elif self.mode == "UPDATE" and hasattr(self.entity, "update"):
                self.entity.update()
            elif self.mode == "DELETE" and hasattr(self.entity, "delete"):
                if MessageDialog.confirm(
                    self, "Confirmation",
                    "Voulez-vous supprimer cet enregistrement ?",
                    confirm_label="Supprimer"
                ):
                    self.entity.delete()
                else:
                    return

            self.entity.ogEngine.commit()

        except Exception as e:
            self.entity.ogEngine.rollback()
            MessageDialog.error(self, "Erreur", f"Échec de l'opération :\n{e}")
            return

        if self.on_done:
            self.on_done()
        self.destroy()

    # --------------------------------------------------
    # Annuler
    # --------------------------------------------------
    def _cancel(self):
        self.destroy()

    # --------------------------------------------------
    # Boutons (ancrés en bas, hors du scroll)
    # --------------------------------------------------
    def _build_buttons(self):
        frame_btn = ctk.CTkFrame(self)
        frame_btn.grid(row=2, column=0, pady=10)

        if self.mode != "DISPLAY":
            ctk.CTkButton(
                frame_btn, text="Enregistrer", command=self._save
            ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_btn, text="Annuler", command=self._cancel
        ).pack(side="left", padx=5)