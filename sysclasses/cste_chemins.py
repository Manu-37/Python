from pathlib import Path

# Variables PRIVÉES au module.
# Le préfixe _ signifie : "usage interne, ne pas importer directement".
_APP_DIR    : Path = Path('')
_PYTHON_DIR : Path = Path('')
_PROJET_NOM : str  = ''
_PROJET_VER : str  = ''


def init_chemins(app_dir: Path, projet_nom: str, projet_ver: str) -> None:
    """
    Appelée UNE SEULE FOIS au démarrage, depuis le point d'entrée du projet.
    Fixe les chemins racines et les constantes projet pour toute l'application.

    Paramètres :
        app_dir    : dossier racine du projet  (ex: .../Python/projets/BaseRef_Manager)
        projet_nom : nom du projet             (ex: "BaseRef_Manager")
        projet_ver : version du projet         (ex: "0.0.1")
    """
    global _APP_DIR, _PYTHON_DIR, _PROJET_NOM, _PROJET_VER
    _APP_DIR    = app_dir
    _PYTHON_DIR = app_dir.parent.parent.resolve()  # remonte deux niveaux jusqu'à DEV/Python
    _PROJET_NOM = projet_nom.upper()
    _PROJET_VER = projet_ver


def get_app_dir() -> Path:
    """Retourne le dossier racine du projet en cours (ex: .../Python/projets/BaseRef_Manager)."""
    return _APP_DIR


def get_python_dir() -> Path:
    """Retourne le dossier Python parent (ex: .../Python) — contient logs, projets, sysclasses, db."""
    return _PYTHON_DIR


def get_projet_nom() -> str:
    """Retourne le nom du projet en majuscules (ex: 'BASEREF_MANAGER')."""
    return _PROJET_NOM


def get_projet_ver() -> str:
    """Retourne la version du projet (ex: '0.0.1')."""
    return _PROJET_VER
