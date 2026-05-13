import customtkinter as ctk
from sysclasses.ui.AutoFormView import AutoFormView
from sysclasses.ui.MessageDialog import MessageDialog


class Bas_Env_FormView(AutoFormView):
    """
    Formulaire spécifique pour le paramétrage base / environnement.

    Extension par rapport à AutoFormView :
        - Bouton "Tester la connexion" ajouté via _extend_buttons().
        - _check() :
            1. Lit l'écran via _get_entity_from_screen() → peuple self.entity
            2. Instancie un clsBAS_ENV_NBE vide et le peuple avec les valeurs
               lues à l'écran — même interface qu'un objet réel chargé depuis la DB
            3. Délègue entièrement à clsDBAManager.test_connection(oNbe)
               qui applique _resolve_ssh() sans modification (comparaison IP
               client/serveur incluse) puis tente connect_with_tunnel()
            4. La connexion de test est éphémère — jamais inscrite au pool
    """

    def __init__(self, parent, entity_instance, mode, ui_colors=None):
        super().__init__(parent, entity_instance, mode, ui_colors=ui_colors)

    # --------------------------------------------------
    # Hook boutons
    # --------------------------------------------------

    def _extend_buttons(self):
        ctk.CTkButton(
            self._frame_btn, text="Tester la connexion", command=self._check
        ).pack(side="left", padx=5)

    # --------------------------------------------------
    # Test de connexion
    # --------------------------------------------------

    def _check(self):
        """
        Teste la connexion avec les paramètres affichés à l'écran.

        On ne fait jamais confiance à l'utilisateur — on lit ce qui est
        affiché, pas ce qui est en base. _get_entity_from_screen() peuple
        self.entity depuis les widgets sans déclencher de sauvegarde.

        On construit ensuite un objet clsBAS_ENV_NBE vide et on le peuple
        manuellement depuis self.entity. Cet objet factice expose exactement
        la même interface qu'un objet réel — _resolve_ssh() s'applique
        sans adaptation.
        """
        # Étape 1 — Lire l'écran et peupler self.entity
        self._get_entity_from_screen()

        # Étape 2 — Construire un objet NBE factice avec les valeurs écran
        # clsBAS_ENV_NBE() sans argument crée un objet vide sans chargement DB.
        # On le peuple manuellement — même interface qu'un objet réel.
        from db.db_baseref.public.clsBAS_ENV_NBE import clsBAS_ENV_NBE
        oNbe = clsBAS_ENV_NBE()

        oNbe.nbe_host        = self.entity.nbe_host
        oNbe.nbe_port        = self.entity.nbe_port
        oNbe.nbe_db_name     = self.entity.nbe_db_name
        oNbe.nbe_user        = self.entity.nbe_user
        oNbe.nbe_pwd         = self.entity.nbe_pwd
        oNbe.nbe_ssh_enabled = self.entity.nbe_ssh_enabled
        oNbe.nbe_ssh_host    = self.entity.nbe_ssh_host
        oNbe.nbe_ssh_port    = self.entity.nbe_ssh_port
        oNbe.nbe_ssh_user    = self.entity.nbe_ssh_user
        oNbe.nbe_ssh_key_path = self.entity.nbe_ssh_key_path

        # Étape 3 — Déléguer le test à clsDBAManager
        # test_connection() applique _resolve_ssh() (comparaison IP client/serveur),
        # tente connect_with_tunnel(), ferme la connexion dans tous les cas.
        from sysclasses.clsDBAManager import clsDBAManager
        resultat = clsDBAManager().test_connection(oNbe)

        # Étape 4 — Afficher le résultat
        if resultat["succes"]:
            MessageDialog.info(
                self,
                "Test de connexion",
                "Connexion établie avec succès."
            )
        else:
            MessageDialog.error(
                self,
                "Test de connexion",
                f"Échec de la connexion.\n\nDétail : {resultat['erreur']}"
            )