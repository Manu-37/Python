import customtkinter as ctk
from sysclasses.clsCrypto import clsCrypto


class Crypto_View(ctk.CTkFrame):
    """
    Vue utilitaire Chiffrement / Déchiffrement.
    Dépendance unique : clsCrypto() — singleton déjà initialisé par AppBootstrap.

    Deux blocs indépendants :
        - Bloc Chiffrement   : saisie texte clair  → résultat chiffré (base64, CTkTextbox)
        - Bloc Déchiffrement : saisie texte chiffré (CTkTextbox) → résultat clair
    """

    def __init__(self, parent, ui_colors=None):
        super().__init__(parent)

        self.UIColors = ui_colors
        self._crypto  = clsCrypto()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)   # titre
        self.grid_rowconfigure(1, weight=1)   # blocs

        self._build_titre()
        self._build_bloc_chiffrement()
        self._build_bloc_dechiffrement()

    # --------------------------------------------------
    # Titre
    # --------------------------------------------------
    def _build_titre(self):
        ctk.CTkLabel(
            self,
            text="Utilitaire Chiffrement / Déchiffrement",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="center"
        ).grid(row=0, column=0, columnspan=2, pady=(16, 10), sticky="ew")

    # --------------------------------------------------
    # Bloc Chiffrement
    # --------------------------------------------------
    def _build_bloc_chiffrement(self):
        bloc = ctk.CTkFrame(self)
        bloc.grid(row=1, column=0, padx=(16, 8), pady=16, sticky="nsew")
        bloc.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bloc,
            text="Chiffrement",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        # Saisie texte clair — Entry simple, une ligne suffit
        ctk.CTkLabel(bloc, text="Texte clair :", anchor="w").grid(
            row=1, column=0, padx=12, pady=(4, 0), sticky="w"
        )
        self._entry_clair = ctk.CTkEntry(
            bloc, width=320, placeholder_text="Saisir le texte à chiffrer"
        )
        self._entry_clair.grid(row=2, column=0, padx=12, pady=(4, 8), sticky="ew")

        ctk.CTkButton(
            bloc, text="Chiffrer", command=self._chiffrer
        ).grid(row=3, column=0, padx=12, pady=(0, 8), sticky="w")

        # Résultat chiffré — Textbox readonly (le token Fernet est long)
        ctk.CTkLabel(bloc, text="Résultat chiffré :", anchor="w").grid(
            row=4, column=0, padx=12, pady=(8, 0), sticky="w"
        )
        self._box_chiffre = ctk.CTkTextbox(
            bloc,
            height=80,
            wrap="word",
            fg_color=self.UIColors.GRISE_BG if self.UIColors else "#e4e4e4",
            text_color=self.UIColors.GRISE_FG if self.UIColors else "#7A7A7A"
        )
        self._box_chiffre.grid(row=5, column=0, padx=12, pady=(4, 8), sticky="ew")
        self._box_chiffre.configure(state="disabled")

        ctk.CTkButton(
            bloc, text="Copier", width=80,
            command=lambda: self._copier_textbox(self._box_chiffre)
        ).grid(row=6, column=0, padx=12, pady=(0, 16), sticky="w")

    # --------------------------------------------------
    # Bloc Déchiffrement
    # --------------------------------------------------
    def _build_bloc_dechiffrement(self):
        bloc = ctk.CTkFrame(self)
        bloc.grid(row=1, column=1, padx=(8, 16), pady=16, sticky="nsew")
        bloc.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bloc,
            text="Déchiffrement",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        # Saisie texte chiffré — Textbox (token Fernet long, collé depuis le .ini)
        ctk.CTkLabel(bloc, text="Texte chiffré :", anchor="w").grid(
            row=1, column=0, padx=12, pady=(4, 0), sticky="w"
        )
        self._box_crypte = ctk.CTkTextbox(
            bloc,
            height=80,
            wrap="word"
        )
        self._box_crypte.grid(row=2, column=0, padx=12, pady=(4, 8), sticky="ew")

        ctk.CTkButton(
            bloc, text="Déchiffrer", command=self._dechiffrer
        ).grid(row=3, column=0, padx=12, pady=(0, 8), sticky="w")

        # Résultat clair — Entry simple, une ligne suffit
        ctk.CTkLabel(bloc, text="Résultat déchiffré :", anchor="w").grid(
            row=4, column=0, padx=12, pady=(8, 0), sticky="w"
        )
        self._entry_dechiffre = ctk.CTkEntry(
            bloc, width=320,
            fg_color=self.UIColors.GRISE_BG if self.UIColors else "#e4e4e4",
            text_color=self.UIColors.GRISE_FG if self.UIColors else "#7A7A7A"
        )
        self._entry_dechiffre.grid(row=5, column=0, padx=12, pady=(4, 8), sticky="ew")
        self._entry_dechiffre.configure(state="readonly")

        ctk.CTkButton(
            bloc, text="Copier", width=80,
            command=lambda: self._copier_entry(self._entry_dechiffre)
        ).grid(row=6, column=0, padx=12, pady=(0, 16), sticky="w")

    # --------------------------------------------------
    # Actions
    # --------------------------------------------------
    def _chiffrer(self):
        texte = self._entry_clair.get().strip()
        if not texte:
            return

        try:
            resultat_bytes = self._crypto.encrypt(texte)
            # Fernet produit du base64 URL-safe → ASCII pur, décodable sans perte
            resultat_str   = resultat_bytes.decode('utf-8')
        except Exception as e:
            resultat_str = f"ERREUR : {e}"

        self._box_chiffre.configure(state="normal")
        self._box_chiffre.delete("1.0", "end")
        self._box_chiffre.insert("1.0", resultat_str)
        self._box_chiffre.configure(state="disabled")

    def _dechiffrer(self):
        # "1.0"    = ligne 1, caractère 0 (Tk numérote les lignes à partir de 1)
        # "end-1c" = fin du contenu moins le \n final ajouté automatiquement par Tk
        texte = self._box_crypte.get("1.0", "end-1c").strip()
        if not texte:
            return

        try:
            resultat_str = self._crypto.decrypt(texte.encode('utf-8'))
        except Exception as e:
            resultat_str = f"ERREUR : {e}"

        self._entry_dechiffre.configure(state="normal")
        self._entry_dechiffre.delete(0, "end")
        self._entry_dechiffre.insert(0, resultat_str)
        self._entry_dechiffre.configure(state="readonly")

    # --------------------------------------------------
    # Copie presse-papiers
    # --------------------------------------------------
    def _copier_textbox(self, box: ctk.CTkTextbox):
        """Lecture depuis un CTkTextbox — syntaxe Tk indexée ligne:caractère."""
        texte = box.get("1.0", "end-1c").strip()
        if texte:
            self.clipboard_clear()
            self.clipboard_append(texte)

    def _copier_entry(self, entry: ctk.CTkEntry):
        """Lecture depuis un CTkEntry — syntaxe standard."""
        texte = entry.get()
        if texte:
            self.clipboard_clear()
            self.clipboard_append(texte)