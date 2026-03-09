from sysclasses.ui.Entity_ListView import Entity_ListView
from db.db_baseref.public.clsBAS_ENV_NBE import clsBAS_ENV_NBE
from .Bas_Env_FormView import Bas_Env_FormView


class Bas_Env_ListView(Entity_ListView):
    """
    Vue liste des paramétrages des Bases de données par environnement.
    Délègue tout à Entity_ListView — surcharger ici si besoin spécifique futur.
    """

    def __init__(self, parent, ui_colors=None):
        super().__init__(
            parent,
            entity_class=clsBAS_ENV_NBE ,
            order_by=clsBAS_ENV_NBE.BAS_ID,  # Tri par base d'abord, puis environnement
            form_class=Bas_Env_FormView,
            ui_colors=ui_colors
        )