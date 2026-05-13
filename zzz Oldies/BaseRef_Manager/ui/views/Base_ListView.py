from sysclasses.ui.Entity_ListView import Entity_ListView
from db.db_baseref.public.clsBAS import clsBAS
from .Base_FormView import Base_FormView


class Base_ListView(Entity_ListView):
    """
    Vue liste des Bases de données.
    Délègue tout à Entity_ListView — surcharger ici si besoin spécifique futur.
    """

    def __init__(self, parent, ui_colors=None):
        super().__init__(
            parent,
            entity_class=clsBAS,
            order_by=clsBAS.BAS_NOM,
            form_class=Base_FormView,
            ui_colors=ui_colors,
            sash_initial_position=0.3
        )