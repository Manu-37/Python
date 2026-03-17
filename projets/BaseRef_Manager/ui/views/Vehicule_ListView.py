from sysclasses.ui.Entity_ListView import Entity_ListView
from db.db_tstat_admin.public.clsVEH import clsVEH
from .Vehicule_FormView import Vehicule_FormView


class Vehicule_ListView(Entity_ListView):
    """
    Vue liste des véhicules Tesla.
    Délègue tout à Entity_ListView — surcharger ici si besoin spécifique futur.
    """

    def __init__(self, parent, ui_colors=None):
        super().__init__(
            parent,
            entity_class=clsVEH,
            order_by=clsVEH.VEH_VIN,
            form_class=Vehicule_FormView,
            ui_colors=ui_colors
        )