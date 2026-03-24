import logging
import sys
import io
import uuid
import datetime
import atexit
import inspect
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .cste_chemins import get_projet_nom, get_projet_ver


class clsLOG:
    """
    Gestionnaire de LOG structuré.
    Signature : PROJET | VERSION | UUID | TIMESTAMP | FICHIER:LIGNE | LEVEL | MESSAGE

    Le nom et la version du projet sont lus via get_projet_nom() / get_projet_ver()
    de cste_chemins — ils ne transitent plus par le .ini.

    Comportement email sur critical() :
        Si l'environnement est PROD (env_params['TYPE'] == 'PROD') ET que
        clsEmailManager est déjà initialisé, un email d'alerte est envoyé.
        Si EmailManager n'est pas encore disponible, le log est émis normalement
        sans erreur — l'email est silencieusement ignoré.
    """
    _STACK_LVL = 2
    _instance  = None

    # --------------------------------------------------
    # Singleton via __new__
    # --------------------------------------------------
    def __new__(cls, config_inst=None):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instance = instance
        return cls._instance

    def __init__(self, config_inst=None):
        if self._initialized:
            return
        self._initialized = True

        self.log_params = config_inst.log_params
        self._env_type  = config_inst.env_params.get('type', '').upper()

        self._project_name  = get_projet_nom()
        self._version       = get_projet_ver()
        self._instance_uuid = str(uuid.uuid4())[:8]
        self._start_time    = datetime.datetime.now()

        # Profil email à utiliser pour les alertes critiques.
        # Valeur par défaut : "ALERTES" — peut être surchargé via log_params['email_profil_critique']
        self._email_profil_critique = self.log_params.get('email_profil_critique', 'ALERTES').upper()

        self._setup_logger(self.log_params)
        atexit.register(self.log_end_treatment)
        self.log_start_treatment()

    def _setup_logger(self, params: dict):
        self._logger = logging.getLogger(self._project_name)
        self._logger.setLevel(params['level'])
        self._logger.handlers.clear()

        log_folder = Path(params['folder'])
        log_folder.mkdir(parents=True, exist_ok=True)
        log_path = log_folder / f"{self._project_name}.log"

        formatter = logging.Formatter('%(message)s')
        handlers = [
            logging.StreamHandler(
                stream=io.TextIOWrapper(
                    sys.stdout.buffer,
                    encoding='utf-8',
                    errors='replace'
                ) if hasattr(sys.stdout, 'buffer') else sys.stdout
            ),
            RotatingFileHandler(
                str(log_path),
                maxBytes=params['max_bytes'],
                backupCount=params['backup_count'],
                encoding='utf-8'
            )
        ]
        for h in handlers:
            h.setFormatter(formatter)
            self._logger.addHandler(h)

    def _get_caller_info(self):
        """Récupère dynamiquement le fichier et la ligne qui a appelé le log."""
        try:
            frame = inspect.stack()[3]
            filename = Path(frame.filename).name
            lineno   = frame.lineno
            return f"{filename}:{lineno}"
        except Exception:
            return "unknown:0"

    def _build_signed_msg(self, level_name: str, msg: str, is_lifecycle=False) -> str:
        """Construit la ligne de log avec la chaîne d'authentification."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        caller    = "SYSTEM" if is_lifecycle else self._get_caller_info()
        return (f"{self._project_name} | {self._version} | {self._instance_uuid} | "
                f"{timestamp} | {caller:20} | {level_name:8} | {msg}")

    # --------------------------------------------------
    # Envoi email alerte critique (PROD uniquement)
    # --------------------------------------------------
    def _envoyer_alerte_critique(self, msg: str):
        """
        Tente d'envoyer un email d'alerte si :
            1. L'environnement est PROD
            2. clsEmailManager est déjà initialisé (singleton disponible)
        Si l'une ou l'autre condition n'est pas remplie, on passe silencieusement.
        """
        self.info(f"clsLOG | _envoyer_alerte_critique | env_type='{self._env_type}'")
        if self._env_type != 'PROD':
            return
        try:
            # Import local pour éviter la dépendance circulaire à l'import du module.
            # clsEmailManager() sans argument retourne l'instance existante
            # ou lève RuntimeError si pas encore initialisé — on attrape les deux cas.
            from sysclasses.clsEmailManager import clsEmailManager
            clsEmailManager().envoyer(
                profil=self._email_profil_critique,
                sujet=f"[{self._project_name}] ALERTE CRITIQUE",
                corps=f"Environnement : {self._env_type}\n\n{msg}"
            )
        except RuntimeError:
            # EmailManager pas encore initialisé — silencieux, le log suffit
            pass
        except Exception:
            # Toute autre erreur d'envoi — silencieux, on ne fait jamais planter
            # l'application à cause d'un email raté
            pass

    # --------------------------------------------------
    # Méthodes de cycle de vie
    # --------------------------------------------------
    def log_start_treatment(self):
        self.always("OUVERTURE DU TRAITEMENT", is_lifecycle=True)

    def log_end_treatment(self):
        duration = datetime.datetime.now() - self._start_time
        self.always(f"FERMETURE DU TRAITEMENT | DUREE : {duration}", is_lifecycle=True)

    # --------------------------------------------------
    # Méthodes de logging
    # --------------------------------------------------
    def always(self, msg: str, is_lifecycle=False):
        self._logger.log(
            logging.CRITICAL,
            self._build_signed_msg("ALWAYS", msg, is_lifecycle),
            stacklevel=self._STACK_LVL
        )

    def critical(self, msg: str):
        self._logger.log(
            logging.CRITICAL,
            self._build_signed_msg("CRITICAL", msg),
            stacklevel=self._STACK_LVL
        )
        self._envoyer_alerte_critique(msg)

    def error(self, msg: str):
        self._logger.error(
            self._build_signed_msg("ERROR", msg),
            stacklevel=self._STACK_LVL
        )

    def warning(self, msg: str):
        self._logger.warning(
            self._build_signed_msg("WARNING", msg),
            stacklevel=self._STACK_LVL
        )

    def info(self, msg: str):
        self._logger.info(
            self._build_signed_msg("INFO", msg),
            stacklevel=self._STACK_LVL
        )

    def debug(self, msg: str):
        self._logger.debug(
            self._build_signed_msg("DEBUG", msg),
            stacklevel=self._STACK_LVL
        )