from sysclasses.ui.Entity_ListView import Entity_ListView
from db.postgres import clsJob_run_details


class Job_run_details_ListView(Entity_ListView):
    """
    Liste des 100 dernières exécutions d'un job donné (jobid), triées par date de lancement décroissante.
    Délègue tout à Entity_ListView — surcharger ici si besoin spécifique futur.
    """

    def __init__(self, parent, jobid: int, ui_colors=None):
        self._jobid = jobid
        self._orderby = clsJob_run_details.START_TIME+' DESC'  # Tri par date de lancement décroissante
        super().__init__(
            parent,
            entity_class=clsJob_run_details ,
            where_clause=f"jobid = {self._jobid}",            
            order_by=self._orderby, 
            nb_lignes_max=100,  
            form_class=None,
            ui_colors=ui_colors,
            show_crud_buttons=False,
            sash_initial_position=0.9
        )

    