from sysclasses.ui.Entity_ListView import Entity_ListView
from db.db_tstat_admin.public.clsTTK import clsTTK
from .Token_FormView import Token_FormView


class Token_ListView(Entity_ListView):
    """
    Vue liste des tokens Tesla.
    Délègue tout à Entity_ListView — surcharger ici si besoin spécifique futur.
    """

    def __init__(self, parent, ui_colors=None):
        super().__init__(
            parent,
            entity_class=clsTTK,
            order_by=clsTTK.VEH_ID,
            form_class=Token_FormView,
            ui_colors=ui_colors
        )