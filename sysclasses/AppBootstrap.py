import sys

from sysclasses.clsINICommun    import clsINICommun
from sysclasses.clsINISecurity  import clsINISecurity
from sysclasses.clsLOG          import clsLOG
from sysclasses.clsCrypto       import clsCrypto
from sysclasses.clsDBAManager   import clsDBAManager
from sysclasses.clsEmailManager import clsEmailManager


class AppBootstrap:
    """
    Initialisation défensive et ordonnée des singletons systématiques.

    Ordre immuable :
        1. clsINICommun    — fichier ini projet (sous-classe obligatoire)
        2. clsINISecurity  — fichier security.ini (données sensibles)
        3. clsLOG          — dépend de clsINICommun + cste_chemins
        4. clsCrypto       — dépend de clsINISecurity
        5. clsDBAManager   — dépend de clsINICommun + clsINISecurity
        6. clsEmailManager — dépend de clsINICommun

    Modes :
        'ui'        : erreurs fatales via dialog graphique CTk (défaut)
                      customtkinter n'est importé qu'en mode ui et uniquement
                      si une erreur fatale survient — pas de dépendance UI
                      pour les projets console.
        'console'   : erreurs fatales via log critical + arrêt propre
        'streamlit' : erreurs fatales via stderr si Streamlit non encore démarré,
                      ou via st.error() + st.stop() si le contexte Streamlit
                      est actif (réexécution de page).
                      streamlit n'est importé qu'en mode streamlit et uniquement
                      si une erreur fatale survient.

    Usage :
        # Application UI (CustomTkinter)
        from projets.MonProjet.clsINIMonProjet import clsINIMonProjet
        bootstrap = AppBootstrap(ini_file, clsINIMonProjet)

        # Script console / cron
        from projets.MonProjet.clsINIMonProjet import clsINIMonProjet
        bootstrap = AppBootstrap(ini_file, clsINIMonProjet, mode='console')

        # Application Streamlit
        from projets.MonProjet.clsINIMonProjet import clsINIMonProjet
        bootstrap = AppBootstrap(ini_file, clsINIMonProjet, mode='streamlit')

    En cas d'échec l'application ne démarre jamais dans un état partiel.
    """

    def __init__(self, ini_file: str, ini_class: type, mode: str = 'ui'):
        if ini_class is None:
            raise TypeError(
                "AppBootstrap requiert une classe INI projet.\n"
                "Exemple : AppBootstrap(ini_file, clsINIMonProjet)"
            )
        if not issubclass(ini_class, clsINICommun):
            raise TypeError(
                f"{ini_class.__name__} n'est pas une sous-classe de clsINICommun."
            )

        self._mode = mode.lower()

        self.oIni      = self._init_ini(ini_file, ini_class)
        self.oSecurity = self._init_security()
        self.oLog      = self._init_log()
        self.oCrypto   = self._init_crypto()
        self.oDB       = self._init_dba()
        self.oEmail    = self._init_email()

    # --------------------------------------------------
    # Étape 1 — INI projet
    # --------------------------------------------------
    def _init_ini(self, ini_file: str, ini_class: type) -> clsINICommun:
        try:
            return ini_class(ini_file)
        except FileNotFoundError:
            self._erreur_fatale(
                "Erreur de configuration",
                f"Fichier de configuration introuvable :\n\n{ini_file}\n\n"
                "Vérifiez que le fichier existe et que le chemin est correct."
            )
        except Exception as e:
            self._erreur_fatale(
                "Erreur de configuration",
                f"Impossible de lire le fichier de configuration :\n\n{ini_file}\n\n"
                f"Détail : {e}"
            )

    # --------------------------------------------------
    # Étape 2 — INI Security
    # --------------------------------------------------
    def _init_security(self) -> clsINISecurity:
        try:
            from pathlib import Path
            key_path = self.oIni.env_params.get('path')
            if not key_path:
                raise ValueError("La clé 'path' est absente de la section [ENVIRONNEMENT].")
            return clsINISecurity(Path(key_path) / 'security.ini')
        except FileNotFoundError:
            self._erreur_fatale(
                "Erreur de configuration",
                "Fichier security.ini introuvable.\n\n"
                "Vérifiez le paramètre 'path' dans [ENVIRONNEMENT]."
            )
        except Exception as e:
            self._erreur_fatale(
                "Erreur de configuration",
                f"Impossible de lire security.ini.\n\nDétail : {e}"
            )

    # --------------------------------------------------
    # Étape 3 — LOG
    # --------------------------------------------------
    def _init_log(self) -> clsLOG:
        try:
            return clsLOG(self.oIni)
        except KeyError as e:
            self._erreur_fatale(
                "Erreur de configuration LOG",
                f"Paramètre manquant dans le fichier .ini :\n\n{e}\n\n"
                "Vérifiez la section [LOG]."
            )
        except Exception as e:
            self._erreur_fatale(
                "Erreur d'initialisation LOG",
                f"Impossible d'initialiser le système de journalisation.\n\nDétail : {e}"
            )

    # --------------------------------------------------
    # Étape 4 — Crypto
    # --------------------------------------------------
    def _init_crypto(self) -> clsCrypto:
        try:
            return clsCrypto()
        except Exception as e:
            self.oLog.error(f"AppBootstrap | Échec init Crypto : {e}")
            self._erreur_fatale(
                "Erreur de chiffrement",
                f"Impossible d'initialiser le module de chiffrement.\n\nDétail : {e}"
            )

    # --------------------------------------------------
    # Étape 5 — DBAManager
    # --------------------------------------------------
    def _init_dba(self) -> clsDBAManager:
        try:
            return clsDBAManager(self.oIni)
        except FileNotFoundError as e:
            self.oLog.error(f"AppBootstrap | Registre BDD introuvable : {e}")
            self._erreur_fatale(
                "Erreur de connexion — Registre introuvable",
                f"Le fichier de registre des bases de données est introuvable :\n\n{e}"
            )
        except RuntimeError as e:
            self.oLog.error(f"AppBootstrap | Échec connexion registre : {e}")
            self._erreur_fatale(
                "Erreur de connexion — Base de données",
                f"Impossible de se connecter à la base de données centrale.\n\n"
                f"Détail : {e}\n\n"
                "Vérifiez les paramètres de connexion et l'accessibilité du serveur."
            )
        except Exception as e:
            self.oLog.error(f"AppBootstrap | Échec init DBAManager : {e}")
            self._erreur_fatale(
                "Erreur de connexion",
                f"Impossible d'initialiser le gestionnaire de bases de données.\n\nDétail : {e}"
            )

    # --------------------------------------------------
    # Étape 6 — EmailManager
    # --------------------------------------------------
    def _init_email(self) -> clsEmailManager:
        try:
            return clsEmailManager(self.oIni)
        except Exception as e:
            self.oLog.error(f"AppBootstrap | Échec init EmailManager : {e}")
            self._erreur_fatale(
                "Erreur d'initialisation Email",
                f"Impossible d'initialiser le gestionnaire d'emails.\n\nDétail : {e}\n\n"
                "Vérifiez les sections [EMAIL_*] dans le fichier .ini."
            )

    # --------------------------------------------------
    # Erreur fatale — dispatch selon le mode
    # --------------------------------------------------
    def _erreur_fatale(self, titre: str, message: str):
        if self._mode == 'console':
            self._erreur_fatale_console(titre, message)
        elif self._mode == 'streamlit':
            self._erreur_fatale_streamlit(titre, message)
        else:
            self._erreur_fatale_ui(titre, message)

    def _erreur_fatale_console(self, titre: str, message: str):
        """
        Mode console : log critical si LOG disponible, sinon stderr.
        Lève RuntimeError pour interrompre le bootstrap proprement.
        """
        msg_complet = f"{titre} | {message}"
        if hasattr(self, 'oLog') and self.oLog:
            self.oLog.critical(f"AppBootstrap | {msg_complet}")
        else:
            print(f"\n[ERREUR FATALE] {msg_complet}\n", file=sys.stderr)
        raise RuntimeError(msg_complet)

    def _erreur_fatale_streamlit(self, titre: str, message: str):
        """
        Mode streamlit : deux comportements selon le contexte d'exécution.

        Avant démarrage Streamlit (phase bootstrap dans le lanceur) :
            → stderr + RuntimeError, comme le mode console.
            Streamlit n'est pas encore démarré, st.* n'est pas disponible.

        Pendant l'exécution Streamlit (réexécution de page, cache_resource) :
            → st.error() + st.stop() pour afficher l'erreur dans le navigateur.
            streamlit n'est importé qu'ici, jamais au niveau module.

        Dans les deux cas : log critical si LOG est disponible.
        """
        msg_complet = f"{titre} | {message}"

        if hasattr(self, 'oLog') and self.oLog:
            self.oLog.critical(f"AppBootstrap | {msg_complet}")
        else:
            print(f"\n[ERREUR FATALE] {msg_complet}\n", file=sys.stderr)

        # Tente d'utiliser le contexte Streamlit s'il est actif
        try:
            import streamlit as st
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            if get_script_run_ctx() is not None:
                # Contexte Streamlit actif → affichage dans le navigateur
                st.error(f"**{titre}**\n\n{message}")
                st.stop()
                return  # st.stop() lève une exception interne Streamlit, mais par sécurité
        except ImportError:
            pass  # streamlit pas installé → on tombe sur le fallback console
        except Exception:
            pass  # get_script_run_ctx a échoué → contexte inactif

        # Pas de contexte Streamlit actif → comportement console
        raise RuntimeError(msg_complet)

    def _erreur_fatale_ui(self, titre: str, message: str):
        """
        Mode UI : dialog graphique CTk.
        customtkinter est importé ici uniquement — pas de dépendance UI
        au niveau du module, les projets console ne le chargent jamais.
        """
        try:
            import customtkinter as ctk

            root = ctk.CTk()
            root.withdraw()

            dlg_w, dlg_h = 460, 220
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            x = (screen_w - dlg_w) // 2
            y = (screen_h - dlg_h) // 2

            dlg = ctk.CTkToplevel(root)
            dlg.title(titre)
            dlg.geometry(f"{dlg_w}x{dlg_h}+{x}+{y}")
            dlg.resizable(False, False)
            dlg.focus_force()
            dlg.lift()

            dlg.grid_columnconfigure(0, weight=1)
            dlg.grid_rowconfigure(0, weight=1)

            ctk.CTkLabel(
                dlg,
                text=message,
                wraplength=420,
                justify="left",
                text_color="#CC0000"
            ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

            def _quitter():
                root.destroy()
                raise SystemExit(1)

            ctk.CTkButton(
                dlg,
                text="Quitter",
                width=120,
                fg_color="#CC0000",
                hover_color="#990000",
                command=_quitter
            ).grid(row=1, column=0, pady=(0, 20))

            dlg.protocol("WM_DELETE_WINDOW", _quitter)
            root.mainloop()

        except SystemExit:
            raise
        except Exception:
            print(f"\n[ERREUR FATALE] {titre}\n{message}\n", file=sys.stderr)
            raise SystemExit(1)