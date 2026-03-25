import logging
import sys
import io
import uuid
import datetime
import atexit
import inspect
from pathlib import Path
from .cste_chemins import get_projet_nom, get_projet_ver


# ==============================================================================
# Handler personnalisé — rotation par timestamp
# ==============================================================================

class _TimestampedFileHandler(logging.Handler):
    """
    Handler de fichier avec rotation basée sur un timestamp dans le nom.

    Nommage   : log_AAAAMMJJ_HHMMSS.log
    Rotation  : à chaque emit(), si taille >= max_bytes → nouveau fichier horodaté
    Seuil     : à chaque ouverture d'un nouveau fichier, contrôle du nombre de
                fichiers présents et alerte par email si palier franchi.

    Le contrôle du seuil est délégué à un callable (_controler_seuil_fichiers)
    fourni par clsLOG à l'instanciation du handler, pour éviter le couplage
    circulaire handler → clsLOG.
    """

    _PATTERN = "log_*.log"
    _FMT_NOM = "log_%Y%m%d_%H%M%S.log"

    def __init__(self, log_folder: Path, max_bytes: int, on_nouveau_fichier=None):
        """
        log_folder        : dossier où écrire les logs (doit exister)
        max_bytes         : taille max d'un fichier avant rotation
        on_nouveau_fichier: callable(log_folder) appelé après chaque ouverture
                            d'un nouveau fichier (contrôle seuil)
        """
        super().__init__()
        self._folder            = log_folder
        self._max_bytes         = max_bytes
        self._on_nouveau_fichier = on_nouveau_fichier
        self._stream            = None
        self._current_path      = None
        self._ouvrir_ou_creer()

    # --------------------------------------------------
    # Ouverture initiale
    # --------------------------------------------------
    def _ouvrir_ou_creer(self):
        """
        Cherche le fichier log_*.log le plus récent.
        - S'il existe et est sous la limite → on s'y attache (append).
        - Sinon → nouveau fichier horodaté.
        """
        existants = sorted(self._folder.glob(self._PATTERN))
        if existants:
            candidat = existants[-1]  # le plus récent (tri alphabétique = tri chronologique)
            if candidat.stat().st_size < self._max_bytes:
                self._ouvrir(candidat)
                return
        self._ouvrir_nouveau()

    def _ouvrir(self, chemin: Path):
        """Attache le stream au fichier indiqué (mode append)."""
        if self._stream:
            self._stream.close()
        self._current_path = chemin
        self._stream = open(chemin, 'a', encoding='utf-8')

    def _ouvrir_nouveau(self):
        """Crée un nouveau fichier horodaté et notifie le contrôleur de seuil."""
        nom = datetime.datetime.now().strftime(self._FMT_NOM)
        chemin = self._folder / nom
        self._ouvrir(chemin)
        # Notifier clsLOG qu'un nouveau fichier vient d'être ouvert
        if self._on_nouveau_fichier:
            try:
                self._on_nouveau_fichier(self._folder)
            except Exception:
                pass  # le contrôle de seuil ne doit jamais faire planter le log

    # --------------------------------------------------
    # Émission — cœur du handler
    # --------------------------------------------------
    def emit(self, record):
        try:
            # Rotation si taille atteinte
            if self._current_path and self._current_path.stat().st_size >= self._max_bytes:
                self._ouvrir_nouveau()
            msg = self.format(record)
            self._stream.write(msg + '\n')
            self._stream.flush()
        except Exception:
            self.handleError(record)

    def close(self):
        if self._stream:
            self._stream.flush()
            self._stream.close()
            self._stream = None
        super().close()


# ==============================================================================
# clsLOG
# ==============================================================================

