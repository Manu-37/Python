import socket
from pathlib import Path
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

    @staticmethod
    def _get_client_host() -> str:
        """
        Retourne l'adresse IP de la machine qui exécute l'applicatif.
        Utilisé par _resolve_ssh() pour déterminer si un tunnel SSH est nécessaire.

        Principe : on ouvre une socket UDP vers une adresse externe (8.8.8.8)
        sans envoyer de données — cela force l'OS à sélectionner l'interface
        réseau active et donc l'IP locale réelle.
        Cette méthode est plus fiable que socket.gethostbyname(gethostname())
        qui peut retourner 127.0.0.1 sur certaines configurations Linux.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    def _resolve_ssh(self, oNbe) -> dict | None:
        """
        ============================================================
        SECTION CRITIQUE — Résolution dynamique du tunnel SSH
        ============================================================

        Problème :
            Un même applicatif peut s'exécuter depuis des machines
            différentes (PC Windows, Freebox Linux) et atteindre des
            bases sur des serveurs différents (Freebox, PC Windows,
            serveur externe). Le besoin d'un tunnel SSH dépend donc
            du couple (machine cliente, serveur cible) — pas de la
            base seule, pas du client seul.

        Exemple concret :
            Base TSTAT_ADMIN sur la Freebox (192.168.1.51) :
            - Depuis le PC Windows  → SSH nécessaire (machines différentes)
            - Depuis la Freebox     → SSH inutile (même machine)

        Règle appliquée :
            1. On récupère l'IP de la machine cliente dynamiquement.
            2. On détermine l'IP du serveur "réel" :
               - Si SSH configuré dans NBE → le serveur SSH est la passerelle,
                 c'est son IP qu'on compare (nbe_ssh_host)
               - Sinon → c'est l'IP directe du serveur DB (nbe_host)
            3. Si client_host == serveur_host → même machine → connexion directe
            4. Sinon → SSH si configuré dans NBE, connexion directe sinon

        Hypothèse importante :
            Les serveurs ont des IP fixes sur le réseau local.
            Si un jour un applicatif Linux doit atteindre le MSSQL
            sur le PC Windows, il faudra passer le PC en IP fixe.
            Ce cas n'existe pas aujourd'hui — décision reportée volontairement.

        Paramètre :
            oNbe : instance de clsBAS_ENV_NBE — contient host, ssh_host,
                   ssh_enabled et tous les paramètres de connexion.

        Retourne :
            dict ssh_params si tunnel nécessaire, None sinon.
        ============================================================
        """
        client_host = self._get_client_host()

        # L'IP du serveur "réel" à comparer avec le client :
        # si SSH est configuré dans NBE, la passerelle SSH EST le serveur cible
        # (c'est elle qu'on atteint en premier depuis le réseau)
        serveur_host = oNbe.nbe_ssh_host if oNbe.nbe_ssh_enabled else oNbe.nbe_host

        self._log.debug(
            f"_resolve_ssh | client={client_host} | serveur={serveur_host} | "
            f"ssh_configured={oNbe.nbe_ssh_enabled}"
        )

        # Même machine → connexion directe, SSH inutile et contre-productif
        if client_host == serveur_host:
            self._log.debug(
                "_resolve_ssh | client == serveur → connexion directe, SSH ignoré"
            )
            return None

        # Machines différentes → SSH si configuré dans NBE
        if oNbe.nbe_ssh_enabled:
            self._log.debug(
                "_resolve_ssh | client != serveur + SSH configuré → tunnel SSH établi"
            )

            base_path = Path(self._config.env_params.get('path'))

            return {
                'enabled':  True,
                'host':     oNbe.nbe_ssh_host,
                'port':     int(oNbe.nbe_ssh_port),
                'user':     oNbe.nbe_ssh_user,
                'ssh_key_path': base_path / oNbe.nbe_ssh_key_path
            }

        # Machines différentes mais SSH non configuré → connexion directe tentée
        # (cas MSSQL local, réseau privé sans SSH, etc.)
        self._log.debug(
            "_resolve_ssh | client != serveur + SSH non configuré → connexion directe tentée"
        )
        return None

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

        print(f"DEBUG TYPE = '{self._config.env_params.get('type', '')}'")
        env_type = self._config.env_params.get('type', '')
        if not env_type:
            self._log.error("get_db : type d'environnement non défini dans la config.")
            return None

        oEnv = clsENV(env_code=env_type)
        oBas = clsBAS(bas_nom=symbolique_name)

        if not oBas.bas_id or not oEnv.env_id:
            self._log.error(f"get_db : base '{symbolique_name}' ou env '{env_type}' introuvable.")
            return None

        oNbe = clsBAS_ENV_NBE(bas_id=oBas.bas_id, env_id=oEnv.env_id)

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

        # Résolution dynamique du tunnel SSH — voir _resolve_ssh() pour
        # l'explication complète de la logique
        ssh_p = self._resolve_ssh(oNbe)

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