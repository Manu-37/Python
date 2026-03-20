import customtkinter as ctk
from sysclasses.ui.AutoFormView import AutoFormView
from sysclasses.ui.MessageDialog import MessageDialog

class Bas_Env_FormView(AutoFormView):
    """
    Formulaire spécifique pour la table Bases de données.
    Actuellement vide, prévu pour extensions futures.
    """
    def __init__(self, parent, entity_instance, mode, ui_colors=None):
        super().__init__(parent, entity_instance, mode, ui_colors=ui_colors)


    def _extend_buttons(self):
        ctk.CTkButton(
            self._frame_btn, text="Tester", command=self._check
        ).pack(side="left", padx=5)

    def _check(self):
        # Placeholder pour la logique de test de connexion à la base
        # À implémenter selon les besoins spécifiques du projet
        from sysclasses import clsDBAManager
        from db.db_baseref import clsBAS, clsENV
        dba = clsDBAManager()
        obas = clsBAS(bas_id=self.bas_id)
        oenv = clsENV(env_id=self.env_id)  
        oEngine = dba.get_db(obas.bas_nom, env_type_test=oenv.env_code)
        if not oEngine or not oEngine.is_connected():
            MessageDialog.error(self, "Test de connexion", "Échec du test de connexion à la base de données.")
        else:
            MessageDialog.info(self, "Test de connexion", "Test de connexion à la base de données réussi !")

