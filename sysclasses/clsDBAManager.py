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

        self._security = clsINISecurity()
        self._crypto   = clsCrypto()

        self._init_registry()

    def _init_registry(self):
        """Ouvre la connexion maître vers le catalogue (db_baseref)."""
        db_p  = self._security.db_params
        ssh_p = self._security.ssh_params

        if not ssh_p.get('ssh_enabled'):
            ssh_p = None
        else:
            ssh_p['enabled'] = True

        db_ref = clsSQL_Postgre(self._log)
        db_ref.connect_with_tunnel(db_p, ssh_p)
        self._connections['__REGISTRY__'] = db_ref
        self._log.debug("Registre central connecté.")

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

        Paramètre :
            oNbe : instance de clsBAS_ENV_NBE — contient host, ssh_host,
                   ssh_enabled et tous les paramètres de connexion.
                   Peut être un objet réel (chargé depuis la DB) ou un objet
                   factice peuplé depuis l'écran (cas test_connection()).

        Retourne :
            dict ssh_params si tunnel nécessaire, None sinon.
        ============================================================
        """
        client_host = self._get_client_host()

        serveur_host = oNbe.nbe_ssh_host if oNbe.nbe_ssh_enabled else oNbe.nbe_host

        self._log.debug(
            f"_resolve_ssh | client={client_host} | serveur={serveur_host} | "
            f"ssh_configured={oNbe.nbe_ssh_enabled}"
        )

        if client_host == serveur_host:
            self._log.debug(
                "_resolve_ssh | client == serveur → connexion directe, SSH ignoré"
            )
            return None

        if oNbe.nbe_ssh_enabled:
            self._log.debug(
                "_resolve_ssh | client != serveur + SSH configuré → tunnel SSH établi"
            )

            base_path = Path(self._config.env_params.get('path'))

            return {
                'enabled':      True,
                'host':         oNbe.nbe_ssh_host,
                'port':         int(oNbe.nbe_ssh_port),
                'user':         oNbe.nbe_ssh_user,
                'ssh_key_path': base_path / oNbe.nbe_ssh_key_path
            }

        self._log.debug(
            "_resolve_ssh | client != serveur + SSH non configuré → connexion directe tentée"
        )
        return None

    def get_db(self, symbolique_name: str, env_type_test: str = None):
        """
        Retourne une connexion active.
        - '__REGISTRY__' : toujours depuis le cache.
        - Autres noms   : résolution via les entités db_baseref si absent du cache.
        - env_type_test : paramètre optionnel pour forcer un type d'environnement spécifique
                          lors de la résolution (utilisé uniquement par le bouton test de BaseRef_Manager).
        """
        if symbolique_name == '__REGISTRY__' and symbolique_name not in self._connections:
            raise RuntimeError(
                "__REGISTRY__ absent du cache — _init_registry() n'a pas été appelé."
            )

        if symbolique_name in self._connections:
            return self._connections[symbolique_name]

        from db.db_baseref import clsENV, clsBAS, clsBAS_ENV_NBE
        if env_type_test:
            env_type = env_type_test
        else:
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

    def test_connection(self, oNbe) -> dict:
        """
        Teste une connexion de manière éphémère — sans inscription au pool.

        Paramètre :
            oNbe : instance de clsBAS_ENV_NBE peuplée depuis l'écran.
                   Même interface qu'un objet réel — _resolve_ssh() s'applique
                   sans modification, y compris la comparaison IP client/serveur.

        Comportement :
            - Emprunte exactement le même chemin que get_db() :
              résolution SSH via _resolve_ssh(), puis connect_with_tunnel().
            - La connexion est fermée dans tous les cas (succès ou échec)
              via un bloc finally — jamais enregistrée dans self._connections.

        Retourne :
            {"succes": True}
            {"succes": False, "erreur": "message lisible"}
        """
        db_p = {
            'host':   oNbe.nbe_host,
            'port':   int(oNbe.nbe_port),
            'dbname': oNbe.nbe_db_name,
            'user':   oNbe.nbe_user,
            'pwd':    oNbe.nbe_pwd
        }

        # _resolve_ssh() applique la logique complète :
        # comparaison IP client/serveur, SSH ignoré si même machine.
        # oNbe est un objet factice peuplé depuis l'écran — _resolve_ssh()
        # ne sait pas (et n'a pas besoin de savoir) d'où viennent les valeurs.
        ssh_p = self._resolve_ssh(oNbe)

        engine = clsSQL_Postgre(self._log)
        try:
            engine.connect_with_tunnel(db_p, ssh_p)
            self._log.info(
                f"test_connection | Succès — {oNbe.nbe_host}:{oNbe.nbe_port}/{oNbe.nbe_db_name}"
            )
            return {"succes": True}

        except Exception as e:
            msg = str(e)
            self._log.warning(f"test_connection | Échec — {msg}")
            return {"succes": False, "erreur": msg}

        finally:
            # Déconnexion systématique — tunnel SSH compris si ouvert
            try:
                engine.disconnect()
            except Exception:
                pass

    def close_all(self):
        """Ferme toutes les connexions actives."""
        for name, conn in self._connections.items():
            try:
                conn.disconnect()
                self._log.info(f"Connexion '{name}' fermée.")
            except Exception as e:
                self._log.warning(f"Erreur fermeture '{name}' : {e}")
        self._connections.clear()