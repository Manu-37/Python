import logging
import sys
import uuid
import datetime
import atexit
import inspect # Pour récupérer les infos d'appel (fichier/ligne)
from logging.handlers import RotatingFileHandler
from pathlib import Path

class clsLOG:
    """
    Gestionnaire de LOG structuré.
    Signature : PROJET | VERSION | UUID | TIMESTAMP | FICHIER:LIGNE | LEVEL | MESSAGE
    """
    _STACK_LVL = 2
    _instance = None

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
        # Garde : si déjà initialisé, on ne fait rien
        if self._initialized:
            return
        self._initialized = True

        self.proj_params = config_inst.project_params
        self.log_params  = config_inst.log_params
        
        self._project_name  = self.proj_params['name']
        self._version       = self.proj_params['version']
        self._instance_uuid = str(uuid.uuid4())[:8]
        self._start_time    = datetime.datetime.now()
        
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
            logging.StreamHandler(sys.stdout), 
            RotatingFileHandler(str(log_path), maxBytes=params['max_bytes'], backupCount=params['backup_count'])
        ]
        for h in handlers:
            h.setFormatter(formatter)
            self._logger.addHandler(h)

    def _get_caller_info(self):
        """Récupère dynamiquement le fichier et la ligne qui a appelé le log."""
        try:
            frame = inspect.stack()[3]
            filename = Path(frame.filename).name
            lineno = frame.lineno
            return f"{filename}:{lineno}"
        except Exception:
            return "unknown:0"

    def _build_signed_msg(self, level_name: str, msg: str, is_lifecycle=False) -> str:
        """Construit la ligne de log avec la chaîne d'authentification."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        caller = "SYSTEM" if is_lifecycle else self._get_caller_info()
        return (f"{self._project_name} | {self._version} | {self._instance_uuid} | "
                f"{timestamp} | {caller:20} | {level_name:8} | {msg}")

    # --- Méthodes de cycle de vie ---

    def log_start_treatment(self):
        self.always("OUVERTURE DU TRAITEMENT", is_lifecycle=True)

    def log_end_treatment(self):
        duration = datetime.datetime.now() - self._start_time
        self.always(f"FERMETURE DU TRAITEMENT | DUREE : {duration}", is_lifecycle=True)

    # --- Méthodes de logging ---

    def always(self, msg: str, is_lifecycle=False):
        self._logger.log(logging.CRITICAL, self._build_signed_msg("ALWAYS", msg, is_lifecycle), stacklevel=self._STACK_LVL)

    def critical(self, msg: str):
        self._logger.log(logging.CRITICAL, self._build_signed_msg("CRITICAL", msg), stacklevel=self._STACK_LVL)

    def error(self, msg: str):
        self._logger.error(self._build_signed_msg("ERROR", msg), stacklevel=self._STACK_LVL)

    def warning(self, msg: str):
        self._logger.warning(self._build_signed_msg("WARNING", msg), stacklevel=self._STACK_LVL)

    def info(self, msg: str):
        self._logger.info(self._build_signed_msg("INFO", msg), stacklevel=self._STACK_LVL)

    def debug(self, msg: str):
        self._logger.debug(self._build_signed_msg("DEBUG", msg), stacklevel=self._STACK_LVL)
