from sysclasses.ui.Entity_ListView import Entity_ListView
from db.db_baseref.public.clsENV import clsENV
from .Environment_FormView import Environment_FormView


class Environment_ListView(Entity_ListView):
    """
    Vue liste des Environnements.
    Délègue tout à Entity_ListView — surcharger ici si besoin spécifique futur.
    """

    def __init__(self, parent, ui_colors=None):
        super().__init__(
            parent,
            entity_class=clsENV,
            order_by=clsENV.ENV_CODE,
            form_class=Environment_FormView,
            ui_colors=ui_colors,
            sash_initial_position=0.3
        )