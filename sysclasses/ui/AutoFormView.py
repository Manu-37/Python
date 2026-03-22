import customtkinter as ctk
from sysclasses.ui.MessageDialog import MessageDialog
from sysclasses.exceptions import ErreurValidationBloquante, AvertissementValidation


class AutoFormView(ctk.CTkFrame):

    def __init__(self, parent, entity_instance, mode: str, ui_colors=None):
        super().__init__(parent)

        self.UIColors = ui_colors
        self.entity   = entity_instance
        self.mode     = mode.upper()
        self.on_done  = None
        self._fields_widgets  = {}
        self._fk_maps         = {}
        self._fk_maps_reverse = {}

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
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
    # Zone scrollable
    # --------------------------------------------------
    def _build_scroll_zone(self):
        self._scroll_frame = ctk.CTkScrollableFrame(self)
        self._scroll_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self._scroll_frame.grid_columnconfigure(0, weight=0)
        self._scroll_frame.grid_columnconfigure(1, weight=0)

    # --------------------------------------------------
    # Construction du formulaire
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

            if col_meta.get("is_fk"):
                widget = self._create_combo_fk(column)
            else:
                widget = self._create_widget(col_meta)

            widget.grid(row=row, column=1, padx=10, pady=5, sticky="w")

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
    # Lecture seule visuelle
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
        choix  = self.entity.get_list_FK(col_name)
        labels = [label for _, label in choix]

        self._fk_maps[col_name]         = {label: val_id for val_id, label in choix}
        self._fk_maps_reverse[col_name] = {val_id: label for val_id, label in choix}

        width = 400
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
    # Extraction écran → entité (SANS sauvegarde)
    # --------------------------------------------------
    def _get_entity_from_screen(self):
        metadata = self.entity.TableMetadata

        for column, widget in self._fields_widgets.items():

            col_meta  = metadata.get_column(column)
            is_pk     = col_meta["is_pk"]
            is_fk     = col_meta.get("is_fk", False)

            if is_pk and not is_fk:
                continue
            if is_pk and is_fk and self.mode in ("DELETE", "DISPLAY"):
                continue

            canonical = col_meta["canonical_type"]
            family    = canonical[0] if isinstance(canonical, tuple) else "STRING"

            if is_fk:
                label_sel = widget.get()
                setattr(self.entity, column,
                        self._fk_maps.get(column, {}).get(label_sel) if label_sel else None)
                continue

            if family == "BOOLEAN":
                value = widget.get() == 1
            else:
                value = widget.get()

            if value == "":
                setattr(self.entity, column, None)
                continue

            if family == "NUMERIC":
                sub_type = col_meta["canonical_type"][1] if isinstance(col_meta["canonical_type"], tuple) else ""
                try:
                    value = float(value) if sub_type in ("FLOAT", "DOUBLE", "DECIMAL") else int(value)
                except (ValueError, TypeError):
                    value = None

            setattr(self.entity, column, value)

    # --------------------------------------------------
    # Hooks avant / après sauvegarde
    # --------------------------------------------------
    def _before_save(self):
        """
        Hook appelé après _get_entity_from_screen() et avant l'opération CRUD.
        self.entity est peuplé depuis l'écran — disponible et exploitable.
        À implémenter dans les sous-classes qui en ont besoin.
        Par défaut, ne fait rien.
        """
        pass

    def _after_save(self):
        """
        Hook appelé après l'opération CRUD réussie et le commit().
        À implémenter dans les sous-classes qui en ont besoin.
        Par défaut, ne fait rien.
        """
        pass

    # --------------------------------------------------
    # Sauvegarde
    # --------------------------------------------------
    def _save(self):
        # Étape 1 — Lecture écran → entité
        self._get_entity_from_screen()

        # Étape 2 — Hook avant (entity peuplée, pas encore en base)
        self._before_save()

        # Étape 3 — Exécution CRUD
        try:
            if self.mode == "INSERT":
                self.entity.insert()
            elif self.mode == "UPDATE":
                self.entity.update()
            elif self.mode == "DELETE":
                if not MessageDialog.confirm(
                    self, "Confirmation",
                    "Voulez-vous supprimer cet enregistrement ?",
                    confirm_label="Supprimer"
                ):
                    return
                self.entity.delete()

            self.entity.ogEngine.commit()

        except ErreurValidationBloquante as e:
            self.entity.ogEngine.rollback()
            MessageDialog.error(self, "Erreur de validation", str(e))
            return

        except AvertissementValidation as e:
            self.entity.ogEngine.commit()
            MessageDialog.warning(self, "Avertissement",
                                  f"Enregistrement effectué avec des avertissements :\n{str(e)}")

        except Exception as e:
            self.entity.ogEngine.rollback()
            MessageDialog.error(self, "Erreur", f"Échec de l'opération :\n{e}")
            return

        # Étape 4 — Hook après (opération commitée avec succès)
        self._after_save()

        if self.on_done:
            self.on_done()
        self.destroy()

    # --------------------------------------------------
    # Annuler
    # --------------------------------------------------
    def _cancel(self):
        self.destroy()

    # --------------------------------------------------
    # Boutons
    # --------------------------------------------------
    def _build_buttons(self):
        self._frame_btn = ctk.CTkFrame(self)
        self._frame_btn.grid(row=2, column=0, pady=10)

        if self.mode != "DISPLAY":
            ctk.CTkButton(
                self._frame_btn, text="Enregistrer", command=self._save
            ).pack(side="left", padx=5)

        ctk.CTkButton(
            self._frame_btn, text="Annuler", command=self._cancel
        ).pack(side="left", padx=5)

        self._extend_buttons()

    def _extend_buttons(self):
        """
        Hook pour ajouter des boutons personnalisés à la suite des boutons standards.
        Appelé à la fin de _build_buttons().
        À implémenter dans les sous-classes qui en ont besoin.
        Par défaut, ne fait rien.
        """
        pass