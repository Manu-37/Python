from sysclasses.ui.Entity_ListView import Entity_ListView
from db.postgres import clsJob
from .Job_run_details_ListView import Job_run_details_ListView


class Job_ListView(Entity_ListView):
    """
    Liste des tâches planifiées (cron.jobs). Sélectionner une ligne affiche les 100 dernières exécutions de la tâche sélectionnée (cron.job_run_details) dans le panneau de droite. 
    Délègue tout à Entity_ListView — surcharger ici si besoin spécifique futur.
    """

    def __init__(self, parent, ui_colors=None):
        super().__init__(
            parent,
            entity_class=clsJob ,
            order_by=clsJob.JOBNAME,  # Tri par nom de job
            form_class=None,
            ui_colors=ui_colors,
            show_crud_buttons=False,
            sash_initial_position=0.2
            )
    
    # --------------------------
    # Sélection / double clic
    # --------------------------
    def _on_row_selected(self, ligne):
        super()._on_row_selected(ligne)
        for w in self.frame_fiche.winfo_children():
            w.destroy()
        Job_run_details_ListView(
            self.frame_fiche, jobid=ligne["jobid"], ui_colors=self.UIColors
        ).pack(expand=True, fill="both")

    def _on_row_double_click(self, ligne):
        pass