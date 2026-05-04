from ..clsPostgres import clsPostgres
from datetime import datetime

class clsJob_run_details(clsPostgres):
    # 1. IDENTITÉ
    _schema = "cron"
    _table  = "job_run_details"
    _pk     = "runid"

    # 2. DICTIONNAIRE DES COLONNES
    # FK — portent le nom de la colonne dans la table étrangère (convention BDD)
    JOBID       = "jobid"
    RUNID       = "runid"
    JOB_PID     = "job_pid"
    DATABASE    = "database"
    USERNAME    = "username"
    COMMAND     = "command"
    STATUS      = "status"
    RETURN_MESSAGE = "return_message"
    START_TIME  = "start_time"
    END_TIME    = "end_time"
    
    # 3. NAISSANCE
    def __init__(self, **kwargs):
        self._oJob = None

        super().__init__(**kwargs)

    # 4. VALIDATION
    def ctrl_valeurs(self) -> tuple[bool, str]:
        """Contrôle d'intégrité details d'exécution d'une tâche."""
        
        libelle_erreur = "Il n'est pas possible d'insérer de ligne dans la table cron.job_run_details via une interface de saisie. Cette table est réservée à l'insertion de détails d'exécution de tâches planifiées."
        flag_error     = True

        # Cette méthode existe pour mémoire puisqu'elle n'a pas vocation a être utilisée dans une interface de saisie. 
        # Par securité, elle bloque toute tentative d'insertion manuelle en retournant une erreur.

        return flag_error, libelle_erreur

    # 5. ACCÈS : Pas de setters ici, les détails d'exécution sont immuables une fois créés. 
    #            Seuls des getters sont proposés.

    # --- PK ---
    @property
    def runid(self) -> int:
        return self.get_natural(self.RUNID)

    # --- FK ---
    @property
    def jobid(self) -> int:
        return self.get_natural(self.JOBID)

    # --- AUTRES COLONNES ---
   
    @property
    def job_pid(self) -> int:
        return self.get_natural(self.JOB_PID)

    @property
    def database(self) -> str:
        return self.get_natural(self.DATABASE)

    @property
    def username(self) -> str:
        return self.get_natural(self.USERNAME)

    @property
    def command(self) -> str:
        return self.get_natural(self.COMMAND)

    @property
    def status(self) -> str:
        return self.get_natural(self.STATUS)

    @property
    def return_message(self) -> str:
        return self.get_natural(self.RETURN_MESSAGE)

    @property
    def start_time(self) -> datetime:
        val = self.get_natural(self.START_TIME)
        return val.astimezone() if val is not None else None

    @property
    def end_time(self) -> datetime:
        val = self.get_natural(self.END_TIME)
        return val.astimezone() if val is not None else None

    # 6. NAVIGATION (Lazy Loading)

    @property
    def oJob(self):
        """Retourne l'objet clsJOB parent (1 seul, logique FK)."""
        if self._oJob is None:
            from .clsJob import clsJob
            self._oJob = clsJob(jobid=self.jobid)
        return self._oJob
