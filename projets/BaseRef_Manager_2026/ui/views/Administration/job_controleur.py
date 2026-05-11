# ui/views/gestion_bases/bas_controleur.py

from sysclasses.ui import QtControleur
from db.postgres.cron import clsJob, clsJob_run_details



class JobControleur(QtControleur):
    """
    Contrôleur de la page Bases de données.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsJob
    _ordre_tri     = clsJob.JOBNAME
    _afficher_crud = False
    _avec_fiche    = False
    _ratio_initial = 0.2

    def _creer_zone_basse(self):
        from sysclasses.ui.qt.qt_liste_vue import QtListeVue
        self._vue_fiche   = None          # requis par le framework
        self._vue_details = QtListeVue(afficher_crud=False)
        return self._vue_details

    def _on_selection(self, ligne):
        # Affiche les détails de la tâche sélectionnée dans la zone basse
        if ligne is None:
            # todo : Afficher widget qmessage "aucune tâche sélectionnée"
            pass
        else:
            jobid = ligne.get(clsJob.JOBID)
            where_param = f"{clsJob_run_details.JOBID} = {jobid}"
            order_param = f"{clsJob_run_details.RUNID} DESC"
            details = clsJob_run_details.load_all(where_clause=where_param,order_by=order_param, limit=100)
            _metadata        = clsJob_run_details.get_metadata()
            colonnes_liste = _metadata.columns
            libelles_liste = [_metadata.get_col_label(col) for col in colonnes_liste]
            self._vue_details.charger(colonnes_liste, libelles_liste, details)