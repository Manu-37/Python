from sysclasses.clsStatBase import clsStatBase


class clsTstatBase(clsStatBase):
    """
    Ancre de toutes les classes d'analyse du projet tstat_analyse.
    Fixe le nom symbolique TSTAT_DATA une seule fois pour tout le projet.

    Même pattern que clsTstatData pour la base de collecte :
        clsStatBase      (sysclasses — framework générique)
            └── clsTstatBase  (tstat_analyse — ancre projet)
                    └── clsChargeStats, clsDrvStats, ...

    Les classes filles n'ont pas à connaître le nom symbolique
    ni à gérer la connexion — elles héritent sans surcharge.
    """

    _DB_SYMBOLIC_NAME = "TSTAT_DATA"

    def __init__(self):
        super().__init__(self._DB_SYMBOLIC_NAME)