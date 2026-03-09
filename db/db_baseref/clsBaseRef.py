# DB/BaseRef/clsBaseRef.py
from db.clsEntity_ABS import clsEntity_ABS
from sysclasses.clsLOG import clsLOG

class clsBaseRef(clsEntity_ABS):
    """
    L'Ancre : Elle centralise les outils pour toutes les tables du catalogue.
    """
    _DB_SYMBOLIC_NAME = "__REGISTRY__"

    def __init__(self, **kwargs):
        from sysclasses.clsDBAManager import clsDBAManager
        # Les singletons se retrouvent simplement via leur constructeur sans argument.
        # __new__ retourne l'instance existante, __init__ ne fait rien (garde _initialized).
        self.ogLog     = clsLOG()
        self.ogManager = clsDBAManager()
        
        # On attache la connexion REGISTRY à l'instance
        self.ogEngine = self.ogManager.get_db(self._DB_SYMBOLIC_NAME)

        # On appelle le constructeur de l'abstraction (clsEntity_ABS)
        super().__init__(**kwargs)