class clsLOG:
    """
    Gestionnaire de LOG structuré.
    Signature : PROJET | VERSION | UUID | TIMESTAMP | FICHIER:LIGNE | LEVEL | MESSAGE

    Nommage des fichiers : log_AAAAMMJJ_HHMMSS.log
    Rotation             : nouveau fichier horodaté quand max_bytes est atteint
    Purge                : à l'instanciation, suppression des fichiers plus vieux
                           que retention_days (basé sur le timestamp du nom)
    Alerte seuil         : à chaque rotation, si le nombre de fichiers franchit
                           un nouveau palier multiple de backup_count → email

    Résolution du chemin 'folder' dans le .ini :
        DEFAULT   → get_python_dir() / 'logs'
        absolu    → utilisé tel quel
        relatif   → résolu depuis get_app_dir()

    Paramètres .ini section [LOG] :
        folder                = DEFAULT
        max_bytes             = 1000000
        backup_count          = 10          # seuil d'alerte (pas de suppression)
        retention_days        = 30          # durée de rétention
        level                 = 20
        email_profil_critique = ALERTES
    """

    _STACK_LVL = 2
    _instance  = None
    _ALERT_FILE = ".last_alert"   # fichier de persistance du palier d'alerte

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

        self._email_profil_critique = self.log_params.get('email_profil_critique', 'ALERTES').upper()

        self._setup_logger(self.log_params)
        self._purger_vieux_logs()          # nettoyage à l'instanciation
        atexit.register(self.log_end_treatment)
        self.log_start_treatment()

    # --------------------------------------------------
    # Setup logger
    # --------------------------------------------------
    def _setup_logger(self, params: dict):
        # Le dossier est déjà résolu par clsINICommun.log_params
        self._log_folder = Path(params['folder'])
        self._log_folder.mkdir(parents=True, exist_ok=True)

        self._max_bytes    = int(params['max_bytes'])
        self._backup_count = int(params['backup_count'])

        self._logger = logging.getLogger(self._project_name)
        self._logger.setLevel(params['level'])
        self._logger.handlers.clear()

        formatter = logging.Formatter('%(message)s')

        # Handler console
        console_handler = logging.StreamHandler(
            stream=io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                errors='replace'
            ) if hasattr(sys.stdout, 'buffer') else sys.stdout
        )
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # Handler fichier horodaté
        file_handler = _TimestampedFileHandler(
            log_folder=self._log_folder,
            max_bytes=self._max_bytes,
            on_nouveau_fichier=self._controler_seuil_fichiers
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    # --------------------------------------------------
    # Purge à l'instanciation (retention_days)
    # --------------------------------------------------
    def _purger_vieux_logs(self):
        """
        Supprime les fichiers log_AAAAMMJJ_HHMMSS.log dont le timestamp
        dans le nom est plus vieux que retention_days jours.
        """
        retention_days = int(self.log_params.get('retention_days', 35))
        limite = datetime.datetime.now() - datetime.timedelta(days=retention_days)
        fmt = "%Y%m%d_%H%M%S"

        for f in self._log_folder.glob("log_*.log"):
            # Extraire le timestamp du nom : log_AAAAMMJJ_HHMMSS.log
            try:
                stem = f.stem               # "log_20260101_120000"
                ts_str = stem[4:]           # "20260101_120000"
                ts = datetime.datetime.strptime(ts_str, fmt)
                if ts < limite:
                    f.unlink()
            except (ValueError, OSError):
                pass  # nom inattendu ou erreur disque → on ignore silencieusement

    # --------------------------------------------------
    # Contrôle seuil à chaque nouveau fichier
    # --------------------------------------------------
    def _controler_seuil_fichiers(self, log_folder: Path):
        """
        Appelé à chaque ouverture d'un nouveau fichier log.
        Envoie un email si un nouveau palier multiple de backup_count est franchi.
        Persiste le palier atteint dans .last_alert pour éviter le flood.
        """
        fichiers = sorted(log_folder.glob("log_*.log"))
        count    = len(fichiers)
        palier_actuel = count // self._backup_count

        if palier_actuel == 0:
            return  # sous le seuil, rien à faire

        # Lire le palier connu (persisté)
        alert_file = log_folder / self._ALERT_FILE
        palier_connu = 0
        try:
            palier_connu = int(alert_file.read_text(encoding='utf-8').strip())
        except (FileNotFoundError, ValueError):
            pass

        if palier_actuel <= palier_connu:
            return  # palier déjà alerté, silence

        # Nouveau palier franchi → email + mise à jour persistance
        try:
            alert_file.write_text(str(palier_actuel), encoding='utf-8')
        except OSError:
            pass

        self._envoyer_alerte_seuil(count, fichiers)

    def _envoyer_alerte_seuil(self, count: int, fichiers: list):
        """
        Envoie l'email d'alerte accumulation de fichiers logs.
        Toujours envoyé (DEV et PROD).
        """
        try:
            # Date la plus ancienne et la plus récente depuis les noms de fichiers
            fmt = "%Y%m%d_%H%M%S"
            dates = []
            for f in fichiers:
                try:
                    ts_str = f.stem[4:]
                    dates.append(datetime.datetime.strptime(ts_str, fmt))
                except ValueError:
                    pass

            date_min = min(dates).strftime('%Y-%m-%d') if dates else "inconnue"
            date_max = max(dates).strftime('%Y-%m-%d') if dates else "inconnue"
            palier   = count // self._backup_count

            corps = (
                f"Projet         : {self._project_name}\n"
                f"Environnement  : {self._env_type}\n"
                f"Dossier logs   : {self._log_folder}\n\n"
                f"Nombre de fichiers logs présents : {count}\n"
                f"Seuil configuré                  : {self._backup_count}\n"
                f"Palier franchi                   : {palier}×\n\n"
                f"Fichiers les plus anciens : {date_min}\n"
                f"Fichiers les plus récents : {date_max}\n"
            )

            from sysclasses.clsEmailManager import clsEmailManager
            clsEmailManager().envoyer(
                profil=self._email_profil_critique,
                sujet=f"[{self._project_name}] ALERTE — Logs accumulés",
                corps=corps
            )
        except RuntimeError:
            pass  # EmailManager pas encore initialisé
        except Exception:
            pass  # erreur d'envoi → silencieux, le log ne doit jamais planter

    # --------------------------------------------------
    # Envoi email alerte critique (PROD uniquement)
    # --------------------------------------------------
    def _envoyer_alerte_critique(self, msg: str):
        self.debug(f"clsLOG | _envoyer_alerte_critique | env_type='{self._env_type}'")
        if self._env_type != 'PROD':
            return
        try:
            from sysclasses.clsEmailManager import clsEmailManager
            clsEmailManager().envoyer(
                profil=self._email_profil_critique,
                sujet=f"[{self._project_name}] ALERTE CRITIQUE",
                corps=f"Environnement : {self._env_type}\n\n{msg}"
            )
        except RuntimeError:
            pass
        except Exception:
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
    # Méthodes de logging — interface publique inchangée
    # --------------------------------------------------
    def _build_signed_msg(self, level_name: str, msg: str, is_lifecycle=False) -> str:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        caller    = "SYSTEM" if is_lifecycle else self._get_caller_info()
        return (f"{self._project_name} | {self._version} | {self._instance_uuid} | "
                f"{timestamp} | {caller:20} | {level_name:8} | {msg}")

    def _get_caller_info(self):
        try:
            frame = inspect.stack()[3]
            filename = Path(frame.filename).name
            lineno   = frame.lineno
            return f"{filename}:{lineno}"
        except Exception:
            return "unknown:0"

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