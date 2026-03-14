from .clsINICommun    import clsINICommun
from .clsINISecurity  import clsINISecurity
from .clsLOG          import clsLOG
from .clsCrypto       import clsCrypto
from .clsSQL_Postgre  import clsSQL_Postgre


class clsDBAManager:
    """
    Gestionnaire du cycle de vie des connexions.
    Singleton : une seule instance par processus, initialisée au démarrage.
    """

    _instance = None

    def __new__(cls, config_inst=None):
        if cls._instance is None:
            if config_inst is None:
                raise RuntimeError(
                    "clsDBAManager doit être initialisé avec un config_inst au premier appel."
                )
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instance = instance
        return cls._instance

    def __init__(self, config_inst=None):
        if self._initialized:
            return
        self._initialized = True

        self._config      = config_inst
        self._log         = clsLOG()
        self._connections = {}

        # clsINISecurity remplace clsINIDBBaseRef
        self._security = clsINISecurity()
        self._crypto   = clsCrypto()

        self._init_registry()

    def _init_registry(self):
        """Ouvre la connexion maître vers le catalogue (db_baseref)."""
        db_p  = self._security.db_params
        ssh_p = self._security.ssh_params

        # ssh_enabled est désormais dans ssh_params (clsINISecurity)
        # et non plus dans env_params (clsINICommun)
        if not ssh_p.get('ssh_enabled'):
            ssh_p = None
        else:
            ssh_p['enabled'] = True

        db_ref = clsSQL_Postgre(self._log)
        db_ref.connect_with_tunnel(db_p, ssh_p)
        self._connections['__REGISTRY__'] = db_ref
        self._log.info("Registre central connecté.")

    def get_db(self, symbolique_name: str):
        """
        Retourne une connexion active.
        - '__REGISTRY__' : toujours depuis le cache.
        - Autres noms   : résolution via les entités db_baseref si absent du cache.
        """
        if symbolique_name == '__REGISTRY__' and symbolique_name not in self._connections:
            raise RuntimeError(
                "__REGISTRY__ absent du cache — _init_registry() n'a pas été appelé."
            )

        if symbolique_name in self._connections:
            return self._connections[symbolique_name]

        from db.db_baseref import clsENV, clsBAS, clsBAS_ENV_NBE

        env_type = self._config.env_params.get('TYPE', '')
        if not env_type:
            self._log.error("get_db : TYPE d'environnement non défini dans la config.")
            return None

        oEnv = clsENV(env_code=env_type)
        oBas = clsBAS(bas_nom=symbolique_name)

        if not oBas.bas_id or not oEnv.env_id:
            self._log.error(f"get_db : base '{symbolique_name}' ou env '{env_type}' introuvable.")
            return None

        oNbe = clsBAS_ENV_NBE(nbe_bas_id=oBas.bas_id, nbe_env_id=oEnv.env_id)

        if not oNbe.nbe_host:
            self._log.error(f"get_db : configuration introuvable pour {symbolique_name}/{env_type}")
            return None

        db_p = {
            'host':   oNbe.nbe_host,
            'port':   int(oNbe.nbe_port),
            'dbname': oNbe.nbe_db_name,
            'user':   oNbe.nbe_user,
            'pwd':    oNbe.nbe_pwd
        }

        ssh_p = None
        if oNbe.nbe_ssh_enabled:
            ssh_p = {
                'enabled':  True,
                'host':     oNbe.nbe_ssh_host,
                'port':     int(oNbe.nbe_ssh_port),
                'user':     oNbe.nbe_ssh_user,
                'key_path': oNbe.nbe_ssh_key_path
            }

        engine = clsSQL_Postgre(self._log)
        try:
            engine.connect_with_tunnel(db_p, ssh_p)
            self._connections[symbolique_name] = engine
            self._log.info(f"Connexion '{symbolique_name}' établie et mise en cache.")
            return engine
        except Exception as e:
            self._log.error(f"Échec connexion '{symbolique_name}' : {e}")
            return None

    def close_all(self):
        """Ferme toutes les connexions actives."""
        for name, conn in self._connections.items():
            try:
                conn.disconnect()
                self._log.info(f"Connexion '{name}' fermée.")
            except Exception as e:
                self._log.warning(f"Erreur fermeture '{name}' : {e}")
        self._connections.clear()