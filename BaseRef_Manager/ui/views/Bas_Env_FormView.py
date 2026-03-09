from sysclasses.ui.AutoFormView import AutoFormView

class Bas_Env_FormView(AutoFormView):
    """
    Formulaire spécifique pour la table Bases de données.
    Actuellement vide, prévu pour extensions futures.
    """
    def __init__(self, parent, entity_instance, mode, ui_colors=None):
        super().__init__(parent, entity_instance, mode, ui_colors=ui_colors)
