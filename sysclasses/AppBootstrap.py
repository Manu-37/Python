import sys
import customtkinter as ctk

from sysclasses.clsINICommun  import clsINICommun
from sysclasses.clsLOG        import clsLOG
from sysclasses.clsCrypto     import clsCrypto
from sysclasses.clsDBAManager import clsDBAManager
from sysclasses.clsEmailManager import clsEmailManager


class AppBootstrap:
    """
    Initialisation défensive et ordonnée des 4 singletons systématiques.

    Ordre immuable :
        1. clsINICommun  — lit le fichier .ini passé en paramètre
        2. clsLOG        — dépend de clsINICommun (project_params, log_params)
        3. clsCrypto     — dépend de clsINICommun (env_params['path'])
        4. clsDBAManager — dépend de tout le reste

    Usage dans main() :
        bootstrap = AppBootstrap(iniFile)
        # Si on arrive ici, tout est prêt et fiable.
        # Les singletons se retrouvent ensuite via leur constructeur sans argument :
        #   clsLOG()        → instance existante
        #   clsDBAManager() → instance existante

    En cas d'échec à n'importe quelle étape :
        - LOG disponible  → l'erreur est loggée
        - Dans tous les cas → dialog graphique CTk + sys.exit(1)
        L'application ne démarre jamais dans un état partiel.
    """

    def __init__(self, ini_file):
        # Les 4 attributs sont renseignés au fur et à mesure.
        # Si une étape échoue, on ne revient jamais ici — sys.exit() a déjà été appelé.
        self.oIni    = self._init_ini(ini_file)
        self.oLog    = self._init_log()
        self.oCrypto = self._init_crypto()
        self.oDB     = self._init_dba()
        self.oEmail  = self._init_email()

    # --------------------------------------------------
    # Étape 1 — INI
    # --------------------------------------------------

    def _init_ini(self, ini_file) -> clsINICommun:
        """
        Premier singleton. Pas de LOG disponible à ce stade.
        L'erreur la plus probable : fichier .ini introuvable ou mal formé.
        """
        try:
            return clsINICommun(ini_file)
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
    # Étape 2 — LOG
    # --------------------------------------------------

    def _init_log(self) -> clsLOG:
        """
        Deuxième singleton. Toujours pas de LOG disponible si ça échoue ici.
        L'erreur la plus probable : section [PROJECT] ou [LOG] absente du .ini,
        ou dossier log non créable (droits insuffisants).
        """
        try:
            return clsLOG(self.oIni)
        except KeyError as e:
            self._erreur_fatale(
                "Erreur de configuration LOG",
                f"Paramètre manquant dans le fichier .ini :\n\n{e}\n\n"
                "Vérifiez les sections [PROJECT] et [LOG]."
            )
        except Exception as e:
            self._erreur_fatale(
                "Erreur d'initialisation LOG",
                f"Impossible d'initialiser le système de journalisation.\n\n"
                f"Détail : {e}"
            )

    # --------------------------------------------------
    # Étape 3 — Crypto
    # --------------------------------------------------

    def _init_crypto(self) -> clsCrypto:
        """
        Troisième singleton. LOG disponible à partir d'ici.
        L'erreur la plus probable : chemin de clé absent ou clé corrompue.
        """
        try:
            key_path = self.oIni.env_params.get('path')
            if not key_path:
                raise ValueError("La clé 'path' est absente de la section [ENVIRONNEMENT] du fichier .ini.")
            return clsCrypto(key_path)
        except Exception as e:
            self.oLog.error(f"AppBootstrap | Échec init Crypto : {e}")
            self._erreur_fatale(
                "Erreur de chiffrement",
                f"Impossible d'initialiser le module de chiffrement.\n\n"
                f"Détail : {e}\n\n"
                "Vérifiez le paramètre 'path' dans [ENVIRONNEMENT] et l'accès au fichier de clé."
            )

    # --------------------------------------------------
    # Étape 4 — DBAManager
    # --------------------------------------------------

    def _init_dba(self) -> clsDBAManager:
        """
        Quatrième et dernier singleton. LOG + Crypto disponibles.
        L'erreur la plus probable : base de données inaccessible,
        tunnel SSH en échec, identifiants incorrects.
        """
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
                f"Impossible d'initialiser le gestionnaire de bases de données.\n\n"
                f"Détail : {e}"
            )

    # --------------------------------------------------
    # Étape 5 — EmailManager
    # --------------------------------------------------

    def _init_email(self) -> clsEmailManager:
        """
        Cinquième singleton. LOG + Crypto + DBA disponibles.
        L'erreur la plus probable : section [EMAIL_*] absente ou mal formée.
        """
        try:
            return clsEmailManager(self.oIni)
        except Exception as e:
            self.oLog.error(f"AppBootstrap | Échec init EmailManager : {e}")
            self._erreur_fatale(
                "Erreur d'initialisation Email",
                f"Impossible d'initialiser le gestionnaire d'emails.\n\n"
                f"Détail : {e}\n\n"
                "Vérifiez les sections [EMAIL_*] dans le fichier .ini."
            )
    
    # --------------------------------------------------
    # Dialog d'erreur fatale — fenêtre CTk temporaire
    # --------------------------------------------------

    def _erreur_fatale(self, titre: str, message: str):
        """
        Affiche une fenêtre d'erreur graphique CTk autonome, puis quitte.

        Fonctionnement :
        - On crée une ctk.CTk() temporaire (fenêtre principale obligatoire pour CTk).
        - withdraw() la rend invisible — seule la dialog est visible.
        - CTkToplevel est posée dessus (c'est une fenêtre secondaire, elle a besoin d'un parent).
        - L'utilisateur clique OK → on détruit tout → sys.exit(1).

        Cette méthode ne retourne jamais — sys.exit() est toujours appelé.
        """
        try:
            # Fenêtre principale CTk invisible — sert uniquement de parent technique
            root = ctk.CTk()
            root.withdraw()   # invisible

            # Centrage : on calcule d'abord, on positionne ensuite
            dlg_w, dlg_h = 460, 220
            # winfo_screenwidth/height = dimensions de l'écran physique
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            x = (screen_w - dlg_w) // 2
            y = (screen_h - dlg_h) // 2

            dlg = ctk.CTkToplevel(root)
            dlg.title(titre)
            dlg.geometry(f"{dlg_w}x{dlg_h}+{x}+{y}")
            dlg.resizable(False, False)

            # focus_force() : force le focus sur cette fenêtre
            # (sinon elle peut apparaître derrière d'autres fenêtres)
            dlg.focus_force()
            dlg.lift()

            # Layout interne de la dialog
            dlg.grid_columnconfigure(0, weight=1)
            dlg.grid_rowconfigure(0, weight=1)

            ctk.CTkLabel(
                dlg,
                text=message,
                wraplength=420,
                justify="left",
                text_color="#CC0000"   # rouge — erreur fatale
            ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

            def _quitter():
                root.destroy()
                sys.exit(1)

            ctk.CTkButton(
                dlg,
                text="Quitter",
                width=120,
                fg_color="#CC0000",
                hover_color="#990000",
                command=_quitter
            ).grid(row=1, column=0, pady=(0, 20))

            # protocol WM_DELETE_WINDOW : clic sur la croix = même effet que Quitter
            dlg.protocol("WM_DELETE_WINDOW", _quitter)

            root.mainloop()

        except Exception:
            # Dernier recours : si CTk lui-même plante (rare mais possible),
            # on affiche dans la console et on quitte quand même.
            print(f"\n[ERREUR FATALE] {titre}\n{message}\n", file=sys.stderr)
            sys.exit(1)

        # Cette ligne ne sera jamais atteinte — sys.exit() est dans _quitter()
        # ou dans le bloc except. Elle est là pour que l'analyseur statique
        # comprenne que la méthode ne retourne pas normalement.
        sys.exit(1)