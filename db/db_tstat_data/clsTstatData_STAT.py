from ..clsStat_ABS import clsStat_ABS


class clsTstatData_STAT(clsStat_ABS):
    """
    Ancre de toutes les classes d'analyse statistique de db_tstat_data.
    Même pattern que clsTstatData pour les entités.

    Fixe le nom symbolique TSTAT_DATA une seule fois.
    Les classes filles héritent de ogLog, ogEngine, _build_where, _date_trunc
    sans avoir à gérer la connexion.
    """

    _DB_SYMBOLIC_NAME = "TSTAT_DATA"

    def __init__(self):
        super().__init__(self._DB_SYMBOLIC_NAME)