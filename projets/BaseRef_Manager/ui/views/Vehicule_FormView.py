from sysclasses.ui.AutoFormView import AutoFormView


class Vehicule_FormView(AutoFormView):
    """
    Formulaire spécifique pour la table Véhicules Tesla.
    Actuellement vide, prévu pour extensions futures.
    """
    def __init__(self, parent, entity_instance, mode, ui_colors=None):
        super().__init__(parent, entity_instance, mode, ui_colors=ui_colors)