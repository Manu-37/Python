from ..clsEntity_ABS import clsEntity_ABS
from sysclasses.clsLOG import clsLOG


class clsTstatData(clsEntity_ABS):
    """
    Ancre de toutes les entités de db_tstat_data.
    Même pattern que clsTstatAdmin et clsBaseRef.
    """
    _DB_SYMBOLIC_NAME = "TSTAT_DATA"

    def __init__(self, **kwargs):
        from sysclasses.clsDBAManager import clsDBAManager
        self.ogLog     = clsLOG()
        self.ogManager = clsDBAManager()
        self.ogEngine  = self.ogManager.get_db(self._DB_SYMBOLIC_NAME)
        super().__init__(**kwargs)