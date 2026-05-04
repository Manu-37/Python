from ..clsPostgres import clsPostgres

class clsJob(clsPostgres):
    # 1. IDENTITÉ
    _schema = "cron"
    _table  = "job"
    _pk     = "jobid"

    # 2. DICTIONNAIRE DES COLONNES
    JOBID          = "jobid"
    SCHEDULE       = "schedule"
    COMMAND        = "command"
    NODENAME       = "nodename"
    NODEPORT       = "nodeport"
    DATABASE       = "database"
    USERNAME       = "username"
    ACTIVE         = "active"
    JOBNAME        = "jobname"
    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._tabJob_run_details = None
        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self):
        """Contrôle d'intégrité pour les bases."""
        libelle_erreur = "Il n'est pas possible d'insérer de ligne dans la table cron.job via une interface de saisie. Cette table est réservée à l'insertion de tâches planifiées pour le catalogue."
        flag_error     = True

        # Cette méthode existe pour mémoire puisqu'elle n'a pas vocation a être utilisée dans une interface de saisie. 
        # Par securité, elle bloque toute tentative d'insertion manuelle en retournant une erreur.

        return flag_error, libelle_erreur

    # 5. ACCÈS

    @property
    def jobid(self) -> int:
        return self.get_natural(self.JOBID)

    @property
    def schedule(self) -> str:
        return self.get_natural(self.SCHEDULE)

    @property
    def command(self) -> str:
        return self.get_natural(self.COMMAND)
    
    @property
    def nodename(self) -> str:
        return self.get_natural(self.NODENAME)

    @property
    def nodeport(self) -> int:
        return self.get_natural(self.NODEPORT)

    @property
    def database(self) -> str:
        return self.get_natural(self.DATABASE)

    @property
    def username(self) -> str:
        return self.get_natural(self.USERNAME)

    @property
    def active(self) -> bool:
        return self.get_natural(self.ACTIVE)

    @property
    def jobname(self) -> str:
        return self.get_natural(self.JOBNAME)

    # 6. NAVIGATION

    @property
    def tabJob_run_details(self):
        """récupère la liste des détails d'exécution de la tâche planifiée (cron.job_run_details)"""
        if self._tabJob_run_details is None:
            from .clsJob_run_details import clsJob_run_details

            sql = f"SELECT * FROM {clsJob_run_details._schema}.{clsJob_run_details._table} " \
                  f"WHERE {clsJob_run_details.JOBID} = {self.ogEngine.placeholder}"

            res = self.ogEngine.execute_select(sql, (self.jobid,))

            self._tabJob_run_details = clsJob_run_details.DepuisResultat(res)

        return self._tabJob_run_details
